#!/usr/bin/env python3
"""
JARVIS Mission + MissionStep durable state model — Stage B of the agent
runtime build-out (JARVIS_AGENT_RUNTIME_SPEC.md, Sections 10-15).

This is deliberately ONLY the durable substrate: persistence, a strict state
machine, concurrency protection, idempotent transitions, cancellation,
canonical errors, restart recovery, and user isolation. It does NOT contain
a Planner, Workers, a Supervisor, a Verifier, or a Recovery Engine — those
are Stages C-G and are built on top of this, not inside it. Building this
narrowly first (per the explicit instruction not to jump ahead) means the
state machine itself gets tested in isolation before anything more complex
depends on it.

Same isolation model as memory.py/context.py: stdlib-only, own SQLite file
(jarvis/jarvis.db, shared physical file with memory.py's tables but its own
two tables here), zero network-capable imports, zero financial-transaction
capability (there is no "execute" concept here at all - a MissionStep only
ever *records* status, it never calls anything).

## Concurrency model
Optimistic locking via a `version` integer column. Every transition's UPDATE
is scoped to `WHERE id = ? AND version = ?` (the version read moments
earlier); if another writer changed the row in between, the UPDATE affects
zero rows and a StateConflictError is raised rather than silently
overwriting the other writer's change - "optimistic locking or equivalent"
per the spec's concurrency requirement.

## Idempotency
Callers may pass an `idempotency_key` to `transition_mission`/
`transition_step`. If the same key is replayed, the cached prior result is
returned rather than re-applying the transition - prevents duplicate side
effects from a retried caller (e.g. a supervisor that resends a request
after a timeout that actually succeeded).

## Restart recovery
`reconcile_interrupted()` is the answer to "what happens if the process
dies mid-mission." It does NOT assume an interrupted EXECUTING/RUNNING
state means the external action didn't happen - per spec Section 12/83,
that's unknown, not false. It moves such rows to BLOCKED with an
explicit `verification_state = "UNKNOWN"` and a structured error
explaining why, so a human or a future Recovery Engine (Stage G) has to
explicitly reconcile it - it can never be silently resumed or silently
marked complete.

## User isolation
Every mission has a `user_id`. Every read and every transition requires the
caller's `user_id` and is scoped to it - a mission belonging to another
user is indistinguishable from a mission that doesn't exist (MissionNotFound
either way), so existence itself is never leaked cross-user.
"""

import argparse
import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent / "jarvis.db"


# ---------------------------------------------------------------------------
# Canonical error model (spec Sections 13-15, scoped to what Stage B needs)
# ---------------------------------------------------------------------------

@dataclass
class ErrorObject:
    code: str
    category: str
    severity: str = "ERROR"
    retryable: bool = False
    user_action_required: bool = False
    message: str = ""
    technical_message: str = ""
    mission_id: Optional[str] = None
    step_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self):
        return asdict(self)


class MissionError(Exception):
    """Base for every canonical mission-runtime error. Always carries a
    structured ErrorObject (`.error`), never just a string, so a caller can
    branch on `.error.code`/`.error.retryable` rather than parsing text."""

    def __init__(self, error: ErrorObject):
        self.error = error
        super().__init__(error.message)


class MissionNotFoundError(MissionError):
    def __init__(self, mission_id, user_id):
        super().__init__(ErrorObject(
            code="MISSION_NOT_FOUND", category="STATE", severity="ERROR",
            retryable=False, mission_id=mission_id,
            message=f"No mission {mission_id!r} for this user.",
            metadata={"user_id": user_id},
        ))


class StepNotFoundError(MissionError):
    def __init__(self, step_id, mission_id=None):
        super().__init__(ErrorObject(
            code="STEP_NOT_FOUND", category="STATE", severity="ERROR",
            retryable=False, mission_id=mission_id, step_id=step_id,
            message=f"No step {step_id!r}.",
        ))


class InvalidStateTransitionError(MissionError):
    def __init__(self, entity, entity_id, from_status, to_status, mission_id=None, step_id=None):
        super().__init__(ErrorObject(
            code="INVALID_STATE_TRANSITION", category="STATE", severity="ERROR",
            retryable=False, mission_id=mission_id, step_id=step_id,
            message=f"{entity} {entity_id!r} cannot transition {from_status} -> {to_status}.",
            metadata={"from_status": from_status, "to_status": to_status},
        ))


