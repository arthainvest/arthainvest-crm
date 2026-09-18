#!/usr/bin/env python3
"""
JARVIS Connector Fabric — Stage M (part 1 of 2, see mcp_gateway.py for the
MCP-specific layer). One authoritative registry of external-system access
points and their security metadata.

    JARVIS -> CONNECTOR FABRIC (this file) -> MCP GATEWAY -> CONNECTOR/TOOL -> EXTERNAL SYSTEM

A Connector describes WHO/WHAT can reach an external system and under what
constraints (trust, privacy, risk, resource limits) - it never reaches
that system itself. Exactly like tools.py (Stage K) and model_router.py
(Stage L) before it: describe -> resolve -> validate -> authorize
METADATA, never execute, never authorize an action, never touch
Authorization/policy/firewall state.

## Structural isolation (same technique as model_router.py, Stage L)

This file has NO import of missions.py, action_firewall.py,
intent_lock.py, tools.py, or workers.py - not "doesn't call them today",
there is no reference to any of them anywhere in this file's namespace.
Registering, or even fully trusting, a connector cannot authorize a
single action, because there is no code path here to Approval Gate or
Action Firewall at all. approval.py IS imported, but ONLY for its
ACTION_CLASSES/RISK_LEVELS constants (exactly like tools.py, Stage K,
already does) - never appr.evaluate(), never request_approval(), never
anything that reads or writes approval state. memory.py's
VALID_PRIVACY_LEVELS is reused the same way, and backend/policy.py's
find_prohibited_routes is the single transaction-pattern source of truth
every prior stage reuses.

## No fake connectors (same rule Stage L already established for providers)

A connector's `status` starts at REGISTERED and can ONLY change via
report_connector_status() - register_connector() has no way to claim
AVAILABLE. Only AVAILABLE is ever usable; REGISTERED, UNAVAILABLE,
AUTH_REQUIRED, RATE_LIMITED, FAILED, and DISABLED (which always wins over
a stale report) are all equally unusable.

## Transaction prohibition

A connector declaring transaction_capable=True, or whose text matches
backend/policy.py's prohibited patterns, is refused at registration -
never persisted - and re-checked at the point of use (defense in depth,
same as every prior stage).

## No secret persistence

There is no field anywhere in this schema for an actual credential/token
value - only `auth_configured: bool`, an honest flag that configuration
exists somewhere else (outside this file's own storage), never what that
configuration IS. This is structural, not policy: the column simply does
not exist, so there is nothing here that could ever leak one.
"""

import hashlib
import json
import sqlite3
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import approval as appr  # noqa: E402 - reuses ACTION_CLASSES/RISK_LEVELS, descriptive only
import memory as mem  # noqa: E402 - reuses VALID_PRIVACY_LEVELS, never a second privacy taxonomy
from policy import find_prohibited_routes  # noqa: E402 - same single source of truth every other layer uses

DB_PATH = Path(__file__).resolve().parent / "jarvis.db"

CONNECTOR_STATUSES = {"REGISTERED", "AVAILABLE", "UNAVAILABLE", "AUTH_REQUIRED", "DISABLED", "RATE_LIMITED", "FAILED"}
EXECUTABLE_CONNECTOR_STATUSES = {"AVAILABLE"}

TRUST_LEVELS = {"VERIFIED", "TRUSTED", "COMMUNITY", "UNKNOWN", "BLOCKED"}
NON_EXECUTABLE_TRUST_LEVELS = {"UNKNOWN", "BLOCKED"}

ACTION_CLASSES = appr.ACTION_CLASSES
RISK_LEVELS = appr.RISK_LEVELS

MATERIAL_FIELDS = (
    "connector_type", "capabilities", "action_class", "risk_level", "privacy_scopes",
    "required_permissions", "transaction_capable", "timeout_seconds", "max_requests_per_minute",
)
ADMINISTRATIVE_FIELDS = ("name", "description", "trust_level", "enabled")


def _now():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

@dataclass
class ErrorObject:
    code: str
    category: str
    severity: str = "ERROR"
    retryable: bool = False
    user_action_required: bool = False
    message: str = ""
    metadata: dict = field(default_factory=dict)
    error_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=_now)

    def to_dict(self):
        return asdict(self)


class ConnectorError(Exception):
    def __init__(self, error: ErrorObject):
        self.error = error
        super().__init__(error.message)


class ConnectorValidationError(ConnectorError):
    def __init__(self, message, violations=None):
        super().__init__(ErrorObject(code="INVALID_INPUT", category="VALIDATION", message=message,
                                      metadata={"violations": violations or []}))


