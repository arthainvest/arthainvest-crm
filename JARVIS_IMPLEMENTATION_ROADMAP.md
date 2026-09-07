# JARVIS — Implementation Roadmap

Phased per spec §36, restructured to 14 phases per the 2026-09-07 strategic redirect (below). Each phase is additive — nothing in an earlier phase is removed or broken by a later one. "Done" criteria are concrete and testable, not vibes: something is only marked ✅ once it's actually been run and shown to work, not just written.

## The 14-phase plan (per the 2026-09-07 redirect, adopted)

| Phase | Purpose | Status |
|---|---|---|
| 1 | Security + Orchestrator | ✅ done |
| 2 | Memory + Life Brain (Context Engine) | ✅ done (this session) |
| 3 | Unified Context + Knowledge Graph | ✅ core built 2026-09-07, see below |
| 3.5 | Context Adoption — wire `assemble_context` into existing skills | ✅ core built 2026-09-07, see `JARVIS_CONTEXT_INTEGRATION.md` |
| 4 | Daily Life OS (tasks/calendar/routines beyond CRM tasks) | not started |
| 5 | Connector Fabric + MCP | not started |
| 6 | Browser + Computer Agent | not started |
| 7 | Mission/Supervisor/Verification (the full orchestrator loop) | not started |
| 8 | Proactive Intelligence | not started |
| 9 | Family + Household OS | not started |
| 10 | Business/Professional OS (deepen what's already built) | mostly done via existing 20 skills, formalization pending |
| 11 | Multimodal + Voice + Cross-device | not started (prototype exists at `06 Marketing/Jarvis/`) |
| 12 | Self-improvement + Evaluation | not started |
| 13 | Developer/Skill Marketplace | not started |
| 14 | Global Platform | not started |

**Scope honesty:** phases 9, 13, 14 in particular are large, multi-session undertakings for a solo operator's tool — they're kept on the list because they're the right long-term shape, not because they're imminent. Each phase still gets its own "proceed" before starting, per the closing note below.

### Domain restructuring (adopted from the redirect)

The existing 20 skills become **capabilities under domains**, not 20 isolated commands:

```
                    JARVIS
                      |
              ORCHESTRATOR (jarvis skill)
                      |
       +--------------+--------------+
       |              |              |
  LIFE BRAIN       BUSINESS       PERSONAL
  (Phase 2-3)      (existing 20    (Phase 4, 9 -
  memory,          skills, mostly   not started)
  knowledge graph  already built)
```

Concretely today: every existing skill (`ceo-dashboard`, `sip-tracking`, `loan-sales`, etc.) sits under BUSINESS and is unchanged in how it's invoked. `jarvis-memory` (Phase 2) is the first LIFE BRAIN capability, and it's designed to be domain-agnostic — the same Context Engine will serve BUSINESS, PERSONAL, and eventually FAMILY memories, distinguished by `privacy_level`/context at query time (see Phase 2 below), not by three separate memory stores. PERSONAL/FAMILY-domain skills (household, family calendar, etc.) don't exist yet — Phase 4 and Phase 9.

### The orchestrator's evolving loop

`superpower` (existing) and `jarvis` (Phase 1) together implement roughly:

```
UNDERSTAND -> PLAN -> EXECUTE -> VERIFY
```

today (`jarvis` understands intent and routes; the routed-to skill executes; `superpower`'s existing sequencing is a form of planning). The target shape, built out incrementally as later phases land — not rewritten in one shot, since most of these steps need infrastructure that doesn't exist yet (memory=Phase 2 done, audit=Phase 3, supervision/recovery=Phase 7):

```
UNDERSTAND -> REMEMBER -> REASON -> PLAN -> ASK/ACT -> SUPERVISE -> VERIFY -> RECOVER -> LEARN
```

REMEMBER is now real (Phase 2, `jarvis-memory`). The rest arrive with their respective phases below.

---

## Phase 1 — Foundation

**1a. Fix the RBAC gap** (see Architecture Assessment §6) — ✅ DONE 2026-09-07
Changed all 9 company-wide analytics endpoints from `get_current_user(token)` to `require_admin(token)`: `/api/analytics/dashboard`, `/api/analytics/dashboard/loan-stage-deals`, `/conversion-rate`, `/sales`, `/team`, `/contacts`, `/calls`, `/lead-sources`, `/calls/by-employee`. (Two more than the six originally scoped in the assessment — `dashboard/loan-stage-deals` and `/contacts`/`/calls` were found to have the identical unfiltered-company-wide-data pattern once the actual route bodies were read, so were included for consistency.)
Verified: each call site's full function body was read to confirm `require_admin` is a safe drop-in (same return shape as `get_current_user`, used identically elsewhere in this file for team-roster CRUD and commissions); `main.py` still parses (`ast.parse` clean); `git diff` is exactly the 9 intended one-line changes, nothing else touched.
**Not verified:** the actual `pytest` suite (552 tests) could not be run — see environment note below. This is a gap in verification, not a known failure.

**1b. Create the `jarvis` orchestrator skill** — ✅ DONE 2026-09-07
`.claude/skills/jarvis/SKILL.md` — routes each of the 12 example prompts from spec §1 to a real skill, or states plainly which aren't built yet (conversation memory, trading journal, dedicated news/market-research synthesis) rather than pretending. Leads with the permanent transaction-refusal check before any routing decision.

**1c. Retrofit the tool-registry manifest block onto all 20 existing skills** — NOT STARTED
Deferred out of this session's scope (mechanical, 20 files, lower urgency than 1a/1b/1d). Next concrete step when picked back up.

**1d. Permanent financial-transaction-prohibition test** — ✅ DONE 2026-09-07, upgraded same day
`backend/tests/test_no_transaction_endpoints.py` — scans all 249 route paths for transaction-execution patterns (transfer, payment, UPI, withdraw, brokerage order, redeem, etc.), plus a regression test confirming it doesn't false-positive on legitimate routes (`/commissions`, `/quotations`, `/mf-holdings`). Manually executed (not via pytest, see below) — all three test functions pass; 249 routes scanned, zero violations.

**Upgraded per explicit instruction: "keep the financial transaction prohibition as an immutable backend/policy rule, not an LLM instruction."** The pattern list moved into `backend/policy.py` (single source of truth, `check_no_transaction_routes()` / `find_prohibited_routes()`), and `main.py`'s `lifespan` startup handler now calls it against the live, running app's actual registered routes — **the app refuses to boot if a transaction-shaped route is ever added**, independent of whether anyone remembers to run the test suite. Verified directly: fed it a clean route list (no raise) and a route list containing `/api/payments/transfer` (raised `ProhibitedRoutePolicyViolation` with a clear message) — both behave correctly. This is the concrete difference between "an LLM was told not to" and "the software cannot."

### Environment finding (not part of the original plan, discovered while trying to verify 1a)

**This machine cannot currently do a clean install of the backend's Python dependencies.** Only Python 3.14 is installed (no older version available), and `requirements.txt`'s pinned `pydantic==2.5.0` pulls in a `pydantic-core` version with no prebuilt wheel for 3.14 — the source build fails (a `ForwardRef._evaluate()` signature change between Python versions breaks pydantic-core's own build script). The project's own `venv/` folder existed but was empty (only `pip`), and `START_BACKEND.bat` runs `pip install -r requirements.txt` on every startup — meaning if this venv were ever deleted/recreated on this machine, the backend would fail to start at all, independent of anything in this session.

This is separate from the RBAC fix and not something to silently work around by upgrading dependencies as a side effect of a security patch. Options, if you want this fixed:
1. Relax the `pydantic`/`fastapi` pins to modern versions with Python 3.14 wheels, then run the full test suite to confirm nothing else broke — a real, separate task, not a quick add-on.
2. Install an older Python (3.11/3.12) alongside 3.14 for this project specifically, matching whatever version production/your usual dev machine actually uses.
Either is a reasonable fix; I didn't pick one unilaterally since it's outside what "fix the RBAC gap" asked for.

---

## Phase 2 — Memory + Life Brain (Context Engine) — ✅ DONE 2026-09-07

Built per the explicit redirect: not "add memory," but the actual foundation. `jarvis/memory.py` (stdlib-only, zero dependencies — runs in any Python, sidesteps the environment issue blocking the backend test suite) writing to `jarvis/jarvis.db`, kept separate from the CRM's own database.

**Implemented:**
- `jarvis_memory` table with every field the redirect specified: `value`/`content`, `source`, `created_at`, `last_confirmed`, `confidence`, `importance`, `expires_at`, plus `privacy_level` (five tiers: `private`, `personal`, `family_shared`, `business`, `public`) and `entity_type`/`entity_id` for CRM cross-referencing.
- `jarvis_memory_edges` — the knowledge graph, as typed relational edges (`from_type/from_id -[relation]-> to_type/to_id`), traversable in both directions via `related()`. Not a dedicated graph database — a relational approximation, which is the right call at this data volume (dozens to low hundreds of entities, not millions).
- Staleness/freshness: importance-scaled reconfirmation windows (`STALENESS_DAYS_BY_IMPORTANCE`) — a core identity fact can go a year without reconfirmation before being flagged stale; a casual preference goes stale in two weeks. Stale memories are downgraded in ranking and explicitly flagged, never silently dropped or silently trusted.
- Privacy enforcement (`ALLOWED_PRIVACY_FOR_CONTEXT`) — `private` is visible *only* in the `private` context itself, not a superset of anything; `business` and `personal`/`family` are fully separated except through `family_shared` and `public`.
- Hybrid retrieval, minus the vector part: structured filtering + knowledge-graph traversal + recency/importance/confidence ranking are real and tested. True semantic/vector search is explicitly NOT implemented (needs an embeddings key that isn't configured) — the code is structured so it slots in later (see the TODO in `recall()`'s docstring) rather than needing a rewrite.
- `.claude/skills/jarvis-memory/SKILL.md` — the usage-facing skill, wired into `jarvis`'s routing table.

**Verified, not just written** (`jarvis/tests/test_memory.py`, run directly — 6/6 pass):
- Recalls the right fact about a specific client, filtered correctly among decoys
- Retrieves the right preference among unrelated memories of the same type
- Forgets on request (soft-delete: gone from recall, row still exists per the standing never-hard-delete policy)
- Stale information is downgraded in ranking and flagged, not silently trusted or silently dropped
- **The highest-stakes one: a `private`-tagged memory does not leak into `business`, `personal`, or `family` contexts** — confirmed it's only recallable in the `private` context itself, and separately confirmed `family_shared` correctly reaches `family`+`personal` but not `business`
- Knowledge-graph traversal finds both outgoing and incoming edges correctly

**A real bug was caught by actually running this**, not just by writing it carefully: `_connect()` never closed its SQLite connections, which leaked file handles and (on Windows specifically) blocked temp-directory cleanup during testing — every single test failed with `PermissionError` on the first run. Fixed by making `_connect()` a proper context manager that always closes the connection, confirmed by rerunning (0/6 passing → 6/6 passing). Documented in the fix's own comment so it isn't reintroduced.

*Done when* (original criterion, met): a fact stated in one conversation is recallable in a separate, later conversation via `jarvis-memory`, with its timestamp, source, and confidence shown — confirmed via direct CLI smoke test (`remember` → `recall` → `forget` → `recall` again, each step's output inspected).

## Phase 3 — Unified Context + Knowledge Graph — ✅ CORE BUILT 2026-09-07

Built per the 2026-09-07 redirect's explicit instruction: not "more graph tables," but the Context Assembly Engine that makes Jarvis "one intelligence that understands the user's current situation before deciding what to do." Status against each of the 10 items specified:

| # | Item | Status |
|---|---|---|
| 1 | Context Assembly Engine | ✅ `jarvis/context.py`'s `assemble_context()` — resolution + recall + traversal + conflict-check + privacy filter + budget, one call |
| 2 | Knowledge graph as active reasoning layer | ✅ `assemble_context` traverses the graph as part of assembly, not just after writes; `jarvis`'s SKILL.md now instructs calling it before cascading actions |
| 3 | Context-aware privacy | ✅ Phase 2's boundary re-verified at the assembly layer, unchanged (not weakened) |
| 4 | Entity resolution | ✅ scoped honestly: **explicit aliases only** (`register_alias`/`resolve_entity`), never fuzzy/ML matching — "Mom" resolves only once someone has actually registered it. This is a deliberate, narrower interpretation than a fuzzy-matching system; upgrading to probabilistic resolution is a real future decision, not something to fake with an LLM guess in the meantime |
| 5 | Relationship traversal | ✅ `traverse()` — multi-hop BFS, cycle-safe, tested against the exact "Raj → Company → Project → Task" shape from the redirect |
| 6 | Context confidence | ✅ `confidence_label()` — known / probably_true / stale per memory; "conflicting" and "unknown" are assembly-level properties (surfaced via `conflicts` and an empty result respectively), not per-row |
| 7 | Conflict resolution | **partial, honestly scoped**: detects conflicts between memories Jarvis was explicitly told (same `fact_key`, different content) and surfaces them rather than silently picking one — tested with the exact calendar-vs-email 4pm/5pm example. Does NOT read a live calendar or live email to detect a real scheduling conflict against actual external data — there's no calendar/email connector wired into `jarvis/` yet (that's Phase 5's job). Don't oversell this as "reads your calendar and email" — it compares memories, which today means memories a skill or the user explicitly gave it |
| 8 | Context budget | ✅ `assemble_context`'s `budget` param truncates and reports `truncated: true` honestly, prioritized by score/hop-distance, never a silent random cut |
| 9 | Context audit trail | ✅ two layers: `jarvis_events` (automatic — every `remember`/`confirm`/`correct`/`forget`/`link` logs itself, a caller can't forget to write it) + `assemble_context`'s `trail` field (human-readable "included X because Y" for one specific assembly) |
| 10 | Tests before moving on | ✅ 9/9 in `jarvis/tests/test_context.py`, covering all 9 categories listed (cross-domain privacy, entity resolution, graph traversal, stale info, conflicting info, irrelevant-context suppression via budget, context injection, permission boundaries, multi-step reasoning) — run for real, not just written |

**Multi-source architecture, per the explicit "don't make the knowledge graph the only source of truth" instruction:**

| Source | Status |
|---|---|
| Structured DB (authoritative facts) | ✅ `jarvis_memory` table |
| Knowledge Graph (relationships) | ✅ `jarvis_memory_edges` + `traverse()` |
| Vector memory (semantic recall) | ❌ not built — needs an embeddings key that isn't configured. `recall()`'s query matching is keyword-only, stated plainly everywhere this matters rather than implied to be smarter than it is |
| Event store (what changed, when) | ✅ `jarvis_events`, auto-logged |
| Conversation memory (interaction history) | ❌ not built — no store of past conversation transcripts exists; `jarvis-memory` only knows what was explicitly `remember()`-ed out of a conversation, not the conversation itself |

**Transaction prohibition kept independent, per the explicit instruction that a context-engine change should never be able to weaken it:** `jarvis/` has zero network-capable imports (stdlib only — it cannot make an HTTP request to anything, structurally, not just by policy) and zero source-text matches against `backend/policy.py`'s exact prohibited-pattern list (the same single source of truth the CRM backend itself is checked against, not a separate copy that could drift). Verified in `jarvis/tests/test_jarvis_cannot_touch_transactions.py` — 2/2 pass.

**A real bug was caught by running the tests, again** (this is becoming the pattern that actually catches things, not a formality): none this time on the first pass — all 15 new-and-existing tests passed on first execution after building the primitives (traverse/resolve_entity/detect_conflicts) individually and smoke-testing each before composing `assemble_context` on top of them.

*Done when* (redirect's own framing, met): a query like "what do I need to prepare for tomorrow's meeting with Raj" resolves the name, recalls relevant memories, traverses to his company/project, and surfaces any conflicting facts — all from one `assemble_context` call, with an explainable trail. This exact scenario is `test_multi_step_reasoning_combines_recall_graph_and_conflicts_in_one_call` and passes.

## Phase 3 — Tool system

Formalize the registry from Phase 1c into something the `jarvis` orchestrator actually reads programmatically to decide routing, rather than the orchestrator's own hardcoded if/else logic. Add the audit log (`jarvis_audit_log`) and wire every skill invocation through it.

*Done when:* `jarvis-audit` skill can answer "what did JARVIS do yesterday" from the log, not from memory of the conversation.

## Phase 4 — Research

Build `jarvis-research`: the fact/analysis/opinion/uncertainty-labeled synthesis pipeline from spec §12, using WebSearch/WebFetch. Build `jarvis-news`: the categorized, personalized news engine from spec §13 (India/World/Business/RBI/SEBI/IRDAI/etc.), producing the headline → what happened → why it matters → impact → source format, not raw article dumps.

*Done when:* "Jarvis, research the latest RBI developments and tell me how they affect my business" produces a cited, dated, fact-vs-analysis-labeled answer connecting an actual RBI action to the actual product lines (MF/insurance/loans) this business sells.

## Phase 5 — CRM (mostly already done)

This phase is largely complete already (the 20 existing skills + 249-route API). Remaining work: close any per-entity gaps found during Phase 1–4 usage, and formalize the knowledge-graph-style cross-entity queries from spec §7 ("clients with loans but no investment relationship") as a documented, reusable query pattern rather than one-off SQL per question.

## Phase 6 — Tasks/calendar

`compliance-calendar` already exists but repurposes `/api/tasks` with a title-convention hack (no server-side filter). Add a proper `is_compliance` flag or dedicated table if usage shows the hack is fragile. Build the natural-language task engine from spec §16 as part of the `jarvis` orchestrator's routing (creating a task from "remind me to call Amit tomorrow at 11" without the user needing to open the Tasks page).

## Phase 7 — Sales intelligence (mostly already done)

`sales-intelligence`, `cross-sell-radar`, `loan-sales`, `credit-manager` already implement most of spec §10. Remaining: make lead scoring's estimate-vs-actual distinction explicit in every output (spec §10's "do not invent financial information" — audit existing skill outputs for this).

## Phase 8 — Investment/trading journal (net new)

Build the `trading_journal` table (Architecture Assessment §5) and a `trading-journal` skill for logging trades and a `trading-analytics` skill for the win-rate/risk-reward/pattern-detection analysis from spec §11. **Hard constraint, tested in Phase 1d's spirit:** neither skill may ever place, modify, or cancel a real order — logging is always a separate, explicit, after-the-fact action.

## Phase 9 — Voice

Reuse the architecture already prototyped in `06 Marketing/Jarvis/` (the wake-word dashboard built earlier this month) rather than starting over: Web Speech API for STT, browser `speechSynthesis` or a TTS pipeline for output, wired to call the `jarvis` orchestrator instead of (or in addition to) the standalone Claude API calls that prototype currently makes directly. This is the one place a small standalone service is genuinely justified, since Claude Code skills don't have an always-on microphone-listening runtime.

## Phase 10 — Proactive intelligence

Build `jarvis_alerts` (Architecture Assessment §5) and a scheduled job (reusing the existing `automations_scheduler.py` pattern in the backend, or a new lightweight equivalent) that periodically checks: leads inactive 48h+, stuck loan cases, renewals approaching, uncontacted important clients, overdue tasks. Surface via desktop notification and/or WhatsApp (channel already built), rate-limited by severity per spec §25's "do not create noisy notifications."

## Phase 11 — Security hardening

Re-run the Architecture Assessment's security section as a checklist: confirm production `CORS_ORIGINS` is explicitly set (not defaulting to `*`), confirm production credentials (S3/WhatsApp/Twilio) match what the business believes is live, add the prompt-injection defense explicitly to `jarvis-research` (treat fetched web content as data per spec §32 — this needs an explicit instruction in that skill's SKILL.md, not just implicit good behavior), formalize the permission matrix (Architecture Assessment §8) as something `jarvis` checks before routing rather than each skill checking independently.

## Phase 12 — Production deployment

Not applicable in the spec's original sense (there's no separate "JARVIS service" to deploy — it lives as skills alongside the existing, already-deployed CRM). This phase becomes: document the complete skill set in one place for onboarding (a `JARVIS_USER_GUIDE.md` — what to say, what it can and can't do), and a final pass confirming every item in spec §2's prohibited-actions list is still architecturally impossible.

---

## Phase 3.5 — Context Adoption — ✅ CORE BUILT 2026-09-07

Full detail in `JARVIS_CONTEXT_INTEGRATION.md`: the mandated flow (`User Request → Intent → Context Assembly → Policy Check → Skill/Agent → Action → Verification → Event`), a complete profile (context/privacy/budget/entities/act-or-recommend/verification/events) for **all 22 capabilities** (20 skills + `jarvis` + `jarvis-memory`), and the priority-ordered wiring status.

**Actually wired this pass** (6 skills, one representative of each priority group): `jarvis`, `superpower`, `compliance-calendar` (task/productivity), `ceo-dashboard` + `credit-manager` (CRM/business — one broad-report shape, one single-entity "prepare for X" shape), `mf-research` (research/document). **14 more queued** with profiles fully defined, same 3-line pattern proven to work.

**The three specified scenarios, tested for real** (`jarvis/tests/test_phase35_scenarios.py`, 3/3 pass):
1. *"Prepare me for my meeting with Raj"* — one `assemble_context` call resolves Raj, recalls the prior commitment and document reference, traverses contact→company→project→task, and surfaces the calendar-vs-email meeting-time conflict rather than picking one.
2. *"What should I do next?"* — confirmed the ranking is importance-driven, not creation-order or alphabetical (seeded a low-priority item first, an urgent one second — the urgent one ranks first in the result).
3. *"Send Raj the document"* — **the critical one**: confirmed Raj and the document both resolve correctly, but zero writes occur as a side effect (memory/event counts unchanged, checked directly against the database) and confirmed there is no function anywhere in `context.py`/`memory.py` whose name suggests it could send/transmit anything. Context resolving an action's *subject* is completely separate from being *permitted to act* — proven, not just asserted.

**Two honest gaps remain:**
- 14 of 20 skills are profiled but not yet edited — each is the same well-proven pattern, genuinely 10 minutes each once picked back up, not a design gap.
- Real conflict resolution against *live* calendar/email data needs Phase 5's connectors — today's version only catches conflicts between things Jarvis was explicitly told (via `remember` with a shared `fact_key`).

Phase 4, or finishing the remaining 14 skill integrations, are the natural next steps — say which.
