"""
Tests for jarvis/recovery.py — the Recovery Engine (Stage G). Run
directly:

    python3 jarvis/tests/test_recovery.py

Covers every required scenario from the Stage G authorization: retryable/
non-retryable classification, max-attempts exhaustion, worker
unavailability, fallback (valid and unavailable), deterministic replan
hand-off, cancellation winning over recovery, idempotency/restart-safety,
concurrent recovery conflicts, unknown external outcomes, verification
conflicts, the TRANSACTION_PROHIBITED hard stop, and cross-user isolation.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import missions as msn  # noqa: E402
import workers  # noqa: E402
import recovery as rec  # noqa: E402


def _fresh_db(tmp_path: Path):
    db_file = tmp_path / "test_jarvis_recovery.db"
    msn.DB_PATH = db_file
    workers.DB_PATH = db_file
    rec.DB_PATH = db_file
    rec.init_db()  # cascades to msn.init_db()


def _mission_executing(user="user-1"):
    mission = msn.create_mission(user, "Test mission")
    msn.transition_mission(mission["mission_id"], user, "UNDERSTANDING")
    msn.transition_mission(mission["mission_id"], user, "PLANNING")
    msn.transition_mission(mission["mission_id"], user, "READY")
    msn.transition_mission(mission["mission_id"], user, "EXECUTING")
    return mission


def _failed_step(mission, user, error, worker_id="jarvis-context-assembly", max_attempts=3, dependencies=None):
    step = msn.create_step(mission["mission_id"], user, "A step", worker_id=worker_id,
                            max_attempts=max_attempts, dependencies=dependencies)
    step = msn.transition_step(step["step_id"], mission["mission_id"], user, "READY")
    step = msn.transition_step(step["step_id"], mission["mission_id"], user, "RUNNING")
    step = msn.transition_step(step["step_id"], mission["mission_id"], user, "FAILED", error=error)
    return step


def _block_mission(mission, user):
    return msn.transition_mission(mission["mission_id"], user, "BLOCKED")


# --- Retryable failure -> bounded retry -----------------------------------------

def test_retryable_failure_is_retried_and_mission_resumes():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _failed_step(mission, "user-1", {"code": "TOOL_TIMEOUT", "category": "TIMEOUT", "retryable": True})
        _block_mission(mission, "user-1")

        attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1")
        assert attempt.status == "RETRYING"
        assert attempt.decision == "RETRY"

        updated_step = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
        assert updated_step["status"] == "READY"

        updated_mission = msn.get_mission(mission["mission_id"], "user-1")
        assert updated_mission["status"] == "EXECUTING", "a blocked mission must resume once a step is re-armed"


def test_timeout_recovery_specifically():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _failed_step(mission, "user-1", {"code": "TOOL_TIMEOUT", "category": "TIMEOUT", "retryable": True})
        attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1")
        assert attempt.status == "RETRYING"
        assert attempt.classification["error_category"] == "TIMEOUT"


# --- Non-retryable failure -> no retry --------------------------------------------

def test_non_retryable_validation_failure_is_not_retried():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _failed_step(mission, "user-1", {"code": "INVALID_INPUT", "category": "VALIDATION", "retryable": False})
        attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1")
        assert attempt.status == "RECOVERY_FAILED"
        assert attempt.decision == "NONE"

        unchanged = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
        assert unchanged["status"] == "FAILED", "a non-retryable step must stay FAILED, never silently reopened"


def test_authorization_denial_is_not_retried():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _failed_step(mission, "user-1", {"code": "ACTION_NOT_AUTHORIZED", "category": "AUTHORIZATION", "retryable": False})
        attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1")
        assert attempt.status == "RECOVERY_FAILED"


def test_authentication_failure_waits_for_user_rather_than_failing_outright():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _failed_step(mission, "user-1", {"code": "AUTH_EXPIRED", "category": "AUTHENTICATION", "retryable": False})
        attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1")
        assert attempt.status == "WAITING_FOR_USER"
        assert attempt.decision == "WAIT"


# --- Max attempts exhausted -> deterministic replan request -----------------------

def test_max_attempts_exhausted_with_no_fallback_requests_a_replan():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _failed_step(mission, "user-1", {"code": "TOOL_TIMEOUT", "category": "TIMEOUT", "retryable": True}, max_attempts=1)
        _block_mission(mission, "user-1")

        attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1")
        assert attempt.status == "REPLANNING"
        assert attempt.decision == "REPLAN"
        assert attempt.classification["attempts_remaining"] == 0

        updated_mission = msn.get_mission(mission["mission_id"], "user-1")
        assert updated_mission["status"] == "PLANNING", "a replan request must hand the mission off to PLANNING"


def test_deterministic_replan_request_is_structured_not_an_llm_call():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _failed_step(mission, "user-1", {"code": "TOOL_TIMEOUT", "category": "TIMEOUT", "retryable": True}, max_attempts=1)
        request = rec.request_replan(mission["mission_id"], step["step_id"], "user-1", {"note": "test"})
        assert request["mission_id"] == mission["mission_id"]
        assert request["step_id"] == step["step_id"]
        assert "classification" in request


# --- Worker unavailable -----------------------------------------------------------

def test_worker_unavailable_waits_when_no_fallback_registered():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _failed_step(mission, "user-1", {"code": "TOOL_NOT_FOUND", "category": "TOOL", "retryable": False},
                             worker_id="totally-unregistered-capability")
        attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1")
        assert attempt.status == "WAITING_FOR_USER"
        assert attempt.decision == "WAIT"


def test_worker_unavailable_but_became_available_since_is_retried():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        # jarvis-context-assembly IS registered in the default registry -
        # simulating "was unavailable at failure time, is available now."
        step = _failed_step(mission, "user-1", {"code": "TOOL_NOT_FOUND", "category": "TOOL", "retryable": False},
                             worker_id="jarvis-context-assembly")
        attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1")
        assert attempt.status == "RETRYING"


# --- Fallback: valid and unavailable ------------------------------------------------

def test_valid_fallback_is_used_when_original_worker_unavailable():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _failed_step(mission, "user-1", {"code": "TOOL_NOT_FOUND", "category": "TOOL", "retryable": False},
                             worker_id="totally-unregistered-capability")
        fallback_map = {"totally-unregistered-capability": ["jarvis-context-assembly"]}

        attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1", fallback_map=fallback_map)
        assert attempt.status == "FALLING_BACK"
        assert attempt.decision == "FALLBACK"
        assert attempt.classification["available_fallback"] == "jarvis-context-assembly"

        updated_step = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
        assert updated_step["status"] == "READY"
        assert updated_step["worker_id"] == "jarvis-context-assembly", "the fallback capability must actually be assigned to the step"


def test_fallback_is_never_invented_only_explicitly_registered_ones_are_used():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _failed_step(mission, "user-1", {"code": "TOOL_NOT_FOUND", "category": "TOOL", "retryable": False},
                             worker_id="totally-unregistered-capability")
        # No fallback_map provided at all - must never guess one.
        attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1")
        assert attempt.decision != "FALLBACK"
        assert attempt.classification["available_fallback"] is None


def test_unavailable_fallback_falls_through_to_recovery_failed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _failed_step(mission, "user-1", {"code": "INVALID_INPUT", "category": "VALIDATION", "retryable": False})
        # Fallback map exists but points at a capability nobody registered.
        fallback_map = {"jarvis-context-assembly": ["some-nonexistent-capability"]}
        attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1", fallback_map=fallback_map)
        assert attempt.status == "RECOVERY_FAILED"


# --- Recovery failure (generic) -----------------------------------------------------

def test_recovery_failure_leaves_step_and_mission_state_untouched():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _failed_step(mission, "user-1", {"code": "INVALID_INPUT", "category": "VALIDATION", "retryable": False})
        _block_mission(mission, "user-1")

        rec.recover_step(mission["mission_id"], step["step_id"], "user-1")

        assert msn.get_step(step["step_id"], mission["mission_id"], "user-1")["status"] == "FAILED"
        assert msn.get_mission(mission["mission_id"], "user-1")["status"] == "BLOCKED"


# --- Cancellation wins ----------------------------------------------------------------

def test_cancellation_wins_over_a_retryable_failure():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _failed_step(mission, "user-1", {"code": "TOOL_TIMEOUT", "category": "TIMEOUT", "retryable": True})
        msn.cancel_mission(mission["mission_id"], "user-1")

        attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1")
        assert attempt.status == "NOT_REQUIRED"
        assert attempt.decision == "NONE"

        unchanged = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
        assert unchanged["status"] == "FAILED", "a cancelled mission's failed step must never spontaneously restart"


# --- Idempotency / restart-safety --------------------------------------------------

def test_recovery_id_replay_returns_cached_attempt_without_reacting():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _failed_step(mission, "user-1", {"code": "TOOL_TIMEOUT", "category": "TIMEOUT", "retryable": True})

        first = rec.recover_step(mission["mission_id"], step["step_id"], "user-1", recovery_id="rec-1")
        assert first.status == "RETRYING"

        # The step is now READY, not FAILED - a naive re-classification
        # would behave differently. The cached replay must not care.
        second = rec.recover_step(mission["mission_id"], step["step_id"], "user-1", recovery_id="rec-1")
        assert second.recovery_id == first.recovery_id == "rec-1"
        assert second.status == first.status


# --- Concurrent recovery / state conflict -------------------------------------------

def test_concurrent_recovery_attempts_do_not_double_reopen_the_step():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _failed_step(mission, "user-1", {"code": "TOOL_TIMEOUT", "category": "TIMEOUT", "retryable": True})

        first = rec.recover_step(mission["mission_id"], step["step_id"], "user-1")
        assert first.status == "RETRYING"

        # A second, independent recovery call (different recovery_id) on
        # the same step - it's now READY, not FAILED, so classify() sees a
        # non-recoverable status and correctly declines rather than
        # attempting a second reopen.
        second = rec.recover_step(mission["mission_id"], step["step_id"], "user-1")
        assert second.status == "NOT_REQUIRED"
        assert second.decision == "NONE"


# --- Unknown external outcome -------------------------------------------------------

def test_unknown_outcome_never_auto_retries():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = msn.create_step(mission["mission_id"], "user-1", "Interrupted step", worker_id="jarvis-context-assembly")
        step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "READY")
        msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "RUNNING")
        # Simulate a real process restart mid-step, exactly as Stage B's
        # own reconcile_interrupted() would - it bypasses transition_step()'s
        # validator specifically for this maintenance sweep.
        msn.reconcile_interrupted(user_id="user-1")

        attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1")
        assert attempt.status == "WAITING_FOR_USER"
        assert attempt.decision == "WAIT"

        unchanged = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
        assert unchanged["status"] == "BLOCKED", "an UNKNOWN outcome must never be auto-retried"


# --- Verification failure (evidence contradicts a claimed success) ------------------

def test_verification_conflict_escalates_never_retries_a_succeeded_step():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = msn.create_step(mission["mission_id"], "user-1", "A step", worker_id="jarvis-memory-write")
        step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "READY")
        step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "RUNNING")
        step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "SUCCEEDED", output={"memory_id": 999})
        # Simulate Stage F's own verdict directly.
        msn.record_step_verification(step["step_id"], mission["mission_id"], "user-1", {
            "status": "FAILED", "reasoning": "row not found", "evidence": {"found": False},
        })

        attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1")
        assert attempt.status == "ESCALATING"
        assert attempt.decision == "ESCALATE"

        unchanged = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
        assert unchanged["status"] == "SUCCEEDED", "a SUCCEEDED step is immutable - recovery must never reopen it, only escalate"


# --- Dependency permanently blocked --------------------------------------------------

def test_dependency_permanently_failed_escalates_this_step():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        dep = _failed_step(mission, "user-1", {"code": "INVALID_INPUT", "category": "VALIDATION", "retryable": False})
        dependent = _failed_step(mission, "user-1", {"code": "TOOL_TIMEOUT", "category": "TIMEOUT", "retryable": True},
                                  dependencies=[dep["step_id"]])
        attempt = rec.recover_step(mission["mission_id"], dependent["step_id"], "user-1")
        assert attempt.status == "ESCALATING"
        assert attempt.classification["dependency_blocked_on"] == dep["step_id"]


# --- TRANSACTION_PROHIBITED hard stop ------------------------------------------------

def test_transaction_prohibited_is_a_terminal_hard_stop_no_matter_what():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = msn.create_step(mission["mission_id"], "user-1", "Transfer money", worker_id="jarvis-context-assembly")
        step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "READY")
        step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "BLOCKED", error={
            "code": "TRANSACTION_PROHIBITED", "category": "POLICY", "severity": "CRITICAL", "retryable": False,
        })

        # Even with an explicit fallback map available, TRANSACTION_PROHIBITED must win.
        fallback_map = {"jarvis-context-assembly": ["jarvis-memory-write"]}
        attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1", fallback_map=fallback_map)

        assert attempt.status == "RECOVERY_FAILED"
        assert attempt.decision == "NONE"
        assert "permanent policy boundary" in attempt.reasoning

        unchanged = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
        assert unchanged["status"] == "BLOCKED", "a prohibited step must never be reopened by any recovery path"


# --- Cross-user isolation -------------------------------------------------------------

def test_cross_user_cannot_recover_another_users_step():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing(user="user-1")
        step = _failed_step(mission, "user-1", {"code": "TOOL_TIMEOUT", "category": "TIMEOUT", "retryable": True})
        try:
            rec.recover_step(mission["mission_id"], step["step_id"], "user-2")
            assert False, "should have raised"
        except msn.MissionNotFoundError:
            pass


# --- Canonical error / attempt fields --------------------------------------------------

def test_recovery_attempt_carries_full_classification_and_reasoning():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _failed_step(mission, "user-1", {"code": "TOOL_TIMEOUT", "category": "TIMEOUT", "retryable": True})
        attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1")
        d = attempt.to_dict()
        for key in ("recovery_id", "mission_id", "step_id", "status", "decision",
                    "classification", "reasoning", "attempt_number", "created_at"):
            assert key in d, f"missing field: {key}"
        assert attempt.status in rec.RECOVERY_STATUSES


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
