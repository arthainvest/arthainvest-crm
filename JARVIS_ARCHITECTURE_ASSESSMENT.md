# JARVIS — Architecture Assessment

**Date:** 2026-09-07
**Status:** Assessment complete, per Section 37 of `JARVIS_MASTER_SPEC.md`. No destructive changes made. This document covers deliverables 1–8 of the "First Task" list; the phased build plan is in `JARVIS_IMPLEMENTATION_ROADMAP.md`.

---

## 1. The single most important finding

**JARVIS is not a greenfield build.** This business already runs a live, actively-developed FastAPI + React CRM (`backend/` + `frontend/`, deployed at `arthainvest-crm.onrender.com`), and — critically — **20 Claude Code skills already exist at `.claude/skills/` that function as a working first draft of exactly the "specialist agents" the spec asks for.** Each one calls the live REST API, not the database directly, and not raw LLM calls without context. `superpower` is already a primitive Executive Agent/orchestrator that chains the others.

This means the honest, non-wasteful path is **evolve this pattern into JARVIS**, not replace it with a from-scratch Python/FastAPI/PostgreSQL/Celery/Redis multi-agent platform per the spec's "recommended tech stack" section. That stack makes sense for a team building a product to sell; it does not make sense for a solo operator's internal tool that already has a working, tested, in-production alternative. Section 28 of the spec agrees: *"DO NOT throw it away... JARVIS should sit above the CRM."* This assessment takes that literally — JARVIS sits above the CRM **and** above the existing skills, not beside or instead of them.

Where this assessment diverges from the spec's letter (e.g., recommending SQLite/MySQL continuity over a PostgreSQL rewrite, skills over a bespoke agent runtime), it does so in service of the spec's own stated priority in its closing section: *"USEFULNESS + INTELLIGENCE + MEMORY + ACCURACY + PROACTIVITY + SECURITY + EXTENSIBILITY"* over architectural purity.

---

## 2. What's reused vs. what needs work

### Reused as-is (working, tested, in production)
- FastAPI backend (`backend/main.py`, 249 routes, 552 tests), SQLite locally / MySQL in production via `db_compat.py`
- React frontend (`frontend/`, plain JS, 29 components)
- JWT auth (`backend/auth.py`)
- All 37 database tables — contacts, leads, deals, `mf_holdings`, `insurance_policies`, `contact_documents`, `commission_records`, tasks, meetings, calls, automations, WhatsApp state, tagging/custom-fields infrastructure
- The 20 existing skills — these become JARVIS's first-generation agents, not a separate thing to duplicate
- Existing AI plumbing: Claude (primary) + OpenAI (fallback) via `_call_ai_text` in `main.py`; `/api/ai/chat` (CRM-grounded chatbot), `/api/ai/detect-followup-date`, per-entity `/ai-suggest`
- WhatsApp Cloud API, Twilio/Exotel telephony, Gmail/SMTP email, Google Calendar sync, Mailchimp/LinkedIn/Zapier/Slack integrations — all built, some not yet credentialed in this environment

### Confirmed dead — do not build against, do not delete (standing policy)
- `CRM-PWA/` (Electron/PWA/Flutter-stub, frozen Aug 21, no `lib/` — the "Flutter app" is a stray config file with no code behind it)
- `FinTech-CRM/` (Next.js+Postgres rewrite attempt, frozen Aug 21)
- `backend/main_postgresql.py` (early 11KB Postgres prototype, superseded, not wired into anything)
- Root-level `arthainvest_crm.db` (0 bytes, stray duplicate of `backend/arthainvest_crm.db`)
- `.claude/worktrees/*` (5 leftover agent-session checkouts)

### Needs fixing before JARVIS can rely on it — see §6 (Security)
- **Company-wide analytics endpoints don't enforce admin-only access server-side.** Three skills' own docs already flag this as a known gap they paper over. This is not a JARVIS-shaped problem to route around — it's a real backend bug that must be fixed, because JARVIS's whole permission model (spec §22/31) assumes the backend is the actual enforcement point, not vibes-based trust in which skill happens to be invoked.

