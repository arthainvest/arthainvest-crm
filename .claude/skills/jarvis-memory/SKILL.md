---
name: jarvis-memory
description: The JARVIS Context Engine - save/recall/correct/forget facts, resolve entity aliases (Mom/Mummy/a contact), traverse the knowledge graph, detect conflicting facts, and assemble a complete situational picture before acting. This is the foundation the other skills and the jarvis orchestrator build on, not a user-facing report. Trigger phrases - "remember that...", "what do you remember about...", "forget that...", "jarvis, recall...", or invoked automatically by other skills via assemble_context before anything non-trivial.
---

# Jarvis Memory (Context Engine)

The implementation is two files, both stdlib-only Python (no dependencies), writing to a separate SQLite file (`jarvis/jarvis.db`) kept apart from the CRM's own `arthainvest_crm.db` on purpose, so a bug here can never touch live business data:

- `jarvis/memory.py` — the stores: memory (facts), the knowledge-graph edges, entity aliases, the event log. Called directly for simple save/recall/forget.
- `jarvis/context.py` — the **Context Assembly Engine** (Phase 3). This is what turns "a collection of skills that can remember things" into "one intelligence that understands the current situation before deciding what to do" — call `assemble_context` (below) before acting on anything non-trivial, rather than calling `recall`/`related` separately and hoping you remembered every relevant angle.

See both files' module docstrings for the full design reasoning (why five privacy tiers, why staleness is a downgrade not a deletion, which of the five context sources the redirect specified — structured DB / knowledge graph / vector memory / event store / conversation memory — are actually built vs. genuinely not yet). This file is the *usage* guide; those are the *design* docs.

## Before doing anything: which context is this?

Every `recall` needs a `--context`: `private`, `personal`, `family`, or `business`. **Get this right - it's the actual privacy enforcement, not a formality.** A `private`-tagged memory is invisible to every context except `private` itself; `business`-tagged memories never reach `personal`/`family` contexts and vice versa; `family_shared` reaches both `personal` and `family` but not `business`. If you're in a business conversation (CRM work, client questions, anything routed here from another CRM skill), the context is `business` - don't widen it "just in case" something relevant might be tagged personal.

## Saving something

```bash
python jarvis/memory.py remember \
  --type episodic \
  --content "Rahul said he'd send documents Monday" \
  --source "conversation 2026-09-07" \
  --entity-type contact --entity-id 101 \
  --importance 3 \
  --privacy business
```

`--type` is one of: `identity`, `business`, `client`, `episodic` (something that happened), `semantic` (a fact), `task`, `decision`, `investment`. `--source` is required - always say where this came from (which conversation, which document, who told you), never leave it vague. `--importance` (1-5) controls how long the memory stays "fresh" before needing reconfirmation (see `STALENESS_DAYS_BY_IMPORTANCE` in memory.py) - a core preference is a 4 or 5, a one-off remark is a 1 or 2. Default `--privacy` is `business`; only mark something `private` if it genuinely shouldn't surface anywhere else, ever.

If a fact changes (a preference shifted, a plan changed), use `correct --id <id> --content "..." --source "..."`, not a fresh `remember` - this keeps the old value's history instead of leaving two contradictory rows. If the same fact just came up again and is still true, use `confirm --id <id>` to reset its staleness clock without creating a duplicate.

## Recalling

```bash
python jarvis/memory.py recall --context business --query "Rahul" --entity-type contact --entity-id 101
```

Results come back ranked (importance + confidence + recency, staleness penalized) and each one says `"stale": true/false` explicitly - **don't present a stale memory as equally certain as a fresh one.** If something's flagged stale, say so ("last confirmed 4 months ago, might be outdated") rather than stating it flatly. Add `--exclude-stale` when staleness genuinely shouldn't count (e.g. "did they ever mention X" where even an old mention answers the question) vs. leaving it in when currency matters (e.g. "what's their current preference").

**Today's `--query` is keyword/substring matching, not semantic search** - it won't find a conceptually-related memory that doesn't share words with the query. Semantic search is planned (`jarvis/memory.py`'s `recall()` docstring has the exact TODO) but needs an embeddings API key that isn't configured yet. Don't claim to have searched "meaning" - if a keyword search plausibly missed something relevant, say that plainly rather than presenting an incomplete result as exhaustive.

## Forgetting

```bash
python jarvis/memory.py forget --id 42
```

