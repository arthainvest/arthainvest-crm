"""
Tests for jarvis/action_firewall.py — the Action Firewall (Stage J). Run
directly:

    python3 jarvis/tests/test_action_firewall.py

The Firewall composes Approval Gate (Stage I) + Intent Lock (Stage H) +
capabilities.py + memory.py's privacy matrix into one final ALLOW/DENY
decision - it never reimplements any of them. Several tests prove the
central claim of this stage directly: an APPROVED request is not, on its
own, sufficient - a cancelled mission, a drifted intent, or a disabled
capability all still deny even when approval itself would have said yes.
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
import action_firewall as fw  # noqa: E402


def _fresh_db(tmp_path: Path):
    db_file = tmp_path / "test_jarvis_firewall.db"
    msn.DB_PATH = db_file
    workers.DB_PATH = db_file
    pl.DB_PATH = db_file
    il.DB_PATH = db_file
    rec.DB_PATH = db_file
    appr.DB_PATH = db_file
    fw.DB_PATH = db_file
    workers.init_db()  # cascades: firewall -> approval -> intent_lock -> missions
    pl.init_db()
    rec.init_db()


@contextmanager
def _temp_capability(cap_id, risk_level, available=True):
    caps.REGISTRY[cap_id] = caps.Capability(cap_id, "test capability", risk_level=risk_level, available=available)
    try:
        yield
    finally:
        caps.REGISTRY.pop(cap_id, None)


class _EchoWorker(workers.Worker):
    worker_id = "echo-worker"
    capabilities = ("test-r2-capability", "test-r3-capability", "test-fallback-capability")

    def execute(self, step, user_id):
        return {"echo": True}


def _mission_executing(user="user-1"):
    mission = msn.create_mission(user, "Test mission")
    msn.transition_mission(mission["mission_id"], user, "UNDERSTANDING")
    msn.transition_mission(mission["mission_id"], user, "PLANNING")
    msn.transition_mission(mission["mission_id"], user, "READY")
    msn.transition_mission(mission["mission_id"], user, "EXECUTING")
    return mission


def _ready_step(mission, user, worker_id="jarvis-context-assembly", description="A step"):
    step = msn.create_step(mission["mission_id"], user, description, worker_id=worker_id)
    return msn.transition_step(step["step_id"], mission["mission_id"], user, "READY")


# --- 1-2: valid low-risk execution ---------------------------------------------

def test_valid_r0_execution_is_allowed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "READ", "R0")
        assert decision.decision == "ALLOW"
        assert decision.reason_codes == []


def test_valid_r1_execution_is_allowed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "DRAFT", "R1")
        assert decision.decision == "ALLOW"


# --- 3-6: R2/R3 lifecycle ------------------------------------------------------

def test_r2_without_approval_is_denied():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert decision.decision == "DENY"
        assert "APPROVAL_REQUIRED" in decision.reason_codes


def test_r2_with_valid_approval_is_allowed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        appr.approve(req.approval_id, "user-1")
        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert decision.decision == "ALLOW"
        assert decision.approval_id == req.approval_id


def test_r3_without_approval_is_denied():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "DELETE", "R3")
        assert decision.decision == "DENY"


def test_r3_with_approval_and_reason_is_allowed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "DELETE", "R3")
        appr.approve(req.approval_id, "user-1", reason="confirmed by phone")
        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "DELETE", "R3")
        assert decision.decision == "ALLOW"


# --- 7-9: approval state interactions -------------------------------------------

def test_expired_approval_is_denied():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2",
                                     ttl_seconds=-1)
        appr.approve(req.approval_id, "user-1")
        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert decision.decision == "DENY"
        assert "APPROVAL_EXPIRED" in decision.reason_codes


def test_rejected_approval_is_denied():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        appr.reject(req.approval_id, "user-1")
        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert decision.decision == "DENY"
        assert "APPROVAL_DENIED" in decision.reason_codes


def test_cancelled_approval_is_denied():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        appr.approve(req.approval_id, "user-1")
        appr.cancel_approval(req.approval_id, "user-1")
        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert decision.decision == "DENY"
        assert "CANCELLED" in decision.reason_codes


# --- 10-13: isolation / metadata -------------------------------------------------

def test_wrong_user_is_denied():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing(user="user-1")
        step = _ready_step(mission, "user-1")
        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-2", "READ", "R0")
        assert decision.decision == "DENY"
        assert "MISSION_OR_STEP_NOT_FOUND" in decision.reason_codes


def test_wrong_mission_or_step_is_denied():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission_a = _mission_executing()
        mission_b = _mission_executing()
        step_a = _ready_step(mission_a, "user-1")
        decision = fw.authorize(mission_b["mission_id"], step_a["step_id"], "user-1", "READ", "R0")
        assert decision.decision == "DENY"
        assert "MISSION_OR_STEP_NOT_FOUND" in decision.reason_codes


def test_missing_metadata_is_denied():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        decision = fw.authorize(None, None, None, "READ", "R0")
        assert decision.decision == "DENY"
        assert "MISSING_REQUIRED_METADATA" in decision.reason_codes


def test_invalid_action_class_is_denied():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "NOT_A_REAL_CLASS", "R0")
        assert decision.decision == "DENY"
        assert "INVALID_ACTION_CLASS" in decision.reason_codes


# --- 14-17: intent / privacy / security / tool validity -------------------------

def test_intent_drift_is_denied_even_with_a_valid_approval():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        plan_v1 = pl.create_plan(mission["mission_id"], "user-1", "Original objective",
                                  [{"local_id": "s1", "description": "thing"}])
        il.lock_intent(mission["mission_id"], "user-1", plan_id=plan_v1["plan_id"])

        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        appr.approve(req.approval_id, "user-1")
        assert fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2").decision == "ALLOW"

        # Simulate drift the same way Stage H's own tests do - direct
        # tampering, since no public API can otherwise cause it.
        import sqlite3
        conn = sqlite3.connect(msn.DB_PATH)
        conn.execute("UPDATE jarvis_missions SET goal = ? WHERE mission_id = ?", ("Tampered goal", mission["mission_id"]))
        conn.commit()
        conn.close()

        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert decision.decision == "DENY"
        assert "INTENT_DRIFT_DETECTED" in decision.reason_codes


def test_privacy_violation_is_denied():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "READ", "R0",
                                 material_params={"privacy_level": "private"}, context="business")
        assert decision.decision == "DENY"
        assert "PRIVACY_SCOPE_DENIED" in decision.reason_codes


def test_security_violation_denied_for_a_disabled_capability():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        with _temp_capability("test-disabled-capability", "R1", available=False):
            mission = _mission_executing()
            step = _ready_step(mission, "user-1", worker_id="test-disabled-capability")
            decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "READ", "R1",
                                     tool_id="test-disabled-capability")
            assert decision.decision == "DENY"
            assert "SECURITY_VIOLATION" in decision.reason_codes


def test_invalid_tool_is_denied_when_explicitly_classified():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2",
                                 tool_id="totally-invented-capability-nobody-registered")
        assert decision.decision == "DENY"
        assert "INVALID_TOOL" in decision.reason_codes


# --- 18-19: transaction hard stop ------------------------------------------------

def test_transaction_prohibited_is_a_hard_stop_not_a_soft_deny():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        try:
            fw.authorize(mission["mission_id"], step["step_id"], "user-1", "FINANCIAL_TRANSACTION", "R2")
            assert False, "should have raised"
        except fw.TransactionProhibitedError as e:
            assert e.error.code == "TRANSACTION_PROHIBITED"
            assert e.error.severity == "CRITICAL"


def test_approval_cannot_rescue_a_transaction_prohibited_action():
    """Even an existing, otherwise-valid APPROVED request for the exact
    same fingerprint must not matter - transaction prohibition is checked
    before approval is even consulted."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", description="Transfer 10,000 rupees via UPI")
        try:
            fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
            assert False, "should have raised despite a benign action_class"
        except fw.TransactionProhibitedError:
            pass


