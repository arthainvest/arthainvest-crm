"""
Tests for jarvis/plans.py — the Plan + PlanStep model and its deterministic
validator (Stage C). Run directly:

    python3 jarvis/tests/test_plans.py

Focused on the mechanics that don't need the Context Engine (that's
test_planner.py's job): schema validation, dependency graph checks,
capability/transaction checks, versioning, and materialize-to-MissionStep.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import missions as msn  # noqa: E402
import plans  # noqa: E402


def _fresh_db(tmp_path: Path):
    db_file = tmp_path / "test_jarvis_plans.db"
    msn.DB_PATH = db_file
    plans.DB_PATH = db_file
    plans.init_db()


def _mission(tmp_path, user="user-1", goal="Prepare briefing"):
    _fresh_db(tmp_path)
    return msn.create_mission(user, goal)


def _step(local_id, description, **kw):
    d = {"local_id": local_id, "description": description}
    d.update(kw)
    return d


# --- 1. Basic planning ------------------------------------------------------

def test_simple_plan_is_valid():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        result = plans.create_plan(mission["mission_id"], "user-1", "Send a briefing",
                                    [_step("s1", "Pull CRM data", required_capability="ceo-dashboard")])
        validated = plans.validate_plan(result["plan_id"], "user-1")
        assert validated["status"] == "VALID"
        assert validated["version"] == 1


# --- 2/3. Multi-step + parallel planning ------------------------------------

def test_multi_step_plan_with_dependencies_and_parallel_groups():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        steps = [
            _step("read_calendar", "Read calendar", required_capability="jarvis-context-assembly"),
            _step("read_email", "Read recent email", required_capability="jarvis-context-assembly"),
            _step("briefing", "Create briefing", required_capability="jarvis-mission-tracking",
                  dependencies=["read_calendar", "read_email"], risk_level="R1"),
        ]
        result = plans.create_plan(mission["mission_id"], "user-1", "Prepare meeting briefing", steps)
        validated = plans.validate_plan(result["plan_id"], "user-1")
        assert validated["status"] == "VALID"
        # read_calendar and read_email are independent -> same parallel group;
        # briefing depends on both -> a later group.
        groups = validated["parallel_groups"]
        assert {"read_calendar", "read_email"} <= set(groups[0])
        assert "briefing" in groups[-1]
        assert groups[-1] != groups[0]


# --- 4. Missing capability ---------------------------------------------------

def test_missing_capability_returns_capability_unavailable():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        steps = [_step("s1", "Check my Gmail inbox", required_capability="gmail-read")]
        result = plans.create_plan(mission["mission_id"], "user-1", "Check my Gmail", steps)
        validated = plans.validate_plan(result["plan_id"], "user-1")
        assert validated["status"] == "INVALID"
        types = {l["type"] for l in validated["limitations"]}
        assert "CAPABILITY_UNAVAILABLE" in types
        unavailable = [l for l in validated["limitations"] if l["type"] == "CAPABILITY_UNAVAILABLE"][0]
        assert unavailable["capability"] == "gmail-read"
        assert "Stage M" in unavailable["reason"]


def test_unknown_capability_id_is_also_unavailable_not_silently_allowed():
    """A capability nobody registered at all must fail closed, exactly like
    a known-unavailable one - never silently treated as fine."""
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        steps = [_step("s1", "Do something with a made-up tool", required_capability="totally-invented-tool")]
        result = plans.create_plan(mission["mission_id"], "user-1", "Something", steps)
        validated = plans.validate_plan(result["plan_id"], "user-1")
        assert validated["status"] == "INVALID"


# --- 5. Missing input --------------------------------------------------------

def test_unresolved_input_flags_clarification_needed_without_blocking():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        steps = [_step("s1", "Pre-screen the deal", required_capability="credit-manager",
                        unresolved_inputs=["deal_id"])]
        result = plans.create_plan(mission["mission_id"], "user-1", "Pre-screen a deal", steps)
        validated = plans.validate_plan(result["plan_id"], "user-1")
        # Unresolved input alone doesn't block validity - it's a
        # "possible after clarification" signal, not an outright rejection.
        assert validated["status"] == "VALID"
        assert validated["clarification_needed"] is True
        types = {l["type"] for l in validated["limitations"]}
        assert "INPUT_UNRESOLVED" in types


# --- 6. Circular dependency --------------------------------------------------

def test_circular_dependency_is_rejected():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        steps = [
            _step("a", "Step A", dependencies=["b"]),
            _step("b", "Step B", dependencies=["a"]),
        ]
        result = plans.create_plan(mission["mission_id"], "user-1", "Something circular", steps)
        validated = plans.validate_plan(result["plan_id"], "user-1")
        assert validated["status"] == "INVALID"
        types = {l["type"] for l in validated["limitations"]}
        assert "CIRCULAR_DEPENDENCY" in types
        assert validated["parallel_groups"] is None


# --- 7. Invalid plan schema ---------------------------------------------------

def test_missing_description_is_rejected_at_creation():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        try:
            plans.create_plan(mission["mission_id"], "user-1", "Something", [_step("s1", "")])
            assert False, "should have raised"
        except plans.PlanValidationError as e:
            assert e.error.code == "INVALID_INPUT"


def test_duplicate_local_id_is_rejected_at_creation():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        try:
            plans.create_plan(mission["mission_id"], "user-1", "Something",
                               [_step("s1", "first"), _step("s1", "duplicate id")])
            assert False, "should have raised"
        except plans.PlanValidationError:
            pass


def test_unknown_dependency_local_id_is_rejected_at_creation():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        try:
            plans.create_plan(mission["mission_id"], "user-1", "Something",
                               [_step("s1", "refers to nothing", dependencies=["does-not-exist"])])
            assert False, "should have raised"
        except plans.PlanValidationError:
            pass


def test_consequential_step_without_verification_is_invalid():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        steps = [_step("s1", "Send something risky", required_capability="ceo-dashboard",
                        risk_level="R2", verification_required=False)]
        result = plans.create_plan(mission["mission_id"], "user-1", "Something", steps)
        validated = plans.validate_plan(result["plan_id"], "user-1")
        assert validated["status"] == "INVALID"
        types = {l["type"] for l in validated["limitations"]}
        assert "MISSING_VERIFICATION_STRATEGY" in types


# --- 10. Transaction ---------------------------------------------------------

def test_transaction_shaped_step_is_prohibited_not_just_invalid():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        steps = [_step("s1", "Transfer 10000 rupees to the vendor's UPI account")]
        result = plans.create_plan(mission["mission_id"], "user-1", "Pay the vendor", steps)
        try:
            plans.validate_plan(result["plan_id"], "user-1")
            assert False, "should have raised TransactionProhibitedError"
        except plans.TransactionProhibitedError as e:
            assert e.error.code == "TRANSACTION_PROHIBITED"
            assert e.error.category == "POLICY"
            assert e.error.severity == "CRITICAL"
            assert e.error.retryable is False
        # The plan record itself still exists, marked INVALID + flagged,
        # for audit purposes - it was not silently discarded.
        stored = plans.get_plan(result["plan_id"], "user-1")
        assert stored["status"] == "INVALID"
        assert stored["transaction_prohibited"] is True


def test_indirect_transaction_phrasing_is_also_caught():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        steps = [_step("s1", "Redeem the client's mutual fund units")]
        result = plans.create_plan(mission["mission_id"], "user-1", "Handle a redemption request", steps)
        try:
            plans.validate_plan(result["plan_id"], "user-1")
            assert False, "should have raised"
        except plans.TransactionProhibitedError:
            pass


def test_materialize_refuses_a_transaction_prohibited_plan_even_if_forced():
    """Defense in depth: even bypassing validate_plan's raise (e.g. an old
    plan record from before this check existed), materialize_plan() must
    independently refuse a plan flagged transaction_prohibited."""
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        steps = [_step("s1", "Execute a UPI payment")]
        result = plans.create_plan(mission["mission_id"], "user-1", "Pay someone", steps)
        try:
            plans.validate_plan(result["plan_id"], "user-1")
        except plans.TransactionProhibitedError:
            pass
        try:
            plans.materialize_plan(result["plan_id"], "user-1")
            assert False, "should have raised - a prohibited plan must never materialize into MissionSteps"
        except (plans.TransactionProhibitedError, plans.InvalidPlanStateError):
            pass


# --- 11. Replanning -----------------------------------------------------------

def test_replan_supersedes_without_mutating_history():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        v1 = plans.create_plan(mission["mission_id"], "user-1", "Original objective",
                                [_step("s1", "Do the original thing")])
        plans.validate_plan(v1["plan_id"], "user-1")
        original_objective_snapshot = plans.get_plan(v1["plan_id"], "user-1")["objective"]

        v2 = plans.create_replan(mission["mission_id"], "user-1", v1["plan_id"],
                                  "Revised objective", [_step("s1", "Do the revised thing")])
        plans.validate_plan(v2["plan_id"], "user-1")

        v1_after = plans.get_plan(v1["plan_id"], "user-1")
        assert v1_after["status"] == "SUPERSEDED"
        assert v1_after["objective"] == original_objective_snapshot, "replanning must never rewrite the old plan's own content"
        assert v2["version"] == 2
        assert v2["previous_plan_id"] == v1["plan_id"]

        all_plans = plans.list_plans(mission["mission_id"], "user-1")
        assert len(all_plans) == 2, "both versions must remain visible in history"


def test_cannot_replan_from_an_already_superseded_plan():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        v1 = plans.create_plan(mission["mission_id"], "user-1", "v1", [_step("s1", "thing")])
        plans.create_replan(mission["mission_id"], "user-1", v1["plan_id"], "v2", [_step("s1", "thing v2")])
        try:
            plans.create_replan(mission["mission_id"], "user-1", v1["plan_id"], "v3 from stale v1", [_step("s1", "thing v3")])
            assert False, "should have raised"
        except plans.InvalidPlanStateError:
            pass


# --- 12. Idempotency ----------------------------------------------------------

def test_create_plan_idempotency_key_prevents_duplicate_plan():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        first = plans.create_plan(mission["mission_id"], "user-1", "Something", [_step("s1", "thing")],
                                   idempotency_key="req-1")
        second = plans.create_plan(mission["mission_id"], "user-1", "Something else entirely", [_step("s1", "different")],
                                    idempotency_key="req-1")
        assert first["plan_id"] == second["plan_id"], "replaying the same idempotency key must return the same plan, not create a new one"
        assert len(plans.list_plans(mission["mission_id"], "user-1")) == 1


def test_materialize_is_idempotent_no_duplicate_mission_steps():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        steps = [
            _step("s1", "First step", required_capability="ceo-dashboard"),
            _step("s2", "Second step", required_capability="ceo-dashboard", dependencies=["s1"], risk_level="R1"),
        ]
        result = plans.create_plan(mission["mission_id"], "user-1", "Two-step thing", steps)
        plans.validate_plan(result["plan_id"], "user-1")
        first = plans.materialize_plan(result["plan_id"], "user-1")
        second = plans.materialize_plan(result["plan_id"], "user-1")
        assert first["mission_step_ids"] == second["mission_step_ids"]
        assert len(msn.list_steps(mission["mission_id"], "user-1")) == 2, "materializing twice must not double-create steps"


def test_materialize_wires_real_dependencies_between_mission_steps():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        steps = [
            _step("first", "Pull data", required_capability="ceo-dashboard"),
            _step("second", "Use the data", required_capability="ceo-dashboard", dependencies=["first"]),
        ]
        result = plans.create_plan(mission["mission_id"], "user-1", "Something", steps)
        plans.validate_plan(result["plan_id"], "user-1")
        materialized = plans.materialize_plan(result["plan_id"], "user-1")

        mission_steps = {s["step_id"]: s for s in msn.list_steps(mission["mission_id"], "user-1")}
        plan_steps = {s["local_id"]: s for s in plans.list_plan_steps(result["plan_id"], "user-1")}
        first_real_id = plan_steps["first"]["mission_step_id"]
        second_real_id = plan_steps["second"]["mission_step_id"]
        assert mission_steps[second_real_id]["dependencies"] == [first_real_id]


def test_only_valid_plan_can_be_materialized():
    with tempfile.TemporaryDirectory() as d:
        mission = _mission(Path(d))
        result = plans.create_plan(mission["mission_id"], "user-1", "Something",
                                    [_step("s1", "orphaned capability", required_capability="gmail-read")])
        plans.validate_plan(result["plan_id"], "user-1")  # -> INVALID (capability unavailable)
        try:
            plans.materialize_plan(result["plan_id"], "user-1")
            assert False, "should have raised - cannot materialize an INVALID plan"
        except plans.InvalidPlanStateError:
            pass


if __name__ == "__main__":
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_") and callable(obj)]
    failures = []
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
        except AssertionError as e:
            failures.append(test.__name__)
            print(f"FAIL: {test.__name__} — {e}")
        except Exception as e:
            failures.append(test.__name__)
            print(f"ERROR: {test.__name__} — {type(e).__name__}: {e}")

    print()
    print(f"{len(tests) - len(failures)}/{len(tests)} passed")
    if failures:
        sys.exit(1)
