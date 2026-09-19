"""Tests for the Stage 7 read-only state refresh (refresh.carry_forward_production and
refresh.refresh_state's non-git logic). Does not touch the real repository's git state -
uses plain dicts as input, and only exercises live git derivation via a real (but
untouched, read-only) call against this actual repo in one integration-style test."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import refresh  # noqa: E402


def test_carry_forward_copies_existing_verified_commit():
    existing_production = {
        "service": "arthainvest-crm (Render)",
        "deployed_commit": "abc123",
        "deploy_status": "Live",
        "health": "ok",
        "db": "ok",
        "verified_utc": "2026-09-19T11:20:00Z",
    }
    result = refresh.carry_forward_production(existing_production, verified_stage="N-27")

    assert result["last_verified_production_commit"] == "abc123"
    assert result["production_commit_status"] == "carried_forward_not_rechecked"
    assert result["production_commit_verified_at"] == "2026-09-19T11:20:00Z"
    assert result["production_commit_verified_stage"] == "N-27"
    # original fields preserved, not dropped
    assert result["deployed_commit"] == "abc123"
    assert result["health"] == "ok"


def test_carry_forward_never_guesses_when_nothing_exists():
    """The hard rule: no verified commit on record -> null, never invented."""
    result = refresh.carry_forward_production(None, verified_stage=None)

    assert result["last_verified_production_commit"] is None
    assert result["production_commit_status"] == "never_verified"
    assert result["production_commit_verified_at"] is None
    assert result["production_commit_verified_stage"] is None


def test_carry_forward_does_not_mutate_the_input():
    existing_production = {"deployed_commit": "xyz", "verified_utc": "t"}
    original_copy = dict(existing_production)
    refresh.carry_forward_production(existing_production, verified_stage="N-1")
    assert existing_production == original_copy


def test_refresh_state_preserves_non_repo_non_production_fields():
    existing_state = {
        "schema_version": "1.0",
        "gate": "N-27",
        "action": "automations_production_smoke_test",
        "status": "closed",
        "target_commit": "36ead25",
        "scope": {"files": ["backend/main.py"], "description": "x"},
        "allowed": ["read_repo_state"],
        "forbidden": ["jarvis", "prospecting"],
        "tests": {"dedicated": "25/25"},
        "production": {"deployed_commit": "36ead25", "verified_utc": "t"},
        "repo": {"local_branch": "master", "local_head": "OLD", "origin_head": "OLD", "note": "stale"},
        "protected_work": ["jarvis/", "prospecting/"],
        "next_gate": None,
    }
    new_state = refresh.refresh_state(existing_state, cwd=str(Path(__file__).resolve().parent.parent.parent))

    # untouched fields
    assert new_state["gate"] == "N-27"
    assert new_state["action"] == "automations_production_smoke_test"
    assert new_state["status"] == "closed"
    assert new_state["target_commit"] == "36ead25"
    assert new_state["scope"] == existing_state["scope"]
    assert new_state["allowed"] == existing_state["allowed"]
    assert new_state["forbidden"] == existing_state["forbidden"]
    assert new_state["tests"] == existing_state["tests"]
    assert new_state["protected_work"] == existing_state["protected_work"]

    # repo block is live-derived, not the stale placeholder
    assert new_state["repo"]["local_head"] != "OLD"
    assert len(new_state["repo"]["local_head"]) == 40  # a real git sha

    # production carries forward with staleness metadata
    assert new_state["production"]["last_verified_production_commit"] == "36ead25"
    assert new_state["production"]["production_commit_status"] == "carried_forward_not_rechecked"
    assert new_state["production"]["production_commit_verified_stage"] == "N-27"


def test_refresh_state_does_not_mutate_the_input():
    existing_state = {
        "gate": "N-1", "production": {"deployed_commit": "a"},
        "repo": {"local_head": "OLD"},
    }
    original_copy = copy_dict(existing_state)
    refresh.refresh_state(existing_state, cwd=str(Path(__file__).resolve().parent.parent.parent))
    assert existing_state == original_copy


def copy_dict(d):
    import copy
    return copy.deepcopy(d)


def test_build_refresh_report_shape():
    existing_state = {"schema_version": "1.0", "protected_work": ["jarvis/"]}
    new_state = {"last_updated_utc": "2026-01-01T00:00:00Z", "production": {"x": 1}}
    report = refresh.build_refresh_report(existing_state, new_state)

    assert report["executed_by"] == "claude-code"
    assert report["gate"] == "STAGE-7"
    assert report["action"] == "state_refresh"
    assert report["status"] == "passed"
    assert report["production"] == {"x": 1}
    assert "commit" in report["forbidden"]
    assert "push" in report["forbidden"]
    assert "deploy" in report["forbidden"]


def test_get_origin_head_returns_none_when_no_remote_ref(tmp_path):
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    result = refresh.get_origin_head(str(tmp_path))
    assert result is None


def test_main_dry_run_writes_nothing(tmp_path, capsys):
    """--apply omitted -> pure preview, zero file writes."""
    control_dir = tmp_path / ".crm-control"
    control_dir.mkdir()
    state_path = control_dir / "state.json"
    report_path = control_dir / "report.json"
    state_path.write_text(
        '{"schema_version":"1.0","gate":"N-1","production":{"deployed_commit":"a","verified_utc":"t"},'
        '"repo":{},"protected_work":[]}',
        encoding="utf-8",
    )
    before_state = state_path.read_text(encoding="utf-8")

    refresh.main(["--repo", str(Path(__file__).resolve().parent.parent.parent), "--control-dir", str(control_dir)])

    assert state_path.read_text(encoding="utf-8") == before_state  # unchanged
    assert not report_path.exists()  # never created in dry-run
    captured = capsys.readouterr()
    assert "[dry-run]" in captured.err
