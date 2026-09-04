---
name: loan-sales
description: Loan pipeline sales review - which deals are moving, which are stuck, what to do next on each. Works off the CRM's live deal data, not a static report. Trigger phrases - "loan sales pipeline", "pipeline review", "which deals need attention", "sales brief".
---

# Loan Sales

A working pipeline review, not a vanity dashboard - the point is a short list of deals that need a specific next action today.

## Data access

`GET https://arthainvest-crm.onrender.com/api/deals?token=<token>` - every deal, with `stage`, `process_status`, `deal_value`, `loan_product`, `updated_at`, and linked contact/lead/company names. `GET /api/analytics/dashboard` gives the aggregate Loan Pipeline / Pipeline Status breakdown already used on the Dashboard, for a fast top-level number before drilling in.

## Process status stages (in order)

`Document Collection` → `Login` → `Under Verification` → `Approved` → `Sanction` → `Disbursement Pending` → `Disbursed`, with `Hold`, `Rejected`, and `Closed - Lost` as off-ramps at any point. A deal's *stage* (new/qualified/proposal/negotiation/closed) is the sales-cycle view; *process_status* is the loan-processing view - use process_status for anything document/lender-facing, stage for anything sales-pipeline-facing.

## Workflow

1. Pull all open deals (exclude `Closed - Lost`, `Rejected`, `Disbursed`).
2. Sort into three buckets:
   - **Moving well** - status changed recently, no action needed beyond routine follow-up.
   - **Stuck** - `updated_at` stale relative to what's normal for that process_status (a `Document Collection` deal idle 5+ days, or a `Sanction`/`Disbursement Pending` deal idle 2+ days, since those later stages should move fast once paperwork's done). These are the priority.
   - **Near the finish line** - `Sanction` or `Disbursement Pending` - highlight separately since these convert to actual revenue soonest.
3. For each stuck deal, name the specific next action: chase documents (hand off to `loan-documents`), chase the lender for a status update, or re-engage a customer who's gone quiet (hand off to `telecalling`).
4. Report total pipeline value by `process_status` bucket (mirrors the Dashboard's Loan Pipeline widget) so the numbers match what's already visible in the app - don't invent a different rollup.
5. If asked for a written report, keep it scannable: deal / loan product / value / stuck-or-moving / next action. Not prose.

## What this skill does NOT do

Doesn't create or move deals on its own without being asked - surfaces what needs attention and lets the user (or a hand-off to `loan-documents`/`telecalling`/`credit-manager`) act on it.