class InvalidMissionStateError(MissionError):
    def __init__(self, message, mission_id=None, step_id=None):
        super().__init__(ErrorObject(
            code="INVALID_MISSION_STATE", category="STATE", severity="ERROR",
            retryable=False, mission_id=mission_id, step_id=step_id, message=message,
        ))


class StateConflictError(MissionError):
    """Raised when the optimistic-locking CAS fails - someone else changed
    this row between when the caller read it and when this write landed.
    Retryable = true: the caller should re-read and try again."""

    def __init__(self, entity, entity_id, mission_id=None, step_id=None):
        super().__init__(ErrorObject(
            code="STATE_CONFLICT", category="CONCURRENCY", severity="ERROR",
            retryable=True, mission_id=mission_id, step_id=step_id,
            message=f"{entity} {entity_id!r} was modified concurrently; re-read and retry.",
        ))


class MissionValidationError(MissionError):
    def __init__(self, message, mission_id=None, step_id=None):
        super().__init__(ErrorObject(
            code="INVALID_INPUT", category="VALIDATION", severity="ERROR",
            retryable=False, mission_id=mission_id, step_id=step_id, message=message,
        ))


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

MISSION_STATUSES = {
    "CREATED", "UNDERSTANDING", "PLANNING", "WAITING_FOR_APPROVAL", "READY",
    "EXECUTING", "WAITING", "VERIFYING", "RECOVERING", "REPLANNING",
    "COMPLETED", "PARTIALLY_COMPLETED", "FAILED", "BLOCKED", "CANCELLED", "EXPIRED",
}

TERMINAL_MISSION_STATUSES = {"COMPLETED", "PARTIALLY_COMPLETED", "FAILED", "CANCELLED", "EXPIRED"}

# Legal forward transitions. Terminal statuses map to an empty set - per
# spec Section 12, a terminal mission can never accidentally transition
# back into active execution, so there is no code path (other than a fresh
# `create_mission`) that adds an edge out of a terminal state.
MISSION_TRANSITIONS = {
    "CREATED": {"UNDERSTANDING", "CANCELLED"},
    "UNDERSTANDING": {"PLANNING", "BLOCKED", "FAILED", "CANCELLED"},
    "PLANNING": {"WAITING_FOR_APPROVAL", "READY", "BLOCKED", "FAILED", "CANCELLED"},
    "WAITING_FOR_APPROVAL": {"READY", "EXPIRED", "FAILED", "CANCELLED"},
    "READY": {"EXECUTING", "BLOCKED", "CANCELLED"},
    "EXECUTING": {"WAITING", "VERIFYING", "RECOVERING", "BLOCKED", "FAILED", "PARTIALLY_COMPLETED", "CANCELLED"},
    "WAITING": {"EXECUTING", "EXPIRED", "BLOCKED", "CANCELLED"},
    "VERIFYING": {"COMPLETED", "PARTIALLY_COMPLETED", "FAILED", "RECOVERING"},
    "RECOVERING": {"EXECUTING", "REPLANNING", "FAILED", "CANCELLED"},
    "REPLANNING": {"PLANNING", "FAILED", "CANCELLED"},
    "BLOCKED": {"EXECUTING", "PLANNING", "FAILED", "CANCELLED"},
    "COMPLETED": set(),
    "PARTIALLY_COMPLETED": set(),
    "FAILED": set(),
    "CANCELLED": set(),
    "EXPIRED": set(),
}

STEP_STATUSES = {
    "PENDING", "READY", "RUNNING", "WAITING", "WAITING_FOR_APPROVAL", "BLOCKED",
    "SUCCEEDED", "PARTIALLY_SUCCEEDED", "FAILED", "SKIPPED", "CANCELLED",
}

TERMINAL_STEP_STATUSES = {"SUCCEEDED", "PARTIALLY_SUCCEEDED", "FAILED", "SKIPPED", "CANCELLED"}

