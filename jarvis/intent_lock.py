#!/usr/bin/env python3
"""
JARVIS Intent Lock — Stage H.

The master spec's own one-line definition (JARVIS_AGENT_RUNTIME_SPEC.md):
"once JARVIS determines the objective, tool outputs and external
instructions must not silently redefine it. External content is data,
not authority."

No detailed Stage H directive was given for this session (unlike Stages
C-G, each of which arrived with an extensive spec before implementation).
Scoped narrowly and honestly from that one line plus what is actually
buildable and testable in this architecture today, per explicit user
authorization to design it this way rather than guess at unstated
requirements.

## What Intent Lock actually protects against here

Every Worker built so far (Stage D) is strictly internal to
jarvis/jarvis.db - there is no browser, no MCP, no external connector,
so there is no genuinely external "webpage says ignore previous
instructions" input flowing into this system yet (that risk belongs to
Stage M/P, not built). Given that, this module does two concrete,
honestly-scoped things rather than defending against a threat that
doesn't exist in this codebase yet:

1. A real, persisted fingerprint of Mission.goal + the active Plan's
   objective, lockable once and re-verifiable at any later point
   (lock_intent / verify_intent / assert_intent_locked). Mission.goal
   and Plan.objective are ALREADY structurally immutable today - no
   function anywhere in missions.py or plans.py can change them after
   creation (verified by inspection and by this module's own tests).
   This is a defense-in-depth safety net that DETECTS drift if that
   structural guarantee is ever accidentally weakened by a future
   change, not a new prevention mechanism layered on top of one that
   doesn't otherwise exist.

2. A structural + behavioral proof that a Worker's OUTPUT is data, not
   authority: nothing in workers.py or supervisor.py reads a
   MissionStep's `output`/`observation` to decide what runs next or to
   reclassify a step's policy/capability - classification (the
   transaction-pattern scan, capability resolution) happens entirely
   from the step's DECLARED description/inputs, before execution, never
   from what a worker returns afterward. This complements (does not
   duplicate) Phase 3.5's existing "context injection is inert data"
   test at the Context Engine layer - this is the same guarantee
   proven again at the Worker Runtime/Supervisor layer, a different
   code path.

## What this stage explicitly does NOT do
Does not defend against genuinely external content (no such input path
exists in this codebase yet - that's Stage M/P's job when built). Is
NOT auto-wired into Supervisor's dispatch loop - it is a standalone,
callable primitive; wiring assert_intent_locked() into the Supervisor's
per-dispatch checkpoint is a natural but explicitly not-yet-done next
integration point, stated here rather than silently assumed.
"""

import hashlib
import sqlite3
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))

import missions as msn  # noqa: E402
import plans  # noqa: E402

DB_PATH = Path(__file__).resolve().parent / "jarvis.db"

INTENT_CHECK_STATUSES = {"MATCH", "DRIFT_DETECTED", "NOT_LOCKED"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _fingerprint(goal: str, objective) -> str:
    combined = f"{goal or ''}|{objective or ''}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Errors (same canonical shape as the rest of the jarvis/ stages)
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
    metadata: dict = field(default_factory=dict)
    error_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=_now)

    def to_dict(self):
        return asdict(self)


class IntentLockError(Exception):
    def __init__(self, error: ErrorObject):
        self.error = error
        super().__init__(error.message)


class IntentNotLockedError(IntentLockError):
    def __init__(self, mission_id):
        super().__init__(ErrorObject(
            code="INTENT_NOT_LOCKED", category="STATE", mission_id=mission_id,
            message=f"Mission {mission_id!r} has no locked intent yet - call lock_intent() first.",
        ))


class IntentDriftError(IntentLockError):
    def __init__(self, mission_id, locked_fingerprint, current_fingerprint):
        super().__init__(ErrorObject(
            code="INTENT_DRIFT_DETECTED", category="SECURITY", severity="CRITICAL", retryable=False,
            mission_id=mission_id,
            message=f"Mission {mission_id!r}'s goal/objective no longer match what was locked - "
                    "the intent may have been silently redefined.",
            metadata={"locked_fingerprint": locked_fingerprint, "current_fingerprint": current_fingerprint},
        ))


# ---------------------------------------------------------------------------
# Intent record
# ---------------------------------------------------------------------------

