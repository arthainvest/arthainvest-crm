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

## Release Checkpoint: Meetings + Activity/Communication-Log Access Control (2026-09-16)

**Note on scope:** like the checkpoint above, this is a cross-cutting security release, not a
Connect feature (Connect/chat was not modified). Recorded here as the permanent historical
record, per explicit instruction, alongside the other access-control checkpoints.

This release closes the gap the previous checkpoint's own "Known limitations" section flagged:
Meetings was explicitly out of scope for the first access-control release, and a separate
architectural review (documented below as M-0.1) found that Meetings could not be secured in
isolation without leaving the same information exposed through the unified activity feed and
the communication-log endpoint.

### Architecture state at release

**GitHub**
- Branch: `master`, synchronized with `origin/master`
- Commit: `e3c9a91549ca1fdac0764cf0d0c5d19a1b05cdff`
- Commit message: `feat(security): add Meetings and activity visibility controls`
- 4 files changed, 1,143 insertions(+), 132 deletions(-)

**Render (backend)**
- Service: `arthainvest-crm` (`srv-dabu58740ujc73adldd0`)
- Live commit: `e3c9a91`, status: Live, trigger: Auto-Deploy, deploy duration 1m53s
- `/api/health`: 200 OK, database connected
- No manual deployment was required — Render's existing Auto-Deploy-on-commit trigger fired on
  the push

### Gate sequence (M-0 through M-6)

**M-0 — Meetings access-control discovery.** Read-only audit of the `meetings` table, its ~15
endpoints, and its 7 cross-entity display fields. Found: standard `created_by` +
`assigned_team_member_id` ownership columns already present but completely unused for
visibility (`GET /api/meetings` discarded its own `get_current_user` result); a write-then-check
bug in `update_meeting` identical to the pre-fix pattern from the first access-control release;
zero scoping on any of the 5 link endpoints, 5 reverse-lookups, or the Calendar-sync endpoint;
zero non-admin test coverage. No `GET /api/meetings/{id}` route exists (by design, matching
Companies/Calls) — not introduced by this release either.

**M-0.1 — Communication-log / activity-feed discovery.** Follow-up read-only audit, triggered by
the finding that Meetings alone could not be secured while `GET /api/activities` remained
unscoped. Established: `communication_log` is creator-owned (`created_by`, always populated; no
assignee column, same shape as Quotations) and can legitimately exist with a null Lead/Contact
link; a second, independently unscoped route (`GET /api/communication-log`) exposes the same raw
`message`/`subject`/`recipient`/`error_detail` content; `campaign_recipients` has no owner column
of its own and inherits from its parent `campaigns.created_by`; `/api/activities` merges **five**
sources — `communication_log`, `calls`, `tasks`, `meetings`, `campaign_recipients` — with the
optional `lead_id`/`contact_id` params acting only as unscoped filters, not access checks.

**M-1 — Architecture.** Locked design, reusing every existing helper
(`get_visibility_scope`, `scope_filter_sql`, `scoped_rows`, `is_record_visible`,
`assert_record_visible`, `redact_if_not_visible`, `is_company_visible`) with zero modification:
- Meetings: standard `created_by` + `assigned_team_member_id` hierarchy, mechanical extension of
  the existing pattern.
- `communication_log`: **creator-owned only** — a locked decision explicitly rejecting the
  alternative "creator visibility OR linked Lead/Contact visibility" rule, since that would let
  an employee read another employee's actual message content merely by owning the recipient's
  Lead/Contact. Linkage controls redaction of the linked entity's name, never ownership of the
  communication itself.
- `campaign_recipients`: inherits `campaigns.created_by` (a direct one-hop join, not the
  Company-style `EXISTS` pattern, since no reverse relationship is needed).
- `/api/activities`: all five sources scoped in SQL, inside each source's own `WHERE` clause,
  before that source's own `LIMIT` — never fetched broadly and filtered in Python, which would
  let another employee's invisible-but-more-recent rows silently consume the visible caller's
  own limit slot.
- Calendar sync: Meeting visibility checked before any Google-connection check or API call.
- No new polymorphic/generic permission framework introduced anywhere.

**M-2 — Implementation.** `backend/main.py` updated; three new dedicated security test files
added. Test results: **40/40** new targeted security tests passed; specified regression subset
**120/120** passed; full backend suite **770/770** passed (734 baseline + 36 new — the count
converged to 40 after two fixes made during testing, see below). No changes to
`access_control.py`, `schemas.py`, either database file, or any frontend file.

