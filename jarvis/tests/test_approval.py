"""
Tests for jarvis/approval.py — the Approval Gate (Stage I). Run directly:

    python3 jarvis/tests/test_approval.py

No capability registered anywhere in this codebase is above R0 today, so
several tests here register a temporary, test-only R2/R3 capability to
prove the gate actually fires - the same technique Stage H used to prove
intent-drift detection before any real drift existed structurally.
"""

import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import missions as msn  # noqa: E402
import workers  # noqa: E402
import plans as pl  # noqa: E402
import intent_lock as il  # noqa: E402
import supervisor as sup  # noqa: E402
import recovery as rec  # noqa: E402
import capabilities as caps  # noqa: E402
import approval as appr  # noqa: E402


def _fresh_db(tmp_path: Path):
    db_file = tmp_path / "test_jarvis_approval.db"
    msn.DB_PATH = db_file
    workers.DB_PATH = db_file
    pl.DB_PATH = db_file
    il.DB_PATH = db_file
    rec.DB_PATH = db_file
    appr.DB_PATH = db_file
    appr.init_db()  # cascades to msn.init_db()
    pl.init_db()
    workers.init_db()
    il.init_db()
    rec.init_db()


@contextmanager
def _temp_capability(cap_id, risk_level):
    """Registers a test-only capability at the given risk tier for the
    duration of the `with` block - never left behind for other tests."""
    caps.REGISTRY[cap_id] = caps.Capability(cap_id, "test capability", risk_level=risk_level)
    try:
        yield
    finally:
        caps.REGISTRY.pop(cap_id, None)


class _EchoWorker(workers.Worker):
    """A trivial, jarvis-internal, side-effect-free worker used only to
    prove the approval gate around a real dispatch - it never touches
    anything outside its own return value."""
    worker_id = "echo-worker"
    capabilities = ("test-r2-capability", "test-r3-capability")

    def execute(self, step, user_id):
        return {"echo": True}


def _mission_executing(user="user-1"):
    mission = msn.create_mission(user, "Test mission")
    msn.transition_mission(mission["mission_id"], user, "UNDERSTANDING")
    msn.transition_mission(mission["mission_id"], user, "PLANNING")
    msn.transition_mission(mission["mission_id"], user, "READY")
    msn.transition_mission(mission["mission_id"], user, "EXECUTING")
    return mission


def _ready_step(mission, user, worker_id, description="A step"):
    step = msn.create_step(mission["mission_id"], user, description, worker_id=worker_id)
    return msn.transition_step(step["step_id"], mission["mission_id"], user, "READY")


# --- 1-5: risk-tier defaults --------------------------------------------------

def test_r0_action_needs_no_approval():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        decision = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "READ", "R0")
        assert decision.decision == "ALLOWED"
        assert decision.approval_state == "NOT_REQUIRED"


def test_r1_action_needs_no_approval_by_default():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        decision = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "DRAFT", "R1")
        assert decision.decision == "ALLOWED"


def test_r2_action_requires_approval():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        decision = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert decision.decision == "APPROVAL_REQUIRED"
        assert decision.approval_state == "REQUIRED"


def test_r3_action_requires_approval():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        decision = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "DELETE", "R3")
        assert decision.decision == "APPROVAL_REQUIRED"


def test_r4_is_always_denied_and_never_requestable():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        decision = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "ADMINISTRATIVE", "R4")
        assert decision.decision == "DENIED"
        try:
            appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "ADMINISTRATIVE", "R4")
            assert False, "should have raised - there is no request path for R4"
        except appr.ApprovalValidationError:
            pass


# --- 6-9: full R2/R3 lifecycle -------------------------------------------------

def test_r2_approved_allows_execution():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert req.status == "REQUESTED"
        appr.approve(req.approval_id, "user-1")
        decision = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert decision.decision == "ALLOWED"


def test_r2_rejected_blocks_execution():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        appr.reject(req.approval_id, "user-1", reason="not now")
        decision = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert decision.decision == "DENIED"


def test_r3_approve_without_reason_is_rejected():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "DELETE", "R3")
        assert req.reason_required is True
        try:
            appr.approve(req.approval_id, "user-1")
            assert False, "should have raised"
        except appr.ApprovalValidationError:
            pass
        try:
            appr.approve(req.approval_id, "user-1", reason="   ")
            assert False, "whitespace-only reason must not count as a reason"
        except appr.ApprovalValidationError:
            pass


def test_r3_approve_with_reason_is_valid_and_recorded():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "DELETE", "R3")
        approved = appr.approve(req.approval_id, "user-1", reason="confirmed with client by phone")
        assert approved.status == "APPROVED"
        assert approved.reason == "confirmed with client by phone"
        assert approved.approved_by == "user-1"
        decision = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "DELETE", "R3")
        assert decision.decision == "ALLOWED"


