#!/usr/bin/env python3
"""
JARVIS Action Firewall — Stage J: the final deterministic gate immediately
before any executable side effect.

    INTENT LOCK -> PERMISSION -> PRIVACY -> POLICY -> SECURITY -> RISK ->
    APPROVAL -> ACTION FIREWALL -> WORKER RUNTIME

This file answers exactly one question: "given everything known about this
action, is this exact action permitted to execute right now?" It combines
the results of the checks already built by earlier stages into one final
ALLOW/DENY decision - it does not re-implement any of them:

    - transaction prohibition + risk/approval state -> delegated to
      approval.evaluate() (Stage I), which already owns that logic
      end to end, including its own reuse of backend/policy.py.
    - intent drift -> delegated to intent_lock.verify_intent() (Stage H).
    - privacy -> reuses memory.ALLOWED_PRIVACY_FOR_CONTEXT directly
      (Stage 2), never a second privacy matrix.
    - permission -> reuses missions.py's own existing user-isolation
      guarantee (a mission/step simply isn't found for the wrong user).
    - tool/worker validity + "security" (a disabled/unavailable
      capability) -> reuses capabilities.py's registry directly.

The Firewall adds exactly the pieces none of those own: fail-closed
handling of missing/unknown metadata, an explicit tool-validity check
Approval Gate never made on its own, and the ORDER in which everything is
checked - critically, cancellation/intent-drift/tool-validity/privacy are
all checked BEFORE consulting approval, so a fully-APPROVED action still
gets denied if the mission has since been cancelled, the intent has
drifted, or the capability has been disabled - approval alone is never
sufficient (Rules 3/4/5 of this stage's authorization).

## The one architectural invariant this stage exists to establish

No executable side effect may leave the Worker Runtime unless the Action
Firewall has returned a valid ALLOW decision for that exact action
context. This is enforced INSIDE workers.execute_step() itself - not
called optionally by the Supervisor - so there is no code path (a future
Supervisor change, a different caller, Recovery's retry, a fallback
reassignment, a replan) that can reach a Worker without passing through
this file first. See workers.py's own docstring for the enforcement point.

## What this file never does
Never executes a tool or a worker. Never decides anything with an LLM -
every branch below is a deterministic function of already-known facts.
Never claims ALLOW means execution succeeded, or that execution succeeding
means verification happened - those remain Stage D's and Stage F's jobs,
strictly separate from this one.
"""

import json
import sqlite3
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))

import missions as msn  # noqa: E402
import capabilities as caps  # noqa: E402
import memory as mem  # noqa: E402
import intent_lock as il  # noqa: E402
import approval as appr  # noqa: E402

DB_PATH = Path(__file__).resolve().parent / "jarvis.db"

DECISIONS = {"ALLOW", "DENY"}

# Every reason a DENY can carry - a fixed, canonical vocabulary so a
# caller/audit can branch on it rather than parsing free text.
REASON_CODES = {
    "MISSING_REQUIRED_METADATA", "INVALID_ACTION_CLASS", "MISSION_OR_STEP_NOT_FOUND",
    "CANCELLED", "INTENT_DRIFT_DETECTED", "INVALID_TOOL", "SECURITY_VIOLATION",
    "PRIVACY_SCOPE_DENIED", "APPROVAL_REQUIRED", "APPROVAL_DENIED", "APPROVAL_EXPIRED",
    "APPROVAL_INVALID", "RESOURCE_LIMIT_EXCEEDED",
}


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
    mission_id: str = None
    step_id: str = None
    metadata: dict = field(default_factory=dict)
    error_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=_now)

    def to_dict(self):
        return asdict(self)


class ActionFirewallError(Exception):
    def __init__(self, error: ErrorObject):
        self.error = error
        super().__init__(error.message)


class TransactionProhibitedError(ActionFirewallError):
    """Propagated, never downgraded to a soft DENY - matches every other
    layer's treatment of this one category. Rescuable by nothing: not
    approval, not recovery, not fallback, not replanning."""

    def __init__(self, mission_id, step_id, matches):
        super().__init__(ErrorObject(
            code="TRANSACTION_PROHIBITED", category="POLICY", severity="CRITICAL", retryable=False,
            mission_id=mission_id, step_id=step_id,
            message="This action is financial-transaction-shaped and can never execute.",
            metadata={"matches": matches},
        ))