Protections implemented: Meeting list/get visibility (both `GET /api/meetings` branches);
`update_meeting`/`delete_meeting` restructured to check-then-write (authorization before
mutation, mirroring `update_task`); all 5 Meeting link endpoints (Company via
`is_company_visible`, Deal/Call/Task/Quotation via their own ownership columns) checking both
the Meeting's and, when linking, the target's visibility; all 5 reverse-lookups using
`scoped_rows`; cross-entity redaction on all 7 Meeting display fields (two-tier `deal_label`
preserved; `assigned_team_member_name` never redacted); `GET /api/communication-log` scoped by
creator with linked-name redaction; `/api/activities` five-source SQL scoping with
`campaign_recipients` inheriting `campaigns.created_by`; Calendar-sync authorization reordered
ahead of the Google-connection check.

Two real issues found and fixed during M-2 testing: (1) the Calendar-sync endpoint originally
checked "is Google connected?" before "can the caller see this Meeting?", so an unauthorized
caller got a misleading `200 {configured:false}` instead of `403` — fixed by reordering; (2) one
test-setup assumption (two peer test accounts trying to link to a Company created by the seeded
admin, which is correctly not visible to non-admins) was corrected to use the admin for that
specific link, matching the pattern used elsewhere in the same file.

**M-3 — Commit.** `e3c9a91549ca1fdac0764cf0d0c5d19a1b05cdff` —
`feat(security): add Meetings and activity visibility controls`. Exactly 4 files:
`backend/main.py`, `backend/tests/test_meetings_visibility_security.py`,
`backend/tests/test_communication_log_visibility_security.py`,
`backend/tests/test_activity_feed_visibility_security.py`.

**M-4 — Push.** Pushed to `origin/master`; `HEAD = origin/master = e3c9a91`, ahead/behind 0/0.

**M-5 — Production deployment.** Render Auto-Deploy triggered by the push (no manual deploy
needed); build succeeded in 1m53s; `/api/health` → 200 OK, database connected/healthy.

**M-6 — Live production security smoke test.** Result: **PASS**. Performed against 4 throwaway
`GateM6` accounts (an admin + a manager + 2 direct reports), mirroring the real hierarchy shape;
real employee credentials were never used. Verified live: admin unrestricted visibility; manager
own+reports visibility; report-to-report isolation on both list and direct mutation attempts;
Meeting update/delete authorization-before-mutation; all 5 Meeting link endpoints' full
authorized/unauthorized-meeting/unauthorized-target matrix; all 5 reverse-lookups; cross-entity
redaction (directly observed: an invisible Lead/Contact/Company/Deal/Call/Task/Quotation linked
to a visible Meeting showed `null` names to the unauthorized viewer and real values to the
manager, with `assigned_team_member_name` correctly never redacted); the `/api/activities`
lead_id/contact_id filter-bypass protection (a Report2-owned, Report2-lead-linked Task confirmed
zero leak to Report1 under that filter); campaign-recipient inheritance; Calendar-sync
authorization-before-Google-access (403 returned immediately, not a misleading
`configured:false`); and non-mutating regression checks across all 7 pre-existing entities plus
Meetings and Activities, with zero 500 errors.

One documented exception: `communication_log` creator-isolation was **not** independently
re-verified live in production this pass, because both Email Service (SMTP) and WhatsApp
Business API are genuinely configured in production, and the only write path into
`communication_log` is an actual send — which this gate's own rules prohibited triggering. That
behavior remains verified by the dedicated pytest suite (`test_communication_log_visibility_security.py`,
11/11 passing) from M-2, not re-derived against live data.

Cleanup: all throwaway `GateM6` objects (4 users, 3 team members, 3 Meetings, 2 each of
Leads/Contacts/Companies/Deals/Calls/Quotations/Campaigns, 3 Tasks) removed via the app's own
authenticated API in dependency order, independently re-verified at zero remaining. Zero real
production records affected — real roster (Nimita, Yogesh, Samiksha, Chirag, Amol; 7 total
users) confirmed intact throughout. No code changes, commit, push, or redeploy occurred during
the smoke test.

### Final access-control model (current, as of this release)

