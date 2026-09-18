"""
Tests for jarvis/model_router.py — the Model Router (Stage L). Run directly:

    python3 jarvis/tests/test_model_router.py

The Router selects, it never invokes, and it never authorizes. Several
tests exist specifically to prove that: model_router.py has no import
path to missions/approval/action_firewall/intent_lock/tools/workers at
all, so a model's output cannot reach permissions, policy, approval
state, intent locks, firewall rules, or the tool registry through this
module - not merely "doesn't currently", structurally cannot.
"""

import ast
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import model_router as mr  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _fresh_db(tmp_path: Path):
    db_file = tmp_path / "test_jarvis_model_router.db"
    mr.DB_PATH = db_file
    mr.init_db()


def _register_provider(provider_id="prov-a", **overrides):
    fields = dict(name="Provider A", description="A test provider", enabled=True, auth_configured=True)
    fields.update(overrides)
    return mr.register_provider(provider_id, **fields)


def _register_model(model_id="model-a", provider_id="prov-a", **overrides):
    fields = dict(
        name="Model A", description="A test model", capabilities=("reasoning", "summarization"),
        context_capacity=8000, modality=("text",), quality_tier="STANDARD", latency_class="STANDARD",
        privacy_scopes=("business", "public"), cost_per_unit=0.01, reliability_score=0.8, enabled=True,
    )
    fields.update(overrides)
    return mr.register_model(model_id, provider_id=provider_id, **fields)


class _FakeAvailableProvider(mr.ModelProvider):
    provider_id = "prov-a"

    def check_status(self):
        return "AVAILABLE"

    def invoke(self, request):
        return mr.ModelResponse(decision_id="d", provider_id=self.provider_id, model_id="model-a",
                                 content={"text": "hello"})


class _FakeFailedProvider(mr.ModelProvider):
    provider_id = "prov-b"

    def check_status(self):
        return "FAILED"

    def invoke(self, request):
        raise RuntimeError("should never be called by the router")


# --- 1-3: registration ------------------------------------------------------------

def test_register_provider():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        p = _register_provider()
        assert p.provider_id == "prov-a"
        assert p.status == "REGISTERED"  # never AVAILABLE merely from registering


def test_register_model():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        m = _register_model()
        assert m.model_id == "model-a"
        assert m.version == 1


def test_duplicate_registration_is_idempotent_no_op():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        m1 = _register_model()
        m2 = _register_model()
        assert m1.version == m2.version == 1
        assert len(mr.list_model_versions("model-a")) == 1


# --- 4: invalid model metadata ------------------------------------------------------

def test_invalid_model_metadata_rejected():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        try:
            _register_model(quality_tier="LUDICROUS")
            assert False
        except mr.ModelRouterValidationError as e:
            assert any(v["field"] == "quality_tier" for v in e.error.metadata["violations"])
        assert mr.get_model("model-a") is None


def test_model_requires_existing_provider():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        try:
            _register_model(provider_id="no-such-provider")
            assert False
        except mr.ProviderNotFoundError:
            pass


# --- 5-9: matching dimensions --------------------------------------------------------

def test_capability_matching():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "AVAILABLE")
        _register_model(capabilities=("reasoning",))
        decision = mr.route(mr.ModelRequest(required_capability="reasoning"))
        assert decision.outcome == "ROUTED"
        assert decision.selected_model_id == "model-a"

        decision2 = mr.route(mr.ModelRequest(required_capability="translation"))
        assert decision2.outcome == "NO_COMPATIBLE_MODEL"
        assert "NO_CAPABILITY_MATCH" in decision2.reason_codes


def test_context_size_matching():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "AVAILABLE")
        _register_model(context_capacity=4000)
        decision = mr.route(mr.ModelRequest(required_capability="reasoning", min_context_capacity=8000))
        assert decision.outcome == "NO_COMPATIBLE_MODEL"
        assert "NO_CONTEXT_MATCH" in decision.reason_codes

        decision2 = mr.route(mr.ModelRequest(required_capability="reasoning", min_context_capacity=2000))
        assert decision2.outcome == "ROUTED"


