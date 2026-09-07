"""
Tests for jarvis/workers.py — the Worker Runtime (Stage D). Run directly:

    python3 jarvis/tests/test_workers.py

Covers: registration/discovery, execution (success/failure/timeout),
Stage B state-machine integration, concurrency (duplicate claim),
idempotency, cancellation, security (cross-user, unauthorized capability),
and — the highest-stakes category — transaction safety through the worker
layer, including bypass attempts via an alternate worker/tool/phrasing.
"""

import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import memory as jm  # noqa: E402
import missions as msn  # noqa: E402
import workers  # noqa: E402


def _fresh_db(tmp_path: Path):
    db_file = tmp_path / "test_jarvis_workers.db"
    jm.DB_PATH = db_file
    msn.DB_PATH = db_file
    workers.DB_PATH = db_file
    jm.init_db()
    workers.init_db()  # cascades to msn.init_db()


def _mission_with_ready_step(user="user-1", worker_id="jarvis-context-assembly", description="Do a thing", inputs=None):
    mission = msn.create_mission(user, "Test mission")
    step = msn.create_step(mission["mission_id"], user, description, worker_id=worker_id, inputs=inputs)
    step = msn.transition_step(step["step_id"], mission["mission_id"], user, "READY")
    return mission, step


# --- Worker registration ------------------------------------------------------

def test_register_and_lookup_worker():
    registry = workers.WorkerRegistry()
    w = workers.ContextWorker()
    registry.register_worker(w)
    assert registry.get_worker("context-worker") is w
    assert w in registry.list_workers()


def test_find_workers_for_capability():
    registry = workers.WorkerRegistry()
    registry.register_worker(workers.ContextWorker())
    registry.register_worker(workers.MemoryWriteWorker())
    found = registry.find_workers_for_capability("jarvis-context-assembly")
    assert [w.worker_id for w in found] == ["context-worker"]
    assert registry.find_workers_for_capability("nonexistent-capability") == []


def test_disabled_worker_is_not_discoverable():
    registry = workers.WorkerRegistry()
    w = workers.ContextWorker()
    w.enabled = False
    registry.register_worker(w)
    assert registry.find_workers_for_capability("jarvis-context-assembly") == []


# --- Execution: success --------------------------------------------------------

def test_successful_execution_returns_structured_result_and_updates_step():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission, step = _mission_with_ready_step()
        result = workers.execute_step(mission["mission_id"], step["step_id"], "user-1")

        assert result.status == "SUCCEEDED"
        assert result.worker_id == "context-worker"
        assert result.execution_id
        assert result.started_at and result.completed_at
        assert isinstance(result.output, dict)  # assemble_context's own return shape
        assert "WORKER_SUCCEEDED" in result.trace

        updated = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
        assert updated["status"] == "SUCCEEDED"
        assert updated["attempt_count"] == 1


def test_memory_write_worker_actually_writes():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission, step = _mission_with_ready_step(
            worker_id="jarvis-memory-write",
            description="Remember something",
            inputs={"memory_type": "decision", "content": "Recorded by a worker"},
        )
        result = workers.execute_step(mission["mission_id"], step["step_id"], "user-1")
        assert result.status == "SUCCEEDED"

        recalled = jm.recall(context="business", query="Recorded by a worker")
        assert any("Recorded by a worker" in m["content"] for m in recalled)


# --- Execution: failure/timeout/malformed input --------------------------------

def test_worker_exception_is_recorded_as_failed_not_silently_swallowed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))

        class BrokenWorker(workers.Worker):
            worker_id = "broken-worker"
            capabilities = ("broken-capability",)

            def execute(self, step):
                raise RuntimeError("deliberately broken")

        registry = workers.WorkerRegistry()
        registry.register_worker(BrokenWorker())

        mission, step = _mission_with_ready_step(worker_id="broken-capability")
        result = workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry)

        assert result.status == "FAILED"
        assert result.error["code"] == "WORKER_EXECUTION_FAILED"
        updated = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
        assert updated["status"] == "FAILED"


def test_worker_timeout_is_recorded_as_timed_out_mapped_to_step_failed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))

        class SlowWorker(workers.Worker):
            worker_id = "slow-worker"
            capabilities = ("slow-capability",)

            def execute(self, step):
                time.sleep(2)
                return "too slow"

        registry = workers.WorkerRegistry()
        registry.register_worker(SlowWorker())

        mission, step = _mission_with_ready_step(worker_id="slow-capability")
        result = workers.execute_step(mission["mission_id"], step["step_id"], "user-1",
                                       registry=registry, timeout_seconds=0.2)

        assert result.status == "TIMED_OUT"
        assert result.error["code"] == "TOOL_TIMEOUT"
        updated = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
        assert updated["status"] == "FAILED", "Worker TIMED_OUT must map to MissionStep FAILED, not a new status"


def test_missing_required_input_fails_before_any_side_effect():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission, step = _mission_with_ready_step(worker_id="jarvis-memory-write", inputs={})  # missing memory_type/content
        try:
            workers.execute_step(mission["mission_id"], step["step_id"], "user-1")
            assert False, "should have raised"
        except workers.WorkerValidationError:
            pass
        # The step must still be READY - nothing was claimed, nothing ran.
        unchanged = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
        assert unchanged["status"] == "READY"
        assert unchanged["attempt_count"] == 0


