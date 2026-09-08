# JARVIS — Current Scope vs. Future Roadmap

Built 2026-09-07 in direct response to the master directive's explicit ask: "Separate current scope from future roadmap." Companion to `JARVIS_PERMISSION_MATRIX.md` and `JARVIS_AGENT_RUNTIME_ASSESSMENT.md` (Stage A audit). `JARVIS_IMPLEMENTATION_ROADMAP.md` remains the detailed phase-by-phase log with dated "done when" criteria — this document is the higher-level cut the directive asked for: a single place that draws one hard line between *what exists and is tested today* and *everything the two master prompts describe that does not exist yet*.

Status labels used below match the master directive's own taxonomy (§73), used precisely rather than loosely:
`NOT IMPLEMENTED` / `DOCUMENTED ONLY` / `IMPLEMENTED BUT NOT INTEGRATED` / `INTEGRATED — TEST COVERAGE INCOMPLETE` / `INTEGRATED AND TESTED`.

## Stage Checkpoint Commit Procedure

Standing procedure for every stage checkpoint from Stage C onward (added 2026-09-07, first applied to the Stage C checkpoint). Nine pre-commit checks run in order; **any failure stops the commit** — none of these are soft warnings.

| # | Check | On failure |
|---|---|---|
| 1 | `git status` | If it doesn't run cleanly, stop — don't guess at repo state. |
| 2 | Re-check `HEAD` + recent concurrent commits (`git log`) | If `HEAD` moved since the last checkpoint, re-run checks 3-5 against the new baseline before proceeding — never assume the last check is still valid. |
| 3 | Inspect the complete diff of every file about to be staged | If a diff contains anything not attributable to this stage's own work, stop and re-scope the staging list — never stage-then-inspect. |
| 4 | Confirm no concurrent-session files are included | If a concurrent file appears in the staged set, unstage it and re-verify from check 1 — never proceed with a manually-trimmed stage. |
| 5 | Confirm no unrelated files are staged | Same as #4. |
| 6 | Re-run this stage's own tests | If any fail, **do not commit**. Fix the root cause (test bug or implementation bug — determine which, per this project's established pattern of not assuming the test is right), re-test, then restart the checklist from #6. |
| 7 | Re-run full regression | If any pre-existing test now fails, **do not commit this stage on top of a red suite** — the regression must be understood and fixed first, even if the cause looks unrelated to this stage's own files. |
| 8 | Re-run the transaction-safety canary specifically | A failure here is `CRITICAL` by definition (same severity as the transaction policy itself) — stop everything, do not commit, do not proceed to the next stage, fix and re-verify before doing anything else. |
| 9 | Re-run the production import/dependency audit | If any required import is missing, **do not commit** — this is exactly the failure mode that caused the earlier crash-loop incident (see `JARVIS_AGENT_RUNTIME_ASSESSMENT.md` §11); it must be zero, not "probably fine." |

**If `git commit` itself fails** (e.g., a pre-commit hook rejects it): do not retry with `--no-verify`. Investigate the hook's complaint, fix the underlying issue, re-stage, and create a **new** commit — never amend, per standing git safety rules, since a rejected commit never happened in the first place. Re-run the full nine-check list again before the retry, since the fix itself is a new change that needs its own verification.

**If any check above fails and requires a code fix:** the fix is made, then the *entire* nine-check sequence restarts from #1 — a partial re-check after a fix is exactly the kind of shortcut that lets a regression slip through.

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

### 1.6 Mission + MissionStep durable state model (Stage B) — ✅ INTEGRATED AND TESTED, 2026-09-07
**Canonical contract: [`JARVIS_STAGE_B_MISSION_RUNTIME_SPEC.md`](JARVIS_STAGE_B_MISSION_RUNTIME_SPEC.md)** — the authoritative technical specification for the Mission + MissionStep subsystem (state machines, concurrency model, canonical errors, restart recovery, user isolation, definition of done). This roadmap intentionally does not duplicate that detail; per that document's own §31, the implementation and its contract live in exactly two places (`jarvis/missions.py` + the spec doc) and this file only tracks status.

