from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import sqlite3
from typing import List
import os
import uuid
from dotenv import load_dotenv

from database_sqlite import get_db, init_db
from schemas import (
    UserLogin, UserCreate, UserResponse, Token,
    LeadCreate, LeadUpdate, LeadResponse,
    DealCreate, DealMove, DealResponse,
    CampaignCreate, CampaignUpdate, CampaignResponse,
    IntegrationToggle, IntegrationResponse,
    SettingsUpdate, SettingsResponse,
    ContactCreate, ContactUpdate, ContactResponse,
    ContactNoteCreate, ContactNoteUpdate, ContactNoteResponse,
    LeadNoteCreate, LeadNoteUpdate, LeadNoteResponse,
    CallCreate, CallResponse,
    DialRequest, DialResponse, AISummaryResponse
)
from auth import hash_password, verify_password, create_access_token, decode_token

load_dotenv()

# Lifespan event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        init_db()
        print("[OK] SQLite database ready!")
    except Exception as e:
        print(f"[ERROR] Database error: {e}")
    try:
        # The DB is fully reset on every startup, so clear stale recordings that
        # no note in the fresh DB references, keeping the two in sync.
        for f in os.listdir(UPLOADS_DIR):
            os.remove(os.path.join(UPLOADS_DIR, f))
    except Exception as e:
        print(f"[WARN] Could not clear uploads directory: {e}")
    yield
    # Shutdown
    print("[OK] Server shutting down")

# Create FastAPI app
app = FastAPI(
    title="ArthaInvest CRM API (SQLite)",
    version="1.0.0",
    description="Backend API for ArthaInvest CRM - SQLite Version for Testing",
    lifespan=lifespan
)

# Add CORS middleware. Defaults to "*" for local development convenience - production
# deployments should set CORS_ORIGINS to a comma-separated list of real frontend origin(s),
# e.g. CORS_ORIGINS=https://app.example.com
_cors_origins_env = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = ["*"] if _cors_origins_env == "*" else [o.strip() for o in _cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded voice-note audio files
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads", "notes")
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "uploads")), name="uploads")

# ============= HELPER FUNCTIONS =============

def get_current_user(token: str = None):
    """Get current authenticated user"""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_data = decode_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_data

def campaign_row_to_dict(row):
    """Attach computed engagement/progress to a raw campaign row"""
    c = dict(row)
    recipients = c.get('recipients') or 0
    c['engagement'] = round((c.get('clicks') or 0) / recipients * 100) if recipients else 0
    c['progress'] = 100 if c.get('status') == 'Completed' else (round((c.get('opens') or 0) / recipients * 100) if recipients else 0)
    return c

def format_duration(seconds):
    """Format a duration in seconds as '5m 20s'"""
    seconds = seconds or 0
    minutes, secs = divmod(seconds, 60)
    return f"{minutes}m {secs}s"

def call_row_to_dict(row):
    c = dict(row)
    c['duration'] = format_duration(c.get('duration_seconds'))
    return c

# ============= HEALTH CHECK =============

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "ArthaInvest API is running"}

# ============= AUTHENTICATION ENDPOINTS =============

@app.post("/api/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login user and return token"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (credentials.username,)
        )
        user = cursor.fetchone()

    if not user or not verify_password(credentials.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user['is_active']:
        raise HTTPException(status_code=403, detail="User inactive")

    # Update last login
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user['id'],)
        )
        conn.commit()

    # Create token
    access_token = create_access_token(
        data={"user_id": user['id'], "username": user['username']}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user['id'],
        "username": user['username'],
        "role": user['role']
    }

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user: UserCreate):
    """Register new user"""
    with get_db() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO users (username, email, password, full_name, role)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user.username, user.email, hash_password(user.password),
                 user.full_name, user.role)
            )
            conn.commit()

            # Get created user
            cursor.execute("SELECT id, username, email, full_name, role, is_active FROM users WHERE username = ?", (user.username,))
            new_user = cursor.fetchone()

            return UserResponse(**dict(new_user))

        except sqlite3.IntegrityError as e:
            raise HTTPException(status_code=400, detail="Username or email already exists")

# ============= LEADS ENDPOINTS =============

