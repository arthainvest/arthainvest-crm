---
name: sip-tracking
description: Tracks each client's SIP - amount, next due date, missed payments, top-up opportunities. Runs on a real mf_holdings table (one row per fund per client), not custom fields. Trigger phrases - "SIP tracking", "who's due for SIP", "SIP status", "missed SIP payments".
---

# SIP Tracking

Backed by the `mf_holdings` table - one row per fund a client holds, so a client with 3 SIPs shows as 3 rows, not squeezed into a single custom field. To capture new holdings data in the first place, use `client-portfolio-entry`; this skill is the read/analysis side.

## Data access

- `GET /api/mf-holdings?contact_id=` - a specific client's holdings.
- `GET /api/mf-holdings?status=Active` - everyone's active holdings.
- `GET /api/mf-holdings/due-soon` - active SIPs overdue or due within 7 days, already computed server-side (don't recompute the date math client-side).
- `PUT /api/mf-holdings/{id}` - update status, amount, next_due_date etc. as things change (a missed-then-caught-up SIP, a stopped SIP, a top-up).

## Workflow

1. **Status check**: `GET /api/mf-holdings/due-soon` is the direct answer to "who's due" - it already filters to Active + overdue-or-within-7-days. Don't hand-roll a date comparison across the full list.
2. **Missed-payment chase**: anything overdue in that list is a client-retention issue, not a sales one - hand off to `telecalling` with context "SIP appears to have missed a cycle," and once contacted, update the holding's status/next_due_date to reflect what was learned rather than leaving it stale.
3. **Top-up opportunity**: look for clients whose SIP `amount` hasn't changed relative to `start_date`/`updated_at` (both real columns now, not an approximation), alongside any income-growth signal available (e.g. a recently closed large loan, suggesting improved cash flow).
4. If a client has genuinely no holdings recorded (`GET /api/mf-holdings?contact_id=` returns empty), say that plainly - it's either a data gap (hand off to `client-portfolio-entry`) or a real `cross-sell-radar` candidate, not an assumed "no SIP."
5. When a SIP's details change (paused, amount changed, fund switched), update the row via `PUT /api/mf-holdings/{id}` rather than creating a duplicate - one fund is one row across its lifetime, status changes, it doesn't get re-created.

## What this skill does NOT do

Doesn't verify against the actual AMC/RTA (registrar) records - see `mf-research`'s MF Central reference for that. This tracks what's recorded in the CRM, only as current as the last update.
