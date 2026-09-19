"""Read-only State Refresh (Stage 7).

Recomputes the parts of state.json/report.json that Stage 6 found going stale - live repo
facts (local HEAD, origin/master, working-tree status) - and carries forward the last
VERIFIED production commit with explicit staleness metadata, rather than re-checking or
guessing production state. This tool never touches git itself and never re-derives
production facts on its own: those require a human-verified gate (like N-15/N-22/N-27's
live Render-dashboard checks), and this script is not that.

Hard boundaries (same as guard.py - see .crm-control/README.md):
- Only the read-only git subcommands in guard._ALLOWED_GIT_SUBCOMMANDS are ever invoked
  (reused from guard.py, not reimplemented, so there is exactly one allowlist in this whole
  package). No commit/push/reset/rebase/stash/clean/checkout/merge/add is ever available.
- This module never fetches from a remote - `origin/master` is read via `git rev-parse
  origin/master` against whatever was last fetched by a separate, explicit `git fetch`
  (part of every gate's own "fresh git audit" step). No network access happens here.
- Production facts are NEVER (re-)derived here. `carry_forward_production` only copies
  values that already exist in a prior state/report record, stamped with an explicit
  `production_commit_status: "carried_forward_not_rechecked"` - it is never permitted to
  invent a value when none exists (returns null fields instead).
- `apply_refresh` only writes to `state.json`/`report.json` inside `.crm-control/` - it
  never touches any other file, and it is only ever invoked when `main()` is called with
  `--apply` (the default is a dry-run preview to stdout).
"""
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guard  # noqa: E402 - reuses guard._run_git's read-only allowlist, not reimplemented


def _now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_local_head(cwd):
    return guard._run_git(["rev-parse", "HEAD"], cwd)[0]


def get_local_branch(cwd):
    return guard._run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)[0]


def get_origin_head(cwd):
    """Reads the LOCAL copy of origin/master - does not fetch. Its freshness depends on
    whatever a separate, explicit `git fetch` last retrieved (standard practice at the start
    of every gate in this protocol); this function makes no network call itself."""
    try:
        return guard._run_git(["rev-parse", "origin/master"], cwd)[0]
    except Exception:
        return None


def build_repo_snapshot(cwd):
    """Live-derived repo facts - the part of state.json Stage 6 found stale."""
    modified = guard.get_modified_tracked(cwd)
    staged = guard.get_staged(cwd)
    untracked = guard.get_untracked(cwd)
    return {
        "local_branch": get_local_branch(cwd),
        "local_head": get_local_head(cwd),
        "origin_head": get_origin_head(cwd),
        "working_tree": {
            "modified_tracked": modified,
            "staged": staged,
            "untracked": untracked,
        },
        "note": (
            "Live-derived at refresh time via read-only git only (no fetch performed by "
            "this script - origin_head reflects the last explicit `git fetch`). "
            "working_tree lists are exactly what guard.py's own read-only helpers see."
        ),
    }


def carry_forward_production(existing_production, verified_stage):
    """Never re-derives production facts. Copies whatever a prior VERIFIED record already
    contains, adds the four explicit staleness fields Stage 7 was authorized to add, and
    returns null fields (never a guess) when no prior record exists."""
    existing_production = existing_production or {}
    result = copy.deepcopy(existing_production)
    last_verified_commit = existing_production.get("deployed_commit")
    verified_at = existing_production.get("verified_utc")
    result["last_verified_production_commit"] = last_verified_commit
    result["production_commit_status"] = (
        "carried_forward_not_rechecked" if last_verified_commit else "never_verified"
    )
    result["production_commit_verified_at"] = verified_at
    result["production_commit_verified_stage"] = verified_stage if last_verified_commit else None
    return result


def refresh_state(existing_state, cwd):
    """Returns a NEW state dict: `repo` is fully live-derived, `production` is carried
    forward with staleness metadata, and every other field (gate/action/status/
    target_commit/scope/tests/protected_work/next_gate) is preserved unchanged - Stage 7's
    authorization is scoped to fixing exactly the staleness Stage 6 found, not rewriting
    what a gate record means."""
    new_state = copy.deepcopy(existing_state)
    new_state["last_updated_utc"] = _now_utc()
    new_state["repo"] = build_repo_snapshot(cwd)
    new_state["production"] = carry_forward_production(
        existing_state.get("production"), existing_state.get("gate")
    )
    return new_state


def build_refresh_report(existing_state, new_state):
    """Builds the report.json record for THIS refresh action itself."""
    return {
        "schema_version": existing_state.get("schema_version", "1.0"),
        "executed_by": "claude-code",
        "timestamp_utc": new_state["last_updated_utc"],
        "gate": "STAGE-7",
        "action": "state_refresh",
        "status": "passed",
        "target_commit": None,
        "scope": {
            "files": [".crm-control/state.json", ".crm-control/report.json"],
            "description": "Read-only refresh: live-derived repo facts (local HEAD, origin/master, working-tree state); production facts carried forward from the last verified record with explicit staleness metadata, never re-derived or guessed.",
        },
        "allowed": ["read_repo_state"],
        "forbidden": [
            "jarvis", "prospecting", "commit", "push", "deploy",
            "reset", "rebase", "stash", "clean", "checkout", "merge",
            "code_changes", "production_reverification", "authorization_inference",
        ],
        "tests": None,
        "production": new_state["production"],
        "protected_work": existing_state.get("protected_work", []),
        "next_gate": None,
    }


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository root (default: cwd)")
    parser.add_argument("--control-dir", default=None, help="Path to .crm-control (default: <repo>/.crm-control)")
    parser.add_argument("--apply", action="store_true", help="Write the refreshed state.json/report.json (default: dry-run preview only)")
    args = parser.parse_args(argv)

    control_dir = Path(args.control_dir) if args.control_dir else Path(args.repo) / ".crm-control"
    state_path = control_dir / "state.json"
    report_path = control_dir / "report.json"

    existing_state = load_json(state_path)
    new_state = refresh_state(existing_state, args.repo)
    new_report = build_refresh_report(existing_state, new_state)

    print(json.dumps({"state": new_state, "report": new_report}, indent=2))

    if args.apply:
        write_json(state_path, new_state)
        write_json(report_path, new_report)
        print(f"\n[applied] wrote {state_path} and {report_path}", file=sys.stderr)
    else:
        print("\n[dry-run] no files written - pass --apply to write state.json/report.json", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
