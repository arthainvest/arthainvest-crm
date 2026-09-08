#!/usr/bin/env python3
"""
JARVIS Recovery Engine — Stage G:

    FAILURE -> CLASSIFY -> RECOVER -> RETRY / FALLBACK / REPLAN / WAIT / ESCALATE -> VERIFY

Deterministic, not an LLM loop. Every decision in this file is a function
of structured facts already sitting in Stage B/D/E/F's own data - error
category/code/retryable/severity, attempt_count vs max_attempts, worker
availability (Stage D's registry), dependency state (Stage B's graph),
verification evidence (Stage F), and mission/step status. No model call
happens anywhere in this file, and it stays true to jarvis/'s standing
zero-network-import guarantee like every other stage.

## Execution boundary (read this before changing recover_step())

Recovery Engine never executes a tool and never dispatches a worker
itself - it only ever RECLASSIFIES and RE-ARMS the ledger:

    FAILED step, RETRY decided  -> missions.reopen_failed_step_for_recovery()
                                    (FAILED -> READY, same worker_id)
    FAILED step, FALLBACK decided -> same function, with a different
                                    worker_id (an explicitly registered
                                    fallback capability - never invented)
    BLOCKED mission -> EXECUTING  (a step became runnable again)
    BLOCKED mission -> PLANNING   (REPLANNING decided - a deterministic
                                    hand-off request, not an LLM call
                                    made from inside this file)

The actual re-execution happens the same way it always has: the
Supervisor (Stage E) picks up the now-READY step on its next scheduling
pass, through Worker Runtime (Stage D), through the same policy checks
every step has always gone through. Recovery Engine adds no second
execution path.

## The transaction boundary, restated for this file specifically

TRANSACTION_PROHIBITED is checked FIRST, before every other rule, and
short-circuits straight to RECOVERY_FAILED with no fallback/replan/
escalation attempted - not because those paths were checked and failed,
but because this file never even considers them for this error code.
This file does not import backend/policy.py or re-scan any text for
transaction patterns - it only ever reads the `error.code` a prior stage
already classified (Stage D's workers.py, which does own the pattern
scan). One source of truth, never duplicated here.

## What this stage does NOT do
No LLM planner call - REPLANNING only produces a structured request
object a human/skill can hand to jarvis/planner.py later (Stage C).
No automatic infinite retry - attempts_remaining is checked from Stage
B's own max_attempts field, never re-derived or overridden here.
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
import workers  # noqa: E402

DB_PATH = Path(__file__).resolve().parent / "jarvis.db"

RECOVERY_STATUSES = {
    "NOT_REQUIRED", "ANALYZING", "RETRYING", "FALLING_BACK", "REPLANNING",
    "WAITING_FOR_USER", "ESCALATING", "RECOVERED", "RECOVERY_FAILED",
}

# Error categories that are never worth blindly retrying even when a
# generic `retryable` flag might say otherwise on a given ErrorObject -
# a deliberate, conservative allow-list rather than trusting `retryable`
# alone for the categories where "don't retry" is a security property,
# not just an efficiency one.
_NEVER_RETRY_CATEGORIES = {"POLICY", "AUTHORIZATION", "VALIDATION", "SECURITY", "PRIVACY"}
_RECOVERABLE_VIA_HUMAN_CATEGORIES = {"AUTHENTICATION"}

# The step statuses Recovery Engine can act on. A SUCCEEDED step whose
# later verification contradicts it is handled separately (see
# classify()'s verification_conflict flag) - it is never reopened, only
# ever escalated, since Stage B's SUCCEEDED status is immutable by design.
_RECOVERABLE_STEP_STATUSES = {"FAILED", "BLOCKED"}


def _now():
    return datetime.now(timezone.utc).isoformat()


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
    step_id: str = None
    metadata: dict = field(default_factory=dict)
    error_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=_now)

    def to_dict(self):
        return asdict(self)


class RecoveryError(Exception):
    def __init__(self, error: ErrorObject):
        self.error = error
        super().__init__(error.message)


class StepNotRecoverableError(RecoveryError):
    def __init__(self, step_id, status):
        super().__init__(ErrorObject(
            code="RECOVERY_UNAVAILABLE", category="RECOVERY", step_id=step_id,
            message=f"Step {step_id!r} is {status!r} - only FAILED/BLOCKED steps (or a SUCCEEDED step "
                    "with contradictory verification evidence) can be considered for recovery.",
        ))


class RecoveryNotFoundError(RecoveryError):
    def __init__(self, recovery_id):
        super().__init__(ErrorObject(code="RECOVERY_NOT_FOUND", category="RECOVERY",
                                      message=f"No recovery attempt {recovery_id!r}."))


# ---------------------------------------------------------------------------
# Recovery attempt record
# ---------------------------------------------------------------------------

@dataclass
class RecoveryAttempt:
    recovery_id: str
    mission_id: str
    step_id: str
    status: str            # one of RECOVERY_STATUSES
    decision: str           # RETRY | FALLBACK | REPLAN | WAIT | ESCALATE | NONE
    classification: dict
    reasoning: str
    attempt_number: int
    created_at: str
    resolved_at: str = None

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
            CREATE TABLE IF NOT EXISTS jarvis_recovery_attempts (
                recovery_id TEXT PRIMARY KEY,
                mission_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                status TEXT NOT NULL,
                decision TEXT NOT NULL,
                classification TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                attempt_number INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                resolved_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_recovery_step ON jarvis_recovery_attempts(step_id)")


def _row_to_attempt(row) -> RecoveryAttempt:
    return RecoveryAttempt(
        recovery_id=row["recovery_id"], mission_id=row["mission_id"], step_id=row["step_id"],
        status=row["status"], decision=row["decision"], classification=json.loads(row["classification"]),
        reasoning=row["reasoning"], attempt_number=row["attempt_number"],
        created_at=row["created_at"], resolved_at=row["resolved_at"],
    )


def _persist(attempt: RecoveryAttempt):
    with _connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO jarvis_recovery_attempts
                (recovery_id, mission_id, step_id, status, decision, classification,
                 reasoning, attempt_number, created_at, resolved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (attempt.recovery_id, attempt.mission_id, attempt.step_id, attempt.status, attempt.decision,
              json.dumps(attempt.classification), attempt.reasoning, attempt.attempt_number,
              attempt.created_at, attempt.resolved_at))


def get_recovery_attempt(recovery_id: str) -> RecoveryAttempt:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jarvis_recovery_attempts WHERE recovery_id = ?", (recovery_id,)).fetchone()
    if row is None:
        raise RecoveryNotFoundError(recovery_id)
    return _row_to_attempt(row)


def list_recovery_attempts_for_step(step_id: str) -> list:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM jarvis_recovery_attempts WHERE step_id = ? ORDER BY created_at ASC", (step_id,)
        ).fetchall()
    return [_row_to_attempt(r) for r in rows]


# ---------------------------------------------------------------------------
# Classify: gather structured facts, decide nothing yet
# ---------------------------------------------------------------------------

def classify(mission_id: str, step_id: str, user_id: str, registry: workers.WorkerRegistry = None,
             fallback_map: dict = None) -> dict:
    """Pure and read-only - never mutates anything. Every field here is an
    already-known fact from an earlier stage, not a new judgment call."""
    registry = registry or workers.DEFAULT_REGISTRY
    fallback_map = fallback_map or {}

    mission = msn.get_mission(mission_id, user_id)
    step = msn.get_step(step_id, mission_id, user_id)
    error = step.get("error") or {}
    verification = step.get("verification") or {}

    dependency_blocked_on = None
    if step.get("dependencies"):
        all_steps = {s["step_id"]: s for s in msn.list_steps(mission_id, user_id)}
        for dep_id in step["dependencies"]:
            dep = all_steps.get(dep_id)
            if dep and dep["status"] not in ("SUCCEEDED", "PARTIALLY_SUCCEEDED") and dep["status"] in msn.TERMINAL_STEP_STATUSES:
                dependency_blocked_on = dep_id
                break

    worker_id = step.get("worker_id")
    worker_available = bool(registry.find_workers_for_capability(worker_id)) if worker_id else False
    fallback_candidates = fallback_map.get(worker_id, [])
    available_fallback = next(
        (cap for cap in fallback_candidates if registry.find_workers_for_capability(cap)), None
    )

    unknown_outcome = (
        step["status"] == "BLOCKED" and verification.get("verification_state") == "UNKNOWN"
    ) or mission.get("verification_state") == "UNKNOWN"

    verification_conflict = (
        step["status"] in ("SUCCEEDED", "PARTIALLY_SUCCEEDED") and verification.get("status") == "FAILED"
    )

    return {
        "mission_status": mission["status"],
        "step_status": step["status"],
        "cancelled": mission["status"] == "CANCELLED" or step["status"] == "CANCELLED",
        "error_code": error.get("code"),
        "error_category": error.get("category"),
        "error_retryable": error.get("retryable", False),
        "error_severity": error.get("severity"),
        "attempt_count": step.get("attempt_count", 0),
        "max_attempts": step.get("max_attempts", 0),
        "attempts_remaining": max(0, step.get("max_attempts", 0) - step.get("attempt_count", 0)),
        "worker_id": worker_id,
        "worker_available": worker_available,
        "available_fallback": available_fallback,
        "dependency_blocked_on": dependency_blocked_on,
        "unknown_outcome": unknown_outcome,
        "verification_conflict": verification_conflict,
        "verification": verification or None,
    }


# ---------------------------------------------------------------------------
# Decide: pure function from classification -> (status, decision, reasoning)
# ---------------------------------------------------------------------------

def _decide(c: dict):
    if c["cancelled"]:
        return "NOT_REQUIRED", "NONE", "mission or step is CANCELLED - cancellation wins over recovery, nothing restarts"

    if c["error_code"] == "TRANSACTION_PROHIBITED":
        return "RECOVERY_FAILED", "NONE", (
            "TRANSACTION_PROHIBITED is a permanent policy boundary - no retry, no fallback, no replan, "
            "no escalation-as-bypass. This is terminal by design, not by exhaustion of other options."
        )

    if c["verification_conflict"]:
        return "ESCALATING", "ESCALATE", (
            "the step reported success, but independently gathered verification evidence contradicts it - "
            "a SUCCEEDED step is immutable in this architecture and cannot be reopened, so this requires "
            "human review, not an automatic retry"
        )

    if c["unknown_outcome"]:
        return "WAITING_FOR_USER", "WAIT", (
            "the outcome of a prior attempt is UNKNOWN (interrupted mid-flight, per Stage B's restart "
            "reconciliation) - the action may or may not have actually happened externally, so it is never "
            "repeated automatically; this requires reconciliation/verification first"
        )

    if c["dependency_blocked_on"]:
        return "ESCALATING", "ESCALATE", (
            f"this step's dependency {c['dependency_blocked_on']!r} did not succeed and is itself terminal - "
            "retrying this step is pointless until the dependency is recovered first"
        )

    if c["error_code"] == "TOOL_NOT_FOUND":
        # Worker availability is re-checked fresh against the registry
        # right now (classify() already did this), independent of whatever
        # `retryable` flag was stored when the failure originally happened -
        # a missing worker is a resource-availability fact, not a fixed
        # property of the error, so it gets its own branch ahead of the
        # generic retryable/non-retryable split below.
        if c["worker_available"]:
            return "RETRYING", "RETRY", "the previously-missing worker capability is now registered and available - retrying"
        if c["available_fallback"]:
            return "FALLING_BACK", "FALLBACK", (
                f"the required worker capability is still unavailable, but an explicitly registered "
                f"fallback {c['available_fallback']!r} is available"
            )
        return "WAITING_FOR_USER", "WAIT", (
            "the required worker capability is still not registered anywhere - waiting for one to "
            "become available rather than retrying against a capability that does not exist"
        )

    if c["step_status"] not in _RECOVERABLE_STEP_STATUSES:
        return "NOT_REQUIRED", "NONE", f"step is {c['step_status']!r}, not FAILED/BLOCKED - nothing to recover"

    non_retryable = (not c["error_retryable"]) or (c["error_category"] in _NEVER_RETRY_CATEGORIES)
    if non_retryable:
        if c["error_category"] in _RECOVERABLE_VIA_HUMAN_CATEGORIES:
            return "WAITING_FOR_USER", "WAIT", (
                f"error category {c['error_category']!r} is not something recovery can fix by retrying "
                "(e.g. an expired credential) - a human needs to intervene before anything can proceed"
            )
        if c["available_fallback"]:
            return "FALLING_BACK", "FALLBACK", (
                f"error category {c['error_category']!r}/code {c['error_code']!r} is non-retryable, but an "
                f"explicitly registered fallback capability {c['available_fallback']!r} is available"
            )
        return "RECOVERY_FAILED", "NONE", (
            f"error category {c['error_category']!r}/code {c['error_code']!r} is non-retryable and no "
            "fallback is registered - recovery cannot proceed on its own"
        )

    # From here, the error IS retryable and not in a never-retry category.
    if c["attempts_remaining"] > 0 and c["worker_available"]:
        return "RETRYING", "RETRY", (
            f"error is retryable ({c['attempts_remaining']} attempt(s) remaining) and the required worker "
            "is currently available - re-arming the same step for another attempt"
        )

    if c["attempts_remaining"] > 0 and not c["worker_available"]:
        if c["available_fallback"]:
            return "FALLING_BACK", "FALLBACK", (
                f"the required worker is currently unavailable, but an explicitly registered fallback "
                f"capability {c['available_fallback']!r} is available"
            )
        return "WAITING_FOR_USER", "WAIT", (
            "the required worker is currently unavailable and no fallback is registered - waiting rather "
            "than retrying against a capability that does not exist"
        )

    # attempts_remaining == 0: max attempts exhausted.
    if c["available_fallback"]:
        return "FALLING_BACK", "FALLBACK", (
            "max attempts exhausted on the original worker, but an explicitly registered fallback "
            f"capability {c['available_fallback']!r} is available and has not been tried yet"
        )

    return "REPLANNING", "REPLAN", (
        "max attempts exhausted and no fallback is registered - a deterministic replan hand-off is the "
        "only remaining path; this does not call the Planner automatically, it only requests one"
    )


# ---------------------------------------------------------------------------
# Act: apply the decision to the ledger (never to a tool directly)
# ---------------------------------------------------------------------------

def _act(mission_id, step_id, user_id, status, decision, classification, idempotency_key):
    if decision == "RETRY":
        msn.reopen_failed_step_for_recovery(step_id, mission_id, user_id, idempotency_key=idempotency_key)
        _resume_mission_if_blocked(mission_id, user_id)
    elif decision == "FALLBACK":
        msn.reopen_failed_step_for_recovery(step_id, mission_id, user_id,
                                             new_worker_id=classification["available_fallback"],
                                             idempotency_key=idempotency_key)
        _resume_mission_if_blocked(mission_id, user_id)
    elif decision == "REPLAN":
        request_replan(mission_id, step_id, user_id, classification)
    # WAIT / ESCALATE / NONE: no ledger mutation - see module docstring.


def _resume_mission_if_blocked(mission_id, user_id):
    mission = msn.get_mission(mission_id, user_id)
    if mission["status"] == "BLOCKED":
        msn.transition_mission(mission_id, user_id, "EXECUTING")


def request_replan(mission_id: str, step_id: str, user_id: str, classification: dict) -> dict:
    """Deterministic hand-off, per spec Section 5: this does NOT call
    jarvis/planner.py or any LLM - it only produces a structured request
    and (if the mission is currently BLOCKED) moves the mission to
    PLANNING, a transition Stage B's own state machine already allows.
    A human or a skill is expected to actually call planner.propose_replan()
    with this request as context - Recovery Engine's job stops at handing
    it off."""
    mission = msn.get_mission(mission_id, user_id)
    if mission["status"] == "BLOCKED":
        mission = msn.transition_mission(mission_id, user_id, "PLANNING")
    return {
        "mission_id": mission_id,
        "step_id": step_id,
        "reason": "max_attempts_exhausted_no_fallback",
        "classification": classification,
        "mission_status_after_handoff": mission["status"],
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def recover_step(mission_id: str, step_id: str, user_id: str, *, registry: workers.WorkerRegistry = None,
                  fallback_map: dict = None, recovery_id: str = None) -> RecoveryAttempt:
    """Idempotent: replaying the same recovery_id returns the exact
    recorded attempt without re-classifying or re-acting - restart-safe
    by construction, same pattern as every other stage's idempotency_key."""
    if recovery_id:
        with _connect() as conn:
            row = conn.execute("SELECT * FROM jarvis_recovery_attempts WHERE recovery_id = ?", (recovery_id,)).fetchone()
        if row is not None:
            return _row_to_attempt(row)

    recovery_id = recovery_id or str(uuid4())
    created_at = _now()

    classification = classify(mission_id, step_id, user_id, registry=registry, fallback_map=fallback_map)
    status, decision, reasoning = _decide(classification)

    step = msn.get_step(step_id, mission_id, user_id)

    _act(mission_id, step_id, user_id, status, decision, classification, recovery_id)

    attempt = RecoveryAttempt(
        recovery_id=recovery_id, mission_id=mission_id, step_id=step_id, status=status, decision=decision,
        classification=classification, reasoning=reasoning, attempt_number=step.get("attempt_count", 0),
        created_at=created_at,
        resolved_at=created_at if status in ("NOT_REQUIRED", "RECOVERY_FAILED", "ESCALATING", "WAITING_FOR_USER") else None,
    )
    _persist(attempt)
    return attempt


def check_recovery_outcome(recovery_id: str, mission_id: str, step_id: str, user_id: str) -> RecoveryAttempt:
    """Observational follow-up, per the RETRYING/FALLING_BACK -> RECOVERED/
    RECOVERY_FAILED lifecycle: call this after the Supervisor has had a
    chance to re-dispatch a re-armed step. Never re-triggers anything
    itself - purely reads the step's current status and updates the
    recorded attempt's final state."""
    attempt = get_recovery_attempt(recovery_id)
    if attempt.status not in ("RETRYING", "FALLING_BACK"):
        return attempt  # already resolved or never actionable - nothing to check

    step = msn.get_step(step_id, mission_id, user_id)
    if step["status"] in ("SUCCEEDED", "PARTIALLY_SUCCEEDED"):
        attempt.status = "RECOVERED"
        attempt.resolved_at = _now()
    elif step["status"] in ("FAILED", "BLOCKED"):
        attempt.status = "RECOVERY_FAILED"
        attempt.resolved_at = _now()
    # else still RUNNING/READY/etc - genuinely still in progress, leave as-is.

    _persist(attempt)
    return attempt
