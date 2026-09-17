#!/usr/bin/env python3
"""
JARVIS Worker Runtime — Stage D: the first real execution runtime capable
of taking a validated (Stage C) MissionStep and executing it through an
authorized Worker (Stage B ledger row -> real bounded operation -> back
into the Stage B ledger).

    Validated Plan (Stage C)
          |
    MissionStep (Stage B)
          |
    Worker Registry (this file)
          |
    Worker (this file)
          |
    Tool  (a plain Python call - see "Tool boundary" below)
          |
    Execution
          |
    Observation

## THE STAGE D EXECUTION BOUNDARY (read this before adding a Worker)

`jarvis/` has been network-free since Phase 2, verified continuously by
`jarvis/tests/test_jarvis_cannot_touch_transactions.py`'s zero-network-
import check. Stage D does NOT change that. Every Worker in this file
executes only a real, bounded, already-existing JARVIS-INTERNAL capability
- one that reads or writes jarvis/jarvis.db through code that already
exists (jarvis/context.py, jarvis/memory.py) - never the live CRM REST API,
never the open internet, never email/WhatsApp/browser/MCP.

This is a deliberate scope decision, not a missing feature: reaching the
CRM API or the internet would require `requests`/`urllib`/`httpx`/etc,
which is exactly the "worth a deliberate, visible decision, not something
that slips in as a side effect" moment the test comment above already
warns about. That decision belongs to Stage M (Connector Fabric), which
hasn't been authorized. So Stage D's workers are real and prove the
runtime genuinely - they just can't yet reach anything outside jarvis.db.
A future ConnectorWorker that calls the CRM API is a Stage M change, not
a Stage D one, and needs its own explicit review exactly like this file's
own docstring says.

The Tool boundary this stage establishes: a Worker's `execute()` calls a
plain Python function (`context.assemble_context`, `memory.remember`) -
there is no mechanism anywhere in this file for the LLM to supply an
arbitrary function, URL, or shell command to run. `execute_step()` only
ever dispatches to a Worker that was explicitly registered in a
WorkerRegistry ahead of time and matched by a capability_id the step
itself declared - the set of things that CAN run is fixed by this file's
own code, not by anything a model generates at request time.

## What this stage does NOT do
No Supervisor (nothing decides *when* a READY step should execute - a
caller still has to call execute_step() itself, same as Stage C's
materialize_plan() didn't start anything). No retries (Stage G). No
verification of whether the outcome was actually correct, only that the
call completed and what it returned (Stage F). No browser/MCP/connector
workers (Stage M/P).
"""

import json
import sqlite3
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import missions as msn  # noqa: E402
import context as ctx  # noqa: E402
import memory as jm  # noqa: E402
import capabilities as caps  # noqa: E402
import approval as appr  # noqa: E402
import action_firewall as firewall  # noqa: E402
import tools as toolreg  # noqa: E402
from policy import find_prohibited_routes  # noqa: E402 - same single source of truth every other layer uses

DB_PATH = Path(__file__).resolve().parent / "jarvis.db"

WORKER_STATUSES = {
    "QUEUED", "STARTING", "RUNNING", "WAITING", "SUCCEEDED",
    "PARTIALLY_SUCCEEDED", "FAILED", "CANCELLED", "TIMED_OUT", "BLOCKED",
}

# Worker-level status -> MissionStep's own (Stage B, unchanged) status
# vocabulary. The two are deliberately different sizes/shapes (Worker
# status is richer - it distinguishes TIMED_OUT from a generic FAILED,
# which matters for observability even though Stage B's own MissionStep
# only has one terminal failure state). This map is the ONE place that
# translation happens - Stage B's contract is never edited to grow new
# statuses just to satisfy this stage (see "Important Stage B/C boundary").
WORKER_STATUS_TO_STEP_STATUS = {
    "SUCCEEDED": "SUCCEEDED",
    "PARTIALLY_SUCCEEDED": "PARTIALLY_SUCCEEDED",
    "FAILED": "FAILED",
    "TIMED_OUT": "FAILED",
    "CANCELLED": "CANCELLED",
    "BLOCKED": "BLOCKED",
}


# ---------------------------------------------------------------------------
# Errors (same canonical shape as missions.py/plans.py)
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
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self):
        return asdict(self)


class WorkerError(Exception):
    def __init__(self, error: ErrorObject):
        self.error = error
        super().__init__(error.message)


