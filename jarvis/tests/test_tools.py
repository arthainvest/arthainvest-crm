"""
Tests for jarvis/tools.py — the Tool Registry (Stage K). Run directly:

    python3 jarvis/tests/test_tools.py

Capability ≠ Worker ≠ Tool. Several tests exist specifically to prove the
central claims of this stage: registration is never authorization (a
registered, even VERIFIED, tool still has to clear Approval Gate + Action
Firewall); a valid approval alone is not sufficient once a tool is
disabled or materially changed; UNKNOWN/BLOCKED trust can never execute;
and a pre-existing test/internal capability_id with no registered Tool is
completely unaffected by any of this.
"""

import sys
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import missions as msn  # noqa: E402
import workers  # noqa: E402
import plans as pl  # noqa: E402
import intent_lock as il  # noqa: E402
import recovery as rec  # noqa: E402
import capabilities as caps  # noqa: E402
import approval as appr  # noqa: E402
import action_firewall as fw  # noqa: E402
import tools as tr  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _fresh_tools_db(tmp_path: Path):
    """For tests that only exercise tools.py in isolation - no mission/
    approval/firewall stack needed."""
    db_file = tmp_path / "test_jarvis_tools.db"
    tr.DB_PATH = db_file
    tr.init_db()


def _fresh_full_db(tmp_path: Path):
    """For integration tests - same pattern test_action_firewall.py uses:
    workers.init_db() cascades to tools/firewall/approval/intent_lock/
    missions; plans and recovery still need their own init_db()."""
    db_file = tmp_path / "test_jarvis_tools_integration.db"
    msn.DB_PATH = db_file
    workers.DB_PATH = db_file
    pl.DB_PATH = db_file
    il.DB_PATH = db_file
    rec.DB_PATH = db_file
    appr.DB_PATH = db_file
    fw.DB_PATH = db_file
    tr.DB_PATH = db_file
    workers.init_db()  # cascades: tools (own) + firewall -> approval -> intent_lock -> missions
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
    worker_id = "tk-echo-worker"
    capabilities = (
        "test-tk-cap", "test-tk-r2", "test-tk-r2b", "test-tk-r2c", "test-tk-r2d",
        "test-tk-recover", "test-tk-fallback-a", "test-tk-fallback-b",
    )

    def execute(self, step, user_id):
        return {"echo": True}


class _CountingWorker(workers.Worker):
    worker_id = "counting-worker"
    capabilities = ("test-tk-r0", "test-tk-r0b")

    def __init__(self):
        self.call_count = 0

    def execute(self, step, user_id):
        self.call_count += 1
        return {"ok": True}


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


def _valid_fields(**overrides):
    base = dict(
        tool_id="tool-context-assembly", name="Context Assembly Tool",
        description="Wraps the Context Engine's assemble_context() call.",
        capability_id="jarvis-context-assembly", worker_id="context-worker",
        action_class="READ", risk_level="R0",
        required_permissions=("read:context",), required_privacy_scopes=("business",),
        transaction_capable=False, security_sensitive=False, side_effect_class="INTERNAL",
        verification_required=False, idempotent=True, cancellable=False,
        connector_id=None, trust_level="VERIFIED", enabled=True,
    )
    base.update(overrides)
    return base


# --- 1-2: register / duplicate -------------------------------------------------

def test_register_valid_tool():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        tool = tr.register_tool(**_valid_fields())
        assert tool.tool_id == "tool-context-assembly"
        assert tool.version == 1
        assert tool.schema_hash


def test_duplicate_registration_is_idempotent_no_op():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        t1 = tr.register_tool(**_valid_fields())
        t2 = tr.register_tool(**_valid_fields())
        assert t1.version == t2.version == 1
        assert len(tr.list_tool_versions("tool-context-assembly")) == 1


# --- 3-7: metadata validation ---------------------------------------------------

