"""
Phase 3.5 — the three real scenarios specified in the 2026-09-07 redirect,
tested end to end against realistic (synthetic, explicitly-remembered) data:

  1. "Prepare me for my meeting with Raj."
  2. "What should I do next?"
  3. "Send Raj the document." — the critical one: context resolves entities,
     but the ability to act must stay independently gated.

Run directly, same as the other jarvis test files — stdlib only.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import memory as jm  # noqa: E402
import context as ctx  # noqa: E402


def _fresh_db(tmp_path: Path):
    jm.DB_PATH = tmp_path / "test_jarvis.db"
    jm.init_db()


def _seed_raj_scenario():
    """A realistic small world: Raj is a contact, works at a company, which
    has a project, which has a pending task. There's a prior commitment, a
    reference to a document, and (deliberately) a conflicting meeting time -
    mirroring the exact redirect scenario."""
    jm.register_alias("Raj", "contact", 7, source="test-setup")
    jm.link("contact", 7, "works_at", "company", 70)
    jm.link("company", 70, "has_project", "project", 700)
    jm.link("project", 700, "has_task", "task", 7000)

    jm.remember("episodic", "Raj asked for a revised quotation with a longer tenure option",
                source="call notes 2026-09-01", entity_type="contact", entity_id=7, importance=4)
    jm.remember("decision", "Committed to sending Raj the updated loan comparison sheet by Friday",
                source="call notes 2026-09-01", entity_type="contact", entity_id=7, importance=4)
    jm.remember("semantic", "Document: Loan_Comparison_Raj_v2.pdf shared in last meeting",
                source="test-setup", entity_type="contact", entity_id=7, importance=3)
    jm.remember("decision", "Meeting with Raj at 4pm tomorrow", source="calendar-note",
                entity_type="contact", entity_id=7, fact_key="meeting_time:raj:tomorrow")
    jm.remember("decision", "Meeting with Raj at 5pm tomorrow", source="email-note",
                entity_type="contact", entity_id=7, fact_key="meeting_time:raj:tomorrow")


def test_scenario_1_prepare_for_meeting_with_raj():
    """Should retrieve: person -> company -> project -> prior commitments ->
    tasks -> documents, per the redirect's exact wording, from one call."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _seed_raj_scenario()

        result = ctx.assemble_context(
            context="business",
            mission="Prepare me for my meeting with Raj",
            mentions=["Raj"], max_hops=3, budget=25,
        )

        # person
        assert ("contact", 7) in {(e["entity_type"], e["entity_id"]) for e in result["resolved_entities"]}
        # company -> project -> task, multi-hop
        related_ids = {(r["entity_type"], r["entity_id"]) for r in result["related_entities"]}
        assert ("company", 70) in related_ids
        assert ("project", 700) in related_ids
        assert ("task", 7000) in related_ids
        # prior commitments
        contents = [m["content"] for m in result["memories"]]
        assert any("Committed to sending" in c for c in contents), "should surface the prior commitment"
        assert any("revised quotation" in c for c in contents), "should surface the prior ask"
        # documents (stored as a memory referencing the file, since there's no dedicated document entity type yet)
        assert any("Loan_Comparison_Raj" in c for c in contents), "should surface the document reference"
        # and the meeting-time conflict should NOT be silently resolved
        assert len(result["conflicts"]) == 1
        print("  trail:")
        for line in result["trail"]:
            print("   -", line)


def test_scenario_2_what_should_i_do_next_uses_context_not_just_a_sort():
    """Should reflect actual priority/importance/urgency signals from memory,
    not simply return whatever's alphabetically or chronologically first -
    i.e. the ranking in assemble_context's output should differ from
    creation order when importance differs."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        # Deliberately seed in an order where a naive "first created" or
        # "alphabetical" sort would give the WRONG answer.
        jm.remember("task", "Low-priority: tidy up old lead notes", source="test",
                    entity_type="contact", entity_id=1, importance=1)
        jm.remember("task", "URGENT: client's KYC documents expire tomorrow", source="test",
                    entity_type="contact", entity_id=2, importance=5)
        jm.remember("task", "Follow up on a cold lead from last month", source="test",
                    entity_type="contact", entity_id=3, importance=2)

        result = ctx.assemble_context(context="business", mission="What should I do next?",
                                       query=None, entity_refs=[("contact", 1), ("contact", 2), ("contact", 3)],
                                       budget=10)

        # The highest-importance item should rank first, not the first-created one.
        top = result["memories"][0]
        assert "KYC documents expire" in top["content"], (
            f"expected the urgent KYC task to rank first, got: {top['content']!r}"
        )
        assert top["confidence_label"] in ("known", "probably_true")


def test_scenario_3_send_raj_the_document_resolves_but_never_sends():
    """THE critical scenario. Context assembly must identify Raj and the
    document reference - but nothing in this engine may send, message, or
    transmit anything anywhere. Verified two ways: behaviorally (calling
    assemble_context for this exact mission produces no side effect beyond
    reading) and structurally (jarvis/ has no network capability at all, so
    it COULD NOT send even if asked to - see
    test_jarvis_cannot_touch_transactions.py for the structural proof)."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        _seed_raj_scenario()

        # Snapshot the DB's memory/event counts before.
        with jm._connect() as conn:
            before_memories = conn.execute("SELECT COUNT(*) c FROM jarvis_memory").fetchone()["c"]
            before_events = conn.execute("SELECT COUNT(*) c FROM jarvis_events").fetchone()["c"]

        result = ctx.assemble_context(
            context="business",
            mission="Send Raj the document",
            mentions=["Raj"], query="document", budget=15,
        )

        # It DOES correctly identify who and what.
        assert ("contact", 7) in {(e["entity_type"], e["entity_id"]) for e in result["resolved_entities"]}, (
            "should still resolve who 'Raj' is"
        )
        assert any("Loan_Comparison_Raj" in m["content"] for m in result["memories"]), (
            "should still find the document reference"
        )

        # It does NOT act: assemble_context is read-only. Nothing was written -
        # memory/event counts are unchanged (assemble_context never calls
        # remember()/link()/forget(), only recall()/traverse()/detect_conflicts(),
        # all of which are pure reads).
        with jm._connect() as conn:
            after_memories = conn.execute("SELECT COUNT(*) c FROM jarvis_memory").fetchone()["c"]
            after_events = conn.execute("SELECT COUNT(*) c FROM jarvis_events").fetchone()["c"]
        assert after_memories == before_memories, "assemble_context must never write a memory as a side effect"
        assert after_events == before_events, "assemble_context must never log an event as a side effect (it isn't the one taking the action)"

        # And there is no function ANYWHERE in this module or memory.py whose
        # name suggests it could send/transmit something - the capability
        # simply doesn't exist to be accidentally triggered.
        import inspect
        all_function_names = (
            [name for name, _ in inspect.getmembers(ctx, inspect.isfunction)] +
            [name for name, _ in inspect.getmembers(jm, inspect.isfunction)]
        )
        send_like = [n for n in all_function_names if any(w in n.lower() for w in ("send", "transmit", "dispatch", "email", "whatsapp", "message"))]
        assert send_like == [], f"found a send-like function that shouldn't exist in the context engine: {send_like}"


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
