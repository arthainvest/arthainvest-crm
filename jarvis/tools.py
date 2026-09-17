#!/usr/bin/env python3
"""
JARVIS Tool Registry — Stage K: one authoritative inventory of executable
tools and their security metadata.

    CAPABILITY (capabilities.py, Stage C)   - "does this ABILITY exist at all"
          |
    WORKER (workers.py, Stage D)            - "what CODE runs it"
          |
    TOOL (this file, Stage K)               - "what EXACT executable identity
                                                is this, what is it allowed to
                                                do, what risk does it carry,
                                                what does it require, how is
                                                it verified, is it trusted"

Capability ≠ Worker ≠ Tool, by design:
  - a Capability (capabilities.py) says an ability exists and is available.
  - a Worker (workers.py) is the code that can execute a capability.
  - a Tool (this file) is a versioned, trust-scoped identity that WRAPS one
    (capability_id, worker_id) pairing with the rest of the security
    metadata Stage K's authorization asks for. Multiple Tools could in
    principle wrap the same capability (e.g. different trust tiers of the
    same underlying ability) - this file never assumes a 1:1 mapping.

This file reuses every existing taxonomy rather than inventing a second one:
action classes and risk levels come from approval.py (which itself reuses
plans.RISK_LEVELS); privacy scopes come from memory.VALID_PRIVACY_LEVELS;
the transaction-prohibition scan reuses backend/policy.py's
find_prohibited_routes - the exact function every other stage already
calls. Nothing here re-derives any of those from scratch.

## Registration is never authorization (the security invariant this file
## exists to hold)

A tool being registered - even as VERIFIED, even as enabled - does not by
itself permit anything to execute. Tool exists ≠ tool allowed. The eventual
chain is:

    Tool Registry -> Permission -> Approval -> Action Firewall -> Worker

The Action Firewall (action_firewall.py, Stage J) remains the final
execution gate; nothing in this file calls it, evaluates approval, or
executes a Worker. This file only describes -> resolves -> validates ->
authorizes METADATA (i.e. "is this tool's own identity currently
executable" - disabled? untrusted? transaction-shaped?) - never "should
THIS SPECIFIC ACTION, right now, actually run" (that question belongs
entirely to approval.py + action_firewall.py, unchanged).

## Trust levels

VERIFIED / TRUSTED / COMMUNITY / UNKNOWN / BLOCKED, per the master
architecture. UNKNOWN and BLOCKED can never execute - and trust is never
inferred from a tool's name/id/description; it is always an explicit,
deliberate value the caller passes at registration (defaulting to the
most conservative value, UNKNOWN, if omitted - fail closed, never assume
trustworthiness).

## Transaction prohibition - rejected at registration AND at execution

A tool that declares transaction_capable=True, or whose action_class is
FINANCIAL_TRANSACTION, or whose own text (name/description/ids) matches
backend/policy.py's prohibited-route patterns, is refused at
register_tool() time - it is never even persisted. validate_tool_availability()
re-runs the identical scan against whatever IS persisted, so even a record
that somehow bypassed register_tool() (e.g. inserted directly, as this
file's own tests deliberately do to prove this defense-in-depth layer is
real and not merely "registration already blocks it so this can't happen")
is still caught at the point of use. No second transaction vocabulary is
created anywhere in this file.

## Existing-worker compatibility (the lesson Stage J already learned once)

Every capability_id/worker_id used by a pre-existing test fixture or an
internal-only worker that was never meant to be catalogued is simply never
registered as a Tool here - and this file makes that the ENTIRE mechanism
for "not a production tool yet", rather than trying to detect it after the
fact. workers.py's own integration (see that file) only gates a
capability_id that resolves to an ACTUALLY REGISTERED Tool; a capability_id
with no registered Tool is completely unaffected, byte-for-byte, exactly
like every capability and internal test worker built before this stage.
This file's own validate_tool_metadata() never checks capability_id/
worker_id against capabilities.py's or any WorkerRegistry's catalog for
exactly this reason (and to avoid a circular import - workers.py imports
this file, so this file must never import workers.py back).

## Tool versioning

A tool's MATERIAL fields (capability_id, worker_id, action_class,
risk_level, transaction_capable, security_sensitive, side_effect_class,
required_permissions, required_privacy_scopes, verification_required,
idempotent, cancellable) define its semantic identity, hashed into
`schema_hash`. Changing any of them bumps `version` and produces a new
`schema_hash` - the OLD version's row is kept forever (get_tool_version(),
list_tool_versions()), never edited in place, so a tool's historical
meaning is never silently rewritten (the same principle plans.py already
applies to plan versions). Administrative fields (name, description,
connector_id, trust_level, enabled) can change in place without bumping
the version - re-trusting or disabling a tool is not a semantic change to
what it DOES.

workers.py folds a resolved Tool's own `tool_id`, `version`, and
`schema_hash` into the exact same fingerprinting mechanism Approval Gate
(Stage I) already owns (`material_params`, already part of
compute_action_fingerprint()) - so a materially changed tool automatically
invalidates a prior approval's fingerprint match, without approval.py
needing to know this file exists at all. No second invalidation mechanism
is built; the existing one is reused.

## What this file never does

Never executes a tool, a worker, or anything else. Never calls
approval.evaluate() or action_firewall.authorize() - composing those
remains workers.py's job (see that file's own Stage K integration), not
this file's. Never decides anything with an LLM. Never infers trust from
a name. Never assumes a capability_id/worker_id is legitimate just because
it looks like one that should exist.
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

import approval as appr  # noqa: E402 - reuses ACTION_CLASSES/RISK_LEVELS, never redefines them
import memory as mem  # noqa: E402 - reuses VALID_PRIVACY_LEVELS, never a second privacy taxonomy
from policy import find_prohibited_routes  # noqa: E402 - same single source of truth every other layer uses

DB_PATH = Path(__file__).resolve().parent / "jarvis.db"

TRUST_LEVELS = {"VERIFIED", "TRUSTED", "COMMUNITY", "UNKNOWN", "BLOCKED"}
NON_EXECUTABLE_TRUST_LEVELS = {"UNKNOWN", "BLOCKED"}  # never allowed to execute, regardless of anything else
EXECUTABLE_TRUST_LEVELS = TRUST_LEVELS - NON_EXECUTABLE_TRUST_LEVELS

SIDE_EFFECT_CLASSES = {"NONE", "INTERNAL", "EXTERNAL"}

# Reused, not reinvented - see approval.ACTION_CLASSES/RISK_LEVELS (which
# themselves reuse plans.RISK_LEVELS).
ACTION_CLASSES = appr.ACTION_CLASSES
RISK_LEVELS = appr.RISK_LEVELS

# A tool's semantic identity. Changing any of these is a MATERIAL change -
# it bumps `version` and changes `schema_hash`. Order matters for nothing
# except readability; comparison/hashing always treats this as a set of
# named fields, never positionally.
MATERIAL_FIELDS = (
    "capability_id", "worker_id", "action_class", "risk_level", "transaction_capable",
    "security_sensitive", "side_effect_class", "required_permissions", "required_privacy_scopes",
    "verification_required", "idempotent", "cancellable",
)

# Administrative metadata - can change in place without a version bump.
ADMINISTRATIVE_FIELDS = ("name", "description", "connector_id", "trust_level", "enabled")


def _now():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Errors (same canonical shape as every other jarvis/ stage)
# ---------------------------------------------------------------------------

@dataclass
class ErrorObject:
    code: str
    category: str
    severity: str = "ERROR"
    retryable: bool = False
    user_action_required: bool = False
    message: str = ""
    tool_id: str = None
    metadata: dict = field(default_factory=dict)
    error_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=_now)

    def to_dict(self):
        return asdict(self)


class ToolError(Exception):
    def __init__(self, error: ErrorObject):
        self.error = error
        super().__init__(error.message)


class ToolValidationError(ToolError):
    def __init__(self, message, tool_id=None, violations=None):
        super().__init__(ErrorObject(code="INVALID_INPUT", category="VALIDATION", tool_id=tool_id,
                                      message=message, metadata={"violations": violations or []}))


class ToolNotFoundError(ToolError):
    def __init__(self, tool_id):
        super().__init__(ErrorObject(code="TOOL_NOT_FOUND", category="STATE", tool_id=tool_id,
                                      message=f"No tool {tool_id!r} is registered."))


class ToolTransactionProhibitedError(ToolError):
    """Raised at register_tool() time (never persisted) AND re-raised by
    assert_tool_executable() at use time (defense in depth, same technique
    every other stage uses) - a transaction-shaped tool is refused
    regardless of registration, trust level, or anything else."""

    def __init__(self, tool_id, matches):
        super().__init__(ErrorObject(
            code="TRANSACTION_PROHIBITED", category="POLICY", severity="CRITICAL", retryable=False,
            tool_id=tool_id,
            message="This tool is financial-transaction-shaped and can never be registered or executed.",
            metadata={"matches": matches},
        ))


class ToolConflictError(ToolError):
    """A concurrent registration race exhausted its retry budget - the
    caller should re-read and retry, same as missions.py's StateConflictError."""

    def __init__(self, tool_id):
        super().__init__(ErrorObject(code="STATE_CONFLICT", category="CONCURRENCY", retryable=True, tool_id=tool_id,
                                      message=f"Tool {tool_id!r} registration was modified concurrently; retry."))


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@dataclass
class Tool:
    tool_id: str
    version: int
    name: str
    description: str
    capability_id: str
    worker_id: str
    action_class: str
    risk_level: str
    required_permissions: tuple
    required_privacy_scopes: tuple
    transaction_capable: bool
    security_sensitive: bool
    side_effect_class: str
    verification_required: bool
    idempotent: bool
    cancellable: bool
    connector_id: str
    trust_level: str
    enabled: bool
    schema_hash: str
    disabled_reason: str
    disabled_at: str
    created_at: str
    updated_at: str
    last_idempotency_key: str

    @property
    def approval_required(self) -> bool:
        # Derived, not stored independently - never a second approval-
        # requirement taxonomy alongside approval.py's own risk tiers.
        return self.risk_level in appr.APPROVAL_REQUIRED_RISK_LEVELS.union(appr.DENIED_RISK_LEVELS)

    def to_dict(self):
        d = asdict(self)
        d["approval_required"] = self.approval_required
        return d


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
    # Deliberately no cascade to missions/approval/firewall - this file
    # never calls into any of them at runtime, only reuses their constants
    # at import time (see module docstring: "must not execute tools").
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_tools (
                row_id TEXT PRIMARY KEY,
                tool_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                capability_id TEXT NOT NULL,
                worker_id TEXT NOT NULL,
                action_class TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                required_permissions TEXT NOT NULL,
                required_privacy_scopes TEXT NOT NULL,
                transaction_capable INTEGER NOT NULL DEFAULT 0,
                security_sensitive INTEGER NOT NULL DEFAULT 0,
                side_effect_class TEXT NOT NULL,
                verification_required INTEGER NOT NULL DEFAULT 0,
                idempotent INTEGER NOT NULL DEFAULT 0,
                cancellable INTEGER NOT NULL DEFAULT 0,
                connector_id TEXT,
                trust_level TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                schema_hash TEXT NOT NULL,
                disabled_reason TEXT,
                disabled_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_idempotency_key TEXT
            )
        """)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_tools_tool_version ON jarvis_tools(tool_id, version)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tools_capability ON jarvis_tools(capability_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tools_worker ON jarvis_tools(worker_id)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_tool_events (
                event_id TEXT PRIMARY KEY,
                tool_id TEXT NOT NULL,
                version INTEGER,
                event_type TEXT NOT NULL,
                actor TEXT,
                reason TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tool_events_tool ON jarvis_tool_events(tool_id)")


def _row_to_tool(row) -> Tool:
    d = dict(row)
    d.pop("row_id", None)
    d["required_permissions"] = tuple(json.loads(d["required_permissions"]))
    d["required_privacy_scopes"] = tuple(json.loads(d["required_privacy_scopes"]))
    d["transaction_capable"] = bool(d["transaction_capable"])
    d["security_sensitive"] = bool(d["security_sensitive"])
    d["verification_required"] = bool(d["verification_required"])
    d["idempotent"] = bool(d["idempotent"])
    d["cancellable"] = bool(d["cancellable"])
    d["enabled"] = bool(d["enabled"])
    return Tool(**d)


def _scan_for_prohibited_text(*texts) -> list:
    combined = " | ".join(t for t in texts if t)
    if not combined:
        return []
    return [pattern for _, pattern in find_prohibited_routes([combined])]


def compute_tool_schema_hash(fields: dict) -> str:
    """Deterministic - no timestamps/randomness. Sequence fields (permissions/
    privacy scopes) are sorted first so field ORDER never affects identity,
    only field CONTENT does."""
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
# Validate (pure - no DB access, usable standalone)
# ---------------------------------------------------------------------------

def validate_tool_metadata(fields: dict) -> list:
    """Returns a list of violation dicts; empty = valid. Deliberately never
    checks capability_id/worker_id against any external catalog (see
    module docstring's "existing-worker compatibility" section) - only
    format/presence and the taxonomies this file legitimately owns
    (action_class, risk_level, trust_level, side_effect_class, privacy
    scopes, field types)."""
    violations = []

    def _req_str(field_name):
        v = fields.get(field_name)
        if not isinstance(v, str) or not v.strip():
            violations.append({"type": "MISSING_REQUIRED_FIELD", "field": field_name})

    _req_str("tool_id")
    _req_str("name")
    _req_str("description")
    _req_str("capability_id")
    _req_str("worker_id")

    action_class = fields.get("action_class")
    if action_class not in ACTION_CLASSES:
        violations.append({
            "type": "MISSING_ACTION_CLASS" if action_class is None else "INVALID_ACTION_CLASS",
            "field": "action_class", "value": action_class,
        })

    risk_level = fields.get("risk_level")
    if risk_level not in RISK_LEVELS:
        violations.append({"type": "INVALID_RISK_LEVEL", "field": "risk_level", "value": risk_level})

    trust_level = fields.get("trust_level")
    if trust_level not in TRUST_LEVELS:
        violations.append({"type": "INVALID_TRUST_LEVEL", "field": "trust_level", "value": trust_level})

    side_effect_class = fields.get("side_effect_class")
    if side_effect_class not in SIDE_EFFECT_CLASSES:
        violations.append({"type": "INVALID_SIDE_EFFECT_CLASS", "field": "side_effect_class", "value": side_effect_class})

    for fname in ("required_permissions", "required_privacy_scopes"):
        v = fields.get(fname)
        if not isinstance(v, (tuple, list)):
            violations.append({"type": "INVALID_FIELD_TYPE", "field": fname})
        elif any(not isinstance(x, str) for x in v):
            violations.append({"type": "INVALID_FIELD_TYPE", "field": fname, "detail": "all entries must be strings"})

    privacy_scopes = fields.get("required_privacy_scopes") or ()
    if isinstance(privacy_scopes, (tuple, list)):
        bad_scopes = [s for s in privacy_scopes if s not in mem.VALID_PRIVACY_LEVELS]
        if bad_scopes:
            violations.append({"type": "INVALID_PRIVACY_SCOPE", "field": "required_privacy_scopes", "value": bad_scopes})

    for fname in ("transaction_capable", "security_sensitive", "verification_required",
                  "idempotent", "cancellable", "enabled"):
        if not isinstance(fields.get(fname), bool):
            violations.append({"type": "INVALID_FIELD_TYPE", "field": fname})

    return violations


# ---------------------------------------------------------------------------
# Register / unregister
# ---------------------------------------------------------------------------

def register_tool(tool_id, *, name, description, capability_id, worker_id, action_class, risk_level,
                   required_permissions=(), required_privacy_scopes=(), transaction_capable=False,
                   security_sensitive=False, side_effect_class="INTERNAL", verification_required=False,
                   idempotent=False, cancellable=False, connector_id=None, trust_level="UNKNOWN",
                   enabled=True, idempotency_key=None, actor=None) -> Tool:
    """Deterministic and fail-closed throughout:
      - invalid metadata -> ToolValidationError, nothing persisted.
      - transaction-shaped (declared OR text-scanned) -> ToolTransactionProhibitedError,
        nothing persisted, no override path.
      - identical re-registration (same tool_id, same everything) -> idempotent
        no-op, returns the existing row unchanged.
      - same tool_id, only administrative fields differ -> updated in place,
        version unchanged.
      - same tool_id, a MATERIAL field differs -> a new version is created;
        the old version's row is never edited (see module docstring)."""
    fields = {
        "tool_id": tool_id, "name": name, "description": description, "capability_id": capability_id,
        "worker_id": worker_id, "action_class": action_class, "risk_level": risk_level,
        "required_permissions": tuple(required_permissions or ()),
        "required_privacy_scopes": tuple(required_privacy_scopes or ()),
        "transaction_capable": bool(transaction_capable), "security_sensitive": bool(security_sensitive),
        "side_effect_class": side_effect_class, "verification_required": bool(verification_required),
        "idempotent": bool(idempotent), "cancellable": bool(cancellable), "connector_id": connector_id,
        "trust_level": trust_level, "enabled": bool(enabled),
    }

    violations = validate_tool_metadata(fields)
    if violations:
        raise ToolValidationError(f"invalid tool metadata for {tool_id!r}", tool_id=tool_id, violations=violations)

    matches = _scan_for_prohibited_text(tool_id, name, description, capability_id, worker_id)
    if fields["transaction_capable"] or matches or action_class == "FINANCIAL_TRANSACTION":
        raise ToolTransactionProhibitedError(
            tool_id, matches or (["transaction_capable=True"] if fields["transaction_capable"]
                                  else ["FINANCIAL_TRANSACTION action_class"]))

    if idempotency_key:
        with _connect() as conn:
            row = conn.execute(
                "SELECT * FROM jarvis_tools WHERE tool_id = ? AND last_idempotency_key = ? "
                "ORDER BY version DESC LIMIT 1", (tool_id, idempotency_key),
            ).fetchone()
        if row:
            return _row_to_tool(row)

    now = _now()
    schema_hash = compute_tool_schema_hash(fields)
    current = get_tool(tool_id)

    if current is None:
        version = _insert_new_version(tool_id, fields, schema_hash, now, idempotency_key)
        _log_event(tool_id, version, "REGISTERED", actor, None, {"schema_hash": schema_hash})
        return get_tool(tool_id)

    if _material_key(current) == _material_key(fields):
        if _admin_key(current) == _admin_key(fields):
            return current  # true duplicate registration - idempotent no-op, nothing changes
        _update_administrative(tool_id, current.version, fields, now)
        _log_event(tool_id, current.version, "UPDATED", actor, None, {"changed": "administrative"})
        return get_tool(tool_id)

    version = _insert_new_version(tool_id, fields, schema_hash, now, idempotency_key)
    _log_event(tool_id, version, "VERSIONED", actor, None, {
        "schema_hash": schema_hash, "previous_version": current.version,
        "previous_schema_hash": current.schema_hash,
    })
    return get_tool(tool_id)


def _insert_new_version(tool_id, fields, schema_hash, now, idempotency_key) -> int:
    """Retry-safe against a concurrent registration of the same tool_id:
    the UNIQUE(tool_id, version) index turns a race into a SQLite
    IntegrityError (two writers both trying to claim the same next
    version), and plain lock contention between concurrent connections to
    the same file surfaces as OperationalError - both are retried
    (re-reading the now-current max version each time) with a short
    backoff, up to 8 attempts, before failing closed with
    ToolConflictError. Never two rows silently claim the same version."""
    max_attempts = 8
    for attempt in range(max_attempts):
        try:
            with _connect() as conn:
                row = conn.execute(
                    "SELECT version FROM jarvis_tools WHERE tool_id = ? ORDER BY version DESC LIMIT 1", (tool_id,)
                ).fetchone()
                next_version = (row["version"] + 1) if row else 1
                conn.execute("""
                    INSERT INTO jarvis_tools
                        (row_id, tool_id, version, name, description, capability_id, worker_id, action_class,
                         risk_level, required_permissions, required_privacy_scopes, transaction_capable,
                         security_sensitive, side_effect_class, verification_required, idempotent, cancellable,
                         connector_id, trust_level, enabled, schema_hash, disabled_reason, disabled_at,
                         created_at, updated_at, last_idempotency_key)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (str(uuid4()), tool_id, next_version, fields["name"], fields["description"],
                      fields["capability_id"], fields["worker_id"], fields["action_class"], fields["risk_level"],
                      json.dumps(list(fields["required_permissions"])), json.dumps(list(fields["required_privacy_scopes"])),
                      int(fields["transaction_capable"]), int(fields["security_sensitive"]), fields["side_effect_class"],
                      int(fields["verification_required"]), int(fields["idempotent"]), int(fields["cancellable"]),
                      fields["connector_id"], fields["trust_level"], int(fields["enabled"]), schema_hash,
                      None, None, now, now, idempotency_key))
            return next_version
        except (sqlite3.IntegrityError, sqlite3.OperationalError):
            if attempt == max_attempts - 1:
                raise ToolConflictError(tool_id)
            time.sleep(0.01 * (attempt + 1))
            continue
    raise ToolConflictError(tool_id)


def _update_administrative(tool_id, version, fields, now):
    with _connect() as conn:
        conn.execute("""
            UPDATE jarvis_tools SET name = ?, description = ?, connector_id = ?, trust_level = ?,
                                     enabled = ?, updated_at = ?
            WHERE tool_id = ? AND version = ?
        """, (fields["name"], fields["description"], fields["connector_id"], fields["trust_level"],
              int(fields["enabled"]), now, tool_id, version))


def unregister_tool(tool_id, *, reason=None, actor=None) -> Tool:
    """Soft-disable only - never deletes a tool's history. Idempotent:
    disabling an already-disabled tool is a no-op, same pattern as
    approval.cancel_approval()."""
    current = get_tool(tool_id)
    if current is None:
        raise ToolNotFoundError(tool_id)
    if not current.enabled:
        return current
    now = _now()
    with _connect() as conn:
        conn.execute("""
            UPDATE jarvis_tools SET enabled = 0, disabled_reason = ?, disabled_at = ?, updated_at = ?
            WHERE tool_id = ? AND version = ?
        """, (reason, now, now, tool_id, current.version))
    _log_event(tool_id, current.version, "DISABLED", actor, reason, {})
    return get_tool(tool_id)


def enable_tool(tool_id, *, actor=None) -> Tool:
    """Symmetric re-enable - kept narrow (no metadata changes here; use
    register_tool() again for that) and equally idempotent."""
    current = get_tool(tool_id)
    if current is None:
        raise ToolNotFoundError(tool_id)
    if current.enabled:
        return current
    now = _now()
    with _connect() as conn:
        conn.execute("""
            UPDATE jarvis_tools SET enabled = 1, disabled_reason = NULL, disabled_at = NULL, updated_at = ?
            WHERE tool_id = ? AND version = ?
        """, (now, tool_id, current.version))
    _log_event(tool_id, current.version, "ENABLED", actor, None, {})
    return get_tool(tool_id)


# ---------------------------------------------------------------------------
# Read / lookup / resolve
# ---------------------------------------------------------------------------

def get_tool(tool_id) -> Tool:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jarvis_tools WHERE tool_id = ? ORDER BY version DESC LIMIT 1", (tool_id,)).fetchone()
    return _row_to_tool(row) if row else None


def get_tool_version(tool_id, version) -> Tool:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jarvis_tools WHERE tool_id = ? AND version = ?", (tool_id, version)).fetchone()
    return _row_to_tool(row) if row else None


def list_tool_versions(tool_id) -> list:
    """The tool's own version history - its audit trail for schema/material
    changes specifically (see list_tool_events() for register/disable/enable
    events, a distinct but complementary audit trail)."""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM jarvis_tools WHERE tool_id = ? ORDER BY version ASC", (tool_id,)).fetchall()
    return [_row_to_tool(r) for r in rows]


def list_tools(*, enabled_only=False) -> list:
    """Deterministic: always the latest version of every distinct tool_id,
    sorted by tool_id."""
    with _connect() as conn:
        rows = conn.execute("""
            SELECT t.* FROM jarvis_tools t
            WHERE t.version = (SELECT MAX(t2.version) FROM jarvis_tools t2 WHERE t2.tool_id = t.tool_id)
            ORDER BY t.tool_id ASC
        """).fetchall()
    result = [_row_to_tool(r) for r in rows]
    if enabled_only:
        result = [t for t in result if t.enabled]
    return result


def lookup_by_capability(capability_id) -> list:
    return [t for t in list_tools() if t.capability_id == capability_id]


def lookup_by_worker(worker_id) -> list:
    return [t for t in list_tools() if t.worker_id == worker_id]


def approval_material_params(tool: Tool, extra: dict = None) -> dict:
    """The material_params a caller SHOULD merge into an approval request
    (approval.request_approval()/evaluate()) for a tool-backed capability,
    so the approval's fingerprint is sensitive to this tool's exact
    version - a plain, public, documented key (`tool_version`), not a
    hidden one. workers.py's own Tool Registry integration merges this
    same dict before calling action_firewall.authorize(), so a version
    bump changes `tool_version`, which changes the fingerprint
    compute_action_fingerprint() already owns (Stage I), which invalidates
    a prior approval for the old version - reusing that existing
    mechanism rather than building a second one."""
    merged = dict(extra or {})
    merged["tool_version"] = tool.version
    return merged


def resolve_tool_identity(*, tool_id=None, capability_id=None, worker_id=None) -> Tool:
    """Deterministic identity resolution - never guesses. An exact tool_id
    always wins. Otherwise, resolves only if capability_id/worker_id (any
    combination given) narrows to EXACTLY one tool; any ambiguity or zero
    match returns None rather than picking one arbitrarily (fail closed,
    per this stage's "no arbitrary execution" mandate)."""
    if tool_id:
        return get_tool(tool_id)

    candidates = None
    if capability_id is not None:
        candidates = {t.tool_id for t in lookup_by_capability(capability_id)}
    if worker_id is not None:
        by_worker = {t.tool_id for t in lookup_by_worker(worker_id)}
        candidates = by_worker if candidates is None else (candidates & by_worker)

    if not candidates or len(candidates) != 1:
        return None
    return get_tool(next(iter(candidates)))


# ---------------------------------------------------------------------------
# Validate availability (metadata-level authorization - never the final
# execution decision, which stays with approval.py + action_firewall.py)
# ---------------------------------------------------------------------------

def validate_tool_availability(tool_id) -> dict:
    """Read-only, never mutates, never raises for anything except the one
    case that must always be a hard stop everywhere (see below). Returns
    {"tool_id", "available", "reason_codes", "tool"} - "available" is False
    the instant ANY reason_code is present; there is no partial-available
    state."""
    tool = get_tool(tool_id)
    if tool is None:
        return {"tool_id": tool_id, "available": False, "reason_codes": ["UNKNOWN_TOOL"], "tool": None}

    reason_codes = []
    matches = _scan_for_prohibited_text(tool.tool_id, tool.name, tool.description, tool.capability_id, tool.worker_id)
    if tool.transaction_capable or matches or tool.action_class == "FINANCIAL_TRANSACTION":
        reason_codes.append("TRANSACTION_PROHIBITED")
    if not tool.enabled:
        reason_codes.append("TOOL_DISABLED")
    if tool.trust_level in NON_EXECUTABLE_TRUST_LEVELS:
        reason_codes.append("TRUST_LEVEL_NOT_EXECUTABLE")

    return {"tool_id": tool_id, "available": not reason_codes, "reason_codes": reason_codes, "tool": tool.to_dict()}


def assert_tool_executable(tool_id) -> dict:
    """Same result as validate_tool_availability(), except TRANSACTION_PROHIBITED
    is raised (never returned as a soft denial) - the hard-stop treatment
    every other stage already gives this one category, applied here too.
    Every other reason (disabled, untrusted, unknown) is returned normally
    for the caller (workers.py) to act on."""
    availability = validate_tool_availability(tool_id)
    if "TRANSACTION_PROHIBITED" in availability["reason_codes"]:
        raise ToolTransactionProhibitedError(tool_id, ["defense-in-depth re-scan matched at point of use"])
    return availability


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------

def _log_event(tool_id, version, event_type, actor, reason, metadata):
    with _connect() as conn:
        conn.execute("""
            INSERT INTO jarvis_tool_events (event_id, tool_id, version, event_type, actor, reason, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid4()), tool_id, version, event_type, actor, reason, json.dumps(metadata or {}), _now()))


def list_tool_events(tool_id) -> list:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM jarvis_tool_events WHERE tool_id = ? ORDER BY created_at ASC", (tool_id,)).fetchall()
    events = []
    for r in rows:
        d = dict(r)
        d["metadata"] = json.loads(d["metadata"]) if d["metadata"] else {}
        events.append(d)
    return events