def test_invalid_metadata_rejected():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        try:
            tr.register_tool(**_valid_fields(name=""))
            assert False
        except tr.ToolValidationError as e:
            assert any(v["field"] == "name" for v in e.error.metadata["violations"])
        assert tr.get_tool("tool-context-assembly") is None


def test_missing_action_class_rejected():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        try:
            tr.register_tool(**_valid_fields(action_class=None))
            assert False
        except tr.ToolValidationError as e:
            assert any(v["type"] == "MISSING_ACTION_CLASS" for v in e.error.metadata["violations"])


def test_invalid_risk_level_rejected():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        try:
            tr.register_tool(**_valid_fields(risk_level="R9"))
            assert False
        except tr.ToolValidationError as e:
            assert any(v["type"] == "INVALID_RISK_LEVEL" for v in e.error.metadata["violations"])


def test_invalid_capability_format_rejected():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        try:
            tr.register_tool(**_valid_fields(capability_id=""))
            assert False
        except tr.ToolValidationError as e:
            assert any(v["field"] == "capability_id" for v in e.error.metadata["violations"])


def test_missing_worker_rejected():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        try:
            tr.register_tool(**_valid_fields(worker_id=None))
            assert False
        except tr.ToolValidationError as e:
            assert any(v["field"] == "worker_id" for v in e.error.metadata["violations"])


# --- 8: disabled tool ------------------------------------------------------------

def test_disabled_tool_is_unavailable():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        tr.register_tool(**_valid_fields())
        tr.unregister_tool("tool-context-assembly", reason="retiring")
        avail = tr.validate_tool_availability("tool-context-assembly")
        assert not avail["available"]
        assert "TOOL_DISABLED" in avail["reason_codes"]


# --- 9-12: lookup / listing ------------------------------------------------------

def test_get_tool_lookup():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        tr.register_tool(**_valid_fields())
        assert tr.get_tool("tool-context-assembly").tool_id == "tool-context-assembly"
        assert tr.get_tool("does-not-exist") is None


def test_lookup_by_capability():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        tr.register_tool(**_valid_fields())
        found = tr.lookup_by_capability("jarvis-context-assembly")
        assert len(found) == 1 and found[0].tool_id == "tool-context-assembly"
        assert tr.lookup_by_capability("unknown-cap") == []


def test_lookup_by_worker():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        tr.register_tool(**_valid_fields())
        found = tr.lookup_by_worker("context-worker")
        assert len(found) == 1 and found[0].tool_id == "tool-context-assembly"
        assert tr.lookup_by_worker("unknown-worker") == []


def test_list_tools_is_deterministic():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        tr.register_tool(**_valid_fields(tool_id="tool-b", capability_id="cap-b", worker_id="worker-b"))
        tr.register_tool(**_valid_fields(tool_id="tool-a", capability_id="cap-a", worker_id="worker-a"))
        ids = [t.tool_id for t in tr.list_tools()]
        assert ids == ["tool-a", "tool-b"]


# --- 13-14: versioning / schema change -------------------------------------------

def test_material_change_bumps_version():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        v1 = tr.register_tool(**_valid_fields())
        v2 = tr.register_tool(**_valid_fields(risk_level="R2"))
        assert v2.version == 2
        assert v2.schema_hash != v1.schema_hash
        assert tr.get_tool_version("tool-context-assembly", 1).risk_level == "R0"
        assert tr.get_tool("tool-context-assembly").risk_level == "R2"


def test_schema_change_preserves_old_version_history():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        tr.register_tool(**_valid_fields())
        tr.register_tool(**_valid_fields(capability_id="jarvis-context-assembly-v2"))
        versions = tr.list_tool_versions("tool-context-assembly")
        assert [v.version for v in versions] == [1, 2]
        assert versions[0].capability_id == "jarvis-context-assembly"
        assert versions[1].capability_id == "jarvis-context-assembly-v2"


