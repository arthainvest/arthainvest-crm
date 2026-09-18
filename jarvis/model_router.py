#!/usr/bin/env python3
"""
JARVIS Model Router — Stage L: a provider-agnostic router that answers one
question — "which registered model/provider should perform this reasoning
task, under the current capability, quality, latency, privacy, reliability,
and resource constraints?" — and nothing else.

    MISSION / TASK
          |
    MODEL ROUTER (this file - route())
          |
    MODEL POLICY (RoutingPolicy - deterministic scoring/tie-break)
          |
    MODEL PROVIDER (an injected adapter - never called by this file)
          |
    MODEL CALL (a caller's own choice, after route() returns)
          |
    STRUCTURED RESULT (ModelResponse)
          |
    VALIDATION (validate_model_response() - structural only, never semantic)

## The one architectural invariant this stage exists to hold

The Model Router does not become the LLM, and it cannot authorize anything.
It NEVER imports missions.py, approval.py, action_firewall.py,
intent_lock.py, tools.py, workers.py, supervisor.py, recovery.py, or
verifier.py - not "doesn't call them today", literally does not have a
reference to any of them anywhere in this file. A model's output, however
adversarial, cannot reach permissions, policy, approval state, intent
locks, firewall rules, or the tool registry THROUGH THIS MODULE, because
there is no code path here that touches any of them at all. This is
checked structurally by this file's own tests, the same way
jarvis/tests/test_jarvis_cannot_touch_transactions.py structurally checks
the whole package for network imports.

`route()` only ever SELECTS - it never INVOKES. The `ModelProvider`
adapter interface declares `invoke()`, but nothing in this file ever calls
it; a caller who receives a `RoutingDecision` may choose to call
`decision`-referenced adapter's `invoke()` themselves, entirely outside
this module. The Model Router therefore cannot execute a tool, a worker,
or a model call, and "the model recommends X" is never the same claim as
"X is authorized" - that gate remains entirely with Approval Gate (Stage
I) and Action Firewall (Stage J), completely undisturbed by this stage.

## No fake providers

Registering a provider or a model is never the same claim as it being
usable. A provider's `status` starts at `REGISTERED` and can ONLY change
via `report_provider_status()` - register_provider() itself has no way to
set status to `AVAILABLE`, simulating the honest fact that this package
has no network access and cannot confirm a provider is reachable merely
by being told its name. Only `AVAILABLE` is ever selectable; `REGISTERED`
(never confirmed), `UNAVAILABLE`, `AUTH_REQUIRED`, `DISABLED`,
`RATE_LIMITED`, and `FAILED` are all equally unusable to the router - the
router does not distinguish "close to usable" from "not usable", per
Section 6's warning against manufacturing responses.

## Reused, not reinvented

Privacy scopes are `memory.VALID_PRIVACY_LEVELS` directly - no second
privacy taxonomy. The transaction-prohibition scan reuses
`backend/policy.py`'s `find_prohibited_routes`, the exact function every
other stage already calls - checked first, before any registry lookup,
and raised (never a soft outcome), matching every prior stage's treatment
of this one category.

## Deterministic routing

Given an identical request, registry state, policy, and availability
state, `route()` always returns the identical decision - no randomness,
no timestamps inside the selection logic itself (only recorded, after the
fact, in the persisted decision's own `created_at`). Ties are broken by
`(provider_id, model_id)` ascending, never arbitrarily.

## Fallback is availability-only

Fallback candidates are other REGISTERED, qualifying models the router
would have picked next - never a path to bypass Action Firewall, Approval
Gate, or the Tool Registry. This file cannot re-attempt a failed tool
execution with "a different model" to route around anything, because it
has no reference to the Worker Runtime at all.
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

import memory as mem  # noqa: E402 - reuses VALID_PRIVACY_LEVELS, never a second privacy taxonomy
from policy import find_prohibited_routes  # noqa: E402 - same single source of truth every other layer uses

DB_PATH = Path(__file__).resolve().parent / "jarvis.db"

PROVIDER_STATUSES = {"REGISTERED", "AVAILABLE", "UNAVAILABLE", "AUTH_REQUIRED", "DISABLED", "RATE_LIMITED", "FAILED"}
EXECUTABLE_PROVIDER_STATUSES = {"AVAILABLE"}  # the only status the router will ever select against

QUALITY_TIERS = ("BASIC", "STANDARD", "ADVANCED", "FRONTIER")
QUALITY_RANK = {tier: i for i, tier in enumerate(QUALITY_TIERS)}

LATENCY_CLASSES = ("FAST", "STANDARD", "SLOW")
LATENCY_RANK = {cls: i for i, cls in enumerate(LATENCY_CLASSES)}

OUTCOMES = {"ROUTED", "NO_COMPATIBLE_MODEL"}

REASON_CODES = {
    "MISSING_REQUIRED_CAPABILITY", "INVALID_PREFERENCE", "PREFERRED_MODEL_SELECTED",
    "PREFERRED_MODEL_UNAVAILABLE", "ROUTED_BY_POLICY", "NO_CAPABILITY_MATCH",
    "NO_AVAILABLE_PROVIDER", "PRIVACY_MISMATCH", "NO_MODALITY_MATCH", "NO_QUALITY_MATCH",
    "NO_LATENCY_MATCH", "NO_CONTEXT_MATCH", "COST_CONSTRAINT_UNMET",
}

# A model's semantic identity - changing any of these bumps its version and
# schema_hash. Providers are deliberately NOT versioned this way (see
# module docstring's registry design note): a provider has almost no
# material shape of its own beyond its own identity, so only models get
# the full versioned-history treatment, mirroring tools.py's own scoping
# decision to version the richer entity, not the thinner one.
MODEL_MATERIAL_FIELDS = (
    "provider_id", "capabilities", "context_capacity", "modality", "quality_tier",
    "latency_class", "privacy_scopes", "cost_per_unit", "reliability_score",
)
MODEL_ADMINISTRATIVE_FIELDS = ("name", "description", "enabled")


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
    metadata: dict = field(default_factory=dict)
    error_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=_now)

    def to_dict(self):
        return asdict(self)


class ModelRouterError(Exception):
    def __init__(self, error: ErrorObject):
        self.error = error
        super().__init__(error.message)


class ModelRouterValidationError(ModelRouterError):
    def __init__(self, message, violations=None):
        super().__init__(ErrorObject(code="INVALID_INPUT", category="VALIDATION", message=message,
                                      metadata={"violations": violations or []}))


class ProviderNotFoundError(ModelRouterError):
    def __init__(self, provider_id):
        super().__init__(ErrorObject(code="PROVIDER_NOT_FOUND", category="STATE",
                                      message=f"No provider {provider_id!r} is registered."))


class ModelNotFoundError(ModelRouterError):
    def __init__(self, model_id):
        super().__init__(ErrorObject(code="MODEL_NOT_FOUND", category="STATE",
                                      message=f"No model {model_id!r} is registered."))


class ModelRouterConflictError(ModelRouterError):
    def __init__(self, entity_id):
        super().__init__(ErrorObject(code="STATE_CONFLICT", category="CONCURRENCY", retryable=True,
                                      message=f"{entity_id!r} registration was modified concurrently; retry."))


class ModelRouterTransactionProhibitedError(ModelRouterError):
    """Checked FIRST, before any registry lookup - a transaction-shaped
    routing request is refused unconditionally, exactly like every other
    stage's treatment of this one category. Never rescuable by a
    preference, a fallback, or anything else."""

    def __init__(self, matches):
        super().__init__(ErrorObject(
            code="TRANSACTION_PROHIBITED", category="POLICY", severity="CRITICAL", retryable=False,
            message="This routing request is financial-transaction-shaped and can never be routed.",
            metadata={"matches": matches},
        ))


# ---------------------------------------------------------------------------
# Public domain types
# ---------------------------------------------------------------------------

@dataclass
class ModelRequest:
    """Routing input. Only `required_capability` is mandatory - every other
    dimension narrows the candidate pool only if supplied."""
    required_capability: str
    task_type: str = None
    quality_requirement: str = None
    latency_requirement: str = None
    min_context_capacity: int = None
    required_modality: str = None
    privacy_scope: str = None
    max_cost: float = None
    preferred_provider_id: str = None
    preferred_model_id: str = None
    fallback_allowed: bool = True
    user_id: str = None

    def to_dict(self):
        return asdict(self)


@dataclass
class ModelResponse:
    """A structural type only - route() never produces one. A caller who
    invokes a ModelProvider adapter themselves, after receiving a
    RoutingDecision, may use this shape and validate_model_response() to
    normalize/sanity-check what came back."""
    decision_id: str
    provider_id: str
    model_id: str
    content: object
    finish_reason: str = None
    usage: dict = field(default_factory=dict)
    latency_ms: float = None
    raw_metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def validate_model_response(response: ModelResponse) -> list:
    """Purely structural - checks presence/shape only. Deliberately never
    inspects `content`/`raw_metadata` for anything resembling an
    authorization, approval, or permission signal: a model's output cannot
    authorize an action by claiming to, because nothing here (or anywhere
    in this file) ever reads it that way. Returns a list of violations;
    empty = structurally valid."""
    violations = []
    if not isinstance(response.decision_id, str) or not response.decision_id.strip():
        violations.append({"type": "MISSING_REQUIRED_FIELD", "field": "decision_id"})
    if not isinstance(response.provider_id, str) or not response.provider_id.strip():
        violations.append({"type": "MISSING_REQUIRED_FIELD", "field": "provider_id"})
    if not isinstance(response.model_id, str) or not response.model_id.strip():
        violations.append({"type": "MISSING_REQUIRED_FIELD", "field": "model_id"})
    if response.content is None:
        violations.append({"type": "MISSING_REQUIRED_FIELD", "field": "content"})
    return violations


class ModelProvider:
    """The injected provider adapter interface (abstract base). A concrete
    subclass is where any real network call would eventually live - this
    file never imports anything network-capable and never instantiates a
    real one; tests use trivial in-memory fakes. `route()` never calls
    either method on this class - see module docstring."""

    provider_id: str = None

    def check_status(self) -> str:
        """Must return a value from PROVIDER_STATUSES. Never fabricate
        AVAILABLE - only report it if genuinely confirmed. No network call
        happens inside jarvis/ itself."""
        raise NotImplementedError

    def invoke(self, request: ModelRequest) -> ModelResponse:
        """Never called by this module. A caller holding a RoutingDecision
        may call this directly, entirely outside route()."""
        raise NotImplementedError


@dataclass
class RoutingPolicy:
    policy_version: str
    quality_weight: float = 10.0
    latency_weight: float = 5.0
    reliability_weight: float = 8.0
    cost_weight: float = 3.0

    def to_dict(self):
        return asdict(self)


DEFAULT_ROUTING_POLICY = RoutingPolicy(policy_version="v1")


@dataclass
class RoutingDecision:
    decision_id: str
    outcome: str  # ROUTED | NO_COMPATIBLE_MODEL
    selected_provider_id: str
    selected_model_id: str
    reason_codes: list
    policy_version: str
    capability_match: bool
    privacy_match: bool
    availability_status: str
    fallback_candidates: list
    required_capability: str
    task_type: str
    user_id: str
    created_at: str

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

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
    # Deliberately no cascade to any other jarvis/ module - this file has
    # no dependency on missions/approval/firewall/intent_lock/tools at all.
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_model_providers (
                provider_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                auth_configured INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'REGISTERED',
                status_reason TEXT,
                status_updated_at TEXT,
                disabled_reason TEXT,
                disabled_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_idempotency_key TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_model_records (
                row_id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                provider_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                capabilities TEXT NOT NULL,
                context_capacity INTEGER NOT NULL,
                modality TEXT NOT NULL,
                quality_tier TEXT NOT NULL,
                latency_class TEXT NOT NULL,
                privacy_scopes TEXT NOT NULL,
                cost_per_unit REAL,
                reliability_score REAL NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                schema_hash TEXT NOT NULL,
                disabled_reason TEXT,
                disabled_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_idempotency_key TEXT
            )
        """)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_model_records_id_version ON jarvis_model_records(model_id, version)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_model_records_provider ON jarvis_model_records(provider_id)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_model_router_events (
                event_id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                version INTEGER,
                event_type TEXT NOT NULL,
                actor TEXT,
                reason TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_router_events_entity ON jarvis_model_router_events(entity_type, entity_id)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_routing_decisions (
                decision_id TEXT PRIMARY KEY,
                outcome TEXT NOT NULL,
                selected_provider_id TEXT,
                selected_model_id TEXT,
                reason_codes TEXT NOT NULL,
                policy_version TEXT NOT NULL,
                capability_match INTEGER NOT NULL,
                privacy_match INTEGER NOT NULL,
                availability_status TEXT,
                fallback_candidates TEXT NOT NULL,
                required_capability TEXT,
                task_type TEXT,
                user_id TEXT,
                created_at TEXT NOT NULL
            )
        """)


def _log_event(entity_type, entity_id, version, event_type, actor, reason, metadata):
    with _connect() as conn:
        conn.execute("""
            INSERT INTO jarvis_model_router_events
                (event_id, entity_type, entity_id, version, event_type, actor, reason, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid4()), entity_type, entity_id, version, event_type, actor, reason,
              json.dumps(metadata or {}), _now()))


