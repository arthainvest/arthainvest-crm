---
name: folio-review
description: Client-by-client mutual fund portfolio review - what they hold, how it's allocated, whether it still fits their goal. Uses custom fields for folio data plus the financial-calculators/mf-research skills for the actual analysis. Trigger phrases - "folio review", "portfolio review", "review this client's funds".
---

# Folio Review

The client-facing counterpart to `sip-tracking` - not "is the SIP running," but "is this portfolio still right for them."

## Data access

Same custom-fields foundation as `sip-tracking` (`GET /api/custom-fields/for/contact/{id}`) - check for `Folio Number`, `SIP Fund Name`, and any recorded goal/purpose (e.g. a `Goal` custom field, or notes on the contact). If a client's goal was captured anywhere (a note, a custom field, or the `Data Collection Sheet for Making Financial Plans.xlsx` template from `financial-calculators`), pull it - a review without knowing the goal is just a performance readout, not actual advice.

## Workflow

1. Pull what's recorded for the client: funds held, SIP amount(s), and their stated goal if captured anywhere.
2. If fund-level performance/rating context is needed, hand off to `mf-research` (Value Research/Morningstar) rather than asserting a fund's quality from memory - ratings and performance are time-sensitive.
3. Check for the obvious review flags: a fund that's changed category/mandate since it was recommended, a goal timeline that's gotten meaningfully closer (should risk be dialed down?), or an allocation that's drifted from what was originally intended (no rebalancing data is tracked automatically here, so this is a judgment call based on what's on file, not a computed drift percentage).
4. Use `Portfolio and Plan Review Template.xls` or `Annual Review Meeting Checklist.xlsx` (from `financial-calculators`) to structure the actual review output/meeting, rather than freeform.
5. If nothing is on file for a client (`sip-tracking` returns nothing recorded), say that plainly - this becomes a "let's capture your current holdings" conversation, not a review.

## Guardrail

This assembles what's known and flags what to discuss - it doesn't recommend a fund switch or reallocation itself. Fund switching has tax and exit-load implications that need the licensed distributor's own judgment on the specific numbers, not a generated recommendation.