def test_administrative_only_change_does_not_bump_version():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        tr.register_tool(**_valid_fields())
        updated = tr.register_tool(**_valid_fields(description="a new, better description"))
        assert updated.version == 1
        assert updated.description == "a new, better description"


# --- 15-19: trust levels ---------------------------------------------------------

def test_trust_level_verified_is_executable():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        tr.register_tool(**_valid_fields(trust_level="VERIFIED"))
        assert tr.validate_tool_availability("tool-context-assembly")["available"]


def test_trust_level_trusted_is_executable():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        tr.register_tool(**_valid_fields(trust_level="TRUSTED"))
        assert tr.validate_tool_availability("tool-context-assembly")["available"]


def test_trust_level_community_is_executable():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        tr.register_tool(**_valid_fields(trust_level="COMMUNITY"))
        assert tr.validate_tool_availability("tool-context-assembly")["available"]


def test_trust_level_unknown_is_blocked():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        tr.register_tool(**_valid_fields(trust_level="UNKNOWN"))
        avail = tr.validate_tool_availability("tool-context-assembly")
        assert not avail["available"]
        assert "TRUST_LEVEL_NOT_EXECUTABLE" in avail["reason_codes"]


def test_trust_level_blocked_is_blocked():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        tr.register_tool(**_valid_fields(trust_level="BLOCKED"))
        avail = tr.validate_tool_availability("tool-context-assembly")
        assert not avail["available"]
        assert "TRUST_LEVEL_NOT_EXECUTABLE" in avail["reason_codes"]


def test_trust_level_defaults_to_unknown_not_inferred_as_trustworthy():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        fields = _valid_fields()
        del fields["trust_level"]
        tool = tr.register_tool(**fields)
        assert tool.trust_level == "UNKNOWN"
        assert not tr.validate_tool_availability("tool-context-assembly")["available"]


# --- 20-21: transaction prohibition ----------------------------------------------

def test_transaction_capable_tool_rejected_at_registration():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        try:
            tr.register_tool(**_valid_fields(tool_id="tool-tx", transaction_capable=True))
            assert False
        except tr.ToolTransactionProhibitedError:
            pass
        assert tr.get_tool("tool-tx") is None


def test_transaction_shaped_text_rejected_at_registration():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        try:
            tr.register_tool(**_valid_fields(tool_id="tool-tx2", description="transfer money between accounts"))
            assert False
        except tr.ToolTransactionProhibitedError:
            pass
        assert tr.get_tool("tool-tx2") is None


def test_financial_transaction_action_class_rejected_at_registration():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        try:
            tr.register_tool(**_valid_fields(tool_id="tool-tx3", action_class="FINANCIAL_TRANSACTION"))
            assert False
        except tr.ToolTransactionProhibitedError:
            pass
        assert tr.get_tool("tool-tx3") is None


