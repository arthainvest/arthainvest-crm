---
name: sip-tracking
description: Tracks each client's SIP - amount, next due date, missed payments, top-up opportunities. No dedicated schema exists for this yet, so it runs on custom fields until usage proves out a real table is worth building. Trigger phrases - "SIP tracking", "who's due for SIP", "SIP status", "missed SIP payments".
---

# SIP Tracking

Mutual funds have zero dedicated schema in this CRM today (unlike loans, which have `deal_value`/`loan_product`, or insurance, which has `renewal_date`/`amount` on Contacts). This skill runs on the CRM's existing custom-fields mechanism as a first version - real, usable now, without needing a backend migration first.

## Data model (custom fields, until real usage justifies a dedicated table)

Check `GET /api/custom-fields` for what's already defined before creating new ones - don't create a near-duplicate field with a slightly different name. If these don't exist yet, create them (`POST /api/custom-fields`, `entity_type: "contact"`):
- `SIP Amount` - the monthly SIP value.
- `SIP Fund Name` - which fund(s); if multiple, list them together rather than trying to model one-fund-per-field.
- `Next SIP Date` - when the next debit is expected.
- `SIP Status` - Active / Paused / Stopped.

Set/read values via `PUT /api/custom-fields/value` and `GET /api/custom-fields/for/contact/{id}`.

## Workflow

1. **Status check**: pull all contacts, check their custom field values for the SIP fields above. A contact with `SIP Status = Active` but a `Next SIP Date` more than ~35 days in the past (a month plus grace) likely missed a payment - flag it, don't assume, since the field could just be stale rather than the SIP actually having failed.
2. **Missed-payment chase**: for anyone flagged, this is a client-retention issue, not a sales one - hand off to `telecalling` with context "SIP appears to have missed a cycle" rather than a generic call reason.
3. **Top-up opportunity**: if asked to find candidates for a SIP increase, look for clients whose SIP amount hasn't changed in a long time relative to when it was set (check the custom field's own history isn't tracked here - so use `created_at`/`updated_at` on the contact as a rough proxy, and be upfront that it's approximate) alongside any income-growth signal available (e.g. recently closed a large loan, suggesting improved cash flow).
4. If a client has genuinely never had a SIP tracked, don't fabricate a status - say clearly that nothing is recorded, and treat that either as a data gap to fill or a `cross-sell-radar` candidate.

## What this skill does NOT do

Doesn't verify against the actual AMC/RTA (registrar) records - see `mf-research`'s MF Central reference for that. This tracks what's recorded in the CRM, which is only as current as the last time someone updated it.
