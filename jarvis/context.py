#!/usr/bin/env python3
"""
JARVIS Context Assembly Engine — Phase 3.

Per the 2026-09-07 redirect: the point of this file is to stop Jarvis
behaving like "a collection of skills that can remember things" and start
behaving like "one intelligence that understands the user's current
situation before deciding what to do." `assemble_context()` is the one
function every skill should call before acting on anything non-trivial —
it's the concrete implementation of "skills must query the graph before
acting, not merely write to it afterward."

## Sources this draws from, and why each is separate (per the redirect)
  - jarvis_memory (structured DB)     -> authoritative facts about what's
                                          known, via memory.recall()
  - jarvis_memory_edges (knowledge graph) -> relationships, via
                                          memory.traverse()
  - entity_aliases (entity resolution) -> "Mom"/"Mummy"/etc. resolved to a
                                          canonical entity, via
                                          memory.resolve_entity() — EXPLICIT
                                          matches only, never a guess
  - jarvis_events (event store)        -> what changed and when; this file
                                          doesn't read it directly, but
                                          memory.py's mutations all write to
                                          it automatically, which is what
                                          makes the "trail" in this file's
                                          output explainable after the fact
  - Vector/semantic memory             -> NOT built (needs an embeddings key
                                          that isn't configured). recall()'s
                                          query matching is keyword-only.
                                          Not faked here — the trail says so
                                          when a query was used.
  - Conversation memory                -> NOT built. No conversation-history
                                          store exists yet; this engine has
                                          no access to "what was said in a
                                          previous chat" beyond what was
                                          explicitly `remember()`-ed from it.

This file decides what gets assembled; the underlying stores stay separate,
per the explicit "don't make the knowledge graph the only source of truth"
instruction. Nothing here talks to the CRM backend directly — a caller that
wants live CRM facts (a deal's current stage, a contact's phone number)
still calls the CRM API itself, the way every existing skill already does;
this engine's job is JARVIS's OWN memory/graph, not a proxy for the CRM.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memory as jm  # noqa: E402


def assemble_context(
    context: str,
    mission: str,
    mentions: list[str] | None = None,
    entity_refs: list[tuple[str, int]] | None = None,
    query: str | None = None,
    budget: int = 15,
    max_hops: int = 2,
) -> dict:
    """
    context:     privacy boundary this assembly happens under — 'private' |
                 'personal' | 'family' | 'business'. Every memory and every
                 related-entity lookup below is filtered through this; see
                 memory.py's ALLOWED_PRIVACY_FOR_CONTEXT for the actual
                 enforcement. This is the hard boundary from Phase 2, kept
                 exactly as-is per the explicit instruction not to weaken it.
    mission:     a human-readable description of what's being attempted
                 (e.g. "prepare for tomorrow's meeting with Raj") — recorded
                 in the trail so the final "why did Jarvis suggest this" is
                 answerable without re-deriving it.
    mentions:    raw text references to resolve via entity_aliases (e.g.
                 ["Raj"]). Anything that doesn't resolve is reported in
                 unresolved_mentions, never silently dropped or guessed at.
    entity_refs: already-known (entity_type, entity_id) pairs to seed
                 traversal/recall from directly, bypassing resolution.
    query:       optional keyword filter passed to recall() (see its
                 docstring — this is NOT semantic search today).
    budget:      max total items (memories + related entities combined)
                 returned. Prevents "dump the entire Life Brain into every
                 prompt" — everything included has an explicit reason in
                 the trail, and truncated=True is set honestly when the
                 budget actually cut something.
    max_hops:    how far to traverse the knowledge graph from each seed
                 entity.
    """
    if context not in jm.ALLOWED_PRIVACY_FOR_CONTEXT:
        raise ValueError(f"context must be one of {sorted(jm.ALLOWED_PRIVACY_FOR_CONTEXT)}, got {context!r}")

    trail: list[str] = [f"Mission: {mission}"]
    resolved_entities: list[dict] = []
    unresolved_mentions: list[str] = []
    seeds: list[tuple[str, int]] = list(entity_refs or [])

    # --- Entity resolution ---
    for mention in (mentions or []):
        matches = jm.resolve_entity(mention)
        if matches:
            for m in matches:
                resolved_entities.append(m)
                seeds.append((m["entity_type"], m["entity_id"]))
            trail.append(
                f"Resolved '{mention}' -> {', '.join(f'{m['entity_type']}:{m['entity_id']}' for m in matches)}"
                + (" (ambiguous — multiple entities share this alias)" if len(matches) > 1 else "")
            )
        else:
            unresolved_mentions.append(mention)
            trail.append(f"'{mention}' has no registered alias — not guessing which entity this refers to")

    seeds = list(dict.fromkeys(seeds))  # dedupe, preserve order

    # --- Recall: memories directly about each seed entity, plus a general query pass ---
    all_memories: list[dict] = []
    seen_memory_ids: set[int] = set()

    def _add_memories(results: list[dict], reason: str):
        for r in results:
            if r["id"] in seen_memory_ids:
                continue
            seen_memory_ids.add(r["id"])
            r["_included_because"] = reason
            all_memories.append(r)

    for etype, eid in seeds:
        results = jm.recall(context=context, entity_type=etype, entity_id=eid, limit=budget)
        if results:
            _add_memories(results, f"about {etype}:{eid}")

    if query:
        results = jm.recall(context=context, query=query, limit=budget)
        _add_memories(results, f"matched query {query!r}")
        trail.append(f"Keyword search for {query!r} (not semantic — see module docstring)")

    if not seeds and not query:
        trail.append("No entities or query given — recall skipped (nothing to scope it to)")

    # --- Knowledge graph traversal from each seed ---
    all_related: list[dict] = []
    seen_related: set[tuple[str, int]] = set(seeds)
    for etype, eid in seeds:
        hops = jm.traverse(etype, eid, max_hops=max_hops)
        new_hops = [h for h in hops if (h["entity_type"], h["entity_id"]) not in seen_related]
        for h in new_hops:
            seen_related.add((h["entity_type"], h["entity_id"]))
            h["_seed"] = f"{etype}:{eid}"
        all_related.extend(new_hops)
        if new_hops:
            trail.append(f"Traversed graph from {etype}:{eid} -> {len(new_hops)} connected entities within {max_hops} hops")

    # --- Conflict detection on every seed entity ---
    conflicts = []
    for etype, eid in seeds:
        found = jm.detect_conflicts(etype, eid, context=context)
        if found:
            conflicts.extend(found)
            trail.append(
                f"CONFLICT on {etype}:{eid}: " +
                "; ".join(f"fact_key={c['fact_key']} has {len(c['conflicting_memories'])} disagreeing values" for c in found)
            )

    # --- Context budget: rank and truncate rather than dumping everything ---
    all_memories.sort(key=lambda r: r.get("_score", 0), reverse=True)
    all_related.sort(key=lambda h: h["hops"])  # closer first

    memory_budget = max(1, int(budget * 0.7)) if budget else len(all_memories)
    related_budget = max(0, budget - min(len(all_memories), memory_budget)) if budget else len(all_related)

    included_memories = all_memories[:memory_budget]
    included_related = all_related[:related_budget]
    truncated = (len(all_memories) > len(included_memories)) or (len(all_related) > len(included_related))

    if truncated:
        trail.append(
            f"Budget ({budget}) cut results: showing {len(included_memories)}/{len(all_memories)} memories, "
            f"{len(included_related)}/{len(all_related)} related entities — suppressed the lowest-ranked, not random"
        )

    for m in included_memories:
        trail.append(f"Included memory #{m['id']} ({m['confidence_label']}) — {m['_included_because']}")

    return {
        "mission": mission,
        "context": context,
        "resolved_entities": resolved_entities,
        "unresolved_mentions": unresolved_mentions,
        "memories": included_memories,
        "related_entities": included_related,
        "conflicts": conflicts,
        "truncated": truncated,
        "trail": trail,
    }


def _cli():
    parser = argparse.ArgumentParser(description="JARVIS Context Assembly Engine")
    parser.add_argument("--context", required=True, choices=sorted(jm.ALLOWED_PRIVACY_FOR_CONTEXT))
    parser.add_argument("--mission", required=True)
    parser.add_argument("--mention", action="append", dest="mentions", default=[])
    parser.add_argument("--entity", action="append", dest="entity_refs_raw", default=[],
                         help="type:id, repeatable, e.g. --entity contact:101")
    parser.add_argument("--query")
    parser.add_argument("--budget", type=int, default=15)
    parser.add_argument("--max-hops", type=int, default=2)
    args = parser.parse_args()

    entity_refs = []
    for raw in args.entity_refs_raw:
        etype, _, eid = raw.partition(":")
        entity_refs.append((etype, int(eid)))

    jm.init_db()
    result = assemble_context(
        context=args.context, mission=args.mission, mentions=args.mentions,
        entity_refs=entity_refs, query=args.query, budget=args.budget, max_hops=args.max_hops,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    sys.exit(_cli() or 0)
