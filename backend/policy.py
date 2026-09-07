"""
JARVIS permanent policy — the single source of truth for rules that must hold
regardless of which skill, agent, or LLM is calling this backend.

Per JARVIS_MASTER_SPEC.md Section 2: "JARVIS MUST NEVER HANDLE MONEY OR
EXECUTE FINANCIAL TRANSACTIONS." This is intentionally enforced here, at the
backend/policy layer, not as an instruction an LLM is asked to follow. An LLM
being told "don't call the transfer endpoint" is a suggestion a bad prompt,
a compromised skill, or a future careless addition could ignore. An app that
refuses to even start if a transaction-shaped route exists is a guarantee.

`check_no_transaction_routes()` is called from two places on purpose:
  1. `main.py`'s startup (`lifespan`) — the app refuses to boot if this ever
     fails, so a bad route can't reach production even if someone forgets to
     run tests.
  2. `backend/tests/test_no_transaction_endpoints.py` — the same check, run
     in CI on every change, so it's caught before merge, not just at boot.

If this check ever fails, the fix is to remove the offending route — not to
edit PROHIBITED_PATH_PATTERNS to let it through. Changing this file is a
deliberate, rare action that should come with an explicit reason and,
ideally, the business owner's explicit sign-off, updated in the same commit
as JARVIS_MASTER_SPEC.md Section 2 if the policy itself is ever meant to
change (it is designed not to).
"""

import re

# Path-segment patterns that would indicate a real money-movement/execution
# endpoint. Matched against the route path only, so finance-adjacent words
# that aren't transaction execution (e.g. "commission", a ledger, not a
# transfer) don't false-positive.
PROHIBITED_PATH_PATTERNS = [
    r"transfer",
    r"\bpay(ment)?s?\b",
    r"\bupi\b",
    r"withdraw",
    r"disburs(e|al)",          # loan *disbursement execution* — tracking a
                                # disbursement that already happened elsewhere
                                # (bank/lender side) is fine; this guards
                                # against JARVIS itself ever triggering one
    r"brokerage.*order",
    r"\border\b.*\b(buy|sell)\b",
    r"\b(buy|sell)\b.*\border\b",
    r"redeem",                 # mutual fund redemption *execution*
    r"purchase.*(fund|insurance|policy)",
    r"bank.*(transfer|debit|credit)",
    r"execute.*trade",
    r"place.*order",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in PROHIBITED_PATH_PATTERNS]


class ProhibitedRoutePolicyViolation(RuntimeError):
    """Raised when a route matching a permanently-prohibited pattern is
    found. Deliberately a RuntimeError subclass so it can't be accidentally
    caught by an `except Exception` around ordinary request handling — this
    should only ever surface at startup and should stop the app cold."""


def find_prohibited_routes(route_paths: list[str]) -> list[tuple[str, str]]:
    """Returns (path, matched_pattern) for every route path that looks like
    a transaction-execution endpoint. Empty list = clean."""
    violations = []
    for path in route_paths:
        for pattern in _COMPILED_PATTERNS:
            if pattern.search(path):
                violations.append((path, pattern.pattern))
    return violations


def check_no_transaction_routes(route_paths: list[str]) -> None:
    """Raises ProhibitedRoutePolicyViolation if any route looks like it could
    move money or execute a transaction. Call this at application startup —
    see main.py's lifespan handler."""
    violations = find_prohibited_routes(route_paths)
    if violations:
        details = "\n".join(f"  {path!r} matched pattern {pat!r}" for path, pat in violations)
        raise ProhibitedRoutePolicyViolation(
            "Refusing to start: found route(s) matching a permanently-prohibited "
            "financial-transaction pattern (JARVIS_MASTER_SPEC.md Section 2). "
            "This is not a bug in this check — it means a route was added that "
            "this business has permanently ruled out. Remove the route; do not "
            "relax the patterns in backend/policy.py to make this pass.\n" + details
        )
