# ArthaInvest Connect — Roadmap & Release Checkpoints

Internal real-time chat/collaboration system for the ArthaInvest CRM. Tracks checkpoint status,
scope boundaries, and release baselines for the Connect feature set (`backend/chat_routes.py`,
`frontend/src/components/chat/`, `frontend/src/contexts/ChatContext.jsx`).

This file is scoped strictly to Connect. It does not track JARVIS (see
`JARVIS_SCOPE_AND_ROADMAP.md`, a separate, unrelated workstream) or any other part of the CRM.

## Status

| Checkpoint | Scope | Status |
|---|---|---|
| 2A-i | DM/group foundation (WebSocket + REST, reconnect catch-up) | ✅ Complete |
| 2A-ii | Fixed org-wide channels, typing indicators, read receipts, unread counts | ✅ Complete |
| 2A-iii | Attachments, search, @mentions, edit/delete, reply-threading, audit trail | ✅ **Complete — LIVE** |
| 2B | CRM-linked chat (messages tied to contacts/leads/deals/policies) | 🔲 Not started |
| 2C | Notifications engine | 🔲 Not started |
| 2D | Permissions/audit redesign (owner/member roles, admin audit view) | 🔲 Not started |

**Standing constraints (all checkpoints):**
- No AI dependency — AI features stay feature-flagged/disabled until an API provider is funded.
- No paid telephony (Twilio/Exotel) introduced without separate explicit authorization.
- No video/screen/voice calling, no WhatsApp-based employee chat, no AI monitoring of private conversations.
- One checkpoint at a time — each gets its own scoped plan-and-verify pass.
- Checkpoint-by-checkpoint deployment discipline: explicit authorization required at each of
  commit / push / Render deploy verification / Hostinger frontend upload / live production
  verification. No step is bundled into the previous one.

---

## Release Checkpoint: Phase 2A-iii (2026-09-09)

### Architecture state at release

**GitHub**
- Branch: `master`, synchronized with `origin/master`
- Phase 2A-iii commit: `692fb291ff47a7fb7013aa7eed06be2c1c1d50bf`
- Commit message: `feat(chat): complete Phase 2A-iii messaging features`
- 13 files changed, 1,494 insertions(+), 58 deletions(-) (11 modified + 2 new test files)

**Render (backend)**
- Service: `arthainvest-crm` (`srv-dabu58740ujc73adldd0`)
- Live commit: `692fb29`, status: Live, trigger: Auto-Deploy, deploy duration 1m54s
- `/api/health`: 200 OK
- Full backend test suite: **662/662 passed** (653 baseline + 9 new tests from the post-review fixes)

**Hostinger (frontend)**
- Document root: `public_html/`
- Live JS bundle: `main.85dfbb9a.js` (previously `main.033c8460.js`)
- Live CSS bundle: `main.61b52827.css` (previously `main.0352adfc.css`)
- `index.html` and `asset-manifest.json` updated; all historical bundle files preserved untouched
  (no deletions); `.htaccess` / `default.php` untouched

### Feature list (verified live in production, not just locally)

- File/image attachments — allow-listed content types, 15 MB cap, DB-blob storage, authenticated
  streaming download
- Full-text/LIKE message search, scoped to caller's own conversation memberships, excludes
  soft-deleted messages
- @mentions — resolved server-side against real, active conversation members only
- Message edit — sender-only, full audit trail (`message_edits` table) written before mutation
- Message delete — soft delete only (body cleared, `deleted_at` set), audit trail preserved,
  sender-only
- Reply-to-message threading, with server-side validation that the reply target exists in the
  same conversation (see Fix 1 below)
- WebSocket events for all of the above, REST fallback for each
- Deleted-message attachment protection (see Fix 2 below)

### Two data-integrity fixes made during review, verified live

1. **Reply-target validation**: `reply_to_message_id` is now validated server-side — must
   reference a real message in the same conversation. Rejects nonexistent IDs and cross-conversation
   references identically (never reveals which case applied), both via REST (400) and WebSocket
   (error event). Confirmed live: an invalid reply target returns `400 {"detail": "Invalid
   reply_to_message_id"}`.
2. **Deleted-message attachment access**: `GET /attachments/{id}/content` now also checks whether
   the parent message is soft-deleted, returning the same 404 as a nonexistent attachment. The
   underlying attachment row and file bytes are never destroyed — only content retrieval is
   blocked. Confirmed live: an attachment's content becomes a 404 immediately after its parent
   message is deleted, while the attachment's metadata still appears in the message record.

### Verification performed

- Backend: 653 passed → two fixes applied → 662 passed (fresh full-suite run, 48m17s — noted as
  longer than the two prior clean runs of 13-18 min, but zero failures; flagged as something to
  watch if it recurs, not treated as a blocker)