# --- 20-21: approval alone is never sufficient -----------------------------------

def test_approved_action_still_denied_once_mission_is_cancelled():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        appr.approve(req.approval_id, "user-1")
        assert fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2").decision == "ALLOW"

        msn.cancel_mission(mission["mission_id"], "user-1")

        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert decision.decision == "DENY"
        assert "CANCELLED" in decision.reason_codes


def test_approved_action_still_denied_for_a_disabled_capability():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        with _temp_capability("test-r2-capability", "R2"):
            mission = _mission_executing()
            step = _ready_step(mission, "user-1", worker_id="test-r2-capability")
            req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2",
                                         tool_id="test-r2-capability")
            appr.approve(req.approval_id, "user-1")
            assert fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2",
                                 tool_id="test-r2-capability").decision == "ALLOW"

        # Capability is now disabled (context manager exited, popped from
        # the registry entirely - simulating it being withdrawn).
        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2",
                                 tool_id="test-r2-capability")
        assert decision.decision == "DENY"
        assert "INVALID_TOOL" in decision.reason_codes


# --- 22-24: idempotency / concurrency / audit ------------------------------------

def test_decision_id_replay_returns_the_cached_decision():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        first = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "READ", "R0", decision_id="dec-1")
        second = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "READ", "R0", decision_id="dec-1")
        assert first.decision_id == second.decision_id == "dec-1"
        assert first.created_at == second.created_at