def test_transaction_prohibition_is_re_checked_at_use_defense_in_depth():
    """Proves this isn't merely 'registration blocks it so it can never
    happen' - a row inserted directly (bypassing register_tool entirely,
    the same 'direct DB tampering proves a live re-check' technique
    Stage H/J's own tests already use) is still caught at the point of use."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        now = tr._now()
        from uuid import uuid4
        with tr._connect() as conn:
            conn.execute("""
                INSERT INTO jarvis_tools
                    (row_id, tool_id, version, name, description, capability_id, worker_id, action_class,
                     risk_level, required_permissions, required_privacy_scopes, transaction_capable,
                     security_sensitive, side_effect_class, verification_required, idempotent, cancellable,
                     connector_id, trust_level, enabled, schema_hash, disabled_reason, disabled_at,
                     created_at, updated_at, last_idempotency_key)
                VALUES (?, 'tool-bypassed', 1, 'x', 'x', 'cap-x', 'worker-x', 'READ', 'R0', '[]', '[]',
                        1, 0, 'INTERNAL', 0, 0, 0, NULL, 'VERIFIED', 1, 'deadbeef', NULL, NULL, ?, ?, NULL)
            """, (str(uuid4()), now, now))
        avail = tr.validate_tool_availability("tool-bypassed")
        assert "TRANSACTION_PROHIBITED" in avail["reason_codes"]
        try:
            tr.assert_tool_executable("tool-bypassed")
            assert False, "defense-in-depth re-scan must still catch a directly-inserted transaction-capable row"
        except tr.ToolTransactionProhibitedError:
            pass


# --- 22-23: idempotency / concurrency --------------------------------------------

def test_registration_idempotency_key():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        t1 = tr.register_tool(**_valid_fields(), idempotency_key="req-1")
        t2 = tr.register_tool(**_valid_fields(risk_level="R2"), idempotency_key="req-1")
        assert t1.version == t2.version == 1
        assert t2.risk_level == "R0"  # the retried call returned the ORIGINAL result, not a new registration


def test_concurrent_registration_is_race_safe():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        errors = []

        def _register(i):
            try:
                tr.register_tool(**_valid_fields(tool_id="tool-concurrent", capability_id=f"cap-{i}"))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=_register, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"unexpected errors under concurrent registration: {errors}"
        versions = tr.list_tool_versions("tool-concurrent")
        assert [v.version for v in versions] == list(range(1, len(versions) + 1)), \
            "concurrent registrations must produce a gap-free, duplicate-free version sequence"


# --- 24: global registry, not per-user (documented, not a gap) ------------------

def test_tool_registry_is_global_not_per_user_by_design():
    """Tool Registry has no user_id scoping - a global catalog, the same
    architectural choice capabilities.py's own static REGISTRY already
    makes. 'Cross-user isolation' therefore does not apply to visibility
    (any user_id can see/use a registered tool); it applies to
    PROVENANCE, which `actor` tracks on every event."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        tr.register_tool(**_valid_fields(), actor="user-1")
        assert tr.get_tool("tool-context-assembly") is not None
        events = tr.list_tool_events("tool-context-assembly")
        assert events[0]["actor"] == "user-1"


# --- 25: Action Firewall integration ---------------------------------------------

def test_action_firewall_never_consulted_when_tool_registry_already_denies():
    with tempfile.TemporaryDirectory() as d:
        _fresh_full_db(Path(d))
        with _temp_capability("test-tk-cap", "R0"):
            tr.register_tool(**_valid_fields(tool_id="tool-blocked", capability_id="test-tk-cap",
                                              worker_id="tk-echo-worker", risk_level="R0", trust_level="BLOCKED"))
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = _ready_step(mission, "user-1", worker_id="test-tk-cap")
            before = len(fw.list_decisions_for_step(step["step_id"]))
            try:
                workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry)
                assert False
            except workers.WorkerToolNotAuthorizedError:
                pass
            after = len(fw.list_decisions_for_step(step["step_id"]))
            assert after == before, "the Action Firewall must never even be consulted once the Tool Registry gate denies"


# --- 26: Approval integration -----------------------------------------------------

def test_approval_fingerprint_uses_the_registered_tool_identity():
    with tempfile.TemporaryDirectory() as d:
        _fresh_full_db(Path(d))
        with _temp_capability("test-tk-r2", "R2"):
            tr.register_tool(**_valid_fields(tool_id="tool-r2-a", capability_id="test-tk-r2",
                                              worker_id="tk-echo-worker", risk_level="R2", trust_level="VERIFIED"))
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = _ready_step(mission, "user-1", worker_id="test-tk-r2")

            tool = tr.get_tool("tool-r2-a")
            req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1",
                                         "EXTERNAL_SIDE_EFFECT", "R2", tool_id=tool.tool_id,
                                         material_params=tr.approval_material_params(tool))
            appr.approve(req.approval_id, "user-1")

            result = workers.execute_step(mission["mission_id"], step["step_id"], "user-1",
                                           registry=registry, action_class="EXTERNAL_SIDE_EFFECT")
            assert result.status == "SUCCEEDED"