@app.get("/api/leads", response_model=list[LeadResponse])
async def get_leads(token: str = Query(None), status: str = Query(None)):
    """Get all leads, optionally filtered by status"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()

        if status:
            cursor.execute("SELECT * FROM leads WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM leads ORDER BY created_at DESC")

        leads = [dict(row) for row in cursor.fetchall()]

    return leads

@app.post("/api/leads", response_model=LeadResponse)
async def create_lead(lead: LeadCreate, token: str = Query(None)):
    """Create new lead"""
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO leads (name, company, email, phone, product, source, created_by, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (lead.name, lead.company, lead.email, lead.phone, lead.product,
             lead.source, current_user['user_id'], 'New')
        )
        conn.commit()
        lead_id = cursor.lastrowid

        # Get created lead
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        new_lead = cursor.fetchone()

    return dict(new_lead)

@app.get("/api/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, token: str = Query(None)):
    """Get single lead"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        lead = cursor.fetchone()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return dict(lead)

@app.put("/api/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: int, lead: LeadUpdate, token: str = Query(None)):
    """Update lead"""
    get_current_user(token)

    updates = []
    values = []

    if lead.name is not None:
        updates.append("name = ?")
        values.append(lead.name)
    if lead.company is not None:
        updates.append("company = ?")
        values.append(lead.company)
    if lead.email is not None:
        updates.append("email = ?")
        values.append(lead.email)
    if lead.phone is not None:
        updates.append("phone = ?")
        values.append(lead.phone)
    if lead.product is not None:
        updates.append("product = ?")
        values.append(lead.product)
    if lead.status is not None:
        updates.append("status = ?")
        values.append(lead.status)
    if lead.ai_score is not None:
        updates.append("ai_score = ?")
        values.append(lead.ai_score)
    if lead.lead_tier is not None:
        updates.append("lead_tier = ?")
        values.append(lead.lead_tier)

    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(lead_id)

    query = f"UPDATE leads SET {', '.join(updates)} WHERE id = ?"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()

        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        updated_lead = cursor.fetchone()

    if not updated_lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return dict(updated_lead)

@app.delete("/api/leads/{lead_id}")
async def delete_lead(lead_id: int, token: str = Query(None)):
    """Delete lead"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT audio_url FROM lead_notes WHERE lead_id = ? AND audio_url IS NOT NULL", (lead_id,))
        audio_urls = [row['audio_url'] for row in cursor.fetchall()]
        cursor.execute("DELETE FROM lead_notes WHERE lead_id = ?", (lead_id,))
        cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        conn.commit()

    for audio_url in audio_urls:
        _delete_audio_file(audio_url)

    return {"message": "Lead deleted"}

# ============= DEALS/PIPELINE ENDPOINTS =============

@app.get("/api/deals", response_model=list[DealResponse])
async def get_deals(stage: str = Query(None), token: str = Query(None)):
    """Get all deals, optionally filtered by stage"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()

        if stage:
            cursor.execute("SELECT * FROM deals WHERE stage = ? ORDER BY created_at DESC", (stage,))
        else:
            cursor.execute("SELECT * FROM deals ORDER BY created_at DESC")

        deals = [dict(row) for row in cursor.fetchall()]

    return deals

VALID_STAGES = ['new', 'qualified', 'proposal', 'negotiation', 'closed']

@app.post("/api/deals", response_model=DealResponse)
async def create_deal(deal: DealCreate, token: str = Query(None)):
    """Create new deal"""
    current_user = get_current_user(token)

    stage = (deal.stage or 'new').lower()
    if stage not in VALID_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of {VALID_STAGES}")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO deals (lead_id, deal_value, probability, loan_product, stage, owner_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (deal.lead_id, deal.deal_value, deal.probability, deal.loan_product, stage, current_user['user_id'])
        )
        conn.commit()
        deal_id = cursor.lastrowid

        cursor.execute("SELECT * FROM deals WHERE id = ?", (deal_id,))
        new_deal = cursor.fetchone()

    return dict(new_deal)

@app.put("/api/deals/{deal_id}/move")
async def move_deal(deal_id: int, move: DealMove, token: str = Query(None)):
    """Move deal to different stage (Kanban drag-drop)"""
    get_current_user(token)

    if move.stage not in VALID_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of {VALID_STAGES}")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE deals SET stage = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (move.stage, deal_id)
        )
        conn.commit()

        cursor.execute("SELECT * FROM deals WHERE id = ?", (deal_id,))
        updated_deal = cursor.fetchone()

    if not updated_deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    return dict(updated_deal)

