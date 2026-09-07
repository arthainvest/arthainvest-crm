# JARVIS — Stage B Mission Runtime Specification

**Status:** Implemented
**Stage:** B — Mission + MissionStep State Model
**Authority:** Canonical Stage B technical specification
**Implementation:** `jarvis/missions.py`
**Tests:** `jarvis/tests/test_missions.py`

## 1. Purpose

Stage B establishes the durable execution-state foundation for JARVIS. It introduces:

- Mission
- MissionStep
- mission state machines
- step state machines
- persistence
- optimistic concurrency control
- idempotent transitions
- dependency-aware step readiness
- cancellation
- restart recovery
- canonical execution errors
- user isolation

Stage B does not execute external tools.

## 2. Architectural Position

Stage B sits between the Context/Intent layer and the future Agent Runtime.

```
USER
  ↓
INTENT
  ↓
CONTEXT
  ↓
MISSION                 ← Stage B
  ↓
MISSION STEPS           ← Stage B
  ↓
PLANNER                 ← Stage C
  ↓
WORKERS                 ← Stage D
  ↓
SUPERVISOR              ← Stage E
  ↓
VERIFIER                ← Stage F
  ↓
RECOVERY                ← Stage G
```

Stage B is therefore a state ledger, not yet an execution engine.

## 3. Mission

A Mission represents a user's objective. Required fields:

```
mission_id
user_id
goal
intent_id
status
risk_level
plan_id
current_step_id
context_reference
created_at
updated_at
started_at
completed_at
deadline
result
error
verification_state
parent_mission_id
```

## 4. Mission Statuses

The canonical Mission states are:

```
CREATED
UNDERSTANDING
PLANNING
WAITING_FOR_APPROVAL
READY
EXECUTING
WAITING
VERIFYING
RECOVERING
REPLANNING
COMPLETED
PARTIALLY_COMPLETED
FAILED
BLOCKED
CANCELLED
EXPIRED
```

## 5. Mission State Rules

Mission transitions must be explicitly defined. No arbitrary:

```
status = "..."
```

mutation is permitted. All transitions must pass through the state-machine implementation.

Terminal states:

```
COMPLETED
PARTIALLY_COMPLETED
FAILED
BLOCKED
CANCELLED
EXPIRED
```

are immutable unless a future explicitly designed reconciliation mechanism states otherwise. Stage B must not silently reopen terminal missions.

## 6. MissionStep

A MissionStep represents one discrete unit of future mission work. Required fields:

```
step_id
mission_id
worker_id
description
status
attempt_count
max_attempts
dependencies
inputs
expected_output
output
observation
error
verification
created_at
updated_at
started_at
completed_at
```

## 7. MissionStep Statuses

Canonical states:

```
PENDING
READY
RUNNING
WAITING
WAITING_FOR_APPROVAL
BLOCKED
SUCCEEDED
PARTIALLY_SUCCEEDED
FAILED
SKIPPED
CANCELLED
```

## 8. Step State Rules

MissionSteps must use an explicit legal-transition map. The implementation must reject illegal transitions. Examples:

```
PENDING → READY
READY → RUNNING
RUNNING → SUCCEEDED
RUNNING → FAILED
RUNNING → WAITING
RUNNING → BLOCKED
```

A transition such as:

```
READY → SUCCEEDED
```

must not be allowed unless the architecture explicitly defines that path.

Stage B does not introduce a recovery transition such as:

```
FAILED → READY
```

because Recovery Engine is Stage G.

## 9. Terminal Step States

Terminal states are:

```
SUCCEEDED
PARTIALLY_SUCCEEDED
FAILED
SKIPPED
CANCELLED
```

Terminal steps cannot accidentally return to:

```
PENDING
READY
RUNNING
WAITING
```

## 10. Mission/Step Relationship

Every MissionStep must belong to exactly one Mission. The implementation must ensure:

```
step.mission_id == mission.mission_id
```

A step from one user's mission must never be attached to another user's mission.

## 11. Current Step Integrity

If:

```
mission.current_step_id
```

is populated, that step must belong to the same Mission. Cross-mission current-step references are invalid.

## 12. Dependencies

MissionSteps may depend on other MissionSteps. Example:

```
Step A
  ↓
Step B
  ↓
Step C
```