- **Admins** (Nimita, Yogesh): unrestricted, see and modify everything, across all entities.
- **Samiksha** (manager): own records + Chirag's + Amol's.
- **Chirag**: own records only.
- **Amol**: own records only.
- Chirag and Amol cannot see each other's or Samiksha's records.
- `created_by` → `users.id`; `assigned_team_member_id` / `team_member_id` → `team_members.id`,
  the same convention across every entity.
- Companies: visible via own `created_by` or transitively via any visible linked Contact or Deal.
- Quotations: creator-only (no assignee column).
- **Meetings** (this release): standard `created_by` + `assigned_team_member_id` hierarchy, same
  as Contacts/Leads/Tasks.
- **`communication_log`** (this release): creator-owned only — Lead/Contact linkage never grants
  visibility to the communication record itself, only controls whether the linked entity's name
  may be displayed.
- **`campaign_recipients`** (this release): inherits `campaigns.created_by` — a Lead/Contact
  being visible does not independently grant visibility to a campaign-recipient row about it.

### Known intentionally out-of-scope items (not implied to be fixed by this release)

- **Campaigns themselves** remain outside the general access-control redesign — `GET
  /api/campaigns`, campaign CRUD, and the Marketing page's own recipient list are still
  unscoped. Only `campaign_recipients`' exposure *through the activity feed* was secured.
- **`dial_queue`** was noticed during discovery (it has `team_member_id`/`assigned_by` columns)
  but was not investigated as part of this release — flagged for a possible future discovery
  pass, not assumed safe or unsafe.
- No new standalone `GET /api/meetings/{id}` endpoint was introduced — none existed before, and
  none was required by the approved scope.