@app.delete("/api/deals/{deal_id}")
async def delete_deal(deal_id: int, token: str = Query(None)):
    """Delete a deal"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM deals WHERE id = ?", (deal_id,))
        conn.commit()

    return {"message": "Deal deleted"}

# ============= ANALYTICS ENDPOINTS =============

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics(token: str = Query(None)):
    """Get dashboard KPI data"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM leads")
        total_leads = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM leads WHERE status = 'qualified'")
        qualified = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM deals WHERE stage != 'closed'")
        active_deals = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM deals WHERE stage = 'closed'")
        closed_deals = cursor.fetchone()['count']

    return {
        "total_leads": total_leads,
        "qualified_leads": qualified,
        "active_deals": active_deals,
        "closed_deals": closed_deals
    }

@app.get("/api/analytics/conversion-rate")
async def get_conversion_rate(token: str = Query(None)):
    """Get lead to deal conversion rate"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM leads")
        total_leads = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM deals")
        total_deals = cursor.fetchone()['count']

    conversion_rate = (total_deals / total_leads * 100) if total_leads > 0 else 0

    return {
        "total_leads": total_leads,
        "total_deals": total_deals,
        "conversion_rate": round(conversion_rate, 2)
    }

@app.get("/api/analytics/sales")
async def get_sales_analytics(token: str = Query(None)):
    """Get sales report metrics, computed from real deals/leads data"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count, COALESCE(SUM(deal_value), 0) as total FROM deals WHERE stage = 'closed'")
        closed = cursor.fetchone()
        closed_count = closed['count']
        total_revenue = closed['total']

        cursor.execute("SELECT COUNT(*) as count FROM deals")
        total_deals = cursor.fetchone()['count']

        cursor.execute("SELECT AVG(deal_value) as avg_value FROM deals")
        avg_deal_row = cursor.fetchone()
        avg_deal_value = avg_deal_row['avg_value'] or 0

    win_rate = round((closed_count / total_deals * 100), 1) if total_deals > 0 else 0

    return {
        "total_revenue": total_revenue,
        "deals_closed": closed_count,
        "win_rate": win_rate,
        "avg_deal_value": round(avg_deal_value)
    }

# ============= CAMPAIGNS ENDPOINTS =============

@app.get("/api/campaigns", response_model=list[CampaignResponse])
async def get_campaigns(token: str = Query(None)):
    """Get all marketing campaigns"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM campaigns ORDER BY created_at DESC")
        campaigns = [campaign_row_to_dict(row) for row in cursor.fetchall()]

    return campaigns

@app.post("/api/campaigns", response_model=CampaignResponse)
async def create_campaign(campaign: CampaignCreate, token: str = Query(None)):
    """Create a new marketing campaign"""
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO campaigns (name, type, status, recipients, opens, clicks, created_by)
            VALUES (?, ?, ?, ?, 0, 0, ?)
            """,
            (campaign.name, campaign.type, campaign.status, campaign.recipients, current_user['user_id'])
        )
        conn.commit()
        campaign_id = cursor.lastrowid

        cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        new_campaign = cursor.fetchone()

    return campaign_row_to_dict(new_campaign)

