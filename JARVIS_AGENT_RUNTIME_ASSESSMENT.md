# JARVIS Agent Runtime — Stage A Architecture Audit

**Date:** 2026-09-07. Per the new master prompt's explicit instruction: this is the audit only. **No code has been changed to implement this prompt.** Everything below is inspection and honest scoping, grounded in the repository's actual current state (re-verified today, after a concurrent session's commits — see the Git Safety section at the end), not assumption.

---

## 0. A scale-honesty note, before the 13 items

The master prompt describes a production-grade autonomous-agent platform: persistent Mission objects, a dynamic Planner, a Worker contract, a Supervisor loop, an independent Verifier, a Recovery engine with failure classification, an Approval/Intent-Lock system, a centralized Agent Firewall, a Model Router, OpenTelemetry-style observability, restart-safe background missions, multi-agent parallelism. That is a genuine multi-week-to-multi-month engineering project for a real team — not something to compress into one or two more agent turns without it becoming exactly the "giant uncontrolled rewrite" both the prompt and the user's own note explicitly warn against.

This document does the audit the prompt asks for (Stage A) honestly. It also says plainly, in §8 below, what a *realistic* Stage B looks like — the smallest safe next slice, not the whole runtime. Everything past that needs its own "proceed," the same discipline every phase so far in this project has used.

---

## 1. Current architecture

`backend/` (FastAPI, 256 routes as of the latest commit) + `frontend/` (React) is the live CRM, deployed at `arthainvest-crm.onrender.com`. `jarvis/` (this session's addition, Phases 2-3.5) is a separate, stdlib-only Python package — `memory.py` (680 lines) and `context.py` (224 lines) — implementing a memory store, a knowledge graph, entity resolution, conflict detection, and a Context Assembly Engine, backed by its own SQLite file (`jarvis/jarvis.db`), deliberately isolated from the CRM's database. Above both sits `.claude/skills/` — 22 markdown files (20 domain skills + `jarvis` + `jarvis-memory`) that Claude Code reads and follows as instructions when invoked; there is no running orchestration *process* today, only prose a model is trusted to execute correctly each time it's invoked.

## 2. Existing agent-like functionality

Two things already resemble pieces of what's being asked for, and it's important to be precise about how far they actually go:

- **`superpower`** is a **fixed, hardcoded sequence** (numbered steps 1-8, branching only on admin-vs-employee) — not a dynamic Planner. It cannot decompose a novel goal, has no dependency graph, no parallelism, no retry/fallback logic, and no replanning if a step's result invalidates a later one.
- **`jarvis`** is an **intent router** — a table mapping request shapes to skill names, plus (as of Phase 3.5) an instruction to call `assemble_context` first for cascading requests. It does not produce a `Mission` object, does not track state across steps, and has no concept of verification or recovery.
- **`assemble_context()`** (Phase 3) is a genuine, tested implementation of the "CONTEXT" step in the requested loop — entity resolution, graph traversal, conflict detection, budget-aware truncation, an explainable trail. This is real and reusable, not aspirational.

Everything else in the requested loop — PLAN, RISK ASSESSMENT, POLICY/PERMISSION as a *checked* gate (not a prose reminder), EXECUTE as a tracked state, OBSERVE, VERIFY, RECOVER/REPLAN, structured mission status — **does not exist as code today.** It exists, at best, as instructions inside a SKILL.md that a model is asked to follow, which is precisely the gap the master prompt's §27/§4 ("The LLM must NOT be the security boundary") correctly identifies as insufficient.

## 3. Existing skills/capabilities

The full profile (context/privacy/budget/entities/act-or-recommend/verification/events) for all 22 already exists in `JARVIS_CONTEXT_INTEGRATION.md` — not reproduced here. Six are wired to call `assemble_context`; 14 are profiled but not yet wired. Two (`telecalling`, `client-portfolio-entry`) are the only ones that take a real external/CRM-write action today; every other skill is recommend/inform-only.

## 4. Existing memory/context architecture

`jarvis/memory.py`: `jarvis_memory` (facts, with confidence/source/importance/freshness/expiry/five-tier privacy), `jarvis_memory_edges` (knowledge graph), `jarvis_events` (auto-logged append-only event store), `entity_aliases` (explicit-only entity resolution). `jarvis/context.py`: `assemble_context()` composing all of the above plus conflict detection and budget-aware truncation into one explainable call. 20 tests across 4 files, all passing as of this audit (re-run today, post concurrent-session commits — no regression).

## 5. Existing policy/security architecture

`backend/policy.py` — the financial-transaction prohibition, enforced two ways: (a) `main.py`'s startup `lifespan` handler calls `check_no_transaction_routes()` against the live app's actual registered routes and **refuses to boot** if one matches a prohibited pattern; (b) `backend/tests/test_no_transaction_endpoints.py` runs the same check in CI. Both are now genuinely **committed and deployed** (see §11 below — this was not true as of this morning and caused a real production incident). `jarvis/tests/test_jarvis_cannot_touch_transactions.py` independently confirms the Context Engine package has zero network-capable imports and zero source-text matches against the same pattern list.

RBAC: `require_admin`/`require_nimita` exist and are correctly applied to all 9 company-wide analytics endpoints (Phase 1 fix, confirmed intact in committed history today) plus team-roster CRUD and the commission ledger. **This is where the honest gap is**: there is no code-level Approval Gate, Intent Lock, or Agent Firewall — "ask before sending," "confirm before dialing," etc. exist only as SKILL.md prose. A skill invoked with a sufficiently different or adversarial prompt has no code-level backstop today beyond the CRM's own RBAC (which governs *data access*, not *action authorization*) and the fact that no skill currently has send/transmit capability at all (verified structurally, not just policy-asserted, for the `jarvis/` package specifically).

## 6. Existing tool abstractions

None, formally. Skills call the CRM REST API directly (via Bash/curl or WebFetch, at the invoking Claude session's discretion) with no schema validation, no declared permission level enforced in code, no risk classification checked before the call happens. The "tool registry" that exists is `JARVIS_CONTEXT_INTEGRATION.md`'s profile table — a *document* a model is expected to have read, not a machine-enforced gate.

## 7. Existing database structures

CRM: 37 tables (contacts, deals, mf_holdings, insurance_policies, tasks, etc.), MySQL in production / SQLite locally, via `db_compat.py`. `jarvis.db`: 4 tables (memory, edges, events, aliases). **No Mission, MissionStep, WorkerExecution, or AgentState tables exist anywhere.** Nothing today can represent "a goal is 40% through a multi-step plan" as a queryable, restart-survivable row.

## 8. What can be reused / what must be added / what should NOT change

**Reuse wholesale:** the Context Engine (`recall`/`traverse`/`detect_conflicts`/`assemble_context` become the CONTEXT step verbatim); `backend/policy.py` (becomes the deterministic core the future Agent Firewall's policy-check step calls into — do not reimplement, call it); the 6 already-wired skills (become the first real Workers once a Worker contract exists, without rewriting their internals, per the prompt's own instruction).

**Must be added, in honest priority order** (this is the realistic Stage B+ sequence, not all-at-once):
1. **Mission/MissionStep state model** — a new, small `jarvis/agent/` package, new SQLite tables in `jarvis.db` (not a new database — reuse the isolation boundary that already exists), a handful of pure functions (`create_mission`, `advance_step`, `get_mission`), tested the same way `memory.py` was: direct execution, real assertions, no pytest dependency required.
2. **A minimal Worker contract** — adapt (not rewrite) 2-3 already-wired skills to return the structured `{status, output, observations, evidence, errors, verification_required}` shape, proving the pattern before converting all 22.
3. **A genuinely independent Verifier** for the narrowest possible case first (e.g., "a memory was actually written" — checkable by reading it back, not trusting the caller) before attempting anything that needs external-system verification (which needs Phase 5 connectors that don't exist yet).
4. Supervisor, Recovery, Approval/Intent-Lock, Agent Firewall, Model Router, Observability, background-mission persistence, multi-agent parallelism — each a real, separate future stage, not a checklist to rush through.

**Should NOT change:** the CRM backend/frontend's existing route contracts and DB schema (another party is actively developing this live — extra caution warranted given §11 below); `backend/policy.py`'s enforcement mechanism (it must remain the floor everything else is built on top of, never routed around); the 6 skills' core domain logic (only their entry point gains a context-assembly/mission-tracking call, per the prompt's own "adapt, don't rewrite" instruction).

## 9. Exact implementation plan (Stage B only — not the whole runtime)

Given §0's scale-honesty note: this audit recommends Stage B be **exactly** the Mission/MissionStep state model (prompt §STEP 4 / Stage B), built and tested the same way every prior phase in this project was — real code, real tests actually run, real bugs fixed when found (which has happened every single phase so far; expect it to happen again). Nothing beyond that in this same pass. Each subsequent stage (Planner, Worker contract, Supervisor, Verifier, Recovery, Approval, Firewall...) gets proposed, scoped, and built in its own turn once the previous one is confirmed solid — matching both the prompt's explicit "do not attempt everything in one uncontrolled change" instruction and this project's entire track record.

## 10. Risks

- **Scope-inflation risk, named plainly:** most of the master prompt's "north star" scenarios (meeting prep, "what's next," the send-boundary test) are **already demonstrably achievable** today via `assemble_context` plus a disciplined skill, as Phase 3.5's three scenario tests proved. Building the full Mission/Planner/Supervisor/Verifier/Recovery/Firewall apparatus is the right long-term shape for real autonomy and multi-step recovery — but it's worth the user knowing explicitly that a large fraction of near-term value is already real, and the remaining apparatus is about *reliability and autonomy at scale*, not unlocking capability that's currently zero.
- **Concurrent-session risk, demonstrated today, not hypothetical:** this exact session had a security fix silently absorbed into an unrelated commit, and separately caused a real production crash-loop because a dependent file was never committed. A persistent, restart-survivable Mission system (§13 of the master prompt) is meaningfully harder to get right when the underlying git/file coordination between concurrent sessions is this loose — worth resolving or at least acknowledging before promising restart-safety as a property.
- **"LLM must not be the security boundary" is correct and currently not fully true.** A real Agent Firewall enforcing Intent Lock/Approval Gates in code (not SKILL.md prose) requires action requests to flow through an actual running checkpoint a skill cannot bypass just by being invoked differently — that's a genuine architecture shift (Claude Code skills are prompt-driven by nature), not a documentation pass, and deserves its own careful design turn rather than being bundled into Stage B.

## 11. Git Safety (per the master prompt's explicit requirement)

**Files modified by this session (Phase 3.5 + earlier):** `backend/main.py` (RBAC fix + policy import — now safely committed, swept into commit `572150d` by the other party, confirmed intact), `backend/policy.py` + `backend/tests/test_no_transaction_endpoints.py` (now safely committed by the other party in `ee9cdfd`, content-verified identical to this session's version), 5 `.claude/skills/*/SKILL.md` files (still uncommitted, working-tree only), the entire `jarvis/` package (still uncommitted, working-tree only), 5 `JARVIS_*.md` docs at repo root (still uncommitted).

**Files from the other session, left untouched by this one:** `backend/database_mysql.py`, `database_sqlite.py`, `db_compat.py`, `schemas.py`, `tests/test_deals.py`, `frontend/src/components/Pipeline.jsx`, `frontend/src/services/api.js` — all now part of committed history (`572150d`, `d057bab`, `126d89f`) rather than sitting as working-tree diffs, so there's nothing left uncommitted from their side to accidentally disturb.

**A real incident, worth stating plainly:** this session's `main.py` edit (adding the `policy.py` import) reached production before `policy.py` was committed, because this session never committed anything — causing Render to crash-loop on every deploy since. The other party found this, verified my uncommitted `policy.py`/test file were correct, and committed exactly those two files to fix it (commit `ee9cdfd`, explicitly noting they left the rest of this session's work untouched). **Lesson for this session going forward: a file that another live change depends on being committed should be flagged for commit promptly, not left as a working-tree-only file indefinitely in a repo with concurrent active development.**

**Staged files:** none. **Commits created by this session:** none — per instruction, nothing has been committed by me at any point in this project.

---

## What Stage A recommends as the actual next step

Build and test the Mission/MissionStep state model (§9) — nothing more — in the next turn, once you say "proceed." Given the git-safety finding above, this session also recommends explicitly deciding whether to commit the currently-uncommitted `jarvis/` package and skill edits soon, given another party is actively developing this same repository and a second silent-absorption-or-crash-loop incident is avoidable.
