#!/usr/bin/env python3
"""
JARVIS Capability Registry — the minimal interface Stage C's Planner needs
to answer "does this capability actually exist" before it can appear in a
plan (spec Section 7: "the Planner must never invent a tool merely because
it would be convenient").

This is deliberately NOT the full Tool Registry from the master spec
(Section 25A.12 / Stage K) - it has none of ToolRegistry's per-tool schema
validation, connector trust levels, or approval-requirement metadata. It is
the smallest thing that lets the Planner do capability *discovery* (does
"gmail_read" exist? no.) without inventing a general registry Stage K
hasn't been asked to build yet.

Static and honest: every entry here reflects what's actually true about
this repository today (per JARVIS_CONTEXT_INTEGRATION.md's profile table
and JARVIS_SCOPE_AND_ROADMAP.md), not what would be nice to have. Anything
not listed, or listed with available=False, must produce
CAPABILITY_UNAVAILABLE rather than being silently invented by a plan.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Capability:
    capability_id: str
    description: str
    required_tools: tuple = field(default_factory=tuple)
    available: bool = True
    risk_level: str = "R1"
    unavailable_reason: Optional[str] = None


# The 20 pre-existing CRM skills - all real, all call the live CRM REST API
# directly, all genuinely available today. Risk level reflects what kind of
# data/action each one touches, per JARVIS_PERMISSION_MATRIX.md's action
# classes (all of these are READ/ANALYZE - none of the 20 skills execute a
# write with external side effects on their own).
_CRM_SKILLS = {
    "ceo-dashboard": "Company-wide analytics and KPI rollup (admin-only).",
    "client-portfolio-entry": "Record/update a client's investment portfolio.",
    "commission-tracking": "Track commission earnings across products.",
    "compliance-calendar": "ARN/POSP/DSA renewal and compliance deadline tracking.",
    "credit-manager": "Pre-screen loan deals for completeness/red flags.",
    "cross-sell-radar": "Identify cross-sell opportunities across existing clients.",
    "financial-calculators": "SIP/EMI/goal-planning calculations.",
    "folio-review": "Review a client's mutual fund folio.",
    "impeccable": "Data-quality / completeness audit across CRM records.",
    "insurance-lapse-prevention": "Flag policies at risk of lapsing.",
    "insurance-research": "Insurance product research.",
    "loan-documents": "Loan document checklist generation.",
    "loan-prospecting": "Loan prospect identification.",
    "loan-research": "Loan product/rate research.",
    "loan-sales": "Loan sales pipeline support.",
    "mf-research": "Mutual fund / equity / macro research source lookup.",
    "sales-intelligence": "Lead scoring and sales pattern analysis.",
    "sip-tracking": "SIP status and continuity tracking.",
    "superpower": "Runs the daily/morning multi-skill routine as one sequence.",
    "telecalling": "Call script / talking-point support.",
}

# JARVIS's own native capabilities (Phases 2-3.5, Stage B) - these are not
# CRM skills, they're the Life Brain / mission substrate itself.
_JARVIS_NATIVE = {
    "jarvis-context-assembly": "Context Engine: entity resolution, graph traversal, "
                                "conflict detection, privacy-filtered recall in one call.",
    "jarvis-memory-write": "Record a fact/decision/commitment to JARVIS's own memory.",
    "jarvis-mission-tracking": "Create/transition a durable Mission or MissionStep.",
}

# Capabilities that do NOT exist yet - listed explicitly (not just absent)
# so the Planner's "unavailable" path is testable and the reason is
# specific rather than a generic lookup miss. Per JARVIS_SCOPE_AND_ROADMAP.md
# Part 2 - these all require Stage D (Worker Runtime) or Stage M (Connector
# Fabric), neither of which is built.
#
# Deliberately NOT listed here: anything financial-transaction-shaped. This
# registry is for "not built yet" capabilities, not "permanently forbidden"
# ones - those are two different concepts, and giving a transaction concept
# a capability_id in this static file would mean this file's own source
# text contains the exact prohibited-pattern vocabulary
# jarvis/tests/test_jarvis_cannot_touch_transactions.py scans for (it did,
# on the first version of this file - caught immediately by that test, as
# intended). The transaction check belongs entirely to plans.py's dynamic
# scan against backend/policy.py's pattern list at validation time (see
# validate_plan()'s "capability availability + transaction-pattern scan"
# step) - the single source of truth stays in one place, not duplicated
# here as a second, hand-maintained copy that could drift.
_KNOWN_UNAVAILABLE = {
    "gmail-read": "No Gmail/email connector exists yet - Stage M (Connector Fabric), not built.",
    "gmail-send": "No email-send capability exists yet - Stage D/M, not built. Also would be "
                  "COMMUNICATE + EXTERNAL_SIDE_EFFECT (R2, approval-required per the permission matrix) even once built.",
    "whatsapp-send": "No JARVIS-orchestrated WhatsApp send capability exists (the CRM's own "
                     "marketing-share feature is separate, human-triggered, outside this registry).",
    "calendar-read": "No calendar connector exists yet - Stage M, not built.",
    "calendar-write": "No calendar connector exists yet - Stage M, not built.",
    "browser-automation": "No browser/computer-use worker exists yet - Stage P, not built.",
    "web-search": "No web-search tool is wired into jarvis/ - Stage D/M, not built.",
}


def _build_registry() -> dict:
    registry = {}
    for cap_id, desc in _CRM_SKILLS.items():
        registry[cap_id] = Capability(cap_id, desc, required_tools=("crm_api",), available=True, risk_level="R0")
    for cap_id, desc in _JARVIS_NATIVE.items():
        registry[cap_id] = Capability(cap_id, desc, required_tools=("jarvis_db",), available=True, risk_level="R0")
    for cap_id, reason in _KNOWN_UNAVAILABLE.items():
        registry[cap_id] = Capability(cap_id, reason.split(" - ")[0], available=False,
                                       risk_level="R2", unavailable_reason=reason)
    return registry


REGISTRY = _build_registry()


def get_capability(capability_id: str) -> Optional[Capability]:
    return REGISTRY.get(capability_id)


def is_available(capability_id: str) -> bool:
    """Unknown capability IDs are treated as unavailable, not as an error
    and not as silently permitted - an unrecognized capability is exactly
    as unusable to the Planner as a known-unavailable one. This is the
    fail-closed behavior the permission matrix requires generally (spec
    Section 25A.23) applied to capability discovery specifically."""
    cap = REGISTRY.get(capability_id)
    return cap is not None and cap.available


def unavailable_reason(capability_id: str) -> str:
    cap = REGISTRY.get(capability_id)
    if cap is None:
        return f"Unknown capability {capability_id!r} - not in the registry at all."
    if cap.available:
        return ""
    return cap.unavailable_reason or "Marked unavailable in the registry."


def list_available() -> list:
    return sorted(cap_id for cap_id, cap in REGISTRY.items() if cap.available)