@app.put("/api/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: int, campaign: CampaignUpdate, token: str = Query(None)):
    """Update a marketing campaign"""
    get_current_user(token)

    updates = []
    values = []

    for field in ['name', 'type', 'status', 'recipients', 'opens', 'clicks']:
        value = getattr(campaign, field)
        if value is not None:
            updates.append(f"{field} = ?")
            values.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(campaign_id)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE campaigns SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()

        cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        updated_campaign = cursor.fetchone()

    if not updated_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return campaign_row_to_dict(updated_campaign)

@app.delete("/api/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: int, token: str = Query(None)):
    """Delete a marketing campaign"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
        conn.commit()

    return {"message": "Campaign deleted"}

# ============= INTEGRATIONS ENDPOINTS =============

@app.get("/api/integrations", response_model=list[IntegrationResponse])
async def get_integrations(token: str = Query(None)):
    """Get all integrations and their connection status"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM integrations ORDER BY id")
        integrations = [dict(row) for row in cursor.fetchall()]

    for i in integrations:
        i['connected'] = bool(i['connected'])

    return integrations

@app.put("/api/integrations/{integration_id}/toggle", response_model=IntegrationResponse)
async def toggle_integration(integration_id: int, toggle: IntegrationToggle, token: str = Query(None)):
    """Connect or disconnect an integration"""
    get_current_user(token)

    last_sync = 'now' if toggle.connected else 'never'

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE integrations SET connected = ?, last_sync = ? WHERE id = ?",
            (1 if toggle.connected else 0, last_sync, integration_id)
        )
        conn.commit()

        cursor.execute("SELECT * FROM integrations WHERE id = ?", (integration_id,))
        updated = cursor.fetchone()

    if not updated:
        raise HTTPException(status_code=404, detail="Integration not found")

    result = dict(updated)
    result['connected'] = bool(result['connected'])
    return result

# ============= SETTINGS ENDPOINTS =============

@app.get("/api/settings", response_model=SettingsResponse)
async def get_settings(token: str = Query(None)):
    """Get the current user's settings, creating a default row if none exists yet"""
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (current_user['user_id'],))
        settings = cursor.fetchone()

        if not settings:
            cursor.execute("SELECT full_name, email FROM users WHERE id = ?", (current_user['user_id'],))
            user = cursor.fetchone()
            cursor.execute(
                """
                INSERT INTO user_settings (user_id, full_name, email)
                VALUES (?, ?, ?)
                """,
                (current_user['user_id'], user['full_name'] if user else '', user['email'] if user else '')
            )
            conn.commit()
            cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (current_user['user_id'],))
            settings = cursor.fetchone()

    result = dict(settings)
    result['notifications'] = bool(result['notifications'])
    result['email_notifications'] = bool(result['email_notifications'])
    result['sms_notifications'] = bool(result['sms_notifications'])
    return result

@app.put("/api/settings", response_model=SettingsResponse)
async def update_settings(settings: SettingsUpdate, token: str = Query(None)):
    """Update the current user's settings (creates the row if it doesn't exist yet)"""
    current_user = get_current_user(token)

    field_map = {
        'full_name': settings.full_name,
        'email': settings.email,
        'phone': settings.phone,
        'company': settings.company,
        'timezone': settings.timezone,
        'theme': settings.theme,
        'notifications': None if settings.notifications is None else int(settings.notifications),
        'email_notifications': None if settings.email_notifications is None else int(settings.email_notifications),
        'sms_notifications': None if settings.sms_notifications is None else int(settings.sms_notifications),
    }
    updates = [(k, v) for k, v in field_map.items() if v is not None]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM user_settings WHERE user_id = ?", (current_user['user_id'],))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("INSERT INTO user_settings (user_id) VALUES (?)", (current_user['user_id'],))

        if updates:
            set_clause = ', '.join(f"{k} = ?" for k, _ in updates)
            values = [v for _, v in updates] + [current_user['user_id']]
            cursor.execute(f"UPDATE user_settings SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", values)

        conn.commit()
        cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (current_user['user_id'],))
        result = dict(cursor.fetchone())

    result['notifications'] = bool(result['notifications'])
    result['email_notifications'] = bool(result['email_notifications'])
    result['sms_notifications'] = bool(result['sms_notifications'])
    return result

# ============= CONTACTS ENDPOINTS =============