class WorkerNotFoundError(WorkerError):
    def __init__(self, capability_id, step_id):
        super().__init__(ErrorObject(
            code="TOOL_NOT_FOUND", category="TOOL", step_id=step_id,
            message=f"No enabled worker supports capability {capability_id!r}.",
            metadata={"capability_id": capability_id},
        ))


class StepNotExecutableError(WorkerError):
    def __init__(self, step_id, current_status):
        super().__init__(ErrorObject(
            code="INVALID_STATE_TRANSITION", category="STATE", step_id=step_id,
            message=f"Step {step_id!r} is {current_status}, not READY - cannot execute.",
        ))


class WorkerValidationError(WorkerError):
    def __init__(self, message, step_id=None):
        super().__init__(ErrorObject(code="INVALID_INPUT", category="VALIDATION", step_id=step_id, message=message))


class WorkerTransactionProhibitedError(WorkerError):
    """Raised when a MissionStep's own text is transaction-shaped - the
    PRIMARY enforcement point for any step that was created directly via
    missions.create_step() rather than materialized from a Stage C plan
    (which would already have been checked by plans.py's validator). Never
    executed, never even claimed (no RUNNING transition occurs)."""

    def __init__(self, mission_id, step_id, matches):
        super().__init__(ErrorObject(
            code="TRANSACTION_PROHIBITED", category="POLICY", severity="CRITICAL",
            retryable=False, mission_id=mission_id, step_id=step_id,
            message="This step is financial-transaction-shaped and cannot execute.",
            metadata={"matches": matches},
        ))


class ApprovalRequiredError(WorkerError):
    """Raised when a step resolves to an approval-requiring risk tier
    (R2/R3, per capabilities.py's own risk_level) and no ALLOWED decision
    exists yet from the Approval Gate (Stage I) - the step is left exactly
    as it was, never claimed, never run. See approval.evaluate()."""

    def __init__(self, mission_id, step_id, decision):
        super().__init__(ErrorObject(
            code="APPROVAL_REQUIRED" if decision.decision == "APPROVAL_REQUIRED" else "ACTION_NOT_AUTHORIZED",
            category="POLICY", severity="ERROR", retryable=(decision.decision == "APPROVAL_REQUIRED"),
            mission_id=mission_id, step_id=step_id,
            message=f"This step requires approval before it can execute (decision={decision.decision!r}).",
            metadata={"approval_decision": decision.to_dict()},
        ))


class WorkerToolNotAuthorizedError(WorkerError):
    """Raised when a step's capability resolves to a REGISTERED Tool
    (Stage K, tools.py) that is not currently executable - disabled, or at
    an UNKNOWN/BLOCKED trust level. A capability_id with no registered
    Tool never raises this (see tools.py's own "existing-worker
    compatibility" note) - this is strictly additive. Distinct from
    ApprovalRequiredError: this is a Tool Registry identity/trust gate,
    checked BEFORE Approval Gate or Action Firewall are even consulted -
    registering a tool is never authorization on its own."""

    def __init__(self, mission_id, step_id, tool_id, reason_codes):
        super().__init__(ErrorObject(
            code="TOOL_NOT_AUTHORIZED", category="POLICY", severity="ERROR", retryable=False,
            mission_id=mission_id, step_id=step_id,
            message=f"Tool {tool_id!r} is not currently executable ({reason_codes}).",
            metadata={"tool_id": tool_id, "reason_codes": reason_codes},
        ))


# ---------------------------------------------------------------------------
# Worker execution result
# ---------------------------------------------------------------------------

@dataclass
class WorkerExecutionResult:
    execution_id: str
    mission_id: str
    step_id: str
    worker_id: str
    status: str
    output: object = None
    observation: object = None
    error: dict = None
    started_at: str = None
    completed_at: str = None
    attempt: int = None
    trace: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------------------
# Worker abstraction
# ---------------------------------------------------------------------------