# --- 27: Intent Lock integration ---------------------------------------------------

def test_intent_drift_denies_execution_even_with_valid_tool_and_approval():
    with tempfile.TemporaryDirectory() as d:
        _fresh_full_db(Path(d))
        with _temp_capability("test-tk-r2b", "R2"):
            tr.register_tool(**_valid_fields(tool_id="tool-r2-b", capability_id="test-tk-r2b",
                                              worker_id="tk-echo-worker", risk_level="R2", trust_level="VERIFIED"))
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = _ready_step(mission, "user-1", worker_id="test-tk-r2b")
            plan = pl.create_plan(mission["mission_id"], "user-1", "Original objective",
                                   [{"local_id": "s1", "description": "thing"}])
            il.lock_intent(mission["mission_id"], "user-1", plan_id=plan["plan_id"])

            tool = tr.get_tool("tool-r2-b")
            material_params = tr.approval_material_params(tool)
            req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1",
                                         "EXTERNAL_SIDE_EFFECT", "R2", tool_id=tool.tool_id,
                                         material_params=material_params)
            appr.approve(req.approval_id, "user-1")

            # Prove the approval genuinely matches BEFORE drift - otherwise
            # a later denial could just be a fingerprint mismatch, not
            # actually proof that intent drift is what caused it.
            pre_drift = fw.authorize(mission["mission_id"], step["step_id"], "user-1",
                                      "EXTERNAL_SIDE_EFFECT", "R2", tool_id=tool.tool_id,
                                      material_params=material_params)
            assert pre_drift.decision == "ALLOW"

            with msn._connect() as conn:
                conn.execute("UPDATE jarvis_missions SET goal = ? WHERE mission_id = ?",
                             ("a completely different goal", mission["mission_id"]))

            try:
                workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                      action_class="EXTERNAL_SIDE_EFFECT")
                assert False, "a registered, trusted, approved tool must still deny on intent drift"
            except workers.ApprovalRequiredError:
                pass


# --- 28: Worker integration --------------------------------------------------------

def test_worker_execute_never_called_when_tool_registry_blocks():
    with tempfile.TemporaryDirectory() as d:
        _fresh_full_db(Path(d))
        with _temp_capability("test-tk-r0", "R0"):
            tr.register_tool(**_valid_fields(tool_id="tool-r0", capability_id="test-tk-r0",
                                              worker_id="counting-worker", risk_level="R0", trust_level="UNKNOWN"))
            counting = _CountingWorker()
            registry = workers.WorkerRegistry()
            registry.register_worker(counting)
            mission = _mission_executing()
            step = _ready_step(mission, "user-1", worker_id="test-tk-r0")
            try:
                workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry)
                assert False
            except workers.WorkerToolNotAuthorizedError:
                pass
            assert counting.call_count == 0


def test_worker_execute_called_exactly_once_when_tool_registry_allows():
    with tempfile.TemporaryDirectory() as d:
        _fresh_full_db(Path(d))
        with _temp_capability("test-tk-r0b", "R0"):
            tr.register_tool(**_valid_fields(tool_id="tool-r0b", capability_id="test-tk-r0b",
                                              worker_id="counting-worker", risk_level="R0", trust_level="VERIFIED"))
            counting = _CountingWorker()
            registry = workers.WorkerRegistry()
            registry.register_worker(counting)
            mission = _mission_executing()
            step = _ready_step(mission, "user-1", worker_id="test-tk-r0b")
            result = workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry)
            assert result.status == "SUCCEEDED"
            assert counting.call_count == 1


# --- 29: Recovery cannot select an invalid tool ------------------------------------

