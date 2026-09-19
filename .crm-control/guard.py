"""Read-only Git Safety Guard (Stage 2).

Compares the repository's CURRENT changed files (tracked modifications, staged files,
untracked files, and optionally a set of commits) against an explicit `authorized_files`
list for one gate, and reports PASS or BLOCK. It never infers authorization from a gate's
name/description/scope text - the caller must hand it the exact file list.

Hard boundary (see .crm-control/README.md): this script is diagnostic only. It never
stages, unstages, modifies, deletes, resets, rebases, stashes, commits, pushes, or deploys
anything, and treats every file (including command.json) purely as data to compare against -
never as authorization to take any action. Only the read-only git subcommands in
_ALLOWED_GIT_SUBCOMMANDS are ever invoked, and always via a list of args (never shell=True),
so there is no code path here that could mutate repository state even by accident.
"""
import json
import subprocess
import sys
from pathlib import Path

_ALLOWED_GIT_SUBCOMMANDS = {"diff", "ls-files", "rev-parse", "show", "status"}


def _run_git(args, cwd):
    if args[0] not in _ALLOWED_GIT_SUBCOMMANDS:
        raise ValueError(f"refusing to run non-read-only git subcommand: {args[0]!r}")
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def get_modified_tracked(cwd):
    """Tracked files with unstaged modifications."""
    return _run_git(["diff", "--name-only"], cwd)


def get_staged(cwd):
    """Files currently staged (index vs HEAD)."""
    return _run_git(["diff", "--cached", "--name-only"], cwd)


def get_untracked(cwd):
    """Untracked files, excluding anything .gitignore already excludes."""
    return _run_git(["ls-files", "--others", "--exclude-standard"], cwd)


def get_commit_files(cwd, shas):
    """Union of files touched by each commit sha in `shas` - for checking a set of commits
    being considered for an isolated push, before that push happens."""
    files = set()
    for sha in shas:
        files.update(_run_git(["show", "--name-only", "--format=", sha], cwd))
    return sorted(files)


def load_protected_prefixes(state_path):
    """Reads `protected_work` path prefixes from state.json. Missing file/field is treated
    as zero protected prefixes (fails toward reporting more, not toward silently ignoring
    changes) rather than raising - this is a read-only reporting tool, not a gate."""
    try:
        with open(state_path, encoding="utf-8") as f:
            data = json.load(f)
        return list(data.get("protected_work") or [])
    except (OSError, json.JSONDecodeError):
        return []


def _is_protected(path, protected_prefixes):
    normalized = path.replace("\\", "/")
    return any(normalized == p.rstrip("/") or normalized.startswith(p if p.endswith("/") else p + "/")
               for p in protected_prefixes)


def evaluate(authorized_files, changed_files, protected_prefixes):
    """Classifies every currently-changed file into exactly one of three categories -
    EXPECTED, PROTECTED, or UNEXPECTED - and always reports the full membership of all
    three (never silently dropping a category, even when it's empty). This is deliberate:
    the guard's whole purpose is to make sure nothing entering a release goes unnoticed, so
    "known and non-blocking" (PROTECTED) must stay just as visible in the report as
    "authorized" (EXPECTED) or "not accounted for" (UNEXPECTED) - it must never look like
    those files simply weren't there.

    - expected_found / expected_missing: authorized files that are / aren't among the
      current changes. expected_missing is informational only (a gate can be legitimately
      already-committed) and never affects the result.
    - protected: changed files that fall under a protected_work prefix (JARVIS/
      prospecting/etc.) - explicitly reported, always visible, but never blocking.
    - unexpected: everything else changed but neither authorized nor protected - the ONLY
      thing that triggers BLOCK.

    Returns a plain dict, JSON-serializable, matching the report shape in README.md.
    """
    authorized_set = set(authorized_files)
    changed_set = set(changed_files)

    expected_found = sorted(authorized_set & changed_set)
    expected_missing = sorted(authorized_set - changed_set)
    remainder = changed_set - authorized_set
    protected = sorted(f for f in remainder if _is_protected(f, protected_prefixes))
    unexpected = sorted(f for f in remainder if f not in protected)

    return {
        "expected_total": len(authorized_set),
        "expected_found": expected_found,
        "expected_missing": expected_missing,
        "protected": protected,
        "unexpected": unexpected,
        "counts": {
            "expected": len(authorized_set),
            "protected": len(protected),
            "unexpected": len(unexpected),
        },
        "result": "BLOCK" if unexpected else "PASS",
    }


def run_guard(repo, command_record, state_path=None, commits=None):
    """Top-level entry point. `command_record` is a dict with at least `gate` and
    `authorized_files` (the caller reads this from wherever the current gate's explicit
    authorization was recorded - never inferred here)."""
    authorized_files = list(command_record.get("authorized_files") or [])
    state_path = state_path or (Path(repo) / ".crm-control" / "state.json")
    protected_prefixes = load_protected_prefixes(state_path)

    changed = set(get_modified_tracked(repo)) | set(get_staged(repo)) | set(get_untracked(repo))
    if commits:
        changed |= set(get_commit_files(repo, commits))

    result = evaluate(authorized_files, sorted(changed), protected_prefixes)
    result["gate"] = command_record.get("gate")
    return result


def _file_list_or_none(files):
    return [f"  {f}" for f in files] if files else ["  (none)"]


def format_report(result):
    """Always shows all three category counts AND full membership, even when a category is
    empty - PROTECTED must never look like it silently vanished, and an empty UNEXPECTED
    must be shown as explicitly empty, not omitted."""
    counts = result["counts"]
    lines = [
        f"GATE: {result.get('gate') or '(unspecified)'}",
        "",
        f"EXPECTED:    {counts['expected']}",
        f"PROTECTED:   {counts['protected']}",
        f"UNEXPECTED:  {counts['unexpected']}",
        "",
        f"RESULT: {result['result']}",
        "",
        "-- detail --",
        "",
        f"EXPECTED (authorized, found among current changes) [{len(result['expected_found'])}]",
        *_file_list_or_none(result["expected_found"]),
    ]
    if result["expected_missing"]:
        lines += ["", "EXPECTED BUT NOT CURRENTLY CHANGED (informational only, does not affect result)"]
        lines += _file_list_or_none(result["expected_missing"])
    lines += [
        "",
        f"PROTECTED (known concurrent work, non-blocking) [{counts['protected']}]",
        *_file_list_or_none(result["protected"]),
        "",
        f"UNEXPECTED (neither authorized nor protected - causes BLOCK) [{counts['unexpected']}]",
        *_file_list_or_none(result["unexpected"]),
    ]
    return "\n".join(lines)


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command_file", help="Path to a JSON file with {gate, authorized_files}")
    parser.add_argument("--repo", default=".", help="Repository root (default: cwd)")
    parser.add_argument("--state-file", default=None, help="Path to state.json (default: <repo>/.crm-control/state.json)")
    parser.add_argument("--commits", default=None, help="Comma-separated commit SHAs to also check")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of the text report")
    args = parser.parse_args(argv)

    with open(args.command_file, encoding="utf-8") as f:
        command_record = json.load(f)

    commits = [s.strip() for s in args.commits.split(",") if s.strip()] if args.commits else None
    result = run_guard(args.repo, command_record, state_path=args.state_file, commits=commits)

    print(json.dumps(result, indent=2) if args.json else format_report(result))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