class Worker:
    """Base class. A concrete Worker declares worker_id/name/capabilities/
    input_schema as class attributes and overrides execute() - everything
    else has a sane default."""

    worker_id = None
    name = None
    capabilities = ()          # capability_ids (jarvis/capabilities.py) this worker supports
    input_schema = ()          # required keys in step['inputs'] - checked before execute()
    enabled = True

    def can_handle(self, step: dict) -> bool:
        return step.get("worker_id") in self.capabilities

    def prepare(self, step: dict) -> None:
        """Pre-flight hook. No-op by default - override for a worker that
        needs setup before execute() (e.g. opening a resource)."""
        return None

    def execute(self, step: dict, user_id: str):
        """Must be overridden. Returns the raw output - NOT wrapped in a
        WorkerExecutionResult (execute_step() does that). Must never call
        anything outside jarvis/jarvis.db - see this module's docstring.
        `user_id` is passed explicitly (not read off `step`, which has no
        user_id field of its own - only Mission does) for any worker whose
        underlying call requires it, e.g. missions.py's own user-isolated API."""
        raise NotImplementedError

    def observe(self, step: dict, output) -> dict:
        """Turns raw execute() output into a recorded observation. Kept as
        a separate step from execute() on purpose (spec Section 22): an
        execution completing is not the same claim as its outcome being
        understood/verified - Stage F (Verifier) is what actually verifies
        an outcome; this is just where the two concepts stay distinguishable
        in the data model rather than being silently collapsed into one."""
        return {"observed_at": datetime.now(timezone.utc).isoformat(), "output_type": type(output).__name__}

    def cancel(self, step: dict) -> bool:
        """Best-effort only. Python cannot safely force-terminate a running
        thread, so this can request cooperative cancellation but must never
        be trusted to mean the underlying call actually stopped - see
        execute_step()'s own cancellation note. Returns whether a
        cancellation request was even possible to issue, not whether it
        succeeded."""
        return False


class ContextWorker(Worker):
    """Wraps context.assemble_context() - a real, bounded, read-only,
    jarvis-internal operation."""

    worker_id = "context-worker"
    name = "Context Assembly Worker"
    capabilities = ("jarvis-context-assembly",)
    input_schema = ()  # every assemble_context() param is optional

    def execute(self, step: dict, user_id: str):
        inputs = step.get("inputs") or {}
        entity_refs = [tuple(e) for e in inputs["entity_refs"]] if inputs.get("entity_refs") else None
        return ctx.assemble_context(
            context=inputs.get("context", "business"),
            mission=step.get("description") or "",
            mentions=inputs.get("mentions"),
            entity_refs=entity_refs,
            query=inputs.get("query"),
            budget=inputs.get("budget", 15),
            max_hops=inputs.get("max_hops", 2),
        )

    def observe(self, step, output):
        obs = super().observe(step, output)
        if isinstance(output, dict):
            obs["resolved_entity_count"] = len(output.get("resolved_entities") or [])
            obs["memory_count"] = len(output.get("memories") or [])
            obs["conflict_count"] = len(output.get("conflicts") or [])
        return obs


class MemoryWriteWorker(Worker):
    """Wraps memory.remember() - a real, bounded, jarvis-internal write.
    Writes only ever land in jarvis/jarvis.db's own memory table, never
    anywhere external."""

    worker_id = "memory-write-worker"
    name = "Memory Write Worker"
    capabilities = ("jarvis-memory-write",)
    input_schema = ("memory_type", "content")

    def execute(self, step: dict, user_id: str):
        inputs = step.get("inputs") or {}
        memory_id = jm.remember(
            inputs["memory_type"], inputs["content"],
            source=inputs.get("source", "worker-execution"),
            entity_type=inputs.get("entity_type"), entity_id=inputs.get("entity_id"),
            importance=inputs.get("importance", 3),
            privacy_level=inputs.get("privacy_level", "business"),
            fact_key=inputs.get("fact_key"),
        )
        return {"memory_id": memory_id}

    def observe(self, step, output):
        obs = super().observe(step, output)
        obs["memory_id"] = output.get("memory_id") if isinstance(output, dict) else None
        return obs


