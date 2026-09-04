import sqlite3
from contextlib import contextmanager
import os

# Overridable so tests can point at an isolated temp file instead of the real dev database.
DB_PATH = os.getenv("DB_PATH", "arthainvest_crm.db")

@contextmanager
def get_db():
    """Get SQLite database connection.

    WAL journal mode + a busy_timeout are required once more than one connection can be open
    at once (e.g. a background scheduler alongside request handling). SQLite's default
    rollback-journal mode locks the *entire file* for the duration of a write, so two
    connections writing around the same time reliably hit "database is locked" - WAL lets
    readers and a single writer proceed concurrently instead, and the busy_timeout makes a
    genuine write/write collision wait and retry rather than failing immediately.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    try:
        yield conn
    finally:
        conn.close()

def execute_query(query, params=None, fetch=False):
    """Execute a database query"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        if fetch:
            result = [dict(row) for row in cursor.fetchall()]
        else:
            conn.commit()
            result = cursor.rowcount
        cursor.close()
        return result

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
        # Future/roadmap - no backend integration built yet, listed here as a marketplace
        # placeholder so they're on the radar to build later. Payment gateways (Razorpay,
        # Stripe, PayU) deliberately excluded - Razorpay was removed from this CRM per an
        # earlier explicit request, so no payment gateway has been re-added without asking.
        ('Facebook Lead Ads', '📘', 'Auto-import leads from Facebook lead-gen campaigns (planned)', 0, 'never'),
        ('IndiaMart', '🅼', 'Auto-fetch leads from your IndiaMart seller account (planned)', 0, 'never'),
        ('TradeIndia', '🅃', 'Auto-fetch leads from your TradeIndia seller account (planned)', 0, 'never'),
        ('Zendesk', '🎫', 'Sync support tickets for client queries (planned)', 0, 'never'),
        ('QuickBooks', '📗', 'Sync commission/invoice records for bookkeeping (planned)', 0, 'never'),
        ('Aircall', '☎️', 'Alternate cloud telephony provider to Twilio (planned)', 0, 'never'),
        ('MSG91', '✉️', 'Combined SMS/WhatsApp/Email sending, alternate to Twilio/SMTP (planned)', 0, 'never'),
        ('Apollo.io', '🎯', 'Lead enrichment and prospecting data (planned)', 0, 'never'),
    ]
    existing = {row['name'] for row in cursor.execute("SELECT name FROM integrations").fetchall()}
    for name, logo, description, connected, last_sync in catalog:
        if name not in existing:
            cursor.execute(
                "INSERT INTO integrations (name, logo, description, connected, last_sync) VALUES (?, ?, ?, ?, ?)",
                (name, logo, description, connected, last_sync)
            )

    # Razorpay was added and then removed from the catalog above - drop any row a previous
    # startup already inserted, so it doesn't linger on databases that saw it before.
    cursor.execute("DELETE FROM integrations WHERE name = 'Razorpay Payments'")

    conn.commit()

def _ensure_team_roster(cursor, conn):
    """Insert any roster member that doesn't exist yet, by name. Same pattern as
    _ensure_integrations_catalog - runs on every startup so it appears without duplicating
    on restart. user_id links a roster entry to a real login for activity tracking in Team
    Productivity reports; entries without one (no login account exists for them yet) show
    real "no data" rather than a fabricated number."""
    roster = [
        ('Artha', 'admin', 'artha@arthainvest.com', '+91-9876500001', 1),
        ('Team Admin', 'admin', 'admin2@arthainvest.com', '+91-9876500002', None),
        ('Rajesh Kumar', 'team_lead', 'rajesh.kumar@arthainvest.com', '+91-9876500003', None),
        ('Suresh Iyer', 'location_head', 'suresh.iyer@arthainvest.com', '+91-9876500004', None),
        ('Arjun Sharma', 'employee', 'arjun.sharma@arthainvest.com', '+91-9876500005', None),
        ('Priya Singh', 'employee', 'priya.singh@arthainvest.com', '+91-9876500006', None),
        ('Vikram Patel', 'employee', 'vikram.patel@arthainvest.com', '+91-9876500007', None),
    ]
    existing = {row['name'] for row in cursor.execute("SELECT name FROM team_members").fetchall()}
    for name, role, email, phone, user_id in roster:
        if name not in existing:
            cursor.execute(
                "INSERT INTO team_members (name, role, email, phone, user_id) VALUES (?, ?, ?, ?, ?)",
                (name, role, email, phone, user_id)
            )
    conn.commit()

