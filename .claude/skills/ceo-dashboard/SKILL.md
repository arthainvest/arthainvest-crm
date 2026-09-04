---
name: ceo-dashboard
description: Executive briefing for the business owner/admin - company-wide pipeline health, team performance by name, and what actually needs their attention this week. Admin-only (see Access note). Trigger phrases - "CEO dashboard", "business overview", "how's the business doing", "owner briefing", "admin dashboard".
---

# CEO Dashboard

An executive briefing, not a data dump - the point is "here's what needs your attention," synthesized from the same live data the app's own Dashboard/Reports pages show, plus per-employee performance the regular Dashboard doesn't surface.

## Access note (read before running)

This skill shows **individual employees' names against their call/conversion numbers** - that's exactly the kind of visibility that should stay with the owner/admin, not spread to the team. **Before running this, confirm the person asking is actually the admin/owner** (Nimita, Yogesh, or the account owner) - if a non-admin account is asking for this, decline and point them to `sales-intelligence` instead, which is the self-scoped version everyone should have.

This is a policy the assistant enforces, not something the CRM's backend enforces today - the API itself doesn't check role before returning this data (see the earlier security notes on this project), so this check has to happen here.

## Data sources

- `GET /api/analytics/dashboard` - leads/deals/contacts counts, pipeline value, loan-stage breakdown, lead-status funnel.
- `GET /api/analytics/sales` - total revenue (closed deal value), win rate, avg deal value.
- `GET /api/analytics/conversion-rate` - lead-to-deal conversion.
- `GET /api/analytics/team` - per-team-member productivity (`TeamProductivityRow`).
- `GET /api/analytics/calls/by-employee` - who called how many people today/this week/this month, and how many actually connected.
- `GET /api/analytics/lead-sources` - which sources are producing real pipeline value, not just lead count.
- Business context: the `arthainvest-business-profile.md` memory (capacity constraint, current products/licenses) - the numbers mean nothing without knowing this is a solo/part-time operation where capacity, not lead volume, is usually the real constraint.
- **Real revenue across all three product lines** (mutual fund trail, insurance commission, loan payout) lives in `commission-tracking`, not the endpoints above - but that skill is restricted to the Nimita account specifically, stricter than this skill's own admin-general access. Only pull it in if the person running this dashboard is confirmed to be Nimita; for Yogesh or any other admin, this dashboard's revenue picture stays limited to `deal_value`/win-rate, and say so plainly rather than silently omitting it.

## Workflow

1. Pull all the endpoints above in one pass.
2. Lead with the **one or two things that actually need a decision** this week - a stuck pipeline stage, an employee whose calls aren't converting, a lead source quietly outperforming the others, a capacity ceiling being hit. Don't lead with a wall of numbers.
3. Team section: name each person, their call volume and connect rate, and how their assigned deals are trending - factual, not evaluative language ("12 calls, 4 connected, 1 moved to Sanction" not "underperforming").
4. Close with pipeline value by loan stage (matches the app's own Loan Pipeline widget - don't recompute a different number) and this week's disbursement-stage deals specifically, since those are closest to actual revenue.
5. Offer to hand any flagged item to the right skill: stuck documents → `loan-documents`, a person's numbers looking off → `sales-intelligence` (run for that person, with them), a stalled lead source → `loan-prospecting`.

## Tone

Direct and short. This is for someone with limited time reading a business briefing, not a report to be admired.