class MissionTrackingWorker(Worker):
    """Wraps missions.create_mission() to spawn a child Mission - a real,
    bounded, jarvis-internal write that gives Stage B's own `parent_mission_id`
    field (declared in the original Mission contract, never previously set
    by any code) its first real use.

    Deliberately narrow: this worker only ever CREATES a new child mission.
    It does not expose a generic "transition any mission to any status"
    action - that would let a plan step reach around the Supervisor/
    Recovery/Verifier state-machine boundaries those stages exist to own,
    for the same reason no other Worker in this file bypasses the ledger.
    Spawning a child mission is safe because the child starts at CREATED,
    like any other mission, and goes through the exact same lifecycle
    every other mission does - nothing here shortcuts a transition."""

    worker_id = "mission-tracking-worker"
    name = "Mission Tracking Worker"
    capabilities = ("jarvis-mission-tracking",)
    input_schema = ("goal",)

    def execute(self, step: dict, user_id: str):
        inputs = step.get("inputs") or {}
        child = msn.create_mission(
            user_id, inputs["goal"],
            risk_level=inputs.get("risk_level"),
            context_reference=inputs.get("context_reference"),
            deadline=inputs.get("deadline"),
            parent_mission_id=step["mission_id"],
        )
        return {"child_mission_id": child["mission_id"], "status": child["status"]}

    def observe(self, step, output):
        obs = super().observe(step, output)
        obs["child_mission_id"] = output.get("child_mission_id") if isinstance(output, dict) else None
        return obs


# ---------------------------------------------------------------------------
# Worker Registry
# ---------------------------------------------------------------------------

class WorkerRegistry:
    def __init__(self):
        self._workers: dict[str, Worker] = {}

    def register_worker(self, worker: Worker) -> None:
        if not worker.worker_id:
            raise WorkerValidationError("a worker must declare a worker_id before registration")
        self._workers[worker.worker_id] = worker

    def get_worker(self, worker_id: str):
        return self._workers.get(worker_id)

    def list_workers(self) -> list:
        return list(self._workers.values())

    def find_workers_for_capability(self, capability_id: str) -> list:
        if not capability_id:
            return []
        return [w for w in self._workers.values() if w.enabled and capability_id in w.capabilities]


def _default_registry() -> WorkerRegistry:
    registry = WorkerRegistry()
    registry.register_worker(ContextWorker())
    registry.register_worker(MemoryWriteWorker())
    registry.register_worker(MissionTrackingWorker())
    return registry


DEFAULT_REGISTRY = _default_registry()


# ---------------------------------------------------------------------------
# Persistence (this file's own table - never touches Stage B's schema)
# ---------------------------------------------------------------------------

