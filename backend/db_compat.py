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

# ArthaInvest is a single-timezone Indian business (Asia/Kolkata, UTC+5:30, no DST), but both
# DB servers' own clocks are UTC - Hostinger's MySQL defaults to UTC, and SQLite's date('now')/
# 'now' are hardcoded UTC with no timezone concept at all. Without this offset, every "due
# today" task/renewal/meeting and every "this month" report silently uses the wrong calendar
# day/month for the ~5.5 hours between midnight and 5:30am IST, since the DB still thinks it's
# the previous day in UTC (confirmed live: 00:49 IST on 2026-09-06 was still 2026-09-05 18:49
# UTC). Using a fixed offset rather than a named zone (MySQL's CONVERT_TZ('Asia/Kolkata') or
# SQLite's unsupported-natively named zones) avoids depending on the timezone-name tables being
# loaded on shared hosting, which can't be assumed.
_IST_OFFSET_MINUTES = 330


def sql_today():
    """CURDATE() vs date('now'), both shifted to IST."""
    if IS_MYSQL:
        return "DATE(CONVERT_TZ(NOW(), '+00:00', '+05:30'))"
    return f"date('now', '+{_IST_OFFSET_MINUTES} minutes')"


def sql_now():
    """NOW() vs SQLite's magic 'now' string literal, both shifted to IST - needed when
    comparing "this month" against the current moment, e.g. sql_year_month(sql_now()). The
    SQLite form is deliberately two comma-separated fragments (a timestring plus a modifier),
    valid wherever a single 'now' literal was - e.g. strftime('%Y-%m', 'now', '+330 minutes')."""
    if IS_MYSQL:
        return "CONVERT_TZ(NOW(), '+00:00', '+05:30')"
    return f"'now', '+{_IST_OFFSET_MINUTES} minutes'"


def sql_current_timestamp():
    """A standalone IST 'now' timestamp expression, usable directly as a value (e.g. in an
    INSERT ... VALUES list) rather than as an argument fragment - unlike sql_now(), whose
    SQLite form is only valid nested inside another date function's argument list."""
    if IS_MYSQL:
        return "CONVERT_TZ(NOW(), '+00:00', '+05:30')"
    return f"datetime('now', '+{_IST_OFFSET_MINUTES} minutes')"


def sql_date_offset(literal, unit="days"):
    """An IST-shifted date offset from today, expressed the way the existing SQLite call site
    already writes it: a quoted SQL string literal like "'-6 days'" (sign + count + unit word),
    not a bound placeholder - main.py:8149 passes this as a fixed literal, never user data.
    MySQL has no single-string interval literal, so for MySQL this parses the literal at
    Python level (safe - it's a hardcoded string, never runtime input) into DATE_ADD/DATE_SUB
    with a real INTERVAL n UNIT clause."""
    if IS_MYSQL:
        text = literal.strip().strip("'\"")
        sign_str, unit_word = text.split(None, 1)
        amount = int(sign_str)
        unit_sql = unit_word.rstrip('s').upper()
        fn = "DATE_SUB" if amount < 0 else "DATE_ADD"
        return f"{fn}(DATE(CONVERT_TZ(NOW(), '+00:00', '+05:30')), INTERVAL {abs(amount)} {unit_sql})"
    return f"date('now', '+{_IST_OFFSET_MINUTES} minutes', {literal})"


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
