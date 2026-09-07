# JARVIS — Execution Permission Matrix

Built 2026-09-07 in response to the master directive's explicit ask: "Add an explicit execution permission matrix." Upgraded the same day to align exactly with the user's follow-up directive — **§25A of `JARVIS_AGENT_RUNTIME_SPEC.md`**, added "as a hard architectural contract, not just documentation," positioned immediately after the Approval Gate / Permission Model sections. That section is the canonical spec, saved verbatim. This document is its living, status-annotated companion — same categories, same terminology, but honest about what exists in code today versus what is still a specification for Stages H–K.

**§25A.26 is explicit that a markdown table alone does not satisfy the contract.** Nothing below should be read as claiming `PermissionEngine` / `ActionClassifier` / `PolicyEngine` / `RiskEngine` / `ApprovalEngine` / `ActionFirewall` exist as code — they don't, except where noted. This document is the specification-to-status mapping, not the implementation.

## 1. Implementation status of the six required components (§25A.26)

| Component | Status | Detail |
|---|---|---|
| `PermissionEngine` | **NOT IMPLEMENTED** | No unified engine. RBAC (`require_admin`/`require_nimita`) and the 5-tier privacy model (`ALLOWED_PRIVACY_FOR_CONTEXT`) are real but separate, narrower mechanisms — not this component. |
| `ActionClassifier` | **NOT IMPLEMENTED** | No code assigns the §25A.2 action classes (`READ`/`COMMUNICATE`/`DELETE`/etc.) to anything. Classification below is manual/documentary only. |
| `PolicyEngine` | **PARTIAL.** `backend/policy.py` is a real, working, narrow instance of this — but only for the `FINANCIAL_TRANSACTION` class. It is not a general policy engine. | |
| `RiskEngine` | **NOT IMPLEMENTED** | No code assigns R0–R4 risk levels. The table in §3 below is the specification, not a running classifier. |
| `ApprovalEngine` | **NOT IMPLEMENTED** | No approval-state machine exists anywhere in `jarvis/` or the CRM backend. |
| `ActionFirewall` | **NOT IMPLEMENTED** | No single choke point exists that every external action passes through. `backend/policy.py`'s startup check is the closest analog, and it only covers one action class. |

This honest gap is the primary input to Stage sequencing: Stages H (Intent Lock), I (Approval Gate), J (Action Firewall), K (Tool Registry) are where these six components get built — none has started.

## 2. Action classes (§25A.2) mapped against what exists today

| Action class | Exists in `jarvis/` today? | Exists in the CRM backend today? |
|---|---|---|
| `READ` | ✅ `recall()`, `traverse()`, `assemble_context()` — all pure reads, proven side-effect-free (`test_phase35_scenarios.py` scenario 3) | ✅ the 249 read routes |
| `SEARCH` / `ANALYZE` | ✅ within `assemble_context`'s scope | ✅ existing skill research workflows (`mf-research`, etc.) |
| `GENERATE` / `DRAFT` | Not built — no drafting capability in `jarvis/` | Not built as a distinct capability |
| `COMMUNICATE` | ❌ **structurally absent** — no send/transmit/dispatch-named function exists anywhere in `jarvis/memory.py` or `jarvis/context.py` (verified by introspection in `test_jarvis_cannot_touch_transactions.py`) | Pre-existing WhatsApp/marketing-share features exist outside `jarvis/`'s scope, human-triggered, not JARVIS-orchestrated |
| `CREATE` / `MODIFY` | ✅ `remember()`/`confirm()`/`correct()`/`link()` — but these only ever write to JARVIS's own isolated memory DB, never to the CRM | ✅ existing CRUD routes, gated by existing RBAC |
| `DELETE` | ✅ `forget()` — soft-delete only, never hard-delete, consistent with the standing never-delete rule | Pre-existing hard-delete routes exist in the CRM backend and have **not** been audited against §25A's R3/APPROVAL_REQUIRED classification — flagged as an open gap, not yet closed |
| `PUBLISH` | ❌ not built | Not built as a JARVIS capability |
| `SCHEDULE` / `AUTOMATE` | ❌ not built (Stage N) | Existing `automations_scheduler.py` pattern is pre-existing CRM infrastructure, not JARVIS-orchestrated |
| `EXTERNAL_SIDE_EFFECT` | ❌ structurally impossible today — `jarvis/` has zero network-capable imports | N/A |
| `FINANCIAL_TRANSACTION` | ❌ **structurally impossible** — see §3 | ✅ **blocked deterministically** — `backend/policy.py` |
| `SECURITY_SENSITIVE` / `ADMINISTRATIVE` | ❌ not built | ✅ gated by existing `require_admin` |

