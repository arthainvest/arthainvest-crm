#!/usr/bin/env python3
"""
JARVIS Proactive Intelligence — Stage N.

    EVENTS + MEMORY + CONTEXT + MISSIONS + SCHEDULES -> SIGNAL -> PRIORITY -> PROPOSAL

This stage never executes anything. It only ever produces PROPOSALS — a
human or a future, separately-authorized caller decides whether to act on
one, and if they do, that action still has to pass through the full
existing pipeline (INTENT LOCK -> PERMISSION -> PRIVACY -> POLICY ->
SECURITY -> RISK -> APPROVAL -> ACTION FIREWALL -> WORKER RUNTIME)
unaffected by anything in this file. Accepting a proposal here is a status
flag, not an execution trigger — there is no code path in this module that
calls workers.py, approval.py, or action_firewall.py.

## Reuse, not reinvention (same discipline as every prior stage)
  - MEMORY: `memory.recall()` / `memory.detect_conflicts()` / the
    `jarvis_events` table it already maintains — this module adds zero new
    memory storage or a second privacy matrix. Context/privacy filtering
    reuses `memory.ALLOWED_PRIVACY_FOR_CONTEXT` directly.
  - MISSIONS: `missions.list_missions()` for stalled-mission signals — no
    new mission state, no new user-isolation model (same "wrong user id ->
    indistinguishable from not-found" guarantee).
  - POLICY: `backend/policy.py`'s `find_prohibited_routes()` is reused to
    scan every proposal's own text for the same permanently-prohibited
    financial-transaction patterns the CRM's own startup check enforces —
    a proposal is refused outright (fails closed, `TransactionProhibitedError`)
    if its title/explanation matches, whether that text came from a
    deterministic template or from untrusted memory content. This is the
    concrete enforcement of "financial transactions remain absolutely
    prohibited" at this layer, not a second policy invented from scratch.
  - SCHEDULES is new in this stage (no prior stage owns recurring
    obligations) — a deliberately narrow table: a cadence and a next-due
    timestamp, nothing else. `register_schedule()`/`mark_schedule_fired()`
    are the only two ways to touch it, both user-isolated exactly like
    missions.py.

## Untrusted content / prompt-injection defense
A memory's `content` can come from any source recorded via `memory.py`,
including something captured from outside this system. That content is
NEVER parsed, evaluated, or treated as an instruction here — it only ever
becomes opaque display text inside a Proposal's `title`/`explanation`
fields, and that text is itself passed through the same
`find_prohibited_routes()` check as everything else before the proposal is
allowed to exist. A memory whose content reads like a request to move
$10000 to another account therefore cannot smuggle a transaction-shaped
suggestion through this layer — see `test_proactive.py`'s injection tests
for the proof.

## What this stage explicitly does NOT do
Does not call any Worker, tool, external API, or network library — grep
this file for `requests`/`httpx`/`workers.execute` and find nothing; that
absence is itself part of the "no autonomous external side effects" and
"no fake live integrations" guarantees, not just an assertion in prose.
Does not grant, escalate, or bypass any permission — `accept_proposal()`
only ever flips a status column.
"""

import hashlib
import sqlite3
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))

import memory as mem  # noqa: E402
import missions as msn  # noqa: E402

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))
import policy as backend_policy  # noqa: E402 - reused, not reimplemented (see module docstring)

DB_PATH = Path(__file__).resolve().parent / "jarvis.db"