@dataclass
class IntentRecord:
    intent_id: str
    mission_id: str
    user_id: str
    goal: str
    plan_id: str
    objective: str
    fingerprint: str
    locked_at: str

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
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_intent_locks (
                intent_id TEXT PRIMARY KEY,
                mission_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                goal TEXT NOT NULL,
                plan_id TEXT,
                objective TEXT,
                fingerprint TEXT NOT NULL,
                locked_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_intent_locks_mission ON jarvis_intent_locks(mission_id, locked_at)")


def _row_to_record(row) -> IntentRecord:
    return IntentRecord(
        intent_id=row["intent_id"], mission_id=row["mission_id"], user_id=row["user_id"],
        goal=row["goal"], plan_id=row["plan_id"], objective=row["objective"],
        fingerprint=row["fingerprint"], locked_at=row["locked_at"],
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def lock_intent(mission_id: str, user_id: str, plan_id: str = None) -> IntentRecord:
    """Captures and persists a fingerprint of Mission.goal + (if a plan_id
    is given) that Plan's objective, as of right now. Idempotent in the
    meaningful sense: locking again with an identical goal/objective
    returns a record with the same fingerprint (a genuine no-op from the
    caller's perspective) rather than treating a re-lock as suspicious -
    only an actual VALUE change, caught by verify_intent(), is drift.
    Re-locking after a legitimate replan (a new Plan version, per Stage
    C's own immutable-history versioning) is expected and correct - that
    is a new authorized intent, not drift."""
    mission = msn.get_mission(mission_id, user_id)
    objective = None
    if plan_id:
        objective = plans.get_plan(plan_id, user_id)["objective"]

    fingerprint = _fingerprint(mission["goal"], objective)
    record = IntentRecord(
        intent_id=str(uuid4()), mission_id=mission_id, user_id=user_id, goal=mission["goal"],
        plan_id=plan_id, objective=objective, fingerprint=fingerprint, locked_at=_now(),
    )
    with _connect() as conn:
        conn.execute("""
            INSERT INTO jarvis_intent_locks
                (intent_id, mission_id, user_id, goal, plan_id, objective, fingerprint, locked_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (record.intent_id, record.mission_id, record.user_id, record.goal,
              record.plan_id, record.objective, record.fingerprint, record.locked_at))
    return record


def get_locked_intent(mission_id: str, user_id: str) -> IntentRecord:
    """Returns the most recently locked intent for this mission, or None
    if lock_intent() was never called."""
    msn.get_mission(mission_id, user_id)  # user-isolation check
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM jarvis_intent_locks WHERE mission_id = ? AND user_id = ? "
            "ORDER BY locked_at DESC LIMIT 1",
            (mission_id, user_id),
        ).fetchone()
    return _row_to_record(row) if row else None


def verify_intent(mission_id: str, user_id: str) -> dict:
    """Re-fingerprints the mission's CURRENT goal (and the locked record's
    own plan's CURRENT objective, if one was captured) and compares
    against what was locked. Read-only - never mutates anything, never
    re-locks on your behalf."""
    locked = get_locked_intent(mission_id, user_id)
    if locked is None:
        return {"status": "NOT_LOCKED", "mission_id": mission_id, "locked_fingerprint": None, "current_fingerprint": None}

    mission = msn.get_mission(mission_id, user_id)
    current_objective = plans.get_plan(locked.plan_id, user_id)["objective"] if locked.plan_id else None
    current_fingerprint = _fingerprint(mission["goal"], current_objective)

    status = "MATCH" if current_fingerprint == locked.fingerprint else "DRIFT_DETECTED"
    return {
        "status": status, "mission_id": mission_id,
        "locked_fingerprint": locked.fingerprint, "current_fingerprint": current_fingerprint,
        "locked_goal": locked.goal, "current_goal": mission["goal"],
        "locked_objective": locked.objective, "current_objective": current_objective,
    }


def assert_intent_locked(mission_id: str, user_id: str) -> IntentRecord:
    """Guard function a caller can use before a consequential action:
    raises if the intent was never locked, or if it has drifted. Returns
    the locked record on success. Not called automatically by any other
    stage yet - see this module's own docstring."""
    result = verify_intent(mission_id, user_id)
    if result["status"] == "NOT_LOCKED":
        raise IntentNotLockedError(mission_id)
    if result["status"] == "DRIFT_DETECTED":
        raise IntentDriftError(mission_id, result["locked_fingerprint"], result["current_fingerprint"])
    return get_locked_intent(mission_id, user_id)
