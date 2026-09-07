# JARVIS — Current Scope vs. Future Roadmap

Built 2026-09-07 in direct response to the master directive's explicit ask: "Separate current scope from future roadmap." Companion to `JARVIS_PERMISSION_MATRIX.md` and `JARVIS_AGENT_RUNTIME_ASSESSMENT.md` (Stage A audit). `JARVIS_IMPLEMENTATION_ROADMAP.md` remains the detailed phase-by-phase log with dated "done when" criteria — this document is the higher-level cut the directive asked for: a single place that draws one hard line between *what exists and is tested today* and *everything the two master prompts describe that does not exist yet*.

Status labels used below match the master directive's own taxonomy (§73), used precisely rather than loosely:
`NOT IMPLEMENTED` / `DOCUMENTED ONLY` / `IMPLEMENTED BUT NOT INTEGRATED` / `INTEGRATED — TEST COVERAGE INCOMPLETE` / `INTEGRATED AND TESTED`.

---

## Part 1 — Current Scope (what actually exists, in code, tested, today)

### 1.1 The pre-existing CRM (not built this effort — the foundation being evolved)
**Status: INTEGRATED AND TESTED** (pre-existing, in production)
- FastAPI backend, 249 routes, JWT auth, SQLite(dev)/MySQL(prod).
- React frontend, 20 Claude Code skills calling the live REST API directly.
- Deployed and live at `arthainvest-crm.onrender.com`.

### 1.2 Security fixes (Phase 1)
**Status: INTEGRATED AND TESTED**
- RBAC gap fix: 9 analytics endpoints moved from `get_current_user` to `require_admin`. Committed (`572150d`).
- `backend/policy.py`: deterministic, code-level (not prompt-level) block on any route matching a financial-transaction pattern, checked at app startup — the app refuses to boot if violated. Committed (`ee9cdfd`).
- `backend/tests/test_no_transaction_endpoints.py`: 3/3 passing (manually executed — see §3, environment note).

### 1.3 Memory / Life Brain (Phase 2)
**Status: INTEGRATED — TEST COVERAGE INCOMPLETE against the CRM app, INTEGRATED AND TESTED as a standalone module**
- `jarvis/memory.py`: 5-tier privacy model, staleness-aware ranking, knowledge-graph edges, auto-logged event store, soft-delete only. 6/6 tests passing (`jarvis/tests/test_memory.py`).
- Deliberately isolated from the CRM's own database (separate SQLite file) — not yet wired into the CRM's own user/auth model (see §2.2, multi-user gap).
- Uncommitted (working-tree only) — see §4, git status.

### 1.4 Unified Context Engine (Phase 3)
**Status: INTEGRATED AND TESTED (as a standalone module)**
- `jarvis/context.py`'s `assemble_context()`: entity resolution (explicit-alias-only) + multi-hop graph traversal + conflict detection + privacy filtering + budget-aware truncation + explainable trail, composed in one call.
- 9/9 tests passing (`jarvis/tests/test_context.py`), including the deliberately adversarial "context injection is inert data" test.
- 2/2 structural-isolation tests passing (`jarvis/tests/test_jarvis_cannot_touch_transactions.py`): zero network-capable imports, zero prohibited-pattern matches.
- Uncommitted — see §4.

### 1.5 Context Adoption (Phase 3.5)
**Status: partial — INTEGRATED AND TESTED for 6 of 22 capabilities; DOCUMENTED ONLY for the remaining 14**
- Wired: `jarvis`, `superpower`, `compliance-calendar`, `ceo-dashboard`, `credit-manager`, `mf-research`.
- Profiled but not yet edited: 14 more skills, full profile table in `JARVIS_CONTEXT_INTEGRATION.md`.
- The three scenarios the redirect specifically demanded ("prepare for meeting with Raj," "what should I do next," "send Raj the document") are each individually tested end to end, 3/3 passing (`jarvis/tests/test_phase35_scenarios.py`) — including proving, not just asserting, that context resolution and the ability to act are structurally separate.

