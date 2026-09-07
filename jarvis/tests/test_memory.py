"""
Memory evaluation tests for the JARVIS Context Engine, per the explicit
scenarios requested in the Phase 2 redirect:

  "What does Jarvis remember about X?"
  "Does it retrieve the right preference?"
  "Does it forget information when requested?"
  "Does stale information get downgraded?"
  "Can private information leak into a family context?"

Each scenario below is a real test against a real (temporary) database, not
a description of intended behavior — run this file directly (see __main__)
or via pytest once the environment issue in JARVIS_IMPLEMENTATION_ROADMAP.md
is resolved. This file has zero third-party dependencies (stdlib only,
same as jarvis/memory.py) so it runs in any Python 3.10+ environment,
including this one.
"""

import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import memory as jarvis_memory  # noqa: E402


def _fresh_db(tmp_path: Path):
    """Point the module at a throwaway DB file for this test, and initialize it."""
    jarvis_memory.DB_PATH = tmp_path / "test_jarvis.db"
    jarvis_memory.init_db()


def test_recalls_the_right_fact_about_a_specific_client():
    """'What does Jarvis remember about X?' — with several unrelated
    memories present, recall filtered to one contact returns only that
    contact's memory, not a neighbor's."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        jarvis_memory.remember(
            "episodic", "Rahul said he would send documents on Monday",
            source="test", entity_type="contact", entity_id=101, privacy_level="business",
        )
        jarvis_memory.remember(
            "episodic", "Priya asked about health insurance for her parents",
            source="test", entity_type="contact", entity_id=202, privacy_level="business",
        )

        results = jarvis_memory.recall(context="business", entity_type="contact", entity_id=101)

        assert len(results) == 1, f"expected exactly 1 memory about contact 101, got {len(results)}"
        assert "Rahul" in results[0]["content"]
        assert "Priya" not in results[0]["content"]


def test_retrieves_the_right_preference_among_decoys():
    """'Does it retrieve the right preference?' — a keyword-scoped query
    surfaces the matching preference, not unrelated memories of the same
    type."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        jarvis_memory.remember("identity", "Prefers WhatsApp over email for client updates",
                                source="test", importance=4)
        jarvis_memory.remember("identity", "Prefers calls in the morning, not after 6pm",
                                source="test", importance=3)
        jarvis_memory.remember("identity", "Likes deals summarized in one line, not paragraphs",
                                source="test", importance=3)

        results = jarvis_memory.recall(context="business", query="WhatsApp")

        assert len(results) == 1
        assert "WhatsApp" in results[0]["content"]


