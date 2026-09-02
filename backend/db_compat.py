"""Backend-selected SQL-fragment helpers for the handful of places main.py needs a real date
function, not just a placeholder value. The cursor shim in database_mysql.py normalizes
`?`/`%s` placeholder style transparently, but SQLite's date functions (date(), datetime(),
julianday(), strftime()) have no placeholder-level equivalent - they're genuinely different
function calls in MySQL. Resolving that difference here, once, as plain SQL-fragment
strings keeps every call site a one-line f-string swap instead of forking business logic
per-backend.
"""
import os

IS_MYSQL = bool(os.getenv("DATABASE_URL"))


def sql_today():
    """CURDATE() vs date('now')."""
    return "CURDATE()" if IS_MYSQL else "date('now')"


def sql_now():
    """NOW() vs SQLite's magic 'now' string literal - needed when comparing "this month"
    against the current moment, e.g. sql_year_month(sql_now())."""
    return "NOW()" if IS_MYSQL else "'now'"


def sql_date_offset(literal, unit="days"):
    """A date offset from today, expressed the way the existing SQLite call site already
    writes it: a quoted SQL string literal like "'-6 days'" (sign + count + unit word),
    not a bound placeholder - main.py:7089 passes this as a fixed literal, never user data.
    MySQL has no single-string interval literal, so for MySQL this parses the literal at
    Python level (safe - it's a hardcoded string, never runtime input) into DATE_ADD/DATE_SUB
    with a real INTERVAL n UNIT clause."""
    if IS_MYSQL:
        text = literal.strip().strip("'\"")
        sign_str, unit_word = text.split(None, 1)
        amount = int(sign_str)
        unit_sql = unit_word.rstrip('s').upper()
        fn = "DATE_SUB" if amount < 0 else "DATE_ADD"
        return f"{fn}(CURDATE(), INTERVAL {abs(amount)} {unit_sql})"
    return f"date('now', {literal})"


def sql_now_offset(placeholder="?"):
    """A datetime `placeholder` seconds in the future from now - used for token-expiry
    timestamps, where the bound param is always a count of seconds (as a string)."""
    if IS_MYSQL:
        return f"DATE_ADD(NOW(), INTERVAL {placeholder} SECOND)"
    return f"datetime('now', {placeholder} || ' seconds')"


def sql_days_between(a_expr, b_expr):
    """(a - b) in days, as a float - TIMESTAMPDIFF(SECOND, b, a)/86400.0 vs
    julianday(a) - julianday(b). Both a_expr/b_expr must be valid date/timestamp SQL
    expressions (column names or nested function calls), not placeholders."""
    if IS_MYSQL:
        return f"(TIMESTAMPDIFF(SECOND, {b_expr}, {a_expr}) / 86400.0)"
    return f"(julianday({a_expr}) - julianday({b_expr}))"


def sql_upsert(conflict_cols, update_cols):
    """The tail clause for an INSERT that should update specific columns on a unique-constraint
    collision - ON DUPLICATE KEY UPDATE col = VALUES(col) vs SQLite's (Postgres-syntax-compatible)
    ON CONFLICT(cols) DO UPDATE SET col = excluded.col. conflict_cols is the UNIQUE constraint
    being upserted against (unused by MySQL, which infers it from whichever unique key collided,
    but required by SQLite's explicit conflict-target syntax); update_cols are the columns to
    refresh from the attempted row."""
    if IS_MYSQL:
        sets = ", ".join(f"{c} = VALUES({c})" for c in update_cols)
        return f"ON DUPLICATE KEY UPDATE {sets}"
    cols = ", ".join(conflict_cols)
    sets = ", ".join(f"{c} = excluded.{c}" for c in update_cols)
    return f"ON CONFLICT({cols}) DO UPDATE SET {sets}"


def sql_year_month(col_expr):
    """'YYYY-MM' of a date/timestamp column - DATE_FORMAT(col, '%Y-%m') vs
    strftime('%Y-%m', col)."""
    if IS_MYSQL:
        return f"DATE_FORMAT({col_expr}, '%Y-%m')"
    return f"strftime('%Y-%m', {col_expr})"