Status: `jarvis/missions.py`, 16/16 tests passing (`jarvis/tests/test_missions.py`), re-verified green as part of the full 61/61 regression sweep at the Stage C checkpoint. Structurally covered by the existing transaction-isolation canary (`test_jarvis_cannot_touch_transactions.py` globs all of `jarvis/*.py`) with no test edit required.

### 1.7 Planner (Stage C) — ✅ INTEGRATED AND TESTED, 2026-09-07
Three new files, on top of Stage B's mission substrate and Phase 3's Context Engine, scoped exactly to "transform Goal + Intent + Context + Capabilities + Constraints into a validated structured Plan — never execute anything" per the authorization for this stage.

- `jarvis/capabilities.py` — the minimal capability registry the Planner needs to answer "does this exist" (spec Section 7's "no invented capabilities"): the 20 pre-existing CRM skills + JARVIS's own native capabilities (context assembly, memory write, mission tracking), all genuinely available, plus 7 explicitly-listed not-yet-built capabilities (Gmail, calendar, browser automation, etc.) that return `CAPABILITY_UNAVAILABLE` with a specific reason rather than being silently invented. This is deliberately narrower than the full Tool Registry (Stage K) — no connector trust levels, no per-tool schema.
- `jarvis/plans.py` — the Plan + PlanStep durable model and its deterministic validator: schema checks, circular-dependency detection (topological sort, also used to compute `parallel_groups`), capability-availability checks, a transaction-pattern scan (reusing `backend/policy.py`'s exact pattern list — the same single source of truth every other layer of this project uses, not a fourth copy), risk/verification-presence checks, versioning with an immutable-history supersede chain (`create_replan`), and `materialize_plan()` to turn a `VALID` plan into real Stage B `MissionStep`s.
- `jarvis/planner.py` — the thin entry point (`propose_plan`/`propose_replan`) that ties the Context Engine (`context.assemble_context`, unchanged, not duplicated) to the plan validator. A real architectural note, not a gap: this file does NOT decompose a goal into steps itself — doing that would require an LLM call, which would need network access, which `jarvis/` is structurally forbidden from having (the same zero-network-import guarantee `test_jarvis_cannot_touch_transactions.py` already enforces). The decomposition reasoning happens in the calling skill/Claude, exactly matching the spec's own "LLM proposes, deterministic code validates" architecture (Section 10) — `propose_plan()` is the validation half, not the reasoning half.

**Implemented and tested (25/25 new: 19 in `jarvis/tests/test_plans.py`, 6 in `jarvis/tests/test_planner.py`):** basic and multi-step planning, parallel-group identification, missing-capability → `CAPABILITY_UNAVAILABLE`, unresolved-input → `clarification_needed` (without blocking validity, per Section 16's "possible after clarification" distinction), circular-dependency rejection, invalid-schema rejection, a consequential (R2+) step missing its required verification flag, transaction-shaped steps → `TransactionProhibitedError` (both a direct and an indirectly-phrased example, and confirmed `materialize_plan()` independently refuses even if the earlier check were somehow bypassed), replanning that supersedes without mutating the prior version's stored content, plan- and materialize-level idempotency (no duplicate plans or `MissionStep`s on a replayed request), Context Engine integration (a plan's context includes resolved entities/memories from `assemble_context`), the privacy boundary holding through the Planner's own entry point (not just inside `context.py` directly), the full 7-step "prepare for my meeting with Raj" example from spec Section 17 end to end, and a structural check (via introspection, same technique as the Phase 3.5 "send Raj the document" test) that neither `plans.py` nor `planner.py` contains any execute/run/invoke/dispatch/send-shaped function name.

**A real, if narrow, design conflict was caught by actually running the existing test suite, not just written carefully:** the first version of `capabilities.py` listed prohibited-transaction concepts (`bank-transfer`, `upi-payment`, etc.) as explicit "known unavailable" registry entries, so its own source text tripped `test_jarvis_cannot_touch_transactions.py`'s existing prohibited-pattern scan — exactly as that test is designed to do. Fixed by removing those entries entirely rather than weakening the test: the capability registry now only lists *not-yet-built* capabilities (a different concept from *permanently forbidden* ones), and transaction detection lives solely in `plans.py`'s dynamic scan against `backend/policy.py`'s pattern list at validation time — one source of truth, not a second hand-maintained copy that could drift.

**Deliberately NOT in Stage C** (per the explicit stage boundary): no code decomposes a goal into steps on its own (that's Claude/the calling skill, by architectural necessity — see above), nothing executes a `MissionStep` against a real tool (Worker Runtime, Stage D), nothing decides *when* a materialized `READY` step should run (Supervisor, Stage E), no resource-limit/budget check (Mission has no budget field yet — honestly N/A rather than fabricated), no `Verifier`/`Recovery Engine` involvement in plan outcomes (Stages F/G).

*Done when* (this stage's own framing from the authorization, met): a Plan model exists with schema validation; the Planner consumes Intent + Context without duplicating the Context Engine; capability discovery, dependency-graph validation, and risk/approval/verification metadata all work; plan versioning exists with an immutable-history guarantee; `MissionStep`s can be derived from a validated plan; no execution occurs anywhere in the stage; and a prohibited transaction can never become an executable plan — each exercised by a real, executed test, not asserted in prose.

### 1.8 Worker Runtime (Stage D) — ✅ INTEGRATED AND TESTED, 2026-09-07
`jarvis/workers.py`, on top of Stage B's mission substrate and Stage C's plan validator. Takes a `READY` `MissionStep` and executes it through an authorized, registered Worker — the first stage where anything in `jarvis/` actually *runs* something, as opposed to recording or validating.

**The Stage D execution boundary, stated explicitly (this was a required deliverable for this stage):** every Worker in this file executes only a real, bounded, already-existing **jarvis-internal** operation — reading/writing `jarvis/jarvis.db` through code that already exists (`context.assemble_context`, `memory.remember`). No worker can reach the live CRM REST API, the open internet, email, WhatsApp, or any external system, because `jarvis/` remains structurally network-free (the same zero-network-import guarantee `test_jarvis_cannot_touch_transactions.py` has enforced since Phase 2). This is a deliberate scope decision, not a missing feature: a worker that calls the CRM API would need `requests`/`urllib`, which is exactly the kind of "worth a deliberate, visible decision" moment that guarantee's own test comment warns about — that decision belongs to Stage M (Connector Fabric), not this one. Two real workers were built to prove the runtime: `ContextWorker` (wraps `assemble_context`) and `MemoryWriteWorker` (wraps `remember`) — no `GmailWorker`/`WhatsAppWorker`/`BrowserWorker` was created, per the explicit "no fake capabilities" instruction, since none of those connectors exist.

**Tool boundary:** a Worker's `execute()` calls a plain, pre-registered Python function — there is no mechanism anywhere in this file for an LLM to supply an arbitrary function, URL, or shell command at request time. `execute_step()` only ever dispatches to a Worker explicitly registered in a `WorkerRegistry` ahead of time, matched by a `capability_id` the step itself declared.

**Implemented and tested (18/18, `jarvis/tests/test_workers.py`):** registration/discovery (including a disabled worker being correctly undiscoverable), successful execution with a structured `WorkerExecutionResult`, a broken worker's exception recorded as `FAILED` (never silently swallowed), a slow worker's timeout recorded as `TIMED_OUT` and correctly mapped to `MissionStep`'s own `FAILED` status (Worker-level status vocabulary is intentionally richer than and distinct from Stage B's fixed 11 `MissionStep` statuses — `workers.py` translates one-directionally rather than growing Stage B's own contract), a missing required input failing before any claim or side effect, an unavailable capability raising `WorkerNotFoundError` without touching step state, only a `READY` step being executable, a duplicate claim on an already-`RUNNING` step correctly rejected (reusing Stage B's own optimistic-lock CAS as the concurrency guarantee — no second concurrency primitive was built), idempotent replay via `execution_id` (no re-execution, one execution record), cancellation propagating through to the `MissionStep` (reusing Stage B's already-idempotent `cancel_step`), cross-user execution correctly blocked, and — the highest-stakes category — a transaction-shaped step blocked *before* any claim or execution (`attempt_count` stays `0`, zero execution records), including two bypass attempts (an innocuous-sounding capability id with transaction-shaped step text, and indirect phrasing) that are both still caught, because the enforcement scans the step's actual text, not its declared capability.

**A real Stage B bug was caught by Stage D actually using the contract for the first time, not by review:** `missions.py`'s `_row_to_step()` deserialized `dependencies` from JSON but never did the same for `inputs`/`expected_output`/`output`/`observation`/`error`/`verification` — Stage B's own tests never happened to read one of those fields back as a structured object, so this sat dormant since the Stage B checkpoint. Fixed directly in `missions.py` (not worked around in `workers.py`, which would have left the same landmine for every future consumer of a `MissionStep`'s fields) by extending `_row_to_step()`'s deserialization to all six JSON-bearing fields. A second, harmless piece of copy-paste cruft (`_row_to_mission()` was unconditionally adding a spurious `dependencies: None` key that no `Mission` field ever used) was removed in the same pass. Re-ran the full 61-test suite that existed before this fix, plus all 18 new Stage D tests: **79/79 passing** — this is a bugfix to already-committed Stage B code, made transparently as part of Stage D, not hidden inside it.

**Deliberately NOT in Stage D** (per the explicit stage boundary): nothing decides *when* a `READY` step should execute — a caller still has to call `execute_step()` itself, exactly as Stage C's `materialize_plan()` didn't start anything either (Supervisor, Stage E). No retries (Stage G — `execute_step()` records one attempt and stops, it does not loop). No verification of whether an outcome was actually *correct*, only that the call completed and what it returned (Stage F — `observe()` is deliberately kept separate from `execute()` in the code to prepare for this, per spec Section 22, but nothing here claims a verified outcome). No connector/browser/MCP workers (Stage M/P). Cancellation is honestly scoped: Python cannot safely force-terminate a running thread, so a `TIMED_OUT`/cancelled worker call may still be running in the background after `execute_step()`/`cancel_execution()` return — this is stated in the code's own docstrings rather than pretending true preemptive cancellation exists.

*Done when* (this stage's own framing from the authorization, met): a Worker abstraction and registry exist with capability discovery; a `MissionStep` can be claimed safely (concurrency-protected, reusing Stage B); a Worker can execute a real bounded jarvis-internal operation with a structured result persisted; errors are canonical; idempotency and cancellation both work; observation is recorded separately from execution; the transaction prohibition remains absolute at this layer too, including against two different bypass phrasings; and no execution occurs without passing every check first — each exercised by a real, executed test.

### 1.9 Supervisor (Stage E) — ✅ INTEGRATED AND TESTED, 2026-09-07
`jarvis/supervisor.py`, turning Stage D's single-call `execute_step()` into a controlled mission execution loop: `schedule → dispatch → observe → update mission → find newly-ready steps → repeat` until a terminal or hand-off condition. No dedicated spec file was created for this stage — per the explicit "otherwise keep the roadmap as the index" instruction, this section is the record.

**The one architectural decision worth calling out explicitly:** `worker success != verified success` (spec Section 12) is enforced literally — this Supervisor **never** sets a Mission to `COMPLETED`, `PARTIALLY_COMPLETED`, or `FAILED`. All three are outcome judgments that belong to Stage F (the Verifier), which doesn't exist yet. What it does on its own authority: all steps terminal and clean → `EXECUTING → VERIFYING`, then stop (an honest "all attempted work is done, ready for review" signal, not a success claim); any step `FAILED`/`BLOCKED`/`CANCELLED`, or pending steps that can structurally never become ready (a dependency stuck in a non-`SUCCEEDED` terminal state) → `BLOCKED`, the one mission-level judgment this stage is explicitly authorized to make, matching the spec's own worked example.

**Reuses rather than duplicates, throughout:** ready-step discovery is `missions.advance_ready_steps()` (Stage B) called as-is — no second dependency-graph implementation. Dispatch is `workers.execute_step()` (Stage D) called as-is — the Supervisor never touches a tool directly. Concurrency protection is Stage B's existing version-CAS — a duplicate claim from a second Supervisor surfaces as `StateConflictError`/`StepNotExecutableError`, handled by skipping, not by building a second locking mechanism. Restart recovery is `missions.reconcile_interrupted()` (Stage B), filtered to one mission. Cancellation is `missions.cancel_mission()`/`workers.cancel_execution()` (Stage B/D), called for every non-terminal step.

**Execution strategy: sequential first, as instructed.** `batch_size` bounds how many `READY` steps one scheduling pass considers, but dispatch itself stays strictly sequential — one `execute_step()` call completes before the next starts. No `ThreadPoolExecutor`-based parallel dispatch was built; the spec's own conditions for supporting it (explicit limits, dependency isolation, concurrency protection, cancellation, deterministic state updates) weren't going to be met by a half-built version, so it wasn't attempted this stage.

**Implemented and tested (13/13, `jarvis/tests/test_supervisor.py`):** a single-step mission reaching `VERIFYING`; starting from `CREATED` through the full legal Stage B path to `EXECUTING`; a 3-step dependency chain (A→B→C) executing in true order, verified by comparing each step's `completed_at`/`started_at` timestamps, not just final status; 7 independent steps all completing correctly with a `batch_size` smaller than the step count; a failing worker correctly blocking the mission rather than a false `VERIFYING`; a step depending on a permanently-blocked one staying `PENDING` forever rather than being silently promoted; an unregistered-capability step blocking in under 5 seconds rather than spinning; cancellation stopping new dispatch and propagating to every non-terminal step; a duplicate-claim scenario correctly raising `StepNotExecutableError` rather than double-executing; `VERIFYING` correctly refusing a second `supervise()` call rather than reopening a finished mission; restart reconciliation recovering an interrupted `RUNNING` step to `BLOCKED`/`UNKNOWN` before resupervision; and — the highest-stakes category — a transaction-shaped step blocked through the full `Supervisor → Worker → Policy` path with zero execution, plus an indirect-phrasing bypass attempt still caught end to end.

**Deliberately NOT in Stage E** (per the explicit stage boundary): no retries — a `FAILED` step stays `FAILED`, Stage B's state machine still has no `FAILED → READY` edge (Stage G). No fallback, no replanning. No real parallel dispatch (see above). No outcome verification (Stage F). No Recovery Engine behavior of any kind. No token/cost budget accounting — `max_runtime_seconds` and `max_total_dispatches` are the only budgets, and the former is honestly optional (`None` by default, meaning "no wall-clock limit configured" rather than a fabricated value).

*Done when* (this stage's own framing from the authorization, met): a Supervisor exists that consumes Missions, discovers ready steps without duplicating Stage B's dependency logic, dispatches through Stage D's Worker Runtime without touching a tool directly, enforces dependency ordering, bounds its own batch size, detects both completion-for-verification and permanently-blocked conditions correctly, supports cancellation and restart recovery by reusing Stage B/D rather than rebuilding either, prevents duplicate execution, and keeps the transaction prohibition absolute through the full path — each exercised by a real, executed test, with no fake verification claimed anywhere.

### 1.10 Verifier (Stage F) — ✅ INTEGRATED AND TESTED, 2026-09-08
`jarvis/verifier.py` closes the loop Stage E deliberately left open: it is the only stage that ever sets a Mission to `COMPLETED`, `PARTIALLY_COMPLETED`, or `FAILED`, and it does so by gathering independent evidence, never by re-trusting a worker's own report. `EXECUTED → OBSERVED → VERIFIED/PARTIALLY_VERIFIED/FAILED/UNVERIFIABLE → (mission) SUCCEEDED-or-not` is enforced literally, not just described.

**What "evidence" means, given `jarvis/` stays structurally network-free (unchanged since Stage D):** there is nothing external to call, so verification means re-checking `jarvis/jarvis.db` itself, independently of the worker's stored return value. `jarvis-context-assembly` steps are verified by **re-running the same read** (`assemble_context` is pure) and comparing against what was recorded — a mismatch produces `PARTIALLY_VERIFIED` (data may have legitimately changed since execution), not a silent pass. `jarvis-memory-write` steps are verified by **independently re-querying the row by id** (`memory.get_memory()`, a new minimal read-only accessor added for this stage) and comparing its actual content — this is the concrete proof that a worker's `SUCCEEDED` is not, on its own, sufficient: three tests deliberately corrupt or delete the underlying row *after* a genuinely successful write and confirm the Verifier still catches the discrepancy and reports `FAILED`. A capability with no registered strategy verifies as `UNVERIFIABLE`, stated honestly — no connector/browser assumption was invented to paper over the gap.

**Mission-level closure rule, evidence-only:** any per-step `FAILED` → mission `FAILED`. All verified steps `VERIFIED` and nothing skipped → mission `COMPLETED`. Anything else (a mix of `VERIFIED`/`PARTIALLY_VERIFIED`/`UNVERIFIABLE`, or skipped work, but nothing contradicted) → `PARTIALLY_COMPLETED`. A mission with zero steps is vacuously `COMPLETED` (nothing was asked, nothing failed) — the one explicit edge case called out rather than left to fall through a default.

**Two more real deserialization bugs, same shape as Stage D's, caught by Stage F reading fields Stage D/E's own tests never happened to inspect:** `missions.py`'s `_row_to_mission()` never deserialized its own JSON-bearing `error`/`result` fields (only `_row_to_step()` got that fix at the Stage D checkpoint) — surfaced immediately by the first test that read `mission["error"]["code"]` after a `FAILED` verification. Fixed at the source the same way as before. This is the third time in three stages that actually exercising a contract has found what code review alone didn't — recorded here plainly, consistent with how the Stage D bug was handled.

**One small, additive contract extension, not a rewrite:** Stage B's `MissionStep.verification` field was declared in the original contract but never wired to anything — there was no way to write to it without going through `transition_step()`'s legal-edge check, which a terminal step (the only kind ever verified) can never pass. Added `missions.record_step_verification()`: a metadata-only update, still using the same optimistic-lock CAS as every other write in that module, that updates `verification` without performing a state transition. This fills in a gap the Stage B spec's own field list already declared as intended for "later Verifier integration" — it doesn't touch the state machine itself.

**Implemented and tested (18/18, `jarvis/tests/test_verifier.py`):** both real workers verified `VERIFIED` on a genuine match; a deleted memory row and a content-mismatched memory row both correctly verified `FAILED` despite the worker having reported `SUCCEEDED`; an unregistered capability correctly `UNVERIFIABLE`; `expected_output`'s `min_resolved_entities` threshold enforced and failing when unmet; a step that never ran rejected with `StepNotVerifiableYetError`; idempotent replay (same `verification_id` on a second call, a fresh one only with `force=True`) and restart-safety (`get_verification()` reads the same persisted field a new process would); mission-level `COMPLETED`/`FAILED`/`PARTIALLY_COMPLETED` all reached correctly including the zero-step vacuous case; `VERIFYING`-only guard proven both for a mission that hasn't gotten there yet and one already verified once (Stage B's state machine has no path back into `VERIFYING`, so double-verification is structurally impossible, not just discouraged); cross-user isolation; and — the guardrail stated most explicitly in this stage's authorization — a transaction-shaped mission proven to never even reach a state the Verifier can act on at all (`BLOCKED`, not `VERIFYING`), so `verify_mission()` raising `MissionNotVerifiableYetError` is the only possible outcome, not a defensive check bolted on separately.

**Deliberately NOT in Stage F** (per the explicit stage boundary): no retries, fallback, or replanning of a `FAILED` verification — it stays `FAILED` (Stage G). No LLM judgment anywhere in this file — every verdict is a deterministic comparison against independently gathered evidence. No verification strategy for any capability beyond the two that exist; a future connector-backed worker (Stage M+) needs its own real evidence source, never a generic "it probably worked."

*Done when* (this stage's own framing from the authorization, met): deterministic verification contracts exist with real evidence, not optimism; all four required verification outcomes are reachable and tested; mission and step verification are integrated using Stage B's own reserved fields rather than a parallel structure; expected-output validation and missing/contradictory-evidence detection both work end to end; verification is idempotent and restart-safe; user/mission isolation holds; canonical errors carry the same structured fields as every other stage; and the transaction boundary is proven structurally unreachable, not merely asserted.

### 1.11 What Part 1 does NOT include, stated plainly
Nothing in Part 1 constitutes a Recovery Engine, an Intent Lock, an Approval Gate, a full Action Firewall, a Tool Registry, a Model Router, a Connector Fabric, MCP integration, browser/computer-use capability, proactive intelligence, or a Family/Household OS. `superpower` is a fixed sequence of skill calls, not a planner in the Stage C sense. `jarvis` is an intent router, not the mission orchestrator. `missions.py` (§1.6) is a state ledger. `planner.py`/`plans.py` (§1.7) validate and version a plan a human/skill proposes. `workers.py` (§1.8) executes one already-claimed step through one already-registered worker, and cannot reach anything outside `jarvis/jarvis.db`. `supervisor.py` (§1.9) runs a mission's steps to completion-for-verification or a correctly-detected blocked state, but never itself declares success. `verifier.py` (§1.10) can now close a mission all the way to `COMPLETED`/`PARTIALLY_COMPLETED`/`FAILED` — but only ever forward, from evidence; a `FAILED` verification is final for this stage, nothing here retries, falls back, or replans it. This is the honest baseline the rest of this document measures against.

---

## Part 2 — Future Roadmap (specified across both master prompts; not yet built)

Organized by the master directive's own 20-stage order (§120–127), cross-referenced against `JARVIS_IMPLEMENTATION_ROADMAP.md`'s 14-phase plan where they cover the same ground. **Stage A only is complete** (`JARVIS_AGENT_RUNTIME_ASSESSMENT.md`, reconciled below in §5 against this newer prompt's specific audit requirements).

| Stage | What it builds | Status | Rough scale |
|---|---|---|---|
| A | Repository audit | ✅ done (`JARVIS_AGENT_RUNTIME_ASSESSMENT.md`, reconciled in §5 below) | — |
| B | Mission + MissionStep state model | ✅ **done 2026-09-07** — `jarvis/missions.py`, 16/16 tests passing, see §1.6 | small–medium (schema, transitions, persistence, tests) |
| C | Planner | ✅ **done 2026-09-07** — `jarvis/plans.py` + `jarvis/planner.py` + `jarvis/capabilities.py`, 25/25 new tests passing, see §1.7 | medium |
| D | Worker Runtime (worker interface, first real workers) | ✅ **done 2026-09-07** — `jarvis/workers.py`, 18/18 tests passing, see §1.8. Scoped to jarvis-internal workers only (no connector reaches the CRM API or internet — that's Stage M) | medium–large |
| E | Supervisor | ✅ **done 2026-09-07** — `jarvis/supervisor.py`, 13/13 tests passing, see §1.9. Never self-declares `COMPLETED` — hands off to Stage F at `VERIFYING` | medium |
| F | Verifier | ✅ **done 2026-09-08** — `jarvis/verifier.py`, 18/18 tests passing, see §1.10. The only stage that ever sets `COMPLETED`/`PARTIALLY_COMPLETED`/`FAILED`, and only from independently gathered evidence | medium |
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
