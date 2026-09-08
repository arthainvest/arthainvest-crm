"""
Tests for jarvis/verifier.py — the Verifier (Stage F). Run directly:

    python3 jarvis/tests/test_verifier.py

The central thing every one of these tests is ultimately checking: a
worker reporting SUCCEEDED is never, on its own, enough to call something
VERIFIED. Several tests deliberately corrupt the underlying data AFTER a
successful execution to prove the Verifier catches it via independent
evidence, not by re-trusting the worker's own report.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import memory as jm  # noqa: E402
import missions as msn  # noqa: E402
import workers  # noqa: E402
import supervisor as sup  # noqa: E402
import verifier as ver  # noqa: E402


def _fresh_db(tmp_path: Path):
    db_file = tmp_path / "test_jarvis_verifier.db"
    jm.DB_PATH = db_file
    msn.DB_PATH = db_file
    workers.DB_PATH = db_file
    jm.init_db()
    workers.init_db()


def _mission_to_verifying(steps_fn, user="user-1"):
    """Helper: build a mission via steps_fn(mission, user) -> None, run
    the Supervisor to completion, and return (mission_id, supervise_result).
    Asserts the mission actually reached VERIFYING (the precondition every
    verifier test needs) so a Supervisor regression fails loudly here."""
    mission = msn.create_mission(user, "Test mission")
    steps_fn(mission, user)
    supervisor = sup.Supervisor(user)
    result = supervisor.supervise(mission["mission_id"])
    assert result["mission"]["status"] == "VERIFYING", \
        f"test setup expected VERIFYING, got {result['mission']['status']}"
    return mission["mission_id"]


# --- Basic: VERIFIED via independent re-check --------------------------------

def test_context_step_that_matches_on_recheck_is_verified():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission_id = _mission_to_verifying(
            lambda m, u: msn.create_step(m["mission_id"], u, "Read context", worker_id="jarvis-context-assembly")
        )
        step = msn.list_steps(mission_id, "user-1")[0]
        result = ver.verify_step(mission_id, step["step_id"], "user-1")
        assert result.status == "VERIFIED"
        assert "fresh_resolved_entities" in result.evidence


def test_memory_write_step_confirmed_by_independent_db_query_is_verified():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission_id = _mission_to_verifying(
            lambda m, u: msn.create_step(
                m["mission_id"], u, "Remember a fact", worker_id="jarvis-memory-write",
                inputs={"memory_type": "decision", "content": "Verifiable content"},
            )
        )
        step = msn.list_steps(mission_id, "user-1")[0]
        result = ver.verify_step(mission_id, step["step_id"], "user-1")
        assert result.status == "VERIFIED"
        assert result.evidence["found"] is True
        assert result.evidence["stored_content"] == "Verifiable content"


# --- The central guarantee: worker success != verified success ----------------

def test_memory_write_worker_reported_success_but_row_was_deleted_verifies_as_failed():
    """The whole point of Stage F. The worker genuinely wrote the row and
    reported SUCCEEDED - that part is real and unchanged. But if the row
    is gone by the time the Verifier independently checks (simulating any
    scenario where the claimed outcome no longer matches reality), the
    Verifier must catch it, not rubber-stamp the worker's self-report."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission_id = _mission_to_verifying(
            lambda m, u: msn.create_step(
                m["mission_id"], u, "Remember a fact that will vanish", worker_id="jarvis-memory-write",
                inputs={"memory_type": "decision", "content": "Will be deleted before verification"},
            )
        )
        step = msn.list_steps(mission_id, "user-1")[0]
        memory_id = step["output"]["memory_id"]

        # Simulate the claimed outcome no longer matching reality.
        forgotten = jm.forget(memory_id)
        assert forgotten is True

        result = ver.verify_step(mission_id, step["step_id"], "user-1")
        assert result.status == "FAILED", "a worker's SUCCEEDED report must never be trusted over contradictory evidence"
        assert result.evidence["found"] is False


def test_memory_write_content_mismatch_is_detected_as_contradictory_evidence():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission_id = _mission_to_verifying(
            lambda m, u: msn.create_step(
                m["mission_id"], u, "Remember a fact", worker_id="jarvis-memory-write",
                inputs={"memory_type": "decision", "content": "Original content"},
            )
        )
        step = msn.list_steps(mission_id, "user-1")[0]
        memory_id = step["output"]["memory_id"]

        # Corrupt the record independently of the worker's own claim.
        jm.correct(memory_id, "Tampered content", source="test-corruption")

        result = ver.verify_step(mission_id, step["step_id"], "user-1")
        assert result.status == "FAILED"
        assert "does not match" in result.reasoning


