"""
Tests for jarvis/supervisor.py — the Mission Supervisor (Stage E). Run
directly:

    python3 jarvis/tests/test_supervisor.py

Covers: basic single/multi-step execution, dependency ordering, batch-
bounded scheduling, completion hand-off (EXECUTING -> VERIFYING, never
COMPLETED), failure/blocked detection, cancellation, concurrency
(duplicate claim), idempotency, restart reconciliation, worker
unavailability, and transaction safety through the full Supervisor ->
Worker -> Policy path including a bypass attempt.
"""

import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import memory as jm  # noqa: E402
import missions as msn  # noqa: E402
import workers  # noqa: E402
import supervisor as sup  # noqa: E402


def _fresh_db(tmp_path: Path):
    db_file = tmp_path / "test_jarvis_supervisor.db"
    jm.DB_PATH = db_file
    msn.DB_PATH = db_file
    workers.DB_PATH = db_file
    jm.init_db()
    workers.init_db()  # cascades to msn.init_db()


def _mission(user="user-1", goal="Test mission"):
    return msn.create_mission(user, goal)


def _add_step(mission, user, description, worker_id="jarvis-context-assembly", dependencies=None, inputs=None):
    return msn.create_step(mission["mission_id"], user, description, worker_id=worker_id,
                            dependencies=dependencies, inputs=inputs)


# --- Basic -----------------------------------------------------------------

def test_basic_single_step_mission_reaches_verifying():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission()
        _add_step(mission, "user-1", "Do one thing")

        supervisor = sup.Supervisor("user-1")
        result = supervisor.supervise(mission["mission_id"])

        assert result["mission"]["status"] == "VERIFYING", "all steps succeeded - hand off to Verifier, never self-declare COMPLETED"
        event_names = [e["event"] for e in result["events"]]
        assert "MISSION_STARTED" in event_names
        assert "STEP_DISPATCHED" in event_names
        assert "STEP_COMPLETED" in event_names


def test_basic_mission_starts_from_created_through_the_legal_path():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission()
        assert mission["status"] == "CREATED"
        _add_step(mission, "user-1", "One step")
        supervisor = sup.Supervisor("user-1")
        started = supervisor.start_mission(mission["mission_id"])
        assert started["status"] == "EXECUTING"


# --- Dependencies ------------------------------------------------------------

def test_dependency_chain_executes_in_order_a_then_b_then_c():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission()
        a = _add_step(mission, "user-1", "Step A")
        b = _add_step(mission, "user-1", "Step B", dependencies=[a["step_id"]])
        c = _add_step(mission, "user-1", "Step C", dependencies=[b["step_id"]])

        supervisor = sup.Supervisor("user-1")
        result = supervisor.supervise(mission["mission_id"])

        assert result["mission"]["status"] == "VERIFYING"
        final_a = msn.get_step(a["step_id"], mission["mission_id"], "user-1")
        final_b = msn.get_step(b["step_id"], mission["mission_id"], "user-1")
        final_c = msn.get_step(c["step_id"], mission["mission_id"], "user-1")
        assert final_a["status"] == final_b["status"] == final_c["status"] == "SUCCEEDED"
        # B must not have started before A completed, C not before B.
        assert final_a["completed_at"] <= final_b["started_at"]
        assert final_b["completed_at"] <= final_c["started_at"]


# --- Bounded batch scheduling --------------------------------------------------

def test_independent_steps_are_all_completed_within_batch_bound():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission()
        for i in range(7):
            _add_step(mission, "user-1", f"Independent step {i}")

        supervisor = sup.Supervisor("user-1", batch_size=2)  # deliberately smaller than the step count
        result = supervisor.supervise(mission["mission_id"])

        assert result["mission"]["status"] == "VERIFYING"
        steps = msn.list_steps(mission["mission_id"], "user-1")
        assert all(s["status"] == "SUCCEEDED" for s in steps)
        assert len(steps) == 7


# --- Failure / Blocked ---------------------------------------------------------

def test_failed_worker_does_not_silently_become_success():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))

        class BrokenWorker(workers.Worker):
            worker_id = "broken-worker"
            capabilities = ("broken-capability",)

            def execute(self, step):
                raise RuntimeError("nope")

        registry = workers.WorkerRegistry()
        registry.register_worker(BrokenWorker())

        mission = _mission()
        _add_step(mission, "user-1", "Will fail", worker_id="broken-capability")

        supervisor = sup.Supervisor("user-1", registry=registry)
        result = supervisor.supervise(mission["mission_id"])

        assert result["mission"]["status"] == "BLOCKED", "a failed step must never let the mission reach VERIFYING as if nothing went wrong"
        event_names = [e["event"] for e in result["events"]]
        assert "STEP_FAILED" in event_names
        assert "MISSION_BLOCKED" in event_names


def test_a_dependent_of_a_permanently_blocked_step_does_not_spin_forever():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission()
        blocked_dep = _add_step(mission, "user-1", "Will be unavailable", worker_id="gmail-read")
        dependent = _add_step(mission, "user-1", "Depends on the blocked one", dependencies=[blocked_dep["step_id"]])

        supervisor = sup.Supervisor("user-1")
        result = supervisor.supervise(mission["mission_id"])

        assert result["mission"]["status"] == "BLOCKED"
        final_dependent = msn.get_step(dependent["step_id"], mission["mission_id"], "user-1")
        assert final_dependent["status"] == "PENDING", "the dependent step must stay PENDING forever, never silently promoted"


