"""MySQL backend for production (e.g. Hostinger's Remote MySQL, reachable from Render over
the network) - selected instead of database_sqlite.py whenever DATABASE_URL is set (see the
switch in main.py). Same compatibility-shim approach as the SQLite path was designed around:
main.py's ~500 existing `cursor.execute()` calls all use SQLite's `?` placeholder style and
rely on `cursor.lastrowid` after INSERT, so the goal here is a cursor that accepts both
unmodified rather than rewriting every call site.

PyMySQL was chosen over mysqlclient/mysql-connector-python because it's pure Python - no
compiled extension, so no risk of a missing prebuilt wheel for the Python version in use
(mysqlclient needs MySQL client dev headers to build from source; hit exactly this problem
with psycopg2-binary during an earlier Postgres attempt on this machine). Unlike psycopg2,
PyMySQL's cursor already has a native, accurate `.lastrowid` after INSERT - so unlike the
Postgres shim, this one needs no "append RETURNING and capture it" trick at all.
"""
import os
import re
from contextlib import contextmanager
from urllib.parse import urlparse, unquote

import pymysql
import pymysql.cursors

IntegrityError = pymysql.err.IntegrityError

# Only the '?' tokens that are genuine placeholders need converting to MySQL's '%s' - one
# that appears inside a quoted SQL string literal (there are none in main.py's queries today,
# but this guards against ever adding one) must be left alone, same quote-aware approach used
# for the earlier Postgres attempt.
_STRING_OR_PLACEHOLDER_RE = re.compile(r"'(?:[^']|'')*'|\?")


def _convert_placeholders(query):
    return _STRING_OR_PLACEHOLDER_RE.sub(lambda m: "%s" if m.group(0) == "?" else m.group(0), query)


class _MySQLCursor(pymysql.cursors.DictCursor):
    def execute(self, query, params=None):
        # Zero-param queries pass through untouched - avoids PyMySQL choking on a stray
        # literal '%' character (e.g. a LIKE pattern, or DATE_FORMAT's '%Y-%m') the way
        # plain %-style substitution would. `params` can be falsy as either None or an empty
        # list/tuple (call sites build up a params list conditionally) - either way must reach
        # PyMySQL as None, since PyMySQL itself only skips its own %-substitution when args
        # `is None`, not merely falsy - passing along an empty list would still trigger it.
        if params:
            query = _convert_placeholders(query)
        else:
            params = None
        return super().execute(query, params)


def _parse_database_url(url):
    """DATABASE_URL as a standard mysql://user:pass@host:port/dbname string - urlparse handles
    this fine regardless of the literal scheme name."""
    parsed = urlparse(url)
    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": unquote(parsed.username) if parsed.username else None,
        "password": unquote(parsed.password) if parsed.password else "",
        "database": parsed.path.lstrip("/"),
    }


@contextmanager
def get_db():
    conn_kwargs = _parse_database_url(os.environ["DATABASE_URL"])
    conn = pymysql.connect(
        cursorclass=_MySQLCursor,
        charset="utf8mb4",
        autocommit=False,
        **conn_kwargs,
    )
    try:
        yield conn
    finally:
        conn.close()


def _create_index_if_missing(cursor, index_name, table, columns):
    """MySQL has no CREATE INDEX IF NOT EXISTS - this runs on every startup, so it must be
    idempotent the same way the CREATE TABLE IF NOT EXISTS statements below already are."""
    try:
        cursor.execute(f"CREATE INDEX {index_name} ON {table}({columns})")
    except pymysql.err.OperationalError as e:
        if e.args[0] != 1061:  # 1061 = ER_DUP_KEYNAME, "Duplicate key name"
            raise


def _add_column_if_missing(cursor, table, column, ddl_type):
    """MySQL has no ADD COLUMN IF NOT EXISTS (pre-8.0.29) - this runs on every startup, so it
    must be idempotent the same way _create_index_if_missing is for indexes."""
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}")
    except pymysql.err.OperationalError as e:
        if e.args[0] != 1060:  # 1060 = ER_DUP_FIELDNAME, "Duplicate column name"
            raise