class ConnectorNotFoundError(ConnectorError):
    def __init__(self, connector_id):
        super().__init__(ErrorObject(code="CONNECTOR_NOT_FOUND", category="STATE",
                                      message=f"No connector {connector_id!r} is registered."))


class ConnectorConflictError(ConnectorError):
    def __init__(self, connector_id):
        super().__init__(ErrorObject(code="STATE_CONFLICT", category="CONCURRENCY", retryable=True,
                                      message=f"Connector {connector_id!r} registration was modified concurrently; retry."))


class ConnectorTransactionProhibitedError(ConnectorError):
    """Checked before any persistence - a transaction-shaped connector is
    refused unconditionally, exactly like every other stage's treatment
    of this one category."""

    def __init__(self, matches):
        super().__init__(ErrorObject(
            code="TRANSACTION_PROHIBITED", category="POLICY", severity="CRITICAL", retryable=False,
            message="This connector is financial-transaction-shaped and can never be registered or used.",
            metadata={"matches": matches},
        ))


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@dataclass
class ConnectorDescriptor:
    connector_id: str
    version: int
    name: str
    description: str
    connector_type: str
    capabilities: tuple
    action_class: str
    risk_level: str
    privacy_scopes: tuple
    required_permissions: tuple
    transaction_capable: bool
    timeout_seconds: float
    max_requests_per_minute: int
    trust_level: str
    enabled: bool
    auth_configured: bool
    status: str
    status_reason: str
    status_updated_at: str
    schema_hash: str
    disabled_reason: str
    disabled_at: str
    created_at: str
    updated_at: str
    last_idempotency_key: str

    @property
    def effective_status(self) -> str:
        return "DISABLED" if not self.enabled else self.status

    def to_dict(self):
        d = asdict(self)
        d["effective_status"] = self.effective_status
        return d


def _row_to_connector(row) -> ConnectorDescriptor:
    d = dict(row)
    d.pop("row_id", None)
    d["capabilities"] = tuple(json.loads(d["capabilities"]))
    d["privacy_scopes"] = tuple(json.loads(d["privacy_scopes"]))
    d["required_permissions"] = tuple(json.loads(d["required_permissions"]))
    d["transaction_capable"] = bool(d["transaction_capable"])
    d["enabled"] = bool(d["enabled"])
    d["auth_configured"] = bool(d["auth_configured"])
    return ConnectorDescriptor(**d)


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_connectors (
                row_id TEXT PRIMARY KEY,
                connector_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                connector_type TEXT NOT NULL,
                capabilities TEXT NOT NULL,
                action_class TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                privacy_scopes TEXT NOT NULL,
                required_permissions TEXT NOT NULL,
                transaction_capable INTEGER NOT NULL DEFAULT 0,
                timeout_seconds REAL NOT NULL,
                max_requests_per_minute INTEGER,
                trust_level TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                auth_configured INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'REGISTERED',
                status_reason TEXT,
                status_updated_at TEXT,
                schema_hash TEXT NOT NULL,
                disabled_reason TEXT,
                disabled_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_idempotency_key TEXT
            )
        """)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_connectors_id_version ON jarvis_connectors(connector_id, version)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_connector_events (
                event_id TEXT PRIMARY KEY,
                connector_id TEXT NOT NULL,
                version INTEGER,
                event_type TEXT NOT NULL,
                actor TEXT,
                reason TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_connector_events_id ON jarvis_connector_events(connector_id)")


def _log_event(connector_id, version, event_type, actor, reason, metadata):
    with _connect() as conn:
        conn.execute("""
            INSERT INTO jarvis_connector_events (event_id, connector_id, version, event_type, actor, reason, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid4()), connector_id, version, event_type, actor, reason, json.dumps(metadata or {}), _now()))


def list_connector_events(connector_id) -> list:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM jarvis_connector_events WHERE connector_id = ? ORDER BY created_at ASC", (connector_id,)
        ).fetchall()
    events = []
    for r in rows:
        d = dict(r)
        d["metadata"] = json.loads(d["metadata"]) if d["metadata"] else {}
        events.append(d)
    return events


def _scan_for_prohibited_text(*texts) -> list:
    combined = " | ".join(t for t in texts if t)
    if not combined:
        return []
    return [pattern for _, pattern in find_prohibited_routes([combined])]


