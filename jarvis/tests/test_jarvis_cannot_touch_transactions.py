"""
Explicit instruction (2026-09-07): "keep the transaction prohibition as a
non-negotiable policy layer independent of memory/context. It should never
be possible for a future context-engine or connector change to accidentally
weaken that boundary."

`backend/policy.py` (and main.py's startup check) already guarantee the CRM
backend itself has no transaction-execution routes. This file guards the
OTHER half of that promise: that the JARVIS Context Engine (memory.py,
context.py) is structurally incapable of executing a transaction, not just
policy-instructed not to.

Two independent checks, either of which failing means someone is about to
weaken the boundary and should stop:

1. No network-capable import exists anywhere in jarvis/*.py. Today this
   package only imports stdlib (argparse, json, sqlite3, datetime, pathlib,
   contextlib) — it cannot make an HTTP request to ANYTHING, let alone a
   transaction endpoint, because it has no way to make requests at all. If a
   future change adds `requests`/`urllib`/`httpx`/etc., that's the moment
   this package gains the *capability* to call external APIs — worth a
   deliberate, visible decision, not something that slips in as a side
   effect of an unrelated feature.
2. No prohibited-pattern string (the same patterns backend/policy.py
   enforces against the CRM's own routes) appears anywhere in jarvis/*.py's
   source — reusing that exact pattern list, not a separate copy, so the
   two layers can never drift apart on what counts as prohibited.
"""

import re
import sys
from pathlib import Path

JARVIS_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = JARVIS_DIR.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from policy import find_prohibited_routes  # noqa: E402

# Anything importing one of these would give jarvis/ the ability to make an
# outbound network call — which today it deliberately cannot do at all.
NETWORK_CAPABLE_MODULES = {
    "requests", "urllib", "urllib2", "http.client", "httpx", "aiohttp",
    "socket", "boto3", "botocore",
}

IMPORT_RE = re.compile(r'^\s*(?:import|from)\s+([\w.]+)', re.MULTILINE)


def _jarvis_source_files() -> list[Path]:
    return [p for p in JARVIS_DIR.glob("*.py") if p.name != "__init__.py"]


def test_jarvis_package_has_zero_network_capable_imports():
    violations = []
    for path in _jarvis_source_files():
        source = path.read_text(encoding="utf-8")
        for match in IMPORT_RE.finditer(source):
            module = match.group(1)
            top_level = module.split(".")[0]
            if top_level in NETWORK_CAPABLE_MODULES or module in NETWORK_CAPABLE_MODULES:
                violations.append((path.name, module))

    assert not violations, (
        "jarvis/ imports a network-capable module, which means it has gained "
        "the ability to make outbound requests it didn't have before. This "
        "isn't necessarily wrong, but it's exactly the kind of change the "
        "2026-09-07 instruction said should never happen silently — if this "
        "is deliberate, it needs its own explicit review, not to slip through "
        "this test:\n" + "\n".join(f"  {f}: imports {m}" for f, m in violations)
    )


def test_jarvis_source_contains_no_prohibited_transaction_patterns():
    """Reuses backend/policy.py's exact pattern list — the SAME source of
    truth as the CRM backend's own check — searched against jarvis/*.py's
    source code (function names, string literals, comments, everything),
    not just route paths this time, since jarvis/ has no routes at all."""
    violations = []
    for path in _jarvis_source_files():
        source = path.read_text(encoding="utf-8")
        # find_prohibited_routes expects a list of "paths" to check against
        # the patterns — a full source file works fine as one big "path" to
        # scan, since the patterns are just regexes over text.
        found = find_prohibited_routes([source])
        for _, pattern in found:
            violations.append((path.name, pattern))

    assert not violations, (
        "jarvis/ source contains text matching a permanently-prohibited "
        "financial-transaction pattern:\n" +
        "\n".join(f"  {f}: matched {p!r}" for f, p in violations)
    )


if __name__ == "__main__":
    tests = [test_jarvis_package_has_zero_network_capable_imports,
              test_jarvis_source_contains_no_prohibited_transaction_patterns]
    failures = []
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
        except AssertionError as e:
            failures.append(test.__name__)
            print(f"FAIL: {test.__name__} — {e}")
    print()
    print(f"{len(tests) - len(failures)}/{len(tests)} passed")
    if failures:
        sys.exit(1)