A dependent step cannot become `READY` until its required dependencies satisfy the readiness rules. Stage B provides dependency-aware readiness. Actual scheduling/execution belongs to Stage E.

## 13. Persistence

Mission and MissionStep state must survive process restart. State must not exist only in:

- Python memory
- global variables
- request objects
- temporary objects

Persistent storage must be authoritative.

## 14. Concurrency

Stage B uses optimistic concurrency control. Each mutable persisted object must have a version. Conceptually:

```
version = N
```

An update succeeds only if the stored version is still `N`. On successful update:

```
version = N + 1
```

If another process has already modified the record:

```
STATE_CONFLICT
```

must be returned.

## 15. Idempotency

Repeated transition requests must not corrupt state. Where an idempotency key is supplied:

```
same request
+
same object
+
same idempotency key
```

must produce an equivalent result rather than duplicate state changes. Idempotency must not permit an illegal transition.

## 16. Cancellation

Mission cancellation must be explicit. Cancellation should be idempotent. A mission that is already terminal must not be restarted merely because cancellation is requested. Stage B records cancellation state. Actual worker/tool cancellation is outside Stage B.

## 17. Restart Recovery

Stage B provides:

```
reconcile_interrupted()
```

or the repository-equivalent mechanism. Interrupted active state must be detected after restart. The system must not assume:

```
process crashed
=
external action did not occur
```

However, Stage B does not perform external reconciliation. That belongs to later execution/verification stages.

## 18. Canonical Errors

Stage B must use structured errors. Required codes:

```
INVALID_INPUT
INVALID_STATE_TRANSITION
MISSION_NOT_FOUND
STEP_NOT_FOUND
STATE_CONFLICT
```

Errors should carry enough information to identify:

- mission
- step
- requested transition
- current state
- reason

where appropriate.

## 19. Error Semantics

A failed state transition is not the same as a failed mission. For example:

```
INVALID_STATE_TRANSITION
```

means the requested state mutation was invalid. It must not automatically change the Mission's state to:

```
FAILED
```

unless the state machine explicitly requires that behavior.

## 20. User Isolation

Every Mission is scoped to a `user_id`. Every MissionStep must be reachable only through an authorized Mission. Tests must prove:

```
User A cannot read User B's Mission.
User A cannot modify User B's Mission.
User A cannot read User B's MissionStep.
User A cannot modify User B's MissionStep.
```

Existing RBAC and authorization rules remain authoritative.

## 21. Context Integration

Stage B references the existing Context Engine. It must not create a second memory system. Mission may store:

```
context_reference
```

which points to the relevant context. The Context Engine remains responsible for:

- retrieval
- privacy filtering
- confidence
- entity resolution
- graph traversal
- conflict detection
- context budgeting

## 22. Intent Integration

Mission stores:

```
intent_id
```

This establishes the relationship between the user's intent and the mission. Stage B does not implement the full Intent Lock. Intent Lock is a later stage.

## 23. Risk

Mission and MissionStep support risk metadata. Risk levels should eventually map to:

```
R0
R1
R2
R3
R4
```

Stage B stores the information. The complete permission/approval/action-firewall system is implemented in later stages.

## 24. Verification State

Mission supports:

```
verification_state
```

This allows later Verifier integration. Stage B does not claim that a Mission is verified merely because it is persisted or transitioned successfully.

## 25. What Stage B Does NOT Do

Stage B does not implement:

- Planner
- Worker Runtime
- Supervisor
- Verifier
- Recovery Engine
- Intent Lock
- Approval Gate
- Action Firewall
- Tool Registry
- Connector Registry
- MCP Gateway
- Browser Agent
- Computer-use Agent
- Model Router
- Background Scheduler
- Proactive Intelligence

These are later stages.

## 26. Execution Boundary

Stage B MUST NOT execute external actions. There must be no:

- email sending
- WhatsApp sending
- API side effects
- browser actions
- computer control
- MCP execution
- financial transaction
- payment
- bank action

Mission state is not execution authority.

## 27. Transaction Safety

The permanent JARVIS transaction prohibition remains active. Stage B must not introduce any transaction capability. The Mission model must never be used as a mechanism to bypass transaction policy. If a prohibited transaction is represented at the mission layer, the authoritative policy must still classify it as:

```
TRANSACTION_PROHIBITED
```

and prevent execution in all future stages.

## 28. Security Boundary

Stage B must fail closed on:

- invalid Mission IDs
- invalid Step IDs
- cross-user access
- illegal state transitions
- stale versions
- malformed input

Do not silently repair invalid state.

## 29. Testing Requirements

Stage B tests must cover:

**Mission**
- creation
- valid transitions
- invalid transitions
- terminal immutability
- persistence
- restart behavior
- cancellation

**MissionStep**
- creation
- valid transitions
- invalid transitions
- dependencies
- readiness
- terminal immutability
- persistence

**Concurrency**
- optimistic locking
- stale update rejection
- simultaneous transition protection

**Idempotency**
- repeated transition
- repeated cancellation
- duplicate request

**Errors**
- Mission not found
- Step not found
- invalid state transition
- state conflict
- invalid input

**Security**
- cross-user isolation
- mission/step ownership

**Regression**
All existing JARVIS Phase 1–3.5 tests must remain passing.

## 30. Current Validation

Current Stage B validation:

```
Stage B tests: 16/16 PASSING
Existing JARVIS regression: 20/20 PASSING
Transaction/security regression: PASSING
Production missing imports: 0
```

If these values change, update this section with the actual results. Never leave stale test claims in this document.

*(Re-verified 2026-09-07 at Stage C's checkpoint: Stage B's own 16/16 unchanged and still green as part of the full 61/61 regression sweep — see `JARVIS_SCOPE_AND_ROADMAP.md` §1.7 for Stage C's own validation record.)*

## 31. Implementation

Primary implementation:

```
jarvis/missions.py
```

Primary tests:

```
jarvis/tests/test_missions.py
```

Do not duplicate the implementation in this document. This document defines the contract.

## 32. Known Limitations

Stage B currently does not determine when a `READY` step should execute. That is the responsibility of the future Supervisor. Stage B does not:

- execute tools
- retry failed steps
- dynamically replan
- verify external outcomes
- select models
- select connectors
- request approvals
- authorize tools

These limitations are intentional.

## 33. Stage Dependencies

```
Phase 1
  ↓
Phase 2 — Memory
  ↓
Phase 3 — Context
  ↓
Phase 3.5 — Context Adoption
  ↓
Stage B — Mission Runtime
  ↓
Stage C — Planner
  ↓
Stage D — Worker Runtime
  ↓
Stage E — Supervisor
  ↓
Stage F — Verifier
  ↓
Stage G — Recovery
```

## 34. Definition of Done

Stage B is complete only when:

- Mission exists
- MissionStep exists
- state machines are explicit
- illegal transitions are rejected
- terminal states are protected
- persistence works
- restart reconciliation exists
- optimistic concurrency works
- idempotency works
- cancellation works
- dependency-aware readiness works
- user isolation works
- canonical errors work
- Context Engine integration is preserved
- transaction prohibition remains intact
- tests pass
- regression passes
- dependency audit passes
- documentation reflects the actual implementation

## 35. Next Stage

The next architectural stage is:

**Stage C — Planner**

Stage C will transform:

```
Goal
+
Intent
+
Context
+
Capabilities
+
Constraints
```

into:

```
Validated Plan
→
MissionSteps
```

Stage C must not execute external actions.

*(Status update, 2026-09-07: Stage C is now implemented — see `JARVIS_SCOPE_AND_ROADMAP.md` §1.7 and `jarvis/plans.py` / `jarvis/planner.py` / `jarvis/capabilities.py`. This section is left as originally written, per §31's own rule against duplicating implementation detail into this document — Stage C's contract belongs in its own record, not retrofitted into Stage B's.)*

## 36. Architectural Principle

The central Stage B principle is:

> A Mission records what JARVIS is trying to accomplish; a MissionStep records the work required; neither grants permission to execute external actions.

Execution authority belongs to later runtime layers.

---

**Document Status:** Canonical
**Stage:** B
**Last Updated:** 2026-09-07 (§30 revalidated at the Stage C checkpoint; §35 status note added — no contract change)
**Source of Truth:** `jarvis/missions.py` + `jarvis/tests/test_missions.py` + this specification