def test_recovery_retry_still_blocked_by_tool_registry():
    with tempfile.TemporaryDirectory() as d:
        _fresh_full_db(Path(d))
        with _temp_capability("test-tk-recover", "R0"):
            tr.register_tool(**_valid_fields(tool_id="tool-recover", capability_id="test-tk-recover",
                                              worker_id="tk-echo-worker", risk_level="R0", trust_level="BLOCKED"))
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = msn.create_step(mission["mission_id"], "user-1", "will fail then recover",
                                    worker_id="test-tk-recover")
            step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "READY")
            step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "RUNNING")
            step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "FAILED",
                                        error={"code": "TOOL_TIMEOUT", "category": "TIMEOUT", "retryable": True})
            attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1", registry=registry)
            assert attempt.decision == "RETRY"
            assert msn.get_step(step["step_id"], mission["mission_id"], "user-1")["status"] == "READY"
            try:
                workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry)
                assert False, "Recovery re-arming a step must not let it bypass the Tool Registry's own gate"
            except workers.WorkerToolNotAuthorizedError:
                pass


# --- 30: fallback cannot bypass tool validation ------------------------------------

def test_fallback_reassignment_still_blocked_by_tool_registry():
    with tempfile.TemporaryDirectory() as d:
        _fresh_full_db(Path(d))
        with _temp_capability("test-tk-fallback-a", "R0"), _temp_capability("test-tk-fallback-b", "R0"):
            tr.register_tool(**_valid_fields(tool_id="tool-fallback-b", capability_id="test-tk-fallback-b",
                                              worker_id="tk-echo-worker", risk_level="R0", trust_level="BLOCKED"))
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = msn.create_step(mission["mission_id"], "user-1", "will fail then fall back",
                                    worker_id="test-tk-fallback-a", max_attempts=1)
            step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "READY")
            step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "RUNNING")
            step = msn.transition_step(step["step_id"], mission["mission_id"], "user-1", "FAILED",
                                        error={"code": "TOOL_TIMEOUT", "category": "TIMEOUT", "retryable": True})
            fallback_map = {"test-tk-fallback-a": ["test-tk-fallback-b"]}
            attempt = rec.recover_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                        fallback_map=fallback_map)
            assert attempt.decision == "FALLBACK"
            reassigned = msn.get_step(step["step_id"], mission["mission_id"], "user-1")
            assert reassigned["worker_id"] == "test-tk-fallback-b"
            try:
                workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry)
                assert False, "a fallback landing on a BLOCKED-trust tool must still be denied"
            except workers.WorkerToolNotAuthorizedError:
                pass


# --- 31: disabled tool after approval ----------------------------------------------

def test_disabling_tool_after_approval_still_denies_execution():
    with tempfile.TemporaryDirectory() as d:
        _fresh_full_db(Path(d))
        with _temp_capability("test-tk-r2c", "R2"):
            tr.register_tool(**_valid_fields(tool_id="tool-r2-c", capability_id="test-tk-r2c",
                                              worker_id="tk-echo-worker", risk_level="R2", trust_level="VERIFIED"))
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = _ready_step(mission, "user-1", worker_id="test-tk-r2c")
            req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1",
                                         "EXTERNAL_SIDE_EFFECT", "R2", tool_id="tool-r2-c")
            appr.approve(req.approval_id, "user-1")

            tr.unregister_tool("tool-r2-c", reason="withdrawn after approval")

            try:
                workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                      action_class="EXTERNAL_SIDE_EFFECT")
                assert False, "APPROVED != AUTHORIZED - disabling the tool must still deny"
            except workers.WorkerToolNotAuthorizedError:
                pass


# --- 32: tool metadata mutation after approval -------------------------------------