@app.get("/api/contacts", response_model=list[ContactResponse])
async def get_contacts(token: str = Query(None)):
    """Get all contacts"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts ORDER BY created_at DESC")
        contacts = [dict(row) for row in cursor.fetchall()]

    return contacts

@app.post("/api/contacts", response_model=ContactResponse)
async def create_contact(contact: ContactCreate, token: str = Query(None)):
    """Create a new contact"""
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO contacts (name, company, email, phone, city, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (contact.name, contact.company, contact.email, contact.phone, contact.city, current_user['user_id'])
        )
        conn.commit()
        contact_id = cursor.lastrowid

        cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        new_contact = cursor.fetchone()

    return dict(new_contact)

@app.put("/api/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: int, contact: ContactUpdate, token: str = Query(None)):
    """Update a contact"""
    get_current_user(token)

    updates = []
    values = []

    for field in ['name', 'company', 'email', 'phone', 'city', 'score']:
        value = getattr(contact, field)
        if value is not None:
            updates.append(f"{field} = ?")
            values.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(contact_id)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE contacts SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()

        cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        updated_contact = cursor.fetchone()

    if not updated_contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return dict(updated_contact)

@app.delete("/api/contacts/{contact_id}")
async def delete_contact(contact_id: int, token: str = Query(None)):
    """Delete a contact"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT audio_url FROM contact_notes WHERE contact_id = ? AND audio_url IS NOT NULL", (contact_id,))
        audio_urls = [row['audio_url'] for row in cursor.fetchall()]
        cursor.execute("DELETE FROM contact_notes WHERE contact_id = ?", (contact_id,))
        cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        conn.commit()

    for audio_url in audio_urls:
        _delete_audio_file(audio_url)

    return {"message": "Contact deleted"}

# ============= CONTACT NOTES ENDPOINTS =============

@app.get("/api/contacts/{contact_id}/notes", response_model=list[ContactNoteResponse])
async def get_contact_notes(contact_id: int, token: str = Query(None)):
    """Get all notes for a contact"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contact_notes WHERE contact_id = ? ORDER BY created_at DESC", (contact_id,))
        notes = [dict(row) for row in cursor.fetchall()]

    return notes

@app.post("/api/contacts/{contact_id}/notes", response_model=ContactNoteResponse)
async def create_contact_note(contact_id: int, note: ContactNoteCreate, token: str = Query(None)):
    """Add a note to a contact"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO contact_notes (contact_id, call_datetime, next_conversation, transcript)
            VALUES (?, ?, ?, ?)
            """,
            (contact_id, note.call_datetime, note.next_conversation, note.transcript)
        )
        conn.commit()
        note_id = cursor.lastrowid

        cursor.execute("SELECT * FROM contact_notes WHERE id = ?", (note_id,))
        new_note = cursor.fetchone()

    return dict(new_note)

@app.put("/api/contacts/{contact_id}/notes/{note_id}", response_model=ContactNoteResponse)
async def update_contact_note(contact_id: int, note_id: int, note: ContactNoteUpdate, token: str = Query(None)):
    """Update a contact note"""
    get_current_user(token)

    updates = []
    values = []

    for field in ['call_datetime', 'next_conversation', 'transcript']:
        value = getattr(note, field)
        if value is not None:
            updates.append(f"{field} = ?")
            values.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(note_id)
    values.append(contact_id)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE contact_notes SET {', '.join(updates)} WHERE id = ? AND contact_id = ?", values)
        conn.commit()

        cursor.execute("SELECT * FROM contact_notes WHERE id = ?", (note_id,))
        updated_note = cursor.fetchone()

    if not updated_note:
        raise HTTPException(status_code=404, detail="Note not found")

    return dict(updated_note)

@app.delete("/api/contacts/{contact_id}/notes/{note_id}")
async def delete_contact_note(contact_id: int, note_id: int, token: str = Query(None)):
    """Delete a contact note"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT audio_url FROM contact_notes WHERE id = ? AND contact_id = ?", (note_id, contact_id))
        existing = cursor.fetchone()
        cursor.execute("DELETE FROM contact_notes WHERE id = ? AND contact_id = ?", (note_id, contact_id))
        conn.commit()

    if existing and existing['audio_url']:
        _delete_audio_file(existing['audio_url'])

    return {"message": "Note deleted"}

