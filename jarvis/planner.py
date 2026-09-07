#!/usr/bin/env python3
"""
JARVIS Planner — Stage C's entry point, thin by design.

Ties three already-built things together rather than reimplementing any of
them (per the explicit "Do NOT duplicate the Life Brain" instruction):

    jarvis/context.py   -> assemble_context()   (Phase 3, unchanged)
    jarvis/capabilities.py -> the capability registry (Stage C, new)
    jarvis/plans.py     -> create_plan() / validate_plan() (Stage C, new)

Planning flow (spec Section 8):

    USER GOAL -> INTENT -> CONTEXT ENGINE -> CONTEXT -> PLANNER -> PLAN

`propose_plan()` is what a skill/Claude actually calls. It does NOT decompose
the goal into steps itself - that reasoning happens in the caller (Claude),
which is why `steps` is a required argument here, not something this
function invents. What this function DOES do deterministically: pull
context first (so the caller's step-authoring can already be informed by
in one call), then hand the proposed steps to plans.py's deterministic
validator - the LLM proposes, the code validates, per spec Section 10.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import context as ctx  # noqa: E402
import plans  # noqa: E402


def propose_plan(mission_id, user_id, objective, steps, *,
                  context_type="business", mentions=None, entity_refs=None,
                  query=None, budget=15, max_hops=2,
                  assumptions=None, constraints=None, risk_level=None,
                  verification_strategy=None, fallback_strategy=None,
                  idempotency_key=None) -> dict:
    """Assembles context, then creates and validates a plan from the given
    steps. Returns {'plan': <validated or rejected plan>, 'context': <what
    informed it>} so a caller/audit log can see both halves. Raises
    plans.TransactionProhibitedError if any step is transaction-shaped -
    this is NOT deferred to a later stage (spec Section 11)."""
    context_result = ctx.assemble_context(
        context=context_type, mission=objective, mentions=mentions,
        entity_refs=entity_refs, query=query, budget=budget, max_hops=max_hops,
    )

    plan = plans.create_plan(
        mission_id, user_id, objective, steps,
        assumptions=assumptions, constraints=constraints, risk_level=risk_level,
        verification_strategy=verification_strategy, fallback_strategy=fallback_strategy,
        idempotency_key=idempotency_key,
    )

    validated = plans.validate_plan(plan["plan_id"], user_id)  # raises TransactionProhibitedError if applicable

    return {"plan": validated, "context": context_result}


def propose_replan(mission_id, user_id, previous_plan_id, objective, steps, **kwargs) -> dict:
    """Same shape as propose_plan(), but supersedes an existing plan
    version instead of starting a fresh version chain. See
    plans.create_replan() for the immutable-history guarantee."""
    context_result = ctx.assemble_context(
        context=kwargs.pop("context_type", "business"), mission=objective,
        mentions=kwargs.pop("mentions", None), entity_refs=kwargs.pop("entity_refs", None),
        query=kwargs.pop("query", None), budget=kwargs.pop("budget", 15),
        max_hops=kwargs.pop("max_hops", 2),
    )

    plan = plans.create_replan(mission_id, user_id, previous_plan_id, objective, steps, **kwargs)
    validated = plans.validate_plan(plan["plan_id"], user_id)

    return {"plan": validated, "context": context_result}
