#!/usr/bin/env python3
"""
JARVIS Verifier — Stage F: the difference between a worker returning
successfully and a mission actually being COMPLETED.

    EXECUTED  (workers.py, Stage D - the call ran)
       |
    OBSERVED  (workers.py's observe() - a raw output was recorded)
       |
    VERIFIED / PARTIALLY_VERIFIED / FAILED / UNVERIFIABLE   (this file)
       |
    SUCCEEDED  (only if VERIFIED all the way - Mission -> COMPLETED)

`worker success != verified success` was Stage E's own stated boundary
(it stops every clean mission at VERIFYING rather than declaring it done).
This file is what actually closes that loop - and it does so by gathering
independent evidence, never by re-trusting the worker's own return value.

## What "evidence" means here (read before adding a verification strategy)

jarvis/ is structurally network-free (Stage D's own execution boundary).
That means Stage F cannot verify anything by calling out to the CRM API,
an external system, or the internet - there is nothing to call. What it
CAN do, and does, is independently re-check jarvis/jarvis.db itself:

  - ContextWorker's output is re-derived: assemble_context() is a pure
    read, so verify_step() calls it again with the same inputs and
    compares - if the two reads disagree, that's real evidence, not a
    rubber stamp.
  - MemoryWriteWorker's output is independently re-queried:
    memory.get_memory(memory_id) is called directly against the database,
    not against the worker's own claimed return value. If the row doesn't
    exist, or its content doesn't match what was supposed to be written,
    that step verifies as FAILED even though the worker itself reported
    SUCCEEDED - this is the concrete case that proves "must never infer
    verification merely because a worker returned successfully."

A capability with no registered strategy verifies as UNVERIFIABLE, stated
honestly, rather than assumed to have succeeded. Extending verification to
a future connector-backed worker (Stage M+) needs its own strategy with
its own real evidence source - never a generic "it probably worked."

## The transaction boundary, restated for this file specifically

A transaction-shaped MissionStep can never reach this file at all: Stage D
blocks it before execution (BLOCKED, zero attempts), which means Stage E's
own mission never reaches VERIFYING for that mission (VERIFYING only
happens when no step is FAILED/BLOCKED/CANCELLED) - it goes to BLOCKED
instead. verify_mission() requires status == VERIFYING, so there is no
code path in this file that can ever be reached for a mission containing
a prohibited step. This is proven by a test, not just asserted here.

## What this stage does NOT do
No retries, no fallback, no replanning (Stage G) - a FAILED verification
stays FAILED, full stop. No LLM judgment call anywhere in this file -
every verdict is a deterministic comparison against independently
gathered evidence.
"""

import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))

import missions as msn  # noqa: E402
import context as ctx  # noqa: E402
import memory as jm  # noqa: E402

VERIFICATION_STATUSES = {"NOT_VERIFIED", "VERIFIED", "PARTIALLY_VERIFIED", "FAILED", "UNVERIFIABLE"}

# The step statuses that even have something to verify. Stage E only ever
# lets a mission reach VERIFYING when no step is FAILED/BLOCKED/CANCELLED,
# so in practice every step this file sees is SUCCEEDED, PARTIALLY_SUCCEEDED,
# or SKIPPED - but this file is defensive about it independently too,
# rather than trusting that invariant blindly.
_VERIFIABLE_STEP_STATUSES = {"SUCCEEDED", "PARTIALLY_SUCCEEDED"}


def _now():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Errors (same canonical shape as the rest of the jarvis/ stages)
# ---------------------------------------------------------------------------

@dataclass
class ErrorObject:
    code: str
    category: str
    severity: str = "ERROR"
    retryable: bool = False
    user_action_required: bool = False
    message: str = ""
    mission_id: str = None
    step_id: str = None
    metadata: dict = field(default_factory=dict)
    error_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=_now)

    def to_dict(self):
        return asdict(self)


class VerifierError(Exception):
    def __init__(self, error: ErrorObject):
        self.error = error
        super().__init__(error.message)


class StepNotVerifiableYetError(VerifierError):
    def __init__(self, step_id, status):
        super().__init__(ErrorObject(
            code="VERIFICATION_UNAVAILABLE", category="VERIFICATION", step_id=step_id,
            message=f"Step {step_id!r} is {status!r} - only SUCCEEDED/PARTIALLY_SUCCEEDED steps can be verified.",
        ))