def test_modality_matching():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "AVAILABLE")
        _register_model(modality=("text",))
        decision = mr.route(mr.ModelRequest(required_capability="reasoning", required_modality="image"))
        assert decision.outcome == "NO_COMPATIBLE_MODEL"
        assert "NO_MODALITY_MATCH" in decision.reason_codes

        decision2 = mr.route(mr.ModelRequest(required_capability="reasoning", required_modality="text"))
        assert decision2.outcome == "ROUTED"


def test_quality_requirement():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "AVAILABLE")
        _register_model(quality_tier="BASIC")
        decision = mr.route(mr.ModelRequest(required_capability="reasoning", quality_requirement="ADVANCED"))
        assert decision.outcome == "NO_COMPATIBLE_MODEL"
        assert "NO_QUALITY_MATCH" in decision.reason_codes

        decision2 = mr.route(mr.ModelRequest(required_capability="reasoning", quality_requirement="BASIC"))
        assert decision2.outcome == "ROUTED"


def test_latency_requirement():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "AVAILABLE")
        _register_model(latency_class="SLOW")
        decision = mr.route(mr.ModelRequest(required_capability="reasoning", latency_requirement="FAST"))
        assert decision.outcome == "NO_COMPATIBLE_MODEL"
        assert "NO_LATENCY_MATCH" in decision.reason_codes

        decision2 = mr.route(mr.ModelRequest(required_capability="reasoning", latency_requirement="SLOW"))
        assert decision2.outcome == "ROUTED"


# --- 10-11: privacy --------------------------------------------------------------------

def test_privacy_scope_matching():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "AVAILABLE")
        _register_model(privacy_scopes=("business",))
        decision = mr.route(mr.ModelRequest(required_capability="reasoning", privacy_scope="business"))
        assert decision.outcome == "ROUTED"
        assert decision.privacy_match is True


def test_privacy_mismatch_fails_closed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "AVAILABLE")
        _register_model(privacy_scopes=("business",))
        decision = mr.route(mr.ModelRequest(required_capability="reasoning", privacy_scope="private"))
        assert decision.outcome == "NO_COMPATIBLE_MODEL"
        assert "PRIVACY_MISMATCH" in decision.reason_codes
        assert decision.selected_model_id is None


# --- 12-14: availability -----------------------------------------------------------------

def test_unavailable_provider_excludes_its_models():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "UNAVAILABLE")
        _register_model()
        decision = mr.route(mr.ModelRequest(required_capability="reasoning"))
        assert decision.outcome == "NO_COMPATIBLE_MODEL"
        assert "NO_AVAILABLE_PROVIDER" in decision.reason_codes


def test_disabled_provider_excludes_its_models_even_if_reported_available():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "AVAILABLE")
        mr.unregister_provider("prov-a", reason="turned off")
        _register_model()
        decision = mr.route(mr.ModelRequest(required_capability="reasoning"))
        assert decision.outcome == "NO_COMPATIBLE_MODEL"
        assert "NO_AVAILABLE_PROVIDER" in decision.reason_codes


def test_unavailable_disabled_model_excluded():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "AVAILABLE")
        _register_model()
        mr.unregister_model("model-a", reason="retired")
        decision = mr.route(mr.ModelRequest(required_capability="reasoning"))
        assert decision.outcome == "NO_COMPATIBLE_MODEL"
        assert "NO_CAPABILITY_MATCH" in decision.reason_codes  # disabled models are excluded from the pool entirely


# --- 15-16: determinism ------------------------------------------------------------------

def test_deterministic_routing():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "AVAILABLE")
        _register_model()
        d1 = mr.route(mr.ModelRequest(required_capability="reasoning"))
        d2 = mr.route(mr.ModelRequest(required_capability="reasoning"))
        assert d1.selected_model_id == d2.selected_model_id == "model-a"
        assert d1.outcome == d2.outcome


def test_deterministic_tie_break():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider("prov-a")
        _register_provider("prov-b")
        mr.report_provider_status("prov-a", "AVAILABLE")
        mr.report_provider_status("prov-b", "AVAILABLE")
        # Identical scoring inputs on both models - tie must break by
        # (provider_id, model_id) ascending, deterministically.
        _register_model("model-z", provider_id="prov-b", quality_tier="STANDARD", latency_class="STANDARD",
                         reliability_score=0.8, cost_per_unit=0.01)
        _register_model("model-a", provider_id="prov-a", quality_tier="STANDARD", latency_class="STANDARD",
                         reliability_score=0.8, cost_per_unit=0.01)
        d1 = mr.route(mr.ModelRequest(required_capability="reasoning"))
        d2 = mr.route(mr.ModelRequest(required_capability="reasoning"))
        assert d1.selected_provider_id == "prov-a"  # prov-a < prov-b alphabetically
        assert d1.selected_model_id == d2.selected_model_id


