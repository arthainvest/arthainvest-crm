---
name: telecalling
description: Build today's call list, place calls through the CRM's click-to-call dialer (Exotel/Twilio), and log outcomes. Trigger phrases - "who should I call today", "prep my call list", "call this lead", "log this call", "telecalling".
---

# Telecalling

Covers the full loop: who to call, placing the call, and logging what happened - not just a script generator.

## Data access

- Call list source: `GET https://arthainvest-crm.onrender.com/api/leads?token=<token>&status=New` (fresh leads needing a first call) and `GET /api/today` / task endpoints for anything explicitly scheduled as a follow-up call today.
- Place a call: `POST /api/calls/dial {"to": "<customer phone>", "lead_id": <id>}` (or `contact_id`). This rings the agent's own saved phone first (Settings → phone number must already be set), then bridges to the customer - it does not dial the customer directly. If `configured: false` comes back, no provider (Exotel/Twilio) is set up, or the agent hasn't saved their own number yet - tell the user which, don't retry silently.
- Log a call manually (e.g. one placed outside the CRM dialer): `POST /api/calls {"name": "...", "phone": "...", "duration_seconds": N, "type": "Outbound", "outcome": "...", "lead_id": <id> or "contact_id": <id>}`.
- Existing call history: `GET /api/calls`.

## Workflow

1. **Build the list.** Combine explicit today-scheduled follow-ups with fresh `status=New` leads. If `loan-prospecting` already produced a ranked list, use that instead of rebuilding one. Respect capacity (see business profile memory) - a shorter list that gets fully worked beats a long one that doesn't.
2. **Before dialing**, confirm the agent's own phone is saved in Settings - if not, say so and stop; `/api/calls/dial` will fail without it.
3. **Place the call** via `POST /api/calls/dial`. This is a real outbound call to a real customer - always confirm the number and the person's name with the user before dialing, never dial from an unconfirmed or guessed number.
4. **After the call**, log the outcome if it wasn't auto-logged by the dial (`call_id` in the dial response means it was) - `outcome` should be specific enough to act on later: "Interested, wants LAP details," "No answer, retry evening," "Not interested," "Wrong number," not just "Called."
5. **Route the outcome**: interested + loan-fit → hand to `loan-documents` to start the checklist, or create a deal via `POST /api/deals`; no answer → note for a retry, don't lose it; not interested → update lead status so it stops showing as "New."

## Call opener by loan product

Keep it short - the goal of a first call is qualifying interest, not a full pitch:

- **LAP/Home**: "Are you looking to raise funds against property, or is this for a new home purchase?"
- **Business/Project/OD/CC**: "What's the funding for - working capital, expansion, or a specific project?" - this alone usually reveals the right product.

## Guardrails

Never fabricate a call outcome or duration that wasn't actually observed. Never place a call to a number the user hasn't confirmed. This is a real telephony action with a real cost per Exotel/Twilio minute - don't dial speculatively "just to test."