@app.post("/api/contacts/{contact_id}/notes/{note_id}/audio", response_model=ContactNoteResponse)
async def upload_note_audio(contact_id: int, note_id: int, token: str = Query(None), audio: UploadFile = File(...)):
    """Attach a recorded voice note to a note, replacing any previous recording"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT audio_url FROM contact_notes WHERE id = ? AND contact_id = ?", (note_id, contact_id))
        existing = cursor.fetchone()

    if not existing:
        raise HTTPException(status_code=404, detail="Note not found")

    if existing['audio_url']:
        _delete_audio_file(existing['audio_url'])

    ext = os.path.splitext(audio.filename or '')[1] or '.webm'
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOADS_DIR, filename)
    with open(file_path, 'wb') as f:
        f.write(await audio.read())

    audio_url = f"/uploads/notes/{filename}"

    with get_db() as conn:
        cursor = conn.cursor()
        # Deliberately not touching updated_at here: saveNote() on the frontend always calls
        # createContactNote/updateContactNote first (which sets updated_at correctly for genuine
        # edits) and only then uploads the recording, including for a brand-new note that has a
        # voice note attached at creation time. Bumping updated_at again here would make a note's
        # very first save falsely show an "Edited" badge in the notes history.
        cursor.execute(
            "UPDATE contact_notes SET audio_url = ? WHERE id = ?",
            (audio_url, note_id)
        )
        conn.commit()
        cursor.execute("SELECT * FROM contact_notes WHERE id = ?", (note_id,))
        updated_note = cursor.fetchone()

    return dict(updated_note)

@app.post("/api/contacts/{contact_id}/ai-suggest", response_model=AISummaryResponse)
async def ai_suggest_contact_followup(contact_id: int, token: str = Query(None)):
    """AI-drafted follow-up suggestion from a contact's note history, via Claude"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM contacts WHERE id = ?", (contact_id,))
        contact = cursor.fetchone()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

        cursor.execute("SELECT * FROM contact_notes WHERE contact_id = ? ORDER BY created_at DESC", (contact_id,))
        notes = [dict(row) for row in cursor.fetchall()]

    return _generate_ai_suggestion(contact['name'], notes)

def _delete_audio_file(audio_url):
    """Best-effort removal of a previously uploaded note recording"""
    try:
        filename = os.path.basename(audio_url)
        file_path = os.path.join(UPLOADS_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    except OSError as e:
        print(f"[WARN] Could not remove audio file {audio_url}: {e}")

def _generate_ai_suggestion(person_name, notes):
    """Draft a follow-up suggestion from a contact/lead's note history via Claude. Requires
    ANTHROPIC_API_KEY - returns configured=False (not an error) when it isn't set, so the
    frontend can show a clear "not set up" message instead of a generic failure."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return AISummaryResponse(configured=False, message="Claude AI is not configured on this server.")

    transcripts = [n['transcript'] for n in notes if n.get('transcript')]
    if not transcripts:
        return AISummaryResponse(configured=True, message="No notes yet to summarize.", suggestion=None)

    history = "\n".join(f"- {t}" for t in transcripts)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": (
                    f"You are a sales assistant for an insurance/loan CRM. Here is the call "
                    f"note history for {person_name}:\n{history}\n\n"
                    "In 2-3 short sentences, suggest what the next follow-up conversation "
                    "should cover. Be specific and actionable, not generic."
                )
            }]
        )
        suggestion = "".join(block.text for block in response.content if hasattr(block, 'text')).strip()
        return AISummaryResponse(configured=True, message="Suggestion generated.", suggestion=suggestion)
    except Exception as e:
        return AISummaryResponse(configured=True, message=f"Claude request failed: {str(e)}")

# ============= LEAD NOTES ENDPOINTS =============

@app.get("/api/leads/{lead_id}/notes", response_model=list[LeadNoteResponse])
async def get_lead_notes(lead_id: int, token: str = Query(None)):
    """Get all notes for a lead"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lead_notes WHERE lead_id = ? ORDER BY created_at DESC", (lead_id,))
        notes = [dict(row) for row in cursor.fetchall()]

    return notes

@app.post("/api/leads/{lead_id}/notes", response_model=LeadNoteResponse)
async def create_lead_note(lead_id: int, note: LeadNoteCreate, token: str = Query(None)):
    """Add a note to a lead"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO lead_notes (lead_id, call_datetime, next_conversation, transcript)
            VALUES (?, ?, ?, ?)
            """,
            (lead_id, note.call_datetime, note.next_conversation, note.transcript)
        )
        conn.commit()
        note_id = cursor.lastrowid

        cursor.execute("SELECT * FROM lead_notes WHERE id = ?", (note_id,))
        new_note = cursor.fetchone()

    return dict(new_note)

