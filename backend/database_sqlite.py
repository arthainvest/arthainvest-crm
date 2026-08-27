import sqlite3
from contextlib import contextmanager
import os

# Overridable so tests can point at an isolated temp file instead of the real dev database.
DB_PATH = os.getenv("DB_PATH", "arthainvest_crm.db")

@contextmanager
def get_db():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
        ('Claude AI', '✨', 'AI-drafted follow-ups and note summaries', 0, 'never'),
        ('LinkedIn', '💼', 'Sync leads and posts from LinkedIn', 0, 'never'),
        ('WhatsApp Business API', '💬', 'Send WhatsApp messages via Meta Cloud API', 0, 'never'),
        ('Email Service', '📮', 'Send real emails via SMTP', 0, 'never'),
        ('Mailchimp', '🐒', 'Sync contacts and send email campaigns', 0, 'never'),
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
