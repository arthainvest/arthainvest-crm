import sqlite3
from contextlib import contextmanager
import os

DB_PATH = "arthainvest_crm.db"

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

def init_db():
    """Initialize database with schema"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Drop existing tables for fresh start
        cursor.execute("DROP TABLE IF EXISTS activity_log")
        cursor.execute("DROP TABLE IF EXISTS deals")
        cursor.execute("DROP TABLE IF EXISTS leads")
        cursor.execute("DROP TABLE IF EXISTS campaigns")
        cursor.execute("DROP TABLE IF EXISTS integrations")
        cursor.execute("DROP TABLE IF EXISTS user_settings")
        cursor.execute("DROP TABLE IF EXISTS users")

        # Create tables
        cursor.execute("""
            CREATE TABLE users (
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
            CREATE TABLE leads (
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                deal_value REAL,
                stage TEXT DEFAULT 'new',
                probability REAL,
                expected_close_date DATE,
                owner_id INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id),
                FOREIGN KEY (owner_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE activity_log (
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
            CREATE TABLE campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT DEFAULT 'Email',
                status TEXT DEFAULT 'Active',
                recipients INTEGER DEFAULT 0,
                opens INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE integrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                logo TEXT,
                description TEXT,
                connected INTEGER DEFAULT 0,
                last_sync TEXT DEFAULT 'never'
            )
        """)

        cursor.execute("""
            CREATE TABLE user_settings (
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

        conn.commit()

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
        """, ('Neha Singh', 'StartUp Fund', 'neha@startup.com', '9876543210', 'new', 1))
        cursor.execute("""
            INSERT INTO leads (name, company, email, phone, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('Vikram Reddy', 'Tech Park', 'vikram@techpark.com', '9876543211', 'new', 1))
        cursor.execute("""
            INSERT INTO leads (name, company, email, phone, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('Anjali Desai', 'Retail Chain', 'anjali@retail.com', '9876543212', 'new', 1))
        cursor.execute("""
            INSERT INTO leads (name, company, email, phone, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('Amit Patel', 'Manufacturing', 'amit@mfg.com', '9876543213', 'new', 1))
        cursor.execute("""
            INSERT INTO leads (name, company, email, phone, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('Priya Kapoor', 'Digital Ventures', 'priya@digital.com', '9876543214', 'new', 1))

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

        # Insert integrations catalog
        cursor.execute("""
            INSERT INTO integrations (name, logo, description, connected, last_sync)
            VALUES (?, ?, ?, ?, ?)
        """, ('Gmail', '📧', 'Sync emails and contacts from Gmail', 1, '2 hours ago'))
        cursor.execute("""
            INSERT INTO integrations (name, logo, description, connected, last_sync)
            VALUES (?, ?, ?, ?, ?)
        """, ('Google Calendar', '📅', 'Sync meetings and schedule', 1, '5 mins ago'))
        cursor.execute("""
            INSERT INTO integrations (name, logo, description, connected, last_sync)
            VALUES (?, ?, ?, ?, ?)
        """, ('Zapier', '⚡', 'Connect with 1000+ apps via Zapier', 1, '3 days ago'))
        cursor.execute("""
            INSERT INTO integrations (name, logo, description, connected, last_sync)
            VALUES (?, ?, ?, ?, ?)
        """, ('Slack', '💬', 'Send notifications to Slack', 0, 'never'))
        cursor.execute("""
            INSERT INTO integrations (name, logo, description, connected, last_sync)
            VALUES (?, ?, ?, ?, ?)
        """, ('HubSpot', '🎯', 'Two-way sync with HubSpot', 1, '5 mins ago'))

        # Insert default settings for the test user
        cursor.execute("""
            INSERT INTO user_settings (user_id, full_name, email, phone, company, timezone, theme, notifications, email_notifications, sms_notifications)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (1, 'Test User', 'test@example.com', '+91-9876543210', '', 'IST', 'light', 1, 1, 0))

        conn.commit()
        cursor.close()
        print("[OK] SQLite database initialized successfully!")
        print("[OK] Test user created: testuser / password")
        print("[OK] Sample leads, deals, campaigns, integrations and settings added!")