def compute_connector_schema_hash(fields: dict) -> str:
    payload = {}
    for k in MATERIAL_FIELDS:
        v = fields[k]
        payload[k] = sorted(v) if isinstance(v, (list, tuple)) else v
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _get(obj, key):
    return obj[key] if isinstance(obj, dict) else getattr(obj, key)


def _norm(v):
    return tuple(sorted(v)) if isinstance(v, (list, tuple)) else v


def _material_key(obj):
    return tuple(_norm(_get(obj, k)) for k in MATERIAL_FIELDS)


def _admin_key(obj):
    return tuple(_get(obj, k) for k in ADMINISTRATIVE_FIELDS)


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

def validate_connector_metadata(fields: dict) -> list:
    violations = []
    for f in ("connector_id", "name", "description", "connector_type"):
        v = fields.get(f)
        if not isinstance(v, str) or not v.strip():
            violations.append({"type": "MISSING_REQUIRED_FIELD", "field": f})

    capabilities = fields.get("capabilities")
    if not isinstance(capabilities, (tuple, list)) or not capabilities or any(
            not isinstance(c, str) or not c.strip() for c in capabilities):
        violations.append({"type": "INVALID_FIELD_TYPE", "field": "capabilities"})

    action_class = fields.get("action_class")
    if action_class not in ACTION_CLASSES:
        violations.append({"type": "INVALID_ACTION_CLASS", "field": "action_class", "value": action_class})

    risk_level = fields.get("risk_level")
    if risk_level not in RISK_LEVELS:
        violations.append({"type": "INVALID_RISK_LEVEL", "field": "risk_level", "value": risk_level})

    privacy_scopes = fields.get("privacy_scopes")
    if not isinstance(privacy_scopes, (tuple, list)):
        violations.append({"type": "INVALID_FIELD_TYPE", "field": "privacy_scopes"})
    else:
        bad = [s for s in privacy_scopes if s not in mem.VALID_PRIVACY_LEVELS]
        if bad:
            violations.append({"type": "INVALID_PRIVACY_SCOPE", "field": "privacy_scopes", "value": bad})

    required_permissions = fields.get("required_permissions")
    if not isinstance(required_permissions, (tuple, list)) or any(not isinstance(p, str) for p in required_permissions):
        violations.append({"type": "INVALID_FIELD_TYPE", "field": "required_permissions"})

    if fields.get("trust_level") not in TRUST_LEVELS:
        violations.append({"type": "INVALID_TRUST_LEVEL", "field": "trust_level", "value": fields.get("trust_level")})

    timeout_seconds = fields.get("timeout_seconds")
    if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
        violations.append({"type": "INVALID_FIELD_TYPE", "field": "timeout_seconds"})

    max_rpm = fields.get("max_requests_per_minute")
    if max_rpm is not None and (not isinstance(max_rpm, int) or isinstance(max_rpm, bool) or max_rpm <= 0):
        violations.append({"type": "INVALID_FIELD_TYPE", "field": "max_requests_per_minute"})

    for f in ("transaction_capable", "enabled", "auth_configured"):
        if not isinstance(fields.get(f), bool):
            violations.append({"type": "INVALID_FIELD_TYPE", "field": f})

    return violations


# ---------------------------------------------------------------------------
# Register / lifecycle
# ---------------------------------------------------------------------------