# Deliberately no FAILED -> READY edge here. Retrying a failed step is a
# Recovery Engine decision (Stage G, not built yet) - this substrate records
# that a step failed, but doesn't decide on its own that it should be
# re-attempted. Building that in here would be jumping ahead.
STEP_TRANSITIONS = {
    "PENDING": {"READY", "BLOCKED", "CANCELLED", "SKIPPED"},
    "READY": {"RUNNING", "BLOCKED", "CANCELLED", "SKIPPED"},
    "RUNNING": {"WAITING", "WAITING_FOR_APPROVAL", "SUCCEEDED", "PARTIALLY_SUCCEEDED", "FAILED", "CANCELLED"},
    "WAITING": {"RUNNING", "FAILED", "CANCELLED"},
    "WAITING_FOR_APPROVAL": {"RUNNING", "FAILED", "CANCELLED"},
    "BLOCKED": {"READY", "FAILED", "CANCELLED"},
    "SUCCEEDED": set(),
    "PARTIALLY_SUCCEEDED": set(),
    "FAILED": set(),
    "SKIPPED": set(),
    "CANCELLED": set(),
}

# Non-terminal statuses that, if still set when the process starts up again,
# mean "an in-flight action whose outcome we don't actually know" - these
# are exactly the ones reconcile_interrupted() sweeps.
INTERRUPTIBLE_MISSION_STATUSES = {"EXECUTING", "WAITING", "RECOVERING", "REPLANNING", "VERIFYING"}
INTERRUPTIBLE_STEP_STATUSES = {"RUNNING", "WAITING", "WAITING_FOR_APPROVAL"}


