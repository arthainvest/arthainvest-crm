"""
Tests for jarvis/planner.py — the Stage C entry point that ties the Context
Engine (Phase 3), the capability registry, and the Plan model together. Run
directly:

    python3 jarvis/tests/test_planner.py

Where test_plans.py exercises the deterministic validator in isolation,
this file exercises the full USER GOAL -> CONTEXT -> PLANNER -> PLAN flow,
including the two properties that mattered most in the authorization for
this stage: the Planner never executes anything, and it never bypasses the
Context Engine's own privacy filtering.
"""

import inspect
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import memory as jm  # noqa: E402
import missions as msn  # noqa: E402
import plans  # noqa: E402
import planner  # noqa: E402
import context as ctx  # noqa: E402


def _fresh_db(tmp_path: Path):
    db_file = tmp_path / "test_jarvis_planner.db"
    jm.DB_PATH = db_file
    msn.DB_PATH = db_file
    plans.DB_PATH = db_file
    jm.init_db()
    plans.init_db()  # cascades to msn.init_db()


def _step(local_id, description, **kw):
    d = {"local_id": local_id, "description": description}
    d.update(kw)
    return d


# --- Context integration -----------------------------------------------------

def test_propose_plan_surfaces_relevant_context():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        jm.register_alias("Raj", "contact", 7, source="test-setup")
        jm.remember("decision", "Committed to sending Raj the updated loan comparison sheet by Friday",
                    source="call notes", entity_type="contact", entity_id=7, importance=4)

        mission = msn.create_mission("user-1", "Prepare for meeting with Raj")
        steps = [_step("resolve_raj", "Resolve who Raj is", required_capability="jarvis-context-assembly")]

        result = planner.propose_plan(mission["mission_id"], "user-1", "Prepare for meeting with Raj",
                                       steps, mentions=["Raj"], budget=15)

        assert result["plan"]["status"] == "VALID"
        resolved = {(e["entity_type"], e["entity_id"]) for e in result["context"]["resolved_entities"]}
        assert ("contact", 7) in resolved
        contents = [m["content"] for m in result["context"]["memories"]]
        assert any("Committed to sending" in c for c in contents)


def test_propose_plan_respects_privacy_boundary():
    """The Planner must consume whatever the Context Engine hands back -
    including its privacy filtering - not re-implement or bypass it."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        jm.remember("identity", "A private note that must never appear in a business plan's context",
                    source="test", privacy_level="private", importance=5)

        mission = msn.create_mission("user-1", "Business planning")
        steps = [_step("s1", "Do something business-related", required_capability="ceo-dashboard")]
        result = planner.propose_plan(mission["mission_id"], "user-1", "Business planning", steps,
                                       context_type="business", query="private note")

        contents = [m["content"] for m in result["context"]["memories"]]
        assert not any("private note" in c for c in contents), "a private-tier memory leaked into a business-context plan"


# --- The spec's own worked example (Section 17) ------------------------------

def test_full_prepare_meeting_example_matches_spec_section_17():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        jm.register_alias("Raj", "contact", 7, source="test-setup")
        jm.link("contact", 7, "works_at", "company", 70)
        jm.remember("decision", "Meeting with Raj at 4pm tomorrow", source="calendar",
                    entity_type="contact", entity_id=7)

        mission = msn.create_mission("user-1", "Prepare me for my meeting with Raj tomorrow")
        steps = [
            _step("resolve_raj", "Resolve Raj", required_capability="jarvis-context-assembly"),
            _step("meeting_details", "Retrieve meeting details", required_capability="jarvis-context-assembly",
                  dependencies=["resolve_raj"]),
            _step("communications", "Retrieve relevant communications", required_capability="jarvis-context-assembly",
                  dependencies=["resolve_raj"]),
            _step("project_context", "Retrieve relevant project context", required_capability="jarvis-context-assembly",
                  dependencies=["resolve_raj"]),
            _step("conflicts", "Identify conflicts / open issues", required_capability="jarvis-context-assembly",
                  dependencies=["meeting_details", "communications", "project_context"]),
            _step("briefing", "Generate briefing", required_capability="jarvis-mission-tracking",
                  dependencies=["conflicts"], risk_level="R1"),
            _step("verify", "Verify briefing completeness", required_capability="jarvis-context-assembly",
                  dependencies=["briefing"], risk_level="R1"),
        ]

        result = planner.propose_plan(mission["mission_id"], "user-1",
                                       "Prepare me for my meeting with Raj tomorrow",
                                       steps, mentions=["Raj"])
        plan = result["plan"]
        assert plan["status"] == "VALID"
        assert len(plan["steps"]) == 7

        # No execution has occurred - no MissionSteps exist yet, only the plan.
        assert msn.list_steps(mission["mission_id"], "user-1") == []

        # Materializing is a separate, explicit act (still not execution -
        # just creating the durable step ledger rows).
        materialized = plans.materialize_plan(plan["plan_id"], "user-1")
        assert len(materialized["mission_step_ids"]) == 7
        real_steps = msn.list_steps(mission["mission_id"], "user-1")
        assert all(s["status"] == "PENDING" for s in real_steps), "materializing must not start execution"


# --- Transaction safety, exercised through the full Planner entry point -----

def test_propose_plan_blocks_a_transfer_request_end_to_end():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = msn.create_mission("user-1", "Handle a payment request")
        steps = [_step("s1", "Transfer 10,000 rupees to the vendor")]
        try:
            planner.propose_plan(mission["mission_id"], "user-1", "Transfer 10,000 rupees", steps)
            assert False, "should have raised TransactionProhibitedError"
        except plans.TransactionProhibitedError as e:
            assert e.error.code == "TRANSACTION_PROHIBITED"
        # And nothing was materialized - no MissionSteps exist.
        assert msn.list_steps(mission["mission_id"], "user-1") == []


# --- Idempotency at the Planner level ----------------------------------------

def test_propose_plan_idempotency_key_does_not_duplicate():
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mission = msn.create_mission("user-1", "Something")
        steps = [_step("s1", "Do a thing", required_capability="ceo-dashboard")]
        first = planner.propose_plan(mission["mission_id"], "user-1", "Something", steps, idempotency_key="req-x")
        second = planner.propose_plan(mission["mission_id"], "user-1", "Something", steps, idempotency_key="req-x")
        assert first["plan"]["plan_id"] == second["plan"]["plan_id"]
        assert len(plans.list_plans(mission["mission_id"], "user-1")) == 1


# --- The Planner never executes anything -------------------------------------

def test_planner_and_plans_modules_contain_no_execution_capable_function():
    """Same technique as test_phase35_scenarios.py's scenario 3: prove by
    introspection, not just by review, that nothing in this stage's code
    could execute a tool even by naming accident."""
    execution_like_words = ("execute", "run_step", "invoke", "dispatch", "call_tool", "send", "transmit")
    for module in (plans, planner):
        names = [name for name, _ in inspect.getmembers(module, inspect.isfunction)]
        offenders = [n for n in names if any(w in n.lower() for w in execution_like_words)]
        assert offenders == [], f"{module.__name__} has an execution-shaped function name: {offenders}"


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