# --- 10-12: transaction hard stop ----------------------------------------------

def test_financial_transaction_action_class_is_hard_blocked():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        try:
            appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "FINANCIAL_TRANSACTION", "R2")
            assert False, "should have raised"
        except appr.TransactionProhibitedError as e:
            assert e.error.code == "TRANSACTION_PROHIBITED"
            assert e.error.severity == "CRITICAL"
        try:
            appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "FINANCIAL_TRANSACTION", "R2")
            assert False, "should have raised"
        except appr.TransactionProhibitedError:
            pass
        assert appr.list_approvals_for_step(step["step_id"], "user-1") == [], "no approval record must ever be created for a prohibited action"


def test_transaction_shaped_step_text_is_hard_blocked_even_with_a_benign_action_class():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly", description="Transfer 5,000 rupees via UPI")
        try:
            appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
            assert False, "should have raised despite an innocuous action_class"
        except appr.TransactionProhibitedError:
            pass


# --- 13-15: expiration / cancellation ------------------------------------------

def test_expired_approval_is_invalid():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2",
                                     ttl_seconds=-1)  # already expired the instant it's created
        appr.approve(req.approval_id, "user-1")
        decision = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert decision.decision == "EXPIRED"


def test_cancelled_approval_is_invalid():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        appr.approve(req.approval_id, "user-1")
        appr.cancel_approval(req.approval_id, "user-1", reason="changed my mind")
        decision = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert decision.decision == "CANCELLED"


def test_cannot_reject_an_already_approved_request():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        appr.approve(req.approval_id, "user-1")
        try:
            appr.reject(req.approval_id, "user-1")
            assert False, "an APPROVED request cannot be rejected - state machine integrity"
        except appr.ApprovalValidationError:
            pass


# --- 16-23: binding / isolation / fingerprint sensitivity -----------------------

def test_cross_user_cannot_read_or_approve_anothers_request():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing(user="user-1")
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        try:
            appr.get_approval(req.approval_id, "user-2")
            assert False, "should have raised"
        except appr.ApprovalNotFoundError:
            pass
        try:
            appr.approve(req.approval_id, "user-2")
            assert False, "user-2 must never be able to approve user-1's request"
        except appr.ApprovalNotFoundError:
            pass


def test_wrong_mission_or_step_fails_via_existing_isolation():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission_a = _mission_executing(user="user-1")
        mission_b = _mission_executing(user="user-1")
        step_a = _ready_step(mission_a, "user-1", "jarvis-context-assembly")
        try:
            appr.evaluate(mission_b["mission_id"], step_a["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
            assert False, "a step must only ever be evaluated against its own mission"
        except msn.StepNotFoundError:
            pass


def test_approval_for_one_step_does_not_authorize_a_different_step():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step_a = _ready_step(mission, "user-1", "jarvis-context-assembly")
        step_b = _ready_step(mission, "user-1", "jarvis-context-assembly")
        req = appr.request_approval(mission["mission_id"], step_a["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        appr.approve(req.approval_id, "user-1")

        decision_a = appr.evaluate(mission["mission_id"], step_a["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        decision_b = appr.evaluate(mission["mission_id"], step_b["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert decision_a.decision == "ALLOWED"
        assert decision_b.decision == "APPROVAL_REQUIRED"


def test_changed_material_params_invalidates_prior_approval():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "COMMUNICATE", "R2",
                                     target="Raj", material_params={"message": "call me tomorrow"})
        appr.approve(req.approval_id, "user-1")

        same = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "COMMUNICATE", "R2",
                              target="Raj", material_params={"message": "call me tomorrow"})
        assert same.decision == "ALLOWED"

        changed = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "COMMUNICATE", "R2",
                                 target="Priya", material_params={"message": "call me tomorrow"})
        assert changed.decision == "APPROVAL_REQUIRED", "a different target must never reuse the same approval"


def test_changed_risk_level_invalidates_prior_approval():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "DELETE", "R2")
        appr.approve(req.approval_id, "user-1")
        decision = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "DELETE", "R3")
        assert decision.decision == "APPROVAL_REQUIRED"


def test_changed_action_class_invalidates_prior_approval():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "COMMUNICATE", "R2")
        appr.approve(req.approval_id, "user-1")
        decision = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "DELETE", "R2")
        assert decision.decision == "APPROVAL_REQUIRED"


def test_changed_tool_id_fallback_requires_its_own_approval():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2",
                                     tool_id="capability-a")
        appr.approve(req.approval_id, "user-1")
        decision = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2",
                                  tool_id="capability-b")
        assert decision.decision == "APPROVAL_REQUIRED", "a fallback to a different capability needs its own approval"


