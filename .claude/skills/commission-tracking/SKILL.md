---
name: commission-tracking
description: The real revenue ledger across all three product lines (mutual fund trail, insurance commission, loan payout) - what's actually being earned, not just deal/policy size. Restricted to the Nimita account only. Trigger phrases - "commission tracking", "log a commission", "how much did I earn", "revenue by product line".
---

# Commission Tracking

The foundation everything else (`ceo-dashboard`, business planning) reports against. Nothing else in the CRM tracks actual earnings - `deals.deal_value` is the loan/investment size, not what was earned on it; insurance premiums and MF trail have no home in the schema at all until this.

## Access note (read before running)

This is restricted to the **Nimita account specifically**, not the admin role generally - the backend enforces this itself (`require_nimita()` in main.py checks username, not role), so even Yogesh's admin login gets a 403. If someone other than Nimita asks for this, tell them plainly it's restricted to that account and stop - don't work around it via another endpoint.

## Data access

- `GET /api/commissions` - full ledger, optionally `?product_type=mutual_fund|insurance|loan`.
- `POST /api/commissions` - log a new entry: `{product_type, description, amount, received_date, contact_id?, lead_id?, deal_id?, notes?}`. Link to the actual contact/lead/deal when there is one - an unlinked entry ("SIP trail, October batch, ₹4,200") is fine when the payout covers many clients at once and isn't worth splitting.
- `GET /api/commissions/summary` - totals grouped by product line, optionally `?start_date=&end_date=` (ISO dates).
- `DELETE /api/commissions/{id}` - remove a mis-entered record.

## Workflow

1. **Logging an entry**: get product_type (must be exactly `mutual_fund`, `insurance`, or `loan`), amount, what it's for, and the date received - not the date it was earned/due, the date it actually landed, since that's what makes this a real ledger instead of a wishlist.
2. **Reviewing earnings**: pull the summary for whatever period's being asked about, and always show the per-line breakdown, not just a total - "₹45,000 this month" is far less useful than "₹30k loan payout, ₹10k insurance, ₹5k MF trail," since it shows which line is actually carrying the business right now.
3. **Trend awareness**: if asked "how am I doing," compare this period's summary against the prior one (same skill, different date range) rather than just reporting a static number - growth or decline by product line is the actually actionable signal.
4. Never estimate or guess a figure that isn't in the ledger - if commission for a period looks incomplete (e.g. a known closed loan with no matching entry), say so and offer to log it, don't extrapolate one.

## What this skill does NOT do

Doesn't compute commission automatically from deal_value or policy premium - commission structures vary by lender/insurer/AMC and aren't modeled anywhere in the CRM, so every entry is logged from what was actually paid, not calculated.