## 3. The one action class already meeting the full §25A contract: `FINANCIAL_TRANSACTION`

This is the only row of the default execution matrix (§25A.4) that is **actually enforced as code today**, matching R4/DENY/NEVER/PROHIBITED exactly:

- **Fail-closed at boot** (§25A.23 in spirit): `backend/policy.py`'s `check_no_transaction_routes()` runs in `main.py`'s `lifespan` startup handler against the live, registered route list. If any route matches a transaction-shaped pattern, the app refuses to start — there is no code path where an unrecognized or unclassified route silently defaults to allowed.
- **No override path** (§25A.18/25A.20): there is no approval mechanism wired to this check at all — not "approval denied," but *no approval concept exists for it in the first place*, which is stronger than the spec's minimum ("do NOT set REQUIRES_APPROVAL") — it was never a settable state.
- **Structural, not just policy-based, for the `jarvis/` package specifically**: `jarvis/memory.py` and `jarvis/context.py` have zero network-capable imports (`requests`/`urllib`/`http.client`/`httpx`/`aiohttp`/`socket`/`boto3`/`botocore` — none present, verified by AST/import inspection in `jarvis/tests/test_jarvis_cannot_touch_transactions.py`) and zero source-text matches against the exact same pattern list `policy.py` uses (imported directly, not duplicated — single source of truth). So even a compromised or misdirected `jarvis/` module could not make the network call to execute a transaction; it isn't a matter of a check being bypassed, the capability doesn't exist to bypass.
- **What §25A.19's "disguised" classification does NOT yet have**: no code today parses natural-language requests like "use browser and finish checkout" and classifies them as `FINANCIAL_TRANSACTION` before dispatch — that classification currently exists only as instruction text in `SKILL.md` files (e.g. `jarvis/SKILL.md`'s "leads with the permanent transaction-refusal check before any routing"), which is prompt-level, not code-level. The code-level backstop (policy.py + structural absence) is what actually prevents execution even if the prompt-level check were somehow bypassed — this is the correct defense-in-depth shape per the spec's own "LLM must never be the final authority" principle, but the *classification* step itself is not yet code.

**Net honest assessment:** the outcome §25A demands for this one action class (financial transactions can never execute, through any path) is already true today, via a narrower and more blunt mechanism (structural absence + startup-time route check) than the general `ActionFirewall`/`RiskEngine` architecture the spec describes. It is not yet generalized to any other action class.

## 4. Default execution matrix (§25A.4) — reproduced with current-status column added

| Action | Risk | Default Permission (spec) | Enforced today? |
|---|---:|---|---|
| Read local JARVIS data | R0 | ALLOW if authorized | ✅ privacy-tier filtered |
| Read permitted connector data | R0 | ALLOW if authorized | ✅ existing RBAC (CRM routes) |
| Search web / Research | R0 | ALLOW | N/A — no web-search capability in `jarvis/` yet |
| Analyze documents | R0 | ALLOW if permitted | N/A — not built |
| Generate content | R0 | ALLOW | N/A — not built |
| Draft email / WhatsApp | R1 | ALLOW | ❌ not built |
| Create internal task | R1 | ALLOW | ✅ pre-existing CRM task routes (outside JARVIS orchestration) |
| Create/modify calendar event | R2 | ALLOW if configured | ❌ not built |
| Send email / WhatsApp / SMS | R2 | CONDITIONAL, verification REQUIRED | ❌ structurally absent in `jarvis/`; pre-existing CRM WhatsApp feature is human-triggered, not gated by this matrix |
| Publish social content | R3 | APPROVAL_REQUIRED | ❌ not built |
| Delete data / external records | R3 | APPROVAL_REQUIRED | ⚠️ `jarvis/forget()` is soft-delete only (effectively stricter than R3); CRM backend's own delete routes **not yet audited** against this requirement — open gap |
| Change security settings / permissions | R3 | APPROVAL_REQUIRED | ✅ gated by existing `require_admin` (pre-existing, not JARVIS-built) |
| Add/install connector, grant tool permissions | R3 | APPROVAL_REQUIRED | N/A — no connector fabric exists yet (Stage M) |
| Execute financial transaction (all forms) | R4 | **DENY, NEVER, PROHIBITED** | ✅ **enforced** — see §3 |