### Genuinely missing (spec asks for these, nothing today provides them)
- Any persistent **memory** across conversations (spec §6) — every skill invocation today starts cold, re-reading the API from scratch
- A **knowledge graph** (spec §7) — the relational data exists in the DB, but nothing today answers cross-entity questions like "clients with loans but no investment"
- A **single natural-language entry point** — today the user (or a session) must already know which of 20 skills/trigger-phrases to invoke; spec §1's core vision is that they shouldn't have to
- **Proactive intelligence** (spec §25) — everything today is pull/on-demand; nothing pushes an alert
- **Trading journal** (spec §11) — no schema, no skill, doesn't exist at all
- **World/news research synthesis** (spec §12/13) — four pointer-skills exist (`mf-research`, `insurance-research`, `loan-research`, and general web-research is implicit) but nothing does the fact/analysis/opinion/uncertainty-labeled synthesis the spec describes
- **Voice** (spec §19) — not started
- **Audit log** (spec §23) — nothing today records who/what/when for AI-driven actions
- **A formal tool registry with input/output schemas and permission levels per tool** (spec §21) — skills call the API ad hoc; there's no machine-readable manifest of what each skill/tool can touch

---

## 3. Financial-transaction prohibition — current state

**Already compliant, by omission.** The 249-route inventory contains zero payment, bank-transfer, UPI, or brokerage-execution endpoints. No `payment_tool`, `bank_transfer_tool`, `upi_tool`, or `brokerage_execution_tool` exists anywhere in the codebase. `commission_records` is a read/write **ledger** (recording money already earned), not a transaction executor — it never moves funds, it logs that a commission was received.

This assessment's job is to make that prohibition a **documented, permanent architectural guarantee** (§22/31 below), not just an accident of what hasn't been built yet. Every future tool added to the registry must pass the checklist in §22.

---

## 4. JARVIS Architecture Map