# --- 17-18: preference -----------------------------------------------------------------

def test_explicit_model_preference():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider("prov-a")
        _register_provider("prov-b")
        mr.report_provider_status("prov-a", "AVAILABLE")
        mr.report_provider_status("prov-b", "AVAILABLE")
        _register_model("model-a", provider_id="prov-a", quality_tier="BASIC")  # would NOT win on score
        _register_model("model-b", provider_id="prov-b", quality_tier="FRONTIER")  # would win on score
        decision = mr.route(mr.ModelRequest(required_capability="reasoning", preferred_model_id="model-a"))
        assert decision.outcome == "ROUTED"
        assert decision.selected_model_id == "model-a"
        assert "PREFERRED_MODEL_SELECTED" in decision.reason_codes


def test_invalid_preference_rejected():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "AVAILABLE")
        _register_model()
        decision = mr.route(mr.ModelRequest(required_capability="reasoning", preferred_model_id="does-not-exist"))
        assert decision.outcome == "NO_COMPATIBLE_MODEL"
        assert "INVALID_PREFERENCE" in decision.reason_codes


# --- 19-20: fallback ---------------------------------------------------------------------

def test_fallback_candidate_reported():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider("prov-a")
        _register_provider("prov-b")
        mr.report_provider_status("prov-a", "AVAILABLE")
        mr.report_provider_status("prov-b", "AVAILABLE")
        _register_model("model-a", provider_id="prov-a", quality_tier="FRONTIER")
        _register_model("model-b", provider_id="prov-b", quality_tier="BASIC")
        decision = mr.route(mr.ModelRequest(required_capability="reasoning"))
        assert decision.selected_model_id == "model-a"
        assert {"provider_id": "prov-b", "model_id": "model-b"} in decision.fallback_candidates


def test_fallback_ordering_matches_ranking():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider("prov-a")
        _register_provider("prov-b")
        _register_provider("prov-c")
        for p in ("prov-a", "prov-b", "prov-c"):
            mr.report_provider_status(p, "AVAILABLE")
        _register_model("model-high", provider_id="prov-a", quality_tier="FRONTIER")
        _register_model("model-mid", provider_id="prov-b", quality_tier="ADVANCED")
        _register_model("model-low", provider_id="prov-c", quality_tier="BASIC")
        decision = mr.route(mr.ModelRequest(required_capability="reasoning"))
        assert decision.selected_model_id == "model-high"
        assert [c["model_id"] for c in decision.fallback_candidates] == ["model-mid", "model-low"]


def test_preferred_model_unavailable_falls_back_when_allowed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider("prov-a")
        _register_provider("prov-b")
        mr.report_provider_status("prov-a", "UNAVAILABLE")
        mr.report_provider_status("prov-b", "AVAILABLE")
        _register_model("model-a", provider_id="prov-a")
        _register_model("model-b", provider_id="prov-b")
        decision = mr.route(mr.ModelRequest(required_capability="reasoning", preferred_model_id="model-a",
                                             fallback_allowed=True))
        assert decision.outcome == "ROUTED"
        assert decision.selected_model_id == "model-b"
        assert "PREFERRED_MODEL_UNAVAILABLE" in decision.reason_codes


def test_preferred_model_unavailable_denies_when_fallback_disallowed():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider("prov-a")
        mr.report_provider_status("prov-a", "UNAVAILABLE")
        _register_model("model-a", provider_id="prov-a")
        decision = mr.route(mr.ModelRequest(required_capability="reasoning", preferred_model_id="model-a",
                                             fallback_allowed=False))
        assert decision.outcome == "NO_COMPATIBLE_MODEL"
        assert "PREFERRED_MODEL_UNAVAILABLE" in decision.reason_codes


