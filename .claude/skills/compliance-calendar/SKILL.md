---
name: compliance-calendar
description: Tracks the owner's own regulatory deadlines - ARN renewal, POSP certification, any CPD/exam requirement - as a real, checkable list, not something held in memory. Missing one of these is a bigger risk than any single lost deal, since it can block the ability to legally transact at all. Trigger phrases - "compliance calendar", "when does my ARN renew", "compliance deadlines", "regulatory renewals".
---

# Compliance Calendar

Lower urgency day-to-day than the sales/prospecting skills, but real downside if skipped entirely - an expired ARN or lapsed POSP certification doesn't just cost one deal, it can block every mutual fund or insurance transaction until it's renewed.

## Data model

No dedicated compliance table exists - this uses the CRM's existing Tasks feature (`GET/POST /api/tasks`) with a consistent naming convention rather than a new schema, since compliance items are genuinely just dated to-dos with a higher failure cost, not a structurally different kind of data.

- Create compliance deadlines as tasks titled `[Compliance] <what>` (e.g. `[Compliance] ARN Renewal`, `[Compliance] POSP Certification Renewal`, `[Compliance] CPD Hours Due`) with the real `due_date` and `priority: "High"`.
- To find them later: `GET /api/tasks`, filter client-side for titles starting with `[Compliance]` (there's no title-prefix filter on the endpoint, so pull the full list and filter here).

## What to track (adjust to what actually applies - check with the business's own licenses, don't assume a generic list is complete)

- **ARN renewal** (AMFI Registration Number - the mutual fund distributor license, ARN-267891 per the business profile) - AMFI-set renewal cycle, typically requires a refresher exam/CPE credits beforehand, so the real deadline to track is "start the renewal process," not just the expiry date.
- **POSP certification** - insurance Point-of-Sale-Person status; check the specific insurer's/IRDAI's renewal requirement and cycle.
- **DSA agreement renewal** - loan DSA agreements with individual lenders may have their own renewal/re-KYC cycle, distinct from ARN/POSP.
- **Any CPD/continuing-education hours** required to keep a license active.

## Workflow

1. When setting up or reviewing the calendar, pull existing `[Compliance]`-tagged tasks first - don't create duplicates for something already tracked.
2. For a genuinely new deadline, create it as a task with real lead time before the actual expiry (e.g. 45 days out, not the expiry date itself), since most of these have a renewal *process* that takes time, not a same-day action.
3. When asked "what's coming up," filter to `[Compliance]` tasks and sort by due date - treat anything within 30 days as needing action this week, not just "on the list."
4. If a compliance deadline is genuinely unknown (e.g. exact ARN renewal cycle isn't recorded anywhere), say so plainly and suggest verifying with AMFI/IRDAI directly rather than guessing a date.

## Guardrail

Never fabricate a compliance deadline that hasn't been confirmed with the actual regulator/license terms - an invented "renewal due" date is worse than no reminder at all, since it creates false confidence. If unsure, say to verify with AMFI/IRDAI/the specific insurer rather than presenting a guess as fact.
