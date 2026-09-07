# JARVIS — Context Integration (Phase 3.5)

**Date:** 2026-09-07. Per the explicit redirect: the Context Engine (Phase 3) exists and is tested, but the 20 existing skills didn't call it — "a functioning brain component, but the rest of the body isn't consistently connected to it." This document is the fix: the mandated flow, a real profile for every skill (not just the ones actually edited), and what's actually wired vs. queued.

## The mandated flow

```
User Request → Intent → Context Assembly → Policy Check → Skill/Agent → Action → Verification → Event
```

Not `User Request → Skill directly`. Concretely:

1. **Intent** — `jarvis` (or the skill directly invoked by name/trigger phrase) figures out what's being asked.
2. **Context Assembly** — call `jarvis/context.py`'s `assemble_context()` with that skill's profile (below) *before* the skill's own logic runs. This resolves entities, recalls memories, traverses the graph, flags conflicts.
3. **Policy Check** — independent of context: is this asker allowed to see/do this (admin/employee/Nimita-only per the CRM's own `require_admin`/`require_nimita`, which the context engine does NOT replace — see "Two separate layers" below), and is this action prohibited outright (the financial-transaction rule, checked at the backend/policy.py level, not here)?
4. **Skill/Agent** — the existing skill's logic runs, now with real assembled context instead of starting cold.
5. **Action** — for skills that can act (a small, explicit list below), the action itself — gated by its own verification step.
6. **Verification** — act-capable skills confirm before acting (dial, write, send-draft) — never silently.
7. **Event** — anything that changed state logs to `jarvis_events` (automatic for memory mutations; skills that write CRM records or place calls should also `remember()` a note of it, so the audit trail covers CRM-side actions too, not just Jarvis's own memory).

## Two separate layers — do not conflate them

**Context Engine privacy** (`private`/`personal`/`family_shared`/`business`/`public`) answers "which *domain* is this information for." **CRM policy checks** (`require_admin`, `require_nimita`) answer "which *specific person*, within business context, can see this." A commission-tracking query is `business`-context AND `require_nimita`-restricted — both apply, independently. Context assembly resolving "Raj" and finding a document does not, by itself, grant permission to send anything to Raj — that's the Policy Check step, unchanged from before this document, and (per the explicit instruction) it stays that way on purpose: **context assembly must never become a way to route around approval gates.**

## Per-skill profile (all 22, defined now — wiring status tracked separately below)

| Skill | Context | Privacy | Budget | Entities it can access | Act or recommend? | Verification | Events |
|---|---|---|---|---|---|---|---|
| `jarvis` (orchestrator) | whatever the request implies | dynamic — asks if unclear | 15-20 | any resolved from mentions | **routes only, never acts** | admin/employee check before routing anything company-wide | none itself (delegates to the routed skill) |
| `jarvis-memory` | N/A — this IS the engine | N/A | N/A | N/A | N/A | N/A | auto-logs every mutation (already built) |
| `superpower` | business | business | 25-30 (synthesizes several skills) | the asker's own assigned deals/leads/clients (employee) or company-wide (admin) | **recommend only** — ends in "here's who to call," never dials | admin/employee check (already documented) | log one "superpower run" event per invocation |
| `ceo-dashboard` | business | business | 20 | company-wide (all contacts/deals/team) | recommend (report) | **admin-only**, enforced by the skill (backend RBAC now also enforces it server-side, Phase 1) | log "dashboard viewed" |
| `sales-intelligence` | business | business | 15 | self-scoped (asker's own `assigned_team_member_id`) | recommend | self-scope check | none (read-only) |
| `loan-sales` | business | business | 20 | deals + linked contacts/companies | recommend, flags stuck deals | none extra | none (read-only) |
| `loan-documents` | business | business | 15 | one deal + its document checklist | recommend + writes checklist notes (custom_fields) | confirm deal ownership if employee | log "document status noted for deal X" |
| `loan-prospecting` | business | business | 15 | leads (status=New) | recommend a call list only | none extra | none |
| `credit-manager` | business | business | 15 | one deal + its contact | recommend (pre-screen, explicitly not underwriting) | none extra (already self-documents the "not a decision" framing) | log "pre-screen run for deal X" |
| `cross-sell-radar` | business | business | 20 (3 product-line lookups per contact) | contacts + their mf_holdings/insurance_policies/deals | recommend | none extra | none |
| `commission-tracking` | business | business **+ require_nimita** (a policy check, not a privacy tier — see above) | 10 | commission ledger | recommend/report | **Nimita-only**, backend-enforced (`require_nimita`) | none (read) unless logging a new entry, then log it |
| `client-portfolio-entry` | business | business | 10 | one contact | **acts** — writes real mf_holdings/insurance_policies rows | confirm details before writing | **must** log "portfolio entry added for contact X" |
| `sip-tracking` | business | business | 15 | mf_holdings | recommend + writes status updates | confirm before status change | log status changes |
| `folio-review` | business | business | 15 | one contact's mf_holdings | recommend | none extra | none |
| `insurance-lapse-prevention` | business | business | 15 | insurance_policies + contacts | recommend a chase sequence — **does not send** WhatsApp itself | draft-then-approve if it ever sends (not built yet) | log "renewal chase flagged for contact X" |
| `telecalling` | business | business | 10 | leads/calls, one at a time | **acts** — places real calls via Exotel/Twilio | **confirm before dialing, every time** | **must** log "call placed to lead X" |
| `impeccable` | inherits from whatever's being checked | inherits | 10 | the specific quotation/deal/document | recommend only (QA check, never sends) | none extra | none |
| `compliance-calendar` | business (the owner's own license compliance, not client data) | business | 10 | tasks tagged `[Compliance]` | recommend | none extra | none |
| `financial-calculators` | business | business | 5 | optional: the contact the calculation is for | inform only | none | none |
| `insurance-research` | business | business | 5 | optional | inform only | none | none |
| `loan-research` | business | business | 5 | optional | inform only | none | none |
| `mf-research` | business | business | 5 | optional | inform only | none | none |

**The clearest "act-capable" skills** — where the "Send Raj the document" boundary matters most — are `telecalling` and `client-portfolio-entry` (real external/CRM-write actions), and `sip-tracking`/`loan-documents` (smaller CRM writes). Every other skill in this list is recommend/inform-only today. None of them send a message, email, or WhatsApp autonomously — the Communication Engine's "draft → ask user → send" rule (spec §18) is unbuilt as an active skill, so nothing sends anything yet regardless of context.

## Wiring status (priority order, as specified)

| Priority | Skill(s) | Status |
|---|---|---|
| 1 | `jarvis` | ✅ wired — calls `assemble_context` before routing anything with cascading effects (done Phase 3, strengthened this pass with the explicit 7-step flow above) |
| 2 | `superpower` | ✅ wired this pass |
| 3 | task/productivity (`compliance-calendar`) | ✅ wired this pass |
| 4 | CRM/business skills | ✅ 2 wired as proof-of-pattern this pass (`ceo-dashboard`, `credit-manager` — chosen as one "broad report" shape and one "single-entity prepare" shape); **12 remaining queued**, profiles fully defined above, same pattern applies |
| 5 | `jarvis-memory` | N/A — it's the engine itself |
| 6 | research/document (`mf-research`) | ✅ 1 wired as proof-of-pattern (`insurance-research`, `loan-research`, `financial-calculators` are the same 3-line pattern — queued, not done) |
| 7 | remaining | queued |

**Honest scope note:** "queued" means the profile is fully defined (table above) and the integration pattern is proven (6 skills actually edited and it works), not that the remaining 14 are unplanned. Doing all 20 with the same manual-edit rigor in one sitting risks the sloppy, unverified mechanical pass this whole project has been explicitly built to avoid. Each queued skill is a 10-minute, well-understood edit once picked back up — same 3-line pattern the 6 done ones now demonstrate.

## Phase 5 interface — built now, so the boundary is real

Per the explicit instruction: today's Jarvis runs on **synthetic/explicit data** (a skill or the user tells Jarvis something via `remember()`/`link()`). Phase 5's live connectors (Gmail, Calendar, WhatsApp) will **feed the same Context Engine** — not a second one. Concretely, a future connector is just another *caller* of the exact same functions:

```python
# Today (explicit): a skill tells Jarvis something the user said
jm.remember("episodic", "Rahul said he'd send documents Monday",
            source="conversation 2026-09-07", entity_type="contact", entity_id=101)

# Phase 5 (live, not built yet): a Gmail connector would call the SAME function
jm.remember("episodic", "Email from Rahul: will send documents Monday",
            source="gmail-sync:msg_id=abc123", entity_type="contact", entity_id=101)
```

No schema change needed for this — `source` already distinguishes provenance in free text (`"conversation ..."` vs `"gmail-sync:..."`), and `fact_key` already lets a synced fact conflict-check against an explicit one (exactly the calendar-vs-email 4pm/5pm scenario, which today only works because both sides were manually `remember()`-ed — Phase 5 makes the "calendar" side automatic, into the identical pipeline). **Nothing in `jarvis/memory.py` or `context.py` needs to change when Phase 5 connectors are built** — they're new data sources feeding an unchanged engine, which is the whole point of building this now rather than after connectors exist.
