---
name: insurance-lapse-prevention
description: A chase sequence for policies approaching renewal, not a single reminder - runs until the premium is actually paid or the client explicitly declines. Upgrades the existing single-shot Upcoming Renewals dashboard widget into an actual retention workflow. Trigger phrases - "renewal chase", "who's about to lapse", "lapse prevention", "renewal follow-up".
---

# Insurance Lapse Prevention

The Dashboard already shows Upcoming Renewals once - this skill is what happens *after* that first reminder doesn't get a response, since a policy lapsing is a real, immediate revenue loss (both the commission and the client relationship), worth more chasing effort than a single dashboard widget provides.

## Data access

`GET /api/contacts/renewals` - the same endpoint behind the Dashboard widget, already filters to contacts with a `renewal_date` coming up and returns `days_until_renewal` and `urgency` (`overdue`/`due_soon`/`upcoming`). Neither `GET /api/calls` nor `GET /api/communication-log` support a contact-id filter server-side (calls only filters by `team_member_id`) - pull the full list and filter client-side by the contact's name/phone to check whether they've already been contacted about this specific renewal.

## Chase cadence (adjust to what's actually realistic given capacity - see business profile memory)

1. **30 days out** (`upcoming`): first reminder - WhatsApp or email, low-pressure, just the renewal date and premium amount.
2. **7 days out** (`due_soon`): second touch, phone call if no response to the first - hand off to `telecalling` with context "renewal due in N days, first reminder unanswered."
3. **Overdue** (`urgency = overdue`): this is now an active lapse risk, not a routine reminder - prioritize above new prospecting for that day; many insurers have a grace period, so check the actual policy terms before assuming it's already lapsed.
4. **Lapsed** (past any grace period with no payment): a genuine win-back conversation, different tone from a renewal reminder - acknowledge the lapse, ask what happened (cost concern, dissatisfaction, just missed it), don't just repeat the same reminder.

## Workflow

1. Pull `/api/contacts/renewals`, bucket by urgency.
2. For each, check whether they've already been contacted this cycle (via calls/communication-log) before sending another touch - a client getting three redundant "your policy is due" messages in one week is worse than one well-timed one.
3. Log every chase attempt (a call via `telecalling`, or a note) so the next check of this skill knows what's already been tried - it should always be answerable "have we already reached out about this one."
4. Escalate `overdue` renewals above routine prospecting work for that session - losing an existing policyholder costs more than the marginal value of one more cold call.
5. For a genuine lapse, after the win-back conversation, this becomes a `cross-sell-radar`-relevant fact too - a client who let insurance lapse is a different risk profile than one who's current.

## Guardrail

Don't send/log a chase message the human hasn't actually reviewed - this plans the cadence and drafts the touch, doesn't autonomously message clients on a schedule.
