"""
Permanent architectural guarantee, per JARVIS_MASTER_SPEC.md Section 2:

    "JARVIS MUST NEVER HANDLE MONEY OR EXECUTE FINANCIAL TRANSACTIONS."

The actual policy (the pattern list, and why each one is there) lives in
`backend/policy.py`, which is also imported and enforced at application
startup (see `main.py`'s `lifespan` handler) — so this isn't the only place
the rule is checked, just the CI-visible one. See policy.py's docstring for
the full reasoning on why this is a backend rule, not an LLM instruction.

If this test ever fails, that is not a bug in the test — it means someone is
about to add exactly the kind of endpoint this business has permanently ruled
out. Do not relax `backend/policy.py`'s patterns to make a new route pass;
remove the route instead, or get explicit, deliberate sign-off to change
policy.py and JARVIS_MASTER_SPEC.md Section 2 together, in the same commit,
with a clear reason.
"""

import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from policy import find_prohibited_routes  # noqa: E402

MAIN_PY = BACKEND_DIR / "main.py"

ROUTE_DECORATOR_RE = re.compile(
    r'@app\.(?:get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']'
)


def _extract_route_paths() -> list[str]:
    """Static extraction from source, rather than importing main.py, since
    importing it requires the full dependency stack (fastapi, pydantic, a
    reachable database, etc.) which may not be installed/reachable in every
    environment this test runs in. The startup check in main.py's lifespan
    covers the "does the real running app agree" case; this covers "can we
    check this without needing the whole app to boot"."""
    source = MAIN_PY.read_text(encoding="utf-8")
    return ROUTE_DECORATOR_RE.findall(source)


def test_route_extraction_actually_finds_routes():
    """Sanity check on the test itself: if this file's regex ever stops
    matching main.py's route decorator style (e.g. after a refactor), we'd
    otherwise silently test zero routes and always pass for the wrong
    reason. Pin to "at least 200" — comfortably below the current 249, so
    this doesn't need updating every time a route is added or removed, but
    would catch the extraction breaking entirely."""
    routes = _extract_route_paths()
    assert len(routes) >= 200, (
        f"Only found {len(routes)} routes — the route-extraction regex may "
        "no longer match main.py's actual route decorator style. Fix the "
        "regex before trusting this test suite's other result."
    )


def test_no_transaction_execution_endpoints_exist():
    routes = _extract_route_paths()
    violations = find_prohibited_routes(routes)

    assert not violations, (
        "Found route(s) matching a prohibited financial-transaction pattern "
        "(JARVIS_MASTER_SPEC.md Section 2 forbids JARVIS from ever handling "
        "money or executing transactions):\n"
        + "\n".join(f"  {path!r} matched pattern {pat!r}" for path, pat in violations)
    )


def test_patterns_do_not_false_positive_on_known_legitimate_routes():
    """Regression guard: these are real, intentional routes that record
    financial *information* (a ledger entry, a quotation) rather than
    executing a transaction. If a future edit to policy.py's patterns
    starts matching these, the patterns are too broad."""
    legitimate_examples = [
        "/api/commissions",
        "/api/commissions/summary",
        "/api/commissions/{commission_id}",
        "/api/quotations",
        "/api/quotations/{quotation_id}/send",
        "/api/mf-holdings",
        "/api/insurance-policies",
        "/api/deals/{deal_id}/process-status",
    ]
    violations = find_prohibited_routes(legitimate_examples)
    assert not violations, (
        f"policy.py's patterns incorrectly flag legitimate route(s): {violations!r} "
        "— narrow the pattern in backend/policy.py."
    )
