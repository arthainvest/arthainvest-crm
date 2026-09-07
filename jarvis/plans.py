#!/usr/bin/env python3
"""
JARVIS Plan + PlanStep durable model — Stage C (Planner), built on top of
Stage B's Mission/MissionStep substrate (jarvis/missions.py).

Architecture, per the explicit instruction this stage was authorized under:

    LLM / Reasoning (Claude, outside this file - a skill proposes steps)
          |
    Structured Plan (create_plan() - just persists what was proposed)
          |
    Schema validation (validate_plan() - step 1)
          |
    Deterministic Planner Validator (validate_plan() - circular deps,
          capability availability, risk/approval/verification presence)
          |
    Policy / capability checks (transaction-pattern scan, reusing
          backend/policy.py - the same single source of truth every other
          layer of this project uses)
          |
    Validated Plan (status = VALID, or INVALID with structured reasons)

This file does NOT decompose a goal into steps itself - that would require
an LLM call, which would need network access, which jarvis/ deliberately
never has (see jarvis/tests/test_jarvis_cannot_touch_transactions.py's
zero-network-import guarantee - this stays true for plans.py too). The
"reasoning" step happens in Claude/a skill, which calls create_plan() with
already-decomposed steps; everything in this file is the deterministic
validation and persistence half of the architecture above.

The Planner MUST NOT execute tools and MUST NOT perform external side
effects - nothing in this file calls anything outside its own SQLite file.
materialize_plan() only creates MissionSteps (Stage B's ledger rows) - it
does not run them. Running a MissionStep is Stage D (Worker Runtime), not
built yet.
"""

import argparse
import json
import sqlite3
import sys
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import missions as msn  # noqa: E402
import capabilities as caps  # noqa: E402
from policy import find_prohibited_routes  # noqa: E402 - the SAME pattern list backend/main.py and jarvis/memory.py's isolation test use, never duplicated

DB_PATH = Path(__file__).resolve().parent / "jarvis.db"

PLAN_STATUSES = {"DRAFT", "VALIDATING", "VALID", "INVALID", "SUPERSEDED", "CANCELLED"}
TERMINAL_PLAN_STATUSES = {"SUPERSEDED", "CANCELLED"}  # VALID/INVALID can still be re-validated or superseded; these two cannot change further
RISK_LEVELS = {"R0", "R1", "R2", "R3", "R4"}
CONSEQUENTIAL_RISK_LEVELS = {"R2", "R3", "R4"}  # per spec: "every consequential step must have a verification strategy"

ASK_USER_CAPABILITY = "ask-user-clarification"


# ---------------------------------------------------------------------------
# Errors (reuses missions.py's ErrorObject shape, same canonical fields)
# ---------------------------------------------------------------------------

@dataclass
class ErrorObject:
    code: str
    category: str
    severity: str = "ERROR"
    retryable: bool = False
    user_action_required: bool = False
    message: str = ""
    plan_id: str = None
    step_local_id: str = None
    metadata: dict = field(default_factory=dict)
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self):
        return asdict(self)


class PlanError(Exception):
    def __init__(self, error: ErrorObject):
        self.error = error
        super().__init__(error.message)


class PlanNotFoundError(PlanError):
    def __init__(self, plan_id, user_id):
        super().__init__(ErrorObject(code="PLAN_NOT_FOUND", category="STATE", plan_id=plan_id,
                                      message=f"No plan {plan_id!r} for this user.", metadata={"user_id": user_id}))


class PlanValidationError(PlanError):
    def __init__(self, message, plan_id=None, step_local_id=None):
        super().__init__(ErrorObject(code="INVALID_INPUT", category="VALIDATION", plan_id=plan_id,
                                      step_local_id=step_local_id, message=message))


class InvalidPlanStateError(PlanError):
    def __init__(self, message, plan_id=None):
        super().__init__(ErrorObject(code="INVALID_MISSION_STATE", category="STATE", plan_id=plan_id, message=message))


