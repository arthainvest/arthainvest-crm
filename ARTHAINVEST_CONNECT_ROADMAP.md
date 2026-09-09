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

## Next up: 2B (CRM-linked chat)

Not started. Requires its own scoped plan-and-verify pass before any implementation begins, per
the standing "one checkpoint at a time" discipline. Do not begin without explicit authorization.