def _ensure_integrations_catalog(cursor, conn):
    """Insert any catalog integration that doesn't exist yet, by name. Runs on every startup
    (not just first-run seeding) so an integration added after a database was already seeded
    still appears, without duplicating rows on restart."""
    catalog = [
        ('Gmail', '📧', 'Sync emails and contacts from Gmail', 1, '2 hours ago'),
        ('Google Calendar', '📅', 'Sync meetings and schedule', 1, '5 mins ago'),
        ('Zapier', '⚡', 'Connect with 1000+ apps via Zapier', 1, '3 days ago'),
        ('Slack', '💬', 'Send notifications to Slack', 0, 'never'),
        ('HubSpot', '🎯', 'Two-way sync with HubSpot', 1, '5 mins ago'),
        ('Twilio', '📞', 'Click-to-call and SMS via Twilio', 0, 'never'),
        ('Exotel', '📱', 'Multi-agent dialer with call recording via Exotel', 0, 'never'),
        ('Claude AI', '✨', 'AI-drafted follow-ups and note summaries', 0, 'never'),
        ('LinkedIn', '💼', 'Sync leads and posts from LinkedIn', 0, 'never'),
        ('WhatsApp Business API', '💬', 'Send WhatsApp messages via Meta Cloud API', 0, 'never'),
        ('Email Service', '📮', 'Send real emails via SMTP', 0, 'never'),
        ('Mailchimp', '🐒', 'Sync contacts and send email campaigns', 0, 'never'),
        ('Google Sheets', '📊', 'Export contacts/leads to a sheet, or bulk-import leads from one', 0, 'never'),
        ('DigiLocker', '🔐', 'Secure document storage and verification', 0, 'never'),
        ('AI Voice Assistant', '🎙️', 'Automated status updates via voice notes', 0, 'never'),
        ('Google Analytics', '📊', 'Track campaign performance and ROI', 0, 'never'),
        ('Priti (AI Voice Caller)', '📞', 'Outbound AI qualification calls via Vapi', 0, 'never'),
        ('OpenAI', '🤖', 'Fallback AI provider for AI Suggest/Detect Date/Content Studio/chatbot', 0, 'never'),
        ('Facebook Lead Ads', '📘', 'Auto-import leads from Facebook lead-gen campaigns (planned)', 0, 'never'),
        ('IndiaMart', '🅼', 'Auto-fetch leads from your IndiaMart seller account (planned)', 0, 'never'),
        ('TradeIndia', '🅃', 'Auto-fetch leads from your TradeIndia seller account (planned)', 0, 'never'),
        ('Zendesk', '🎫', 'Sync support tickets for client queries (planned)', 0, 'never'),
        ('QuickBooks', '📗', 'Sync commission/invoice records for bookkeeping (planned)', 0, 'never'),
        ('Aircall', '☎️', 'Alternate cloud telephony provider to Twilio (planned)', 0, 'never'),
        ('MSG91', '✉️', 'Combined SMS/WhatsApp/Email sending, alternate to Twilio/SMTP (planned)', 0, 'never'),
        ('Apollo.io', '🎯', 'Lead enrichment and prospecting data (planned)', 0, 'never'),
    ]
    cursor.execute("SELECT name FROM integrations")
    existing = {row['name'] for row in cursor.fetchall()}
    for name, logo, description, connected, last_sync in catalog:
        if name not in existing:
            cursor.execute(
                "INSERT INTO integrations (name, logo, description, connected, last_sync) VALUES (%s, %s, %s, %s, %s)",
                (name, logo, description, connected, last_sync)
            )

    cursor.execute("DELETE FROM integrations WHERE name = 'Razorpay Payments'")
    conn.commit()