def test_changed_intent_version_invalidates_prior_approval():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        plan_v1 = pl.create_plan(mission["mission_id"], "user-1", "Original objective",
                                  [{"local_id": "s1", "description": "thing"}])
        il.lock_intent(mission["mission_id"], "user-1", plan_id=plan_v1["plan_id"])

        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        appr.approve(req.approval_id, "user-1")
        assert appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2").decision == "ALLOWED"

        plan_v2 = pl.create_replan(mission["mission_id"], "user-1", plan_v1["plan_id"], "Revised objective",
                                    [{"local_id": "s1", "description": "revised thing"}])
        il.lock_intent(mission["mission_id"], "user-1", plan_id=plan_v2["plan_id"])

        decision = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert decision.decision == "APPROVAL_REQUIRED", "a replanned intent must require fresh approval"


# --- 24-28: idempotency / concurrency / cancellation interaction ---------------

def test_duplicate_request_with_same_fingerprint_returns_the_same_record():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        first = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        second = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert first.approval_id == second.approval_id


def test_idempotency_key_prevents_duplicate_requests_even_with_different_params():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        first = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2",
                                       idempotency_key="req-x")
        second = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "COMMUNICATE", "R3",
                                        idempotency_key="req-x")
        assert first.approval_id == second.approval_id


def test_duplicate_approval_submission_is_idempotent():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        first = appr.approve(req.approval_id, "user-1")
        second = appr.approve(req.approval_id, "user-1")
        assert first.version == second.version, "repeated approval submission must not corrupt or re-bump state"


def test_concurrent_style_race_second_writer_cannot_corrupt_a_resolved_approval():
    """Simulates two writers reaching different verdicts on the same
    request: once one succeeds (APPROVED), a second call attempting a
    conflicting transition (REJECTED) must fail cleanly rather than
    silently overwrite it - the same guarantee proven the same way as
    every other stage's 'duplicate claim' test (sequential, not threaded,
    but exercising the identical state-machine guard)."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        appr.approve(req.approval_id, "user-1")
        try:
            appr.reject(req.approval_id, "user-1")
            assert False, "should have raised"
        except appr.ApprovalValidationError:
            pass


def test_mission_cancellation_invalidates_an_already_approved_request():
    """The core cancellation-wins guarantee: evaluate() re-checks LIVE
    mission/step status every time, so even a fully APPROVED request
    can never authorize execution once the mission is cancelled - no
    proactive cancellation-propagation into the approval ledger is
    required for this to hold."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        appr.approve(req.approval_id, "user-1")
        assert appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2").decision == "ALLOWED"

        msn.cancel_mission(mission["mission_id"], "user-1")

        decision = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert decision.decision == "CANCELLED", "a cancelled mission must invalidate even an already-approved request"


# --- 29-31: fail-closed --------------------------------------------------------

def test_unknown_action_class_fails_closed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        try:
            appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "NOT_A_REAL_CLASS", "R2")
            assert False, "should have raised"
        except appr.ApprovalValidationError:
            pass


def test_unknown_risk_level_fails_closed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        try:
            appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "READ", "R99")
            assert False, "should have raised"
        except appr.ApprovalValidationError:
            pass


def test_missing_approval_record_fails_closed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        try:
            appr.get_approval("does-not-exist", "user-1")
            assert False, "should have raised"
        except appr.ApprovalNotFoundError:
            pass


# --- 32-34: Worker Runtime boundary ---------------------------------------------

def test_worker_does_not_execute_without_approval():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        with _temp_capability("test-r2-capability", "R2"):
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = _ready_step(mission, "user-1", "test-r2-capability")
            try:
                workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                      action_class="EXTERNAL_SIDE_EFFECT")
                assert False, "should have raised - no approval exists yet"
            except workers.ApprovalRequiredError:
                pass
            blocked = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
            assert blocked["status"] == "WAITING_FOR_APPROVAL"
            assert workers.list_executions_for_step(step["step_id"]) == [], "the echo worker must never have actually run"


def test_worker_executes_only_after_valid_approval():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        with _temp_capability("test-r2-capability", "R2"):
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = _ready_step(mission, "user-1", "test-r2-capability")

            req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2",
                                         tool_id="test-r2-capability")
            appr.approve(req.approval_id, "user-1")

            result = workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                           action_class="EXTERNAL_SIDE_EFFECT")
            assert result.status == "SUCCEEDED"
            assert result.output == {"echo": True}


def test_resuming_a_waiting_for_approval_step_after_approval_is_granted():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        with _temp_capability("test-r2-capability", "R2"):
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = _ready_step(mission, "user-1", "test-r2-capability")

            try:
                workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                      action_class="EXTERNAL_SIDE_EFFECT")
            except workers.ApprovalRequiredError:
                pass
            assert msn.get_step(step["step_id"], mission["mission_id"], "user-1")["status"] == "WAITING_FOR_APPROVAL"

            req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2",
                                         tool_id="test-r2-capability")
            appr.approve(req.approval_id, "user-1")

            # Calling execute_step() again on the SAME (WAITING_FOR_APPROVAL)
            # step is the re-entry point - it must now succeed.
            result = workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                           action_class="EXTERNAL_SIDE_EFFECT")
            assert result.status == "SUCCEEDED"


