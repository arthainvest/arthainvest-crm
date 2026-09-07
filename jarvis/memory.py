#!/usr/bin/env python3
"""
JARVIS Context Engine — the memory + knowledge-graph foundation.

Per the strategic redirect on this project (2026-09-07): this is not "add a
memory feature" — it's the foundation everything else (planning, proactive
intelligence, agents, automation) is meant to build on. Scoped realistically
for what a solo operator's Claude-Code-skills system actually needs today,
architected so the pieces the redirect asked for that aren't built yet
(vector/semantic search) can slot in later without a rewrite.

Deliberately a SEPARATE SQLite file (jarvis/jarvis.db), not inside the CRM's
arthainvest_crm.db — JARVIS sits above the CRM (see
JARVIS_ARCHITECTURE_ASSESSMENT.md §28), and this way a bug in JARVIS's own
memory can never corrupt or lock the live CRM database.

## What's implemented now (hybrid retrieval, minus the vector part)
  - Structured DB filtering (memory_type, entity, privacy context)
  - Knowledge graph (jarvis_memory_edges — simple typed edges, traversable;
    not a dedicated graph database, but the relational-edges pattern scales
    fine at this data volume and needs no new infrastructure)
  - Recency + importance + confidence ranking
  - Freshness/staleness: a memory past its expires_at, or never reconfirmed
    in a long time relative to its importance, is downgraded in ranking and
    flagged in the result, not silently treated as equally true as a fact
    confirmed yesterday
  - Privacy boundaries: five tiers (private, personal, family_shared,
    business, public), enforced by context at recall time

## What's NOT implemented yet (by design, not by accident)
  - True semantic/vector similarity search — needs an embeddings API key
    (OPENAI_API_KEY exists as a field in backend/.env but is currently
    empty). `recall()`'s `query` matching today is a simple case-insensitive
    substring/keyword match, not semantic. The function signature and
    ranking pipeline are structured so a `_semantic_score()` step can be
    inserted alongside the existing structured/graph/recency scoring once a
    real embedding backend is configured — see the TODO in `recall()`.
  - A dedicated graph database — the edges table is a relational
    approximation, sufficient for the entity counts this business actually
    has (dozens to low hundreds of contacts/deals/projects, not millions).
"""

import argparse
import json
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "jarvis.db"

VALID_MEMORY_TYPES = {
    "identity", "business", "client", "episodic", "semantic",
    "task", "decision", "investment",
}

VALID_PRIVACY_LEVELS = {"private", "personal", "family_shared", "business", "public"}

# Which privacy levels are visible when recalling in a given context.
# "private" is deliberately visible ONLY in the "private" context itself -
# not a superset of anything else - so a private memory can never leak into
# a business or family conversation just because someone asks broadly.
ALLOWED_PRIVACY_FOR_CONTEXT = {
    "private": {"private", "public"},
    "personal": {"personal", "family_shared", "public"},
    "family": {"family_shared", "public"},
    "business": {"business", "public"},
}

# How long (in days) a memory of a given importance can go without being
# reconfirmed before it's considered stale and downgraded in ranking. Higher
# importance = allowed to stay "fresh" longer without reconfirmation (a core
# identity fact doesn't need daily reconfirming; a casual preference does).
STALENESS_DAYS_BY_IMPORTANCE = {1: 14, 2: 30, 3: 90, 4: 180, 5: 365}