def test_material_tool_change_after_approval_requires_fresh_approval():
    with tempfile.TemporaryDirectory() as d:
        _fresh_full_db(Path(d))
        with _temp_capability("test-tk-r2d", "R2"):
            tr.register_tool(**_valid_fields(tool_id="tool-r2-d", capability_id="test-tk-r2d",
                                              worker_id="tk-echo-worker", risk_level="R2", trust_level="VERIFIED"))
            registry = workers.WorkerRegistry()
            registry.register_worker(_EchoWorker())
            mission = _mission_executing()
            step = _ready_step(mission, "user-1", worker_id="test-tk-r2d")
            tool_v1 = tr.get_tool("tool-r2-d")
            material_params_v1 = tr.approval_material_params(tool_v1)
            req = appr.request_approval(mission["mission_id"], step["step_id"], "user-1",
                                         "EXTERNAL_SIDE_EFFECT", "R2", tool_id=tool_v1.tool_id,
                                         material_params=material_params_v1)
            appr.approve(req.approval_id, "user-1")

            # Prove the approval genuinely matches at v1 BEFORE the change.
            pre_change = fw.authorize(mission["mission_id"], step["step_id"], "user-1",
                                       "EXTERNAL_SIDE_EFFECT", "R2", tool_id=tool_v1.tool_id,
                                       material_params=material_params_v1)
            assert pre_change.decision == "ALLOW"

            # Material change (new required_permissions) - bumps the tool's
            # version, which changes `tool_version` in material_params,
            # which changes the SAME approval fingerprint mechanism Stage I
            # already owns.
            tr.register_tool(**_valid_fields(tool_id="tool-r2-d", capability_id="test-tk-r2d",
                                              worker_id="tk-echo-worker", risk_level="R2", trust_level="VERIFIED",
                                              required_permissions=("something-new",)))
            assert tr.get_tool("tool-r2-d").version == 2

            try:
                workers.execute_step(mission["mission_id"], step["step_id"], "user-1", registry=registry,
                                      action_class="EXTERNAL_SIDE_EFFECT")
                assert False, "a materially changed tool schema must invalidate the old approval's fingerprint"
            except workers.ApprovalRequiredError:
                pass


# --- 33: restart persistence --------------------------------------------------------

def test_tool_registration_persists_across_a_simulated_restart():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        tr.register_tool(**_valid_fields())
        # Simulate a process restart: nothing survives except the DB file
        # itself - a fresh SELECT through a fresh connection, same
        # technique test_action_firewall.py's own restart test uses.
        tool = tr.get_tool("tool-context-assembly")
        assert tool is not None
        assert tool.version == 1


# --- 34: audit trail -----------------------------------------------------------------

def test_audit_trail_records_every_lifecycle_event():
    with tempfile.TemporaryDirectory() as d:
        _fresh_tools_db(Path(d))
        tr.register_tool(**_valid_fields(), actor="user-1")
        tr.register_tool(**_valid_fields(risk_level="R2"), actor="user-1")
        tr.unregister_tool("tool-context-assembly", reason="done", actor="user-1")
        events = tr.list_tool_events("tool-context-assembly")
        assert [e["event_type"] for e in events] == ["REGISTERED", "VERSIONED", "DISABLED"]
        assert all(e["actor"] == "user-1" for e in events)


# --- 35: full integration path --------------------------------------------------------

def test_full_integration_path_register_execute_then_disable():
    """Reuses a REAL, pre-existing capability + worker (Stage D's
    ContextWorker/jarvis-context-assembly) rather than a synthetic fixture,
    proving this composes with the actual runtime, not just test doubles."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_full_db(Path(d))
        tr.register_tool(tool_id="tool-context-real", name="Context Assembly", description="real capability",
                          capability_id="jarvis-context-assembly", worker_id="context-worker",
                          action_class="READ", risk_level="R0", trust_level="VERIFIED")
        mission = _mission_executing()
        step = _ready_step(mission, "user-1", worker_id="jarvis-context-assembly")
        result = workers.execute_step(mission["mission_id"], step["step_id"], "user-1")
        assert result.status == "SUCCEEDED"

        tr.unregister_tool("tool-context-real", reason="end of integration test")
        step2 = _ready_step(mission, "user-1", worker_id="jarvis-context-assembly")
        try:
            workers.execute_step(mission["mission_id"], step2["step_id"], "user-1")
            assert False
        except workers.WorkerToolNotAuthorizedError:
            pass


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