# --- UNVERIFIABLE: no connector/browser assumptions ---------------------------

def test_unregistered_capability_verifies_as_unverifiable_not_assumed_success():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = msn.create_mission("user-1", "Mission with an unknown worker")
        step = msn.create_step(mission["mission_id"], "user-1", "Do something", worker_id="some-future-capability")
        step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "READY")
        step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "RUNNING")
        step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "SUCCEEDED", output={"claimed": "success"})

        result = ver.verify_step(mission["mission_id"], step["step_id"], "user-1")
        assert result.status == "UNVERIFIABLE"
        assert "no verification strategy" in result.reasoning


# --- Expected-output validation ------------------------------------------------

def test_expected_output_threshold_enforced_against_context_step():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission_id = _mission_to_verifying(
            lambda m, u: msn.create_step(
                m["mission_id"], u, "Read context expecting entities", worker_id="jarvis-context-assembly",
                expected_output={"min_resolved_entities": 5},  # unreachable - no memories were seeded
            )
        )
        step = msn.list_steps(mission_id, "user-1")[0]
        result = ver.verify_step(mission_id, step["step_id"], "user-1")
        assert result.status == "FAILED"
        assert "expected_output" in result.reasoning


# --- Step-status guard ------------------------------------------------------------

def test_verify_step_rejects_a_step_that_never_ran():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = msn.create_mission("user-1", "Not run yet")
        step = msn.create_step(mission["mission_id"], "user-1", "Untouched step", worker_id="jarvis-context-assembly")
        try:
            ver.verify_step(mission["mission_id"], step["step_id"], "user-1")
            assert False, "should have raised"
        except ver.StepNotVerifiableYetError as e:
            assert e.error.code == "VERIFICATION_UNAVAILABLE"


# --- Idempotent / restart-safe --------------------------------------------------

def test_verify_step_is_idempotent_second_call_returns_cached_result():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission_id = _mission_to_verifying(
            lambda m, u: msn.create_step(m["mission_id"], u, "Read context", worker_id="jarvis-context-assembly")
        )
        step = msn.list_steps(mission_id, "user-1")[0]
        first = ver.verify_step(mission_id, step["step_id"], "user-1")
        second = ver.verify_step(mission_id, step["step_id"], "user-1")
        assert first.verification_id == second.verification_id, "a second call must return the cached result, not re-verify"

        # A restart is nothing special here - get_verification() reads the
        # same persisted field a fresh process would see.
        recovered = ver.get_verification(step["step_id"])
        assert recovered["verification_id"] == first.verification_id


def test_force_true_recomputes_verification():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission_id = _mission_to_verifying(
            lambda m, u: msn.create_step(m["mission_id"], u, "Read context", worker_id="jarvis-context-assembly")
        )
        step = msn.list_steps(mission_id, "user-1")[0]
        first = ver.verify_step(mission_id, step["step_id"], "user-1")
        second = ver.verify_step(mission_id, step["step_id"], "user-1", force=True)
        assert first.verification_id != second.verification_id, "force=True must produce a fresh verification record"


# --- Mission-level integration ---------------------------------------------------

def test_verify_mission_all_verified_reaches_completed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission_id = _mission_to_verifying(
            lambda m, u: msn.create_step(m["mission_id"], u, "Read context", worker_id="jarvis-context-assembly")
        )
        outcome = ver.verify_mission(mission_id, "user-1")
        assert outcome["mission"]["status"] == "COMPLETED"
        assert outcome["mission"]["verification_state"] == "VERIFIED"
        assert len(outcome["results"]) == 1
        assert outcome["results"][0].status == "VERIFIED"


def test_verify_mission_with_a_failed_verification_reaches_failed_not_completed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission_id = _mission_to_verifying(
            lambda m, u: msn.create_step(
                m["mission_id"], u, "Remember, then get corrupted", worker_id="jarvis-memory-write",
                inputs={"memory_type": "decision", "content": "Will be corrupted"},
            )
        )
        step = msn.list_steps(mission_id, "user-1")[0]
        jm.forget(step["output"]["memory_id"])

        outcome = ver.verify_mission(mission_id, "user-1")
        assert outcome["mission"]["status"] == "FAILED", "a mission must never reach COMPLETED when evidence contradicts a claimed outcome"
        assert outcome["mission"]["verification_state"] == "FAILED"
        assert outcome["mission"]["error"]["code"] == "VERIFICATION_FAILED"