class TransactionProhibitedError(PlanError):
    """Raised (not just returned as a status) when a proposed plan contains
    a financial-transaction-shaped step. Mirrors backend/policy.py's own
    ProhibitedRoutePolicyViolation: this is CRITICAL, non-retryable, and
    the plan is never materialized into MissionSteps regardless of caller
    behavior - see materialize_plan()'s own independent re-check below."""

    def __init__(self, plan_id, matches):
        super().__init__(ErrorObject(
            code="TRANSACTION_PROHIBITED", category="POLICY", severity="CRITICAL",
            retryable=False, user_action_required=False, plan_id=plan_id,
            message="This plan contains a financial-transaction-shaped step and cannot be created or validated.",
            metadata={"matches": matches},
        ))


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
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_plans (
                plan_id TEXT PRIMARY KEY,
                mission_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                previous_plan_id TEXT,
                objective TEXT NOT NULL,
                assumptions TEXT,
                constraints TEXT,
                required_capabilities TEXT,
                required_tools TEXT,
                risk_level TEXT,
                approval_requirements TEXT,
                verification_strategy TEXT,
                fallback_strategy TEXT,
                parallel_groups TEXT,
                status TEXT NOT NULL,
                clarification_needed INTEGER NOT NULL DEFAULT 0,
                transaction_prohibited INTEGER NOT NULL DEFAULT 0,
                limitations TEXT,
                materialized INTEGER NOT NULL DEFAULT 0,
                mission_step_ids TEXT,
                last_idempotency_key TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_plan_steps (
                plan_step_id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                local_id TEXT NOT NULL,
                description TEXT NOT NULL,
                purpose TEXT,
                required_capability TEXT,
                worker_type TEXT,
                required_tools TEXT,
                dependencies TEXT NOT NULL DEFAULT '[]',
                inputs TEXT,
                unresolved_inputs TEXT NOT NULL DEFAULT '[]',
                expected_output TEXT,
                risk_level TEXT NOT NULL DEFAULT 'R1',
                approval_required INTEGER NOT NULL DEFAULT 0,
                verification_required INTEGER NOT NULL DEFAULT 0,
                fallback TEXT,
                mission_step_id TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (plan_id) REFERENCES jarvis_plans(plan_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_plans_mission ON jarvis_plans(mission_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_plan_steps_plan ON jarvis_plan_steps(plan_id)")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _row_to_plan(row) -> dict:
    d = dict(row)
    for jf in ("assumptions", "constraints", "required_capabilities", "required_tools",
               "approval_requirements", "parallel_groups", "limitations", "mission_step_ids"):
        d[jf] = json.loads(d[jf]) if d[jf] else ([] if jf != "parallel_groups" else None)
    d["clarification_needed"] = bool(d["clarification_needed"])
    d["transaction_prohibited"] = bool(d["transaction_prohibited"])
    d["materialized"] = bool(d["materialized"])
    return d


def _row_to_plan_step(row) -> dict:
    d = dict(row)
    d["dependencies"] = json.loads(d["dependencies"] or "[]")
    d["unresolved_inputs"] = json.loads(d["unresolved_inputs"] or "[]")
    d["inputs"] = json.loads(d["inputs"]) if d["inputs"] else None
    d["required_tools"] = json.loads(d["required_tools"]) if d["required_tools"] else []
    d["expected_output"] = json.loads(d["expected_output"]) if d["expected_output"] else None
    d["fallback"] = json.loads(d["fallback"]) if d["fallback"] else None
    d["approval_required"] = bool(d["approval_required"])
    d["verification_required"] = bool(d["verification_required"])
    return d


def _scan_for_prohibited_text(*texts) -> list:
    """Runs the same pattern list backend/policy.py enforces against CRM
    routes, against arbitrary plan text - the identical technique
    jarvis/tests/test_jarvis_cannot_touch_transactions.py already uses to
    scan jarvis/*.py's own source. One source of truth, three use sites."""
    combined = " | ".join(t for t in texts if t)
    if not combined:
        return []
    return [pattern for _, pattern in find_prohibited_routes([combined])]


def _topological_info(steps: list) -> dict:
    """steps: list of dicts with 'local_id' and 'dependencies' (list of
    local_ids). Returns {'cycle': bool, 'levels': {local_id: int}, 'order': [...]}.
    Levels are used to compute parallel_groups (same level, no direct edge
    = safe to run in parallel; this doesn't re-check "no direct edge within
    a level" separately because Kahn's algorithm by construction never
    puts two directly-dependent nodes in the same level)."""
    ids = [s["local_id"] for s in steps]
    deps = {s["local_id"]: list(s.get("dependencies") or []) for s in steps}
    indegree = {i: 0 for i in ids}
    children = {i: [] for i in ids}
    for i in ids:
        for d in deps[i]:
            if d in indegree:
                indegree[i] += 1
                children[d].append(i)

    levels = {}
    frontier = [i for i in ids if indegree[i] == 0]
    for i in frontier:
        levels[i] = 0
    order = []
    remaining_indegree = dict(indegree)
    queue = list(frontier)
    while queue:
        node = queue.pop(0)
        order.append(node)
        for child in children[node]:
            remaining_indegree[child] -= 1
            levels[child] = max(levels.get(child, 0), levels[node] + 1)
            if remaining_indegree[child] == 0:
                queue.append(child)

    cycle = len(order) != len(ids)
    return {"cycle": cycle, "levels": levels, "order": order}


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create_plan(mission_id, user_id, objective, steps, *, assumptions=None, constraints=None,
                 risk_level=None, verification_strategy=None, fallback_strategy=None,
                 previous_plan_id=None, version=1, idempotency_key=None) -> dict:
    """`steps`: list of dicts, each with at minimum 'local_id' and
    'description'. Optional per-step keys: purpose, required_capability,
    worker_type, required_tools (list), dependencies (list of local_ids),
    inputs (dict), unresolved_inputs (list of names), expected_output,
    risk_level (default 'R1'), approval_required (bool), verification_required
    (bool), fallback.

    Does NOT validate - call validate_plan() next. Kept separate so a plan
    can exist in DRAFT (e.g. for inspection/UI preview) before the
    deterministic checks run, matching the spec's own DRAFT -> VALIDATING
    -> VALID/INVALID sequence."""
    msn.get_mission(mission_id, user_id)  # raises MissionNotFoundError if not owned/found

    if not objective or not str(objective).strip():
        raise PlanValidationError("objective is required", plan_id=None)
    if not steps:
        raise PlanValidationError("a plan must have at least one step", plan_id=None)

    if idempotency_key:
        with _connect() as conn:
            existing = conn.execute(
                "SELECT plan_id FROM jarvis_plans WHERE mission_id = ? AND last_idempotency_key = ?",
                (mission_id, idempotency_key),
            ).fetchone()
        if existing:
            return get_plan(existing["plan_id"], user_id)

    seen_local_ids = set()
    for s in steps:
        if "local_id" not in s or not s["local_id"]:
            raise PlanValidationError("every step needs a local_id (used to wire dependencies)", plan_id=None)
        if s["local_id"] in seen_local_ids:
            raise PlanValidationError(f"duplicate local_id {s['local_id']!r} in one plan", plan_id=None)
        seen_local_ids.add(s["local_id"])
        if not s.get("description") or not str(s["description"]).strip():
            raise PlanValidationError(f"step {s['local_id']!r} is missing a description", plan_id=None, step_local_id=s["local_id"])
    for s in steps:
        for dep in s.get("dependencies") or []:
            if dep not in seen_local_ids:
                raise PlanValidationError(f"step {s['local_id']!r} depends on unknown local_id {dep!r}", plan_id=None, step_local_id=s["local_id"])

    required_capabilities = sorted({s["required_capability"] for s in steps if s.get("required_capability")})
    required_tools = sorted({t for s in steps for t in (s.get("required_tools") or [])})
    approval_requirements = sorted(s["local_id"] for s in steps if s.get("approval_required"))

    plan_id = str(uuid.uuid4())
    now = _now()
    with _connect() as conn:
        conn.execute("""
            INSERT INTO jarvis_plans
                (plan_id, mission_id, user_id, version, previous_plan_id, objective,
                 assumptions, constraints, required_capabilities, required_tools,
                 risk_level, approval_requirements, verification_strategy, fallback_strategy,
                 status, last_idempotency_key, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT', ?, ?, ?)
        """, (plan_id, mission_id, user_id, version, previous_plan_id, objective,
              json.dumps(assumptions or []), json.dumps(constraints or []),
              json.dumps(required_capabilities), json.dumps(required_tools),
              risk_level, json.dumps(approval_requirements),
              verification_strategy, fallback_strategy, idempotency_key, now, now))

        for s in steps:
            conn.execute("""
                INSERT INTO jarvis_plan_steps
                    (plan_step_id, plan_id, local_id, description, purpose, required_capability,
                     worker_type, required_tools, dependencies, inputs, unresolved_inputs,
                     expected_output, risk_level, approval_required, verification_required,
                     fallback, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), plan_id, s["local_id"], s["description"], s.get("purpose"),
                  s.get("required_capability"), s.get("worker_type"),
                  json.dumps(s.get("required_tools") or []), json.dumps(s.get("dependencies") or []),
                  json.dumps(s.get("inputs")) if s.get("inputs") is not None else None,
                  json.dumps(s.get("unresolved_inputs") or []), json.dumps(s.get("expected_output")) if s.get("expected_output") is not None else None,
                  s.get("risk_level") or "R1", int(bool(s.get("approval_required"))),
                  int(bool(s.get("verification_required"))),
                  json.dumps(s.get("fallback")) if s.get("fallback") is not None else None, now))

    return get_plan(plan_id, user_id)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def get_plan(plan_id, user_id) -> dict:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jarvis_plans WHERE plan_id = ? AND user_id = ?", (plan_id, user_id)).fetchone()
    if row is None:
        raise PlanNotFoundError(plan_id, user_id)
    plan = _row_to_plan(row)
    plan["steps"] = list_plan_steps(plan_id, user_id)
    return plan


def list_plan_steps(plan_id, user_id) -> list:
    get_plan_shallow(plan_id, user_id)
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM jarvis_plan_steps WHERE plan_id = ? ORDER BY created_at ASC", (plan_id,)).fetchall()
    return [_row_to_plan_step(r) for r in rows]


def get_plan_shallow(plan_id, user_id) -> dict:
    """Like get_plan but without recursing into list_plan_steps (which
    itself calls this) - avoids infinite recursion while still enforcing
    user isolation before returning step rows."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jarvis_plans WHERE plan_id = ? AND user_id = ?", (plan_id, user_id)).fetchone()
    if row is None:
        raise PlanNotFoundError(plan_id, user_id)
    return _row_to_plan(row)


def list_plans(mission_id, user_id) -> list:
    msn.get_mission(mission_id, user_id)
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM jarvis_plans WHERE mission_id = ? AND user_id = ? ORDER BY version ASC",
            (mission_id, user_id),
        ).fetchall()
    return [_row_to_plan(r) for r in rows]


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

def validate_plan(plan_id, user_id) -> dict:
    """Runs every deterministic check from spec Section 6, in order, and
    persists the result. Never asks an LLM anything - every check here is
    pure code against what create_plan() already stored."""
    plan = get_plan_shallow(plan_id, user_id)
    if plan["status"] in TERMINAL_PLAN_STATUSES:
        raise InvalidPlanStateError(f"Plan {plan_id!r} is {plan['status']} and cannot be re-validated.", plan_id=plan_id)

    with _connect() as conn:
        conn.execute("UPDATE jarvis_plans SET status = 'VALIDATING', updated_at = ? WHERE plan_id = ?", (_now(), plan_id))

    steps = list_plan_steps(plan_id, user_id)
    limitations = []
    transaction_prohibited = False
    clarification_needed = False

    # 1. Mission state permits planning.
    mission = msn.get_mission(plan["mission_id"], user_id)
    if mission["status"] in msn.TERMINAL_MISSION_STATUSES:
        limitations.append({"type": "INVALID_MISSION_STATE", "detail": f"mission is {mission['status']} (terminal)"})

    # 2. Schema validity was already enforced at create_plan() time (every
    # step has a description and a unique local_id) - re-confirmed here
    # defensively since a plan could in principle be re-validated after a
    # schema assumption changes.
    for s in steps:
        if not s.get("description"):
            limitations.append({"type": "MISSING_REQUIRED_FIELD", "step": s["local_id"], "detail": "missing description"})

    # 3. Circular dependency check + parallel-group computation.
    topo = _topological_info(steps)
    if topo["cycle"]:
        involved = sorted(set(s["local_id"] for s in steps) - set(topo["order"]))
        limitations.append({"type": "CIRCULAR_DEPENDENCY", "detail": f"cycle involves: {involved}"})
        parallel_groups = None
    else:
        by_level = {}
        for local_id, level in topo["levels"].items():
            by_level.setdefault(level, []).append(local_id)
        parallel_groups = [sorted(by_level[lvl]) for lvl in sorted(by_level)]

    # 4/5. Capability availability + transaction-pattern scan (independent
    # checks - a step can fail one, the other, both, or neither). Note the
    # capability registry (capabilities.py) deliberately never enumerates
    # transaction-shaped capabilities at all - see that file's comment.
    # TRANSACTION_PROHIBITED is only ever raised by the dynamic text scan
    # below, which reuses backend/policy.py directly (single source of truth).
    for s in steps:
        cap_id = s.get("required_capability")
        if cap_id and not caps.is_available(cap_id):
            limitations.append({"type": "CAPABILITY_UNAVAILABLE", "step": s["local_id"], "capability": cap_id,
                                 "reason": caps.unavailable_reason(cap_id)})

        matches = _scan_for_prohibited_text(
            s.get("description"), s.get("purpose"), cap_id, s.get("worker_type"),
            json.dumps(s.get("required_tools")) if s.get("required_tools") else None,
            json.dumps(s.get("fallback")) if s.get("fallback") else None,
        )
        if matches:
            transaction_prohibited = True
            limitations.append({"type": "TRANSACTION_PROHIBITED", "step": s["local_id"], "matched_patterns": matches})

    # 6. Input validity - unresolved inputs don't block VALID, but do
    # require clarification (spec Section 16's PLAN_POSSIBLE_AFTER_CLARIFICATION).
    for s in steps:
        if s.get("unresolved_inputs"):
            clarification_needed = True
            limitations.append({"type": "INPUT_UNRESOLVED", "step": s["local_id"], "inputs": s["unresolved_inputs"]})

    # 7/9. Risk classification + verification-for-consequential-steps.
    for s in steps:
        if s.get("risk_level") not in RISK_LEVELS:
            limitations.append({"type": "MISSING_REQUIRED_FIELD", "step": s["local_id"], "detail": "invalid/missing risk_level"})
        if s.get("risk_level") in CONSEQUENTIAL_RISK_LEVELS and not s.get("verification_required"):
            limitations.append({"type": "MISSING_VERIFICATION_STRATEGY", "step": s["local_id"],
                                 "detail": f"risk {s.get('risk_level')} steps must set verification_required=true"})

    # 10. Resource limits - no Mission-level budget field exists yet
    # (Stage B didn't add one; not fabricated here either). Honestly N/A.

    blocking_types = {"INVALID_MISSION_STATE", "MISSING_REQUIRED_FIELD", "CIRCULAR_DEPENDENCY",
                       "CAPABILITY_UNAVAILABLE", "TRANSACTION_PROHIBITED", "MISSING_VERIFICATION_STRATEGY"}
    has_blocking = any(l["type"] in blocking_types for l in limitations)
    status = "INVALID" if has_blocking else "VALID"

    with _connect() as conn:
        conn.execute("""
            UPDATE jarvis_plans
            SET status = ?, clarification_needed = ?, transaction_prohibited = ?,
                limitations = ?, parallel_groups = ?, updated_at = ?
            WHERE plan_id = ?
        """, (status, int(clarification_needed), int(transaction_prohibited),
              json.dumps(limitations), json.dumps(parallel_groups) if parallel_groups is not None else None,
              _now(), plan_id))

    if transaction_prohibited:
        # Raised, not just returned - per spec Section 11: "do not defer
        # the transaction block to Stage D or Stage J." The plan record
        # itself still exists (status=INVALID, transaction_prohibited=True)
        # for audit purposes, but the caller gets a hard stop, matching
        # missions.py/backend policy.py's existing "no soft failure for
        # this category" pattern.
        raise TransactionProhibitedError(plan_id, [l for l in limitations if l["type"] == "TRANSACTION_PROHIBITED"])

    return get_plan(plan_id, user_id)


# ---------------------------------------------------------------------------
# Replan / supersede / cancel
# ---------------------------------------------------------------------------

def create_replan(mission_id, user_id, previous_plan_id, objective, steps, **kwargs) -> dict:
    """Creates a new plan version and marks the previous one SUPERSEDED.
    Never edits the previous plan's own content - only its status - so its
    historical meaning (what it said at the time) is never silently
    rewritten, per spec Section 9."""
    previous = get_plan_shallow(previous_plan_id, user_id)
    if previous["mission_id"] != mission_id:
        raise PlanValidationError("previous_plan_id does not belong to this mission", plan_id=previous_plan_id)
    if previous["status"] in TERMINAL_PLAN_STATUSES:
        raise InvalidPlanStateError(f"Cannot replan from a plan that is already {previous['status']}.", plan_id=previous_plan_id)

    new_plan = create_plan(mission_id, user_id, objective, steps,
                            previous_plan_id=previous_plan_id, version=previous["version"] + 1, **kwargs)

    with _connect() as conn:
        conn.execute("UPDATE jarvis_plans SET status = 'SUPERSEDED', updated_at = ? WHERE plan_id = ? AND user_id = ?",
                      (_now(), previous_plan_id, user_id))

    return new_plan


def cancel_plan(plan_id, user_id) -> dict:
    plan = get_plan_shallow(plan_id, user_id)
    if plan["status"] == "CANCELLED":
        return get_plan(plan_id, user_id)
    if plan["status"] in TERMINAL_PLAN_STATUSES:
        raise InvalidPlanStateError(f"Plan {plan_id!r} is {plan['status']} and cannot be cancelled.", plan_id=plan_id)
    with _connect() as conn:
        conn.execute("UPDATE jarvis_plans SET status = 'CANCELLED', updated_at = ? WHERE plan_id = ? AND user_id = ?",
                      (_now(), plan_id, user_id))
    return get_plan(plan_id, user_id)


# ---------------------------------------------------------------------------
# Materialize: Plan -> real MissionSteps (Stage B). No execution occurs.
# ---------------------------------------------------------------------------

def materialize_plan(plan_id, user_id) -> dict:
    """Only allowed for a VALID, non-transaction-prohibited plan. Creates
    one real missions.create_step() per PlanStep, in dependency order,
    translating local_id references into the real mission_step_ids Stage B
    assigns. Idempotent: if this plan was already materialized, returns
    the existing mapping rather than creating duplicate MissionSteps."""
    plan = get_plan(plan_id, user_id)
    if plan["materialized"]:
        return plan  # already done - no duplicates created

    if plan["status"] != "VALID":
        raise InvalidPlanStateError(f"Only a VALID plan can be materialized (this one is {plan['status']}).", plan_id=plan_id)
    if plan["transaction_prohibited"]:
        # Defense in depth: validate_plan() should already have raised for
        # this, so reaching here with the flag set means something bypassed
        # that path - refuse anyway, exactly like backend/policy.py's own
        # "no override path" rule for this category.
        raise TransactionProhibitedError(plan_id, plan["limitations"])

    steps = list_plan_steps(plan_id, user_id)
    topo = _topological_info(steps)
    if topo["cycle"]:
        raise InvalidPlanStateError("Cannot materialize a plan with a circular dependency.", plan_id=plan_id)

    by_local_id = {s["local_id"]: s for s in steps}
    local_to_mission_step_id = {}

    with _connect() as conn:
        pass  # ensure DB exists / connection valid before the loop below

    for local_id in topo["order"]:
        s = by_local_id[local_id]
        real_deps = [local_to_mission_step_id[d] for d in s["dependencies"]]
        created = msn.create_step(
            plan["mission_id"], user_id, s["description"],
            worker_id=s.get("required_capability") or s.get("worker_type"),
            dependencies=real_deps,
            inputs=s.get("inputs"),
            expected_output=s.get("expected_output"),
        )
        local_to_mission_step_id[local_id] = created["step_id"]
        with _connect() as conn:
            conn.execute("UPDATE jarvis_plan_steps SET mission_step_id = ? WHERE plan_id = ? AND local_id = ?",
                          (created["step_id"], plan_id, local_id))

    mission_step_ids = [local_to_mission_step_id[s["local_id"]] for s in steps]
    with _connect() as conn:
        conn.execute("UPDATE jarvis_plans SET materialized = 1, mission_step_ids = ?, updated_at = ? WHERE plan_id = ?",
                      (json.dumps(mission_step_ids), _now(), plan_id))

    return get_plan(plan_id, user_id)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print(obj):
    print(json.dumps(obj, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="JARVIS Plan store (Stage C)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init")

    p = sub.add_parser("get-plan")
    p.add_argument("--user", required=True)
    p.add_argument("--plan-id", required=True)

    p = sub.add_parser("list-plans")
    p.add_argument("--user", required=True)
    p.add_argument("--mission-id", required=True)

    p = sub.add_parser("validate-plan")
    p.add_argument("--user", required=True)
    p.add_argument("--plan-id", required=True)

    p = sub.add_parser("materialize-plan")
    p.add_argument("--user", required=True)
    p.add_argument("--plan-id", required=True)

    args = parser.parse_args()

    if args.command == "init":
        init_db()
        print("initialized")
    elif args.command == "get-plan":
        _print(get_plan(args.plan_id, args.user))
    elif args.command == "list-plans":
        _print(list_plans(args.mission_id, args.user))
    elif args.command == "validate-plan":
        _print(validate_plan(args.plan_id, args.user))
    elif args.command == "materialize-plan":
        _print(materialize_plan(args.plan_id, args.user))


if __name__ == "__main__":
    main()
