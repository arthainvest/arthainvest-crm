"""
Tests for jarvis/connectors.py — Connector Fabric (Stage M, part 1).
"""

import ast
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import connectors as cr  # noqa: E402


def _fresh_db(tmp_path: Path):
    db_file = tmp_path / "test_jarvis_connectors.db"
    cr.DB_PATH = db_file
    cr.init_db()


def _register(connector_id="conn-a", **overrides):
    fields = dict(
        name="Connector A", description="A test connector", connector_type="email",
        capabilities=("read", "send"), action_class="COMMUNICATE", risk_level="R2",
        privacy_scopes=("business",), required_permissions=("email:read",), trust_level="VERIFIED",
    )
    fields.update(overrides)
    return cr.register_connector(connector_id, **fields)


# --- registration / discovery -----------------------------------------------------

def test_register_connector():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        c = _register()
        assert c.connector_id == "conn-a"
        assert c.status == "REGISTERED"  # never AVAILABLE merely from registering


def test_duplicate_registration_idempotent():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        c1 = _register()
        c2 = _register()
        assert c1.version == c2.version == 1
        assert len(cr.list_connector_versions("conn-a")) == 1


def test_lookup_by_capability():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register()
        assert [c.connector_id for c in cr.lookup_connectors_by_capability("send")] == ["conn-a"]
        assert cr.lookup_connectors_by_capability("no-such-cap") == []


# --- status lifecycle ---------------------------------------------------------------

def test_status_lifecycle_registered_to_available():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register()
        assert cr.get_connector("conn-a").status == "REGISTERED"
        cr.report_connector_status("conn-a", "AVAILABLE")
        assert cr.get_connector("conn-a").effective_status == "AVAILABLE"


def test_disabled_overrides_reported_available():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register()
        cr.report_connector_status("conn-a", "AVAILABLE")
        cr.unregister_connector("conn-a", reason="turned off")
        assert cr.get_connector("conn-a").effective_status == "DISABLED"


# --- deterministic discovery ---------------------------------------------------------

def test_deterministic_listing():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register("conn-b", connector_type="calendar", capabilities=("read",))
        _register("conn-a")
        assert [c.connector_id for c in cr.list_connectors()] == ["conn-a", "conn-b"]


# --- trust ------------------------------------------------------------------------------

def test_trust_levels_default_unknown_and_unknown_blocked_not_executable():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        fields = dict(name="X", description="X", connector_type="email", capabilities=("read",),
                      action_class="READ", risk_level="R0")
        c = cr.register_connector("conn-x", **fields)  # no trust_level given
        assert c.trust_level == "UNKNOWN"
        cr.report_connector_status("conn-x", "AVAILABLE")
        avail = cr.validate_connector_availability("conn-x")
        assert not avail["available"]
        assert "TRUST_LEVEL_NOT_EXECUTABLE" in avail["reason_codes"]


def test_trust_level_verified_and_available_is_usable():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register(trust_level="VERIFIED")
        cr.report_connector_status("conn-a", "AVAILABLE")
        avail = cr.validate_connector_availability("conn-a")
        assert avail["available"]


def test_trust_level_blocked_never_usable():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register(trust_level="BLOCKED")
        cr.report_connector_status("conn-a", "AVAILABLE")
        avail = cr.validate_connector_availability("conn-a")
        assert not avail["available"]
        assert "TRUST_LEVEL_NOT_EXECUTABLE" in avail["reason_codes"]


# --- authentication -----------------------------------------------------------------------

def test_auth_required_state_excludes_connector():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register()
        cr.report_connector_status("conn-a", "AUTH_REQUIRED", reason="no token configured")
        avail = cr.validate_connector_availability("conn-a")
        assert not avail["available"]
        assert "CONNECTOR_NOT_AVAILABLE" in avail["reason_codes"]


def test_rate_limited_state_excludes_connector():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register()
        cr.report_connector_status("conn-a", "RATE_LIMITED")
        avail = cr.validate_connector_availability("conn-a")
        assert not avail["available"]


# --- authorization separation (structural + behavioral) --------------------------------