@app.put("/api/leads/{lead_id}/notes/{note_id}", response_model=LeadNoteResponse)
async def update_lead_note(lead_id: int, note_id: int, note: LeadNoteUpdate, token: str = Query(None)):
    """Update a lead note"""
    get_current_user(token)

    updates = []
    values = []

    for field in ['call_datetime', 'next_conversation', 'transcript']:
        value = getattr(note, field)
        if value is not None:
            updates.append(f"{field} = ?")
            values.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(note_id)
    values.append(lead_id)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE lead_notes SET {', '.join(updates)} WHERE id = ? AND lead_id = ?", values)
        conn.commit()

        cursor.execute("SELECT * FROM lead_notes WHERE id = ?", (note_id,))
        updated_note = cursor.fetchone()

    if not updated_note:
        raise HTTPException(status_code=404, detail="Note not found")

    return dict(updated_note)

@app.delete("/api/leads/{lead_id}/notes/{note_id}")
async def delete_lead_note(lead_id: int, note_id: int, token: str = Query(None)):
    """Delete a lead note"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT audio_url FROM lead_notes WHERE id = ? AND lead_id = ?", (note_id, lead_id))
        existing = cursor.fetchone()
        cursor.execute("DELETE FROM lead_notes WHERE id = ? AND lead_id = ?", (note_id, lead_id))
        conn.commit()

    if existing and existing['audio_url']:
        _delete_audio_file(existing['audio_url'])

    return {"message": "Note deleted"}

@app.post("/api/leads/{lead_id}/notes/{note_id}/audio", response_model=LeadNoteResponse)
async def upload_lead_note_audio(lead_id: int, note_id: int, token: str = Query(None), audio: UploadFile = File(...)):
    """Attach a recorded voice note to a lead note, replacing any previous recording"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT audio_url FROM lead_notes WHERE id = ? AND lead_id = ?", (note_id, lead_id))
        existing = cursor.fetchone()

    if not existing:
        raise HTTPException(status_code=404, detail="Note not found")

    if existing['audio_url']:
        _delete_audio_file(existing['audio_url'])

    ext = os.path.splitext(audio.filename or '')[1] or '.webm'
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOADS_DIR, filename)
    with open(file_path, 'wb') as f:
        f.write(await audio.read())

    audio_url = f"/uploads/notes/{filename}"

    with get_db() as conn:
        cursor = conn.cursor()
        # See the identical note on upload_note_audio() above: not touching updated_at here so a
        # brand-new note saved with a voice note attached doesn't falsely show "Edited".
        cursor.execute(
            "UPDATE lead_notes SET audio_url = ? WHERE id = ?",
            (audio_url, note_id)
        )
        conn.commit()
        cursor.execute("SELECT * FROM lead_notes WHERE id = ?", (note_id,))
        updated_note = cursor.fetchone()

    return dict(updated_note)

@app.post("/api/leads/{lead_id}/ai-suggest", response_model=AISummaryResponse)
async def ai_suggest_lead_followup(lead_id: int, token: str = Query(None)):
    """AI-drafted follow-up suggestion from a lead's note history, via Claude"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM leads WHERE id = ?", (lead_id,))
        lead = cursor.fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        cursor.execute("SELECT * FROM lead_notes WHERE lead_id = ? ORDER BY created_at DESC", (lead_id,))
        notes = [dict(row) for row in cursor.fetchall()]

    return _generate_ai_suggestion(lead['name'], notes)

# ============= CALLS ENDPOINTS =============

@app.get("/api/calls", response_model=list[CallResponse])
async def get_calls(token: str = Query(None)):
    """Get all logged calls"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM calls ORDER BY call_date DESC, created_at DESC")
        calls = [call_row_to_dict(row) for row in cursor.fetchall()]

    return calls

@app.post("/api/calls", response_model=CallResponse)
async def create_call(call: CallCreate, token: str = Query(None)):
    """Log a new call"""
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO calls (name, phone, duration_seconds, type, outcome, call_date, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (call.name, call.phone, call.duration_seconds, call.type, call.outcome, call.call_date, current_user['user_id'])
        )
        conn.commit()
        call_id = cursor.lastrowid

        cursor.execute("SELECT * FROM calls WHERE id = ?", (call_id,))
        new_call = cursor.fetchone()

    return call_row_to_dict(new_call)