def test_worker_unavailable_blocks_the_step_not_an_infinite_loop():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission()
        _add_step(mission, "user-1", "Needs a capability that doesn't exist", worker_id="totally-unregistered")

        supervisor = sup.Supervisor("user-1")
        started = time.monotonic()
        result = supervisor.supervise(mission["mission_id"])
        elapsed = time.monotonic() - started

        assert elapsed < 5, "supervise() must terminate promptly, not spin"
        assert result["mission"]["status"] == "BLOCKED"


# --- Cancellation ---------------------------------------------------------------

def test_cancel_mission_stops_new_dispatch_and_marks_pending_steps_cancelled():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission()
        _add_step(mission, "user-1", "One")
        _add_step(mission, "user-1", "Two")

        supervisor = sup.Supervisor("user-1")
        supervisor.start_mission(mission["mission_id"])
        cancelled = supervisor.cancel_mission(mission["mission_id"], reason="user changed mind")

        assert cancelled["status"] == "CANCELLED"
        assert supervisor._stopped is True

        # CANCELLED is terminal - supervise() must refuse to resume it
        # rather than silently reopening a cancelled mission.
        try:
            sup.Supervisor("user-1").supervise(mission["mission_id"])
            assert False, "should have raised - a cancelled mission must never be resupervised"
        except sup.SupervisorInvalidStateError:
            pass

        for step in msn.list_steps(mission["mission_id"], "user-1"):
            assert step["status"] in ("CANCELLED",) or step["status"] in msn.TERMINAL_STEP_STATUSES


# --- Concurrency: duplicate claim -----------------------------------------------

def test_two_supervisors_cannot_both_execute_the_same_step():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission()
        step = _add_step(mission, "user-1", "Only one claimant allowed")
        msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "READY")

        # Simulate supervisor B already having claimed it.
        msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "RUNNING")

        supervisor_a = sup.Supervisor("user-1")
        try:
            supervisor_a.dispatch_step(mission["mission_id"], step["step_id"])
            assert False, "should have raised - the step is already RUNNING"
        except workers.StepNotExecutableError:
            pass


# --- Idempotency -----------------------------------------------------------------

def test_supervise_called_twice_on_an_already_verifying_mission_does_not_redispatch():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission()
        _add_step(mission, "user-1", "One step")

        supervisor = sup.Supervisor("user-1")
        first = supervisor.supervise(mission["mission_id"])
        assert first["mission"]["status"] == "VERIFYING"

        steps_after_first = msn.list_steps(mission["mission_id"], "user-1")
        assert len(steps_after_first) == 1

        # VERIFYING is terminal-ish for this Supervisor (no edge it owns
        # leads out of it) - a fresh supervise() call must not try to
        # restart the mission or duplicate the step.
        try:
            supervisor2 = sup.Supervisor("user-1")
            supervisor2.supervise(mission["mission_id"])
            assert False, "should have raised - VERIFYING is not a resumable status for this stage"
        except sup.SupervisorInvalidStateError:
            pass
        assert len(msn.list_steps(mission["mission_id"], "user-1")) == 1, "no duplicate step was created"


# --- Restart / reconciliation ------------------------------------------------------

def test_reconcile_mission_recovers_interrupted_state_before_resuming():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission()
        step = _add_step(mission, "user-1", "Interrupted step")
        msn.transition_mission(mission["mission_id"], "user-1", "UNDERSTANDING")
        msn.transition_mission(mission["mission_id"], "user-1", "PLANNING")
        msn.transition_mission(mission["mission_id"], "user-1", "READY")
        msn.transition_mission(mission["mission_id"], "user-1", "EXECUTING")
        msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "READY")
        msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "RUNNING")
        # Simulate a crash here - process dies mid-step.

        supervisor = sup.Supervisor("user-1")
        reconciled = supervisor.reconcile_mission(mission["mission_id"])
        assert mission["mission_id"] in reconciled["missions"]
        assert step["step_id"] in reconciled["steps"]

        recovered_mission = msn.get_mission(mission["mission_id"], "user-1")
        assert recovered_mission["status"] == "BLOCKED"
        assert recovered_mission["verification_state"] == "UNKNOWN"


# --- Transaction safety, through the full Supervisor -> Worker -> Policy path ------

def test_transaction_shaped_step_is_blocked_through_supervisor_with_zero_execution():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission()
        _add_step(mission, "user-1", "Transfer 5,000 rupees via UPI to settle the account")

        supervisor = sup.Supervisor("user-1")
        result = supervisor.supervise(mission["mission_id"])

        assert result["mission"]["status"] == "BLOCKED"
        event_names = [e["event"] for e in result["events"]]
        assert "STEP_BLOCKED" in event_names
        blocked_events = [e for e in result["events"] if e["event"] == "STEP_BLOCKED"]
        assert any(e.get("reason") == "transaction_prohibited" for e in blocked_events)

        steps = msn.list_steps(mission["mission_id"], "user-1")
        assert steps[0]["status"] == "BLOCKED"
        assert steps[0]["attempt_count"] == 0, "a prohibited step must never be claimed - zero execution"
        assert workers.list_executions_for_step(steps[0]["step_id"]) == []


def test_transaction_bypass_via_indirect_phrasing_is_still_blocked_end_to_end():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission()
        _add_step(mission, "user-1", "Please redeem the client's mutual fund units")

        supervisor = sup.Supervisor("user-1")
        result = supervisor.supervise(mission["mission_id"])

        assert result["mission"]["status"] == "BLOCKED"


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