```
                              ┌─────────────────────────────┐
                              │         THE USER             │
                              │  (voice / text / Claude Code) │
                              └───────────────┬───────────────┘
                                              │
                              ┌───────────────▼───────────────┐
                              │      JARVIS ORCHESTRATOR       │
                              │   (.claude/skills/jarvis/)     │
                              │  intent detection → routing    │
                              │  → self-check → memory update  │
                              └───┬───────────────────────┬────┘
                  ┌───────────────┘                       └───────────────┐
                  ▼                                                       ▼
      ┌───────────────────────┐                              ┌───────────────────────┐
      │   EXISTING SKILLS      │                              │     NEW SKILLS         │
      │  (already built,       │                              │  (this project adds)   │
      │   reused as agents)    │                              │                         │
      │                        │                              │  - jarvis (router)      │
      │  ceo-dashboard          │                              │  - jarvis-memory        │
      │  sales-intelligence     │                              │  - jarvis-research      │
      │  sip-tracking           │                              │  - jarvis-news          │
      │  folio-review           │                              │  - jarvis-briefing      │
      │  cross-sell-radar       │                              │  - jarvis-eod           │
      │  insurance-lapse-       │                              │  - trading-journal      │
      │    prevention           │                              │  - jarvis-alerts        │
      │  commission-tracking    │                              │    (proactive)          │
      │  credit-manager         │                              │  - jarvis-audit         │
      │  loan-documents          │                             │                         │
      │  loan-sales              │                             │                         │
      │  loan-prospecting        │                             │                         │
      │  telecalling              │                            │                         │
      │  impeccable                │                           │                         │
      │  compliance-calendar        │                          │                         │
      │  client-portfolio-entry      │                         │                         │
      │  superpower (orchestrator)    │                        │                         │
      │  financial-calculators         │                       │                         │
      │  insurance-research              │                     │                         │
      │  loan-research                    │                    │                         │
      │  mf-research                        │                  │                         │
      └───────────┬────────────┘                               └────────────┬────────────┘
                  │                                                          │
                  └──────────────────────┬───────────────────────────────────┘
                                          ▼
                          ┌────────────────────────────────┐
                          │   ARTHAINVEST CRM REST API       │
                          │   backend/main.py — 249 routes    │
                          │   (existing, unmodified except     │
                          │    the RBAC fix in §6)              │
                          └───────────────┬────────────────────┘
                                          ▼
                          ┌────────────────────────────────┐
                          │   SQLite (dev) / MySQL (prod)     │
                          │   37 tables, via db_compat.py       │
                          └────────────────────────────────────┘

     Alongside the CRM, JARVIS also reaches:
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │ Web/News      │  │ Memory store  │  │ Audit log     │  │ Notification  │
     │ research       │  │ (new, local)   │  │ (new, local)   │  │ channel        │
     │ (WebSearch/    │  │ jarvis_memory. │  │ jarvis_audit.  │  │ (desktop/      │
     │  WebFetch)     │  │ json or table  │  │ log            │  │  WhatsApp)     │
     └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

**Key architectural decision:** JARVIS is implemented as **a layer of Claude Code skills**, not a separate running service. The "agents" in spec §5 map to skills; the "orchestrator" in spec §4 is the top-level `jarvis` skill; the "tool registry" in spec §21 is a manifest file each skill's SKILL.md conforms to (see §7 below). This gets every spec requirement except true always-on background voice/proactive-push without inventing new infrastructure the business doesn't need yet. Sections 9 (Voice) and 10 (Proactive) of the roadmap note where a small standalone service genuinely becomes necessary (a scheduler process for alerts, a mic-listening dashboard like the earlier `06 Marketing/Jarvis` HUD prototype for voice) — those are scoped narrowly, not as a rewrite of everything above.

---

## 5. Data model additions (JARVIS-specific, on top of the existing 37 tables)

No existing table is modified except the RBAC fix (a code-level auth check, not a schema change). New, additive tables:

```sql
-- Memory: every fact/commitment/decision JARVIS should recall later
CREATE TABLE jarvis_memory (
    id INTEGER PRIMARY KEY,
    memory_type TEXT NOT NULL,       -- identity | business | client | episodic | semantic | task | decision | investment
    content TEXT NOT NULL,
    entity_type TEXT,                -- contact | lead | deal | company | NULL (general)
    entity_id INTEGER,
    source TEXT NOT NULL,            -- which skill/conversation created this
    confidence REAL DEFAULT 1.0,
    importance INTEGER DEFAULT 3,    -- 1 (low) - 5 (critical)
    privacy_level TEXT DEFAULT 'business',  -- personal | business | sensitive
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP              -- soft delete only, never hard-delete (matches "never delete anything" policy)
);

-- Audit log: every JARVIS-driven action, per spec §23
CREATE TABLE jarvis_audit_log (
    id INTEGER PRIMARY KEY,
    user TEXT NOT NULL,
    agent TEXT NOT NULL,             -- which skill
    tool TEXT,                       -- which API endpoint / capability
    action TEXT NOT NULL,
    request_summary TEXT,
    result_summary TEXT,
    permission_level TEXT,
    approved_by_user BOOLEAN,
    error TEXT,
    created_at TIMESTAMP
);

-- Trading journal, per spec §11 — entirely new domain
CREATE TABLE trading_journal (
    id INTEGER PRIMARY KEY,
    instrument TEXT NOT NULL,
    trade_date DATE NOT NULL,
    side TEXT NOT NULL,              -- buy | sell
    quantity REAL,
    entry_price REAL,
    exit_price REAL,
    stop_loss REAL,
    target REAL,
    strategy TEXT,
    setup TEXT,
    reasoning TEXT,
    pnl REAL,
    holding_period_hours REAL,
    screenshot_path TEXT,
    emotional_state TEXT,
    mistake TEXT,
    lesson TEXT,
    created_at TIMESTAMP
);
-- Explicitly: this table is written to by the user (directly or via a
-- logging skill) and read by an analytics skill. No code path writes to
-- it as a side effect of "analyse this stock" — recording a trade must
-- always be an explicit, separate action, never inferred.