def register_connector(connector_id, *, name, description, connector_type, capabilities, action_class, risk_level,
                        privacy_scopes=(), required_permissions=(), transaction_capable=False, timeout_seconds=30.0,
                        max_requests_per_minute=None, trust_level="UNKNOWN", enabled=True, auth_configured=False,
                        idempotency_key=None, actor=None) -> ConnectorDescriptor:
    fields = {
        "connector_id": connector_id, "name": name, "description": description, "connector_type": connector_type,
        "capabilities": tuple(capabilities or ()), "action_class": action_class, "risk_level": risk_level,
        "privacy_scopes": tuple(privacy_scopes or ()), "required_permissions": tuple(required_permissions or ()),
        "transaction_capable": bool(transaction_capable), "timeout_seconds": timeout_seconds,
        "max_requests_per_minute": max_requests_per_minute, "trust_level": trust_level, "enabled": bool(enabled),
        "auth_configured": bool(auth_configured),
    }
    violations = validate_connector_metadata(fields)
    if violations:
        raise ConnectorValidationError(f"invalid connector metadata for {connector_id!r}", violations)

    matches = _scan_for_prohibited_text(connector_id, name, description, connector_type, *fields["capabilities"])
    if fields["transaction_capable"] or matches or action_class == "FINANCIAL_TRANSACTION":
        raise ConnectorTransactionProhibitedError(
            matches or (["transaction_capable=True"] if fields["transaction_capable"]
                        else ["FINANCIAL_TRANSACTION action_class"]))

    if idempotency_key:
        with _connect() as conn:
            row = conn.execute(
                "SELECT * FROM jarvis_connectors WHERE connector_id = ? AND last_idempotency_key = ? "
                "ORDER BY version DESC LIMIT 1", (connector_id, idempotency_key),
            ).fetchone()
        if row:
            return _row_to_connector(row)

    now = _now()
    schema_hash = compute_connector_schema_hash(fields)
    current = get_connector(connector_id)

    if current is None:
        version = _insert_version(connector_id, fields, schema_hash, now, idempotency_key)
        _log_event(connector_id, version, "REGISTERED", actor, None, {"schema_hash": schema_hash})
        return get_connector(connector_id)

    if _material_key(current) == _material_key(fields):
        if _admin_key(current) == _admin_key(fields):
            return current
        _update_administrative(connector_id, current.version, fields, now)
        _log_event(connector_id, current.version, "UPDATED", actor, None, {"changed": "administrative"})
        return get_connector(connector_id)

    version = _insert_version(connector_id, fields, schema_hash, now, idempotency_key)
    _log_event(connector_id, version, "VERSIONED", actor, None, {
        "schema_hash": schema_hash, "previous_version": current.version, "previous_schema_hash": current.schema_hash,
    })
    return get_connector(connector_id)


def _insert_version(connector_id, fields, schema_hash, now, idempotency_key) -> int:
    max_attempts = 8
    for attempt in range(max_attempts):
        try:
            with _connect() as conn:
                row = conn.execute(
                    "SELECT version FROM jarvis_connectors WHERE connector_id = ? ORDER BY version DESC LIMIT 1",
                    (connector_id,),
                ).fetchone()
                next_version = (row["version"] + 1) if row else 1
                conn.execute("""
                    INSERT INTO jarvis_connectors
                        (row_id, connector_id, version, name, description, connector_type, capabilities, action_class,
                         risk_level, privacy_scopes, required_permissions, transaction_capable, timeout_seconds,
                         max_requests_per_minute, trust_level, enabled, auth_configured, status, status_reason,
                         status_updated_at, schema_hash, disabled_reason, disabled_at, created_at, updated_at,
                         last_idempotency_key)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'REGISTERED', NULL, NULL, ?, NULL, NULL, ?, ?, ?)
                """, (str(uuid4()), connector_id, next_version, fields["name"], fields["description"],
                      fields["connector_type"], json.dumps(list(fields["capabilities"])), fields["action_class"],
                      fields["risk_level"], json.dumps(list(fields["privacy_scopes"])),
                      json.dumps(list(fields["required_permissions"])), int(fields["transaction_capable"]),
                      fields["timeout_seconds"], fields["max_requests_per_minute"], fields["trust_level"],
                      int(fields["enabled"]), int(fields["auth_configured"]), schema_hash, now, now, idempotency_key))
            return next_version
        except (sqlite3.IntegrityError, sqlite3.OperationalError):
            if attempt == max_attempts - 1:
                raise ConnectorConflictError(connector_id)
            time.sleep(0.01 * (attempt + 1))
            continue
    raise ConnectorConflictError(connector_id)


def _update_administrative(connector_id, version, fields, now):
    with _connect() as conn:
        conn.execute("""
            UPDATE jarvis_connectors SET name = ?, description = ?, trust_level = ?, enabled = ?, updated_at = ?
            WHERE connector_id = ? AND version = ?
        """, (fields["name"], fields["description"], fields["trust_level"], int(fields["enabled"]), now,
              connector_id, version))


def report_connector_status(connector_id, status, *, reason=None, actor=None) -> ConnectorDescriptor:
    """The ONLY way a connector's status can ever become AVAILABLE."""
    if status not in CONNECTOR_STATUSES:
        raise ConnectorValidationError(f"unknown connector status {status!r}",
                                        [{"type": "INVALID_STATUS", "field": "status", "value": status}])
    current = get_connector(connector_id)
    if current is None:
        raise ConnectorNotFoundError(connector_id)
    now = _now()
    with _connect() as conn:
        conn.execute("""
            UPDATE jarvis_connectors SET status = ?, status_reason = ?, status_updated_at = ?, updated_at = ?
            WHERE connector_id = ? AND version = ?
        """, (status, reason, now, now, connector_id, current.version))
    _log_event(connector_id, current.version, "STATUS_REPORTED", actor, reason, {"status": status})
    return get_connector(connector_id)