def _now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _connect():
    """Same pattern as memory.py's _connect() - a proper context manager
    that always closes the connection (see memory.py's docstring for why
    that matters on Windows specifically)."""
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
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_missions (
                mission_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                goal TEXT NOT NULL,
                intent_id TEXT,
                status TEXT NOT NULL,
                risk_level TEXT,
                plan_id TEXT,
                current_step_id TEXT,
                context_reference TEXT,
                deadline TEXT,
                result TEXT,
                error TEXT,
                verification_state TEXT,
                parent_mission_id TEXT,
                version INTEGER NOT NULL DEFAULT 1,
                last_idempotency_key TEXT,
                last_transition_result TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_mission_steps (
                step_id TEXT PRIMARY KEY,
                mission_id TEXT NOT NULL,
                worker_id TEXT,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                dependencies TEXT NOT NULL DEFAULT '[]',
                inputs TEXT,
                expected_output TEXT,
                output TEXT,
                observation TEXT,
                error TEXT,
                verification TEXT,
                attempt_count INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                version INTEGER NOT NULL DEFAULT 1,
                last_idempotency_key TEXT,
                last_transition_result TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (mission_id) REFERENCES jarvis_missions(mission_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_missions_user ON jarvis_missions(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_steps_mission ON jarvis_mission_steps(mission_id)")


def _row_to_mission(row) -> dict:
    d = dict(row)
    d["dependencies"] = None
    return d


def _row_to_step(row) -> dict:
    d = dict(row)
    d["dependencies"] = json.loads(d["dependencies"] or "[]")
    return d


# ---------------------------------------------------------------------------
# Mission CRUD + transitions
# ---------------------------------------------------------------------------

def create_mission(user_id, goal, intent_id=None, risk_level=None,
                    context_reference=None, deadline=None, parent_mission_id=None) -> dict:
    if not user_id or not str(user_id).strip():
        raise MissionValidationError("user_id is required")
    if not goal or not str(goal).strip():
        raise MissionValidationError("goal is required")

    mission_id = str(uuid.uuid4())
    now = _now()
    with _connect() as conn:
        conn.execute("""
            INSERT INTO jarvis_missions
                (mission_id, user_id, goal, intent_id, status, risk_level,
                 context_reference, deadline, parent_mission_id, version,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, 'CREATED', ?, ?, ?, ?, 1, ?, ?)
        """, (mission_id, user_id, goal, intent_id, risk_level,
              context_reference, deadline, parent_mission_id, now, now))
    return get_mission(mission_id, user_id)


def get_mission(mission_id, user_id) -> dict:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM jarvis_missions WHERE mission_id = ? AND user_id = ?",
            (mission_id, user_id),
        ).fetchone()
    if row is None:
        raise MissionNotFoundError(mission_id, user_id)
    return _row_to_mission(row)


def list_missions(user_id, status=None) -> list:
    with _connect() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM jarvis_missions WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                (user_id, status),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM jarvis_missions WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
    return [_row_to_mission(r) for r in rows]


def transition_mission(mission_id, user_id, to_status, *, error=None, result=None,
                        verification_state=None, idempotency_key=None) -> dict:
    if to_status not in MISSION_STATUSES:
        raise MissionValidationError(f"Unknown mission status {to_status!r}", mission_id=mission_id)

    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM jarvis_missions WHERE mission_id = ? AND user_id = ?",
            (mission_id, user_id),
        ).fetchone()
        if row is None:
            raise MissionNotFoundError(mission_id, user_id)

        if idempotency_key and row["last_idempotency_key"] == idempotency_key:
            cached = row["last_transition_result"]
            return json.loads(cached) if cached else _row_to_mission(row)

        current_status = row["status"]
        if current_status in TERMINAL_MISSION_STATUSES:
            raise InvalidStateTransitionError("Mission", mission_id, current_status, to_status, mission_id=mission_id)
        if to_status not in MISSION_TRANSITIONS.get(current_status, set()):
            raise InvalidStateTransitionError("Mission", mission_id, current_status, to_status, mission_id=mission_id)

        version = row["version"]
        now = _now()
        started_at = row["started_at"] or (now if to_status == "EXECUTING" and row["started_at"] is None else row["started_at"])
        completed_at = now if to_status in TERMINAL_MISSION_STATUSES else row["completed_at"]
        error_json = json.dumps(error) if error is not None else row["error"]
        result_json = json.dumps(result) if result is not None else row["result"]
        verification_state = verification_state if verification_state is not None else row["verification_state"]

        cur = conn.execute("""
            UPDATE jarvis_missions
            SET status = ?, version = version + 1, updated_at = ?,
                started_at = ?, completed_at = ?, error = ?, result = ?,
                verification_state = ?, last_idempotency_key = ?
            WHERE mission_id = ? AND user_id = ? AND version = ?
        """, (to_status, now, started_at, completed_at, error_json, result_json,
              verification_state, idempotency_key, mission_id, user_id, version))

        if cur.rowcount == 0:
            raise StateConflictError("Mission", mission_id, mission_id=mission_id)

        updated = conn.execute(
            "SELECT * FROM jarvis_missions WHERE mission_id = ?", (mission_id,)
        ).fetchone()
        result_dict = _row_to_mission(updated)

        if idempotency_key:
            conn.execute(
                "UPDATE jarvis_missions SET last_transition_result = ? WHERE mission_id = ?",
                (json.dumps(result_dict), mission_id),
            )

    return result_dict


def cancel_mission(mission_id, user_id, reason=None, idempotency_key=None) -> dict:
    """Cancellation is always available from any non-terminal state and is
    itself idempotent - cancelling an already-cancelled mission is a no-op,
    not an error (per the standing "user can always cancel" rule)."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM jarvis_missions WHERE mission_id = ? AND user_id = ?",
            (mission_id, user_id),
        ).fetchone()
        if row is None:
            raise MissionNotFoundError(mission_id, user_id)

        if row["status"] == "CANCELLED":
            return _row_to_mission(row)
        if row["status"] in TERMINAL_MISSION_STATUSES:
            raise InvalidStateTransitionError("Mission", mission_id, row["status"], "CANCELLED", mission_id=mission_id)

        version = row["version"]
        now = _now()
        error_json = json.dumps({"code": "MISSION_CANCELLED", "category": "USER", "reason": reason}) if reason else row["error"]

        cur = conn.execute("""
            UPDATE jarvis_missions
            SET status = 'CANCELLED', version = version + 1, updated_at = ?,
                completed_at = ?, error = ?, last_idempotency_key = ?
            WHERE mission_id = ? AND user_id = ? AND version = ?
        """, (now, now, error_json, idempotency_key, mission_id, user_id, version))

        if cur.rowcount == 0:
            raise StateConflictError("Mission", mission_id, mission_id=mission_id)

        updated = conn.execute("SELECT * FROM jarvis_missions WHERE mission_id = ?", (mission_id,)).fetchone()
    return _row_to_mission(updated)


# ---------------------------------------------------------------------------
# MissionStep CRUD + transitions
# ---------------------------------------------------------------------------

def create_step(mission_id, user_id, description, worker_id=None, dependencies=None,
                 inputs=None, expected_output=None, max_attempts=3) -> dict:
    get_mission(mission_id, user_id)  # raises MissionNotFoundError if not owned/found

    if not description or not str(description).strip():
        raise MissionValidationError("description is required", mission_id=mission_id)

    dependencies = dependencies or []
    with _connect() as conn:
        existing_ids = {r["step_id"] for r in conn.execute(
            "SELECT step_id FROM jarvis_mission_steps WHERE mission_id = ?", (mission_id,)
        ).fetchall()}
    unknown = set(dependencies) - existing_ids
    if unknown:
        raise MissionValidationError(f"Unknown dependency step_id(s): {sorted(unknown)}", mission_id=mission_id)

    step_id = str(uuid.uuid4())
    now = _now()
    with _connect() as conn:
        conn.execute("""
            INSERT INTO jarvis_mission_steps
                (step_id, mission_id, worker_id, description, status, dependencies,
                 inputs, expected_output, attempt_count, max_attempts, version,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, 'PENDING', ?, ?, ?, 0, ?, 1, ?, ?)
        """, (step_id, mission_id, worker_id, description, json.dumps(dependencies),
              json.dumps(inputs) if inputs is not None else None,
              json.dumps(expected_output) if expected_output is not None else None,
              max_attempts, now, now))
    return get_step(step_id, mission_id, user_id)


def get_step(step_id, mission_id, user_id) -> dict:
    get_mission(mission_id, user_id)  # user-isolation check
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM jarvis_mission_steps WHERE step_id = ? AND mission_id = ?",
            (step_id, mission_id),
        ).fetchone()
    if row is None:
        raise StepNotFoundError(step_id, mission_id)
    return _row_to_step(row)


def list_steps(mission_id, user_id) -> list:
    get_mission(mission_id, user_id)  # user-isolation check
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM jarvis_mission_steps WHERE mission_id = ? ORDER BY created_at ASC",
            (mission_id,),
        ).fetchall()
    return [_row_to_step(r) for r in rows]


def transition_step(step_id, mission_id, user_id, to_status, *, error=None,
                     output=None, observation=None, verification=None,
                     idempotency_key=None) -> dict:
    if to_status not in STEP_STATUSES:
        raise MissionValidationError(f"Unknown step status {to_status!r}", step_id=step_id, mission_id=mission_id)
    get_mission(mission_id, user_id)  # user-isolation check

    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM jarvis_mission_steps WHERE step_id = ? AND mission_id = ?",
            (step_id, mission_id),
        ).fetchone()
        if row is None:
            raise StepNotFoundError(step_id, mission_id)

        if idempotency_key and row["last_idempotency_key"] == idempotency_key:
            cached = row["last_transition_result"]
            return json.loads(cached) if cached else _row_to_step(row)

        current_status = row["status"]
        if current_status in TERMINAL_STEP_STATUSES:
            raise InvalidStateTransitionError("MissionStep", step_id, current_status, to_status, mission_id=mission_id, step_id=step_id)
        if to_status not in STEP_TRANSITIONS.get(current_status, set()):
            raise InvalidStateTransitionError("MissionStep", step_id, current_status, to_status, mission_id=mission_id, step_id=step_id)

        version = row["version"]
        now = _now()
        started_at = row["started_at"] or (now if to_status == "RUNNING" else row["started_at"])
        completed_at = now if to_status in TERMINAL_STEP_STATUSES else row["completed_at"]
        attempt_count = row["attempt_count"] + (1 if to_status == "RUNNING" else 0)
        error_json = json.dumps(error) if error is not None else row["error"]
        output_json = json.dumps(output) if output is not None else row["output"]
        observation_json = json.dumps(observation) if observation is not None else row["observation"]
        verification_json = json.dumps(verification) if verification is not None else row["verification"]

        cur = conn.execute("""
            UPDATE jarvis_mission_steps
            SET status = ?, version = version + 1, updated_at = ?, started_at = ?,
                completed_at = ?, attempt_count = ?, error = ?, output = ?,
                observation = ?, verification = ?, last_idempotency_key = ?
            WHERE step_id = ? AND mission_id = ? AND version = ?
        """, (to_status, now, started_at, completed_at, attempt_count, error_json,
              output_json, observation_json, verification_json, idempotency_key,
              step_id, mission_id, version))

        if cur.rowcount == 0:
            raise StateConflictError("MissionStep", step_id, mission_id=mission_id, step_id=step_id)

        updated = conn.execute("SELECT * FROM jarvis_mission_steps WHERE step_id = ?", (step_id,)).fetchone()
        result_dict = _row_to_step(updated)

        if idempotency_key:
            conn.execute(
                "UPDATE jarvis_mission_steps SET last_transition_result = ? WHERE step_id = ?",
                (json.dumps(result_dict), step_id),
            )

    return result_dict


def cancel_step(step_id, mission_id, user_id, reason=None, idempotency_key=None) -> dict:
    get_mission(mission_id, user_id)  # user-isolation check
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM jarvis_mission_steps WHERE step_id = ? AND mission_id = ?",
            (step_id, mission_id),
        ).fetchone()
        if row is None:
            raise StepNotFoundError(step_id, mission_id)

        if row["status"] == "CANCELLED":
            return _row_to_step(row)
        if row["status"] in TERMINAL_STEP_STATUSES:
            raise InvalidStateTransitionError("MissionStep", step_id, row["status"], "CANCELLED", mission_id=mission_id, step_id=step_id)

        version = row["version"]
        now = _now()
        error_json = json.dumps({"code": "STEP_CANCELLED", "category": "USER", "reason": reason}) if reason else row["error"]

        cur = conn.execute("""
            UPDATE jarvis_mission_steps
            SET status = 'CANCELLED', version = version + 1, updated_at = ?,
                completed_at = ?, error = ?, last_idempotency_key = ?
            WHERE step_id = ? AND mission_id = ? AND version = ?
        """, (now, now, error_json, idempotency_key, step_id, mission_id, version))

        if cur.rowcount == 0:
            raise StateConflictError("MissionStep", step_id, mission_id=mission_id, step_id=step_id)

        updated = conn.execute("SELECT * FROM jarvis_mission_steps WHERE step_id = ?", (step_id,)).fetchone()
    return _row_to_step(updated)


def advance_ready_steps(mission_id, user_id) -> list:
    """Move every PENDING step whose dependencies are all SUCCEEDED into
    READY. Read-only in scope of *deciding what to run* - it does not run
    anything (no Worker/Supervisor exists yet); it only makes dependency-
    satisfied steps visible as READY so a future Supervisor can pick them
    up. Returns the list of steps that were advanced."""
    steps = list_steps(mission_id, user_id)
    by_id = {s["step_id"]: s for s in steps}
    advanced = []
    for step in steps:
        if step["status"] != "PENDING":
            continue
        deps = step["dependencies"]
        if all(by_id.get(d, {}).get("status") == "SUCCEEDED" for d in deps):
            advanced.append(transition_step(step["step_id"], mission_id, user_id, "READY"))
    return advanced


# ---------------------------------------------------------------------------
# Restart recovery
# ---------------------------------------------------------------------------

def reconcile_interrupted(user_id=None) -> dict:
    """Sweep every mission/step left in a non-terminal 'in flight' status
    from a prior process. Per spec Section 12/83: an interrupted EXECUTING
    mission's actual outcome is UNKNOWN, not FAILED and not COMPLETED - so
    this moves them to BLOCKED with verification_state=UNKNOWN and a
    structured error explaining why, rather than guessing either way.

    Call this once at process/session startup, before anything else reads
    mission state. Idempotent: running it twice in a row with nothing new
    interrupted is a no-op (BLOCKED is not itself an interruptible status,
    so a second sweep finds nothing left to reconcile)."""
    reconciled = {"missions": [], "steps": []}
    with _connect() as conn:
        if user_id:
            mission_rows = conn.execute(
                "SELECT mission_id, user_id FROM jarvis_missions WHERE user_id = ? AND status IN ({})".format(
                    ",".join("?" * len(INTERRUPTIBLE_MISSION_STATUSES))
                ),
                (user_id, *INTERRUPTIBLE_MISSION_STATUSES),
            ).fetchall()
        else:
            mission_rows = conn.execute(
                "SELECT mission_id, user_id FROM jarvis_missions WHERE status IN ({})".format(
                    ",".join("?" * len(INTERRUPTIBLE_MISSION_STATUSES))
                ),
                tuple(INTERRUPTIBLE_MISSION_STATUSES),
            ).fetchall()

        step_rows = conn.execute(
            "SELECT step_id, mission_id FROM jarvis_mission_steps WHERE status IN ({})".format(
                ",".join("?" * len(INTERRUPTIBLE_STEP_STATUSES))
            ),
            tuple(INTERRUPTIBLE_STEP_STATUSES),
        ).fetchall()

    interruption_note = {
        "code": "MISSION_INTERRUPTED", "category": "STATE", "severity": "WARNING",
        "message": "Process restarted while this was in flight. The outcome of any "
                   "external action attempted before the restart is UNKNOWN and has "
                   "not been assumed to be either success or failure - reconcile "
                   "manually before resuming.",
    }

    for row in mission_rows:
        mid, uid = row["mission_id"], row["user_id"]
        with _connect() as conn:
            r = conn.execute("SELECT version FROM jarvis_missions WHERE mission_id = ?", (mid,)).fetchone()
            if r is None:
                continue
            now = _now()
            conn.execute("""
                UPDATE jarvis_missions
                SET status = 'BLOCKED', version = version + 1, updated_at = ?,
                    verification_state = 'UNKNOWN', error = ?
                WHERE mission_id = ? AND version = ?
            """, (now, json.dumps(interruption_note), mid, r["version"]))
        reconciled["missions"].append(mid)

    for row in step_rows:
        sid, mid = row["step_id"], row["mission_id"]
        with _connect() as conn:
            r = conn.execute("SELECT version FROM jarvis_mission_steps WHERE step_id = ?", (sid,)).fetchone()
            if r is None:
                continue
            now = _now()
            conn.execute("""
                UPDATE jarvis_mission_steps
                SET status = 'BLOCKED', version = version + 1, updated_at = ?,
                    verification = ?, error = ?
                WHERE step_id = ? AND version = ?
            """, (now, json.dumps({"verification_state": "UNKNOWN"}), json.dumps(interruption_note), sid, r["version"]))
        reconciled["steps"].append(sid)

    return reconciled


# ---------------------------------------------------------------------------
# CLI (same style as memory.py / context.py)
# ---------------------------------------------------------------------------

def _print(obj):
    print(json.dumps(obj, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="JARVIS Mission/MissionStep state store")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init")

    p = sub.add_parser("create-mission")
    p.add_argument("--user", required=True)
    p.add_argument("--goal", required=True)
    p.add_argument("--risk-level")

    p = sub.add_parser("get-mission")
    p.add_argument("--user", required=True)
    p.add_argument("--mission-id", required=True)

    p = sub.add_parser("list-missions")
    p.add_argument("--user", required=True)
    p.add_argument("--status")

    p = sub.add_parser("transition-mission")
    p.add_argument("--user", required=True)
    p.add_argument("--mission-id", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--idempotency-key")

    p = sub.add_parser("cancel-mission")
    p.add_argument("--user", required=True)
    p.add_argument("--mission-id", required=True)
    p.add_argument("--reason")

    p = sub.add_parser("create-step")
    p.add_argument("--user", required=True)
    p.add_argument("--mission-id", required=True)
    p.add_argument("--description", required=True)

    p = sub.add_parser("list-steps")
    p.add_argument("--user", required=True)
    p.add_argument("--mission-id", required=True)

    p = sub.add_parser("reconcile")
    p.add_argument("--user")

    args = parser.parse_args()

    if args.command == "init":
        init_db()
        print("initialized")
    elif args.command == "create-mission":
        _print(create_mission(args.user, args.goal, risk_level=args.risk_level))
    elif args.command == "get-mission":
        _print(get_mission(args.mission_id, args.user))
    elif args.command == "list-missions":
        _print(list_missions(args.user, status=args.status))
    elif args.command == "transition-mission":
        _print(transition_mission(args.mission_id, args.user, args.to, idempotency_key=args.idempotency_key))
    elif args.command == "cancel-mission":
        _print(cancel_mission(args.mission_id, args.user, reason=args.reason))
    elif args.command == "create-step":
        _print(create_step(args.mission_id, args.user, args.description))
    elif args.command == "list-steps":
        _print(list_steps(args.mission_id, args.user))
    elif args.command == "reconcile":
        _print(reconcile_interrupted(user_id=args.user))


if __name__ == "__main__":
    main()