def list_router_events(entity_type, entity_id) -> list:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM jarvis_model_router_events WHERE entity_type = ? AND entity_id = ? ORDER BY created_at ASC",
            (entity_type, entity_id),
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


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------

@dataclass
class ProviderRecord:
    provider_id: str
    name: str
    description: str
    enabled: bool
    auth_configured: bool
    status: str
    status_reason: str
    status_updated_at: str
    disabled_reason: str
    disabled_at: str
    created_at: str
    updated_at: str
    last_idempotency_key: str

    @property
    def effective_status(self) -> str:
        """DISABLED always wins over whatever status was last reported -
        an operator turning a provider off must never be silently
        overridden by a stale AVAILABLE report."""
        return "DISABLED" if not self.enabled else self.status

    def to_dict(self):
        d = asdict(self)
        d["effective_status"] = self.effective_status
        return d


def _row_to_provider(row) -> ProviderRecord:
    d = dict(row)
    d["enabled"] = bool(d["enabled"])
    d["auth_configured"] = bool(d["auth_configured"])
    return ProviderRecord(**d)


def validate_provider_metadata(fields: dict) -> list:
    violations = []
    for f in ("provider_id", "name", "description"):
        v = fields.get(f)
        if not isinstance(v, str) or not v.strip():
            violations.append({"type": "MISSING_REQUIRED_FIELD", "field": f})
    for f in ("enabled", "auth_configured"):
        if not isinstance(fields.get(f), bool):
            violations.append({"type": "INVALID_FIELD_TYPE", "field": f})
    return violations