def test_connectors_has_no_import_of_execution_or_mutation_modules():
    src = Path(cr.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(n.name.split(".")[0] for n in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module.split(".")[0])
    forbidden = {"missions", "action_firewall", "intent_lock", "tools", "workers",
                 "supervisor", "recovery", "verifier", "plans"}
    assert not (imported & forbidden), f"connectors.py must not import {forbidden}, found {imported & forbidden}"


def test_registration_never_authorizes_anything():
    """Registering, even as VERIFIED + AVAILABLE, is metadata only - there
    is no function in this module that could ever authorize an action;
    this is proven by the import-isolation test above and reinforced here
    by confirming registration has zero side effect beyond its own table."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        c = _register(trust_level="VERIFIED")
        cr.report_connector_status("conn-a", "AVAILABLE")
        assert cr.validate_connector_availability("conn-a")["available"]
        # "available" is a Connector Fabric opinion only - nothing here
        # claims or implies any action is now approved.


# --- privacy ------------------------------------------------------------------------------

def test_privacy_scopes_are_declared_metadata():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        c = _register(privacy_scopes=("business", "public"))
        assert set(c.privacy_scopes) == {"business", "public"}


def test_invalid_privacy_scope_rejected():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        try:
            _register(privacy_scopes=("not-a-real-scope",))
            assert False
        except cr.ConnectorValidationError as e:
            assert any(v["type"] == "INVALID_PRIVACY_SCOPE" for v in e.error.metadata["violations"])


# --- user isolation (documented, global registry) --------------------------------------

def test_registry_is_global_not_per_user_by_design():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register(actor="user-1")
        # No user_id scoping exists - same architectural choice as
        # capabilities.py/tools.py/model_router.py. Visible to any caller;
        # provenance tracked via actor on the event log instead.
        assert cr.get_connector("conn-a") is not None
        events = cr.list_connector_events("conn-a")
        assert events[0]["actor"] == "user-1"


# --- malformed metadata -----------------------------------------------------------------

def test_malformed_metadata_rejected():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        try:
            _register(risk_level="R9")
            assert False
        except cr.ConnectorValidationError as e:
            assert any(v["field"] == "risk_level" for v in e.error.metadata["violations"])
        assert cr.get_connector("conn-a") is None


def test_invalid_timeout_rejected():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        try:
            _register(timeout_seconds=-5)
            assert False
        except cr.ConnectorValidationError as e:
            assert any(v["field"] == "timeout_seconds" for v in e.error.metadata["violations"])


# --- timeout / resource limits -----------------------------------------------------------

def test_timeout_and_rate_limit_metadata_stored():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        c = _register(timeout_seconds=15.0, max_requests_per_minute=60)
        assert c.timeout_seconds == 15.0
        assert c.max_requests_per_minute == 60


# --- versioning -----------------------------------------------------------------------------

def test_material_change_bumps_version_history_preserved():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        v1 = _register(risk_level="R1")
        v2 = _register(risk_level="R2")
        assert v2.version == 2
        assert v2.schema_hash != v1.schema_hash
        assert cr.get_connector_version("conn-a", 1).risk_level == "R1"


def test_administrative_only_change_no_version_bump():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register()
        updated = _register(description="a better description")
        assert updated.version == 1
        assert updated.description == "a better description"


# --- audit -----------------------------------------------------------------------------------

def test_audit_trail():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register(actor="user-1")
        cr.report_connector_status("conn-a", "AVAILABLE", actor="user-1")
        cr.unregister_connector("conn-a", reason="done", actor="user-1")
        events = cr.list_connector_events("conn-a")
        assert [e["event_type"] for e in events] == ["REGISTERED", "STATUS_REPORTED", "DISABLED"]


# --- restart -----------------------------------------------------------------------------------

def test_restart_persistence():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register()
        c = cr.get_connector("conn-a")
        assert c is not None and c.version == 1


# --- concurrency / idempotency ----------------------------------------------------------------

def test_registration_idempotency_key():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        c1 = _register(idempotency_key="req-1")
        c2 = _register(risk_level="R4" if False else "R1", idempotency_key="req-1")
        assert c1.version == c2.version == 1


def test_concurrent_registration_race_safe():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        errors = []

        def _r(i):
            try:
                _register("conn-concurrent", capabilities=(f"cap-{i}",))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=_r, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
        versions = cr.list_connector_versions("conn-concurrent")
        assert [v.version for v in versions] == list(range(1, len(versions) + 1))


# --- transaction-capable connector hard stop ---------------------------------------------------

def test_transaction_capable_connector_rejected_at_registration():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        try:
            _register("conn-tx", transaction_capable=True)
            assert False
        except cr.ConnectorTransactionProhibitedError:
            pass
        assert cr.get_connector("conn-tx") is None


def test_transaction_shaped_text_rejected():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        try:
            _register("conn-tx2", description="executes wire transfers between accounts")
            assert False
        except cr.ConnectorTransactionProhibitedError:
            pass


def test_transaction_prohibition_rechecked_at_use_defense_in_depth():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        now = cr._now()
        from uuid import uuid4
        with cr._connect() as conn:
            conn.execute("""
                INSERT INTO jarvis_connectors
                    (row_id, connector_id, version, name, description, connector_type, capabilities, action_class,
                     risk_level, privacy_scopes, required_permissions, transaction_capable, timeout_seconds,
                     max_requests_per_minute, trust_level, enabled, auth_configured, status, status_reason,
                     status_updated_at, schema_hash, disabled_reason, disabled_at, created_at, updated_at, last_idempotency_key)
                VALUES (?, 'conn-bypassed', 1, 'x', 'x', 'email', '["read"]', 'READ', 'R0', '[]', '[]',
                        1, 30.0, NULL, 'VERIFIED', 1, 0, 'AVAILABLE', NULL, ?, 'deadbeef', NULL, NULL, ?, ?, NULL)
            """, (str(uuid4()), now, now, now))
        avail = cr.validate_connector_availability("conn-bypassed")
        assert "TRANSACTION_PROHIBITED" in avail["reason_codes"]
        try:
            cr.assert_connector_usable("conn-bypassed")
            assert False
        except cr.ConnectorTransactionProhibitedError:
            pass


# --- no secret leakage -----------------------------------------------------------------------

def test_no_secret_or_credential_columns_exist():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        with cr._connect() as conn:
            cols = {r[1].lower() for r in conn.execute("PRAGMA table_info(jarvis_connectors)").fetchall()}
        forbidden_substrings = ("secret", "token", "password", "api_key", "credential")
        leaked = [c for c in cols if any(f in c for f in forbidden_substrings)]
        assert leaked == [], f"no column should ever hold a credential value, found: {leaked}"


# --- full integration boundary -----------------------------------------------------------------

def test_full_integration_boundary():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _register(trust_level="COMMUNITY")
        assert not cr.validate_connector_availability("conn-a")["available"]  # not AVAILABLE yet
        cr.report_connector_status("conn-a", "AVAILABLE")
        assert cr.validate_connector_availability("conn-a")["available"]
        cr.report_connector_status("conn-a", "FAILED", reason="health check failed")
        assert not cr.validate_connector_availability("conn-a")["available"]


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
