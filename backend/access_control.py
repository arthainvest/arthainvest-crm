"""Employee data-visibility / access control.

Root cause fixed here: none of the 7 CRM entity tables (contacts, leads, deals, tasks, calls,
quotations, companies) ever filtered by who owns a record - every authenticated user could see
and modify every record. Reported directly as a production bug ("nimita's contacts show up for
samiksha"). This module is the single shared place that decides, for a given caller, which
records they may see or modify - main.py's list/get/write endpoints call into it rather than
each hand-rolling their own ownership check.

Kept as its own module rather than added to main.py's "HELPER FUNCTIONS" section, following the
same instinct that already split out chat_routes.py/calling_providers.py/storage.py/db_compat.py
out of an already-large main.py. Deliberately self-contained (re-derives get_db itself) so
main.py imports this, not the other way around.

The core rule (confirmed with the business owner): admins (users.role = 'admin') see and can
modify everything, no restriction. Everyone else sees/modifies a record only if they are its
assignee or its creator, OR the record's assignee/creator reports directly to them (one level of
manager oversight - team_members.reports_to - not a multi-level/transitive hierarchy, since
nothing deeper than "a manager sees their direct reports' work" was ever asked for).

Two independent identity spaces show up across the 7 entities' ownership columns, and both need
resolving for every caller:
  - `created_by` / deals' `owner_id` store `users.id`.
  - `assigned_team_member_id` / calls' `team_member_id` store `team_members.id`.
A `VisibilityScope` carries both sets so any entity's filter is a single table lookup away.
"""
import os
from dataclasses import dataclass, field
from typing import Optional

IS_MYSQL = bool(os.getenv("DATABASE_URL"))
if IS_MYSQL:
    from database_mysql import get_db
else:
    from database_sqlite import get_db


@dataclass
class VisibilityScope:
    user_ids: set = field(default_factory=set)
    team_member_ids: set = field(default_factory=set)


def get_visibility_scope(cursor, current_user) -> Optional[VisibilityScope]:
    """None means "admin, no restriction" - every call site must treat None as "skip filtering
    entirely", not as an empty/impossible scope. Otherwise resolves the caller's own
    team_members row (same query GET /api/team/me already uses) plus every team_members row
    whose reports_to points at it, and returns the two id-spaces described above."""
    cursor.execute("SELECT role FROM users WHERE id = ?", (current_user['user_id'],))
    role_row = cursor.fetchone()
    if role_row and role_row['role'] == 'admin':
        return None

    scope = VisibilityScope(user_ids={current_user['user_id']})

    cursor.execute("SELECT id FROM team_members WHERE user_id = ?", (current_user['user_id'],))
    self_row = cursor.fetchone()
    if self_row:
        scope.team_member_ids.add(self_row['id'])
        cursor.execute("SELECT id, user_id FROM team_members WHERE reports_to = ?", (self_row['id'],))
        for r in cursor.fetchall():
            scope.team_member_ids.add(r['id'])
            if r['user_id'] is not None:
                scope.user_ids.add(r['user_id'])

    return scope


def _in_clause(values):
    """IN () is invalid SQL, so an empty set is padded with a -1 sentinel id that can never
    match a real row - same convention already used for "no real id" elsewhere in main.py
    (e.g. the deals/calls legacy-owner fallback joins)."""
    values = list(values) if values else [-1]
    return ", ".join(["?"] * len(values)), values


def scope_filter_sql(scope: VisibilityScope, user_id_cols=(), team_member_id_cols=()):
    """Returns (sql_fragment, params): a standalone parenthesized boolean OR-ing every given
    user_id_cols against scope.user_ids and every team_member_id_cols against
    scope.team_member_ids, for the caller to AND into their own WHERE/conditions list.
    Caller must not call this when scope is None (admin) - there is nothing to filter."""
    parts, params = [], []
    for col in user_id_cols:
        placeholders, vals = _in_clause(scope.user_ids)
        parts.append(f"{col} IN ({placeholders})")
        params.extend(vals)
    for col in team_member_id_cols:
        placeholders, vals = _in_clause(scope.team_member_ids)
        parts.append(f"{col} IN ({placeholders})")
        params.extend(vals)
    return "(" + " OR ".join(parts) + ")", params


def scoped_rows(cursor, sql, params, scope, user_id_cols=(), team_member_id_cols=(), order_by=None):
    """Runs `sql` (which must already contain its own WHERE clause, e.g.
    "SELECT id FROM leads WHERE call_id = ?") ANDed with the scope filter when scope is not
    None, then an optional ORDER BY, and returns cursor.fetchall(). Shared by every
    reverse-lookup route (e.g. "leads linked to this Call") so the same AND-the-scope-in shape
    isn't hand-repeated at each of the ~30 call sites across 7 entities."""
    params = list(params)
    if scope is not None:
        clause, scope_params = scope_filter_sql(scope, user_id_cols=user_id_cols, team_member_id_cols=team_member_id_cols)
        sql += " AND " + clause
        params.extend(scope_params)
    if order_by:
        sql += " ORDER BY " + order_by
    cursor.execute(sql, params)
    return cursor.fetchall()