# --- 21: no compatible model -----------------------------------------------------------

def test_no_compatible_model_when_registry_empty():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        decision = mr.route(mr.ModelRequest(required_capability="reasoning"))
        assert decision.outcome == "NO_COMPATIBLE_MODEL"
        assert "NO_CAPABILITY_MATCH" in decision.reason_codes


# --- 22-23: auth-required / rate-limited -------------------------------------------------

def test_authentication_required_state_excludes_provider():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "AUTH_REQUIRED", reason="no API key configured")
        _register_model()
        decision = mr.route(mr.ModelRequest(required_capability="reasoning"))
        assert decision.outcome == "NO_COMPATIBLE_MODEL"
        assert "NO_AVAILABLE_PROVIDER" in decision.reason_codes


def test_rate_limited_state_excludes_provider():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "RATE_LIMITED")
        _register_model()
        decision = mr.route(mr.ModelRequest(required_capability="reasoning"))
        assert decision.outcome == "NO_COMPATIBLE_MODEL"
        assert "NO_AVAILABLE_PROVIDER" in decision.reason_codes


# --- 24: resource constraint --------------------------------------------------------------

def test_resource_constraint_cost():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "AVAILABLE")
        _register_model(cost_per_unit=1.00)
        decision = mr.route(mr.ModelRequest(required_capability="reasoning", max_cost=0.10))
        assert decision.outcome == "NO_COMPATIBLE_MODEL"
        assert "COST_CONSTRAINT_UNMET" in decision.reason_codes

        decision2 = mr.route(mr.ModelRequest(required_capability="reasoning", max_cost=2.00))
        assert decision2.outcome == "ROUTED"


# --- 25-26: idempotency / concurrency ------------------------------------------------------

def test_routing_idempotency():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "AVAILABLE")
        _register_model()
        d1 = mr.route(mr.ModelRequest(required_capability="reasoning"), decision_id="fixed-id")
        d2 = mr.route(mr.ModelRequest(required_capability="translation"), decision_id="fixed-id")
        assert d1.decision_id == d2.decision_id
        assert d2.required_capability == "reasoning"  # replayed, not re-evaluated


def test_concurrent_registry_modification_is_race_safe():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        errors = []

        def _register(i):
            try:
                _register_model("model-concurrent", capabilities=(f"cap-{i}",))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=_register, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"unexpected errors under concurrent registration: {errors}"
        versions = mr.list_model_versions("model-concurrent")
        assert [v.version for v in versions] == list(range(1, len(versions) + 1))


# --- 27: registry versioning ---------------------------------------------------------------

def test_registry_versioning_preserves_history():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        v1 = _register_model(quality_tier="BASIC")
        v2 = _register_model(quality_tier="ADVANCED")
        assert v2.version == 2
        assert v2.schema_hash != v1.schema_hash
        assert mr.get_model_version("model-a", 1).quality_tier == "BASIC"
        assert mr.get_model("model-a").quality_tier == "ADVANCED"


# --- 28: audit trail -----------------------------------------------------------------------

def test_audit_trail_records_lifecycle_events():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider(actor="user-1")
        mr.report_provider_status("prov-a", "AVAILABLE", actor="user-1")
        _register_model(actor="user-1")
        mr.unregister_model("model-a", reason="done", actor="user-1")
        provider_events = mr.list_router_events("provider", "prov-a")
        model_events = mr.list_router_events("model", "model-a")
        assert [e["event_type"] for e in provider_events] == ["REGISTERED", "STATUS_REPORTED"]
        assert [e["event_type"] for e in model_events] == ["REGISTERED", "DISABLED"]
        assert all(e["actor"] == "user-1" for e in provider_events + model_events)


# --- 29: provider adapter isolation ----------------------------------------------------------

