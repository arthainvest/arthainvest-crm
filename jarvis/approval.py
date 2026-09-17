#!/usr/bin/env python3
"""
JARVIS Approval Gate — Stage I.

    INTENT LOCK
       |
    PLAN / MISSION STEP
       |
    ACTION CLASSIFICATION
       |
    PERMISSION CHECKS
       |
    APPROVAL GATE   <- this file
       |
    ACTION FIREWALL (Stage J, not built)
       |
    WORKER RUNTIME
       |
    VERIFICATION

This file answers exactly one question: "does this specific action have
the required explicit approval before execution is allowed?" It is
deliberately NOT a second authorization engine - permission/privacy/
security checks already exist upstream (RBAC in the CRM backend, the
five-tier privacy model in memory.py), and a full Action Firewall is
Stage J, not this one. `APPROVED != AUTHORIZED != ALLOWED != SAFE` -
approval is one condition among several, never a substitute for policy.

## Risk tiers - reused, not reinvented

R0-R4 already exist as a real, used vocabulary in plans.py
(`RISK_LEVELS`/`CONSEQUENTIAL_RISK_LEVELS`) and in capabilities.py (every
Capability carries a `risk_level`). This file imports plans.RISK_LEVELS
directly rather than defining a second taxonomy.

## Action classes - reused from the master spec, implemented here for
## the first time

JARVIS_AGENT_RUNTIME_SPEC.md Section 25A.2 already names the canonical
action-class vocabulary (READ, COMMUNICATE, DELETE, etc.) - no stage
before this one has needed to represent it as code. This file is the
first to do so, reusing that exact vocabulary rather than inventing a
new one. A caller requesting approval must pass an explicit
`action_class` - this file does not attempt to auto-classify an action,
since that is what a future Tool Registry (Stage K) or Action Firewall
(Stage J) would own, not this narrow layer.

## Default approval matrix (Section 6 of the authorization)

    R0 -> NOT_REQUIRED   (read/search/analyze/generate)
    R1 -> NOT_REQUIRED   (draft/low-risk internal work)
    R2 -> REQUIRED       (external side effects)
    R3 -> REQUIRED + a non-empty reason
    R4 -> DENIED, unconditionally - there is no approval path for R4 at
          all, and TRANSACTION_PROHIBITED is checked even before that,
          reusing backend/policy.py directly (see _scan_for_prohibited_text)
          - never a second transaction-pattern vocabulary.

## Why there is no real R2/R3 worker in this codebase to gate yet

Every capability registered so far (jarvis-context-assembly,
jarvis-memory-write, jarvis-mission-tracking) is R0 in capabilities.py -
matching Stage D/H's own honest framing that jarvis/ is still entirely
internal. This means the enforcement hook added to workers.py in this
stage (see that file's execute_step()) has nothing real to gate today -
proven instead with a test-only R2 worker fixture, the same technique
Stage H used to prove intent-drift detection via direct database
tampering: build the real mechanism, prove it fires correctly, be
honest that no production capability exercises it yet.

## Intent Lock integration (Section 18)

The current locked intent's fingerprint (Stage H's `IntentRecord.fingerprint`,
if one exists) is folded into this file's own action fingerprint - so a
legitimate replan (which re-locks to a new fingerprint) naturally
invalidates any prior approval's fingerprint match, without a separate
"is this stale" check. `evaluate()` additionally re-verifies the intent
live via `intent_lock.verify_intent()` at evaluation time, not only at
request time - if verify_intent() ever reports DRIFT_DETECTED, approval
is invalid regardless of what its own stored state says.

## Recovery integration (Section 19)

Recovery Engine (recovery.py) never executes anything itself - it only
ever re-arms a step to READY via missions.reopen_failed_step_for_recovery().
The actual execution attempt still goes through workers.execute_step(),
which is where this file's enforcement hook lives - so Recovery cannot
bypass approval by construction: there is only one execution path, and
it is gated regardless of how the step became READY again (a normal
Planner materialization, or a Recovery retry/fallback).
"""

import hashlib
import json
import sqlite3
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import missions as msn  # noqa: E402
import plans as pl  # noqa: E402
import intent_lock as il  # noqa: E402
from policy import find_prohibited_routes  # noqa: E402 - same single source of truth every other layer uses

DB_PATH = Path(__file__).resolve().parent / "jarvis.db"