class MissionNotVerifiableYetError(VerifierError):
    def __init__(self, mission_id, status):
        super().__init__(ErrorObject(
            code="VERIFICATION_UNAVAILABLE", category="VERIFICATION", mission_id=mission_id,
            message=f"Mission {mission_id!r} is {status!r}, not VERIFYING - nothing for the Verifier to do yet "
                    "(or it was already verified once, and verification does not re-open a terminal mission).",
        ))


# ---------------------------------------------------------------------------
# Verification result
# ---------------------------------------------------------------------------

@dataclass
class VerificationResult:
    verification_id: str
    mission_id: str
    step_id: str
    worker_id: str
    status: str          # one of VERIFICATION_STATUSES
    evidence: dict
    reasoning: str
    checked_at: str

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------------------
# Verification strategies - one per capability_id, each returns
# (status, evidence, reasoning). No strategy ever trusts step['output']
# as sufficient evidence on its own without an independent check.
# ---------------------------------------------------------------------------

def _verify_context_assembly(step: dict):
    stored_output = step.get("output")
    if stored_output is None:
        return "UNVERIFIABLE", {}, "no output was recorded for this step - nothing to verify against"

    inputs = step.get("inputs") or {}
    try:
        entity_refs = [tuple(e) for e in inputs["entity_refs"]] if inputs.get("entity_refs") else None
        fresh = ctx.assemble_context(
            context=inputs.get("context", "business"),
            mission=step.get("description") or "",
            mentions=inputs.get("mentions"),
            entity_refs=entity_refs,
            query=inputs.get("query"),
            budget=inputs.get("budget", 15),
            max_hops=inputs.get("max_hops", 2),
        )
    except Exception as e:
        return "UNVERIFIABLE", {"error": str(e)}, "re-running the read for independent comparison raised an exception"

    evidence = {
        "stored_resolved_entities": len(stored_output.get("resolved_entities") or []),
        "fresh_resolved_entities": len(fresh.get("resolved_entities") or []),
        "stored_memory_count": len(stored_output.get("memories") or []),
        "fresh_memory_count": len(fresh.get("memories") or []),
    }

    expected = step.get("expected_output") or {}
    min_entities = expected.get("min_resolved_entities")
    if min_entities is not None and evidence["stored_resolved_entities"] < min_entities:
        return "FAILED", evidence, (
            f"expected_output required at least {min_entities} resolved entities, "
            f"but only {evidence['stored_resolved_entities']} were recorded"
        )

    if fresh.get("resolved_entities") == stored_output.get("resolved_entities") and \
       fresh.get("memories") == stored_output.get("memories"):
        return "VERIFIED", evidence, "re-running the same read independently produced identical results"

    return "PARTIALLY_VERIFIED", evidence, (
        "re-running the read produced different results than what was recorded - the underlying "
        "context may have legitimately changed since execution (e.g. a later write); this is a "
        "genuine ambiguity, not asserted as either success or failure"
    )


def _verify_memory_write(step: dict):
    stored_output = step.get("output")
    if not stored_output or "memory_id" not in stored_output:
        return "UNVERIFIABLE", {}, "no memory_id was recorded in this step's output - nothing to independently check"

    memory_id = stored_output["memory_id"]
    row = jm.get_memory(memory_id)
    if row is None:
        return "FAILED", {"memory_id": memory_id, "found": False}, (
            f"the worker reported writing memory_id={memory_id}, but an independent query of "
            "jarvis_memory found no such row (or it was already forgotten) - the claimed outcome "
            "does not match what is actually in the database"
        )

    evidence = {"memory_id": memory_id, "found": True, "stored_content": row["content"]}
    expected_content = (step.get("inputs") or {}).get("content")
    if expected_content is not None and row["content"] != expected_content:
        evidence["expected_content"] = expected_content
        return "FAILED", evidence, (
            "the memory row exists, but its content does not match what was supposed to be written - "
            "found evidence, but it contradicts the claimed outcome"
        )

    return "VERIFIED", evidence, "independently re-queried jarvis_memory by id and confirmed the row exists with the expected content"