def register_provider(provider_id, *, name, description, enabled=True, auth_configured=False,
                       idempotency_key=None, actor=None) -> ProviderRecord:
    """Status always starts REGISTERED regardless of `auth_configured` -
    that flag is honest metadata about whether config exists, never a
    claim that the provider has been confirmed reachable. Only
    report_provider_status() can change status. Idempotent: re-registering
    with identical fields is a no-op; changed administrative fields update
    in place (a provider has no material/versioned shape of its own, see
    module docstring)."""
    fields = {"provider_id": provider_id, "name": name, "description": description,
              "enabled": bool(enabled), "auth_configured": bool(auth_configured)}
    violations = validate_provider_metadata(fields)
    if violations:
        raise ModelRouterValidationError(f"invalid provider metadata for {provider_id!r}", violations)

    matches = _scan_for_prohibited_text(provider_id, name, description)
    if matches:
        raise ModelRouterTransactionProhibitedError(matches)

    if idempotency_key:
        with _connect() as conn:
            row = conn.execute(
                "SELECT * FROM jarvis_model_providers WHERE provider_id = ? AND last_idempotency_key = ?",
                (provider_id, idempotency_key),
            ).fetchone()
        if row:
            return _row_to_provider(row)

    now = _now()
    current = get_provider(provider_id)
    if current is not None:
        unchanged = (current.name == name and current.description == description
                     and current.enabled == bool(enabled) and current.auth_configured == bool(auth_configured))
        if unchanged:
            return current
        with _connect() as conn:
            conn.execute("""
                UPDATE jarvis_model_providers
                SET name = ?, description = ?, enabled = ?, auth_configured = ?, updated_at = ?
                WHERE provider_id = ?
            """, (name, description, int(enabled), int(auth_configured), now, provider_id))
        _log_event("provider", provider_id, None, "UPDATED", actor, None, {})
        return get_provider(provider_id)

    with _connect() as conn:
        conn.execute("""
            INSERT INTO jarvis_model_providers
                (provider_id, name, description, enabled, auth_configured, status, status_reason,
                 status_updated_at, disabled_reason, disabled_at, created_at, updated_at, last_idempotency_key)
            VALUES (?, ?, ?, ?, ?, 'REGISTERED', NULL, NULL, NULL, NULL, ?, ?, ?)
        """, (provider_id, name, description, int(enabled), int(auth_configured), now, now, idempotency_key))
    _log_event("provider", provider_id, None, "REGISTERED", actor, None, {})
    return get_provider(provider_id)