def _ensure_team_roster(cursor, conn):
    """Same pattern as _ensure_integrations_catalog - runs on every startup so it appears
    without duplicating on restart."""
    roster = [
        ('Artha', 'admin', 'artha@arthainvest.com', '+91-9876500001', 1),
        ('Team Admin', 'admin', 'admin2@arthainvest.com', '+91-9876500002', None),
        ('Rajesh Kumar', 'team_lead', 'rajesh.kumar@arthainvest.com', '+91-9876500003', None),
        ('Suresh Iyer', 'location_head', 'suresh.iyer@arthainvest.com', '+91-9876500004', None),
        ('Arjun Sharma', 'employee', 'arjun.sharma@arthainvest.com', '+91-9876500005', None),
        ('Priya Singh', 'employee', 'priya.singh@arthainvest.com', '+91-9876500006', None),
        ('Vikram Patel', 'employee', 'vikram.patel@arthainvest.com', '+91-9876500007', None),
    ]
    cursor.execute("SELECT name FROM team_members")
    existing = {row['name'] for row in cursor.fetchall()}
    for name, role, email, phone, user_id in roster:
        if name not in existing:
            cursor.execute(
                "INSERT INTO team_members (name, role, email, phone, user_id) VALUES (%s, %s, %s, %s, %s)",
                (name, role, email, phone, user_id)
            )
    conn.commit()