SIGNAL_TYPES = {
    "deadline_overdue", "follow_up_due", "fact_changed",
    "recurring_obligation", "anomaly_conflict", "suggestion", "stalled_mission",
}
URGENCY_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
_URGENCY_WEIGHT = {"LOW": 1.0, "MEDIUM": 2.0, "HIGH": 3.0, "CRITICAL": 5.0}
PROPOSAL_STATUSES = {"PENDING", "ACCEPTED", "DISMISSED", "EXPIRED"}
TERMINAL_PROPOSAL_STATUSES = {"DISMISSED", "EXPIRED"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _now_dt():
    return datetime.now(timezone.utc)


def _parse_dt(s):
    d = datetime.fromisoformat(s)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d


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


class ProactiveError(Exception):
    def __init__(self, error: ErrorObject):
        self.error = error
        super().__init__(error.message)


class TransactionProhibitedError(ProactiveError):
    """Propagated, never downgraded — matches action_firewall.py's own rule
    that a transaction-shaped action is refused outright, not routed to
    approval, recovery, or a fallback."""
    def __init__(self, text):
        super().__init__(ErrorObject(
            code="TRANSACTION_PROHIBITED", category="SECURITY", severity="CRITICAL",
            message="Refusing to create a proposal whose text matches a permanently-prohibited "
                    "financial-transaction pattern (backend/policy.py). This is not a bug — "
                    "remove or reword the underlying signal, do not relax the pattern.",
            metadata={"text": text[:200]},
        ))


class MissingMetadataError(ProactiveError):
    def __init__(self, field_name):
        super().__init__(ErrorObject(
            code="MISSING_REQUIRED_METADATA", category="SECURITY",
            message=f"Refusing to proceed: required field {field_name!r} is missing or empty.",
            metadata={"field": field_name},
        ))


class ProposalNotFoundError(ProactiveError):
    def __init__(self, proposal_id, user_id):
        super().__init__(ErrorObject(
            code="PROPOSAL_NOT_FOUND", category="STATE",
            message=f"No proposal {proposal_id!r} for this user.",
            metadata={"user_id": user_id},
        ))


class InvalidProposalStateError(ProactiveError):
    def __init__(self, proposal_id, from_status, to_status):
        super().__init__(ErrorObject(
            code="INVALID_PROPOSAL_STATE", category="STATE",
            message=f"Cannot move proposal {proposal_id!r} from {from_status!r} to {to_status!r}.",
            metadata={"from_status": from_status, "to_status": to_status},
        ))


class ScheduleNotFoundError(ProactiveError):
    def __init__(self, schedule_id, user_id):
        super().__init__(ErrorObject(
            code="SCHEDULE_NOT_FOUND", category="STATE",
            message=f"No schedule {schedule_id!r} for this user.",
            metadata={"user_id": user_id},
        ))


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class Proposal:
    proposal_id: str
    user_id: str
    signal_type: str
    urgency: str
    confidence: float
    priority: float
    title: str
    explanation: str
    source_kind: str
    source_id: str
    dedupe_key: str
    status: str
    privacy_level: str
    created_at: str
    expires_at: str = None
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
    mem.DB_PATH = DB_PATH if mem.DB_PATH != DB_PATH else mem.DB_PATH
    msn.DB_PATH = DB_PATH if msn.DB_PATH != DB_PATH else msn.DB_PATH
    mem.init_db()
    msn.init_db()
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_proposals (
                proposal_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                urgency TEXT NOT NULL,
                confidence REAL NOT NULL,
                priority REAL NOT NULL,
                title TEXT NOT NULL,
                explanation TEXT NOT NULL,
                source_kind TEXT NOT NULL,
                source_id TEXT,
                dedupe_key TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                privacy_level TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                resolved_at TEXT
            )
        """)
        # Partial unique index: only one PENDING proposal per (user, signal) at
        # a time. This is a real DB-enforced concurrency guarantee, not just an
        # application-level check-then-insert race - a second concurrent scan
        # that tries to insert the same dedupe_key while one is already
        # PENDING gets a real IntegrityError, which _create_proposal() catches
        # and turns into "return the existing one" (true idempotency).
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_proposals_dedupe_pending
            ON jarvis_proposals(dedupe_key) WHERE status = 'PENDING'
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_proposals_user ON jarvis_proposals(user_id, status)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_schedules (
                schedule_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                schedule_key TEXT NOT NULL,
                description TEXT NOT NULL,
                cadence_days INTEGER NOT NULL,
                last_fired_at TEXT,
                next_due_at TEXT NOT NULL,
                privacy_level TEXT NOT NULL DEFAULT 'business',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_schedules_user_key ON jarvis_schedules(user_id, schedule_key)")


def _row_to_proposal(row) -> dict:
    return dict(row)


def _row_to_schedule(row) -> dict:
    return dict(row)


# ---------------------------------------------------------------------------
# Policy reuse: no proposal may ever look like a financial-transaction action
# ---------------------------------------------------------------------------

def _is_prohibited_text(text: str) -> bool:
    """Reuses backend/policy.py's own compiled patterns rather than a second
    list. find_prohibited_routes() is written for route *paths*, but its
    patterns are plain regexes over text - passing free text through the
    same function is a legitimate reuse of the identical prohibited-word
    list, not a reimplementation of it."""
    return bool(backend_policy.find_prohibited_routes([text or ""]))


def _assert_not_prohibited(*texts: str) -> None:
    for t in texts:
        if _is_prohibited_text(t):
            raise TransactionProhibitedError(t)


# ---------------------------------------------------------------------------
# Priority + dedupe
# ---------------------------------------------------------------------------

def _priority(confidence: float, urgency: str) -> float:
    return round(confidence * _URGENCY_WEIGHT[urgency], 4)


def _dedupe_key(user_id: str, signal_type: str, source_kind: str, source_id) -> str:
    combined = f"{user_id}|{signal_type}|{source_kind}|{source_id}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Proposal creation (idempotent, fails closed, policy-checked)
# ---------------------------------------------------------------------------

def _create_proposal(*, user_id, signal_type, urgency, confidence, title, explanation,
                      source_kind, source_id, privacy_level, expires_at=None) -> dict:
    if not user_id:
        raise MissingMetadataError("user_id")
    if signal_type not in SIGNAL_TYPES:
        raise MissingMetadataError("signal_type")
    if urgency not in URGENCY_LEVELS:
        raise MissingMetadataError("urgency")
    if privacy_level not in mem.VALID_PRIVACY_LEVELS:
        raise MissingMetadataError("privacy_level")
    if not title or not explanation:
        raise MissingMetadataError("title/explanation")

    # Every proposal must carry its own source and explanation - "no
    # proposal without an explanation/source" is enforced here, not left to
    # caller discipline.
    _assert_not_prohibited(title, explanation)

    dedupe_key = _dedupe_key(user_id, signal_type, source_kind, source_id)
    proposal_id = str(uuid4())
    now = _now()
    priority = _priority(confidence, urgency)

    with _connect() as conn:
        try:
            conn.execute(
                """INSERT INTO jarvis_proposals
                   (proposal_id, user_id, signal_type, urgency, confidence, priority, title,
                    explanation, source_kind, source_id, dedupe_key, status, privacy_level,
                    created_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?, ?)""",
                (proposal_id, user_id, signal_type, urgency, confidence, priority, title,
                 explanation, source_kind, str(source_id) if source_id is not None else None,
                 dedupe_key, privacy_level, now, expires_at),
            )
        except sqlite3.IntegrityError:
            # A PENDING proposal for this exact signal already exists - this
            # IS the deduplication/idempotency guarantee, enforced by the DB,
            # not just an app-level check that a race could slip past.
            row = conn.execute(
                "SELECT * FROM jarvis_proposals WHERE dedupe_key = ? AND status = 'PENDING'",
                (dedupe_key,),
            ).fetchone()
            return _row_to_proposal(row)

        row = conn.execute("SELECT * FROM jarvis_proposals WHERE proposal_id = ?", (proposal_id,)).fetchone()
        return _row_to_proposal(row)


# ---------------------------------------------------------------------------
# Schedules (recurring obligations) - new in this stage, deliberately narrow
# ---------------------------------------------------------------------------

def register_schedule(user_id: str, schedule_key: str, description: str, cadence_days: int,
                       privacy_level: str = "business", first_due_at: str = None) -> dict:
    if not user_id:
        raise MissingMetadataError("user_id")
    if not schedule_key:
        raise MissingMetadataError("schedule_key")
    if cadence_days <= 0:
        raise MissingMetadataError("cadence_days")
    if privacy_level not in mem.VALID_PRIVACY_LEVELS:
        raise MissingMetadataError("privacy_level")
    _assert_not_prohibited(description)

    now = _now()
    next_due = first_due_at or now
    with _connect() as conn:
        existing = conn.execute(
            "SELECT * FROM jarvis_schedules WHERE user_id = ? AND schedule_key = ?",
            (user_id, schedule_key),
        ).fetchone()
        if existing:
            # Re-registering updates the definition (description/cadence can
            # legitimately change) without resetting last_fired_at/next_due_at
            # history - a genuine update, not a duplicate.
            conn.execute(
                "UPDATE jarvis_schedules SET description = ?, cadence_days = ?, privacy_level = ? WHERE schedule_id = ?",
                (description, cadence_days, privacy_level, existing["schedule_id"]),
            )
            row = conn.execute("SELECT * FROM jarvis_schedules WHERE schedule_id = ?", (existing["schedule_id"],)).fetchone()
            return _row_to_schedule(row)

        schedule_id = str(uuid4())
        conn.execute(
            """INSERT INTO jarvis_schedules
               (schedule_id, user_id, schedule_key, description, cadence_days, last_fired_at,
                next_due_at, privacy_level, created_at)
               VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?)""",
            (schedule_id, user_id, schedule_key, description, cadence_days, next_due, privacy_level, now),
        )
        row = conn.execute("SELECT * FROM jarvis_schedules WHERE schedule_id = ?", (schedule_id,)).fetchone()
        return _row_to_schedule(row)


def list_schedules(user_id: str) -> list:
    if not user_id:
        raise MissingMetadataError("user_id")
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM jarvis_schedules WHERE user_id = ? ORDER BY next_due_at", (user_id,)).fetchall()
    return [_row_to_schedule(r) for r in rows]


def get_schedule(schedule_id: str, user_id: str) -> dict:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM jarvis_schedules WHERE schedule_id = ? AND user_id = ?", (schedule_id, user_id)
        ).fetchone()
    if not row:
        raise ScheduleNotFoundError(schedule_id, user_id)
    return _row_to_schedule(row)


def mark_schedule_fired(schedule_id: str, user_id: str) -> dict:
    """Advances the schedule's clock - call this once the recurring
    obligation has actually been handled (by a human, or by whatever the
    caller does after accepting the resulting proposal). Never called
    automatically by this module itself."""
    schedule = get_schedule(schedule_id, user_id)  # user-isolation check
    now_dt = _now_dt()
    next_due = (now_dt + timedelta(days=schedule["cadence_days"])).isoformat()
    with _connect() as conn:
        conn.execute(
            "UPDATE jarvis_schedules SET last_fired_at = ?, next_due_at = ? WHERE schedule_id = ? AND user_id = ?",
            (now_dt.isoformat(), next_due, schedule_id, user_id),
        )
        row = conn.execute("SELECT * FROM jarvis_schedules WHERE schedule_id = ?", (schedule_id,)).fetchone()
    return _row_to_schedule(row)


# ---------------------------------------------------------------------------
# Signal detectors - deterministic functions over EVENTS/MEMORY/MISSIONS/SCHEDULES
# ---------------------------------------------------------------------------

def _scan_deadline_overdue(user_id, context) -> list:
    """An active memory whose expires_at has passed is an overdue-deadline
    signal - reuses memory.recall()'s own staleness/expiry computation
    rather than re-deriving expiry logic here."""
    out = []
    for m in mem.recall(context, include_stale=True, limit=1000):
        if not m["expires_at"]:
            continue
        if _parse_dt(m["expires_at"]) >= _now_dt():
            continue
        urgency = "CRITICAL" if m["importance"] >= 5 else "HIGH"
        out.append(dict(
            signal_type="deadline_overdue", urgency=urgency, confidence=m["confidence"],
            title=f"Overdue: {m['content'][:80]}",
            explanation=f"Memory #{m['id']} ({m['memory_type']}) expired at {m['expires_at']} and is still active.",
            source_kind="memory", source_id=m["id"], privacy_level=m["privacy_level"],
        ))
    return out


def _scan_follow_ups(user_id, context) -> list:
    """A 'task' memory that has gone stale (per memory.py's own
    importance-scaled staleness window) without being reconfirmed is a
    follow-up-due signal."""
    out = []
    for m in mem.recall(context, memory_type="task", include_stale=True, limit=1000):
        if not m["stale"]:
            continue
        out.append(dict(
            signal_type="follow_up_due", urgency="MEDIUM", confidence=m["confidence"],
            title=f"Follow up: {m['content'][:80]}",
            explanation=f"Task memory #{m['id']} hasn't been reconfirmed since {m['last_confirmed']}.",
            source_kind="memory", source_id=m["id"], privacy_level=m["privacy_level"],
        ))
    return out


def _scan_fact_changes(user_id, context, since_days: int = 7) -> list:
    """A recent `correct` event (a fact whose value just changed) is a
    changes signal - reuses memory.py's own jarvis_events audit trail
    rather than a second change-tracking mechanism."""
    cutoff = (_now_dt() - timedelta(days=since_days)).isoformat()
    out = []
    with mem._connect() as conn:
        rows = conn.execute(
            "SELECT * FROM jarvis_events WHERE event_type = 'correct' AND created_at >= ? ORDER BY created_at DESC",
            (cutoff,),
        ).fetchall()
    for ev in rows:
        memory_row = mem.get_memory(ev["memory_id"])
        if not memory_row:
            continue
        allowed = mem.ALLOWED_PRIVACY_FOR_CONTEXT[context]
        if memory_row["privacy_level"] not in allowed:
            continue
        out.append(dict(
            signal_type="fact_changed", urgency="MEDIUM", confidence=memory_row["confidence"],
            title=f"Changed: {memory_row['content'][:80]}",
            explanation=f"Memory #{memory_row['id']} was corrected on {ev['created_at']}: {ev['detail'] or ''}"[:300],
            source_kind="event", source_id=ev["id"], privacy_level=memory_row["privacy_level"],
        ))
    return out


def _scan_recurring_obligations(user_id) -> list:
    out = []
    for s in list_schedules(user_id):
        if _parse_dt(s["next_due_at"]) > _now_dt():
            continue
        out.append(dict(
            signal_type="recurring_obligation", urgency="HIGH", confidence=1.0,
            title=f"Due: {s['description'][:80]}",
            explanation=f"Recurring obligation {s['schedule_key']!r} was due at {s['next_due_at']} "
                        f"(cadence {s['cadence_days']}d).",
            source_kind="schedule", source_id=s["schedule_id"], privacy_level=s["privacy_level"],
        ))
    return out


def _scan_anomalies(context) -> list:
    """Aggregate anomaly scan: for every (entity_type, entity_id) that has
    at least one fact_key'd memory, reuse memory.detect_conflicts() (the
    existing single-entity primitive) rather than building a second
    conflict-detection algorithm."""
    out = []
    with mem._connect() as conn:
        entities = conn.execute(
            "SELECT DISTINCT entity_type, entity_id FROM jarvis_memory "
            "WHERE deleted_at IS NULL AND fact_key IS NOT NULL AND entity_type IS NOT NULL AND entity_id IS NOT NULL"
        ).fetchall()
    for e in entities:
        for conflict in mem.detect_conflicts(e["entity_type"], e["entity_id"], context):
            memories = conflict["conflicting_memories"]
            worst_confidence = max(m["confidence"] for m in memories)
            source_id = f"{e['entity_type']}:{e['entity_id']}:{conflict['fact_key']}"
            out.append(dict(
                signal_type="anomaly_conflict", urgency="HIGH", confidence=worst_confidence,
                title=f"Conflicting facts about {conflict['fact_key']}",
                explanation=f"{len(memories)} active memories disagree on {conflict['fact_key']!r} "
                            f"for {e['entity_type']}#{e['entity_id']}.",
                source_kind="conflict", source_id=source_id, privacy_level=memories[0]["privacy_level"],
            ))
    return out


def _scan_suggestions(user_id, context) -> list:
    """Catch-all: an important, still-fresh memory nearing the end of its
    staleness window gets a gentle 'reconfirm soon' suggestion, distinct
    from deadline_overdue (which fires only after expiry)."""
    out = []
    now = _now_dt()
    for m in mem.recall(context, include_stale=False, limit=1000):
        if m["importance"] < 4:
            continue
        last_confirmed = _parse_dt(m["last_confirmed"])
        window_days = mem.STALENESS_DAYS_BY_IMPORTANCE.get(m["importance"], 30)
        age_days = (now - last_confirmed).days
        if age_days < window_days * 0.8:
            continue
        out.append(dict(
            signal_type="suggestion", urgency="LOW", confidence=m["confidence"],
            title=f"Reconfirm soon: {m['content'][:80]}",
            explanation=f"Memory #{m['id']} is approaching its staleness window ({age_days}/{window_days} days).",
            source_kind="memory", source_id=m["id"], privacy_level=m["privacy_level"],
        ))
    return out


def _scan_stalled_missions(user_id, stalled_after_days: int = 3) -> list:
    """A mission sitting in a non-terminal, non-active status for a long
    time is itself a proactive signal - reuses missions.list_missions()'s
    existing user isolation, adds no new mission state."""
    out = []
    cutoff = _now_dt() - timedelta(days=stalled_after_days)
    for mission in msn.list_missions(user_id):
        if mission["status"] in msn.TERMINAL_MISSION_STATUSES:
            continue
        if mission["status"] not in ("WAITING", "BLOCKED"):
            continue
        updated = mission.get("updated_at") or mission.get("created_at")
        if not updated or _parse_dt(updated) > cutoff:
            continue
        out.append(dict(
            signal_type="stalled_mission", urgency="MEDIUM", confidence=1.0,
            title=f"Stalled mission: {mission['goal'][:80]}",
            explanation=f"Mission {mission['mission_id']} has been {mission['status']} since {updated}.",
            source_kind="mission", source_id=mission["mission_id"], privacy_level="business",
        ))
    return out


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def generate_proposals(user_id: str, context: str) -> list:
    """Runs every detector, creates (or dedupes into) a Proposal for each
    candidate signal, and returns the full current PENDING set for this
    user/context sorted by priority descending. Safe to call repeatedly
    (e.g. on a timer) - repeated calls against an unchanged signal return
    the same proposal, never a duplicate."""
    if not user_id:
        raise MissingMetadataError("user_id")
    if context not in mem.ALLOWED_PRIVACY_FOR_CONTEXT:
        raise MissingMetadataError("context")

    candidates = []
    candidates += _scan_deadline_overdue(user_id, context)
    candidates += _scan_follow_ups(user_id, context)
    candidates += _scan_fact_changes(user_id, context)
    candidates += _scan_recurring_obligations(user_id)
    candidates += _scan_anomalies(context)
    candidates += _scan_suggestions(user_id, context)
    candidates += _scan_stalled_missions(user_id)

    created = []
    for c in candidates:
        proposal = _create_proposal(user_id=user_id, **c)
        created.append(proposal)

    created.sort(key=lambda p: p["priority"], reverse=True)
    return created


def list_proposals(user_id: str, status: str = None) -> list:
    if not user_id:
        raise MissingMetadataError("user_id")
    with _connect() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM jarvis_proposals WHERE user_id = ? AND status = ? ORDER BY priority DESC",
                (user_id, status),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM jarvis_proposals WHERE user_id = ? ORDER BY priority DESC", (user_id,)
            ).fetchall()
    return [_row_to_proposal(r) for r in rows]


def get_proposal(proposal_id: str, user_id: str) -> dict:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM jarvis_proposals WHERE proposal_id = ? AND user_id = ?", (proposal_id, user_id)
        ).fetchone()
    if not row:
        raise ProposalNotFoundError(proposal_id, user_id)
    return _row_to_proposal(row)


def accept_proposal(proposal_id: str, user_id: str) -> dict:
    """Flips status to ACCEPTED. This is the ENTIRE effect - no mission is
    created, no worker is invoked, no external call is made. Idempotent:
    accepting an already-ACCEPTED proposal is a no-op that returns it
    unchanged, since replaying the same acceptance is not a new decision."""
    current = get_proposal(proposal_id, user_id)
    if current["status"] == "ACCEPTED":
        return current
    if current["status"] in TERMINAL_PROPOSAL_STATUSES:
        raise InvalidProposalStateError(proposal_id, current["status"], "ACCEPTED")

    now = _now()
    with _connect() as conn:
        cursor = conn.execute(
            "UPDATE jarvis_proposals SET status = 'ACCEPTED', resolved_at = ? "
            "WHERE proposal_id = ? AND user_id = ? AND status = 'PENDING'",
            (now, proposal_id, user_id),
        )
        if cursor.rowcount == 0:
            # Lost a race with a concurrent transition - re-check rather than
            # assume success or silently overwrite.
            latest = get_proposal(proposal_id, user_id)
            if latest["status"] == "ACCEPTED":
                return latest
            raise InvalidProposalStateError(proposal_id, latest["status"], "ACCEPTED")
        row = conn.execute("SELECT * FROM jarvis_proposals WHERE proposal_id = ?", (proposal_id,)).fetchone()
    return _row_to_proposal(row)


def dismiss_proposal(proposal_id: str, user_id: str, reason: str = None) -> dict:
    """PENDING or ACCEPTED -> DISMISSED. Idempotent the same way as
    accept_proposal(). Freeing the dedupe_key's partial-unique slot means a
    genuinely new occurrence of the same signal can be proposed again later
    - dismissing does not permanently suppress it."""
    current = get_proposal(proposal_id, user_id)
    if current["status"] == "DISMISSED":
        return current
    if current["status"] == "EXPIRED":
        raise InvalidProposalStateError(proposal_id, current["status"], "DISMISSED")

    now = _now()
    with _connect() as conn:
        cursor = conn.execute(
            "UPDATE jarvis_proposals SET status = 'DISMISSED', resolved_at = ? "
            "WHERE proposal_id = ? AND user_id = ? AND status IN ('PENDING', 'ACCEPTED')",
            (now, proposal_id, user_id),
        )
        if cursor.rowcount == 0:
            latest = get_proposal(proposal_id, user_id)
            if latest["status"] == "DISMISSED":
                return latest
            raise InvalidProposalStateError(proposal_id, latest["status"], "DISMISSED")
        row = conn.execute("SELECT * FROM jarvis_proposals WHERE proposal_id = ?", (proposal_id,)).fetchone()
    return _row_to_proposal(row)


def expire_stale_proposals(user_id: str = None) -> dict:
    """Restart/persistence safety sweep: any PENDING proposal past its own
    expires_at is moved to EXPIRED. Never silently deletes a row (matches
    this project's standing soft-delete-only convention) and never assumes
    a proposal was acted on just because it expired unseen."""
    now = _now()
    with _connect() as conn:
        if user_id:
            cursor = conn.execute(
                "UPDATE jarvis_proposals SET status = 'EXPIRED', resolved_at = ? "
                "WHERE user_id = ? AND status = 'PENDING' AND expires_at IS NOT NULL AND expires_at < ?",
                (now, user_id, now),
            )
        else:
            cursor = conn.execute(
                "UPDATE jarvis_proposals SET status = 'EXPIRED', resolved_at = ? "
                "WHERE status = 'PENDING' AND expires_at IS NOT NULL AND expires_at < ?",
                (now, now),
            )
        expired_count = cursor.rowcount
    return {"expired": expired_count}