-- Alerts queue, for proactive intelligence (spec §25)
CREATE TABLE jarvis_alerts (
    id INTEGER PRIMARY KEY,
    alert_type TEXT NOT NULL,        -- lead_inactive | case_stuck | renewal_due | task_overdue | ...
    entity_type TEXT,
    entity_id INTEGER,
    severity TEXT DEFAULT 'normal',  -- low | normal | high | critical
    message TEXT NOT NULL,
    surfaced_at TIMESTAMP,
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP
);
```

These live in a **new, separate SQLite file** (`jarvis.db`) rather than inside `arthainvest_crm.db` — deliberately, so JARVIS's own state can never corrupt or lock the live CRM database, and so this stays true to "JARVIS sits above the CRM" (§28) rather than merging into it. A thin read-only join happens at query time (application layer), not via foreign keys across files.

---

## 6. Security architecture — the RBAC fix (Phase 1, do first)

**Finding:** `/api/analytics/dashboard`, `/api/analytics/team`, `/api/analytics/calls/by-employee`, `/api/analytics/sales`, `/api/analytics/conversion-rate`, and `/api/analytics/lead-sources` (main.py, confirmed at lines ~1782, 7901, 8120 and others in that family) currently only require `get_current_user` — any authenticated employee, not just `require_admin`. Three of the existing skills' own SKILL.md files already documented this as a known gap and self-enforce a policy check before calling these endpoints. That is not sufficient: a skill's internal policy check is not a security boundary if the underlying endpoint has none. Anyone with a valid token can call the endpoint directly (curl, Postman, a future integration) and bypass the skill entirely.

**Fix (additive, non-destructive, does not change any response shape or break the frontend for admin users — only tightens who can call it):**

Change the dependency on each of those routes from `get_current_user` to `require_admin`, matching the pattern already used correctly for team-roster CRUD and the commission ledger.

This is the correct **first line of JARVIS's implementation**, before any new skill is written, because every permission decision JARVIS makes downstream (spec §22) is only as trustworthy as the API it's calling.

## 7. Tool registry format

Every skill JARVIS treats as a "tool" gets a manifest block at the top of its SKILL.md (new convention, added going forward — existing skills get this retrofitted, not rewritten):

```yaml
tool_name: sip-tracking
description: Tracks each client's SIP status and due dates
reads: [GET /api/mf-holdings]
writes: [PUT /api/mf-holdings/{id}]
permission_level: 1   # analyse — see permission matrix below
security_classification: business_data
requires_approval: false
timeout_seconds: 30
```

Explicitly, the registry MUST NEVER contain an entry with `writes` targeting any payment/transfer/brokerage-execution endpoint, because no such endpoint exists and none may ever be added (spec §2). This is enforced by convention today (there is nothing to register) and should be enforced by a lint check once the registry is machine-read (roadmap Phase 11).

## 8. Permission matrix

| Level | Name | Existing skills at this level | Enforcement point |
|---|---|---|---|
| 0 | Read-only | `mf-research`, `loan-research`, `insurance-research`, `financial-calculators` (external reference only) | N/A — no CRM write access exists |
| 1 | Analyse | `sales-intelligence`, `folio-review`, `cross-sell-radar`, `loan-sales`, `credit-manager`, `sip-tracking` (read path) | CRM API auth (JWT) |
| 2 | Prepare/Draft | `impeccable`, communication drafting (WhatsApp/email templates) | CRM API auth + explicit "draft only" skill instructions |
| 3 | User approval required | `client-portfolio-entry` (writes MF/insurance records), `commission-tracking` (writes ledger), `telecalling` (places a real call), any WhatsApp send | CRM API auth + `require_nimita`/`require_admin` where applicable + the skill's own "you draft, I approve" pattern |
| 4 | Approved execution, non-financial | Automations enrollment, task/reminder creation, compliance-calendar entries | CRM API auth |
| — | **Financial transaction execution** | **None. Permanently blocked. No skill, tool, or future addition may occupy this level.** | Architectural — no endpoint exists to call |

`ceo-dashboard` and `credit-manager` currently rely on the API for level-1 enforcement that the API doesn't fully provide — this is exactly the gap §6 fixes.

---

## Next document

See `JARVIS_IMPLEMENTATION_ROADMAP.md` for the phased plan (spec §36), starting with the RBAC fix and the `jarvis` orchestrator skill as Phase 1.
