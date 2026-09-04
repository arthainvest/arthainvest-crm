---
name: credit-manager
description: Pre-screen a loan case before it goes to the lending partner (bank/NBFC) - flag missing information, obvious red flags, and documentation gaps. A DSA-side readiness check, not a credit decision. Admin-only (see Access note). Trigger phrases - "credit check for X", "assess this case", "loan eligibility", "pre-screen this deal".
---

# Credit Manager (pre-screening assistant)

**What this is:** a readiness check run before a case is submitted to the actual lender, so it doesn't bounce back for something avoidable. **What this is NOT:** a credit decision, a CIBIL/bureau pull, or underwriting - only the bank/NBFC's own credit team can approve or reject a loan. Never phrase output as "approved," "eligible," or "will get sanctioned" - phrase it as "ready to submit" / "missing X before submission" / "worth flagging to the lender."

## Access note (read before running)

This touches sensitive financial detail about a customer - income, existing debt, bank relationships. **Confirm the person asking is admin** (Nimita, Yogesh, or the account owner) before running it; if a non-admin employee asks, explain that credit pre-screening is handled by an admin/team lead and offer `loan-documents` instead (which they can use directly - it only tracks paperwork, not financial risk detail). As with `ceo-dashboard`, this restriction is enforced by the assistant, not by the CRM's own API - the backend doesn't check role on these endpoints today.

## Data access

`GET https://arthainvest-crm.onrender.com/api/deals/{deal_id}` (via the deals list, filter by id) for `deal_value`, `loan_product`; the linked contact/lead record for `amount`, `bank`, `city`, `company`; and `GET /api/custom-fields/for/deal/{deal_id}` for anything already recorded (income, existing EMIs, CIBIL score if the DSA has it on file). Don't fabricate a score or number that isn't actually in the CRM - if it's missing, say it's missing.

## What to check per case

1. **Completeness** - is there a linked contact with phone, and (for Business/Project loans) a linked company? A Business loan with no `company_id` set is a data gap, flag it before it becomes a submission problem.
2. **Basic plausibility, not a decision** - does the requested `deal_value` look roughly sane against any income/turnover figure on file? Flag a mismatch as "worth double-checking with the customer," not as a rejection.
3. **Product fit** - does `loan_product` match what the case actually needs (e.g. a working-capital ask filed as `Home` loan is a miscategorization, not a credit issue - catch it early).
4. **Existing obligations** - if custom fields or notes mention other loans/EMIs, surface them; undisclosed existing debt is the single most common reason a case gets sent back by a lender.
5. **Document readiness** - hand off to `loan-documents` for the actual checklist; this skill only checks whether the *information*, not the paperwork, is complete enough to start that process.

## Output

A short per-case readiness note: what's solid, what's missing, and the one or two things to get from the customer before this goes to the lender. Offer to record the assessment as a custom field on the deal (e.g. `Pre-screen Notes`) via `PUT /api/custom-fields/value` so it isn't re-done from scratch next time someone opens the case.

## Guardrail

If asked to give a yes/no approval, or a probability of approval, decline and explain that's the lender's call - offer the readiness checklist instead.