@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    msn.DB_PATH = DB_PATH if msn.DB_PATH != DB_PATH else msn.DB_PATH
    msn.init_db()
    firewall.DB_PATH = DB_PATH if firewall.DB_PATH != DB_PATH else firewall.DB_PATH
    firewall.init_db()  # cascades to approval.init_db() + intent_lock.init_db() - execute_step() calls into all three
    toolreg.DB_PATH = DB_PATH if toolreg.DB_PATH != DB_PATH else toolreg.DB_PATH
    toolreg.init_db()
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jarvis_worker_executions (
                execution_id TEXT PRIMARY KEY,
                mission_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                worker_id TEXT NOT NULL,
                status TEXT NOT NULL,
                output TEXT,
                observation TEXT,
                error TEXT,
                started_at TEXT,
                completed_at TEXT,
                attempt INTEGER,
                trace TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_worker_exec_step ON jarvis_worker_executions(step_id)")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _persist_result(result: WorkerExecutionResult):
    with _connect() as conn:
        conn.execute("""
            INSERT INTO jarvis_worker_executions
                (execution_id, mission_id, step_id, worker_id, status, output,
                 observation, error, started_at, completed_at, attempt, trace)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (result.execution_id, result.mission_id, result.step_id, result.worker_id,
              result.status, json.dumps(result.output, default=str) if result.output is not None else None,
              json.dumps(result.observation, default=str) if result.observation is not None else None,
              json.dumps(result.error) if result.error is not None else None,
              result.started_at, result.completed_at, result.attempt, json.dumps(result.trace)))


def _row_to_result(row) -> WorkerExecutionResult:
    return WorkerExecutionResult(
        execution_id=row["execution_id"], mission_id=row["mission_id"], step_id=row["step_id"],
        worker_id=row["worker_id"], status=row["status"],
        output=json.loads(row["output"]) if row["output"] else None,
        observation=json.loads(row["observation"]) if row["observation"] else None,
        error=json.loads(row["error"]) if row["error"] else None,
        started_at=row["started_at"], completed_at=row["completed_at"], attempt=row["attempt"],
        trace=json.loads(row["trace"]) if row["trace"] else [],
    )


def get_execution(execution_id: str):
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jarvis_worker_executions WHERE execution_id = ?", (execution_id,)).fetchone()
    return _row_to_result(row) if row else None


def list_executions_for_step(step_id: str) -> list:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM jarvis_worker_executions WHERE step_id = ? ORDER BY started_at ASC", (step_id,)
        ).fetchall()
    return [_row_to_result(r) for r in rows]


def _scan_step_for_prohibited_text(step: dict) -> list:
    texts = [step.get("description"), step.get("worker_id")]
    inputs = step.get("inputs")
    if inputs:
        texts.append(json.dumps(inputs, default=str))
    combined = " | ".join(t for t in texts if t)
    if not combined:
        return []
    return [pattern for _, pattern in find_prohibited_routes([combined])]


# ---------------------------------------------------------------------------
# The runtime: execute one MissionStep through one Worker
# ---------------------------------------------------------------------------

def execute_step(mission_id, step_id, user_id, *, registry: WorkerRegistry = None,
                  timeout_seconds: float = 30, execution_id: str = None,
                  action_class: str = None, target=None, material_params: dict = None) -> WorkerExecutionResult:
    """The entire Stage D runtime lives in this one function. Order of
    operations is deliberate - every check that can fail closed happens
    BEFORE the step is claimed (READY -> RUNNING) or a Worker is called,
    per spec Section 15 ("Invalid execution requests must fail before the
    worker performs side effects").

    Stage I integration: if the step's capability resolves to an
    approval-requiring risk tier (R2/R3 in capabilities.py), the caller
    must pass `action_class` and the Approval Gate (approval.py) must
    already have an ALLOWED decision for this exact action, or the step
    is never claimed. No capability registered today is above R0, so this
    path has nothing real to gate yet - proven instead with a test-only
    R2 worker fixture (see test_approval.py), the same technique Stage H
    used to prove intent-drift detection before any real drift existed."""
    registry = registry or DEFAULT_REGISTRY
    execution_id = execution_id or str(uuid.uuid4())

    # Idempotency: a replayed execution_id returns the recorded result
    # verbatim - no re-validation, no re-claim, no second Worker call.
    cached = get_execution(execution_id)
    if cached is not None:
        return cached

    mission = msn.get_mission(mission_id, user_id)          # user isolation + existence, raises MissionNotFoundError
    step = msn.get_step(step_id, mission_id, user_id)        # step belongs to this mission, raises StepNotFoundError

    if step["status"] not in ("READY", "WAITING_FOR_APPROVAL"):
        raise StepNotExecutableError(step_id, step["status"])
    # WAITING_FOR_APPROVAL is Stage I's re-entry point: calling execute_step()
    # again on a step that previously stopped here re-evaluates approval: if
    # it is now ALLOWED, execution proceeds (WAITING_FOR_APPROVAL -> RUNNING
    # is a legal Stage B edge); if not, it raises again without progressing.

    # Transaction safety - the primary enforcement point for a step that
    # didn't come from a Stage C plan (plans.py already checked those).
    # Nothing is claimed, nothing runs, if this matches.
    matches = _scan_step_for_prohibited_text(step)
    if matches:
        msn.transition_step(step_id, mission_id, user_id, "BLOCKED", error={
            "code": "TRANSACTION_PROHIBITED", "category": "POLICY", "severity": "CRITICAL",
            "retryable": False, "matched_patterns": matches,
        })
        raise WorkerTransactionProhibitedError(mission_id, step_id, matches)

    capability_id = step.get("worker_id")
    candidates = registry.find_workers_for_capability(capability_id)
    if not candidates:
        raise WorkerNotFoundError(capability_id, step_id)
    worker = candidates[0]

    if not worker.can_handle(step):
        raise WorkerValidationError(f"worker {worker.worker_id!r} declined this step", step_id=step_id)

    missing_inputs = [k for k in worker.input_schema if not (step.get("inputs") or {}).get(k)]
    if missing_inputs:
        raise WorkerValidationError(f"missing required inputs for {worker.worker_id!r}: {missing_inputs}", step_id=step_id)

    # Stage K: Tool Registry - additive and strictly backward-compatible.
    # A capability_id is only gated here if it was explicitly registered
    # as a Tool (tools.register_tool()); a capability_id with no
    # registered Tool - every pre-existing R0 capability, every ad-hoc
    # test/internal worker - is completely unaffected, byte for byte,
    # exactly the lesson Stage J's own INVALID_TOOL scoping already
    # learned once. Registration is never authorization on its own: a
    # VERIFIED, enabled tool still has to clear Approval Gate + Action
    # Firewall below like any other capability - this only adds an
    # earlier, tool-identity-specific fail-closed gate (disabled tool, or
    # an UNKNOWN/BLOCKED trust level, refused before Approval/Firewall are
    # even consulted).
    registered_tools = toolreg.lookup_by_capability(capability_id)
    tool = registered_tools[0] if registered_tools else None
    resolved_tool_id = capability_id
    if tool is not None:
        try:
            availability = toolreg.assert_tool_executable(tool.tool_id)
        except toolreg.ToolTransactionProhibitedError as e:
            msn.transition_step(step_id, mission_id, user_id, "BLOCKED", error={
                "code": "TRANSACTION_PROHIBITED", "category": "POLICY", "severity": "CRITICAL",
                "retryable": False, "matched_patterns": e.error.metadata.get("matches"),
            })
            raise WorkerTransactionProhibitedError(mission_id, step_id, e.error.metadata.get("matches", []))
        if not availability["available"]:
            msn.transition_step(step_id, mission_id, user_id, "BLOCKED", error={
                "code": "TOOL_NOT_AUTHORIZED", "category": "POLICY", "severity": "ERROR",
                "retryable": False, "metadata": {"reason_codes": availability["reason_codes"], "tool_id": tool.tool_id},
            })
            raise WorkerToolNotAuthorizedError(mission_id, step_id, tool.tool_id, availability["reason_codes"])
        # The registered Tool's own identity (distinct from the bare
        # capability_id - Capability != Tool) becomes the tool_id passed
        # to Approval/Firewall - action_firewall.py's own tool-validity
        # check recognizes a Tool Registry identity directly (see that
        # file's own Stage K note), so this composes without weakening
        # that check. The tool's CURRENT version is folded into
        # material_params via the same public helper a caller requesting
        # approval should use (toolreg.approval_material_params()) - a
        # version bump changes that value, which changes the fingerprint
        # compute_action_fingerprint() already owns (Stage I), invalidating
        # a prior approval for the old version. No second invalidation
        # mechanism is built here.
        resolved_tool_id = tool.tool_id
        material_params = toolreg.approval_material_params(tool, material_params)

    # Stage J: Action Firewall - the UNIVERSAL final gate. Every execution,
    # regardless of risk tier, passes through firewall.authorize() - there
    # is no code path around it. For an R0/R1 capability this resolves to
    # ALLOW quickly (the Firewall's own delegated Approval Gate check
    # already returns ALLOWED for those tiers), so no existing R0 worker's
    # behavior or tests change. Only an R2+ capability makes action_class
    # a hard requirement (fail-closed, never guessed) - matching the exact
    # boundary Stage I established, now enforced one layer up.
    cap = caps.get_capability(capability_id)
    effective_risk_level = tool.risk_level if tool is not None else (cap.risk_level if cap is not None else None)
    if effective_risk_level in appr.APPROVAL_REQUIRED_RISK_LEVELS.union(appr.DENIED_RISK_LEVELS) \
            and action_class is None:
        raise WorkerValidationError(
            f"capability {capability_id!r} is risk {effective_risk_level!r} and requires an action_class "
            "to evaluate approval - failing closed rather than guessing one", step_id=step_id,
        )

    try:
        decision = firewall.authorize(mission_id, step_id, user_id, action_class,
                                       effective_risk_level,
                                       tool_id=resolved_tool_id, target=target, material_params=material_params)
    except firewall.TransactionProhibitedError as e:
        # Same treatment as the top-level transaction check above:
        # never claimed, zero attempts recorded.
        msn.transition_step(step_id, mission_id, user_id, "BLOCKED", error={
            "code": "TRANSACTION_PROHIBITED", "category": "POLICY", "severity": "CRITICAL",
            "retryable": False, "matched_patterns": e.error.metadata.get("matches"),
        })
        raise WorkerTransactionProhibitedError(mission_id, step_id, e.error.metadata.get("matches", []))

    if decision.decision != "ALLOW":
        _PERMANENT_DENIAL_REASONS = {
            "MISSING_REQUIRED_METADATA", "INVALID_ACTION_CLASS", "MISSION_OR_STEP_NOT_FOUND",
            "CANCELLED", "INTENT_DRIFT_DETECTED", "INVALID_TOOL", "SECURITY_VIOLATION",
            "PRIVACY_SCOPE_DENIED", "APPROVAL_DENIED",
        }
        if set(decision.reason_codes) & _PERMANENT_DENIAL_REASONS:
            # Never "waiting" - this will never resolve on its own.
            msn.transition_step(step_id, mission_id, user_id, "BLOCKED",
                                 error={"code": "ACTION_NOT_AUTHORIZED", "category": "POLICY",
                                        "severity": "ERROR", "retryable": False,
                                        "metadata": {"decision": decision.to_dict()}})
        else:
            # APPROVAL_REQUIRED / APPROVAL_EXPIRED / APPROVAL_INVALID -
            # genuinely still pending. Claim, then park at
            # WAITING_FOR_APPROVAL (a Stage B edge declared since Stage B,
            # never used until Stage I) rather than a dead end - calling
            # execute_step() again once approved is the re-entry point
            # (see the status guard above).
            msn.transition_step(step_id, mission_id, user_id, "RUNNING")
            msn.transition_step(step_id, mission_id, user_id, "WAITING_FOR_APPROVAL",
                                 error={"code": "APPROVAL_REQUIRED", "category": "POLICY",
                                        "severity": "WARNING", "retryable": True,
                                        "metadata": {"decision": decision.to_dict()}})
        raise ApprovalRequiredError(mission_id, step_id, decision)

    # Claim the step. This uses Stage B's existing optimistic-lock CAS -
    # the concurrency guarantee comes from missions.py, not from anything
    # new built here. If another caller already claimed this step, this
    # raises StateConflictError and we propagate it unchanged.
    msn.transition_step(step_id, mission_id, user_id, "RUNNING")

    started_at = _now()
    trace = [f"WORKER_SELECTED:{worker.worker_id}", "WORKER_STARTED"]

    def _run():
        worker.prepare(step)
        raw_output = worker.execute(step, user_id)
        observation = worker.observe(step, raw_output)
        return raw_output, observation

    output = None
    observation = None
    error = None

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_run)
            try:
                output, observation = future.result(timeout=timeout_seconds)
                worker_status = "SUCCEEDED"
                trace += ["WORKER_EXECUTED", "WORKER_OBSERVED", "WORKER_SUCCEEDED"]
            except FuturesTimeoutError:
                worker_status = "TIMED_OUT"
                error = {"code": "TOOL_TIMEOUT", "category": "TIMEOUT", "severity": "ERROR", "retryable": True,
                         "message": f"{worker.worker_id} did not complete within {timeout_seconds}s"}
                trace.append("WORKER_TIMED_OUT")
                # NOTE: the underlying thread is NOT forcibly terminated -
                # Python has no safe mechanism for that. It may still be
                # running in the background after this function returns.
                # This is recorded honestly as TIMED_OUT, never claimed as
                # cancelled or stopped - see this module's docstring.
    except Exception as e:
        worker_status = "FAILED"
        error = {"code": "WORKER_EXECUTION_FAILED", "category": "WORKER", "severity": "ERROR",
                 "retryable": False, "message": str(e), "exception_type": type(e).__name__}
        trace.append("WORKER_FAILED")

    completed_at = _now()
    step_status = WORKER_STATUS_TO_STEP_STATUS[worker_status]
    updated_step = msn.transition_step(step_id, mission_id, user_id, step_status,
                                        output=output, observation=observation, error=error)

    result = WorkerExecutionResult(
        execution_id=execution_id, mission_id=mission_id, step_id=step_id, worker_id=worker.worker_id,
        status=worker_status, output=output, observation=observation, error=error,
        started_at=started_at, completed_at=completed_at, attempt=updated_step["attempt_count"], trace=trace,
    )
    _persist_result(result)
    return result


def cancel_execution(mission_id, step_id, user_id, reason=None) -> dict:
    """Propagates Mission-level cancellation intent down to the MissionStep
    via Stage B's already-idempotent cancel_step(). If a Worker call is
    actively in flight in a background thread, this does NOT and cannot
    force it to stop (see execute_step()'s TIMED_OUT note) - it only marks
    the step CANCELLED in the ledger. Never claim the underlying operation
    was actually interrupted unless it can be verified (spec Section 19)."""
    msn.get_mission(mission_id, user_id)  # user isolation check
    return msn.cancel_step(step_id, mission_id, user_id, reason=reason)