def get_provider(provider_id) -> ProviderRecord:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jarvis_model_providers WHERE provider_id = ?", (provider_id,)).fetchone()
    return _row_to_provider(row) if row else None


def list_providers(*, enabled_only=False) -> list:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM jarvis_model_providers ORDER BY provider_id ASC").fetchall()
    result = [_row_to_provider(r) for r in rows]
    if enabled_only:
        result = [p for p in result if p.enabled]
    return result


def report_provider_status(provider_id, status, *, reason=None, actor=None) -> ProviderRecord:
    """The ONLY way a provider's status can ever become AVAILABLE. In
    production this would be called by a future connector/health-check
    layer after a genuine confirmation - this file makes no such call
    itself, it only records what it is told."""
    if status not in PROVIDER_STATUSES:
        raise ModelRouterValidationError(f"unknown provider status {status!r}",
                                          [{"type": "INVALID_STATUS", "field": "status", "value": status}])
    current = get_provider(provider_id)
    if current is None:
        raise ProviderNotFoundError(provider_id)
    now = _now()
    with _connect() as conn:
        conn.execute("""
            UPDATE jarvis_model_providers SET status = ?, status_reason = ?, status_updated_at = ?, updated_at = ?
            WHERE provider_id = ?
        """, (status, reason, now, now, provider_id))
    _log_event("provider", provider_id, None, "STATUS_REPORTED", actor, reason, {"status": status})
    return get_provider(provider_id)


def unregister_provider(provider_id, *, reason=None, actor=None) -> ProviderRecord:
    current = get_provider(provider_id)
    if current is None:
        raise ProviderNotFoundError(provider_id)
    if not current.enabled:
        return current
    now = _now()
    with _connect() as conn:
        conn.execute("""
            UPDATE jarvis_model_providers SET enabled = 0, disabled_reason = ?, disabled_at = ?, updated_at = ?
            WHERE provider_id = ?
        """, (reason, now, now, provider_id))
    _log_event("provider", provider_id, None, "DISABLED", actor, reason, {})
    return get_provider(provider_id)


def enable_provider(provider_id, *, actor=None) -> ProviderRecord:
    current = get_provider(provider_id)
    if current is None:
        raise ProviderNotFoundError(provider_id)
    if current.enabled:
        return current
    now = _now()
    with _connect() as conn:
        conn.execute("""
            UPDATE jarvis_model_providers SET enabled = 1, disabled_reason = NULL, disabled_at = NULL, updated_at = ?
            WHERE provider_id = ?
        """, (now, provider_id))
    _log_event("provider", provider_id, None, "ENABLED", actor, None, {})
    return get_provider(provider_id)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class ModelRecord:
    model_id: str
    version: int
    provider_id: str
    name: str
    description: str
    capabilities: tuple
    context_capacity: int
    modality: tuple
    quality_tier: str
    latency_class: str
    privacy_scopes: tuple
    cost_per_unit: float
    reliability_score: float
    enabled: bool
    schema_hash: str
    disabled_reason: str
    disabled_at: str
    created_at: str
    updated_at: str
    last_idempotency_key: str

    def to_dict(self):
        return asdict(self)