def init_db():
    """Create the schema if it doesn't exist yet, then seed demo data only on a genuinely
    empty database (first run). Never drops or touches existing tables/rows - this runs on
    every server startup, so anything destructive here would wipe real production data on
    the next restart or redeploy."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'employee',
                full_name TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company TEXT,
                email TEXT,
                phone TEXT,
                product TEXT,
                ai_score INTEGER,
                lead_tier TEXT,
                status TEXT DEFAULT 'new',
                source TEXT,
                created_by INTEGER,
                assigned_team_member_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (assigned_team_member_id) REFERENCES team_members(id)
            )
        """)

        # Same "ALTER TABLE for pre-existing databases" situation as deals.assigned_team_member_id below.
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN assigned_team_member_id INTEGER")
        except sqlite3.OperationalError:
            pass

        # Set by POST /api/leads/{id}/convert once this lead has been turned into a real
        # Contact - marks it as historical rather than an active prospect still being worked,
        # without ever deleting the lead or its notes/activity history.
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN converted_contact_id INTEGER REFERENCES contacts(id)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN call_id INTEGER REFERENCES calls(id)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN task_id INTEGER REFERENCES tasks(id)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN deal_id INTEGER REFERENCES deals(id)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN company_id INTEGER REFERENCES companies(id)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN quotation_id INTEGER REFERENCES quotations(id)")
        except sqlite3.OperationalError:
            pass

        # A related Contact this lead is linked to (e.g. a referral) - distinct from
        # converted_contact_id above, which is only ever set by the one-time conversion flow.
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN contact_id INTEGER REFERENCES contacts(id)")
        except sqlite3.OperationalError:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                deal_value REAL,
                stage TEXT DEFAULT 'new',
                probability REAL,
                loan_product TEXT DEFAULT 'LAP',
                expected_close_date DATE,
                owner_id INTEGER,
                notes TEXT,
                assigned_team_member_id INTEGER,
                process_status TEXT DEFAULT 'Login',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id),
                FOREIGN KEY (owner_id) REFERENCES users(id),
                FOREIGN KEY (assigned_team_member_id) REFERENCES team_members(id)
            )
        """)

        # CREATE TABLE IF NOT EXISTS only applies to brand-new databases - a database that
        # already has a `deals` table from before this column existed needs it added
        # explicitly. SQLite raises "duplicate column name" if it's already there, which is
        # the expected/safe outcome on every startup after the first.
        try:
            cursor.execute("ALTER TABLE deals ADD COLUMN loan_product TEXT DEFAULT 'LAP'")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE deals ADD COLUMN assigned_team_member_id INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            # Loan-specific sub-status (Login/Sanction/Hold/Disbursed) shown in the Pipeline
            # "Sales Pipeline" table - distinct from the generic deals.stage (new/qualified/
            # proposal/negotiation/closed). Was frontend-only state before (reset to 'Login' on
            # every reload) - this makes it real and persisted.
            cursor.execute("ALTER TABLE deals ADD COLUMN process_status TEXT DEFAULT 'Login'")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE deals ADD COLUMN company_id INTEGER REFERENCES companies(id)")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE deals ADD COLUMN contact_id INTEGER REFERENCES contacts(id)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE deals ADD COLUMN call_id INTEGER REFERENCES calls(id)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE deals ADD COLUMN task_id INTEGER REFERENCES tasks(id)")
        except sqlite3.OperationalError:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                entity_type TEXT,
                entity_id INTEGER,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT DEFAULT 'Email',
                status TEXT DEFAULT 'Active',
                recipients INTEGER DEFAULT 0,
                opens INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                message TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        # campaigns existed in databases from earlier this session, before message existed.
        try:
            cursor.execute("ALTER TABLE campaigns ADD COLUMN message TEXT")
        except sqlite3.OperationalError:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                lead_id INTEGER,
                contact_id INTEGER,
                status TEXT DEFAULT 'Pending',
                sent_at TIMESTAMP,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
                FOREIGN KEY (lead_id) REFERENCES leads(id),
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS integrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                logo TEXT,
                description TEXT,
                connected INTEGER DEFAULT 0,
                last_sync TEXT DEFAULT 'never'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                email TEXT,
                phone TEXT,
                company TEXT,
                timezone TEXT DEFAULT 'IST',
                theme TEXT DEFAULT 'light',
                notifications INTEGER DEFAULT 1,
                email_notifications INTEGER DEFAULT 1,
                sms_notifications INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company TEXT,
                email TEXT,
                phone TEXT,
                city TEXT,
                score INTEGER,
                amount REAL,
                bank TEXT,
                status TEXT DEFAULT 'Active',
                renewal_date DATE,
                created_by INTEGER,
                assigned_team_member_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (assigned_team_member_id) REFERENCES team_members(id)
            )
        """)

        # Same "ALTER TABLE for pre-existing databases" situation as deals.assigned_team_member_id.
        for ddl in [
            "ALTER TABLE contacts ADD COLUMN amount REAL",
            "ALTER TABLE contacts ADD COLUMN bank TEXT",
            "ALTER TABLE contacts ADD COLUMN status TEXT DEFAULT 'Active'",
            "ALTER TABLE contacts ADD COLUMN assigned_team_member_id INTEGER",
            "ALTER TABLE contacts ADD COLUMN renewal_date DATE",
            "ALTER TABLE contacts ADD COLUMN company_id INTEGER REFERENCES companies(id)",
            # Set when this contact was created via "Convert to Contact" on a lead - lets the
            # Contact page show where they came from, the reverse of leads.converted_contact_id.
            "ALTER TABLE contacts ADD COLUMN converted_from_lead_id INTEGER REFERENCES leads(id)",
            "ALTER TABLE contacts ADD COLUMN quotation_id INTEGER REFERENCES quotations(id)",
            "ALTER TABLE contacts ADD COLUMN call_id INTEGER REFERENCES calls(id)",
        ]:
            try:
                cursor.execute(ddl)
            except sqlite3.OperationalError:
                pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                call_datetime TEXT,
                next_conversation TEXT,
                transcript TEXT,
                audio_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                call_datetime TEXT,
                next_conversation TEXT,
                transcript TEXT,
                audio_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                due_date DATE NOT NULL,
                completed INTEGER DEFAULT 0,
                priority TEXT DEFAULT 'Normal',
                created_by INTEGER,
                assigned_team_member_id INTEGER,
                lead_id INTEGER,
                contact_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (assigned_team_member_id) REFERENCES team_members(id),
                FOREIGN KEY (lead_id) REFERENCES leads(id),
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            )
        """)

        # tasks already existed in databases from earlier this session, before priority/
        # lead_id/contact_id existed.
        for ddl in [
            "ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'Normal'",
            "ALTER TABLE tasks ADD COLUMN lead_id INTEGER REFERENCES leads(id)",
            "ALTER TABLE tasks ADD COLUMN contact_id INTEGER REFERENCES contacts(id)",
            "ALTER TABLE tasks ADD COLUMN call_id INTEGER REFERENCES calls(id)",
            "ALTER TABLE tasks ADD COLUMN quotation_id INTEGER REFERENCES quotations(id)",
            "ALTER TABLE tasks ADD COLUMN company_id INTEGER REFERENCES companies(id)",
        ]:
            try:
                cursor.execute(ddl)
            except sqlite3.OperationalError:
                pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                meeting_date DATE NOT NULL,
                meeting_time TEXT,
                lead_id INTEGER,
                contact_id INTEGER,
                location TEXT,
                notes TEXT,
                status TEXT DEFAULT 'Scheduled',
                created_by INTEGER,
                assigned_team_member_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id),
                FOREIGN KEY (contact_id) REFERENCES contacts(id),
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (assigned_team_member_id) REFERENCES team_members(id)
            )
        """)

        try:
            cursor.execute("ALTER TABLE meetings ADD COLUMN company_id INTEGER REFERENCES companies(id)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE meetings ADD COLUMN deal_id INTEGER REFERENCES deals(id)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE meetings ADD COLUMN google_calendar_event_id TEXT")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE meetings ADD COLUMN call_id INTEGER REFERENCES calls(id)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE meetings ADD COLUMN task_id INTEGER REFERENCES tasks(id)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE meetings ADD COLUMN quotation_id INTEGER REFERENCES quotations(id)")
        except sqlite3.OperationalError:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS communication_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT NOT NULL,
                recipient TEXT,
                subject TEXT,
                message TEXT,
                status TEXT NOT NULL,
                error_detail TEXT,
                created_by INTEGER,
                lead_id INTEGER,
                contact_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (lead_id) REFERENCES leads(id),
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            )
        """)

        # communication_log existed in databases from earlier this session, before lead_id/
        # contact_id existed - older logged sends stay unlinked (real "not linked" rather than
        # a guessed match), new ones get linked at send time from the Lead/Contact action buttons.
        for ddl in [
            "ALTER TABLE communication_log ADD COLUMN lead_id INTEGER REFERENCES leads(id)",
            "ALTER TABLE communication_log ADD COLUMN contact_id INTEGER REFERENCES contacts(id)",
        ]:
            try:
                cursor.execute(ddl)
            except sqlite3.OperationalError:
                pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                duration_seconds INTEGER DEFAULT 0,
                type TEXT DEFAULT 'Outbound',
                outcome TEXT,
                call_date DATE,
                created_by INTEGER,
                team_member_id INTEGER,
                lead_id INTEGER,
                contact_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (team_member_id) REFERENCES team_members(id),
                FOREIGN KEY (lead_id) REFERENCES leads(id),
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            )
        """)

        for ddl in [
            "ALTER TABLE calls ADD COLUMN lead_id INTEGER REFERENCES leads(id)",
            "ALTER TABLE calls ADD COLUMN contact_id INTEGER REFERENCES contacts(id)",
            "ALTER TABLE calls ADD COLUMN company_id INTEGER REFERENCES companies(id)",
            # Set by the Exotel dial/status-callback path (see main.py's dial_call and the
            # /api/webhooks/exotel/status handler) - Twilio-dialed calls leave both NULL.
            "ALTER TABLE calls ADD COLUMN recording_url TEXT",
            "ALTER TABLE calls ADD COLUMN provider_call_sid TEXT",
        ]:
            try:
                cursor.execute(ddl)
            except sqlite3.OperationalError:
                pass

        # Same "ALTER TABLE for pre-existing databases" situation as deals.assigned_team_member_id.
        try:
            cursor.execute("ALTER TABLE calls ADD COLUMN team_member_id INTEGER")
        except sqlite3.OperationalError:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dial_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                contact_id INTEGER,
                team_member_id INTEGER NOT NULL,
                status TEXT DEFAULT 'Pending',
                assigned_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id),
                FOREIGN KEY (contact_id) REFERENCES contacts(id),
                FOREIGN KEY (team_member_id) REFERENCES team_members(id),
                FOREIGN KEY (assigned_by) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                industry TEXT,
                city TEXT,
                phone TEXT,
                email TEXT,
                website TEXT,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quotation_number TEXT,
                lead_id INTEGER,
                contact_id INTEGER,
                deal_id INTEGER,
                title TEXT NOT NULL,
                status TEXT DEFAULT 'Draft',
                valid_until DATE,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id),
                FOREIGN KEY (contact_id) REFERENCES contacts(id),
                FOREIGN KEY (deal_id) REFERENCES deals(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        # quotations existed in databases from earlier this session, before deal_id existed.
        try:
            cursor.execute("ALTER TABLE quotations ADD COLUMN deal_id INTEGER REFERENCES deals(id)")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE quotations ADD COLUMN contact_id INTEGER REFERENCES contacts(id)")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE quotations ADD COLUMN company_id INTEGER REFERENCES companies(id)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE quotations ADD COLUMN call_id INTEGER REFERENCES calls(id)")
        except sqlite3.OperationalError:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotation_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quotation_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount REAL DEFAULT 0,
                FOREIGN KEY (quotation_id) REFERENCES quotations(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Bridges the gap between triggering a Priti (Vapi) voice call and Vapi's later
        # end-of-call-report webhook, which only carries the call's own id - not which
        # lead/contact/team member it was for. Without this, the webhook's `calls` insert has
        # no way to resolve those and the logged call is permanently unlinked.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voice_call_context (
                vapi_call_id TEXT PRIMARY KEY,
                lead_id INTEGER,
                contact_id INTEGER,
                team_member_id INTEGER,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id),
                FOREIGN KEY (contact_id) REFERENCES contacts(id),
                FOREIGN KEY (team_member_id) REFERENCES team_members(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        # Same retrofit pattern as deals.loan_product - only matters for a database that
        # already existed before these columns were added.
        try:
            cursor.execute("ALTER TABLE user_settings ADD COLUMN ga_tracking_id TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE user_settings ADD COLUMN default_report_period TEXT DEFAULT 'This Month'")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE user_settings ADD COLUMN linkedin_access_token TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE user_settings ADD COLUMN linkedin_token_expires_at TIMESTAMP")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE user_settings ADD COLUMN linkedin_member_urn TEXT")
        except sqlite3.OperationalError:
            pass

        # Tags: free-form colored labels a contact/lead can carry. entity_type/entity_id is a
        # polymorphic pointer (rather than separate contact_tags/lead_tags junction tables) so
        # the same tag can be assigned across entity kinds without duplicating the schema.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#9c6b2e',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tag_id) REFERENCES tags(id),
                UNIQUE(entity_type, entity_id, tag_id)
            )
        """)

        # Groups are audience segments (e.g. "Diwali campaign", "SIP clients") that a broadcast
        # or automation can target - separate from tags, which are free-form labels.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups(id),
                UNIQUE(entity_type, entity_id, group_id)
            )
        """)

        # Custom field definitions (e.g. "SIP Amount", "Policy Number") plus the actual values
        # stored per contact/lead - same entity_type/entity_id pattern as tags/groups above.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                field_type TEXT DEFAULT 'text',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_field_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                custom_field_id INTEGER NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                value TEXT,
                FOREIGN KEY (custom_field_id) REFERENCES custom_fields(id),
                UNIQUE(custom_field_id, entity_type, entity_id)
            )
        """)

        # One row per WhatsApp thread with a phone number - linked to a contact/lead when a
        # matching phone number is found, otherwise left unlinked until one is (e.g. a first
        # inbound message from a brand-new number auto-creates a lead - see webhook handling
        # in main.py). opted_out_at/opt_out_reason record a customer replying STOP; checked
        # before every outbound send so we never message someone who opted out.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_conversation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                lead_id INTEGER,
                wa_number TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                opted_out_at TIMESTAMP,
                opt_out_reason TEXT,
                last_message_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts(id),
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
        """)

        # wa_message_id is Meta's own message id, used to match an incoming delivery/read
        # status update (from the webhook) back to the row we created when we sent it.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_message (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                direction TEXT NOT NULL,
                wa_message_id TEXT,
                message_type TEXT DEFAULT 'text',
                template_name TEXT,
                body TEXT,
                media_url TEXT,
                status TEXT DEFAULT 'sent',
                error_message TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES whatsapp_conversation(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_whatsapp_conversation_wa_number ON whatsapp_conversation(wa_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_whatsapp_message_wa_message_id ON whatsapp_message(wa_message_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_whatsapp_message_conversation ON whatsapp_message(conversation_id)")

        try:
            # Which team member (agent) currently owns this conversation - the Inbox's "mine
            # only" filter scopes to this for non-admin roles.
            cursor.execute("ALTER TABLE whatsapp_conversation ADD COLUMN assigned_user_id INTEGER REFERENCES users(id)")
        except sqlite3.OperationalError:
            pass
        try:
            # Meta attaches a `referral` block to the first inbound message of a click-to-WhatsApp
            # ad conversation (source URL, headline, ad/media id) - stored as raw JSON so we know
            # which ad brought this lead in, without needing a separate ads-tracking table.
            cursor.execute("ALTER TABLE whatsapp_message ADD COLUMN referral_json TEXT")
        except sqlite3.OperationalError:
            pass

        # Canned responses an agent can fire off in one click - wired to the WhatsApp
        # conversation composer.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quick_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shortcut TEXT UNIQUE NOT NULL,
                message TEXT NOT NULL,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        # WhatsApp Flows (Meta's native in-chat forms) - a Flow is built and published in Meta
        # Business Manager first; this just records the resulting meta_flow_id so we can trigger
        # sending it. terminal_screen names the screen whose data_exchange response should be
        # treated as the finished submission - defaults to Meta's own "SUCCESS" convention, but
        # is editable per-Flow once the real screen names are known (we don't control the Flow's
        # actual screen graph, that's authored in Meta's Flow Builder).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meta_flow_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT DEFAULT 'draft',
                terminal_screen TEXT DEFAULT 'SUCCESS',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        # One row per flow_token we hand out when triggering a Flow send - the data endpoint
        # (Meta calls it directly, with no way to carry our own auth) looks a session up by
        # flow_token to resolve back to the conversation/contact/lead it belongs to, and
        # accumulates the in-progress answers until the terminal screen completes it.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_flow_session (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flow_token TEXT UNIQUE NOT NULL,
                flow_id INTEGER NOT NULL,
                conversation_id INTEGER,
                current_screen TEXT,
                status TEXT DEFAULT 'in_progress',
                submission_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (flow_id) REFERENCES flows(id),
                FOREIGN KEY (conversation_id) REFERENCES whatsapp_conversation(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_whatsapp_flow_session_token ON whatsapp_flow_session(flow_token)")

        # One row per CRM user who has connected a Google account (Sheets export/import).
        # refresh_token lives here, never sent to the frontend - access_token is short-lived
        # and refreshed on demand using it, same separation LinkedIn's OAuth doesn't need
        # (LinkedIn's own tokens are long-lived, Google's access tokens expire in ~1 hour).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS google_oauth_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                google_email TEXT,
                access_token TEXT,
                refresh_token TEXT NOT NULL,
                token_expires_at TIMESTAMP,
                scope TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # A Zapier "Catch Hook" URL the CRM POSTs a JSON payload to whenever a matching event
        # happens - no OAuth, no API key, just a URL the user pastes in from their own Zap.
        # event_type is 'lead.created', 'deal.closed', or 'all' (fires for every event type).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zapier_webhooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                event_type TEXT NOT NULL DEFAULT 'all',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_triggered_at TIMESTAMP,
                last_status TEXT,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS slack_webhooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                event_type TEXT NOT NULL DEFAULT 'all',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_triggered_at TIMESTAMP,
                last_status TEXT,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        # Developer API keys - let an external system (a website contact form, a
        # click-to-WhatsApp ad landing page, a Zapier/webhook integration) call
        # POST /api/public/leads without a user login. Only key_hash (SHA-256 of the raw key)
        # is ever stored, never the raw value - see main.py's get_user_from_api_key().
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                key_prefix TEXT NOT NULL,
                key_hash TEXT NOT NULL,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP,
                revoked_at TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash)")

        # "Forgot password" email flow - a one-time token, emailed as a reset link, that lets
        # someone who is locked out (not just changing a known password) set a new one without
        # an admin's help. Only token_hash (SHA-256 of the raw token) is ever stored, same
        # reasoning as api_keys.key_hash above - the raw token only exists in the emailed link.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token_hash ON password_reset_tokens(token_hash)")

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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                trigger_type TEXT NOT NULL DEFAULT 'manual',
                group_id INTEGER,
                status TEXT DEFAULT 'active',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automation_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                automation_id INTEGER NOT NULL,
                step_order INTEGER NOT NULL,
                wait_minutes INTEGER DEFAULT 0,
                message_type TEXT DEFAULT 'text',
                template_name TEXT,
                body TEXT,
                FOREIGN KEY (automation_id) REFERENCES automations(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automation_enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                automation_id INTEGER NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                current_step INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                next_run_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (automation_id) REFERENCES automations(id),
                UNIQUE(automation_id, entity_type, entity_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_automation_enrollments_automation ON automation_enrollments(automation_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_automation_enrollments_next_run ON automation_enrollments(next_run_at, status)")

        conn.commit()

        # Runs on every startup regardless of seed state (unlike the demo-data block below),
        # so a catalog entry added after a database was already seeded still shows up.
        _ensure_integrations_catalog(cursor, conn)
        _ensure_team_roster(cursor, conn)

        # Schema is in place. Only seed demo data into a genuinely empty database (first run
        # ever) - never on a restart of a database that already has real users/data in it.
        cursor.execute("SELECT COUNT(*) as count FROM users")
        if cursor.fetchone()['count'] > 0:
            cursor.close()
            print("[OK] Database schema ready (existing data preserved)")
            return

        if os.getenv("SEED_DEMO_DATA", "true").lower() == "false":
            cursor.close()
            print("[OK] Database schema ready (demo seeding disabled via SEED_DEMO_DATA=false)")
            return

        # Insert test user (testuser/12345 - must match Login.jsx displayed hint)
        from auth import hash_password
        hashed_password = hash_password("12345")
        cursor.execute("""
            INSERT INTO users (username, email, password, role, full_name, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('testuser', 'test@example.com', hashed_password, 'admin', 'Test User', 1))

        # Insert sample data
        cursor.execute("""
            INSERT INTO leads (name, company, email, phone, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('Neha Singh', 'StartUp Fund', 'neha@startup.com', '9876543210', 'New', 1))
        cursor.execute("""
            INSERT INTO leads (name, company, email, phone, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('Vikram Reddy', 'Tech Park', 'vikram@techpark.com', '9876543211', 'New', 1))
        cursor.execute("""
            INSERT INTO leads (name, company, email, phone, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('Anjali Desai', 'Retail Chain', 'anjali@retail.com', '9876543212', 'New', 1))
        cursor.execute("""
            INSERT INTO leads (name, company, email, phone, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('Amit Patel', 'Manufacturing', 'amit@mfg.com', '9876543213', 'New', 1))
        cursor.execute("""
            INSERT INTO leads (name, company, email, phone, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('Priya Kapoor', 'Digital Ventures', 'priya@digital.com', '9876543214', 'New', 1))

        # Insert sample deals
        cursor.execute("""
            INSERT INTO deals (lead_id, deal_value, stage, probability, owner_id)
            VALUES (?, ?, ?, ?, ?)
        """, (1, 50000, 'new', 0.3, 1))
        cursor.execute("""
            INSERT INTO deals (lead_id, deal_value, stage, probability, owner_id)
            VALUES (?, ?, ?, ?, ?)
        """, (2, 75000, 'qualified', 0.5, 1))
        cursor.execute("""
            INSERT INTO deals (lead_id, deal_value, stage, probability, owner_id)
            VALUES (?, ?, ?, ?, ?)
        """, (3, 100000, 'proposal', 0.7, 1))
        cursor.execute("""
            INSERT INTO deals (lead_id, deal_value, stage, probability, owner_id)
            VALUES (?, ?, ?, ?, ?)
        """, (4, 120000, 'negotiation', 0.8, 1))

        # Insert sample campaigns
        cursor.execute("""
            INSERT INTO campaigns (name, type, status, recipients, opens, clicks, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('Insurance Awareness', 'Email', 'Active', 3000, 1200, 450, 1))
        cursor.execute("""
            INSERT INTO campaigns (name, type, status, recipients, opens, clicks, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('Health Insurance Promotion', 'WhatsApp', 'Completed', 2500, 2000, 800, 1))
        cursor.execute("""
            INSERT INTO campaigns (name, type, status, recipients, opens, clicks, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('Q3 Product Launch', 'Email', 'Completed', 1200, 600, 180, 1))

        # Insert default settings for the test user
        cursor.execute("""
            INSERT INTO user_settings (user_id, full_name, email, phone, company, timezone, theme, notifications, email_notifications, sms_notifications)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (1, 'Test User', 'test@example.com', '+91-9876543210', '', 'IST', 'light', 1, 1, 0))

        # Insert sample contacts
        cursor.execute("""
            INSERT INTO contacts (name, company, email, phone, city, score, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('Neha Singh', 'Tech Startup', 'neha@techstartup.com', '+91-9876543210', 'Mumbai, Andheri West', 85, 1))
        cursor.execute("""
            INSERT INTO contacts (name, company, email, phone, city, score, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('Vikram Reddy', 'Tech Park', 'vikram@techpark.com', '+91-9876543211', 'Bangalore, Whitefield', 72, 1))
        cursor.execute("""
            INSERT INTO contacts (name, company, email, phone, city, score, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('Anjali Desai', 'Retail Chain', 'anjali@retail.com', '+91-9876543212', 'Pune, Kothrud', 65, 1))
        cursor.execute("""
            INSERT INTO contacts (name, company, email, phone, city, score, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('Amit Patel', 'Manufacturing', 'amit@mfg.com', '+91-9876543213', 'Ahmedabad, Naroda', 58, 1))
        cursor.execute("""
            INSERT INTO contacts (name, company, email, phone, city, score, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('Priya Kapoor', 'Digital Ventures', 'priya@digital.com', '+91-9876543214', 'Delhi, Connaught Place', 80, 1))

        # Insert a sample note so "Active Contacts" analytics has something to count.
        # call_datetime is left NULL here (excluded from the avg-response-time calc) since a
        # fixed seed date would predate the contact's real (CURRENT_TIMESTAMP) created_at and
        # produce a negative average - real notes added through the UI use the actual call time,
        # which is always >= the contact's created_at, so the formula holds for genuine usage.
        cursor.execute("""
            INSERT INTO contact_notes (contact_id, next_conversation, transcript)
            VALUES (?, ?, ?)
        """, (1, '2026-08-25T10:30', 'Discussed LAP requirements, sending document checklist.'))

        # Insert sample calls
        cursor.execute("""
            INSERT INTO calls (name, phone, duration_seconds, type, outcome, call_date, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('Neha Singh', '+91-9876543210', 320, 'Outbound', 'Interested', '2026-08-21', 1))
        cursor.execute("""
            INSERT INTO calls (name, phone, duration_seconds, type, outcome, call_date, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('Vikram Reddy', '+91-9876543211', 225, 'Inbound', 'Not Interested', '2026-08-21', 1))
        cursor.execute("""
            INSERT INTO calls (name, phone, duration_seconds, type, outcome, call_date, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('Anjali Desai', '+91-9876543212', 490, 'Outbound', 'Meeting Scheduled', '2026-08-20', 1))
        cursor.execute("""
            INSERT INTO calls (name, phone, duration_seconds, type, outcome, call_date, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('Amit Patel', '+91-9876543213', 410, 'Outbound', 'Follow-up Needed', '2026-08-20', 1))

        conn.commit()
        cursor.close()
        print("[OK] SQLite database initialized successfully!")
        print("[OK] Test user created: testuser / password")
        print("[OK] Sample leads, deals, campaigns, integrations, settings, contacts and calls added!")