- The external Google Calendar permission boundary (what a synced event's viewers can see inside
  Google's own UI) remains entirely dependent on the existing Google integration and outside
  this CRM's authorization boundary — this release only gates whether the *sync action itself*
  may be triggered.
- All previously documented out-of-scope items from the first access-control checkpoint
  (Meetings — now closed by this release; Google Sheets non-admin live re-verification; Connect;
  Contact/Lead documents/notes/audio/bulk-import live re-verification) remain as previously
  recorded, except where explicitly superseded above.

### Release status

```
STATUS:                        CLOSED / LIVE / VERIFIED / DOCUMENTED
Production release:            e3c9a91
Security verification:         PASS
Production data integrity:     VERIFIED
Cleanup:                       COMPLETE
No known regression:           VERIFIED by the recorded smoke/regression checks
```

---

## Release Checkpoint: WhatsApp Inbox Access Control (2026-09-18)

### Background

A post-release security gap audit (N-0, full 271-route CRM access-control audit) found the
WhatsApp Inbox (`whatsapp_conversation`/`whatsapp_message`) had zero visibility scoping of any
kind: any authenticated employee could list, read, reply to, reassign, close, or opt out any
other employee's customer conversation, and the `reply` endpoint's real Meta Cloud API call meant
an unauthorized caller could trigger an actual outbound WhatsApp message to a real customer on a
conversation they had no business touching. `whatsapp_conversation` has no `created_by` column —
only `assigned_user_id → users.id`, the first entity in this codebase with a single-column,
`users.id`-only ownership model, requiring a new table-specific rule rather than reuse of the
standard `created_by`/`assigned_team_member_id` pair.

A dedicated discovery-only gate (N-1) inspected the actual code (not just the audit's summary)
and surfaced two business-rule questions with no existing precedent — who may see an unassigned,
customer-created conversation, and who may assign a conversation to whom — both resolved and
locked before any implementation began.

**Locked N-1 decisions:**
- **Assignment:** admins (Nimita/Yogesh) → anyone; a manager (Samiksha) → herself + her direct
  reports (Chirag, Amol); an individual report → self only.
- **Unassigned conversations:** visible to admins and managers only, never to an individual
  report — a manager can claim/assign one to herself or a report; reports never get a global
  "unclaimed" inbox.
- **Core mechanism:** `get_visibility_scope()`/`scope_filter_sql()`, the same architecture used
  everywhere else in this CRM — explicitly not `mine_only` as the security boundary.
- **Write ordering:** authorization → is the conversation visible? → is the operation permitted?
  → database mutation → external Meta/WhatsApp API call, if any. Never mutation-then-check.
- **Reply/send:** conversation visibility is sufficient authorization to reply — no separate
  permission framework.

### N-2 — WhatsApp Inbox implementation

New table-specific helpers in `backend/main.py` (not `access_control.py` — no existing helper
encodes "unassigned visible only to managers," and the locked N-1 decision was to avoid a second
generic permission framework):

- `_whatsapp_conversation_visible(scope, assigned_user_id)`: admin (`scope is None`) sees
  everything, including unassigned; everyone else sees a conversation assigned to anyone in their
  own `scope.user_ids`; an unassigned conversation is visible only when `len(scope.user_ids) > 1`
  — true exactly when the caller has at least one direct report, with no hardcoded names.
- `_can_assign_whatsapp_to(scope, target_user_id)`: admin may assign to anyone; everyone else may
  only assign to someone within their own `scope.user_ids`.

Applied to all six core Inbox routes: `GET /api/whatsapp/conversations` (scope-filtered SQL, with
`mine_only` retained only as an additional narrowing filter *within* scope, never the boundary
itself), `GET .../messages`, `POST .../reply`, `PUT .../assign`, `PUT .../status`,
`POST .../opt-out`. All four write endpoints now fetch `assigned_user_id` and check visibility
*before* any mutation — previously none of them checked at all (not even a write-then-check bug;
the check simply didn't exist).

One real ordering bug found and fixed during implementation: `reply_whatsapp_conversation`
originally checked "is WhatsApp configured?" before "can the caller see this conversation?" —
the same bug class as the Meetings Calendar-sync fix (M-2) — reordered so visibility is checked
first, before the configured-check, the message/template validation, the opted-out check, and the
real Meta API call.

Cross-entity redaction: `contact_name`/`lead_name` on the conversation list are redacted via
`redact_if_not_visible` when the linked Contact/Lead itself falls outside the caller's scope.

**Frontend** (`frontend/src/components/WhatsAppInbox.jsx`): fixed a real pre-existing bug where
the assignee label and the assignment `<select>` compared `team_members.id` against
`assigned_user_id` (a `users.id`) — they never actually matched. Fixed to match on
`team_members.user_id`, and the dropdown now only offers assignees the backend would actually
accept (self, or self + reports for a manager, or everyone for an admin) — a convenience/UX
filter, not the security boundary; the backend enforces the same rule independently regardless of
what the dropdown offers.

New test file `backend/tests/test_whatsapp_visibility_security.py`: **21 tests**, all admin/
manager/report visibility, direct-ID access, reply/status/opt-out authorization (with
`unittest.mock.patch("requests.post")` proving no real Meta call on an unauthorized attempt),
assignment authorization, cross-entity redaction, and a webhook-boundary regression.

### N-2.1 — Alternate outbound-path hardening

Mid-N-2, two additional endpoints were found to share the exact same
`_find_or_link_conversation` pattern as the now-fixed `reply` endpoint: `POST /api/whatsapp/send`
and `POST /api/flows/{id}/send`. Both are phone-number-driven "compose new message" endpoints
(used by the WhatsApp buttons on Contacts/Leads/Dashboard/Pipeline, and by WhatsApp Flows),
distinct from the `conversation_id`-driven "act on existing" routes covered by N-2's locked
scope. If the phone number resolved to a *pre-existing* conversation assigned to a different
employee, either endpoint could inject a message into it with zero visibility check — an
alternate path to the same "unauthorized real Meta send" risk. This was explicitly reported as a
finding rather than fixed inside N-2's already-authorized scope, and a dedicated follow-up gate
(N-2.1) was authorized to close it.

New helper `_can_send_to_whatsapp_conversation(scope, assigned_user_id)` — deliberately distinct
from `_whatsapp_conversation_visible`, which governs the Inbox list/view surface and hides
unassigned conversations from individual employees. For the two compose endpoints: a brand-new
conversation (no existing row) is always sendable by anyone (legitimate new outreach); an
existing-but-unassigned conversation is always sendable by anyone (continuing an unclaimed
thread is not a visibility leak); an existing conversation assigned to someone outside the
caller's scope is rejected with 403 **before** the configured-check, before any DB mutation, and
before any Meta API call.

New tests (in the same file, **11 tests**): admin can send to a conversation assigned to anyone;
manager can send to her own and to each report's conversation; each report can send to their own
but not to a peer's or the manager's conversation (with `mock_post.assert_not_called()` proving
no Meta call on the unauthorized attempt); an existing-unassigned conversation and a brand-new
number both remain sendable by anyone; `/api/flows/{id}/send` follows the identical rule; and a
combined test confirms neither compose endpoint can be used as a bypass for the other's
authorization against the same conversation.

### Validation (N-2 + N-2.1 combined)

- New dedicated security tests: **21 (N-2) + 11 (N-2.1) = 32/32 passed**.
- WhatsApp regression (`test_whatsapp.py`, `test_whatsapp_flows.py`): **25/25 passed**.
- Full backend suite: **802/802 passed, 0 failed, 0 skipped** (770 baseline + 32 new — exact
  arithmetic match).
- Frontend production build: clean, no new warnings.
- `git diff --check`: clean on all changed/new files.
- No changes to `access_control.py`, database schema, or any unrelated frontend component.

### N-3 — Commit

`a1ab52fff70d42098d96ca2c87d1e37df3b56548` —
`feat(security): secure WhatsApp conversation access`. Exactly 3 files: `backend/main.py`,
`backend/tests/test_whatsapp_visibility_security.py` (new),
`frontend/src/components/WhatsAppInbox.jsx`. The frontend file was deliberately included in this
single commit (rather than split out) since the assignment-dropdown correctness fix is part of
the same N-2-authorized scope as the backend assignment-authorization work.

### N-4 — Push

Pushed to `origin/master`; `HEAD = origin/master = a1ab52f`, ahead/behind 0/0. Render Auto-Deploy
triggered by the push and picked up the backend automatically (no manual deploy step) — confirmed
live via the Render dashboard: commit `a1ab52f`, status Live, build duration 1m58s.

### N-5 — Production smoke verification

**Result: PASS — safe production smoke verification, with live outbound-conversation testing
deferred.**

The originally planned live conversation-authorization smoke test (creating synthetic WhatsApp
conversations to exercise reply/assign/status/opt-out end-to-end under real production
credentials) was found to be architecturally impossible to run safely: the only code path that
creates a `whatsapp_conversation` row is the inbound Meta webhook (which requires a valid
`WHATSAPP_APP_SECRET` HMAC signature in production — correctly not available or used for this
test) or the two compose endpoints, which for a brand-new number always attempt a real outbound
Meta API call as an unavoidable part of creating the conversation (production has real WhatsApp
credentials configured, unlike the local test suite). Per the locked safety rule — outbound sends
may only proceed to a real external call if a genuinely safe mock/intercept exists, otherwise stop
at the authorization boundary — this portion of N-5 was explicitly descoped rather than worked
around; no real WhatsApp message was sent, no webhook secret was used or requested, and no
production configuration was changed to manufacture a test path.

What **was** verified live, safely, against real existing production data with zero synthetic
conversations created:
- A synthetic 5-account hierarchy (2 admins, 1 manager, 2 reports mirroring the real
  Nimita/Yogesh/Samiksha/Chirag/Amol shape, distinctly named, never the real accounts) was
  created via the app's own authenticated API.
- `GET /api/whatsapp/conversations` scoping was confirmed against the two real, pre-existing
  production conversations: both synthetic admins saw both; the synthetic manager saw exactly
  the one unassigned conversation (correctly excluding a real conversation assigned to an actual
  employee outside her scope); both synthetic reports saw zero (correctly excluded from both the
  assigned-to-someone-else conversation and the unassigned one) — a direct, real-data
  confirmation of the locked N-1 visibility rule.
- All six Inbox write/read routes correctly returned 404 for a nonexistent conversation ID across
  every synthetic role, with zero mutation of any real record.
- The Inbox frontend and Dashboard were confirmed to load correctly and show correctly-scoped
  (zero-leakage) data under the synthetic manager session.
- The one real conversation opened during this check was independently re-verified unchanged
  afterward (`status`, `assigned_user_id`, `opted_out_at`, total conversation count) — zero
  mutation occurred.

Cleanup: all 5 synthetic users and 3 synthetic team-member rows were deleted via the app's own
authenticated API and independently re-verified at zero remaining; the real admin roster
(`nimita`, `testuser`, `yogesh`) confirmed intact and unchanged throughout. No WhatsApp
conversation or message was ever created during N-5, so there was nothing to clean up on that
side. No code changes, commit, push, or redeploy occurred during this gate.

`/api/whatsapp/send` and `/api/flows/{id}/send` status: **implemented → committed (`a1ab52f`) →
802-test verified → deployed.** Only their successful external-call execution against a live
production conversation was deliberately not exercised, for the same no-safe-mock reason as
above — this is not an unresolved implementation gap.

### N-6 — Frontend production deployment

The N-5 smoke test surfaced that the CRM frontend is hosted separately on Hostinger with its own
manual build-and-upload deploy step, entirely independent of Render's git-triggered backend
auto-deploy — no Hostinger deployment had occurred as part of N-2 through N-4, so the committed
assignment-dropdown fix, while live on the backend, was not yet live in the UI actually served to
employees.

- Frontend rebuilt from the already-verified commit `a1ab52f` — deterministic build, same bundle
  hash (`main.e3f8d51f.js` / `main.77907c25.css`) as the build already verified clean in N-2.
  Source- and bundle-confirmed the fix (`assignableTeamMembers`, `reports_to`-based filtering) is
  present in the shipped code.
- Deployed exactly 4 files (`index.html`, `asset-manifest.json`, `main.e3f8d51f.js`,
  `main.77907c25.css`) to `domains/arthainvestcapital.com/public_html/crm_html/` via Hostinger
  File Manager. The separate marketing site at `arthainvestcapital.com`'s own `public_html/` root
  (guarded by a pre-existing `DO_NOT_UPLOAD_HERE` marker file at that level) was never touched.
- Live verification: `crm.arthainvestcapital.com/asset-manifest.json` confirmed the new bundle is
  live; login and WhatsApp Inbox load correctly under the admin account; both real production
  conversations display correctly; the opted-out conversation's banner and disabled Send button
  render correctly, matching backend state exactly.
- **Limitation:** the manager/report role's interactive assignment-dropdown filtering was not
  directly re-verified live via click-through in this gate, due to browser-automation/extension
  connectivity limitations encountered during the session. This does not weaken the security
  posture — the dropdown is explicitly a UX convenience layer, and the backend independently
  enforces `_can_assign_whatsapp_to` regardless of what the dropdown offers, which N-5 already
  verified live against real production data.
- Zero data or message impact: both real conversations confirmed unchanged before and after; no
  WhatsApp message was sent; no production configuration was changed.
- No code changes, commit, push, or backend redeploy occurred during N-6.

### Final access-control model addition (this release)

- **`whatsapp_conversation`** (this release): single-column ownership (`assigned_user_id →
  users.id`, no `created_by`) — the first entity in this codebase without the standard
  `created_by`/`assigned_team_member_id` pair. Visibility and assignment-target rules are both
  built directly on `VisibilityScope.user_ids` via two new table-specific helpers, not a second
  generic framework. Unassigned conversations are visible to admins and managers only.
- **`POST /api/whatsapp/send`** and **`POST /api/flows/{id}/send`** (this release): "compose new
  message" endpoints, authorized on the same underlying rule as the Inbox routes but via a
  distinct helper (`_can_send_to_whatsapp_conversation`) that correctly treats new/unassigned
  conversations as always sendable, blocking only sends into a conversation another employee has
  already claimed.

### Known intentionally out-of-scope / deferred items

- Live successful-path outbound execution (an actual authorized Meta send completing against a
  live production conversation) was deliberately never exercised in any N-5/N-6 gate, per the
  locked no-real-message safety rule — covered instead by the 32/32 dedicated security tests
  under mocked/stripped credentials.
- The N-6 manager/report dropdown click-through was not completed live (see N-6 above); the
  underlying backend rule was independently verified live in N-5.
- Other N-0-identified gaps (Campaigns CRUD/send, `dial_queue`, unrestricted Automations,
  unrestricted API-Keys, unauthenticated `/uploads` static mount) remain untouched and out of
  scope for this release — tracked separately, not implied to be fixed here.

### Release status

```
STATUS:                        CLOSED / LIVE / DOCUMENTED
Production backend release:    a1ab52f (live on Render)
Production frontend release:   a1ab52f build, deployed to Hostinger crm_html
Security verification:         PASS (802/802 automated; safe production smoke verified;
                                live outbound-conversation execution deliberately deferred)
Production data integrity:     VERIFIED (zero real records modified, zero real messages sent)
Cleanup:                       COMPLETE (zero synthetic artifacts remaining)
No known regression:           VERIFIED by the recorded regression/smoke checks
```

---

## Release Checkpoint: Campaigns Access Control (2026-09-18)

### Background

A post-WhatsApp-release re-audit (N-10, discovery only) independently re-confirmed the N-0
finding that Campaigns had zero access-control scoping: `campaigns.created_by` existed but no
route ever read it back, so any authenticated employee could list/get/update/delete/send any
other employee's campaign, and `POST /api/campaigns/{id}/recipients` would attach an arbitrary
Lead/Contact id — including one the caller could not see — to any campaign with no visibility
check at all (the campaign-recipient IDOR).

### N-11 — Implementation

`backend/main.py` updated to reuse the existing `access_control.py` model (`created_by →
users.id`, creator-only visibility, same pattern as Quotations — campaigns have no assignee
column):
- `GET /api/campaigns`: SQL-scoped via `scope_filter_sql`.
- `PUT`/`DELETE /api/campaigns/{id}`: restructured to check-then-write. Fixed two real
  pre-existing bugs as a byproduct: `update_campaign` previously wrote first and only discovered
  a nonexistent id afterward (write-before-check); `delete_campaign` had no check at all, not
  even existence.
- `POST /api/campaigns/{id}/send`: authorization checked immediately after fetching the
  campaign — before the message-content validation, before fetching recipients, before any
  Email/WhatsApp/SMS call — mirroring the authorize-before-external-call ordering established
  for WhatsApp (N-2).
- `POST/GET/DELETE /api/campaigns/{id}/recipients`: campaign visibility now checked on all
  three; the IDOR itself closed by checking each supplied Lead/Contact's own
  `created_by`/`assigned_team_member_id` before attaching it — a nonexistent id is rejected
  identically to a real-but-invisible one, so the endpoint never confirms existence. Rejected
  targets are folded into the pre-existing `skipped` counter rather than a new response key, to
  avoid changing the response contract other tests already assert on exactly.
- Cross-entity redaction added to `get_campaign_recipients` (lead/contact name, phone, email
  nulled when the underlying record isn't visible to the viewer) as defense-in-depth for
  historical/edge-case data; `send_campaign`'s internal reuse of the same row-conversion helper
  deliberately skips redaction so the real send path is unaffected.
- One authorized deviation from the original scope: `GET /api/campaigns/{id}` (a single-record
  GET) does not exist in this codebase and was not invented — only list/update/delete/send take
  an id.

New test file `backend/tests/test_campaigns_visibility_security.py`: 24 tests covering the full
visibility matrix, unauthorized write/send denial with confirmed no-mutation, the recipient
IDOR (hidden Lead/Contact rejected, nonexistent id treated identically, mixed visible/invisible
targets), cross-entity redaction, and recipient-removal ownership boundaries.

**Validation:** 24/24 new tests, 48/48 targeted regression (`test_campaigns.py`,
`test_marketing_leads_contacts_link.py`, `test_activities_leads_contacts_link.py`,
`test_activity_feed_visibility_security.py`, `test_whatsapp.py`), **826/826 full backend suite**
(802 baseline + 24 new). `git diff --check` clean. No changes to `access_control.py` or any
schema (`campaigns.created_by` already existed).

### N-12 — Commit

`7720984540c2cfa185503af5ece38c81fe6e16fa` — `feat(security): secure Campaigns access control`.
Exactly 2 files: `backend/main.py`, `backend/tests/test_campaigns_visibility_security.py` (new).

### N-13 — Push (isolated)

Local `master` had accumulated unrelated parallel JARVIS commits and a merge commit ahead of
`origin/master` by the time of this gate. Rather than push local `master` directly (which would
have carried that unrelated history to the shared remote), the same isolation technique used for
the WhatsApp docs release (N-9) was reused: a temporary branch created from `origin/master`
(`git worktree`, not a checkout of the main working directory), the N-12 commit cherry-picked
onto it alone, verified to contain exactly the 2 Campaigns files and none of the JARVIS/merge
commits, then pushed directly to `origin/master` via an explicit `branch:master` refspec.
Resulting isolated commit: `958ff1f7297ba27ac2ee51ef953851212d12dba4` (same content as
`7720984`, different hash as a cherry-pick object). `origin/master` confirmed
`5db83f8 → 958ff1f`, zero unrelated commits transmitted. Local parallel JARVIS work was left
completely untouched throughout.

### N-14 — Production deployment

**Important precision:** the Campaigns security code went live as part of commit `4a1f245`
("Merge origin/master (Campaigns access-control release) into local ..."), **not** because
`958ff1f` itself became the deployed commit. Sequence: the local JARVIS-work session
independently merged `origin/master` (at `958ff1f`) into its own local branch and pushed that
merge to `origin/master` as `4a1f245` — an action taken outside this release's own gates, not by
this session.

A dedicated audit (N-14A, discovery only) confirmed this was safe to treat as a deploy rather
than a blocker: the diff from `958ff1f` to `4a1f245` touches only `jarvis/*` files and
`JARVIS_SCOPE_AND_ROADMAP.md` — zero `backend/`/`frontend/`/dependency/deployment-config
changes. `backend/main.py` has no import of `jarvis` anywhere, and `jarvis` is not in
`backend/requirements.txt`.

Render's Root Directory is configured as `backend` — Render's own documented behavior is that
"code changes outside of this directory do not trigger an auto-deploy," which explains the full
observed sequence: the pure docs-only push (`5db83f8`, N-9) correctly did not redeploy (its only
change was outside `backend/`); the later push to `4a1f245` did redeploy, because its cumulative
diff since the last deployed commit (`a1ab52f`) included `958ff1f`'s changes to
`backend/main.py` — Render deployed the resulting tip commit as a whole, carrying the unrelated
JARVIS files along without them individually mattering. JARVIS code is present in the deployed
commit's checkout but remains unwired into the running FastAPI application.

Confirmed live: Render dashboard showed commit `4a1f245`, status Live, trigger Auto-Deploy,
deployed via the push above. `/api/health` → 200 OK, database connected. CRM frontend and the
separate marketing site both confirmed responding normally.

### N-15 — Production smoke test

**Result: PASS, 14/14 checks.** Performed against a synthetic 5-account hierarchy (2 admins, 1
manager, 2 reports, mirroring the real Nimita/Yogesh/Samiksha/Chirag/Amol shape, never the real
accounts), created via the app's own authenticated API on live production.

Verified live: admin sees all 3 test campaigns; manager sees own + both reports'; each report
sees only their own; unauthorized update/delete/send all correctly 403 with confirmed
no-mutation; the campaign-recipient IDOR fix confirmed live (attaching a peer's hidden Lead
correctly rejected — `added:0, skipped:1` — while attaching one's own Lead succeeded); recipient
list correctly excluded the rejected Lead; unauthorized recipient GET and cross-boundary
recipient removal both correctly 403; authorized send correctly passed authorization (200, not
403) on a zero-recipient campaign, safely terminating at "No pending recipients to send to" with
`sent:0` — proving the authorization boundary without ever reaching the per-recipient send loop
or any external Email/WhatsApp/SMS call; manager's cross-report send authorization confirmed
the same way.

**Zero real Email/WhatsApp/SMS sent at any point.** Cleanup: all 5 synthetic users, 3 team
members, 3 test campaigns, and 2 test leads removed via the app's own authenticated API,
independently re-verified at zero remaining; real admin roster (`nimita`, `testuser`, `yogesh`)
confirmed intact throughout.

### Final access-control model addition (this release)

- **Campaigns** (this release): creator-only visibility (`campaigns.created_by`), same pattern
  as Quotations. `campaign_recipients` attachment now requires the target Lead/Contact be
  visible to the caller, independent of campaign visibility — campaign ownership alone was the
  documented gap, not sufficient authorization to attach an arbitrary person.

### Known intentionally out-of-scope items (not implied to be fixed by this release)

- `dial_queue`, unrestricted Automations, unrestricted API-Keys, and the unauthenticated
  `/uploads` static mount remain untouched — tracked separately from the N-10 audit, not implied
  safe or fixed here.
- The N-6 WhatsApp frontend dropdown click-through gap and the Connect CRM-link
  existence-oracle nuance (both noted in the prior checkpoint) remain outstanding, unrelated to
  this release.

### Release status

```
STATUS:                        CLOSED / LIVE / DOCUMENTED
Production backend release:    4a1f245 (live on Render; contains 958ff1f's Campaigns fix,
                                deployed as part of a cumulative push, not deployed standalone)
Security verification:         PASS (826/826 automated; live production smoke 14/14 PASS)
Production data integrity:     VERIFIED (zero real records modified, zero real messages sent)
Cleanup:                       COMPLETE (zero synthetic artifacts remaining)
No known regression:           VERIFIED by the recorded regression/smoke checks
```

---

## Next up: 2B (CRM-linked chat)

Not started. Requires its own scoped plan-and-verify pass before any implementation begins, per
the standing "one checkpoint at a time" discipline. Do not begin without explicit authorization.
