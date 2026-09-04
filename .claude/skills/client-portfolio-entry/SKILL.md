---
name: client-portfolio-entry
description: Captures a client's mutual fund holdings and insurance policies into the real mf_holdings/insurance_policies tables - the data-entry side that sip-tracking, folio-review, insurance-lapse-prevention, and cross-sell-radar all depend on. Trigger phrases - "add a fund for this client", "log this policy", "record their SIP", "add an insurance policy", "capture their portfolio".
---

# Client Portfolio Entry

The write side of the MF/insurance tracking system - `sip-tracking`, `folio-review`, and `insurance-lapse-prevention` are all read-only against `mf_holdings`/`insurance_policies`; this is what actually puts data in those tables, one client at a time or from a documents/notes handoff after a meeting.

## Data model

**`mf_holdings`** - one row per fund a client holds:
`POST /api/mf-holdings` with `{contact_id, fund_name, folio_number?, fund_category?, investment_type ("SIP"/"Lumpsum"/"SWP"), amount?, frequency?, next_due_date?, status ("Active"/"Paused"/"Stopped"/"Redeemed"), start_date?, goal?, notes?}`.
Update an existing row (a SIP amount changed, a fund switched status, a client paused) via `PUT /api/mf-holdings/{id}` - never create a duplicate row for the same fund just because a detail changed.

**`insurance_policies`** - one row per policy a client holds:
`POST /api/insurance-policies` with `{contact_id, policy_type ("Health"/"Life"/"Motor"/"Term"/"ULIP"/"Other"), policy_number?, insurer?, sum_assured?, premium_amount?, premium_frequency?, start_date?, renewal_date?, status ("Active"/"Lapsed"/"Renewed"/"Cancelled"/"Matured"/"Claimed"), notes?}`.
Update via `PUT /api/insurance-policies/{id}` for renewals, status changes, or corrections - same rule, one policy is one row across its whole lifecycle.

Both require a real `contact_id` - if the client isn't in Contacts yet, create them first (`POST /api/contacts`) rather than inventing a placeholder.

## Workflow

1. **From a client conversation/meeting**: capture what was discussed directly - fund name, SIP amount, policy type and premium, whatever's concrete. Don't wait to batch it later; a detail not written down within the session tends to get lost.
2. **From existing paperwork/notes not yet in the CRM**: this is a backfill - check `GET /api/mf-holdings?contact_id=` / `GET /api/insurance-policies?contact_id=` first to avoid creating a duplicate of something already recorded.
3. **Before creating**, confirm the contact exists and is the right one (search by name/phone, don't assume a match) - a holding attached to the wrong contact is worse than not recording it at all, since it'll surface in the wrong person's `folio-review`/`cross-sell-radar` results.
4. **Field discipline**: leave a field blank rather than guessing a plausible-looking number - `sip-tracking`'s missed-payment detection and `insurance-lapse-prevention`'s chase cadence both depend on `next_due_date`/`renewal_date` being real dates that were actually confirmed, not filled-in placeholders.
5. After entering, mention what's now trackable as a result - "Rajesh's Parag Parikh SIP is now in the system, `sip-tracking` will flag it if a payment's missed" - so whoever's using this knows it actually took effect, not just that a form was submitted.

## Guardrail

Only record what's actually known/confirmed. A missing `renewal_date` that gets flagged as "needs follow-up" is far better than a guessed date that silently produces a wrong lapse-prevention chase later.