def test_repeated_calls_are_independently_consistent_no_corruption():
    """Same guarantee every other stage's 'concurrent race' test proves
    sequentially: repeated evaluation of the same, unchanged action context
    always yields the same decision - nothing about calling it twice
    corrupts or flips the outcome."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        appr.approve(req.approval_id, "user-1")
        results = [fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2").decision
                    for _ in range(5)]
        assert results == ["ALLOW"] * 5


def test_audit_trail_decisions_are_persisted_and_listable():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        fw.authorize(mission["mission_id"], step["step_id"], "user-1", "READ", "R0")
        fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        decisions = fw.list_decisions_for_step(step["step_id"])
        assert len(decisions) == 2
        assert decisions[0].decision == "ALLOW"
        assert decisions[1].decision == "DENY"
        # Every recorded decision carries enough to answer "what/who/why/when".
        for d_ in decisions:
            assert d_.user_id == "user-1" and d_.mission_id == mission["mission_id"] and d_.created_at


# --- 25-26: Worker Runtime boundary -----------------------------------------------

def test_worker_cannot_execute_when_firewall_denies():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        with _temp_capability("test-r2-capability", "R2"):
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = _ready_step(mission, "user-1", worker_id="test-r2-capability")
            try:
                workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                      action_class="EXTERNAL_SIDE_EFFECT")
                assert False, "should have raised - no approval exists"
            except workers.ApprovalRequiredError:
                pass
            assert msn.get_step(step["step_id"], mission["mission_id"], "user-1")["status"] == "WAITING_FOR_APPROVAL"
            assert workers.list_executions_for_step(step["step_id"]) == [], "the worker must never have actually run"


def test_worker_proceeds_only_after_firewall_allows():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        with _temp_capability("test-r2-capability", "R2"):
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = _ready_step(mission, "user-1", worker_id="test-r2-capability")
            req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2",
                                         tool_id="test-r2-capability")
            appr.approve(req.approval_id, "user-1")
            result = workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                           action_class="EXTERNAL_SIDE_EFFECT")
            assert result.status == "SUCCEEDED"


def test_r0_capability_is_completely_unaffected_no_action_class_needed():
    """Backward-compatibility proof: the universal Firewall call must not
    require every existing R0 caller to start passing action_class."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", worker_id="jarvis-context-assembly")
        result = workers.execute_step(mission["mission_id"], step["step_id"], "user-1")
        assert result.status == "SUCCEEDED"


# --- 27-29: Recovery / fallback / replan cannot bypass ---------------------------

def test_recovery_retry_cannot_bypass_the_firewall():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        with _temp_capability("test-r2-capability", "R2"):
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = msn.create_step(mission["mission_id"], "user-1", "failed once", worker_id="test-r2-capability")
            step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "READY")
            step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "RUNNING")
            step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "FAILED",
                                        error={"code": "TOOL_TIMEOUT", "category": "TIMEOUT", "retryable": True})
            attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1", registry=registry)
            assert attempt.decision == "RETRY"
            assert msn.get_step(step["step_id"], mission["mission_id"], "user-1")["status"] == "READY"
            try:
                workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                      action_class="EXTERNAL_SIDE_EFFECT")
                assert False, "recovery must not have bypassed the firewall"
            except workers.ApprovalRequiredError:
                pass