def init_db():
    """Create the schema if it doesn't exist yet, then seed demo data only on a genuinely
    empty database (first run). Fresh schema (not an ALTER-retrofit chain like
    database_sqlite.py) since this is a brand-new database every time it's pointed at a fresh
    MySQL instance - the final column set, written directly.

    No FOREIGN KEY constraints, matching database_sqlite.py's actual behavior (SQLite never
    enforces them without PRAGMA foreign_keys=ON, which this app never sets) - keeping this
    schema behaviorally identical, and avoiding a circular-dependency table-creation-order
    problem (leads references contacts, contacts references leads' converted-from column, etc).
    UNIQUE constraints ARE kept, since main.py's INSERTs rely on them for upsert targets.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role VARCHAR(50) DEFAULT 'employee',
                full_name TEXT,
                is_active INT DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name TEXT NOT NULL,
                industry TEXT,
                city TEXT,
                phone TEXT,
                email TEXT,
                website TEXT,
                notes TEXT,
                created_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calls (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                duration_seconds INT DEFAULT 0,
                type VARCHAR(50) DEFAULT 'Outbound',
                outcome TEXT,
                call_date DATE,
                created_by INT,
                team_member_id INT,
                lead_id INT,
                contact_id INT,
                company_id INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        # Set by the Exotel dial/status-callback path (see main.py's dial_call and the
        # /api/webhooks/exotel/status handler) - Twilio-dialed calls leave both NULL. Added
        # after the table above already existed in production, so ADD COLUMN not CREATE.
        _add_column_if_missing(cursor, "calls", "recording_url", "TEXT")
        _add_column_if_missing(cursor, "calls", "provider_call_sid", "VARCHAR(255)")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title TEXT NOT NULL,
                due_date DATE NOT NULL,
                completed INT DEFAULT 0,
                priority VARCHAR(50) DEFAULT 'Normal',
                created_by INT,
                assigned_team_member_id INT,
                lead_id INT,
                contact_id INT,
                call_id INT,
                quotation_id INT,
                company_id INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                quotation_number TEXT,
                lead_id INT,
                contact_id INT,
                deal_id INT,
                title TEXT NOT NULL,
                status VARCHAR(50) DEFAULT 'Draft',
                valid_until DATE,
                notes TEXT,
                created_by INT,
                company_id INT,
                call_id INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotation_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                quotation_id INT NOT NULL,
                description TEXT NOT NULL,
                amount DOUBLE DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name TEXT NOT NULL,
                company TEXT,
                email TEXT,
                phone TEXT,
                product TEXT,
                ai_score INT,
                lead_tier TEXT,
                status VARCHAR(50) DEFAULT 'new',
                source TEXT,
                created_by INT,
                assigned_team_member_id INT,
                converted_contact_id INT,
                call_id INT,
                task_id INT,
                deal_id INT,
                company_id INT,
                quotation_id INT,
                contact_id INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                lead_id INT NOT NULL,
                deal_value DOUBLE,
                stage VARCHAR(50) DEFAULT 'new',
                probability DOUBLE,
                loan_product VARCHAR(50) DEFAULT 'LAP',
                expected_close_date DATE,
                owner_id INT,
                notes TEXT,
                assigned_team_member_id INT,
                process_status VARCHAR(50) DEFAULT 'Login',
                company_id INT,
                contact_id INT,
                call_id INT,
                task_id INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name TEXT NOT NULL,
                company TEXT,
                email TEXT,
                phone TEXT,
                city TEXT,
                score INT,
                amount DOUBLE,
                bank TEXT,
                status VARCHAR(50) DEFAULT 'Active',
                renewal_date DATE,
                created_by INT,
                assigned_team_member_id INT,
                company_id INT,
                converted_from_lead_id INT,
                quotation_id INT,
                call_id INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                action TEXT,
                entity_type TEXT,
                entity_id INT,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name TEXT NOT NULL,
                type VARCHAR(50) DEFAULT 'Email',
                status VARCHAR(50) DEFAULT 'Active',
                recipients INT DEFAULT 0,
                opens INT DEFAULT 0,
                clicks INT DEFAULT 0,
                message TEXT,
                created_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_recipients (
                id INT AUTO_INCREMENT PRIMARY KEY,
                campaign_id INT NOT NULL,
                lead_id INT,
                contact_id INT,
                status VARCHAR(50) DEFAULT 'Pending',
                sent_at DATETIME,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS integrations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name TEXT NOT NULL,
                logo TEXT,
                description TEXT,
                connected INT DEFAULT 0,
                last_sync TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INT PRIMARY KEY,
                full_name TEXT,
                email TEXT,
                phone TEXT,
                company TEXT,
                timezone VARCHAR(50) DEFAULT 'IST',
                theme VARCHAR(20) DEFAULT 'light',
                notifications INT DEFAULT 1,
                email_notifications INT DEFAULT 1,
                sms_notifications INT DEFAULT 0,
                ga_tracking_id TEXT,
                default_report_period VARCHAR(50) DEFAULT 'This Month',
                linkedin_access_token TEXT,
                linkedin_token_expires_at DATETIME,
                linkedin_member_urn TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_notes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                contact_id INT NOT NULL,
                call_datetime TEXT,
                next_conversation TEXT,
                transcript TEXT,
                audio_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_notes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                lead_id INT NOT NULL,
                call_datetime TEXT,
                next_conversation TEXT,
                transcript TEXT,
                audio_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meetings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title TEXT NOT NULL,
                meeting_date DATE NOT NULL,
                meeting_time TEXT,
                lead_id INT,
                contact_id INT,
                location TEXT,
                notes TEXT,
                status VARCHAR(50) DEFAULT 'Scheduled',
                created_by INT,
                assigned_team_member_id INT,
                company_id INT,
                deal_id INT,
                google_calendar_event_id TEXT,
                call_id INT,
                task_id INT,
                quotation_id INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS communication_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                channel TEXT NOT NULL,
                recipient TEXT,
                subject TEXT,
                message TEXT,
                status TEXT NOT NULL,
                error_detail TEXT,
                created_by INT,
                lead_id INT,
                contact_id INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dial_queue (
                id INT AUTO_INCREMENT PRIMARY KEY,
                lead_id INT,
                contact_id INT,
                team_member_id INT NOT NULL,
                status VARCHAR(50) DEFAULT 'Pending',
                assigned_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_members (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                user_id INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Bridges triggering a Priti (Vapi) voice call and Vapi's later end-of-call-report
        # webhook, which only carries the call's own id. Its PK isn't named `id` (the one
        # exception in this schema), which is why every other table's INSERTs can rely on
        # PyMySQL's native cursor.lastrowid without any special-casing.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voice_call_context (
                vapi_call_id VARCHAR(255) PRIMARY KEY,
                lead_id INT,
                contact_id INT,
                team_member_id INT,
                created_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Tags/groups/custom fields: entity_type/entity_id is a polymorphic pointer (rather
        # than separate contact_tags/lead_tags junction tables) so the same tag/group/field can
        # be assigned across entity kinds without duplicating the schema. entity_type is
        # VARCHAR here (not TEXT) because it's part of a composite UNIQUE/index - MySQL can't
        # index a bare TEXT/BLOB column without an explicit prefix length.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                color VARCHAR(20) DEFAULT '#9c6b2e',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_tags (
                id INT AUTO_INCREMENT PRIMARY KEY,
                entity_type VARCHAR(50) NOT NULL,
                entity_id INT NOT NULL,
                tag_id INT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(entity_type, entity_id, tag_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_groups (
                id INT AUTO_INCREMENT PRIMARY KEY,
                entity_type VARCHAR(50) NOT NULL,
                entity_id INT NOT NULL,
                group_id INT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(entity_type, entity_id, group_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_fields (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                field_type VARCHAR(50) DEFAULT 'text',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_field_values (
                id INT AUTO_INCREMENT PRIMARY KEY,
                custom_field_id INT NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id INT NOT NULL,
                value TEXT,
                UNIQUE(custom_field_id, entity_type, entity_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # One row per WhatsApp thread with a phone number - linked to a contact/lead when a
        # matching phone number is found, otherwise left unlinked until one is. opted_out_at/
        # opt_out_reason record a customer replying STOP; checked before every outbound send.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_conversation (
                id INT AUTO_INCREMENT PRIMARY KEY,
                contact_id INT,
                lead_id INT,
                wa_number VARCHAR(32) NOT NULL,
                status VARCHAR(50) DEFAULT 'open',
                opted_out_at DATETIME,
                opt_out_reason TEXT,
                last_message_at DATETIME,
                assigned_user_id INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # wa_message_id is Meta's own message id, used to match an incoming delivery/read
        # status update (from the webhook) back to the row we created when we sent it.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_message (
                id INT AUTO_INCREMENT PRIMARY KEY,
                conversation_id INT NOT NULL,
                direction VARCHAR(20) NOT NULL,
                wa_message_id VARCHAR(255),
                message_type VARCHAR(50) DEFAULT 'text',
                template_name TEXT,
                body TEXT,
                media_url TEXT,
                status VARCHAR(50) DEFAULT 'sent',
                error_message TEXT,
                referral_json TEXT,
                created_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        _create_index_if_missing(cursor, "idx_whatsapp_conversation_wa_number", "whatsapp_conversation", "wa_number")
        _create_index_if_missing(cursor, "idx_whatsapp_message_wa_message_id", "whatsapp_message", "wa_message_id")
        _create_index_if_missing(cursor, "idx_whatsapp_message_conversation", "whatsapp_message", "conversation_id")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quick_replies (
                id INT AUTO_INCREMENT PRIMARY KEY,
                shortcut VARCHAR(255) UNIQUE NOT NULL,
                message TEXT NOT NULL,
                created_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flows (
                id INT AUTO_INCREMENT PRIMARY KEY,
                meta_flow_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status VARCHAR(50) DEFAULT 'draft',
                terminal_screen VARCHAR(255) DEFAULT 'SUCCESS',
                created_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_flow_session (
                id INT AUTO_INCREMENT PRIMARY KEY,
                flow_token VARCHAR(255) UNIQUE NOT NULL,
                flow_id INT NOT NULL,
                conversation_id INT,
                current_screen TEXT,
                status VARCHAR(50) DEFAULT 'in_progress',
                submission_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        _create_index_if_missing(cursor, "idx_whatsapp_flow_session_token", "whatsapp_flow_session", "flow_token")

        # One row per CRM user who has connected a Google account (Sheets export/import).
        # refresh_token lives here, never sent to the frontend.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS google_oauth_tokens (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL UNIQUE,
                google_email TEXT,
                access_token TEXT,
                refresh_token TEXT NOT NULL,
                token_expires_at DATETIME,
                scope TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # A Zapier "Catch Hook" URL the CRM POSTs a JSON payload to whenever a matching event
        # happens - no OAuth, no API key, just a URL the user pastes in from their own Zap.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zapier_webhooks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                url TEXT NOT NULL,
                event_type VARCHAR(50) NOT NULL DEFAULT 'all',
                created_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_triggered_at DATETIME,
                last_status TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS slack_webhooks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                url TEXT NOT NULL,
                event_type VARCHAR(50) NOT NULL DEFAULT 'all',
                created_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_triggered_at DATETIME,
                last_status TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Developer API keys - let an external system (a website contact form, a
        # click-to-WhatsApp ad landing page, a Zapier/webhook integration) call
        # POST /api/public/leads without a user login. Only key_hash (SHA-256 of the raw key)
        # is ever stored, never the raw value - see main.py's get_user_from_api_key().
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                key_prefix VARCHAR(20) NOT NULL,
                key_hash VARCHAR(64) NOT NULL,
                created_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used_at DATETIME,
                revoked_at DATETIME
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        _create_index_if_missing(cursor, "idx_api_keys_key_hash", "api_keys", "key_hash")

        # "Forgot password" email flow - see database_sqlite.py's matching table for the full
        # rationale (only token_hash is ever persisted, never the raw token).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                token_hash VARCHAR(64) NOT NULL,
                expires_at DATETIME NOT NULL,
                used_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        _create_index_if_missing(cursor, "idx_password_reset_tokens_token_hash", "password_reset_tokens", "token_hash")

        # Commission/revenue ledger - see database_sqlite.py's matching table for the full
        # rationale (a repeatable log, not a single current-state value, so it can't live in
        # custom_field_values).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commission_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_type VARCHAR(20) NOT NULL,
                description VARCHAR(255) NOT NULL,
                amount DECIMAL(12,2) NOT NULL,
                received_date DATE NOT NULL,
                contact_id INT,
                lead_id INT,
                deal_id INT,
                notes TEXT,
                created_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        _create_index_if_missing(cursor, "idx_commission_records_product_type", "commission_records", "product_type")
        _create_index_if_missing(cursor, "idx_commission_records_received_date", "commission_records", "received_date")

        # Mutual fund holdings - see database_sqlite.py's matching table for the full
        # rationale (one row per fund, replacing the earlier custom-fields stopgap that could
        # only hold a single value per field per contact).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mf_holdings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                contact_id INT NOT NULL,
                folio_number VARCHAR(100),
                fund_name VARCHAR(255) NOT NULL,
                fund_category VARCHAR(50),
                investment_type VARCHAR(20) NOT NULL DEFAULT 'SIP',
                amount DECIMAL(12,2),
                frequency VARCHAR(20) DEFAULT 'Monthly',
                next_due_date DATE,
                status VARCHAR(20) NOT NULL DEFAULT 'Active',
                start_date DATE,
                goal VARCHAR(255),
                notes TEXT,
                created_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        _create_index_if_missing(cursor, "idx_mf_holdings_contact_id", "mf_holdings", "contact_id")
        _create_index_if_missing(cursor, "idx_mf_holdings_next_due_date", "mf_holdings", "next_due_date")
        _create_index_if_missing(cursor, "idx_mf_holdings_status", "mf_holdings", "status")

        # Insurance policies - see database_sqlite.py's matching table for the full rationale
        # (one row per policy; contacts.renewal_date/amount are left untouched for the
        # Dashboard's existing Upcoming Renewals widget, this is the fuller multi-policy view).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insurance_policies (
                id INT AUTO_INCREMENT PRIMARY KEY,
                contact_id INT NOT NULL,
                policy_number VARCHAR(100),
                insurer VARCHAR(100),
                policy_type VARCHAR(20) NOT NULL DEFAULT 'Health',
                sum_assured DECIMAL(14,2),
                premium_amount DECIMAL(12,2),
                premium_frequency VARCHAR(20) DEFAULT 'Annual',
                start_date DATE,
                renewal_date DATE,
                status VARCHAR(20) NOT NULL DEFAULT 'Active',
                notes TEXT,
                created_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        _create_index_if_missing(cursor, "idx_insurance_policies_contact_id", "insurance_policies", "contact_id")
        _create_index_if_missing(cursor, "idx_insurance_policies_renewal_date", "insurance_policies", "renewal_date")
        _create_index_if_missing(cursor, "idx_insurance_policies_status", "insurance_policies", "status")

        # Client documents - see database_sqlite.py's matching table for the full rationale
        # (replaces the old "DigiLocker" modal, which was UI-only and never stored anything).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                contact_id INT NOT NULL,
                document_type VARCHAR(50) NOT NULL DEFAULT 'Other',
                file_name VARCHAR(255) NOT NULL,
                file_url VARCHAR(500) NOT NULL,
                uploaded_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        _create_index_if_missing(cursor, "idx_contact_documents_contact_id", "contact_documents", "contact_id")

        # Automations: a simple linear drip sequence. automations is the flow itself,
        # automation_steps are its ordered messages (each fires wait_minutes after the
        # previous one), and automation_enrollments tracks each lead/contact's live progress
        # through it - entity_type/entity_id is the same polymorphic pointer entity_tags/
        # entity_groups already use, rather than a WhatsApp-conversation-specific column, so
        # an automation can enroll either a lead or a contact directly. Sending the actual
        # steps on a schedule is a separate piece of work (see main.py's AUTOMATIONS section);
        # this is the CRUD + enrollment bookkeeping layer only.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                trigger_type VARCHAR(50) NOT NULL DEFAULT 'manual',
                group_id INT,
                status VARCHAR(20) DEFAULT 'active',
                created_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automation_steps (
                id INT AUTO_INCREMENT PRIMARY KEY,
                automation_id INT NOT NULL,
                step_order INT NOT NULL,
                wait_minutes INT DEFAULT 0,
                message_type VARCHAR(20) DEFAULT 'text',
                template_name VARCHAR(255),
                body TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automation_enrollments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                automation_id INT NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id INT NOT NULL,
                current_step INT DEFAULT 0,
                status VARCHAR(20) DEFAULT 'active',
                next_run_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(automation_id, entity_type, entity_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        _create_index_if_missing(cursor, "idx_automation_enrollments_automation", "automation_enrollments", "automation_id")
        _create_index_if_missing(cursor, "idx_automation_enrollments_next_run", "automation_enrollments", "next_run_at, status")

        conn.commit()

        _ensure_integrations_catalog(cursor, conn)
        _ensure_team_roster(cursor, conn)

        cursor.execute("SELECT COUNT(*) as count FROM users")
        if cursor.fetchone()['count'] > 0:
            cursor.close()
            print("[OK] Database schema ready (existing data preserved)")
            return

        if os.getenv("SEED_DEMO_DATA", "true").lower() == "false":
            cursor.close()
            print("[OK] Database schema ready (demo seeding disabled via SEED_DEMO_DATA=false)")
            return

        from auth import hash_password
        hashed_password = hash_password("12345")
        cursor.execute("""
            INSERT INTO users (username, email, password, role, full_name, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('testuser', 'test@example.com', hashed_password, 'admin', 'Test User', 1))

        cursor.execute("""
            INSERT INTO leads (name, company, email, phone, status, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('Neha Singh', 'StartUp Fund', 'neha@startup.com', '9876543210', 'New', 1))
        cursor.execute("""
            INSERT INTO leads (name, company, email, phone, status, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('Vikram Reddy', 'Tech Park', 'vikram@techpark.com', '9876543211', 'New', 1))
        cursor.execute("""
            INSERT INTO leads (name, company, email, phone, status, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('Anjali Desai', 'Retail Chain', 'anjali@retail.com', '9876543212', 'New', 1))
        cursor.execute("""
            INSERT INTO leads (name, company, email, phone, status, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('Amit Patel', 'Manufacturing', 'amit@mfg.com', '9876543213', 'New', 1))
        cursor.execute("""
            INSERT INTO leads (name, company, email, phone, status, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('Priya Kapoor', 'Digital Ventures', 'priya@digital.com', '9876543214', 'New', 1))

        cursor.execute("""
            INSERT INTO deals (lead_id, deal_value, stage, probability, owner_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (1, 50000, 'new', 0.3, 1))
        cursor.execute("""
            INSERT INTO deals (lead_id, deal_value, stage, probability, owner_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (2, 75000, 'qualified', 0.5, 1))
        cursor.execute("""
            INSERT INTO deals (lead_id, deal_value, stage, probability, owner_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (3, 100000, 'proposal', 0.7, 1))
        cursor.execute("""
            INSERT INTO deals (lead_id, deal_value, stage, probability, owner_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (4, 120000, 'negotiation', 0.8, 1))

        cursor.execute("""
            INSERT INTO campaigns (name, type, status, recipients, opens, clicks, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('Insurance Awareness', 'Email', 'Active', 3000, 1200, 450, 1))
        cursor.execute("""
            INSERT INTO campaigns (name, type, status, recipients, opens, clicks, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('Health Insurance Promotion', 'WhatsApp', 'Completed', 2500, 2000, 800, 1))
        cursor.execute("""
            INSERT INTO campaigns (name, type, status, recipients, opens, clicks, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('Q3 Product Launch', 'Email', 'Completed', 1200, 600, 180, 1))

        cursor.execute("""
            INSERT INTO user_settings (user_id, full_name, email, phone, company, timezone, theme, notifications, email_notifications, sms_notifications)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (1, 'Test User', 'test@example.com', '+91-9876543210', '', 'IST', 'light', 1, 1, 0))

        cursor.execute("""
            INSERT INTO contacts (name, company, email, phone, city, score, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('Neha Singh', 'Tech Startup', 'neha@techstartup.com', '+91-9876543210', 'Mumbai, Andheri West', 85, 1))
        cursor.execute("""
            INSERT INTO contacts (name, company, email, phone, city, score, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('Vikram Reddy', 'Tech Park', 'vikram@techpark.com', '+91-9876543211', 'Bangalore, Whitefield', 72, 1))
        cursor.execute("""
            INSERT INTO contacts (name, company, email, phone, city, score, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('Anjali Desai', 'Retail Chain', 'anjali@retail.com', '+91-9876543212', 'Pune, Kothrud', 65, 1))
        cursor.execute("""
            INSERT INTO contacts (name, company, email, phone, city, score, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('Amit Patel', 'Manufacturing', 'amit@mfg.com', '+91-9876543213', 'Ahmedabad, Naroda', 58, 1))
        cursor.execute("""
            INSERT INTO contacts (name, company, email, phone, city, score, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('Priya Kapoor', 'Digital Ventures', 'priya@digital.com', '+91-9876543214', 'Delhi, Connaught Place', 80, 1))

        cursor.execute("""
            INSERT INTO contact_notes (contact_id, next_conversation, transcript)
            VALUES (%s, %s, %s)
        """, (1, '2026-08-25T10:30', 'Discussed LAP requirements, sending document checklist.'))

        cursor.execute("""
            INSERT INTO calls (name, phone, duration_seconds, type, outcome, call_date, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('Neha Singh', '+91-9876543210', 320, 'Outbound', 'Interested', '2026-08-21', 1))
        cursor.execute("""
            INSERT INTO calls (name, phone, duration_seconds, type, outcome, call_date, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('Vikram Reddy', '+91-9876543211', 225, 'Inbound', 'Not Interested', '2026-08-21', 1))
        cursor.execute("""
            INSERT INTO calls (name, phone, duration_seconds, type, outcome, call_date, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('Anjali Desai', '+91-9876543212', 490, 'Outbound', 'Meeting Scheduled', '2026-08-20', 1))
        cursor.execute("""
            INSERT INTO calls (name, phone, duration_seconds, type, outcome, call_date, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('Amit Patel', '+91-9876543213', 410, 'Outbound', 'Follow-up Needed', '2026-08-20', 1))

        conn.commit()
        cursor.close()
        print("[OK] MySQL database initialized successfully!")
        print("[OK] Test user created: testuser / password")
        print("[OK] Sample leads, deals, campaigns, integrations, settings, contacts and calls added!")