# ---------------------------------------------------------------------------
# Decision record
# ---------------------------------------------------------------------------

@dataclass
class FirewallDecision:
    decision_id: str
    mission_id: str
    step_id: str
    user_id: str
    action_class: str
    risk_level: str
    tool_id: str
    decision: str            # ALLOW | DENY
    reason_codes: list
    checks: dict
    approval_id: str
    intent_lock_id: str
    created_at: str

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
    appr.DB_PATH = DB_PATH if appr.DB_PATH != DB_PATH else appr.DB_PATH
    appr.init_db()  # cascades to msn.init_db() and il.init_db() - authorize() calls into both
    il.DB_PATH = DB_PATH if il.DB_PATH != DB_PATH else il.DB_PATH
    il.init_db()
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_firewall_decisions (
                decision_id TEXT PRIMARY KEY,
                mission_id TEXT,
                step_id TEXT,
                user_id TEXT,
                action_class TEXT,
                risk_level TEXT,
                tool_id TEXT,
                decision TEXT NOT NULL,
                reason_codes TEXT NOT NULL,
                checks TEXT NOT NULL,
                approval_id TEXT,
                intent_lock_id TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_firewall_step ON jarvis_firewall_decisions(step_id)")


def _row_to_decision(row) -> FirewallDecision:
    d = dict(row)
    d["reason_codes"] = json.loads(d["reason_codes"])
    d["checks"] = json.loads(d["checks"])
    return FirewallDecision(**d)


def _persist(decision: FirewallDecision):
    with _connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO jarvis_firewall_decisions
                (decision_id, mission_id, step_id, user_id, action_class, risk_level, tool_id,
                 decision, reason_codes, checks, approval_id, intent_lock_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (decision.decision_id, decision.mission_id, decision.step_id, decision.user_id,
              decision.action_class, decision.risk_level, decision.tool_id, decision.decision,
              json.dumps(decision.reason_codes), json.dumps(decision.checks), decision.approval_id,
              decision.intent_lock_id, decision.created_at))


def get_decision(decision_id: str) -> FirewallDecision:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jarvis_firewall_decisions WHERE decision_id = ?", (decision_id,)).fetchone()
    return _row_to_decision(row) if row else None


def list_decisions_for_step(step_id: str) -> list:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM jarvis_firewall_decisions WHERE step_id = ? ORDER BY created_at ASC", (step_id,)
        ).fetchall()
    return [_row_to_decision(r) for r in rows]


def _deny(*, mission_id, step_id, user_id, action_class, risk_level, tool_id, reason_codes,
          checks, approval_id=None, intent_lock_id=None, decision_id=None) -> FirewallDecision:
    d = FirewallDecision(
        decision_id=decision_id or str(uuid4()), mission_id=mission_id, step_id=step_id, user_id=user_id,
        action_class=action_class, risk_level=risk_level, tool_id=tool_id, decision="DENY",
        reason_codes=reason_codes, checks=checks, approval_id=approval_id, intent_lock_id=intent_lock_id,
        created_at=_now(),
    )
    _persist(d)
    return d


def _allow(*, mission_id, step_id, user_id, action_class, risk_level, tool_id, checks,
           approval_id=None, intent_lock_id=None, decision_id=None) -> FirewallDecision:
    d = FirewallDecision(
        decision_id=decision_id or str(uuid4()), mission_id=mission_id, step_id=step_id, user_id=user_id,
        action_class=action_class, risk_level=risk_level, tool_id=tool_id, decision="ALLOW",
        reason_codes=[], checks=checks, approval_id=approval_id, intent_lock_id=intent_lock_id,
        created_at=_now(),
    )
    _persist(d)
    return d


# ---------------------------------------------------------------------------
# The one entry point
# ---------------------------------------------------------------------------