def test_verify_mission_with_unverifiable_step_reaches_partially_completed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = msn.create_mission("user-1", "Mixed mission")
        step = msn.create_step(mission["mission_id"], "user-1", "Unknown capability step", worker_id="some-future-capability")
        step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "READY")
        step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "RUNNING")
        msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "SUCCEEDED", output={"claimed": "done"})
        msn.transition_mission(mission["mission_id"], "user-1", "UNDERSTANDING")
        msn.transition_mission(mission["mission_id"], "user-1", "PLANNING")
        msn.transition_mission(mission["mission_id"], "user-1", "READY")
        msn.transition_mission(mission["mission_id"], "user-1", "EXECUTING")
        msn.transition_mission(mission["mission_id"], "user-1", "VERIFYING")

        outcome = ver.verify_mission(mission["mission_id"], "user-1")
        assert outcome["mission"]["status"] == "PARTIALLY_COMPLETED"
        assert outcome["results"][0].status == "UNVERIFIABLE"


def test_verify_mission_with_no_steps_is_vacuously_completed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = msn.create_mission("user-1", "Empty mission")
        supervisor = sup.Supervisor("user-1")
        result = supervisor.supervise(mission["mission_id"])
        assert result["mission"]["status"] == "VERIFYING"

        outcome = ver.verify_mission(mission["mission_id"], "user-1")
        assert outcome["mission"]["status"] == "COMPLETED"
        assert outcome["results"] == []


def test_verify_mission_requires_verifying_status():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = msn.create_mission("user-1", "Still fresh")
        try:
            ver.verify_mission(mission["mission_id"], "user-1")
            assert False, "should have raised"
        except ver.MissionNotVerifiableYetError as e:
            assert e.error.code == "VERIFICATION_UNAVAILABLE"


def test_verify_mission_cannot_be_called_twice():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission_id = _mission_to_verifying(
            lambda m, u: msn.create_step(m["mission_id"], u, "Read context", worker_id="jarvis-context-assembly")
        )
        first = ver.verify_mission(mission_id, "user-1")
        assert first["mission"]["status"] == "COMPLETED"
        try:
            ver.verify_mission(mission_id, "user-1")
            assert False, "COMPLETED is terminal - re-verifying must be refused, not silently reopened"
        except ver.MissionNotVerifiableYetError:
            pass


# --- User isolation --------------------------------------------------------------

def test_cross_user_cannot_verify_or_read_another_users_mission():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission_id = _mission_to_verifying(
            lambda m, u: msn.create_step(m["mission_id"], u, "Read context", worker_id="jarvis-context-assembly"),
            user="user-1",
        )
        try:
            ver.verify_mission(mission_id, "user-2")
            assert False, "should have raised"
        except msn.MissionNotFoundError:
            pass


# --- Transaction boundary: structurally unreachable, proven not asserted -------

def test_transaction_shaped_mission_never_reaches_a_verifiable_state():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = msn.create_mission("user-1", "Contains a prohibited step")
        msn.create_step(mission["mission_id"], "user-1", "Transfer 50,000 rupees via UPI")

        supervisor = sup.Supervisor("user-1")
        result = supervisor.supervise(mission["mission_id"])
        assert result["mission"]["status"] == "BLOCKED", "Stage E must divert a prohibited step to BLOCKED, never VERIFYING"

        try:
            ver.verify_mission(mission["mission_id"], "user-1")
            assert False, "the Verifier must never be reachable for a mission containing a prohibited step"
        except ver.MissionNotVerifiableYetError:
            pass  # correct - VERIFYING was never reached, so this is the only possible outcome


# --- Canonical error fields --------------------------------------------------------

def test_error_objects_carry_canonical_fields():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = msn.create_mission("user-1", "Fresh")
        try:
            ver.verify_mission(mission["mission_id"], "user-1")
            assert False
        except ver.MissionNotVerifiableYetError as e:
            err = e.error.to_dict()
            for key in ("error_id", "code", "category", "severity", "retryable",
                        "user_action_required", "message", "mission_id", "timestamp"):
                assert key in err, f"missing canonical error field: {key}"


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