def _column(record, name):
    """Reads one column off `record` regardless of row type. SQLite's cursor.fetchone() returns
    a `sqlite3.Row` - it supports `row[name]` but, unlike a real dict, has NO `.get()` method
    (raising AttributeError, not returning None, for a missing key) - a bug that stayed hidden
    through the entire 705-test suite because every one of those tests runs as the seeded admin
    account, where `scope is None` short-circuits before this code path is ever reached. MySQL's
    cursor (a real DictCursor subclass) supports both `.get()` and `[name]` fine; this helper
    works uniformly across both by using `[name]` with a KeyError/IndexError fallback rather
    than assuming `.get()` exists."""
    try:
        return record[name]
    except (KeyError, IndexError):
        return None


def is_record_visible(scope: Optional[VisibilityScope], record, user_id_cols=(), team_member_id_cols=()) -> bool:
    """Python-side equivalent of scope_filter_sql for a single already-fetched row - works with
    a plain dict, a MySQL DictCursor row, or a raw sqlite3.Row (every call site in main.py
    passes cursor.fetchone()'s result directly, without wrapping it in dict() first)."""
    if scope is None:
        return True
    return (
        any(_column(record, c) in scope.user_ids for c in user_id_cols)
        or any(_column(record, c) in scope.team_member_ids for c in team_member_id_cols)
    )


def assert_record_visible(scope, record, user_id_cols=(), team_member_id_cols=(), detail="You don't have access to this record"):
    """Raises 403 if a single already-fetched record's ownership columns fall outside the
    caller's scope. No-op for admins (scope is None). Import HTTPException lazily to keep this
    module free of a FastAPI import at load time, matching chat_routes.py's own lean-import
    style."""
    if not is_record_visible(scope, record, user_id_cols, team_member_id_cols):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail=detail)


def redact_if_not_visible(scope, row, display_fields, user_id_col=None, team_member_id_col=None):
    """Sets row[f] = None for every field in display_fields when the OTHER entity it was
    denormalized from is outside the caller's scope. Fixes the cross-entity display-name leak:
    a Deal visible to Chirag can still be joined against a Contact owned by Amol for display
    (contact_name) - that name must not leak just because the Deal itself is visible.

    The caller must ALSO select the linked row's own ownership column(s) into `row` under
    user_id_col/team_member_id_col (e.g. "contacts.created_by as _contact_created_by") alongside
    the display field(s) being joined in - this function only ever looks at columns already
    present in `row`, it does not re-query anything itself (see is_company_visible for the one
    exception, where Company's own visibility rule needs a live EXISTS check instead of a plain
    column comparison).

    No-op for admins (scope is None). Also a harmless no-op when there's no linked record at
    all: an absent join leaves the linked row's ownership columns NULL, which never matches any
    real id, so is_record_visible correctly returns False - redacting a display field that was
    already None to None again."""
    if scope is None:
        return
    user_cols = [user_id_col] if user_id_col else []
    tm_cols = [team_member_id_col] if team_member_id_col else []
    if not is_record_visible(scope, row, user_id_cols=user_cols, team_member_id_cols=tm_cols):
        for f in display_fields:
            row[f] = None


def company_visibility_sql(scope):
    """Returns (sql_fragment, params) for company-row visibility. Companies have no assignee/
    creator-only-restricted column of their own that's useful here beyond created_by - per the
    approved data-visibility plan, a company is ALSO visible if the caller can see at least one
    Contact or Deal that references it (e.g. Chirag's own contact whose employer he didn't
    personally create the Company record for). Caller must skip calling this when scope is None
    (admin - no restriction). Moved here from main.py (where it was originally added as
    `_company_visibility_sql`) so `is_company_visible` below can reuse it without a circular
    import - this module is the natural home for every visibility rule, not just the simple
    column-comparison ones."""
    created_clause, created_params = scope_filter_sql(scope, user_id_cols=["companies.created_by"])
    contact_clause, contact_params = scope_filter_sql(scope, user_id_cols=["contacts.created_by"], team_member_id_cols=["contacts.assigned_team_member_id"])
    deal_clause, deal_params = scope_filter_sql(scope, user_id_cols=["deals.owner_id"], team_member_id_cols=["deals.assigned_team_member_id"])
    sql = (
        f"({created_clause}"
        f" OR EXISTS (SELECT 1 FROM contacts WHERE contacts.company_id = companies.id AND {contact_clause})"
        f" OR EXISTS (SELECT 1 FROM deals WHERE deals.company_id = companies.id AND {deal_clause}))"
    )
    return sql, created_params + contact_params + deal_params


def is_company_visible(cursor, scope, company_id):
    """Live re-check of company_visibility_sql for a single id - used to decide whether to
    redact a denormalized company_name shown on another entity's row (Lead/Task/Call/Quotation
    all carry their own direct company_id, a path company_visibility_sql's EXISTS clauses don't
    cover since those only check contacts.company_id/deals.company_id - so a company reachable
    ONLY through a Lead/Task/Call/Quotation link needs this explicit re-check, unlike a company
    shown via a Deal or Contact, which is always already covered by company_visibility_sql's own
    EXISTS clauses by construction (see the audit notes for the full reasoning). Returns True
    (visible, nothing to redact) when scope is None (admin) or company_id is None (no link)."""
    if scope is None or company_id is None:
        return True
    clause, params = company_visibility_sql(scope)
    cursor.execute(f"SELECT 1 FROM companies WHERE companies.id = ? AND {clause}", [company_id] + params)
    return cursor.fetchone() is not None
