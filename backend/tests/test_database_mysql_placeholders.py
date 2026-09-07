"""Unit tests for database_mysql._convert_placeholders, run without a real MySQL connection.

Regression coverage for a real production crash: any query combining a real bind parameter
(so PyMySQL's own %-substitution kicks in) with a literal '%' from something like
DATE_FORMAT(col, '%Y-%m') raised "TypeError: not enough arguments for format string", because
PyMySQL's mogrify does `query % args` and a bare '%Y' isn't a valid format spec it can satisfy.
"""
from database_mysql import _convert_placeholders


def test_plain_placeholder_conversion():
    assert _convert_placeholders("SELECT * FROM t WHERE id = ?") == "SELECT * FROM t WHERE id = %s"


def test_placeholder_inside_quoted_string_is_left_alone():
    assert _convert_placeholders("SELECT '?' FROM t WHERE id = ?") == "SELECT '?' FROM t WHERE id = %s"


def test_literal_percent_is_escaped_alongside_a_real_placeholder():
    query = "SELECT * FROM calls WHERE DATE_FORMAT(call_date, '%Y-%m') = ? AND team_member_id = ?"
    converted = _convert_placeholders(query)
    assert converted == "SELECT * FROM calls WHERE DATE_FORMAT(call_date, '%%Y-%%m') = %s AND team_member_id = %s"

    # This is the exact failure mode from production: PyMySQL's mogrify does `query % args`,
    # so simulate that step directly and confirm it no longer raises.
    formatted = converted % ("2026-09", 3)
    assert formatted == "SELECT * FROM calls WHERE DATE_FORMAT(call_date, '%Y-%m') = 2026-09 AND team_member_id = 3"
