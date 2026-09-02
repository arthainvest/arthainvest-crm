"""One-time data migration: copies every row from the live SQLite database into the MySQL
database that database_mysql.py's schema targets, preserving original primary key values so
existing foreign-key-shaped references (lead_id, contact_id, etc.) keep pointing at the same
rows after the move.

Usage:
    DATABASE_URL="mysql://user:pass@host:3306/dbname" python migrate_sqlite_to_mysql.py

Safe to re-run: each table's existing MySQL rows are cleared immediately before that table's
SQLite rows are copied in, so running this twice reproduces the same end state rather than
duplicating or accumulating rows. This DOES mean it overwrites whatever is currently in the
target MySQL tables (demo/seed data from init_db(), or a previous partial run) - that is the
point of this script, not a bug, but it means never pointing DATABASE_URL at a database with
real data you want to keep from any source other than this SQLite file.

Prompts for confirmation before touching the target unless run with --yes.
"""
import argparse
import os
import sqlite3
import sys

import database_mysql
import database_sqlite

# (table, integer auto-increment PK column to reset afterwards, or None if the table has no
# such column - either because its PK isn't auto-increment (user_settings keys off the
# users.id value it belongs to) or isn't an integer at all (voice_call_context's PK is Vapi's
# own call id string).
TABLES = [
    ("users", "id"),
    ("companies", "id"),
    ("team_members", "id"),
    ("calls", "id"),
    ("tasks", "id"),
    ("quotations", "id"),
    ("quotation_items", "id"),
    ("leads", "id"),
    ("deals", "id"),
    ("contacts", "id"),
    ("activity_log", "id"),
    ("campaigns", "id"),
    ("campaign_recipients", "id"),
    ("integrations", "id"),
    ("user_settings", None),
    ("contact_notes", "id"),
    ("lead_notes", "id"),
    ("meetings", "id"),
    ("communication_log", "id"),
    ("dial_queue", "id"),
    ("voice_call_context", None),
    ("tags", "id"),
    ("entity_tags", "id"),
    ("groups", "id"),
    ("entity_groups", "id"),
    ("custom_fields", "id"),
    ("custom_field_values", "id"),
    ("whatsapp_conversation", "id"),
    ("whatsapp_message", "id"),
    ("quick_replies", "id"),
    ("flows", "id"),
    ("whatsapp_flow_session", "id"),
    ("google_oauth_tokens", "id"),
    ("zapier_webhooks", "id"),
    ("slack_webhooks", "id"),
]


def _sqlite_connect():
    conn = sqlite3.connect(database_sqlite.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def migrate_table(sqlite_conn, mysql_cursor, table, pk_col):
    rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()

    mysql_cursor.execute(f"DELETE FROM {table}")

    if not rows:
        return 0

    columns = rows[0].keys()
    col_list = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    insert_sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
    for row in rows:
        mysql_cursor.execute(insert_sql, tuple(row[c] for c in columns))

    if pk_col:
        max_id = max(row[pk_col] for row in rows)
        # Integer-validated (came straight from an SQLite INTEGER PRIMARY KEY column) -
        # f-string interpolation here is safe, ALTER TABLE doesn't support bound parameters.
        mysql_cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = {max_id + 1}")

    return len(rows)


def verify(sqlite_conn, mysql_cursor):
    print("\nVerifying row counts (SQLite source vs MySQL target)...")
    mismatches = []
    for table, _ in TABLES:
        sqlite_count = sqlite_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        mysql_cursor.execute(f"SELECT COUNT(*) as c FROM {table}")
        mysql_count = mysql_cursor.fetchone()["c"]
        status = "OK" if sqlite_count == mysql_count else "MISMATCH"
        if status == "MISMATCH":
            mismatches.append(table)
        print(f"  {table}: sqlite={sqlite_count} mysql={mysql_count} [{status}]")
    return mismatches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt")
    args = parser.parse_args()

    if not os.getenv("DATABASE_URL"):
        sys.exit("DATABASE_URL is not set - point it at the target MySQL database first.")

    print(f"Source (SQLite): {database_sqlite.DB_PATH}")
    print(f"Target (MySQL):  {os.getenv('DATABASE_URL').split('@')[-1]}")
    print(f"\nThis will DELETE and replace the contents of {len(TABLES)} tables in the target")
    print("MySQL database with what's currently in the SQLite file above.")
    if not args.yes:
        confirm = input("Type 'yes' to continue: ")
        if confirm.strip().lower() != "yes":
            sys.exit("Aborted.")

    sqlite_conn = _sqlite_connect()
    with database_mysql.get_db() as mysql_conn:
        mysql_cursor = mysql_conn.cursor()
        total = 0
        for table, pk_col in TABLES:
            count = migrate_table(sqlite_conn, mysql_cursor, table, pk_col)
            print(f"  migrated {table}: {count} row(s)")
            total += count
        mysql_conn.commit()
        print(f"\nDone - {total} row(s) migrated across {len(TABLES)} tables.")

        mismatches = verify(sqlite_conn, mysql_cursor)

    sqlite_conn.close()

    if mismatches:
        sys.exit(f"\nRow count mismatch in: {', '.join(mismatches)} - investigate before trusting this migration.")
    print("\nAll row counts match.")


if __name__ == "__main__":
    main()