# Reused, not reinvented - see plans.RISK_LEVELS.
RISK_LEVELS = pl.RISK_LEVELS
NO_APPROVAL_RISK_LEVELS = {"R0", "R1"}
APPROVAL_REQUIRED_RISK_LEVELS = {"R2", "R3"}
REASON_REQUIRED_RISK_LEVELS = {"R3"}
DENIED_RISK_LEVELS = {"R4"}

# JARVIS_AGENT_RUNTIME_SPEC.md Section 25A.2's own vocabulary, reused verbatim.
ACTION_CLASSES = {
    "READ", "SEARCH", "ANALYZE", "GENERATE", "DRAFT", "COMMUNICATE", "CREATE",
    "MODIFY", "DELETE", "PUBLISH", "SCHEDULE", "AUTOMATE", "EXTERNAL_SIDE_EFFECT",
    "FINANCIAL_TRANSACTION", "SECURITY_SENSITIVE", "ADMINISTRATIVE",
}

APPROVAL_STATUSES = {"NOT_REQUIRED", "REQUIRED", "REQUESTED", "APPROVED", "REJECTED", "EXPIRED", "CANCELLED"}
_TERMINAL_APPROVAL_STATUSES = {"APPROVED", "REJECTED", "EXPIRED", "CANCELLED"}

DECISIONS = {"ALLOWED", "APPROVAL_REQUIRED", "DENIED", "EXPIRED", "INVALID", "CANCELLED"}

DEFAULT_TTL_SECONDS = 24 * 60 * 60  # 24h - never silently renewed, never silently extended


def _now():
    return datetime.now(timezone.utc)


def _now_iso():
    return _now().isoformat()


# ---------------------------------------------------------------------------
# Errors (same canonical shape as the rest of the jarvis/ stages, extended
# with the approval-specific codes Section 28 names)
# ---------------------------------------------------------------------------

@dataclass
class ErrorObject:
    code: str
    category: str
    severity: str = "ERROR"
    retryable: bool = False
    user_action_required: bool = False
    message: str = ""
    mission_id: str = None
    step_id: str = None
    metadata: dict = field(default_factory=dict)
    error_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self):
        return asdict(self)


class ApprovalError(Exception):
    def __init__(self, error: ErrorObject):
        self.error = error
        super().__init__(error.message)


class ApprovalValidationError(ApprovalError):
    def __init__(self, message, mission_id=None, step_id=None):
        super().__init__(ErrorObject(code="INVALID_INPUT", category="VALIDATION",
                                      mission_id=mission_id, step_id=step_id, message=message))


class ApprovalNotFoundError(ApprovalError):
    def __init__(self, approval_id):
        super().__init__(ErrorObject(code="APPROVAL_INVALID", category="STATE",
                                      message=f"No approval request {approval_id!r}."))


class TransactionProhibitedError(ApprovalError):
    """This is checked BEFORE anything else in evaluate()/request_approval() -
    a transaction-shaped action must never reach REQUESTED, let alone
    APPROVED. No approval, of any kind, changes this outcome."""

    def __init__(self, mission_id, step_id, matches):
        super().__init__(ErrorObject(
            code="TRANSACTION_PROHIBITED", category="POLICY", severity="CRITICAL",
            retryable=False, mission_id=mission_id, step_id=step_id,
            message="This action is financial-transaction-shaped and can never be approved.",
            metadata={"matches": matches},
        ))


class ApprovalStateConflictError(ApprovalError):
    def __init__(self, approval_id):
        super().__init__(ErrorObject(code="STATE_CONFLICT", category="CONCURRENCY", retryable=True,
                                      message=f"Approval {approval_id!r} was modified concurrently; re-read and retry."))


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@dataclass
class ApprovalRequest:
    approval_id: str
    user_id: str
    mission_id: str
    step_id: str
    action_class: str
    risk_level: str
    action_fingerprint: str
    summary: str
    reason_required: bool
    status: str
    version: int
    created_at: str
    expires_at: str
    intent_lock_id: str = None
    tool_id: str = None
    reason: str = None
    approved_by: str = None
    approved_at: str = None
    rejected_at: str = None
    cancelled_at: str = None
    last_idempotency_key: str = None

    def to_dict(self):
        return asdict(self)