def _row_to_model(row) -> ModelRecord:
    d = dict(row)
    d.pop("row_id", None)
    d["capabilities"] = tuple(json.loads(d["capabilities"]))
    d["modality"] = tuple(json.loads(d["modality"]))
    d["privacy_scopes"] = tuple(json.loads(d["privacy_scopes"]))
    d["enabled"] = bool(d["enabled"])
    return ModelRecord(**d)


def compute_model_schema_hash(fields: dict) -> str:
    payload = {}
    for k in MODEL_MATERIAL_FIELDS:
        v = fields[k]
        payload[k] = sorted(v) if isinstance(v, (list, tuple)) else v
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _get(obj, key):
    return obj[key] if isinstance(obj, dict) else getattr(obj, key)


def _norm(v):
    return tuple(sorted(v)) if isinstance(v, (list, tuple)) else v


def _model_material_key(obj):
    return tuple(_norm(_get(obj, k)) for k in MODEL_MATERIAL_FIELDS)


def _model_admin_key(obj):
    return tuple(_get(obj, k) for k in MODEL_ADMINISTRATIVE_FIELDS)


def validate_model_metadata(fields: dict) -> list:
    violations = []
    for f in ("model_id", "provider_id", "name", "description"):
        v = fields.get(f)
        if not isinstance(v, str) or not v.strip():
            violations.append({"type": "MISSING_REQUIRED_FIELD", "field": f})

    capabilities = fields.get("capabilities")
    if not isinstance(capabilities, (tuple, list)) or not capabilities or any(
            not isinstance(c, str) or not c.strip() for c in capabilities):
        violations.append({"type": "INVALID_FIELD_TYPE", "field": "capabilities"})

    modality = fields.get("modality")
    if not isinstance(modality, (tuple, list)) or not modality or any(
            not isinstance(m, str) or not m.strip() for m in modality):
        violations.append({"type": "INVALID_FIELD_TYPE", "field": "modality"})

    context_capacity = fields.get("context_capacity")
    if not isinstance(context_capacity, int) or isinstance(context_capacity, bool) or context_capacity <= 0:
        violations.append({"type": "INVALID_FIELD_TYPE", "field": "context_capacity"})

    if fields.get("quality_tier") not in QUALITY_TIERS:
        violations.append({"type": "INVALID_QUALITY_TIER", "field": "quality_tier", "value": fields.get("quality_tier")})

    if fields.get("latency_class") not in LATENCY_CLASSES:
        violations.append({"type": "INVALID_LATENCY_CLASS", "field": "latency_class", "value": fields.get("latency_class")})

    privacy_scopes = fields.get("privacy_scopes")
    if not isinstance(privacy_scopes, (tuple, list)):
        violations.append({"type": "INVALID_FIELD_TYPE", "field": "privacy_scopes"})
    else:
        bad = [s for s in privacy_scopes if s not in mem.VALID_PRIVACY_LEVELS]
        if bad:
            violations.append({"type": "INVALID_PRIVACY_SCOPE", "field": "privacy_scopes", "value": bad})

    cost_per_unit = fields.get("cost_per_unit")
    if cost_per_unit is not None and (not isinstance(cost_per_unit, (int, float)) or isinstance(cost_per_unit, bool) or cost_per_unit < 0):
        violations.append({"type": "INVALID_FIELD_TYPE", "field": "cost_per_unit"})

    reliability_score = fields.get("reliability_score")
    if not isinstance(reliability_score, (int, float)) or isinstance(reliability_score, bool) or not (0.0 <= reliability_score <= 1.0):
        violations.append({"type": "INVALID_FIELD_TYPE", "field": "reliability_score"})

    if not isinstance(fields.get("enabled"), bool):
        violations.append({"type": "INVALID_FIELD_TYPE", "field": "enabled"})

    return violations