### 1.6 What Part 1 does NOT include, stated plainly
Nothing in Part 1 constitutes a Mission system, a Planner, a Worker runtime, a Supervisor, a Verifier, a Recovery Engine, an Intent Lock, an Approval Gate, an Action Firewall, a Model Router, a Connector Fabric, MCP integration, browser/computer-use capability, proactive intelligence, or a Family/Household OS. `superpower` is a fixed sequence of skill calls, not a planner. `jarvis` is an intent router, not a mission orchestrator. This is the honest baseline the rest of this document measures against.

---

## Part 2 — Future Roadmap (specified across both master prompts; not yet built)

Organized by the master directive's own 20-stage order (§120–127), cross-referenced against `JARVIS_IMPLEMENTATION_ROADMAP.md`'s 14-phase plan where they cover the same ground. **Stage A only is complete** (`JARVIS_AGENT_RUNTIME_ASSESSMENT.md`, reconciled below in §5 against this newer prompt's specific audit requirements).

| Stage | What it builds | Status | Rough scale |
|---|---|---|---|
| A | Repository audit | ✅ done (`JARVIS_AGENT_RUNTIME_ASSESSMENT.md`, reconciled in §5 below) | — |
| B | Mission + MissionStep state model | NOT IMPLEMENTED | small–medium (schema, transitions, persistence, tests) |
| C | Planner | NOT IMPLEMENTED | medium |
| D | Worker Runtime (worker interface, first real workers) | NOT IMPLEMENTED | medium–large |
| E | Supervisor | NOT IMPLEMENTED | medium |
| F | Verifier | NOT IMPLEMENTED | medium |
| G | Recovery Engine | NOT IMPLEMENTED | medium |
| H | Intent Lock | NOT IMPLEMENTED | small |
| I | Approval Gate — now scoped by the §25A hard contract (`JARVIS_AGENT_RUNTIME_SPEC.md` §25A, added 2026-09-07): `ApprovalEngine` + the full permission/approval state machines | NOT IMPLEMENTED | medium (upgraded from small–medium — §25A adds explicit state machines, expiration, mission-scoped least-privilege) |
| J | Action Firewall — now scoped by §25A: `ActionFirewall` as the single required choke point, §25A.20's no-bypass rule, §25A.19's disguised-transaction classification | NOT IMPLEMENTED | medium–large (upgraded — disguised-request classification is new, nontrivial scope) |
| K | Tool Registry — now scoped by §25A.12/13: full tool + connector permission records, `ActionClassifier` + `RiskEngine` (R0–R4) | NOT IMPLEMENTED | medium (upgraded from small–medium) |
| L | Model Router | NOT IMPLEMENTED | medium |
| M | Connector Fabric + MCP Gateway | NOT IMPLEMENTED | large |
| N | Background Missions (durable scheduler) | NOT IMPLEMENTED | medium |
| O | Proactive Intelligence (Attention Firewall, Life Event Engine, Goal Engine) | NOT IMPLEMENTED | large |
| P | Browser / Computer Use | NOT IMPLEMENTED | large |
| Q | Security Hardening (zero-trust pass, prompt-injection defense audit) | NOT IMPLEMENTED (some pieces exist ad hoc — e.g. context-injection is already proven inert in Phase 3.5's tests — but no dedicated hardening pass has been done) | medium |
| R | Observability (execution trace, structured events, audit log UI) | partial — `jarvis_events` exists (§1.3) but no trace-event taxonomy, no UI | medium |
| S | Evaluation / benchmark suite | NOT IMPLEMENTED | medium |
| T | Production Hardening | NOT IMPLEMENTED | small–medium, but gated on the environment fix below |

**Also not started, and outside the 20-stage list but explicitly named in the directive:** Digital Twin, Family/Household OS, multi-channel Communication System, Voice pipeline (a disconnected prototype exists at `06 Marketing/Jarvis/`, not integrated), Developer/Skill Marketplace, Global Platform scale-out.

**Scale honesty, restated from the Stage A audit:** the full B–T sequence is realistically weeks-to-months of real engineering work for a solo operator's tool, not a single session. This roadmap intentionally does not compress that timeline — each stage still gets its own explicit "proceed" before starting, per both master prompts' own repeated instruction not to attempt this in one uncontrolled change.

---

## 3. The one blocking environment issue that affects every future stage

This machine has only Python 3.14 installed. The backend's pinned `pydantic==2.5.0` has no prebuilt wheel for 3.14, so the CRM backend's own `pytest` suite cannot currently be installed or run on this machine — a real constraint on how future stages (especially D, Q, S) get verified, not something fixed by this document. `jarvis/`'s own modules sidestep this today by being stdlib-only with manually-executed test files, which is why Phase 2/3/3.5 verification was real despite this gap — but a Worker Runtime (Stage D) that needs to call the actual CRM backend will eventually need this resolved. Flagged again here because Stage D depends on it; not fixed, per standing scope discipline.

---

## 4. Git status snapshot (as of this document, 2026-09-07)

Per standing git-safety instructions — reported honestly, not glossed over:

**Uncommitted, this session's work (never committed, per explicit standing instruction not to commit unless told):**
`jarvis/` (memory.py, context.py, tests/), `.claude/skills/jarvis/`, `.claude/skills/jarvis-memory/`, five modified `SKILL.md` files (`superpower`, `compliance-calendar`, `ceo-dashboard`, `credit-manager`, `mf-research`), and all `JARVIS_*.md` docs including this one and `JARVIS_PERMISSION_MATRIX.md`.

**Modified since this session last checked, by the concurrent session (git author "ArthaInvest Team") — NOT this session's changes, left untouched:**
`backend/main.py`, `backend/schemas.py`, `backend/tests/test_contacts.py`, `frontend/src/components/Contacts.jsx`, `frontend/src/services/api.js`, five `prospecting/*.xlsx` files, `prospecting/09_Dashboard.html`, `prospecting/outbox/F_loan_balance_transfer.csv`. (`backend/main.py` was previously confirmed safely committed with this session's RBAC+policy changes in `572150d`/`ee9cdfd`; the new modification on top of that is the other session's, not re-verified line-by-line here since it's out of scope for this document — flagged for awareness, not touched.)

**Untracked, not from this session:** `Zips & Bundles/bajaj letters hitesh*.zip` (pre-existing, unrelated).

Recent commits (all from the concurrent session, none from this one): `ee9cdfd`, `572150d`, `d057bab`, `126d89f`, `83f7f94`.

**This session still has not committed anything**, consistent with the standing rule, but this is the second time this exact situation (load-bearing uncommitted work sitting indefinitely in a repo with active concurrent development) has been flagged as a real risk — see the crash-loop incident in `JARVIS_AGENT_RUNTIME_ASSESSMENT.md` §11. The two pending questions from the previous stage report remain open and are restated in §6.

---

## 5. Reconciling this prompt's Stage A requirements against the existing audit

The master directive's Stage A asks for: current architecture, current capabilities, current routes, current database, current tests, current gaps, current risks, concurrent work, git status, dependency status. All ten are already covered by `JARVIS_AGENT_RUNTIME_ASSESSMENT.md`'s 11 sections, written against the shorter master prompt earlier the same day — the architecture described in both prompts is identical, just specified in far more detail in the second. No re-audit was performed from scratch; §4 above refreshes only the git-status snapshot, since that is the one input that changes hour to hour with a concurrent session active.

---

## 6. Two questions from the prior stage report, still open

Restated here since this document doesn't resolve them on its own:
1. Whether to commit the currently-uncommitted work now (§4), given the demonstrated crash-loop risk of leaving load-bearing files uncommitted in a repo with active concurrent development.
2. Whether to proceed to Stage B (Mission + MissionStep state model only — the smallest real next step, per this session's own scale-honesty recommendation and both master prompts' explicit instruction against one uncontrolled rewrite) or pause here.