@contextmanager
def _connect():
    """Connection as a proper context manager: commits on clean exit, rolls
    back on exception, and always closes the underlying connection.

    `sqlite3.Connection` used directly as `with conn:` only wraps the
    transaction (commit/rollback) — it does NOT close the connection. Left
    that way, connections pile up unclosed and, on Windows specifically,
    keep an OS-level file lock held until garbage collection eventually
    closes them — which broke `tempfile.TemporaryDirectory()` cleanup in
    the test suite (PermissionError: file in use) the first time this was
    actually run. Explicit `close()` in `finally` fixes both that and the
    general connection-leak risk in long-running use (e.g. a skill calling
    this repeatedly in one session)."""
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


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS jarvis_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                fact_key TEXT,
                source TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 1.0,
                importance INTEGER NOT NULL DEFAULT 3,
                privacy_level TEXT NOT NULL DEFAULT 'business',
                created_at TEXT NOT NULL,
                last_confirmed TEXT NOT NULL,
                expires_at TEXT,
                deleted_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_jarvis_memory_type ON jarvis_memory(memory_type);
            CREATE INDEX IF NOT EXISTS idx_jarvis_memory_entity ON jarvis_memory(entity_type, entity_id);
            CREATE INDEX IF NOT EXISTS idx_jarvis_memory_privacy ON jarvis_memory(privacy_level);
            CREATE INDEX IF NOT EXISTS idx_jarvis_memory_fact_key ON jarvis_memory(fact_key);

            CREATE TABLE IF NOT EXISTS jarvis_memory_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_type TEXT NOT NULL,
                from_id INTEGER NOT NULL,
                relation TEXT NOT NULL,
                to_type TEXT NOT NULL,
                to_id INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_edges_from ON jarvis_memory_edges(from_type, from_id);
            CREATE INDEX IF NOT EXISTS idx_edges_to ON jarvis_memory_edges(to_type, to_id);

            -- Event store (Phase 3): an append-only log of what changed and
            -- when, independent of the current state in jarvis_memory. This
            -- is what makes "why did Jarvis think that" answerable later —
            -- jarvis_memory tells you what's currently believed, this tells
            -- you the history of how that belief was built.
            CREATE TABLE IF NOT EXISTS jarvis_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,      -- remember | confirm | correct | forget | link
                memory_id INTEGER,
                edge_id INTEGER,
                detail TEXT,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_events_created ON jarvis_events(created_at);

            -- Entity resolution (Phase 3): EXPLICIT aliases only — "Mom"
            -- resolves to a contact only if someone has actually registered
            -- that alias, never a guessed fuzzy match. Consistent with this
            -- project's standing "never fill a gap with a plausible guess."
            CREATE TABLE IF NOT EXISTS entity_aliases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alias_text TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                confidence REAL NOT NULL DEFAULT 1.0,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_aliases_text ON entity_aliases(alias_text);
            """
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------
# Core operations
# --------------------------------------------------------------------------

def _log_event(conn, event_type: str, memory_id: int | None = None,
                edge_id: int | None = None, detail: str | None = None) -> None:
    """Internal: append to the event store. Called automatically by every
    mutating operation below — the audit trail is not something a caller can
    forget to write, it happens as a side effect of the mutation itself."""
    conn.execute(
        "INSERT INTO jarvis_events (event_type, memory_id, edge_id, detail, created_at) VALUES (?, ?, ?, ?, ?)",
        (event_type, memory_id, edge_id, detail, _now_iso()),
    )


def remember(
    memory_type: str,
    content: str,
    source: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    confidence: float = 1.0,
    importance: int = 3,
    privacy_level: str = "business",
    expires_at: str | None = None,
    fact_key: str | None = None,
) -> int:
    """
    fact_key: optional. Set this when the memory asserts a specific, single-
    valued fact that could later be contradicted (e.g. "meeting_time:raj:
    2026-09-08") — this is what lets detect_conflicts() mechanically notice
    two different values for the same fact-slot, rather than needing to
    understand natural language well enough to know two sentences are about
    the same thing. Leave it unset for memories that don't represent a
    single-valued fact (most episodic/semantic memories don't need one).
    """
    if memory_type not in VALID_MEMORY_TYPES:
        raise ValueError(f"memory_type must be one of {sorted(VALID_MEMORY_TYPES)}, got {memory_type!r}")
    if privacy_level not in VALID_PRIVACY_LEVELS:
        raise ValueError(f"privacy_level must be one of {sorted(VALID_PRIVACY_LEVELS)}, got {privacy_level!r}")
    if not (1 <= importance <= 5):
        raise ValueError(f"importance must be 1-5, got {importance}")
    if not source:
        raise ValueError("source is required — every memory must say where it came from")

    now = _now_iso()
    with _connect() as conn:
        cursor = conn.execute(
            """INSERT INTO jarvis_memory
               (memory_type, content, entity_type, entity_id, fact_key, source, confidence,
                importance, privacy_level, created_at, last_confirmed, expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (memory_type, content, entity_type, entity_id, fact_key, source, confidence,
             importance, privacy_level, now, now, expires_at),
        )
        memory_id = cursor.lastrowid
        _log_event(conn, "remember", memory_id=memory_id, detail=content[:200])
        return memory_id


def confirm(memory_id: int) -> None:
    """Mark a memory as reconfirmed right now — resets its staleness clock
    without changing its content. Use when the same fact comes up again and
    is still true, rather than creating a duplicate row."""
    with _connect() as conn:
        conn.execute(
            "UPDATE jarvis_memory SET last_confirmed = ? WHERE id = ? AND deleted_at IS NULL",
            (_now_iso(), memory_id),
        )
        _log_event(conn, "confirm", memory_id=memory_id)


def correct(memory_id: int, new_content: str, source: str) -> int:
    """Update a memory's content (e.g. a preference changed) while keeping
    its history — the old content isn't destroyed, a new row records the
    correction, and the old row is soft-deleted with a pointer to why.
    Returns the new memory's id."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jarvis_memory WHERE id = ?", (memory_id,)).fetchone()
        if not row:
            raise ValueError(f"no memory with id {memory_id}")
        now = _now_iso()
        conn.execute(
            "UPDATE jarvis_memory SET deleted_at = ? WHERE id = ?",
            (f"corrected:{now}", memory_id),
        )
        cursor = conn.execute(
            """INSERT INTO jarvis_memory
               (memory_type, content, entity_type, entity_id, fact_key, source, confidence,
                importance, privacy_level, created_at, last_confirmed, expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (row["memory_type"], new_content, row["entity_type"], row["entity_id"], row["fact_key"], source,
             row["confidence"], row["importance"], row["privacy_level"], now, now, row["expires_at"]),
        )
        new_id = cursor.lastrowid
        _log_event(conn, "correct", memory_id=new_id, detail=f"superseded id={memory_id}: {new_content[:180]}")
        return new_id


def forget(memory_id: int) -> bool:
    """Soft-delete: the memory stops being recalled, but the row isn't
    physically destroyed (matches this project's standing 'never delete
    anything, only report/quarantine' policy — applied here as 'soft-delete,
    never hard-delete'). Returns True if a live memory was found and forgotten."""
    with _connect() as conn:
        cursor = conn.execute(
            "UPDATE jarvis_memory SET deleted_at = ? WHERE id = ? AND deleted_at IS NULL",
            (_now_iso(), memory_id),
        )
        forgotten = cursor.rowcount > 0
        if forgotten:
            _log_event(conn, "forget", memory_id=memory_id)
        return forgotten


def link(from_type: str, from_id: int, relation: str, to_type: str, to_id: int) -> int:
    """Create a knowledge-graph edge, e.g. link('contact', 12, 'has_deal', 'deal', 44)."""
    with _connect() as conn:
        cursor = conn.execute(
            """INSERT INTO jarvis_memory_edges (from_type, from_id, relation, to_type, to_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (from_type, from_id, relation, to_type, to_id, _now_iso()),
        )
        edge_id = cursor.lastrowid
        _log_event(conn, "link", edge_id=edge_id,
                    detail=f"{from_type}:{from_id} -[{relation}]-> {to_type}:{to_id}")
        return edge_id


def related(entity_type: str, entity_id: int) -> list[dict]:
    """Traverse the knowledge graph in both directions from one entity — the
    building block for context-aware requests like 'move tomorrow's meeting'
    needing to know who else is involved, what deadlines are linked, etc.
    before acting. Single hop — see traverse() for multi-hop."""
    with _connect() as conn:
        outgoing = conn.execute(
            "SELECT relation, to_type as other_type, to_id as other_id, 'outgoing' as direction "
            "FROM jarvis_memory_edges WHERE from_type = ? AND from_id = ?",
            (entity_type, entity_id),
        ).fetchall()
        incoming = conn.execute(
            "SELECT relation, from_type as other_type, from_id as other_id, 'incoming' as direction "
            "FROM jarvis_memory_edges WHERE to_type = ? AND to_id = ?",
            (entity_type, entity_id),
        ).fetchall()
        return [dict(r) for r in list(outgoing) + list(incoming)]


def traverse(entity_type: str, entity_id: int, max_hops: int = 3) -> list[dict]:
    """Multi-hop breadth-first traversal — the actual building block for
    'Raj -> Company -> Project -> previous meetings -> commitments ->
    documents -> pending tasks'. Returns every entity reachable within
    max_hops, each tagged with how many hops away it is and the path of
    relations that reached it (first path found, since this is BFS).
    Cycle-safe: never revisits an entity already reached at a shorter hop
    count."""
    start = (entity_type, entity_id)
    visited = {start: []}
    frontier = [start]
    results = []

    for hop in range(1, max_hops + 1):
        next_frontier = []
        for etype, eid in frontier:
            for edge in related(etype, eid):
                other = (edge["other_type"], edge["other_id"])
                if other in visited:
                    continue
                path = visited[(etype, eid)] + [{"relation": edge["relation"], "direction": edge["direction"]}]
                visited[other] = path
                next_frontier.append(other)
                results.append({
                    "entity_type": other[0],
                    "entity_id": other[1],
                    "hops": hop,
                    "path": path,
                })
        frontier = next_frontier
        if not frontier:
            break

    return results


# --------------------------------------------------------------------------
# Entity resolution (Phase 3) — explicit aliases only, never a fuzzy guess
# --------------------------------------------------------------------------

def register_alias(alias_text: str, entity_type: str, entity_id: int,
                    source: str, confidence: float = 1.0) -> int:
    """Register that some text ('Mom', 'Mummy', a WhatsApp display name)
    refers to a specific entity. This is the ONLY way resolve_entity() will
    ever match that text to that entity — there is no fuzzy/ML matching
    here, on purpose. If it isn't registered, it isn't resolved."""
    with _connect() as conn:
        cursor = conn.execute(
            """INSERT INTO entity_aliases (alias_text, entity_type, entity_id, confidence, source, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (alias_text, entity_type, entity_id, confidence, source, _now_iso()),
        )
        return cursor.lastrowid


def resolve_entity(text: str) -> list[dict]:
    """Case-insensitive exact match against registered aliases. Returns ALL
    matching entities (there can legitimately be more than one — two people
    who both get called 'Raj' by different sources) rather than silently
    picking one; the caller decides how to disambiguate (e.g. by which
    context/domain is asking). Returns an empty list, not a guess, if
    nothing was ever registered for this text."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM entity_aliases WHERE LOWER(alias_text) = LOWER(?)",
            (text,),
        ).fetchall()
        return [dict(r) for r in rows]


# --------------------------------------------------------------------------
# Conflict detection (Phase 3)
# --------------------------------------------------------------------------

def detect_conflicts(entity_type: str, entity_id: int, context: str) -> list[dict]:
    """Groups ACTIVE (non-deleted) memories about one entity by fact_key.
    Any fact_key with more than one distinct content value among currently-
    active memories is a real, structural conflict — e.g. two different
    'meeting_time:raj:2026-09-08' assertions that were never reconciled via
    correct(). Memories with no fact_key are never flagged (they're not
    asserting a single-valued fact, so there's nothing to conflict). Only
    considers memories visible in the given context (privacy-respecting,
    same as recall())."""
    if context not in ALLOWED_PRIVACY_FOR_CONTEXT:
        raise ValueError(f"context must be one of {sorted(ALLOWED_PRIVACY_FOR_CONTEXT)}, got {context!r}")
    allowed_privacy = ALLOWED_PRIVACY_FOR_CONTEXT[context]

    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM jarvis_memory WHERE deleted_at IS NULL AND entity_type = ? AND entity_id = ? "
            "AND fact_key IS NOT NULL AND privacy_level IN ({})".format(
                ",".join("?" for _ in allowed_privacy)
            ),
            (entity_type, entity_id, *allowed_privacy),
        ).fetchall()

    by_fact_key: dict[str, list[dict]] = {}
    for row in rows:
        by_fact_key.setdefault(row["fact_key"], []).append(dict(row))

    conflicts = []
    for fact_key, memories in by_fact_key.items():
        distinct_contents = {m["content"] for m in memories}
        if len(distinct_contents) > 1:
            conflicts.append({"fact_key": fact_key, "conflicting_memories": memories})
    return conflicts


def confidence_label(stale: bool, confidence: float) -> str:
    """One of 'known' | 'probably_true' | 'stale' — the per-memory piece of
    the Phase 3 confidence taxonomy (known/probably_true/stale/conflicting/
    unknown). 'conflicting' and 'unknown' aren't properties of a single
    memory row — they're properties of a *query result* (conflicting = two
    active memories disagree, from detect_conflicts(); unknown = recall()
    found nothing at all) — assembled at the Context Engine layer, not here."""
    if stale:
        return "stale"
    if confidence >= 0.8:
        return "known"
    return "probably_true"


def _is_stale(row: sqlite3.Row, now: datetime) -> bool:
    if row["expires_at"]:
        try:
            expires = datetime.fromisoformat(row["expires_at"])
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if now >= expires:
                return True
        except ValueError:
            pass
    last_confirmed = datetime.fromisoformat(row["last_confirmed"])
    if last_confirmed.tzinfo is None:
        last_confirmed = last_confirmed.replace(tzinfo=timezone.utc)
    max_age_days = STALENESS_DAYS_BY_IMPORTANCE.get(row["importance"], 30)
    return (now - last_confirmed) > timedelta(days=max_age_days)


def recall(
    context: str,
    query: str | None = None,
    memory_type: str | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    include_stale: bool = True,
    limit: int = 10,
) -> list[dict]:
    """
    context: which privacy boundary is asking — 'private' | 'personal' |
             'family' | 'business'. Determines which privacy_level rows are
             even eligible to be returned (see ALLOWED_PRIVACY_FOR_CONTEXT) —
             this is the enforcement point that stops a private memory from
             leaking into a business or family-shared conversation.
    query:   plain keyword/substring match against content today. TODO once
             an embeddings key is configured: add a semantic similarity pass
             here (embed `query`, cosine-similarity against stored content
             embeddings, blend into the ranking below alongside recency/
             importance/confidence) rather than replacing this — keyword
             match stays a useful exact-match signal even after that lands.
    """
    if context not in ALLOWED_PRIVACY_FOR_CONTEXT:
        raise ValueError(f"context must be one of {sorted(ALLOWED_PRIVACY_FOR_CONTEXT)}, got {context!r}")

    allowed_privacy = ALLOWED_PRIVACY_FOR_CONTEXT[context]
    now = datetime.now(timezone.utc)

    sql = "SELECT * FROM jarvis_memory WHERE deleted_at IS NULL AND privacy_level IN ({})".format(
        ",".join("?" for _ in allowed_privacy)
    )
    params: list = list(allowed_privacy)

    if memory_type:
        sql += " AND memory_type = ?"
        params.append(memory_type)
    if entity_type:
        sql += " AND entity_type = ?"
        params.append(entity_type)
    if entity_id is not None:
        sql += " AND entity_id = ?"
        params.append(entity_id)
    if query:
        sql += " AND content LIKE ?"
        params.append(f"%{query}%")

    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    results = []
    for row in rows:
        stale = _is_stale(row, now)
        if stale and not include_stale:
            continue
        last_confirmed = datetime.fromisoformat(row["last_confirmed"])
        if last_confirmed.tzinfo is None:
            last_confirmed = last_confirmed.replace(tzinfo=timezone.utc)
        recency_days = (now - last_confirmed).days
        # Ranking: importance and confidence dominate; recency is a tiebreaker
        # (more recent = slightly higher); staleness directly penalizes score
        # rather than just being a boolean flag, so a stale-but-important
        # memory still surfaces (with the flag) rather than disappearing.
        score = (row["importance"] * 2) + (row["confidence"] * 3) - (recency_days * 0.01)
        if stale:
            score -= 5
        results.append({
            "id": row["id"],
            "memory_type": row["memory_type"],
            "content": row["content"],
            "entity_type": row["entity_type"],
            "entity_id": row["entity_id"],
            "fact_key": row["fact_key"],
            "source": row["source"],
            "confidence": row["confidence"],
            "confidence_label": confidence_label(stale, row["confidence"]),
            "importance": row["importance"],
            "privacy_level": row["privacy_level"],
            "created_at": row["created_at"],
            "last_confirmed": row["last_confirmed"],
            "expires_at": row["expires_at"],
            "stale": stale,
            "_score": score,
        })

    results.sort(key=lambda r: r["_score"], reverse=True)
    return results[:limit]


# --------------------------------------------------------------------------
# CLI — so skills can call this via Bash without a Python import
# --------------------------------------------------------------------------

def _cli():
    parser = argparse.ArgumentParser(description="JARVIS Context Engine — memory + knowledge graph")
    sub = parser.add_subparsers(dest="command", required=True)

    p_remember = sub.add_parser("remember")
    p_remember.add_argument("--type", required=True, dest="memory_type", choices=sorted(VALID_MEMORY_TYPES))
    p_remember.add_argument("--content", required=True)
    p_remember.add_argument("--source", required=True)
    p_remember.add_argument("--entity-type")
    p_remember.add_argument("--entity-id", type=int)
    p_remember.add_argument("--confidence", type=float, default=1.0)
    p_remember.add_argument("--importance", type=int, default=3)
    p_remember.add_argument("--privacy", dest="privacy_level", default="business", choices=sorted(VALID_PRIVACY_LEVELS))
    p_remember.add_argument("--expires-at")
    p_remember.add_argument("--fact-key", help="set this when asserting a single-valued fact that could later conflict (e.g. meeting_time:raj:2026-09-08)")

    p_recall = sub.add_parser("recall")
    p_recall.add_argument("--context", required=True, choices=sorted(ALLOWED_PRIVACY_FOR_CONTEXT))
    p_recall.add_argument("--query")
    p_recall.add_argument("--type", dest="memory_type", choices=sorted(VALID_MEMORY_TYPES))
    p_recall.add_argument("--entity-type")
    p_recall.add_argument("--entity-id", type=int)
    p_recall.add_argument("--limit", type=int, default=10)
    p_recall.add_argument("--exclude-stale", action="store_true")

    p_forget = sub.add_parser("forget")
    p_forget.add_argument("--id", required=True, type=int, dest="memory_id")

    p_confirm = sub.add_parser("confirm")
    p_confirm.add_argument("--id", required=True, type=int, dest="memory_id")

    p_correct = sub.add_parser("correct")
    p_correct.add_argument("--id", required=True, type=int, dest="memory_id")
    p_correct.add_argument("--content", required=True)
    p_correct.add_argument("--source", required=True)

    p_link = sub.add_parser("link")
    p_link.add_argument("--from-type", required=True)
    p_link.add_argument("--from-id", required=True, type=int)
    p_link.add_argument("--relation", required=True)
    p_link.add_argument("--to-type", required=True)
    p_link.add_argument("--to-id", required=True, type=int)

    p_related = sub.add_parser("related")
    p_related.add_argument("--entity-type", required=True)
    p_related.add_argument("--entity-id", required=True, type=int)

    p_traverse = sub.add_parser("traverse")
    p_traverse.add_argument("--entity-type", required=True)
    p_traverse.add_argument("--entity-id", required=True, type=int)
    p_traverse.add_argument("--max-hops", type=int, default=3)

    p_alias = sub.add_parser("register-alias")
    p_alias.add_argument("--alias", required=True, dest="alias_text")
    p_alias.add_argument("--entity-type", required=True)
    p_alias.add_argument("--entity-id", required=True, type=int)
    p_alias.add_argument("--source", required=True)
    p_alias.add_argument("--confidence", type=float, default=1.0)

    p_resolve = sub.add_parser("resolve")
    p_resolve.add_argument("--text", required=True)

    p_conflicts = sub.add_parser("conflicts")
    p_conflicts.add_argument("--entity-type", required=True)
    p_conflicts.add_argument("--entity-id", required=True, type=int)
    p_conflicts.add_argument("--context", required=True, choices=sorted(ALLOWED_PRIVACY_FOR_CONTEXT))

    p_events = sub.add_parser("events")
    p_events.add_argument("--limit", type=int, default=20)

    sub.add_parser("init")

    args = parser.parse_args()
    init_db()

    if args.command == "init":
        print(f"jarvis.db ready at {DB_PATH}")
    elif args.command == "remember":
        mid = remember(args.memory_type, args.content, args.source, args.entity_type,
                        args.entity_id, args.confidence, args.importance,
                        args.privacy_level, args.expires_at, args.fact_key)
        print(json.dumps({"id": mid}))
    elif args.command == "recall":
        results = recall(args.context, args.query, args.memory_type, args.entity_type,
                          args.entity_id, include_stale=not args.exclude_stale, limit=args.limit)
        print(json.dumps(results, indent=2))
    elif args.command == "forget":
        ok = forget(args.memory_id)
        print(json.dumps({"forgotten": ok}))
    elif args.command == "confirm":
        confirm(args.memory_id)
        print(json.dumps({"confirmed": True}))
    elif args.command == "correct":
        new_id = correct(args.memory_id, args.content, args.source)
        print(json.dumps({"corrected": True, "new_id": new_id}))
    elif args.command == "link":
        eid = link(args.from_type, args.from_id, args.relation, args.to_type, args.to_id)
        print(json.dumps({"edge_id": eid}))
    elif args.command == "related":
        print(json.dumps(related(args.entity_type, args.entity_id), indent=2))
    elif args.command == "traverse":
        print(json.dumps(traverse(args.entity_type, args.entity_id, args.max_hops), indent=2))
    elif args.command == "register-alias":
        aid = register_alias(args.alias_text, args.entity_type, args.entity_id, args.source, args.confidence)
        print(json.dumps({"alias_id": aid}))
    elif args.command == "resolve":
        print(json.dumps(resolve_entity(args.text), indent=2))
    elif args.command == "conflicts":
        print(json.dumps(detect_conflicts(args.entity_type, args.entity_id, args.context), indent=2))
    elif args.command == "events":
        with _connect() as conn:
            rows = conn.execute(
                "SELECT * FROM jarvis_events ORDER BY created_at DESC LIMIT ?", (args.limit,)
            ).fetchall()
        print(json.dumps([dict(r) for r in rows], indent=2))


if __name__ == "__main__":
    sys.exit(_cli() or 0)