- Frontend: production build clean, zero new warnings
- 10-item diff/security review (scope, secrets, debug code, attachment security, search
  authorization, edit/delete authorization, reply integrity, mention/XSS, deleted-message
  behavior, file-scope correctness) — passed after the two fixes
- Live production smoke test (logged in as a real user, isolated test channel, cleaned up via the
  app's own soft-delete afterward): authentication, chat page load, existing channel
  functionality, send, reply, edit, delete, attachment upload/download, deleted-attachment
  protection, search, @mention rendering — all confirmed working end-to-end through the actual
  deployed UI, not just via direct API calls
- Zero browser console errors, zero new server/runtime errors in Render logs during the test window

### Known, non-blocking items

- Pydantic `class-based config` deprecation warning in `schemas.py:32` — pre-existing, unrelated
  to this checkpoint
- Pre-existing `react-hooks/exhaustive-deps` ESLint warnings in unrelated components (Calls,
  Companies, Contacts, Dashboard, Integrations, LeadsList, Marketing, Pipeline, Quotations,
  Settings, Team) — pre-existing, unrelated
- The one anomalously long (48m17s vs ~13-18min baseline) full-suite run — no failures, not
  investigated further since it didn't block release; revisit if it recurs

### Unrelated outstanding work (not part of Connect, explicitly not touched by this checkpoint)

- JARVIS workstream commits (`452c207`, `ff5385b`, `2bdde5f`) — separate concurrent session,
  independently verified and approved by that session, published to `origin/master` alongside
  this checkpoint's commit since they shared the same local branch history
- `prospecting/*` spreadsheet/dashboard updates — separate routine data-entry work, uncommitted
  local changes at time of this release
- Two untracked zip files in `Zips & Bundles/`
- Anthropic AI credit balance (₹0) — explicitly deferred, not a Connect dependency

---

## Release Checkpoint: Employee Data-Visibility / Access Control (2026-09-15)

**Note on scope:** this checkpoint is not a Connect feature. It is a cross-cutting security
release affecting all seven core CRM entities (Connect/chat was not modified). It is recorded
here, alongside the Connect checkpoints, as the permanent historical record of this release —
per explicit instruction — rather than in a new file.

### Architecture state at release

**GitHub**
- Branch: `master`, synchronized with `origin/master`
- Commit: `243d253dfa91f78c82a68b2773bc0e8c723e247b`
- Commit message: `feat(security): add employee data visibility controls`
- 8 files changed, 2,189 insertions(+), 483 deletions(-)

**Render (backend)**
- Service: `arthainvest-crm` (`srv-dabu58740ujc73adldd0`)
- Live commit: `243d253`, status: Live, trigger: Auto-Deploy, deploy duration 2m07s
- `/api/health`: 200 OK, database connected

**Hostinger (frontend)**
- Document root: `domains/arthainvestcapital.com/public_html/crm_html/` (served at
  `crm.arthainvestcapital.com` — the CRM now lives on a subdomain; the root domain
  `arthainvestcapital.com` is a separate marketing site, not touched by CRM releases)
- Live JS bundle: `main.91ed8cf8.js` (previously `main.dff1bd4c.js`)
- CSS unchanged (`main.77907c25.css` — no style changes in this release)
- `index.html` and `asset-manifest.json` updated; `.htaccess` / `default.php` untouched

### Scope

Ownership-based visibility and write-protection across all 7 core CRM entities: Contacts,
Leads, Deals, Tasks, Calls, Quotations, Companies. **Meetings is explicitly out of scope** —
not covered by this or any prior access-control work; deferred to a future phase.

### Visibility model

- **Admins** (`users.role = 'admin'` — Nimita, Yogesh): unrestricted, see and modify everything.
- **Managers**: see and modify their own records plus their direct reports' records. Determined
  by a general `team_members.reports_to` field (one level only, no transitive hierarchy) —
  not hardcoded names. Set via the Team page's "Reports To" field.
- **Individual employees**: see and modify only their own records (created by them, or assigned
  to them), strictly isolated from peers and from their manager's own personal records.

### Entity-level ownership rules

| Entity | Creator column | Assignee column |
|---|---|---|
| Contacts | `created_by` | `assigned_team_member_id` |
| Leads | `created_by` | `assigned_team_member_id` |
| Deals | `owner_id` (no `created_by`) | `assigned_team_member_id` |
| Tasks | `created_by` | `assigned_team_member_id` |
| Calls | `created_by` | `team_member_id` |
| Quotations | `created_by` only | *(no assignee column — creator-only, not extended through a linked Deal's assignment)* |
| Companies | `created_by`, plus transitively visible via any visible linked Contact or Deal | *(no assignee column)* |

Enforced by a shared module, `backend/access_control.py`, applied to both reads (list
filtering, single-record GET) and writes (update/delete/assign/link), across roughly 45 routes.

### Cross-entity redaction

A visible record never leaks an invisible linked record's identifying name. Example: a Deal
visible to an employee, but linked to a Contact outside their visibility scope, shows the raw
`contact_id` (harmless foreign key) but `contact_name: null` — confirmed live in production
(see Verification below). Applies to every denormalized display field across all 7 entities
(e.g. `assigned_team_member_name`, `company_name`, `contact_name`, `deal_label`,
`deal_lead_name`, etc.).

### Protected high-risk endpoints/subresources

- Contact documents, notes, voice-note audio, and AI-suggested follow-ups
- Lead notes, voice-note audio, and AI-suggested follow-ups
- Contact renewals (`GET /api/contacts/renewals`)
- Company ↔ team-member visibility, both directions
- Task link/reverse-link to Contact, Call, Quotation, Company (checks visibility of both the
  Task and the link target)
- All reverse-lookup collection routes (e.g. `GET /api/calls/{id}/leads`)

### Bulk-import security fix

`bulk_import_contacts`'s phone-number-dedup check previously queried the entire `contacts`
table unscoped, which could be used as an existence oracle to probe whether a phone number
existed anywhere in the system, including records outside the caller's visibility. Now scoped
to the caller's own visibility before the dedup check runs.

### Google Sheets export security fix

`google_sheets_export` (Contacts and Leads) previously exported the caller's entire table
unscoped — a non-admin could bulk-exfiltrate every record in the system via Sheets export, not
just their own. Now scoped identically to the list endpoints. Admin export remains unrestricted.

### Test results

- Full backend suite: **734 passed**, 0 failed, 0 skipped
- Dedicated non-admin security suite (`test_data_visibility_security.py`): **23/23 passed** —
  the first tests in this codebase to run as a genuinely restricted non-admin user; every prior
  test in the suite ran as admin and could not have caught a visibility gap
- Google Sheets tests (`test_google_sheets.py`, including 6 new export-scoping tests): **20/20 passed**

### Live production smoke test (2026-09-15/16)

Performed against 3 throwaway accounts created for this purpose (a manager + 2 direct reports,
mirroring the real Samiksha/Chirag/Amol hierarchy) — real employee credentials were never used.

- Admin bypass: confirmed — sees everything, no redaction applied
- Manager hierarchy: confirmed — sees own + both reports' records
- Peer isolation: confirmed — each report sees only their own, across Contacts, Leads, Deals,
  Tasks, Calls, Quotations, Companies
- Direct-ID access to out-of-scope records: confirmed blocked (403) on every entity tested
- Cross-entity redaction: confirmed directly — an invisible Contact linked to a visible Deal
  showed `contact_id` but `contact_name: null` to the unauthorized viewer, and the real name to
  the manager/admin
- Google Sheets export and Connect regression were not re-exercised live (see Known limitations)

### Gate D.1 — production smoke-test cleanup (2026-09-16)

All throwaway test data created for the live smoke test was removed via the app's own
authenticated API, in dependency order, and independently re-verified:
- 0 GateD users remaining, 0 GateD team members remaining, 0 GateD CRM records remaining
  (Contacts, Leads, Deal, Quotation, Company, Task, Call all checked)
- 0 real records affected — real roster (Nimita, Yogesh, Samiksha, Chirag, Amol) confirmed
  intact and unchanged throughout
- No source changes, no new commit, no push, no deploy performed during cleanup

### Known limitations / observations (not implied to be fixed)

- **Meetings** is not covered by the access-control model at all — explicitly out of scope,
  deferred to a future phase.
- Google Sheets export scoping was verified by the 6 dedicated pytest tests but not
  independently re-exercised live in production, since no non-admin account has its own Google
  OAuth connection to test against (only the admin's `arthainvestcapital@gmail.com` connection
  exists). The code path is the same one covered by the passing tests.
- Connect (chat) was not re-tested as part of this release, since this release did not modify
  any Connect code.
- Contact/Lead documents, notes, audio, AI-suggest, and bulk-import were covered by the
  dedicated security test suite but not independently re-exercised live in production this pass.
- During the live smoke test, the admin's JWT session expired mid-verification, producing one
  misleading intermediate reading (an apparent "0 team members" result that was actually a 401
  auth failure, not data loss) — resolved by re-authenticating and re-verifying; not a
  production incident, noted here only for the historical record.

---

## Next up: 2B (CRM-linked chat)

Not started. Requires its own scoped plan-and-verify pass before any implementation begins, per
the standing "one checkpoint at a time" discipline. Do not begin without explicit authorization.