def register_model(model_id, *, provider_id, name, description, capabilities, context_capacity, modality,
                    quality_tier, latency_class, privacy_scopes=(), cost_per_unit=None, reliability_score=0.5,
                    enabled=True, idempotency_key=None, actor=None) -> ModelRecord:
    """Requires provider_id to reference an ALREADY-registered provider -
    unlike Tool Registry's deliberate avoidance of checking capability_id
    against an external catalog, ProviderRecord is THIS module's own
    registry, so checking existence within one's own domain does not
    create the "existing worker compatibility" trap Stage K was careful
    about; it is simply referential integrity within a single file."""
    fields = {
        "model_id": model_id, "provider_id": provider_id, "name": name, "description": description,
        "capabilities": tuple(capabilities or ()), "context_capacity": context_capacity,
        "modality": tuple(modality or ()), "quality_tier": quality_tier, "latency_class": latency_class,
        "privacy_scopes": tuple(privacy_scopes or ()), "cost_per_unit": cost_per_unit,
        "reliability_score": reliability_score, "enabled": bool(enabled),
    }
    violations = validate_model_metadata(fields)
    if violations:
        raise ModelRouterValidationError(f"invalid model metadata for {model_id!r}", violations)

    if get_provider(provider_id) is None:
        raise ProviderNotFoundError(provider_id)

    matches = _scan_for_prohibited_text(model_id, name, description, *fields["capabilities"])
    if matches:
        raise ModelRouterTransactionProhibitedError(matches)

    if idempotency_key:
        with _connect() as conn:
            row = conn.execute(
                "SELECT * FROM jarvis_model_records WHERE model_id = ? AND last_idempotency_key = ? "
                "ORDER BY version DESC LIMIT 1", (model_id, idempotency_key),
            ).fetchone()
        if row:
            return _row_to_model(row)

    now = _now()
    schema_hash = compute_model_schema_hash(fields)
    current = get_model(model_id)

    if current is None:
        version = _insert_model_version(model_id, fields, schema_hash, now, idempotency_key)
        _log_event("model", model_id, version, "REGISTERED", actor, None, {"schema_hash": schema_hash})
        return get_model(model_id)

    if _model_material_key(current) == _model_material_key(fields):
        if _model_admin_key(current) == _model_admin_key(fields):
            return current
        _update_model_administrative(model_id, current.version, fields, now)
        _log_event("model", model_id, current.version, "UPDATED", actor, None, {"changed": "administrative"})
        return get_model(model_id)

    version = _insert_model_version(model_id, fields, schema_hash, now, idempotency_key)
    _log_event("model", model_id, version, "VERSIONED", actor, None, {
        "schema_hash": schema_hash, "previous_version": current.version, "previous_schema_hash": current.schema_hash,
    })
    return get_model(model_id)


