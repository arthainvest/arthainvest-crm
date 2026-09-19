"""Minimal tests for the Stage 2 Git Safety Guard's partition logic (guard.evaluate) and its
read-only git subcommand allowlist. Does not touch the real repository - uses plain lists/
dicts as input, matching the pattern the N-24/N-25 gate's real authorized_files would take."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import guard  # noqa: E402


def test_pass_when_only_authorized_files_changed():
    result = guard.evaluate(
        authorized_files=["backend/main.py", "backend/tests/test_automations.py"],
        changed_files=["backend/main.py", "backend/tests/test_automations.py"],
        protected_prefixes=[],
    )
    assert result["result"] == "PASS"
    assert result["unexpected"] == []
    assert result["expected_found"] == ["backend/main.py", "backend/tests/test_automations.py"]
    assert result["expected_missing"] == []


def test_block_when_unauthorized_file_changed():
    result = guard.evaluate(
        authorized_files=["backend/main.py"],
        changed_files=["backend/main.py", "jarvis/proactive.py"],
        protected_prefixes=[],
    )
    assert result["result"] == "BLOCK"
    assert result["unexpected"] == ["jarvis/proactive.py"]


def test_protected_paths_are_visible_and_non_blocking():
    """The exact real-world case this exists for: JARVIS/prospecting files are legitimately
    mid-change from a concurrent, unrelated workstream throughout this whole engagement.
    They must never flip the result to BLOCK, but - per the Stage 2 correction - they must
    ALSO always appear explicitly in the report and the counts, never silently dropped."""
    result = guard.evaluate(
        authorized_files=["backend/main.py"],
        changed_files=["backend/main.py", "jarvis/proactive.py", "prospecting/09_Dashboard.html"],
        protected_prefixes=["jarvis/", "prospecting/"],
    )
    assert result["result"] == "PASS"
    assert result["unexpected"] == []
    assert set(result["protected"]) == {"jarvis/proactive.py", "prospecting/09_Dashboard.html"}
    assert result["counts"] == {"expected": 1, "protected": 2, "unexpected": 0}


def test_protected_prefix_matches_bare_directory_name_too():
    result = guard.evaluate(
        authorized_files=[],
        changed_files=["jarvis/x.py"],
        protected_prefixes=["jarvis"],  # no trailing slash
    )
    assert result["protected"] == ["jarvis/x.py"]
    assert result["counts"]["protected"] == 1
    assert result["result"] == "PASS"


def test_expected_missing_is_informational_not_a_failure():
    """A gate that's already been committed (files no longer show as 'changed') must still
    report PASS, not BLOCK - expected_missing is informational only."""
    result = guard.evaluate(
        authorized_files=["backend/main.py", "backend/tests/test_automations.py"],
        changed_files=[],
        protected_prefixes=[],
    )
    assert result["result"] == "PASS"
    assert result["expected_missing"] == ["backend/main.py", "backend/tests/test_automations.py"]


def test_unrelated_authorized_files_not_present_do_not_cause_block():
    result = guard.evaluate(
        authorized_files=["backend/main.py"],
        changed_files=["backend/schemas.py"],
        protected_prefixes=[],
    )
    assert result["result"] == "BLOCK"
    assert result["unexpected"] == ["backend/schemas.py"]
    assert result["expected_missing"] == ["backend/main.py"]


def test_guard_only_allows_read_only_git_subcommands():
    with pytest.raises(ValueError):
        guard._run_git(["commit", "-m", "nope"], cwd=".")
    with pytest.raises(ValueError):
        guard._run_git(["push"], cwd=".")
    with pytest.raises(ValueError):
        guard._run_git(["reset", "--hard"], cwd=".")


def test_load_protected_prefixes_missing_file_returns_empty_list(tmp_path):
    missing = tmp_path / "does_not_exist.json"
    assert guard.load_protected_prefixes(missing) == []


def test_format_report_shows_pass_and_block():
    pass_result = guard.evaluate(["a"], ["a"], [])
    pass_result["gate"] = "TEST-1"
    text = guard.format_report(pass_result)
    assert "RESULT: PASS" in text

    block_result = guard.evaluate(["a"], ["a", "b"], [])
    block_result["gate"] = "TEST-2"
    text = guard.format_report(block_result)
    assert "RESULT: BLOCK" in text
    assert "b" in text


def test_report_always_shows_all_three_categories_even_when_empty():
    """Stage 2 correction: PROTECTED must never look like it silently vanished, and an
    empty category must be shown as explicitly empty (0 / "(none)"), not omitted from the
    report entirely."""
    result = guard.evaluate(authorized_files=["a"], changed_files=["a"], protected_prefixes=[])
    result["gate"] = "TEST-EMPTY-PROTECTED"
    text = guard.format_report(result)
    assert "PROTECTED:   0" in text
    assert "UNEXPECTED:  0" in text
    assert "PROTECTED (known concurrent work, non-blocking) [0]" in text
    assert "UNEXPECTED (neither authorized nor protected - causes BLOCK) [0]" in text


def test_counts_always_present_and_consistent_with_lists():
    result = guard.evaluate(
        authorized_files=["a", "b"],
        changed_files=["a", "c", "d"],
        protected_prefixes=["c"],
    )
    assert result["counts"] == {
        "expected": 2,
        "protected": len(result["protected"]),
        "unexpected": len(result["unexpected"]),
    }
    assert result["protected"] == ["c"]
    assert result["unexpected"] == ["d"]
    assert result["result"] == "BLOCK"