@app.delete("/api/calls/{call_id}")
async def delete_call(call_id: int, token: str = Query(None)):
    """Delete a logged call"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM calls WHERE id = ?", (call_id,))
        conn.commit()

    return {"message": "Call deleted"}

@app.post("/api/calls/dial", response_model=DialResponse)
async def dial_call(dial: DialRequest, token: str = Query(None)):
    """Click-to-call via Twilio: rings the agent's own phone first, then bridges the call to
    the customer's number once the agent answers. Requires TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER (a Twilio-owned number) to be set, plus the
    agent's own phone number saved in Settings - without those, returns configured=False so
    the frontend can fall back to a plain tel: link instead of erroring."""
    current_user = get_current_user(token)

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not (account_sid and auth_token and from_number):
        return DialResponse(configured=False, message="Twilio is not configured on this server.")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT phone FROM user_settings WHERE user_id = ?", (current_user['user_id'],))
        row = cursor.fetchone()

    agent_number = row['phone'] if row else None
    if not agent_number:
        return DialResponse(
            configured=False,
            message="Add your own phone number in Settings first - Twilio calls you there, then connects you to the customer."
        )

    try:
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioRestException

        client = Client(account_sid, auth_token)
        call = client.calls.create(
            to=agent_number,
            from_=from_number,
            twiml=f'<Response><Dial callerId="{from_number}">{dial.to}</Dial></Response>'
        )
        return DialResponse(configured=True, message=f"Calling you at {agent_number} now.", call_sid=call.sid)
    except TwilioRestException as e:
        return DialResponse(configured=True, message=f"Twilio couldn't place the call: {e.msg}")
    except Exception as e:
        return DialResponse(configured=True, message=f"Call failed: {str(e)}")

# ============= MORE ANALYTICS ENDPOINTS =============

@app.get("/api/analytics/contacts")
async def get_contacts_analytics(token: str = Query(None)):
    """Get contacts report metrics, computed from real contacts/notes data"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM contacts")
        total_contacts = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(DISTINCT contact_id) as count FROM contact_notes")
        active_contacts = cursor.fetchone()['count']

        # Avg hours between a contact being added and their first logged note
        cursor.execute("""
            SELECT AVG(
                (julianday(first_note.call_datetime) - julianday(c.created_at)) * 24
            ) as avg_hours
            FROM contacts c
            JOIN (
                SELECT contact_id, MIN(call_datetime) as call_datetime
                FROM contact_notes
                WHERE call_datetime IS NOT NULL
                GROUP BY contact_id
            ) first_note ON first_note.contact_id = c.id
        """)
        avg_hours_row = cursor.fetchone()
        avg_response_hours = avg_hours_row['avg_hours'] if avg_hours_row and avg_hours_row['avg_hours'] is not None else None

        # "High-value" contacts (score >= 70) as a proxy for conversion
        cursor.execute("SELECT COUNT(*) as count FROM contacts WHERE score >= 70")
        high_value = cursor.fetchone()['count']

    conversion_rate = round((high_value / total_contacts * 100), 1) if total_contacts > 0 else 0

    return {
        "total_contacts": total_contacts,
        "active_contacts": active_contacts,
        "avg_response_time_hours": round(avg_response_hours, 1) if avg_response_hours is not None else None,
        "conversion_rate": conversion_rate
    }

@app.get("/api/analytics/calls")
async def get_calls_analytics(token: str = Query(None)):
    """Get calls report metrics, computed from real calls data"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count, COALESCE(AVG(duration_seconds), 0) as avg_seconds FROM calls")
        row = cursor.fetchone()
        total_calls = row['count']
        avg_seconds = row['avg_seconds']

        cursor.execute("""
            SELECT COUNT(*) as count FROM calls
            WHERE outcome IN ('Interested', 'Meeting Scheduled')
        """)
        successful = cursor.fetchone()['count']

        cursor.execute("""
            SELECT COUNT(*) as count FROM calls
            WHERE strftime('%Y-%m', call_date) = strftime('%Y-%m', 'now')
        """)
        calls_this_month = cursor.fetchone()['count']

    success_rate = round((successful / total_calls * 100), 1) if total_calls > 0 else 0

    return {
        "total_calls": total_calls,
        "avg_duration": format_duration(round(avg_seconds)),
        "call_success_rate": success_rate,
        "calls_this_month": calls_this_month
    }

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
