---
name: cross-sell-radar
description: Finds clients who have one product line with this business but not another - a loan client with no insurance, an insurance client with no MF investment, etc. The single highest revenue-per-hour activity available, since these are warm relationships, not cold leads. Trigger phrases - "cross-sell", "who should I cross-sell to", "cross-sell radar", "upsell opportunities".
---

# Cross-Sell Radar

The same person is often a candidate for more than one of Mutual Funds, Insurance, and Loans - and selling a second product to an existing client is far higher-probability than acquiring a new one. Nothing in the CRM surfaces this automatically today; this skill builds that view from data that's already there.

## How each vertical shows up in the CRM (there's no single "product" field spanning all three)

- **Loans**: `GET /api/deals` - `loan_product` (LAP/Home/Business/Project/OD/CC) tells you someone has an active or past loan relationship.
- **Insurance**: `GET /api/insurance-policies?contact_id=` - the real per-policy table now; a contact with any `status = 'Active'` row is a current policyholder, and `policy_type` tells you which lines they're covered on (a Health policy but no Life policy is itself a flaggable gap). Cross-check `GET /api/contacts/renewals` too, since older data may only exist in the legacy `contacts.renewal_date`/`amount` fields if it predates this table.
- **Mutual Funds**: `GET /api/mf-holdings?contact_id=` - any row with `status = 'Active'` means a current MF relationship; `fund_category`/`goal` tell you what kind. If nothing's recorded for a client, that's itself useful information (either they're not an MF client, or the relationship simply hasn't been logged yet via `client-portfolio-entry`) - say which, don't assume "no MF investment."

## Workflow

1. Pull contacts, leads, and deals. For each unique person (match by phone/email across contacts and deals' linked leads), determine which of the three product lines they show signal for.
2. Flag anyone with **exactly one or two** of the three lines - a full three-for-three client has nothing to cross-sell into (celebrate them, don't pester them); a zero-signal contact may just be a name in the system with nothing established yet, not a cross-sell target.
3. Rank by what's missing, weighted by what's most contextually sensible to offer next: a loan client is a natural insurance conversation (loan protection, and they're already trusting you with a large financial decision); an insurance client with disposable income signals (higher premium/sum assured) is a natural SIP conversation.
4. For each flagged person, give a **specific, real reason**, not a generic "consider offering X" - "Rajesh has a ₹15L business loan with us but no insurance on file - worth a loan-protection conversation" is useful, "cross-sell insurance to Rajesh" is not.
5. Hand off: ready to call → `telecalling`; want market context to pitch a specific product → `mf-research`/`insurance-research`/`loan-research`.

## Guardrail

This surfaces opportunity, it doesn't pitch anything itself and never contacts a client directly - always a list handed to a human to act on. Don't flag someone as a cross-sell target based on incomplete data with false confidence - if the MF signal is genuinely just "nothing recorded," say that's what it is, not "no MF investment."