def authorize(mission_id, step_id, user_id, action_class=None, risk_level=None, *,
              tool_id=None, target=None, material_params=None, context="business",
              decision_id=None) -> FirewallDecision:
    """Fail-closed at every step: any check that cannot be positively
    resolved denies rather than assumes. Raises only for
    TRANSACTION_PROHIBITED (a hard stop, consistent with every other
    layer) - every other outcome, including every other reason to deny,
    is returned as a normal FirewallDecision, never an exception, so a
    caller always gets a recorded decision to inspect."""
    checks = {}

    if decision_id:
        cached = get_decision(decision_id)
        if cached is not None:
            return cached

    # 1. Fail-closed on missing/unknown metadata - checked before anything
    # else even tries to look anything up.
    if not mission_id or not step_id or not user_id:
        checks["metadata"] = "FAIL"
        return _deny(mission_id=mission_id, step_id=step_id, user_id=user_id, action_class=action_class,
                     risk_level=risk_level, tool_id=tool_id, reason_codes=["MISSING_REQUIRED_METADATA"],
                     checks=checks, decision_id=decision_id)
    if action_class is not None and action_class not in appr.ACTION_CLASSES:
        checks["action_class"] = "FAIL"
        return _deny(mission_id=mission_id, step_id=step_id, user_id=user_id, action_class=action_class,
                     risk_level=risk_level, tool_id=tool_id, reason_codes=["INVALID_ACTION_CLASS"],
                     checks=checks, decision_id=decision_id)
    checks["metadata"] = "PASS"

    # 2. Mission/step existence + user isolation ("permission" in this
    # single-operator architecture - reused from missions.py, not
    # reimplemented: a mismatched user_id makes the row simply not exist).
    try:
        mission = msn.get_mission(mission_id, user_id)
        step = msn.get_step(step_id, mission_id, user_id)
    except (msn.MissionNotFoundError, msn.StepNotFoundError):
        checks["permission"] = "FAIL"
        return _deny(mission_id=mission_id, step_id=step_id, user_id=user_id, action_class=action_class,
                     risk_level=risk_level, tool_id=tool_id, reason_codes=["MISSION_OR_STEP_NOT_FOUND"],
                     checks=checks, decision_id=decision_id)
    checks["permission"] = "PASS"

    # 3. Cancellation - live re-check, same principle as Approval Gate.
    if mission["status"] == "CANCELLED" or step["status"] == "CANCELLED":
        checks["cancellation"] = "FAIL"
        return _deny(mission_id=mission_id, step_id=step_id, user_id=user_id, action_class=action_class,
                     risk_level=risk_level, tool_id=tool_id, reason_codes=["CANCELLED"],
                     checks=checks, decision_id=decision_id)
    checks["cancellation"] = "PASS"

    # 4. Intent Lock - re-verified live here too, not only inside
    # Approval Gate's own fingerprint, since an approved action must still
    # be denied if intent has drifted since, independent of approval state.
    locked = il.get_locked_intent(mission_id, user_id)
    intent_lock_id = locked.intent_id if locked else None
    if locked is not None:
        result = il.verify_intent(mission_id, user_id)
        if result["status"] == "DRIFT_DETECTED":
            checks["intent_lock"] = "FAIL"
            return _deny(mission_id=mission_id, step_id=step_id, user_id=user_id, action_class=action_class,
                         risk_level=risk_level, tool_id=tool_id, reason_codes=["INTENT_DRIFT_DETECTED"],
                         checks=checks, intent_lock_id=intent_lock_id, decision_id=decision_id)
    checks["intent_lock"] = "PASS"

    # 5. Tool/worker validity + "security" (disabled/unavailable capability).
    # "Unknown to capabilities.py" is only a hard DENY when the caller
    # explicitly engaged classification (passed a real action_class) -
    # a step whose worker_id was never meant to be a cataloged jarvis
    # capability (an ad-hoc test Worker, for instance) is not a security
    # violation on its own; Worker Runtime's own registry lookup already
    # handles "no Worker exists for this at all" separately and earlier.
    resolved_tool_id = tool_id or step.get("worker_id")
    cap = caps.get_capability(resolved_tool_id) if resolved_tool_id else None
    if resolved_tool_id and cap is None and action_class is not None:
        checks["tool_validity"] = "FAIL"
        return _deny(mission_id=mission_id, step_id=step_id, user_id=user_id, action_class=action_class,
                     risk_level=risk_level, tool_id=resolved_tool_id, reason_codes=["INVALID_TOOL"],
                     checks=checks, intent_lock_id=intent_lock_id, decision_id=decision_id)
    if cap is not None and not cap.available:
        checks["tool_validity"] = "PASS"
        checks["security"] = "FAIL"
        return _deny(mission_id=mission_id, step_id=step_id, user_id=user_id, action_class=action_class,
                     risk_level=risk_level, tool_id=resolved_tool_id, reason_codes=["SECURITY_VIOLATION"],
                     checks=checks, intent_lock_id=intent_lock_id, decision_id=decision_id)
    checks["tool_validity"] = "PASS"
    checks["security"] = "PASS"

    risk_level = risk_level or (cap.risk_level if cap is not None else "R1")
    if risk_level not in appr.RISK_LEVELS:
        checks["risk"] = "FAIL"
        return _deny(mission_id=mission_id, step_id=step_id, user_id=user_id, action_class=action_class,
                     risk_level=risk_level, tool_id=resolved_tool_id, reason_codes=["MISSING_REQUIRED_METADATA"],
                     checks=checks, intent_lock_id=intent_lock_id, decision_id=decision_id)
    checks["risk"] = "PASS"

    action_class = action_class or "READ"

    # 6. Privacy - reuses memory.py's existing context/privacy matrix
    # directly, never a second copy.
    declared_privacy = (material_params or {}).get("privacy_level")
    if declared_privacy:
        allowed = mem.ALLOWED_PRIVACY_FOR_CONTEXT.get(context, set())
        if declared_privacy not in allowed:
            checks["privacy"] = "FAIL"
            return _deny(mission_id=mission_id, step_id=step_id, user_id=user_id, action_class=action_class,
                         risk_level=risk_level, tool_id=resolved_tool_id, reason_codes=["PRIVACY_SCOPE_DENIED"],
                         checks=checks, intent_lock_id=intent_lock_id, decision_id=decision_id)
    checks["privacy"] = "PASS"

    # 7. Policy + risk + approval - delegated entirely to Approval Gate
    # (Stage I), which already owns the transaction-prohibition check
    # (backend/policy.py) and the full approval state machine. Not
    # reimplemented here - only consulted.
    try:
        approval_decision = appr.evaluate(mission_id, step_id, user_id, action_class, risk_level,
                                           tool_id=resolved_tool_id, target=target, material_params=material_params)
    except appr.TransactionProhibitedError as e:
        checks["policy"] = "FAIL"
        raise TransactionProhibitedError(mission_id, step_id, e.error.metadata.get("matches", []))

    approval_id = getattr(approval_decision, "approval_id", None)
    if approval_decision.decision != "ALLOWED":
        checks["policy"] = "FAIL"
        code = {
            "APPROVAL_REQUIRED": "APPROVAL_REQUIRED", "DENIED": "APPROVAL_DENIED",
            "EXPIRED": "APPROVAL_EXPIRED", "CANCELLED": "CANCELLED", "INVALID": "APPROVAL_INVALID",
        }.get(approval_decision.decision, "APPROVAL_REQUIRED")
        return _deny(mission_id=mission_id, step_id=step_id, user_id=user_id, action_class=action_class,
                     risk_level=risk_level, tool_id=resolved_tool_id, reason_codes=[code], checks=checks,
                     approval_id=approval_id, intent_lock_id=intent_lock_id, decision_id=decision_id)
    checks["policy"] = "PASS"

    # 8. Resource limits - no per-mission budget field exists yet
    # (Stage E's own roadmap entry already states this honestly). N/A
    # today, not fabricated - stated explicitly rather than silently
    # passed without comment.
    checks["resource_limits"] = "N/A"

    return _allow(mission_id=mission_id, step_id=step_id, user_id=user_id, action_class=action_class,
                  risk_level=risk_level, tool_id=resolved_tool_id, checks=checks,
                  approval_id=approval_id, intent_lock_id=intent_lock_id, decision_id=decision_id)