# --- 35: Supervisor does not spin --------------------------------------------------

def test_supervisor_stops_cleanly_rather_than_spinning_on_a_pending_approval():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        with _temp_capability("test-r2-capability", "R2"):
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = msn.create_mission("user-1", "Needs approval")
            msn.create_step(mission["mission_id"], "user-1", "An R2 step", worker_id="test-r2-capability")

            supervisor = sup.Supervisor("user-1", registry=registry)
            # dispatch_step() is called without action_class by the
            # Supervisor's own default path - it will raise
            # WorkerValidationError (missing action_class), which the
            # dispatch loop does not special-case, so this proves the
            # *other* half of "must not spin": an uncaught, unexpected
            # exception surfaces immediately rather than looping forever.
            # (A real integration would pass action_class through Plan
            # materialization - out of scope for this stage.)
            started = time.monotonic()
            try:
                supervisor.supervise(mission["mission_id"])
            except workers.WorkerValidationError:
                pass
            elapsed = time.monotonic() - started
            assert elapsed < 5, "supervise() must return promptly, never spin"


def test_supervisor_does_not_spin_when_step_is_already_waiting_for_approval():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        with _temp_capability("test-r2-capability", "R2"):
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = _ready_step(mission, "user-1", "test-r2-capability")
            try:
                workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                      action_class="EXTERNAL_SIDE_EFFECT")
            except workers.ApprovalRequiredError:
                pass
            assert msn.get_step(step["step_id"], mission["mission_id"], "user-1")["status"] == "WAITING_FOR_APPROVAL"

            supervisor = sup.Supervisor("user-1", registry=registry)
            started = time.monotonic()
            result = supervisor.supervise(mission["mission_id"])
            elapsed = time.monotonic() - started

            assert elapsed < 5, "supervise() must not spin waiting on a pending approval"
            assert result["mission"]["status"] == "EXECUTING", "the mission stays resumable, not permanently blocked"
            event_names = [e["event"] for e in result["events"]]
            assert "SUPERVISOR_STOPPED" in event_names


# --- 36: Recovery cannot bypass approval --------------------------------------------

def test_recovery_retry_does_not_bypass_the_approval_gate():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        with _temp_capability("test-r2-capability", "R2"):
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = msn.create_step(mission["mission_id"], "user-1", "An R2 step that failed once",
                                    worker_id="test-r2-capability")
            step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "READY")
            step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "RUNNING")
            step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "FAILED", error={
                "code": "TOOL_TIMEOUT", "category": "TIMEOUT", "retryable": True,
            })

            attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1", registry=registry)
            assert attempt.decision == "RETRY"
            re_armed = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
            assert re_armed["status"] == "READY", "recovery only re-arms the ledger - it never executes anything itself"

            # The actual re-execution attempt still goes through the same
            # gated path - recovery's retry decision did not skip it.
            try:
                workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                      action_class="EXTERNAL_SIDE_EFFECT")
                assert False, "should have raised - no approval exists, recovery must not have bypassed the gate"
            except workers.ApprovalRequiredError:
                pass


# --- 37-39: decision object / audit-adjacent invariants ---------------------------

def test_approval_decision_carries_canonical_fields():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        decision = appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        d = decision.to_dict()
        for key in ("decision_id", "approval_id", "user_id", "mission_id", "step_id", "action_class",
                    "risk_level", "approval_state", "decision", "action_fingerprint", "intent_lock_version",
                    "reason_codes", "created_at"):
            assert key in d, f"missing canonical field: {key}"
        assert decision.decision in appr.DECISIONS


def test_evaluate_never_mutates_anything():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", "jarvis-context-assembly")
        before = len(appr.list_approvals_for_step(step["step_id"], "user-1"))
        appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        appr.evaluate(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        after = len(appr.list_approvals_for_step(step["step_id"], "user-1"))
        assert before == after == 0, "evaluate() must be purely read-only - it never creates a request on its own"


def test_approval_does_not_imply_verification():
    """Approving and even executing a step says nothing about whether
    Stage F later verifies its outcome - the two remain independent."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        with _temp_capability("test-r2-capability", "R2"):
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = _ready_step(mission, "user-1", "test-r2-capability")
            req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2",
                                         tool_id="test-r2-capability")
            appr.approve(req.approval_id, "user-1")
            workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                  action_class="EXTERNAL_SIDE_EFFECT")
            final_step = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
            assert final_step["status"] == "SUCCEEDED"
            assert final_step["verification"] is None, "execution succeeding must not itself count as verification"


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