Soft-delete only, per this project's standing "never delete anything" policy applied to memory specifically - the row stops being recalled but isn't physically destroyed. If someone asks Jarvis to forget something, actually run this - don't just silently omit it from a future answer while leaving it recallable.

## The knowledge graph

```bash
python jarvis/memory.py link --from-type meeting --from-id 500 --relation involves --to-type contact --to-id 101
python jarvis/memory.py related --entity-type meeting --entity-id 500          # one hop
python jarvis/memory.py traverse --entity-type contact --entity-id 7 --max-hops 3   # multi-hop BFS
```

`related` is one hop; `traverse` follows the chain outward (e.g. contact → company → project → task) up to `--max-hops`, tagging each result with how many hops away it is and the path of relations that reached it. Use this **before** acting on anything that implies cascading effects - "move tomorrow's meeting" shouldn't just find the meeting, it should traverse from it first to see who's involved, what task/deal it's linked to, and mention anything that moving it would affect, before confirming the move.

## Entity resolution - "Mom", "Mummy", and a CRM contact are the same person

```bash
python jarvis/memory.py register-alias --alias "Mom" --entity-type contact --entity-id 55 --source "user told me"
python jarvis/memory.py resolve --text "Mom"
```

**Explicit aliases only - never a fuzzy/guessed match.** If "Mom" was never registered, `resolve` returns an empty list, not a best guess. If someone refers to a person by a name/nickname you don't have an alias for, ask once ("who's Mom - Priya's mother, the contact you added last week?") and register it, rather than guessing which contact they mean. `resolve` can return more than one match if the same alias was registered for different entities by different sources - don't silently pick one, surface the ambiguity.

## Conflicting facts - don't silently pick one

If two skills (or a calendar sync and an email scan) assert different values for the same fact, tag both with the SAME `--fact-key` when you `remember` them (e.g. `--fact-key "meeting_time:raj:2026-09-08"`), then:

```bash
python jarvis/memory.py conflicts --entity-type contact --entity-id 7 --context business
```

If this returns anything, **surface the conflict to the user rather than picking a value** - "your calendar says 4pm but an email from Raj says 5pm, which is right?" is the correct response, not silently going with one. Only memories that share a `fact_key` are compared this way - most memories don't need one (they're not asserting a single contested value).

## Assembling full context before acting (the actual Phase 3 deliverable)

```bash
python jarvis/context.py --context business --mission "prepare for tomorrow's meeting with Raj" \
  --mention Raj --max-hops 2 --budget 15
```

This is the one call that does resolution + recall + graph traversal + conflict detection + privacy filtering + budget-aware truncation together, and returns an **explainable trail** (`"trail": [...]`) saying exactly what was included and why - "I suggested this because I found X, Y, Z" per the redirect's explicit ask. Use `--mention` for named-but-unresolved references ("Raj"), `--entity type:id` (repeatable) when you already know the entity, `--query` for a keyword search alongside entity-scoped recall.

**Always call this instead of separately calling `recall`/`traverse`/`conflicts` for anything where missing an angle would matter** - a one-off "what's this contact's phone number" doesn't need it (that's a plain CRM API call), but "what do I need to prepare for this meeting" or anything where forgetting a linked deadline/conflict/related person would be a real miss, does.

**On the confidence taxonomy** (known / probably_true / stale / conflicting / unknown): `assemble_context`'s memories carry `confidence_label` (known/probably_true/stale per-item); `conflicts` in the result covers "conflicting"; an empty `memories` list with no error is "unknown" - say so plainly ("I don't have anything on that") rather than inferring from general knowledge and presenting it as if it came from memory.

## What this is NOT

Not a place to log raw conversation transcripts - store the extracted fact/decision/commitment, not the whole exchange. Not a substitute for the CRM's own tables (`contacts`, `deals`, `mf_holdings`, etc.) - business-of-record data lives there; `assemble_context` doesn't call the CRM API itself, so if live CRM facts (current deal stage, phone number) are needed, fetch those the normal way and treat this engine's output as the *relationship/memory* layer, not a CRM proxy. Not yet wired to any automatic capture - nothing writes here unless a skill explicitly calls `remember`/`link`/`register-alias`. Not semantic search (see `recall`'s note above) and not able to read live calendar/email to resolve a real scheduling conflict against actual calendar data - that needs the connectors Phase 5 is scoped for; today's conflict detection only compares memories that were explicitly told to Jarvis with the same `fact_key`.