_STRATEGIES = {
    "jarvis-context-assembly": _verify_context_assembly,
    "jarvis-memory-write": _verify_memory_write,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_verification(step_id: str) -> dict:
    """Reads back an already-recorded verification from the MissionStep's
    own `verification` field - this IS the idempotency/cache mechanism.
    No second persistence store was built for this; Stage B's own field,
    reserved for exactly this since the Stage B contract, is used directly."""
    with msn._connect() as conn:
        row = conn.execute("SELECT verification FROM jarvis_mission_steps WHERE step_id = ?", (step_id,)).fetchone()
    if row is None or not row["verification"]:
        return None
    return json.loads(row["verification"])


def verify_step(mission_id: str, step_id: str, user_id: str, force: bool = False) -> VerificationResult:
    """Idempotent by default: a step that already has a recorded
    verification returns it unchanged rather than re-running evidence
    gathering (restart-safe by construction - there is no in-flight state
    to reconcile, each call is a single synchronous read-then-write).
    Pass force=True to deliberately re-check."""
    step = msn.get_step(step_id, mission_id, user_id)

    if not force:
        cached = get_verification(step_id)
        if cached is not None:
            return VerificationResult(**cached)

    if step["status"] not in _VERIFIABLE_STEP_STATUSES:
        raise StepNotVerifiableYetError(step_id, step["status"])

    strategy = _STRATEGIES.get(step.get("worker_id"))
    if strategy is None:
        status, evidence, reasoning = (
            "UNVERIFIABLE", {},
            f"no verification strategy is registered for capability {step.get('worker_id')!r} - "
            "this is stated honestly rather than assuming the worker's own report was correct",
        )
    else:
        status, evidence, reasoning = strategy(step)

    if status not in VERIFICATION_STATUSES:
        raise VerifierError(ErrorObject(code="INVALID_INPUT", category="VALIDATION", step_id=step_id,
                                         message=f"a verification strategy returned an unknown status {status!r}"))

    result = VerificationResult(
        verification_id=str(uuid4()), mission_id=mission_id, step_id=step_id,
        worker_id=step.get("worker_id"), status=status, evidence=evidence,
        reasoning=reasoning, checked_at=_now(),
    )
    msn.record_step_verification(step_id, mission_id, user_id, result.to_dict())
    return result


def verify_mission(mission_id: str, user_id: str) -> dict:
    """The closing act of the whole B->C->D->E->F chain: verifies every
    verifiable step, then makes the ONE judgment this whole architecture
    has been deferring since Stage E - COMPLETED, PARTIALLY_COMPLETED, or
    FAILED - based entirely on gathered evidence, never on trusting that
    the workers all just worked. Requires the mission to be at VERIFYING
    (Stage E's own hand-off point); refuses to run on anything else,
    including a mission already verified once - VERIFYING has no path
    back to itself in Stage B's state machine, so double-verification is
    structurally impossible, not just discouraged."""
    mission = msn.get_mission(mission_id, user_id)
    if mission["status"] != "VERIFYING":
        raise MissionNotVerifiableYetError(mission_id, mission["status"])

    steps = msn.list_steps(mission_id, user_id)
    if not steps:
        # Nothing was ever asked of this mission, and nothing failed -
        # vacuously complete, stated explicitly rather than falling
        # through to a less honest default.
        final = msn.transition_mission(mission_id, user_id, "COMPLETED", verification_state="VERIFIED")
        return {"mission": final, "results": []}

    results = [verify_step(mission_id, s["step_id"], user_id) for s in steps if s["status"] in _VERIFIABLE_STEP_STATUSES]
    skipped_count = sum(1 for s in steps if s["status"] == "SKIPPED")

    failed = [r for r in results if r.status == "FAILED"]
    if failed:
        mission_status, verification_state = "FAILED", "FAILED"
        error = {
            "code": "VERIFICATION_FAILED", "category": "VERIFICATION", "severity": "ERROR", "retryable": False,
            "message": "one or more steps' claimed outcomes did not match independently gathered evidence.",
            "metadata": {"failed_step_ids": [r.step_id for r in failed]},
        }
    elif results and all(r.status == "VERIFIED" for r in results) and skipped_count == 0:
        mission_status, verification_state, error = "COMPLETED", "VERIFIED", None
    else:
        mission_status, verification_state = "PARTIALLY_COMPLETED", "PARTIALLY_VERIFIED"
        error = {
            "code": "VERIFICATION_INCOMPLETE", "category": "VERIFICATION", "severity": "WARNING", "retryable": False,
            "message": "not every step could be fully verified (partial evidence, unverifiable capability, "
                       "or skipped work) - no evidence of failure, but full completion is not confirmed either.",
        }

    final = msn.transition_mission(mission_id, user_id, mission_status, verification_state=verification_state, error=error)
    return {"mission": final, "results": results}
