"""Static guard for a real production bug found while verifying Phase 2A-ii live.

database_mysql.py's cursor auto-converts '?' placeholders to MySQL's '%s' (see
_convert_placeholders), and unconditionally escapes every literal '%' to '%%' first so a
DATE_FORMAT-style format string in a zero-param query survives untouched. That doubling also
hits a query that already spells its placeholders as '%s' - it becomes '%%s', and PyMySQL then
raises "not all arguments converted during string formatting" the instant that query actually
runs with real parameters.

This bit _ensure_chat_channels() in production: it used '%s' directly (copying
_ensure_integrations_catalog's style, which turned out to have the exact same latent bug - just
never exercised, since every catalog entry it might INSERT already existed). Every backend test
in this suite runs against SQLite, which has no such placeholder rewriting, so nothing caught
this before it shipped - 0 channels were ever created against the real MySQL database despite
631 tests passing. This test parses database_mysql.py with Python's ast module (not a fragile
regex) to make sure neither of these two functions can reintroduce the same mistake.

NOTE: a broader sweep also found the same '%s' pattern throughout the MySQL demo-seed block
further down in this file (INSERT INTO users/leads/deals/contacts/calls, guarded behind "if a
genuinely empty database" - apparently never exercised against real production, which has never
been empty). That block lives inside init_db() itself rather than its own helper, so it's now
covered by adding "init_db" to GUARDED_FUNCTIONS below.
"""
import ast
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATABASE_MYSQL_PY = BACKEND_DIR / "database_mysql.py"

# The functions known to build parameterized cursor.execute() calls - init_db()'s demo-seed
# block is included alongside the two helpers the bug originally shipped in (see module
# docstring), so a literal '%s' anywhere a real query runs with params is caught.
GUARDED_FUNCTIONS = ("_ensure_integrations_catalog", "_ensure_chat_channels", "init_db")


def _find_bad_execute_calls(source: str, function_names=GUARDED_FUNCTIONS):
    """Returns (line_number, query_snippet) for every `cursor.execute(query, params)` call
    (2+ positional args) inside one of `function_names` whose query argument is a string
    literal containing '%s'. A zero/one-arg call is exempt - this cursor only rewrites the
    query when params is truthy."""
    tree = ast.parse(source, filename=str(DATABASE_MYSQL_PY))
    violations = []

    for func_node in ast.walk(tree):
        if not (isinstance(func_node, ast.FunctionDef) and func_node.name in function_names):
            continue
        for node in ast.walk(func_node):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            is_execute_call = (
                isinstance(func, ast.Attribute) and func.attr == "execute"
                and isinstance(func.value, ast.Name) and func.value.id == "cursor"
            )
            if not is_execute_call or len(node.args) < 2:
                continue

            query_arg = node.args[0]
            if isinstance(query_arg, ast.Constant) and isinstance(query_arg.value, str):
                if "%s" in query_arg.value:
                    violations.append((node.lineno, query_arg.value.strip()[:80]))

    return violations


def test_no_parameterized_query_uses_literal_percent_s_placeholders():
    source = DATABASE_MYSQL_PY.read_text(encoding="utf-8")
    violations = _find_bad_execute_calls(source)
    assert not violations, (
        "Found parameterized cursor.execute(query, params) call(s) using literal '%s' "
        "placeholders in one of " + ", ".join(GUARDED_FUNCTIONS) + ". This cursor expects '?' "
        "(it converts '?' -> '%s' itself); a query that already contains '%s' gets "
        "double-escaped to '%%s' and raises 'not all arguments converted during string "
        "formatting' the moment it actually runs with real parameters. Use '?' instead:\n"
        + "\n".join(f"  line {ln}: {snippet!r}" for ln, snippet in violations)
    )


def test_guard_itself_detects_the_original_bug_shape():
    """Sanity check on the test itself: if this ever stops detecting the exact bug shape that
    shipped to production, the guard above would be silently useless."""
    bad_source = '''
def _ensure_chat_channels(cursor, conn):
    cursor.execute("SELECT id FROM conversations WHERE slug = %s", (slug,))
'''
    violations = _find_bad_execute_calls(bad_source)
    assert len(violations) == 1
    assert "%s" in violations[0][1]