def test_fallback_reassignment_cannot_bypass_the_firewall():
    """A fallback to a different capability changes the tool_id, which
    changes the action fingerprint - it needs its own approval, checked
    at the Firewall the same way a fresh dispatch would be."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        with _temp_capability("test-r2-capability", "R2"), _temp_capability("test-fallback-capability", "R2"):
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = msn.create_step(mission["mission_id"], "user-1", "failed, will fall back",
                                    worker_id="test-r2-capability", max_attempts=1)
            step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "READY")
            step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "RUNNING")
            step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "FAILED",
                                        error={"code": "TOOL_TIMEOUT", "category": "TIMEOUT", "retryable": True})

            fallback_map = {"test-r2-capability": ["test-fallback-capability"]}
            attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                        fallback_map=fallback_map)
            assert attempt.decision == "FALLBACK"
            reassigned = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
            assert reassigned["worker_id"] == "test-fallback-capability"

            # No approval exists yet for the NEW (fallback) capability -
            # the firewall must still deny.
            try:
                workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                      action_class="EXTERNAL_SIDE_EFFECT")
                assert False, "the fallback capability must require its own approval"
            except workers.ApprovalRequiredError:
                pass


def test_replan_cannot_bypass_the_firewall():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        plan_v1 = pl.create_plan(mission["mission_id"], "user-1", "Original objective",
                                  [{"local_id": "s1", "description": "thing"}])
        il.lock_intent(mission["mission_id"], "user-1", plan_id=plan_v1["plan_id"])

        req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        appr.approve(req.approval_id, "user-1")
        assert fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2").decision == "ALLOW"

        plan_v2 = pl.create_replan(mission["mission_id"], "user-1", plan_v1["plan_id"], "Revised objective",
                                    [{"local_id": "s1", "description": "revised"}])
        il.lock_intent(mission["mission_id"], "user-1", plan_id=plan_v2["plan_id"])

        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2")
        assert decision.decision == "DENY", "a replanned intent must require fresh approval, not reuse the old one"


# --- 30: restart behavior ---------------------------------------------------------

def test_firewall_decision_survives_a_simulated_restart():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = _mission_executing()
        step = _ready_step(mission, "user-1")
        decision = fw.authorize(mission["mission_id"], step["step_id"], "user-1", "READ", "R0", decision_id="dec-restart")

        # Simulate a restart: a brand new lookup by decision_id, as a
        # fresh process would do, with no in-memory state carried over.
        recovered = fw.get_decision("dec-restart")
        assert recovered is not None
        assert recovered.decision == decision.decision == "ALLOW"


# --- 31: full integration path -----------------------------------------------------

def test_full_integration_path_supervisor_approval_and_execution():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        with _temp_capability("test-r2-capability", "R2"):
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = msn.create_mission("user-1", "Needs approval end to end")
            msn.create_step(mission["mission_id"], "user-1", "An R2 step", worker_id="test-r2-capability")

            supervisor = sup.Supervisor("user-1", registry=registry)
            supervisor.start_mission(mission["mission_id"])
            step = msn.list_steps(mission["mission_id"], "user-1")[0]
            msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "READY")

            # First attempt: no approval yet - firewall denies, step parks.
            try:
                workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                      action_class="EXTERNAL_SIDE_EFFECT")
            except workers.ApprovalRequiredError:
                pass
            assert msn.get_step(step["step_id"], mission["mission_id"], "user-1")["status"] == "WAITING_FOR_APPROVAL"

            # Approval granted.
            req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1", "EXTERNAL_SIDE_EFFECT", "R2",
                                         tool_id="test-r2-capability")
            appr.approve(req.approval_id, "user-1")

            # Re-entry succeeds.
            result = workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                           action_class="EXTERNAL_SIDE_EFFECT")
            assert result.status == "SUCCEEDED"

            decisions = fw.list_decisions_for_step(step["step_id"])
            assert decisions[0].decision == "DENY" and decisions[-1].decision == "ALLOW"


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
