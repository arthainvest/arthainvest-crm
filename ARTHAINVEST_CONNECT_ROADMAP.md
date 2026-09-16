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

## Next up: 2B (CRM-linked chat)

Not started. Requires its own scoped plan-and-verify pass before any implementation begins, per
the standing "one checkpoint at a time" discipline. Do not begin without explicit authorization.
