---
name: sales-intelligence
description: Self-scoped performance intelligence for any team member - your own conversion rate, best lead source, fastest-closing loan product, and what to do differently. Available to every employee, not just admin. Trigger phrases - "how am I doing", "my sales numbers", "sales intelligence", "what's working for me".
---

# Sales Intelligence

The employee-facing counterpart to `ceo-dashboard` - same underlying data, scoped to one person's own numbers so everyone can use it without seeing (or exposing) anyone else's performance.

## Access note

Default to **only the numbers for the person asking** - filter every query by their own `team_member_id`/`assigned_team_member_id`. Only widen to another person's numbers, or a company-wide comparison, if the person asking is confirmed admin (Nimita/Yogesh/owner) - otherwise that's `ceo-dashboard`'s job, not this one. If it's genuinely unclear who's asking, ask rather than assume admin-level access.

## Data sources (filter to the asker's own team_member_id where the endpoint supports it)

- `GET /api/leads?assigned_team_member_id=<id>` and `GET /api/deals` (filter client-side by `assigned_team_member_id`) - their own funnel.
- `GET /api/analytics/calls/by-employee` - filter the response to just their row for call volume/connect rate.
- `GET /api/analytics/lead-sources` - company-wide by source (this one isn't personally filterable since source isn't tied to an owner) - use it to answer "which source should I be asking for more leads from," not as a company financial disclosure; keep it to counts/conversion, not raw deal values, when talking to a non-admin.
- `GET /api/deals` grouped by `loan_product` and `process_status`, scoped to their own deals - which product they close fastest, where their deals tend to stall.

## Workflow

1. Confirm whose numbers this is for (see Access note).
2. Pull their leads/deals/calls, compute: personal conversion rate, calls-to-connect ratio, which loan product they're winning most often, and where in the pipeline their deals typically stall.
3. Compare against what's realistically achievable given the business's capacity constraint (see business profile memory) rather than against a made-up benchmark.
4. Give 2-3 concrete, specific suggestions - not generic sales advice. "Your LAP calls connect at 40% but Business calls at 15% - lead with LAP when you have a choice" is useful; "improve your pitch" is not.
5. Offer hand-offs: more prospects to call → `loan-prospecting`; deals stuck in one stage → `loan-documents`; ready to place calls → `telecalling`.

## Tone

Coaching, not grading. This exists to help someone sell more, not to be used as a performance review against them.