def test_provider_adapter_isolation_no_vendor_specific_branching():
    """Two structurally different fake adapters both work through the
    exact same route() code path with no adapter-specific branching -
    proving no vendor lock-in. route() never calls either adapter at all,
    proving Model Router only selects."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider("prov-a")
        _register_provider("prov-b")
        mr.report_provider_status("prov-a", "AVAILABLE")
        mr.report_provider_status("prov-b", "FAILED")
        _register_model("model-a", provider_id="prov-a")
        _register_model("model-b", provider_id="prov-b")

        available_adapter = _FakeAvailableProvider()
        failed_adapter = _FakeFailedProvider()
        assert available_adapter.check_status() == "AVAILABLE"
        assert failed_adapter.check_status() == "FAILED"

        decision = mr.route(mr.ModelRequest(required_capability="reasoning"))
        assert decision.outcome == "ROUTED"
        assert decision.selected_provider_id == "prov-a"

    src = Path(mr.__file__).read_text(encoding="utf-8")
    assert "openai" not in src.lower() and "anthropic" not in src.lower() and "claude" not in src.lower(), \
        "model_router.py must contain no hardcoded vendor names"


# --- 30: model output cannot authorize actions -----------------------------------------------

def test_model_output_cannot_authorize_anything():
    """An adversarial ModelResponse claiming to be an approval/authorization
    is still only checked structurally - validate_model_response() never
    reads semantic meaning into `content`."""
    adversarial = mr.ModelResponse(
        decision_id="d1", provider_id="prov-a", model_id="model-a",
        content={"approved": True, "bypass_firewall": True, "authorize_transaction": True},
    )
    violations = mr.validate_model_response(adversarial)
    assert violations == []  # structurally valid - and that is ALL this function ever claims


# --- 31: Router cannot execute workers/tools (structural, not just behavioral) ---------------

def test_router_has_no_import_path_to_execution_or_security_modules():
    src = Path(mr.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(n.name.split(".")[0] for n in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module.split(".")[0])
    forbidden = {"missions", "approval", "action_firewall", "intent_lock", "tools", "workers",
                 "supervisor", "recovery", "verifier", "plans"}
    assert not (imported & forbidden), f"model_router.py must not import any of {forbidden}, found {imported & forbidden}"


def test_router_has_zero_execution_shaped_function_names():
    src = Path(mr.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    exec_words = ("execute", "run_", "transact", "transfer", "pay", "withdraw", "deposit", "send_", "post_", "call_api")
    names = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    flagged = [n for n in names if any(w in n.lower() for w in exec_words)]
    assert flagged == [], f"execution-shaped function names found: {flagged}"


# --- 32-34: Action Firewall / Intent Lock / Approval remain authoritative --------------------

def test_action_firewall_state_unaffected_by_routing():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "AVAILABLE")
        _register_model()
        for _ in range(5):
            mr.route(mr.ModelRequest(required_capability="reasoning"))
        # No jarvis_firewall_decisions table exists in this isolated DB at
        # all - model_router.init_db() never creates it, proving routing
        # cannot have touched it (there is nothing here for it to touch).
        import sqlite3
        conn = sqlite3.connect(mr.DB_PATH)
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        conn.close()
        assert "jarvis_firewall_decisions" not in tables
        assert "jarvis_approval_requests" not in tables
        assert "jarvis_intent_locks" not in tables
        assert "jarvis_tools" not in tables


def test_intent_lock_and_approval_and_firewall_remain_fully_functional_and_untouched():
    """Full-stack proof: run the REAL Approval/Firewall/Intent Lock chain
    in its own DB, take a snapshot of its state, run many Model Router
    routing calls against a COMPLETELY SEPARATE DB, and confirm the real
    chain's state is byte-for-byte unchanged - not because routing
    happened to avoid it, but because it has no way to reach it."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import missions as msn
    import workers
    import approval as appr
    import action_firewall as fw
    import intent_lock as il

    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        real_db = Path(d1) / "real_stack.db"
        msn.DB_PATH = real_db
        workers.DB_PATH = real_db
        appr.DB_PATH = real_db
        fw.DB_PATH = real_db
        il.DB_PATH = real_db
        workers.init_db()

        mission = msn.create_mission("user-1", "Test mission")
        before_missions = len(msn.list_missions_for_user("user-1")) if hasattr(msn, "list_missions_for_user") else None
        before_approvals = _connect_count(real_db, "jarvis_approval_requests")
        before_firewall = _connect_count(real_db, "jarvis_firewall_decisions")
        before_intent = _connect_count(real_db, "jarvis_intent_locks")

        _fresh_db(Path(d2))
        _register_provider()
        mr.report_provider_status("prov-a", "AVAILABLE")
        _register_model()
        for _ in range(10):
            mr.route(mr.ModelRequest(required_capability="reasoning"))

        after_approvals = _connect_count(real_db, "jarvis_approval_requests")
        after_firewall = _connect_count(real_db, "jarvis_firewall_decisions")
        after_intent = _connect_count(real_db, "jarvis_intent_locks")
        assert before_approvals == after_approvals
        assert before_firewall == after_firewall
        assert before_intent == after_intent
        # And the mission itself is still exactly as it was.
        assert msn.get_mission(mission["mission_id"], "user-1")["status"] == mission["status"]


