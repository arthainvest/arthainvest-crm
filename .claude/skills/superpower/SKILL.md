---
name: superpower
description: The one-command daily kickoff - chains pipeline review, prospecting, and document-chasing into a single morning routine, scoped to admin or employee automatically. Trigger phrases - "superpower", "run my morning", "start my day", "give me everything", "full briefing".
---

# Superpower

Runs the other CRM skills together as one morning routine, in the order that actually matters (what's urgent first, what to do about it last) - instead of the user having to remember and invoke five separate skills one at a time.

## Before running: who's asking

Check whether the person is admin (Nimita/Yogesh/owner) or a regular employee (Samiksha/Amol/Chirag/etc.) - this changes which sub-skills get included, same access rule as `ceo-dashboard`/`sales-intelligence`/`credit-manager`. If unclear, ask.

## Sequence

**For admin:**
1. `ceo-dashboard` - company-wide health check, what needs a decision this week.
2. `loan-sales` - which deals are stuck vs. moving, near-disbursement deals to watch.
3. `loan-documents` - for any deal `ceo-dashboard`/`loan-sales` flagged as stuck in Document Collection, pull the specific checklist gap.
4. `loan-prospecting` - fresh prospects ranked for today, if there's calling capacity left after chasing existing pipeline.
5. Close with: here's what needs your attention, here's who to call, here's what's blocked and on whom.

**For an employee:**
1. `sales-intelligence` - their own numbers, what's working, what to change.
2. `loan-sales` filtered to their own deals - which of their deals need a push today.
3. `loan-documents` for anything of theirs stuck in Document Collection.
4. `loan-prospecting` - their next call list.
5. Close with: here's your day, in the order to work it.

## What it does NOT do

Doesn't skip straight to `telecalling` and start dialing - this is a briefing that ends in "here's who to call," the human decides when to actually place calls. Doesn't run `credit-manager` automatically for every deal in the pipeline (that's a per-case tool, not a bulk one) - only mention it as a next step if a specific case looks like it needs pre-screening. Doesn't run `impeccable` automatically either - that's for a specific thing about to go out, not part of a morning scan.

## If this is a repeat run same day

Don't re-fetch and re-report everything from scratch if it was just run an hour ago - ask whether they want a full refresh or just what's changed since.
