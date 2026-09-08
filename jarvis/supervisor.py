#!/usr/bin/env python3
"""
JARVIS Supervisor — Stage E: turns the Worker Runtime (Stage D) into a
controlled mission execution loop.

    Mission
      |
    Supervisor (this file)
      |
    Ready Step Selection   (reuses missions.advance_ready_steps - Stage B)
      |
    Worker Runtime          (reuses workers.execute_step - Stage D)
      |
    Observation
      |
    Mission State Update    (Stage B's own state machine - never bypassed)
      |
    Next Ready Step
      |
      ... repeat until a terminal or hand-off condition is reached

## What "mission completion detection" means here (read before changing this)

`worker success != verified success` (spec Section 12). Stage F (the
Verifier) does not exist yet. So this Supervisor NEVER sets a Mission to
COMPLETED, PARTIALLY_COMPLETED, or FAILED - all three are outcome
judgments that belong to Stage F. What it DOES do on its own authority:

  - All steps terminal, none FAILED/BLOCKED/CANCELLED -> mission moves
    EXECUTING -> VERIFYING and the loop stops. This says "all attempted
    work finished cleanly, ready for a Verifier to look at it" - it is
    NOT a claim that the mission succeeded.
  - Some step FAILED/BLOCKED/CANCELLED (so the mission can never fully
    finish as planned) -> mission moves to BLOCKED and the loop stops.
    BLOCKED is the one mission-level judgment this stage is explicitly
    authorized to make (spec Section 14's own worked example is exactly
    this shape).
  - No ready steps, no in-flight steps, but PENDING steps remain whose
    dependencies can never be satisfied (a dependency already reached a
    non-SUCCEEDED terminal state) -> also BLOCKED, for the same reason -
    the Supervisor must not spin forever waiting for a step that can
    never become ready (spec Section 14).

## What this stage does NOT do
No retries (Stage G - a FAILED step stays FAILED; there is still no
FAILED -> READY edge in Stage B's state machine). No fallback, no
replanning. No real concurrent dispatch - see `batch_size` below. No
verification of outcomes. No Recovery Engine behavior of any kind.
"""

import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))

import missions as msn  # noqa: E402
import workers  # noqa: E402

# The only mission-level transitions this stage ever performs, plus the
# fixed "start a fresh/resumed mission" happy path - nothing here invents
# a Stage B transition that doesn't already exist in missions.py.
_HAPPY_PATH = ["UNDERSTANDING", "PLANNING", "READY", "EXECUTING"]
_RESUMABLE_TO_EXECUTING = {"WAITING", "BLOCKED"}

_TERMINATING_STEP_STATUSES = {"FAILED", "BLOCKED", "CANCELLED"}


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
    metadata: dict = field(default_factory=dict)
    error_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=_now)

    def to_dict(self):
        return asdict(self)


class SupervisorError(Exception):
    def __init__(self, error: ErrorObject):
        self.error = error
        super().__init__(error.message)


class SupervisorInvalidStateError(SupervisorError):
    def __init__(self, mission_id, status, message):
        super().__init__(ErrorObject(code="INVALID_MISSION_STATE", category="STATE",
                                      mission_id=mission_id, message=message,
                                      metadata={"status": status}))


class SupervisorBudgetExceededError(SupervisorError):
    def __init__(self, mission_id, budget_name, limit):
        super().__init__(ErrorObject(code="RESOURCE_LIMIT_EXCEEDED", category="RESOURCE_LIMIT",
                                      severity="WARNING", retryable=True, mission_id=mission_id,
                                      message=f"{budget_name} limit ({limit}) reached before the mission could finish this pass.",
                                      metadata={"budget": budget_name, "limit": limit}))


# ---------------------------------------------------------------------------
# Supervisor
# ---------------------------------------------------------------------------

