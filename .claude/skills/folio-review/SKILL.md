---
name: folio-review
description: Client-by-client mutual fund portfolio review - what they hold, how it's allocated, whether it still fits their goal. Reads the mf_holdings table, uses financial-calculators/mf-research for the actual analysis. Trigger phrases - "folio review", "portfolio review", "review this client's funds".
---

# Folio Review

The client-facing counterpart to `sip-tracking` - not "is the SIP running," but "is this portfolio still right for them."

## Data access

`GET /api/mf-holdings?contact_id={id}` - every fund the client holds, with `folio_number`, `fund_category`, `investment_type`, `amount`, `goal`, and `status` per row. A client's goal is recorded per-holding (not once per client), since different funds often serve different goals for the same person - pull all their rows and group by `goal` if they have more than one purpose being funded.

## Workflow

1. Pull the client's full holdings list; group by `goal` where set.
2. If fund-level performance/rating context is needed, hand off to `mf-research` (Value Research/Morningstar) rather than asserting a fund's quality from memory - ratings and performance are time-sensitive.
3. Check for the obvious review flags: a fund that's changed category/mandate since it was recommended, a goal timeline that's gotten meaningfully closer (should risk be dialed down?), or an allocation that's drifted from what was originally intended (no rebalancing data is tracked automatically here, so this is a judgment call based on what's on file, not a computed drift percentage).
4. Use `Portfolio and Plan Review Template.xls` or `Annual Review Meeting Checklist.xlsx` (from `financial-calculators`) to structure the actual review output/meeting, rather than freeform.
5. If nothing is on file for a client (`GET /api/mf-holdings?contact_id={id}` returns empty), say that plainly - hand off to `client-portfolio-entry` to capture their current holdings first, this isn't a review yet.

## Guardrail

This assembles what's known and flags what to discuss - it doesn't recommend a fund switch or reallocation itself. Fund switching has tax and exit-load implications that need the licensed distributor's own judgment on the specific numbers, not a generated recommendation.