def _insert_model_version(model_id, fields, schema_hash, now, idempotency_key) -> int:
    max_attempts = 8
    for attempt in range(max_attempts):
        try:
            with _connect() as conn:
                row = conn.execute(
                    "SELECT version FROM jarvis_model_records WHERE model_id = ? ORDER BY version DESC LIMIT 1",
                    (model_id,),
                ).fetchone()
                next_version = (row["version"] + 1) if row else 1
                conn.execute("""
                    INSERT INTO jarvis_model_records
                        (row_id, model_id, version, provider_id, name, description, capabilities, context_capacity,
                         modality, quality_tier, latency_class, privacy_scopes, cost_per_unit, reliability_score,
                         enabled, schema_hash, disabled_reason, disabled_at, created_at, updated_at, last_idempotency_key)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (str(uuid4()), model_id, next_version, fields["provider_id"], fields["name"], fields["description"],
                      json.dumps(list(fields["capabilities"])), fields["context_capacity"],
                      json.dumps(list(fields["modality"])), fields["quality_tier"], fields["latency_class"],
                      json.dumps(list(fields["privacy_scopes"])), fields["cost_per_unit"], fields["reliability_score"],
                      int(fields["enabled"]), schema_hash, None, None, now, now, idempotency_key))
            return next_version
        except (sqlite3.IntegrityError, sqlite3.OperationalError):
            if attempt == max_attempts - 1:
                raise ModelRouterConflictError(model_id)
            time.sleep(0.01 * (attempt + 1))
            continue
    raise ModelRouterConflictError(model_id)


def _update_model_administrative(model_id, version, fields, now):
    with _connect() as conn:
        conn.execute("""
            UPDATE jarvis_model_records SET name = ?, description = ?, enabled = ?, updated_at = ?
            WHERE model_id = ? AND version = ?
        """, (fields["name"], fields["description"], int(fields["enabled"]), now, model_id, version))


def unregister_model(model_id, *, reason=None, actor=None) -> ModelRecord:
    current = get_model(model_id)
    if current is None:
        raise ModelNotFoundError(model_id)
    if not current.enabled:
        return current
    now = _now()
    with _connect() as conn:
        conn.execute("""
            UPDATE jarvis_model_records SET enabled = 0, disabled_reason = ?, disabled_at = ?, updated_at = ?
            WHERE model_id = ? AND version = ?
        """, (reason, now, now, model_id, current.version))
    _log_event("model", model_id, current.version, "DISABLED", actor, reason, {})
    return get_model(model_id)


def enable_model(model_id, *, actor=None) -> ModelRecord:
    current = get_model(model_id)
    if current is None:
        raise ModelNotFoundError(model_id)
    if current.enabled:
        return current
    now = _now()
    with _connect() as conn:
        conn.execute("""
            UPDATE jarvis_model_records SET enabled = 1, disabled_reason = NULL, disabled_at = NULL, updated_at = ?
            WHERE model_id = ? AND version = ?
        """, (now, model_id, current.version))
    _log_event("model", model_id, current.version, "ENABLED", actor, None, {})
    return get_model(model_id)


def get_model(model_id) -> ModelRecord:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jarvis_model_records WHERE model_id = ? ORDER BY version DESC LIMIT 1", (model_id,)).fetchone()
    return _row_to_model(row) if row else None


def get_model_version(model_id, version) -> ModelRecord:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jarvis_model_records WHERE model_id = ? AND version = ?", (model_id, version)).fetchone()
    return _row_to_model(row) if row else None


def list_model_versions(model_id) -> list:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM jarvis_model_records WHERE model_id = ? ORDER BY version ASC", (model_id,)).fetchall()
    return [_row_to_model(r) for r in rows]


def list_models(*, enabled_only=False) -> list:
    with _connect() as conn:
        rows = conn.execute("""
            SELECT m.* FROM jarvis_model_records m
            WHERE m.version = (SELECT MAX(m2.version) FROM jarvis_model_records m2 WHERE m2.model_id = m.model_id)
            ORDER BY m.model_id ASC
        """).fetchall()
    result = [_row_to_model(r) for r in rows]
    if enabled_only:
        result = [m for m in result if m.enabled]
    return result


def lookup_models_by_provider(provider_id) -> list:
    return [m for m in list_models() if m.provider_id == provider_id]


def lookup_models_by_capability(capability) -> list:
    return [m for m in list_models() if capability in m.capabilities]


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def _score(model: ModelRecord, policy: RoutingPolicy) -> float:
    quality_rank = QUALITY_RANK[model.quality_tier]
    latency_penalty = LATENCY_RANK[model.latency_class]
    cost = model.cost_per_unit or 0.0
    return (quality_rank * policy.quality_weight
            + model.reliability_score * policy.reliability_weight
            - latency_penalty * policy.latency_weight
            - cost * policy.cost_weight)


def _sorted_candidates(models: list, policy: RoutingPolicy) -> list:
    return sorted(models, key=lambda m: (-_score(m, policy), m.provider_id, m.model_id))


def _provider_available(model: ModelRecord) -> bool:
    provider = get_provider(model.provider_id)
    return provider is not None and provider.enabled and provider.effective_status in EXECUTABLE_PROVIDER_STATUSES


def _filter_candidates(request: ModelRequest):
    """Staged, ordered filtering - stops at the first stage that empties
    the pool, returning a specific reason code rather than a generic one.
    Returns (candidates, reason_code_if_empty)."""
    pool = [m for m in list_models(enabled_only=True) if request.required_capability in m.capabilities]
    if not pool:
        return [], "NO_CAPABILITY_MATCH"

    if request.privacy_scope:
        pool = [m for m in pool if request.privacy_scope in m.privacy_scopes]
        if not pool:
            return [], "PRIVACY_MISMATCH"

    pool = [m for m in pool if _provider_available(m)]
    if not pool:
        return [], "NO_AVAILABLE_PROVIDER"

    if request.min_context_capacity is not None:
        pool = [m for m in pool if m.context_capacity >= request.min_context_capacity]
        if not pool:
            return [], "NO_CONTEXT_MATCH"

    if request.required_modality:
        pool = [m for m in pool if request.required_modality in m.modality]
        if not pool:
            return [], "NO_MODALITY_MATCH"

    if request.quality_requirement:
        min_rank = QUALITY_RANK.get(request.quality_requirement, len(QUALITY_TIERS))
        pool = [m for m in pool if QUALITY_RANK[m.quality_tier] >= min_rank]
        if not pool:
            return [], "NO_QUALITY_MATCH"

    if request.latency_requirement:
        max_rank = LATENCY_RANK.get(request.latency_requirement, -1)
        pool = [m for m in pool if LATENCY_RANK[m.latency_class] <= max_rank]
        if not pool:
            return [], "NO_LATENCY_MATCH"

    if request.max_cost is not None:
        pool = [m for m in pool if m.cost_per_unit is not None and m.cost_per_unit <= request.max_cost]
        if not pool:
            return [], "COST_CONSTRAINT_UNMET"

    return pool, None


def _no_match_decision(decision_id, request, reason_code) -> RoutingDecision:
    d = RoutingDecision(
        decision_id=decision_id, outcome="NO_COMPATIBLE_MODEL", selected_provider_id=None, selected_model_id=None,
        reason_codes=[reason_code], policy_version=DEFAULT_ROUTING_POLICY.policy_version,
        capability_match=(reason_code != "NO_CAPABILITY_MATCH"), privacy_match=(reason_code != "PRIVACY_MISMATCH"),
        availability_status=None, fallback_candidates=[], required_capability=request.required_capability,
        task_type=request.task_type, user_id=request.user_id, created_at=_now(),
    )
    _persist_decision(d)
    return d


def _persist_decision(d: RoutingDecision):
    with _connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO jarvis_routing_decisions
                (decision_id, outcome, selected_provider_id, selected_model_id, reason_codes, policy_version,
                 capability_match, privacy_match, availability_status, fallback_candidates, required_capability,
                 task_type, user_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (d.decision_id, d.outcome, d.selected_provider_id, d.selected_model_id, json.dumps(d.reason_codes),
              d.policy_version, int(d.capability_match), int(d.privacy_match), d.availability_status,
              json.dumps(d.fallback_candidates), d.required_capability, d.task_type, d.user_id, d.created_at))


def get_decision(decision_id: str) -> RoutingDecision:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jarvis_routing_decisions WHERE decision_id = ?", (decision_id,)).fetchone()
    if row is None:
        return None
    d = dict(row)
    d["reason_codes"] = json.loads(d["reason_codes"])
    d["fallback_candidates"] = json.loads(d["fallback_candidates"])
    d["capability_match"] = bool(d["capability_match"])
    d["privacy_match"] = bool(d["privacy_match"])
    return RoutingDecision(**d)


def route(request: ModelRequest, *, policy: RoutingPolicy = None, decision_id: str = None) -> RoutingDecision:
    """The one entry point. Never raises for a legitimate "nothing
    qualifies" outcome (returned as NO_COMPATIBLE_MODEL, like Action
    Firewall returns DENY as data) - only raises for a validation error or
    the unconditional transaction hard-stop. Never calls a ModelProvider's
    check_status()/invoke() - availability is read from what
    report_provider_status() already recorded, never probed live from
    here."""
    policy = policy or DEFAULT_ROUTING_POLICY
    decision_id = decision_id or str(uuid4())

    cached = get_decision(decision_id)
    if cached is not None:
        return cached

    if not request.required_capability or not str(request.required_capability).strip():
        raise ModelRouterValidationError("required_capability is required",
                                          [{"type": "MISSING_REQUIRED_CAPABILITY", "field": "required_capability"}])

    matches = _scan_for_prohibited_text(request.task_type, request.required_capability)
    if matches:
        raise ModelRouterTransactionProhibitedError(matches)

    if request.preferred_model_id:
        preferred = get_model(request.preferred_model_id)
        if preferred is None:
            d = RoutingDecision(
                decision_id=decision_id, outcome="NO_COMPATIBLE_MODEL", selected_provider_id=None,
                selected_model_id=None, reason_codes=["INVALID_PREFERENCE"], policy_version=policy.policy_version,
                capability_match=False, privacy_match=False, availability_status=None, fallback_candidates=[],
                required_capability=request.required_capability, task_type=request.task_type,
                user_id=request.user_id, created_at=_now(),
            )
            _persist_decision(d)
            return d

    pool, empty_reason = _filter_candidates(request)

    if request.preferred_model_id:
        preferred = get_model(request.preferred_model_id)
        preferred_qualifies = preferred is not None and any(m.model_id == preferred.model_id for m in pool)
        if preferred_qualifies:
            ranked = _sorted_candidates([m for m in pool if m.model_id != preferred.model_id], policy)
            provider = get_provider(preferred.provider_id)
            d = RoutingDecision(
                decision_id=decision_id, outcome="ROUTED", selected_provider_id=preferred.provider_id,
                selected_model_id=preferred.model_id, reason_codes=["PREFERRED_MODEL_SELECTED"],
                policy_version=policy.policy_version, capability_match=True, privacy_match=True,
                availability_status=provider.effective_status if provider else None,
                fallback_candidates=[{"provider_id": m.provider_id, "model_id": m.model_id} for m in ranked],
                required_capability=request.required_capability, task_type=request.task_type,
                user_id=request.user_id, created_at=_now(),
            )
            _persist_decision(d)
            return d
        if not request.fallback_allowed:
            d = RoutingDecision(
                decision_id=decision_id, outcome="NO_COMPATIBLE_MODEL", selected_provider_id=None,
                selected_model_id=None, reason_codes=["PREFERRED_MODEL_UNAVAILABLE"],
                policy_version=policy.policy_version, capability_match=False, privacy_match=False,
                availability_status=None, fallback_candidates=[], required_capability=request.required_capability,
                task_type=request.task_type, user_id=request.user_id, created_at=_now(),
            )
            _persist_decision(d)
            return d
        # fallback_allowed=True and preference didn't qualify - fall
        # through to normal ranked selection over whatever DOES qualify.

    if not pool:
        return _no_match_decision(decision_id, request, empty_reason or "NO_CAPABILITY_MATCH")

    ranked = _sorted_candidates(pool, policy)
    selected = ranked[0]
    fallback = ranked[1:]
    provider = get_provider(selected.provider_id)
    reason_codes = ["ROUTED_BY_POLICY"]
    if request.preferred_model_id:
        reason_codes = ["PREFERRED_MODEL_UNAVAILABLE", "ROUTED_BY_POLICY"]

    d = RoutingDecision(
        decision_id=decision_id, outcome="ROUTED", selected_provider_id=selected.provider_id,
        selected_model_id=selected.model_id, reason_codes=reason_codes, policy_version=policy.policy_version,
        capability_match=True, privacy_match=(not request.privacy_scope or request.privacy_scope in selected.privacy_scopes),
        availability_status=provider.effective_status if provider else None,
        fallback_candidates=[{"provider_id": m.provider_id, "model_id": m.model_id} for m in fallback],
        required_capability=request.required_capability, task_type=request.task_type,
        user_id=request.user_id, created_at=_now(),
    )
    _persist_decision(d)
    return d
