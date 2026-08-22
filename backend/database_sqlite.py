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

        conn.commit()

        # Insert test user (testuser/TestPass123 - must match Login.jsx displayed hint)
        from auth import hash_password
        hashed_password = hash_password("TestPass123")
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

        conn.commit()
        cursor.close()
        print("[OK] SQLite database initialized successfully!")
        print("[OK] Test user created: testuser / password")
        print("[OK] Sample leads and deals added!")