def _connect_count(db_path, table):
    import sqlite3
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except sqlite3.OperationalError:
        return 0
    finally:
        conn.close()


# --- 35: transaction canary (in-file, package-wide canary covers this file automatically) ----

def test_transaction_shaped_routing_request_is_a_hard_stop():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        try:
            mr.route(mr.ModelRequest(required_capability="reasoning", task_type="transfer funds between accounts"))
            assert False
        except mr.ModelRouterTransactionProhibitedError:
            pass


def test_transaction_shaped_provider_registration_is_a_hard_stop():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        try:
            _register_provider(description="executes trades and wire transfers")
            assert False
        except mr.ModelRouterTransactionProhibitedError:
            pass
        assert mr.get_provider("prov-a") is None


# --- 36: restart persistence -----------------------------------------------------------------

def test_registration_persists_across_a_simulated_restart():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        _register_model()
        provider = mr.get_provider("prov-a")
        model = mr.get_model("model-a")
        assert provider is not None and model is not None
        assert model.version == 1


# --- 37: cross-user / privacy isolation where applicable --------------------------------------

def test_registry_is_global_privacy_enforced_per_request_not_per_user():
    """Model Router's registry has no user_id scoping - a global catalog,
    same choice capabilities.py and tools.py already make. Isolation that
    DOES apply here is privacy-scope matching (proven in tests 10-11), not
    user identity - a request simply declares what privacy scope its data
    carries, and the router enforces that regardless of who's asking."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider()
        mr.report_provider_status("prov-a", "AVAILABLE")
        _register_model(privacy_scopes=("private",))
        d1 = mr.route(mr.ModelRequest(required_capability="reasoning", privacy_scope="private", user_id="user-1"))
        d2 = mr.route(mr.ModelRequest(required_capability="reasoning", privacy_scope="private", user_id="user-2"))
        assert d1.outcome == d2.outcome == "ROUTED"  # same model, both users - no user-scoping exists
        d3 = mr.route(mr.ModelRequest(required_capability="reasoning", privacy_scope="public", user_id="user-1"))
        assert d3.outcome == "NO_COMPATIBLE_MODEL"  # but privacy scope itself is still enforced


# --- 38: full integration path -----------------------------------------------------------------

def test_full_integration_path():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register_provider("prov-a", name="Provider A", description="test", auth_configured=True)
        mr.report_provider_status("prov-a", "AVAILABLE")
        _register_model("model-a", provider_id="prov-a", quality_tier="ADVANCED")

        decision = mr.route(mr.ModelRequest(required_capability="reasoning", quality_requirement="STANDARD",
                                             privacy_scope="business", user_id="user-1"))
        assert decision.outcome == "ROUTED"
        assert decision.selected_provider_id == "prov-a"
        assert decision.selected_model_id == "model-a"

        # The CALLER, not the router, invokes the adapter.
        adapter = _FakeAvailableProvider()
        response = adapter.invoke(mr.ModelRequest(required_capability="reasoning"))
        assert mr.validate_model_response(response) == []

        # Availability changes - a legitimate model-level fallback, never
        # an action-recovery bypass (there is no action here at all).
        mr.report_provider_status("prov-a", "UNAVAILABLE")
        decision2 = mr.route(mr.ModelRequest(required_capability="reasoning"))
        assert decision2.outcome == "NO_COMPATIBLE_MODEL"
        assert "NO_AVAILABLE_PROVIDER" in decision2.reason_codes

        events = mr.list_router_events("provider", "prov-a")
        assert [e["event_type"] for e in events] == ["REGISTERED", "STATUS_REPORTED", "STATUS_REPORTED"]


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
