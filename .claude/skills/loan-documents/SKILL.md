---
name: loan-documents
description: Track and chase the loan document checklist for a deal - what's collected, what's pending, and who to nudge. Maps directly to the CRM's Pipeline process_status stages. Trigger phrases - "what documents are pending for X", "document checklist", "chase documents", "loan documents status".
---

# Loan Documents

The CRM's deal `process_status` already encodes the document/underwriting lifecycle:
`Document Collection` → `Login` → `Under Verification` → `Approved` → `Sanction` → `Disbursement Pending` → `Disbursed` (or `Hold` / `Rejected` / `Closed - Lost` at any point).

A deal sitting in `Document Collection` for a long time is a paperwork bottleneck, not a sales problem - this skill exists to catch that.

## Data access

`GET https://arthainvest-crm.onrender.com/api/deals?token=<token>` returns every deal with `process_status`, `loan_product`, `deal_value`, `updated_at`, and the linked contact/lead/company. Update status with `PUT /api/deals/{deal_id}/process-status`.

Custom fields (`GET/PUT /api/custom-fields/...`, `entity_type=deal`) are where per-document checklist state should live - e.g. a field named `Documents Pending` holding a comma-separated list, or one boolean-ish field per document if the list is short. Check `GET /api/custom-fields` first for what already exists before creating new ones; don't create a duplicate field with a slightly different name.

## Standard document checklist by loan product

These are starting points, not fixed - confirm against what the actual lending partner (bank/NBFC) asks for on that specific deal, since requirements vary by lender:

- **LAP / Home**: KYC (PAN, Aadhaar), property title documents, latest 6-month bank statement, income proof (ITR/salary slips), property valuation report.
- **Business**: KYC, GST returns (last 12 months), business bank statements (12 months), audited financials/ITR (2-3 years), business registration proof.
- **Project**: everything Business needs, plus the project report/DPR, cost estimates, and any existing approvals (environmental/municipal) relevant to the project.
- **OD / CC**: KYC, bank statements (12 months), financial statements, existing facility letters if renewing/switching.

## Workflow

1. Pull deals, filter to `process_status = "Document Collection"` (or whichever stage was asked about).
2. For each, check existing custom-field notes for what's already marked collected; if none exist yet, start the checklist for that loan product from the list above.
3. Flag deals where `updated_at` is stale (more than ~5-7 days with no status change is a real stall for a document-collection stage) - these need a chase call before anything else, hand off to `telecalling`.
4. Report per deal: contact name, loan product, days in current stage, documents still outstanding, and the one thing to ask for next.
5. When a document set completes, move the deal forward with `PUT /api/deals/{deal_id}/process-status` rather than leaving status stale after the fact.