def test_unavailable_capability_returns_worker_not_found():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission, step = _mission_with_ready_step(worker_id="gmail-read")
        try:
            workers.execute_step(mission["mission_id"], step["step_id"], "user-1")
            assert False, "should have raised"
        except workers.WorkerNotFoundError as e:
            assert e.error.code == "TOOL_NOT_FOUND"
        unchanged = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
        assert unchanged["status"] == "READY"


# --- State machine integration --------------------------------------------------

def test_only_a_ready_step_can_be_executed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = msn.create_mission("user-1", "Test")
        step = msn.create_step(mission["mission_id"], "user-1", "A step", worker_id="jarvis-context-assembly")
        # Still PENDING, never advanced to READY.
        try:
            workers.execute_step(mission["mission_id"], step["step_id"], "user-1")
            assert False, "should have raised"
        except workers.StepNotExecutableError:
            pass


# --- Concurrency: duplicate worker claim ----------------------------------------

def test_duplicate_claim_on_an_already_running_step_raises_state_conflict():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission, step = _mission_with_ready_step()
        # Simulate "worker A already claimed it" by transitioning to RUNNING directly.
        msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "RUNNING")
        try:
            workers.execute_step(mission["mission_id"], step["step_id"], "user-1")
            assert False, "a second execute_step() call must not be able to claim an already-RUNNING step"
        except workers.StepNotExecutableError:
            pass  # status is RUNNING, not READY - correctly rejected before any claim attempt


# --- Idempotency ------------------------------------------------------------------

def test_repeated_execution_id_returns_cached_result_without_reexecuting():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission, step = _mission_with_ready_step()
        first = workers.execute_step(mission["mission_id"], step["step_id"], "user-1", execution_id="exec-1")
        second = workers.execute_step(mission["mission_id"], step["step_id"], "user-1", execution_id="exec-1")
        assert first.execution_id == second.execution_id == "exec-1"
        assert first.completed_at == second.completed_at, "replay must return the exact cached result, not re-run"
        # Only one execution record exists.
        assert len(workers.list_executions_for_step(step["step_id"])) == 1


# --- Cancellation -------------------------------------------------------------------

def test_cancellation_propagates_to_the_mission_step():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission, step = _mission_with_ready_step()
        msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "RUNNING")
        cancelled = workers.cancel_execution(mission["mission_id"], step["step_id"], "user-1", reason="user changed mind")
        assert cancelled["status"] == "CANCELLED"


# --- Security -----------------------------------------------------------------------

def test_cross_user_mission_cannot_be_executed_against():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission, step = _mission_with_ready_step(user="user-1")
        try:
            workers.execute_step(mission["mission_id"], step["step_id"], "user-2")
            assert False, "user-2 must never be able to execute user-1's step"
        except msn.MissionNotFoundError:
            pass


def test_capability_with_no_registered_worker_is_unauthorized_not_silently_run():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        registry = workers.WorkerRegistry()  # deliberately empty
        mission, step = _mission_with_ready_step()
        try:
            workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry)
            assert False, "should have raised"
        except workers.WorkerNotFoundError:
            pass


# --- Transaction safety, exercised through the Worker layer specifically ------------

def test_transaction_shaped_step_is_blocked_before_any_claim_or_execution():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission, step = _mission_with_ready_step(description="Transfer 10,000 rupees via UPI to the vendor")
        try:
            workers.execute_step(mission["mission_id"], step["step_id"], "user-1")
            assert False, "should have raised"
        except workers.WorkerTransactionProhibitedError as e:
            assert e.error.code == "TRANSACTION_PROHIBITED"
            assert e.error.severity == "CRITICAL"

        blocked = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
        assert blocked["status"] == "BLOCKED"
        assert blocked["attempt_count"] == 0, "a prohibited step must never even be claimed - zero attempts recorded"
        assert workers.list_executions_for_step(step["step_id"]) == [], "no execution record for a prohibited step"


def test_transaction_bypass_via_a_differently_named_capability_still_blocked():
    """The description itself is the enforcement surface, not the
    capability id - renaming the worker_id to something innocuous-sounding
    must not bypass the check, since the scan reads the step's actual text."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission, step = _mission_with_ready_step(
            worker_id="jarvis-context-assembly",  # an innocuous, real capability
            description="Please redeem the client's mutual fund units today",
        )
        try:
            workers.execute_step(mission["mission_id"], step["step_id"], "user-1")
            assert False, "should have raised despite using a legitimate capability id"
        except workers.WorkerTransactionProhibitedError:
            pass


def test_transaction_bypass_via_indirect_phrasing_still_blocked():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission, step = _mission_with_ready_step(description="Execute a bank transfer to settle the invoice")
        try:
            workers.execute_step(mission["mission_id"], step["step_id"], "user-1")
            assert False, "should have raised"
        except workers.WorkerTransactionProhibitedError:
            pass


if __name__ == "__main__":
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_") and callable(obj)]
    failures = []
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
        except AssertionError as e:
            failures.append(test.__name__)
            print(f"FAIL: {test.__name__} — {e}")
        except Exception as e:
            failures.append(test.__name__)
            print(f"ERROR: {test.__name__} — {type(e).__name__}: {e}")

    print()
    print(f"{len(tests) - len(failures)}/{len(tests)} passed")
    if failures:
        sys.exit(1)