@dataclass
class ApprovalDecision:
    decision_id: str
    approval_id: str
    user_id: str
    mission_id: str
    step_id: str
    action_class: str
    risk_level: str
    approval_state: str
    decision: str
    action_fingerprint: str
    intent_lock_version: str
    reason_codes: list
    created_at: str
    expires_at: str = None

    def to_dict(self):
        return asdict(self)


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
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
    msn.DB_PATH = DB_PATH if msn.DB_PATH != DB_PATH else msn.DB_PATH
    msn.init_db()
    il.DB_PATH = DB_PATH if il.DB_PATH != DB_PATH else il.DB_PATH
    il.init_db()  # approval.py calls into intent_lock.py at runtime - its table must exist too
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_approval_requests (
                approval_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                mission_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                action_class TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                action_fingerprint TEXT NOT NULL,
                intent_lock_id TEXT,
                tool_id TEXT,
                summary TEXT,
                reason_required INTEGER NOT NULL DEFAULT 0,
                reason TEXT,
                status TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                approved_by TEXT,
                approved_at TEXT,
                rejected_at TEXT,
                cancelled_at TEXT,
                last_idempotency_key TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_approval_step ON jarvis_approval_requests(step_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_approval_fingerprint ON jarvis_approval_requests(action_fingerprint)")


def _row_to_request(row) -> ApprovalRequest:
    d = dict(row)
    d["reason_required"] = bool(d["reason_required"])
    return ApprovalRequest(**d)


# ---------------------------------------------------------------------------
# Action fingerprint (Section 9) - deterministic, no timestamps/randomness
# ---------------------------------------------------------------------------

def compute_action_fingerprint(*, user_id, mission_id, step_id, action_class, risk_level,
                                tool_id=None, target=None, material_params=None,
                                intent_lock_fingerprint=None) -> str:
    """Represents the material execution identity. If ANY of these change -
    including the locked intent's own fingerprint changing via a
    legitimate replan - the resulting fingerprint changes, and a previously
    APPROVED request for the old fingerprint no longer matches (Section 14:
    'if the material action fingerprint changes: REQUIRES_APPROVAL again')."""
    payload = {
        "user_id": user_id, "mission_id": mission_id, "step_id": step_id,
        "action_class": action_class, "risk_level": risk_level, "tool_id": tool_id,
        "target": target, "material_params": material_params or {},
        "intent_lock_fingerprint": intent_lock_fingerprint,
    }
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _scan_for_prohibited_text(*texts) -> list:
    combined = " | ".join(t for t in texts if t)
    if not combined:
        return []
    return [pattern for _, pattern in find_prohibited_routes([combined])]


def _current_locked_intent_fingerprint(mission_id, user_id):
    """Best-effort: not every mission has called lock_intent() yet (Stage H
    is not auto-wired into anything). Returns (intent_id, fingerprint, drifted)."""
    locked = il.get_locked_intent(mission_id, user_id)
    if locked is None:
        return None, None, False
    result = il.verify_intent(mission_id, user_id)
    drifted = result["status"] == "DRIFT_DETECTED"
    return locked.intent_id, locked.fingerprint, drifted


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------

def evaluate(mission_id, step_id, user_id, action_class, risk_level=None, *,
             tool_id=None, target=None, material_params=None) -> ApprovalDecision:
    """The read-only question this whole file exists to answer: given this
    exact action, is execution currently allowed? Never mutates anything -
    request_approval()/approve()/reject()/cancel_approval() do that."""
    if action_class not in ACTION_CLASSES:
        raise ApprovalValidationError(f"unknown action_class {action_class!r}", mission_id=mission_id, step_id=step_id)

    mission = msn.get_mission(mission_id, user_id)  # user isolation + existence
    step = msn.get_step(step_id, mission_id, user_id)
    # tool_id defaults to the step's own capability - "no tool_id given"
    # means "use whatever this step actually is", not "no tool identity at
    # all". This must resolve identically here and in request_approval()
    # (and in any caller, e.g. action_firewall.py, that fills it in from
    # the same step) or two callers computing "the same" fingerprint from
    # different resolved values would silently never match.
    tool_id = tool_id or step.get("worker_id")

    reason_codes = []

    # Cancellation wins over everything else, including an already-APPROVED
    # request - re-checked live against current state, not only against
    # the approval record's own (possibly stale) status.
    if mission["status"] == "CANCELLED" or step["status"] == "CANCELLED":
        return _decision(mission_id, step_id, user_id, action_class, risk_level or "R1",
                          "CANCELLED", "CANCELLED", None, None, ["MISSION_OR_STEP_CANCELLED"])

    # TRANSACTION_PROHIBITED is checked before anything else, including
    # before the risk lookup - it hard-stops regardless of risk_level.
    matches = _scan_for_prohibited_text(step.get("description"), step.get("worker_id"),
                                         json.dumps(step.get("inputs")) if step.get("inputs") else None,
                                         json.dumps(material_params) if material_params else None,
                                         action_class if action_class == "FINANCIAL_TRANSACTION" else None)
    if matches or action_class == "FINANCIAL_TRANSACTION":
        raise TransactionProhibitedError(mission_id, step_id, matches or ["FINANCIAL_TRANSACTION action_class"])

    risk_level = risk_level or "R1"
    if risk_level not in RISK_LEVELS:
        raise ApprovalValidationError(f"unknown risk_level {risk_level!r}", mission_id=mission_id, step_id=step_id)

    if risk_level in DENIED_RISK_LEVELS:
        return _decision(mission_id, step_id, user_id, action_class, risk_level,
                          "REQUIRED", "DENIED", None, None, ["RISK_R4_NEVER_APPROVABLE"])

    intent_id, intent_fp, drifted = _current_locked_intent_fingerprint(mission_id, user_id)
    if drifted:
        return _decision(mission_id, step_id, user_id, action_class, risk_level,
                          "REQUIRED", "INVALID", None, intent_id, ["INTENT_DRIFT_DETECTED"])

    if risk_level in NO_APPROVAL_RISK_LEVELS:
        return _decision(mission_id, step_id, user_id, action_class, risk_level,
                          "NOT_REQUIRED", "ALLOWED", None, intent_id, [])

    # R2/R3 from here on - a matching, valid approval must exist.
    fingerprint = compute_action_fingerprint(
        user_id=user_id, mission_id=mission_id, step_id=step_id, action_class=action_class,
        risk_level=risk_level, tool_id=tool_id, target=target, material_params=material_params,
        intent_lock_fingerprint=intent_fp,
    )
    existing = _find_active_request(step_id, fingerprint)
    if existing is None:
        return _decision(mission_id, step_id, user_id, action_class, risk_level,
                          "REQUIRED", "APPROVAL_REQUIRED", fingerprint, intent_id, ["NO_MATCHING_APPROVAL"])

    if existing.status == "APPROVED":
        if _now_iso() > existing.expires_at:
            return _decision(mission_id, step_id, user_id, action_class, risk_level,
                              "EXPIRED", "EXPIRED", fingerprint, intent_id, ["APPROVAL_EXPIRED"], approval_id=existing.approval_id)
        if existing.reason_required and not (existing.reason and existing.reason.strip()):
            return _decision(mission_id, step_id, user_id, action_class, risk_level,
                              "APPROVED", "INVALID", fingerprint, intent_id, ["APPROVAL_MISSING_REQUIRED_REASON"], approval_id=existing.approval_id)
        return _decision(mission_id, step_id, user_id, action_class, risk_level,
                          "APPROVED", "ALLOWED", fingerprint, intent_id, [], approval_id=existing.approval_id)

    if existing.status == "REJECTED":
        return _decision(mission_id, step_id, user_id, action_class, risk_level,
                          "REJECTED", "DENIED", fingerprint, intent_id, ["APPROVAL_REJECTED"], approval_id=existing.approval_id)

    if existing.status == "EXPIRED":
        return _decision(mission_id, step_id, user_id, action_class, risk_level,
                          "EXPIRED", "EXPIRED", fingerprint, intent_id, ["APPROVAL_EXPIRED"], approval_id=existing.approval_id)

    if existing.status == "CANCELLED":
        return _decision(mission_id, step_id, user_id, action_class, risk_level,
                          "CANCELLED", "CANCELLED", fingerprint, intent_id, ["APPROVAL_CANCELLED"], approval_id=existing.approval_id)

    # REQUESTED, still pending.
    return _decision(mission_id, step_id, user_id, action_class, risk_level,
                      "REQUESTED", "APPROVAL_REQUIRED", fingerprint, intent_id, ["APPROVAL_PENDING"], approval_id=existing.approval_id)


def _decision(mission_id, step_id, user_id, action_class, risk_level, approval_state, decision,
              fingerprint, intent_lock_id, reason_codes, approval_id=None) -> ApprovalDecision:
    return ApprovalDecision(
        decision_id=str(uuid4()), approval_id=approval_id, user_id=user_id, mission_id=mission_id,
        step_id=step_id, action_class=action_class, risk_level=risk_level, approval_state=approval_state,
        decision=decision, action_fingerprint=fingerprint, intent_lock_version=intent_lock_id,
        reason_codes=reason_codes, created_at=_now_iso(),
    )


def _find_active_request(step_id, fingerprint):
    """Most recent non-superseded request for this exact fingerprint on
    this step - REQUESTED/APPROVED are 'active', but a terminal REJECTED/
    EXPIRED/CANCELLED for the SAME fingerprint is still returned (so
    evaluate() can report the specific reason) rather than treated as if
    it never existed."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM jarvis_approval_requests WHERE step_id = ? AND action_fingerprint = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (step_id, fingerprint),
        ).fetchone()
    return _row_to_request(row) if row else None


# ---------------------------------------------------------------------------
# Request / approve / reject / cancel
# ---------------------------------------------------------------------------

def request_approval(mission_id, step_id, user_id, action_class, risk_level, *,
                      tool_id=None, target=None, material_params=None, summary="",
                      ttl_seconds=DEFAULT_TTL_SECONDS, idempotency_key=None) -> ApprovalRequest:
    """Creates a durable REQUESTED record. Idempotent by fingerprint: a
    second call with an identical fingerprint while an active (REQUESTED
    or APPROVED, unexpired) request already exists returns that request
    rather than creating a duplicate (Section 25: 'should not create
    uncontrolled duplicate approval requests')."""
    if action_class not in ACTION_CLASSES:
        raise ApprovalValidationError(f"unknown action_class {action_class!r}", mission_id=mission_id, step_id=step_id)
    if risk_level not in RISK_LEVELS:
        raise ApprovalValidationError(f"unknown risk_level {risk_level!r}", mission_id=mission_id, step_id=step_id)
    if risk_level in DENIED_RISK_LEVELS:
        raise ApprovalValidationError("R4 actions can never be approved - there is no request path for them",
                                       mission_id=mission_id, step_id=step_id)

    mission = msn.get_mission(mission_id, user_id)
    step = msn.get_step(step_id, mission_id, user_id)
    tool_id = tool_id or step.get("worker_id")  # same resolution as evaluate() - must match identically
    if mission["status"] == "CANCELLED" or step["status"] == "CANCELLED":
        raise ApprovalValidationError("cannot request approval for a cancelled mission/step",
                                       mission_id=mission_id, step_id=step_id)

    matches = _scan_for_prohibited_text(step.get("description"), step.get("worker_id"),
                                         json.dumps(step.get("inputs")) if step.get("inputs") else None,
                                         json.dumps(material_params) if material_params else None)
    if matches or action_class == "FINANCIAL_TRANSACTION":
        raise TransactionProhibitedError(mission_id, step_id, matches or ["FINANCIAL_TRANSACTION action_class"])

    intent_id, intent_fp, _drifted = _current_locked_intent_fingerprint(mission_id, user_id)
    fingerprint = compute_action_fingerprint(
        user_id=user_id, mission_id=mission_id, step_id=step_id, action_class=action_class,
        risk_level=risk_level, tool_id=tool_id, target=target, material_params=material_params,
        intent_lock_fingerprint=intent_fp,
    )

    if idempotency_key:
        with _connect() as conn:
            row = conn.execute(
                "SELECT * FROM jarvis_approval_requests WHERE step_id = ? AND last_idempotency_key = ?",
                (step_id, idempotency_key),
            ).fetchone()
        if row:
            return _row_to_request(row)

    existing = _find_active_request(step_id, fingerprint)
    if existing is not None and existing.status in ("REQUESTED", "APPROVED") and _now_iso() <= existing.expires_at:
        return existing

    now = _now()
    record = ApprovalRequest(
        approval_id=str(uuid4()), user_id=user_id, mission_id=mission_id, step_id=step_id,
        action_class=action_class, risk_level=risk_level, action_fingerprint=fingerprint,
        intent_lock_id=intent_id, tool_id=tool_id, summary=summary,
        reason_required=risk_level in REASON_REQUIRED_RISK_LEVELS, status="REQUESTED", version=1,
        created_at=now.isoformat(), expires_at=(now + timedelta(seconds=ttl_seconds)).isoformat(),
        last_idempotency_key=idempotency_key,
    )
    with _connect() as conn:
        conn.execute("""
            INSERT INTO jarvis_approval_requests
                (approval_id, user_id, mission_id, step_id, action_class, risk_level, action_fingerprint,
                 intent_lock_id, tool_id, summary, reason_required, reason, status, version,
                 created_at, expires_at, last_idempotency_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (record.approval_id, record.user_id, record.mission_id, record.step_id, record.action_class,
              record.risk_level, record.action_fingerprint, record.intent_lock_id, record.tool_id,
              record.summary, int(record.reason_required), record.reason, record.status, record.version,
              record.created_at, record.expires_at, record.last_idempotency_key))
    return record


def get_approval(approval_id, user_id) -> ApprovalRequest:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jarvis_approval_requests WHERE approval_id = ? AND user_id = ?",
                            (approval_id, user_id)).fetchone()
    if row is None:
        raise ApprovalNotFoundError(approval_id)
    return _row_to_request(row)


def list_approvals_for_step(step_id, user_id) -> list:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM jarvis_approval_requests WHERE step_id = ? AND user_id = ? ORDER BY created_at ASC",
            (step_id, user_id),
        ).fetchall()
    return [_row_to_request(r) for r in rows]


def _transition(approval_id, user_id, *, from_statuses, to_status, reason=None, actor_field=None):
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jarvis_approval_requests WHERE approval_id = ? AND user_id = ?",
                            (approval_id, user_id)).fetchone()
        if row is None:
            raise ApprovalNotFoundError(approval_id)
        current = _row_to_request(row)

        if current.status == to_status:
            return current  # idempotent no-op for repeated identical submissions

        if current.status not in from_statuses:
            raise ApprovalValidationError(
                f"approval {approval_id!r} is {current.status!r}, cannot transition to {to_status!r}",
                mission_id=current.mission_id, step_id=current.step_id,
            )

        if to_status == "APPROVED" and current.reason_required and not (reason and reason.strip()):
            raise ApprovalValidationError("R3 approval requires a non-empty reason",
                                           mission_id=current.mission_id, step_id=current.step_id)

        now = _now_iso()
        timestamp_field = {"APPROVED": "approved_at", "REJECTED": "rejected_at", "CANCELLED": "cancelled_at"}.get(to_status)
        sets = ["status = ?", "version = version + 1"]
        params = [to_status]
        if timestamp_field:
            sets.append(f"{timestamp_field} = ?")
            params.append(now)
        if reason is not None:
            sets.append("reason = ?")
            params.append(reason)
        if actor_field:
            sets.append(f"{actor_field} = ?")
            params.append(user_id)

        cur = conn.execute(
            f"UPDATE jarvis_approval_requests SET {', '.join(sets)} "
            "WHERE approval_id = ? AND user_id = ? AND version = ?",
            (*params, approval_id, user_id, current.version),
        )
        if cur.rowcount == 0:
            raise ApprovalStateConflictError(approval_id)

        updated = conn.execute("SELECT * FROM jarvis_approval_requests WHERE approval_id = ?", (approval_id,)).fetchone()
    return _row_to_request(updated)


def approve(approval_id, user_id, reason=None) -> ApprovalRequest:
    """Approval is explicit and self-service in this single-operator
    architecture: only the same user_id who owns the request may approve
    it (enforced the same way every other stage enforces user isolation -
    the row simply isn't found for a different user_id)."""
    return _transition(approval_id, user_id, from_statuses={"REQUESTED"}, to_status="APPROVED",
                        reason=reason, actor_field="approved_by")


def reject(approval_id, user_id, reason=None) -> ApprovalRequest:
    return _transition(approval_id, user_id, from_statuses={"REQUESTED"}, to_status="REJECTED", reason=reason)


def cancel_approval(approval_id, user_id, reason=None) -> ApprovalRequest:
    """Idempotent: cancelling an already-cancelled approval is a no-op
    (handled by _transition's own status == to_status short-circuit)."""
    return _transition(approval_id, user_id, from_statuses={"REQUESTED", "APPROVED"}, to_status="CANCELLED", reason=reason)


def cancel_approvals_for_step(mission_id, step_id, user_id, reason="step or mission cancelled") -> list:
    """Convenience for a caller (e.g. a future Supervisor cancellation
    path) that wants to proactively cancel every pending/approved request
    for a step. Not required for correctness - evaluate() already
    re-checks live mission/step status on every call, so a cancelled
    step's approval can never authorize execution even if this is never
    called - but calling it keeps the approval ledger itself tidy."""
    cancelled = []
    for req in list_approvals_for_step(step_id, user_id):
        if req.status in ("REQUESTED", "APPROVED"):
            cancelled.append(cancel_approval(req.approval_id, user_id, reason=reason))
    return cancelled