## 5. Data access matrix (§25A.11) — current status

| Data Scope | Same User | Family Member | Business User | External Tool |
|---|---|---|---|---|
| PRIVATE | ✅ ALLOW | ✅ DENY (tested) | ✅ DENY (tested) | ✅ DENY (structurally — no external tool can reach `jarvis/`'s DB) |
| PERSONAL | ✅ ALLOW | ✅ DENY by default (tested) | ✅ DENY (tested) | ✅ DENY (structural) |
| FAMILY_SHARED | ✅ ALLOW | ✅ ALLOW (tested) | ✅ DENY (tested) | ✅ DENY (structural) |
| BUSINESS | ✅ ALLOW if authorized | ✅ DENY (tested) | ⚠️ ALLOW if authorized — **not yet meaningfully testable**, see gap below | ✅ DENY (structural) |
| PUBLIC | ✅ ALLOW | ✅ ALLOW | ✅ ALLOW | ✅ ALLOW |

**Gap, restated from `JARVIS_PERMISSION_MATRIX`'s prior version and `JARVIS_SCOPE_AND_ROADMAP.md` §1.3:** the privacy tiers correctly separate *domains* (tested exhaustively in `jarvis/tests/test_memory.py` and `test_context.py`), but `jarvis_memory` rows are not yet scoped to a `user_id` — there's only one real user of this system today (the solo operator), so "Same User" vs. "Business User" vs. "Family Member" as *distinct people* hasn't been exercised. This must be added before a second real person's data enters JARVIS's memory.

## 6. Permission states and approval states (§25A.5–25A.6) — current status

Neither the canonical `NOT_CHECKED/ALLOWED/DENIED/REQUIRES_APPROVAL/EXPIRED/REVOKED` state machine nor the `NOT_REQUIRED/REQUIRED/REQUESTED/APPROVED/REJECTED/EXPIRED/CANCELLED` approval state machine exists as code anywhere yet. Where a decision is made today, it is binary and implicit (a route either has `require_admin` or it doesn't; a memory row either matches the privacy filter or it doesn't) — not modeled as an explicit, auditable state object per §25A.21's `PermissionDecision`. This is exactly what Stage I (Approval Gate) and Stage J (Action Firewall) need to build.

## 7. User execution modes (§25A.7) — current status

None of `ASK/ASSIST/PLAN/SUPERVISED/EXECUTE/AUTOPILOT/BACKGROUND/STOP` exist as a selectable runtime mode today. Every current interaction is effectively closest to `ASK`/`ASSIST` in spirit (Claude reasons, then a skill calls the CRM API directly with the user watching) — but this is a description of the current shape, not an implemented mode selector. Building a real mode selector is Stage I/E territory (Approval Gate + Supervisor).

## 8. What this document is and isn't

- **Is:** the authoritative bridge between §25A's contract (in `JARVIS_AGENT_RUNTIME_SPEC.md`) and this codebase's actual state, updated whenever either changes.
- **Isn't:** the `PermissionEngine`. Per §25A.26, this table's existence does not satisfy the contract — only running code that every tool execution passes through does. Treat every "✅" above as "the *outcome* this row demands is currently true," never as "this component has been built," except where explicitly stated (the `FINANCIAL_TRANSACTION` row in §3, which is the one case where both are true).
- **Next concrete step**, when Stage H/I/J/K is picked up: build `ActionClassifier` first (it's the cheapest, most mechanical piece — tag each existing tool/skill with a §25A.2 class), then `RiskEngine` (assign R0–R4 per §25A.4), before attempting `ApprovalEngine`/`ActionFirewall`, which depend on both existing first.
