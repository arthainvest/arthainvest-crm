---
name: impeccable
description: Final quality/compliance pass before something goes out - a loan case to a lender, a quotation to a client, an email/WhatsApp draft, or any customer-facing document. Catches errors and gaps before they leave the building, not after. Trigger phrases - "impeccable check", "review before sending", "double-check this", "is this ready to send".
---

# Impeccable

A last-look gate, not a first-draft tool - run this on something that's *about* to go out, right before it goes out. It doesn't write the thing; it catches what's wrong with it.

## What it can be run on

1. **A loan case going to the lender** - pull the deal (`GET /api/deals`, filtered to the id), cross-check that `loan-documents`' checklist is actually complete and `credit-manager`'s pre-screen has been done (check custom fields for existing notes from either) - don't redo their work, just confirm it happened and nothing's fallen through since.
2. **A quotation** - `GET /api/quotations/{id}` before `POST /api/quotations/{id}/send`. Check: correct client name and contact linked, line items sum correctly to `grand_total`, no placeholder text (`[Name]`, `TODO`, `XXX`, `Lorem ipsum`) left in, `valid_until` is a real future date, and the loan/product details match what the linked deal actually says - a quotation citing a different loan amount than the deal is the single most embarrassing thing to send.
3. **An email/WhatsApp draft** (via `communication-log` context, or a draft handed to this skill directly) - correct recipient name used in the greeting (not a leftover template name), no unresolved merge fields, professional tone consistent with prior sends to that contact, and factual claims in it actually match what's in the CRM for that lead/deal.
4. **Any general document** - typos, internal consistency (a number stated twice that doesn't match itself), and whether it actually says what the sender thinks it says.

## Workflow

1. Ask what's being checked and pull it in full - don't skim, actually read every line/field.
2. Check facts against the CRM, not against what the user tells you the facts are - if the user says "the loan amount is 50L" but the linked deal says 45L, flag the discrepancy, don't silently trust either side.
3. Report as a pass/fail-per-item checklist, not prose - "✓ Client name correct / ✗ Line 3 says ₹45L, deal record says ₹50L / ✓ No placeholder text" - so the person can act on it in seconds.
4. If everything passes, say so plainly - don't manufacture a nitpick just to seem thorough.
5. Never send/submit anything itself - it reports what to fix, the human sends it.

## Guardrail

This is a checklist, not a rewrite tool - if something's wrong, name exactly what and where, don't silently "fix" the customer-facing content yourself.