def unregister_connector(connector_id, *, reason=None, actor=None) -> ConnectorDescriptor:
    current = get_connector(connector_id)
    if current is None:
        raise ConnectorNotFoundError(connector_id)
    if not current.enabled:
        return current
    now = _now()
    with _connect() as conn:
        conn.execute("""
            UPDATE jarvis_connectors SET enabled = 0, disabled_reason = ?, disabled_at = ?, updated_at = ?
            WHERE connector_id = ? AND version = ?
        """, (reason, now, now, connector_id, current.version))
    _log_event(connector_id, current.version, "DISABLED", actor, reason, {})
    return get_connector(connector_id)


def enable_connector(connector_id, *, actor=None) -> ConnectorDescriptor:
    current = get_connector(connector_id)
    if current is None:
        raise ConnectorNotFoundError(connector_id)
    if current.enabled:
        return current
    now = _now()
    with _connect() as conn:
        conn.execute("""
            UPDATE jarvis_connectors SET enabled = 1, disabled_reason = NULL, disabled_at = NULL, updated_at = ?
            WHERE connector_id = ? AND version = ?
        """, (now, connector_id, current.version))
    _log_event(connector_id, current.version, "ENABLED", actor, None, {})
    return get_connector(connector_id)


# ---------------------------------------------------------------------------
# Read / lookup
# ---------------------------------------------------------------------------

def get_connector(connector_id) -> ConnectorDescriptor:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM jarvis_connectors WHERE connector_id = ? ORDER BY version DESC LIMIT 1", (connector_id,)
        ).fetchone()
    return _row_to_connector(row) if row else None


def get_connector_version(connector_id, version) -> ConnectorDescriptor:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM jarvis_connectors WHERE connector_id = ? AND version = ?", (connector_id, version)
        ).fetchone()
    return _row_to_connector(row) if row else None


def list_connector_versions(connector_id) -> list:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM jarvis_connectors WHERE connector_id = ? ORDER BY version ASC", (connector_id,)
        ).fetchall()
    return [_row_to_connector(r) for r in rows]


def list_connectors(*, enabled_only=False) -> list:
    with _connect() as conn:
        rows = conn.execute("""
            SELECT c.* FROM jarvis_connectors c
            WHERE c.version = (SELECT MAX(c2.version) FROM jarvis_connectors c2 WHERE c2.connector_id = c.connector_id)
            ORDER BY c.connector_id ASC
        """).fetchall()
    result = [_row_to_connector(r) for r in rows]
    if enabled_only:
        result = [c for c in result if c.enabled]
    return result


def lookup_connectors_by_capability(capability) -> list:
    return [c for c in list_connectors() if capability in c.capabilities]


def validate_connector_availability(connector_id) -> dict:
    """Same fail-closed shape as tools.validate_tool_availability() - never
    raises except for the one TRANSACTION_PROHIBITED case handled by
    assert_connector_usable() below."""
    connector = get_connector(connector_id)
    if connector is None:
        return {"connector_id": connector_id, "available": False, "reason_codes": ["UNKNOWN_CONNECTOR"], "connector": None}

    reason_codes = []
    matches = _scan_for_prohibited_text(connector.connector_id, connector.name, connector.description, connector.connector_type)
    if connector.transaction_capable or matches or connector.action_class == "FINANCIAL_TRANSACTION":
        reason_codes.append("TRANSACTION_PROHIBITED")
    if not connector.enabled:
        reason_codes.append("CONNECTOR_DISABLED")
    if connector.trust_level in NON_EXECUTABLE_TRUST_LEVELS:
        reason_codes.append("TRUST_LEVEL_NOT_EXECUTABLE")
    if connector.effective_status not in EXECUTABLE_CONNECTOR_STATUSES:
        reason_codes.append("CONNECTOR_NOT_AVAILABLE")

    return {"connector_id": connector_id, "available": not reason_codes, "reason_codes": reason_codes,
            "connector": connector.to_dict()}


def assert_connector_usable(connector_id) -> dict:
    availability = validate_connector_availability(connector_id)
    if "TRANSACTION_PROHIBITED" in availability["reason_codes"]:
        raise ConnectorTransactionProhibitedError(["defense-in-depth re-scan matched at point of use"])
    return availability