def test_forgets_when_asked():
    """'Does it forget information when requested?' — after forget(), the
    memory no longer appears in recall, even though (per the standing
    never-hard-delete policy) the row itself still exists in the database,
    just soft-deleted."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        mid = jarvis_memory.remember("semantic", "Client's old office address (moved since)",
                                      source="test")

        before = jarvis_memory.recall(context="business", query="office address")
        assert len(before) == 1, "memory should be recallable before forgetting"

        forgotten = jarvis_memory.forget(mid)
        assert forgotten is True

        after = jarvis_memory.recall(context="business", query="office address")
        assert len(after) == 0, "forgotten memory should not be recallable anymore"

        # never-hard-delete: the row is still physically present, just marked deleted
        with jarvis_memory._connect() as conn:
            row = conn.execute("SELECT deleted_at FROM jarvis_memory WHERE id = ?", (mid,)).fetchone()
        assert row is not None, "row must still exist in the database (soft delete, not hard delete)"
        assert row["deleted_at"] is not None


def test_stale_information_is_downgraded_not_deleted():
    """'Does stale information get downgraded?' — an old, low-importance,
    never-reconfirmed memory should rank below an equally-relevant fresh
    one, and be flagged stale=True, but should still be recallable (not
    silently dropped) unless the caller explicitly excludes stale results."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))

        # A low-importance memory "created" 200 days ago and never reconfirmed
        # since — well past its staleness window (30 days at importance=2).
        old_timestamp = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
        with jarvis_memory._connect() as conn:
            conn.execute(
                """INSERT INTO jarvis_memory
                   (memory_type, content, source, confidence, importance, privacy_level,
                    created_at, last_confirmed)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                ("semantic", "Was considering a home loan sometime this year", "test",
                 1.0, 2, "business", old_timestamp, old_timestamp),
            )

        # A fresh, equally-worded-topic memory confirmed just now.
        jarvis_memory.remember("semantic", "Considering a home loan next quarter",
                                source="test", importance=2)

        results = jarvis_memory.recall(context="business", query="home loan")
        assert len(results) == 2

        stale_result = next(r for r in results if "sometime this year" in r["content"])
        fresh_result = next(r for r in results if "next quarter" in r["content"])

        assert stale_result["stale"] is True, "the 200-day-old unconfirmed memory should be flagged stale"
        assert fresh_result["stale"] is False, "the just-created memory should not be flagged stale"
        assert results[0]["id"] == fresh_result["id"], "fresh memory should rank above the stale one"

        # exclude_stale should actually exclude it, not just deprioritize
        results_no_stale = jarvis_memory.recall(context="business", query="home loan", include_stale=False)
        assert len(results_no_stale) == 1
        assert results_no_stale[0]["id"] == fresh_result["id"]


def test_private_memory_does_not_leak_into_family_context():
    """'Can private information leak into a family context?' — the single
    highest-stakes test. A memory stored as privacy_level='private' must
    never come back when recalling in the 'family' context (or 'business',
    or any context other than 'private' itself)."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        jarvis_memory.remember(
            "semantic", "Personal medical detail not to be shared with anyone",
            source="test", privacy_level="private",
        )
        jarvis_memory.remember(
            "episodic", "Planning a family trip in December",
            source="test", privacy_level="family_shared",
        )

        family_results = jarvis_memory.recall(context="family")
        business_results = jarvis_memory.recall(context="business")
        personal_results = jarvis_memory.recall(context="personal")
        private_results = jarvis_memory.recall(context="private")

        for results, ctx_name in [(family_results, "family"), (business_results, "business"),
                                   (personal_results, "personal")]:
            contents = [r["content"] for r in results]
            assert not any("medical" in c for c in contents), (
                f"PRIVACY LEAK: private memory surfaced in {ctx_name!r} context: {contents}"
            )

        # but it IS visible in its own ('private') context
        private_contents = [r["content"] for r in private_results]
        assert any("medical" in c for c in private_contents), (
            "private memory should still be recallable in the private context itself"
        )

        # and family_shared memory reaches 'family' and 'personal', but not 'business'
        assert any("family trip" in r["content"] for r in family_results)
        assert any("family trip" in r["content"] for r in personal_results)
        assert not any("family trip" in r["content"] for r in business_results), (
            "family_shared memory leaked into the business context"
        )


def test_knowledge_graph_traversal():
    """Not one of the five explicitly-requested scenarios, but the other
    Phase 2 pillar — confirms the edges table actually supports the 'move
    tomorrow's meeting, what else is connected' use case: traversal finds
    both outgoing and incoming edges for an entity."""
    with tempfile.TemporaryDirectory() as d:
        _fresh_db(Path(d))
        jarvis_memory.link("meeting", 500, "involves", "contact", 101)
        jarvis_memory.link("meeting", 500, "involves", "contact", 202)
        jarvis_memory.link("task", 900, "follows_up_on", "meeting", 500)

        connections = jarvis_memory.related("meeting", 500)
        relations = {(c["relation"], c["other_type"], c["other_id"], c["direction"]) for c in connections}

        assert ("involves", "contact", 101, "outgoing") in relations
        assert ("involves", "contact", 202, "outgoing") in relations
        # task 900 "follows_up_on" meeting 500 — from meeting 500's perspective
        # that's an incoming edge, and the "other" entity is the task, not
        # meeting 500 itself.
        assert ("follows_up_on", "task", 900, "incoming") in relations, (
            f"expected an incoming 'follows_up_on' edge from task 900, got: {relations}"
        )
        assert len(connections) == 3


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