class Supervisor:
    """One Supervisor instance drives one supervise() call for one user.
    Stateless between calls except for the cooperative `_stopped` flag -
    all real state lives in Stage B's persisted Mission/MissionStep rows,
    per spec Section 16 ("preserve mission state... avoid duplicate
    execution after restart"). A fresh Supervisor created after a restart
    and pointed at the same mission_id picks up exactly where the ledger
    left off - there is no supervisor-side state to lose.

    `batch_size` bounds how many READY steps are considered per scheduling
    pass. Dispatch itself stays strictly sequential within this stage -
    one execute_step() call completes fully before the next starts. Real
    concurrent dispatch (per spec Section 9's "if parallel execution is
    supported, it must have explicit limits/dependency isolation/
    concurrency protection/cancellation/deterministic state updates") is
    deliberately NOT built here - `batch_size` only caps how much work one
    scheduling pass considers before re-checking cancellation/mission
    state, not how many workers run at once."""

    def __init__(self, user_id, registry: workers.WorkerRegistry = None,
                 batch_size: int = 5, max_total_dispatches: int = 500,
                 max_runtime_seconds: float = None, timeout_seconds: float = 30):
        self.user_id = user_id
        self.registry = registry or workers.DEFAULT_REGISTRY
        self.batch_size = batch_size
        self.max_total_dispatches = max_total_dispatches
        self.max_runtime_seconds = max_runtime_seconds  # None = no wall-clock budget (honestly unavailable unless the caller sets one)
        self.timeout_seconds = timeout_seconds
        self._stopped = False

    # -- lifecycle -----------------------------------------------------

    def start_mission(self, mission_id) -> dict:
        """Advances the Mission to EXECUTING via Stage B's own legal edges
        only. Safe to call on a fresh CREATED mission or to resume one
        already partway along (READY/WAITING/BLOCKED) - never invents a
        transition Stage B doesn't already allow."""
        mission = msn.get_mission(mission_id, self.user_id)
        status = mission["status"]

        if status == "EXECUTING":
            return mission
        if status in msn.TERMINAL_MISSION_STATUSES:
            raise SupervisorInvalidStateError(mission_id, status, "cannot start supervision on a terminal mission")

        if status == "CREATED":
            path = _HAPPY_PATH
        elif status in _HAPPY_PATH:
            path = _HAPPY_PATH[_HAPPY_PATH.index(status) + 1:]
        elif status in _RESUMABLE_TO_EXECUTING:
            path = ["EXECUTING"]
        else:
            raise SupervisorInvalidStateError(mission_id, status,
                                               f"mission status {status!r} is not one supervision can resume from")

        for target in path:
            mission = msn.transition_mission(mission_id, self.user_id, target)
        return mission

    def schedule_ready_steps(self, mission_id) -> list:
        """Reuses Stage B's own dependency-aware promotion - no dependency
        logic is duplicated here. Returns the steps just promoted this
        call (not the full set of already-READY steps - see supervise())."""
        return msn.advance_ready_steps(mission_id, self.user_id)

    def dispatch_step(self, mission_id, step_id):
        """Thin pass-through to the Worker Runtime - the Supervisor never
        executes a tool itself. Exceptions propagate; supervise() decides
        what each one means for the mission, this method does not."""
        return workers.execute_step(mission_id, step_id, self.user_id,
                                     registry=self.registry, timeout_seconds=self.timeout_seconds)

    def observe_step(self, mission_id, step_id) -> dict:
        return msn.get_step(step_id, mission_id, self.user_id)

    def cancel_mission(self, mission_id, reason=None) -> dict:
        """Stops future dispatch (sets the cooperative flag) and propagates
        cancellation down to every non-terminal MissionStep, reusing Stage
        B's already-idempotent cancel_mission()/cancel_step(). A step
        whose worker call is already in flight is NOT forcibly interrupted
        - see workers.py's own cancellation note; this only guarantees the
        ledger reflects CANCELLED, never that an in-flight call actually stopped."""
        self._stopped = True
        mission = msn.cancel_mission(mission_id, self.user_id, reason=reason)
        for step in msn.list_steps(mission_id, self.user_id):
            if step["status"] not in msn.TERMINAL_STEP_STATUSES:
                try:
                    workers.cancel_execution(mission_id, step["step_id"], self.user_id, reason=reason)
                except (msn.InvalidStateTransitionError, msn.StateConflictError):
                    pass  # already terminal or claimed by another writer - fine, cancellation is best-effort
        return mission

    def reconcile_mission(self, mission_id) -> dict:
        """Call this before supervise() after a real process restart.
        Reuses Stage B's reconcile_interrupted() (no second restart-
        recovery mechanism built here), filtered to this one mission."""
        swept = msn.reconcile_interrupted(user_id=self.user_id)
        mission_steps = {s["step_id"] for s in msn.list_steps(mission_id, self.user_id)}
        return {
            "missions": [m for m in swept["missions"] if m == mission_id],
            "steps": [s for s in swept["steps"] if s in mission_steps],
        }

    def stop(self):
        """Cooperative shutdown - takes effect at the next loop checkpoint,
        not by interrupting an in-flight dispatch (dispatch_step() is
        synchronous; nothing is left RUNNING mid-call when stop() is
        observed, since the loop only checks between dispatches)."""
        self._stopped = True

    # -- the execution loop ---------------------------------------------

    def supervise(self, mission_id) -> dict:
        """Runs schedule -> dispatch -> reconcile in a loop until a
        terminal/hand-off mission state, cancellation, or a budget is
        reached. Returns {'mission': <final mission dict>, 'events': [...]}."""
        events = []

        def _event(name, **detail):
            events.append({"event": name, "timestamp": _now(), **detail})

        mission = self.start_mission(mission_id)
        _event("MISSION_STARTED", mission_id=mission_id)

        start_time = time.monotonic()
        total_dispatches = 0

        while not self._stopped:
            mission = msn.get_mission(mission_id, self.user_id)

            if mission["status"] == "CANCELLED":
                _event("MISSION_CANCELLED", mission_id=mission_id)
                break
            if mission["status"] in msn.TERMINAL_MISSION_STATUSES:
                break

            if self.max_runtime_seconds is not None and (time.monotonic() - start_time) > self.max_runtime_seconds:
                mission = msn.transition_mission(mission_id, self.user_id, "WAITING", error={
                    "code": "RESOURCE_LIMIT_EXCEEDED", "category": "RESOURCE_LIMIT", "severity": "WARNING",
                    "retryable": True, "message": f"max_runtime_seconds ({self.max_runtime_seconds}) exceeded - "
                                                    "call supervise() again to resume, nothing was lost.",
                })
                _event("SUPERVISOR_STOPPED", reason="max_runtime_seconds exceeded")
                break

            newly_ready = self.schedule_ready_steps(mission_id)
            if newly_ready:
                _event("READY_STEPS_DISCOVERED", step_ids=[s["step_id"] for s in newly_ready])

            all_steps = msn.list_steps(mission_id, self.user_id)
            ready_steps = [s for s in all_steps if s["status"] == "READY"]

            if not ready_steps:
                non_terminal = [s for s in all_steps if s["status"] not in msn.TERMINAL_STEP_STATUSES]
                if not non_terminal:
                    bad = [s for s in all_steps if s["status"] in _TERMINATING_STEP_STATUSES]
                    if not bad:
                        mission = msn.transition_mission(mission_id, self.user_id, "VERIFYING")
                        _event("MISSION_PROGRESS_UPDATED", to="VERIFYING")
                    else:
                        mission = msn.transition_mission(mission_id, self.user_id, "BLOCKED", error={
                            "code": "STEP_TERMINATED_UNSUCCESSFULLY", "category": "STATE", "severity": "ERROR",
                            "message": f"{len(bad)} step(s) ended FAILED/BLOCKED/CANCELLED - mission cannot complete as planned.",
                            "metadata": {"step_ids": [s["step_id"] for s in bad]},
                        })
                        _event("MISSION_BLOCKED", step_ids=[s["step_id"] for s in bad])
                    break
                else:
                    in_flight = [s for s in all_steps if s["status"] in ("RUNNING", "WAITING", "WAITING_FOR_APPROVAL")]
                    if not in_flight:
                        mission = msn.transition_mission(mission_id, self.user_id, "BLOCKED", error={
                            "code": "NO_PROGRESS_POSSIBLE", "category": "STATE", "severity": "ERROR",
                            "message": "Pending steps remain but none can ever become READY - "
                                       "a dependency is stuck in a non-SUCCEEDED terminal state.",
                            "metadata": {"pending_step_ids": [s["step_id"] for s in non_terminal]},
                        })
                        _event("MISSION_BLOCKED", reason="no_progress_possible")
                        break
                    continue  # something is genuinely still in flight - loop again without dispatching

            for step in ready_steps[: self.batch_size]:
                if self._stopped:
                    break
                mission = msn.get_mission(mission_id, self.user_id)
                if mission["status"] == "CANCELLED":
                    break
                if total_dispatches >= self.max_total_dispatches:
                    raise SupervisorBudgetExceededError(mission_id, "max_total_dispatches", self.max_total_dispatches)

                _event("STEP_DISPATCHED", step_id=step["step_id"])
                try:
                    result = self.dispatch_step(mission_id, step["step_id"])
                    total_dispatches += 1
                    if result.status == "SUCCEEDED":
                        _event("STEP_COMPLETED", step_id=step["step_id"])
                    elif result.status in ("FAILED", "TIMED_OUT"):
                        _event("STEP_FAILED", step_id=step["step_id"], worker_status=result.status)
                except workers.WorkerNotFoundError as e:
                    total_dispatches += 1
                    msn.transition_step(step["step_id"], mission_id, self.user_id, "BLOCKED", error=e.error.to_dict())
                    _event("STEP_BLOCKED", step_id=step["step_id"], reason="worker_not_found")
                except workers.WorkerTransactionProhibitedError:
                    total_dispatches += 1
                    _event("STEP_BLOCKED", step_id=step["step_id"], reason="transaction_prohibited")
                except msn.StateConflictError:
                    _event("STEP_BLOCKED", step_id=step["step_id"], reason="claimed_by_another_supervisor")
                except workers.StepNotExecutableError:
                    _event("STEP_BLOCKED", step_id=step["step_id"], reason="already_progressed_elsewhere")

        if self._stopped and mission["status"] not in msn.TERMINAL_MISSION_STATUSES and mission["status"] != "VERIFYING" and mission["status"] != "BLOCKED":
            _event("SUPERVISOR_STOPPED", reason="stop() called")

        return {"mission": mission, "events": events}
