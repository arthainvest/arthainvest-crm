from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager
import sqlite3
from typing import List
import os
import uuid
import smtplib
import hashlib
import hmac
import json
import secrets
import asyncio
from datetime import datetime, timedelta
from email.mime.text import MIMEText
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
    DialRequest, DialResponse, AISummaryResponse,
    WhatsAppSendRequest, WhatsAppSendResponse, WhatsAppReplyRequest,
    WhatsAppTemplatesResponse, WhatsAppConversationResponse, WhatsAppMessageResponse,
    ConversationAssign, ConversationStatusUpdate,
    TagCreate, TagResponse, EntityTagRequest,
    GroupCreate, GroupResponse, EntityGroupRequest,
    CustomFieldCreate, CustomFieldResponse, CustomFieldValueSet,
    QuickReplyCreate, QuickReplyUpdate, QuickReplyResponse,
    AutomationCreate, AutomationUpdate, AutomationResponse, AutomationEnrollRequest,
    ApiKeyCreate, ApiKeyResponse, ApiKeyCreateResponse,
    EmailSendRequest, EmailSendResponse,
    SmsSendRequest, SmsSendResponse,
    MailchimpSyncResponse,
    TeamMemberCreate, TeamMemberUpdate, TeamMemberResponse, TeamProductivityRow
)
from auth import hash_password, verify_password, create_access_token, decode_token

load_dotenv()

_automation_scheduler_task = None

# Lifespan event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global _automation_scheduler_task
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
    # In-process drip/automation runner. There's no Celery/Redis in this app yet, so this is a
    # lightweight stand-in: a loop that wakes up once a minute and fires any automation step
    # whose next_run_at has arrived. Fine at this scale; a real task queue is worth adding
    # before automation volume gets large or the app runs multiple backend instances.
    _automation_scheduler_task = asyncio.create_task(_run_automation_scheduler())
    yield
    # Shutdown
    if _automation_scheduler_task:
        _automation_scheduler_task.cancel()
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

# ============= WHATSAPP HELPERS =============

def normalize_phone(phone):
    """Digits-only phone number, e.g. '+91 98765-43210' -> '919876543210'."""
    return ''.join(ch for ch in (phone or '') if ch.isdigit())

def _phone_suffix_match(a, b, length=10):
    """Compare the last `length` digits so a stored '+91-9876543210' matches WhatsApp's
    '919876543210' (country code included) without needing exact formatting to line up."""
    return bool(a) and bool(b) and len(a) >= length and len(b) >= length and a[-length:] == b[-length:]

def _find_or_link_conversation(cursor, wa_number_digits):
    """Find the conversation for this WhatsApp number, or create one - linking it to a
    matching contact/lead by phone number when one exists. Returns a dict, never None."""
    cursor.execute("SELECT * FROM whatsapp_conversation WHERE wa_number = ?", (wa_number_digits,))
    convo = cursor.fetchone()
    if convo:
        return dict(convo)

    contact_id = None
    lead_id = None
    cursor.execute("SELECT id, phone FROM contacts WHERE phone IS NOT NULL AND phone != ''")
    for row in cursor.fetchall():
        if _phone_suffix_match(normalize_phone(row['phone']), wa_number_digits):
            contact_id = row['id']
            break
    if not contact_id:
        cursor.execute("SELECT id, phone FROM leads WHERE phone IS NOT NULL AND phone != ''")
        for row in cursor.fetchall():
            if _phone_suffix_match(normalize_phone(row['phone']), wa_number_digits):
                lead_id = row['id']
                break

    cursor.execute(
        """INSERT INTO whatsapp_conversation (contact_id, lead_id, wa_number, status, last_message_at)
           VALUES (?, ?, ?, 'open', CURRENT_TIMESTAMP)""",
        (contact_id, lead_id, wa_number_digits)
    )
    cursor.execute("SELECT * FROM whatsapp_conversation WHERE id = ?", (cursor.lastrowid,))
    return dict(cursor.fetchone())

def _send_whatsapp_api_message(to_digits, message=None, template_name=None, template_language="en_US", template_params=None):
    """Raw call to the Meta Cloud API. Returns (ok, wa_message_id_or_None, error_text_or_None).
    Caller is responsible for checking WHATSAPP_TOKEN/WHATSAPP_PHONE_ID are set first."""
    import requests
    wa_token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")

    if template_name:
        components = []
        if template_params:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in template_params]
            })
        body = {
            "messaging_product": "whatsapp",
            "to": to_digits,
            "type": "template",
            "template": {"name": template_name, "language": {"code": template_language}, "components": components}
        }
    else:
        body = {
            "messaging_product": "whatsapp",
            "to": to_digits,
            "type": "text",
            "text": {"body": message}
        }

    try:
        resp = requests.post(
            f"https://graph.facebook.com/v19.0/{phone_id}/messages",
            headers={"Authorization": f"Bearer {wa_token}"},
            json=body,
            timeout=10
        )
        if resp.status_code >= 400:
            return False, None, resp.text[:500]
        data = resp.json()
        wa_message_id = (data.get("messages") or [{}])[0].get("id")
        return True, wa_message_id, None
    except Exception as e:
        return False, None, str(e)[:500]

def _log_whatsapp_message(cursor, conversation_id, direction, status, message_type='text',
                           template_name=None, body=None, wa_message_id=None, error_message=None,
                           created_by=None, media_url=None, referral_json=None):
    cursor.execute(
        """INSERT INTO whatsapp_message
           (conversation_id, direction, wa_message_id, message_type, template_name, body,
            media_url, status, error_message, created_by, referral_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (conversation_id, direction, wa_message_id, message_type, template_name, body,
         media_url, status, error_message, created_by, referral_json)
    )
    cursor.execute("UPDATE whatsapp_conversation SET last_message_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (conversation_id,))
    return cursor.lastrowid

def require_api_key(x_api_key: str = Header(None)):
    """Auth for machine-to-machine endpoints (ad forms, Google Sheets, etc.) that can't carry
    a user's JWT. Looks up the key by its stored hash - the raw key is never persisted."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM api_keys WHERE key_hash = ? AND revoked_at IS NULL", (key_hash,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Invalid or revoked API key")
        cursor.execute("UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE id = ?", (row['id'],))
        conn.commit()
    return dict(row)

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
    if lead.marketing_opt_in is not None:
        updates.append("marketing_opt_in = ?")
        values.append(int(lead.marketing_opt_in))

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
        'ga_tracking_id': settings.ga_tracking_id,
        'default_report_period': settings.default_report_period,
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
    if contact.marketing_opt_in is not None:
        updates.append("marketing_opt_in = ?")
        values.append(int(contact.marketing_opt_in))

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

@app.post("/api/sms/send", response_model=SmsSendResponse)
async def send_sms(sms: SmsSendRequest, token: str = Query(None)):
    """Send a real SMS via Twilio, reusing the same credentials as click-to-call. Returns
    configured=False when TWILIO_* isn't set, so the frontend can fall back to an sms: link."""
    get_current_user(token)

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not (account_sid and auth_token and from_number):
        return SmsSendResponse(configured=False, message="Twilio SMS is not configured on this server.")

    try:
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioRestException

        client = Client(account_sid, auth_token)
        client.messages.create(to=sms.to, from_=from_number, body=sms.message)
        return SmsSendResponse(configured=True, message=f"SMS sent to {sms.to}.")
    except TwilioRestException as e:
        return SmsSendResponse(configured=True, message=f"SMS failed: {e.msg}")
    except Exception as e:
        return SmsSendResponse(configured=True, message=f"SMS failed: {str(e)}")

@app.post("/api/whatsapp/send", response_model=WhatsAppSendResponse)
async def send_whatsapp(payload: WhatsAppSendRequest, token: str = Query(None)):
    """Send a real WhatsApp message via the Meta Cloud API - freeform text (only deliverable
    inside Meta's 24h customer-service window) or an approved template (deliverable any time,
    required for anything marketing-like). Returns configured=False when WHATSAPP_TOKEN/
    WHATSAPP_PHONE_ID aren't set, so the frontend can fall back to a wa.me link. Every attempt
    is logged to whatsapp_message, win or lose, so Conversations/Reports have a real history."""
    current_user = get_current_user(token)

    wa_token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")

    if not (wa_token and phone_id):
        return WhatsAppSendResponse(configured=False, message="WhatsApp Business API is not configured on this server.")

    if not payload.message and not payload.template_name:
        raise HTTPException(status_code=400, detail="Provide either 'message' (freeform text) or 'template_name'.")

    to_digits = normalize_phone(payload.to)

    with get_db() as conn:
        cursor = conn.cursor()
        convo = _find_or_link_conversation(cursor, to_digits)
        if payload.contact_id and not convo['contact_id']:
            cursor.execute("UPDATE whatsapp_conversation SET contact_id = ? WHERE id = ?", (payload.contact_id, convo['id']))
        if payload.lead_id and not convo['lead_id']:
            cursor.execute("UPDATE whatsapp_conversation SET lead_id = ? WHERE id = ?", (payload.lead_id, convo['id']))
        conn.commit()

        if convo['opted_out_at']:
            return WhatsAppSendResponse(
                configured=True,
                message="This contact opted out of WhatsApp messages and cannot be messaged.",
                conversation_id=convo['id']
            )

        ok, wa_message_id, error = _send_whatsapp_api_message(
            to_digits, message=payload.message, template_name=payload.template_name,
            template_language=payload.template_language, template_params=payload.template_params
        )
        _log_whatsapp_message(
            cursor, convo['id'], direction='out', status='sent' if ok else 'failed',
            message_type='template' if payload.template_name else 'text',
            template_name=payload.template_name, body=payload.message,
            wa_message_id=wa_message_id, error_message=error, created_by=current_user['user_id']
        )
        conn.commit()

    if ok:
        return WhatsAppSendResponse(configured=True, message=f"WhatsApp message sent to {payload.to}.", conversation_id=convo['id'])
    return WhatsAppSendResponse(configured=True, message=f"WhatsApp send failed: {error}", conversation_id=convo['id'])

@app.get("/api/whatsapp/templates", response_model=WhatsAppTemplatesResponse)
async def get_whatsapp_templates(token: str = Query(None)):
    """List message templates approved (or pending/rejected) on the connected WhatsApp
    Business Account. Requires WHATSAPP_BUSINESS_ACCOUNT_ID (the WABA id, not the phone id)
    alongside WHATSAPP_TOKEN."""
    get_current_user(token)

    wa_token = os.getenv("WHATSAPP_TOKEN")
    waba_id = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")
    if not (wa_token and waba_id):
        return WhatsAppTemplatesResponse(configured=False, message="WHATSAPP_BUSINESS_ACCOUNT_ID is not configured on this server.", templates=[])

    try:
        import requests
        resp = requests.get(
            f"https://graph.facebook.com/v19.0/{waba_id}/message_templates",
            headers={"Authorization": f"Bearer {wa_token}"},
            params={"limit": 100},
            timeout=10
        )
        if resp.status_code >= 400:
            return WhatsAppTemplatesResponse(configured=True, message=f"Could not fetch templates: {resp.text[:200]}", templates=[])
        data = resp.json()
        templates = [
            {"name": t.get("name"), "status": t.get("status"), "category": t.get("category"), "language": t.get("language")}
            for t in data.get("data", [])
        ]
        return WhatsAppTemplatesResponse(configured=True, message=f"Found {len(templates)} template(s).", templates=templates)
    except Exception as e:
        return WhatsAppTemplatesResponse(configured=True, message=f"Failed to fetch templates: {str(e)}", templates=[])

@app.get("/api/whatsapp/conversations", response_model=list[WhatsAppConversationResponse])
async def get_whatsapp_conversations(token: str = Query(None), status: str = Query(None), mine_only: bool = Query(False)):
    """List WhatsApp conversations, newest activity first. mine_only restricts the list to
    conversations assigned to the calling user - the 'agent visibility scope' equivalent."""
    current_user = get_current_user(token)

    query = """
        SELECT c.*, ct.name as contact_name, ld.name as lead_name,
               (SELECT body FROM whatsapp_message m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) as last_message,
               (SELECT message_type FROM whatsapp_message m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) as last_message_type
        FROM whatsapp_conversation c
        LEFT JOIN contacts ct ON ct.id = c.contact_id
        LEFT JOIN leads ld ON ld.id = c.lead_id
        WHERE 1=1
    """
    params = []
    if status:
        query += " AND c.status = ?"
        params.append(status)
    if mine_only:
        query += " AND c.assigned_user_id = ?"
        params.append(current_user['user_id'])
    query += " ORDER BY c.last_message_at DESC"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conversations = [dict(row) for row in cursor.fetchall()]

    return conversations

@app.get("/api/whatsapp/conversations/{conversation_id}/messages", response_model=list[WhatsAppMessageResponse])
async def get_whatsapp_messages(conversation_id: int, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM whatsapp_message WHERE conversation_id = ? ORDER BY created_at ASC", (conversation_id,))
        messages = [dict(row) for row in cursor.fetchall()]
    return messages

@app.post("/api/whatsapp/conversations/{conversation_id}/reply", response_model=WhatsAppSendResponse)
async def reply_whatsapp_conversation(conversation_id: int, payload: WhatsAppReplyRequest, token: str = Query(None)):
    """Send a message inside an existing conversation, without needing the customer's raw
    phone number again - used by the agent inbox / conversation thread view."""
    current_user = get_current_user(token)

    wa_token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")
    if not (wa_token and phone_id):
        return WhatsAppSendResponse(configured=False, message="WhatsApp Business API is not configured on this server.")
    if not payload.message and not payload.template_name:
        raise HTTPException(status_code=400, detail="Provide either 'message' or 'template_name'.")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM whatsapp_conversation WHERE id = ?", (conversation_id,))
        convo = cursor.fetchone()
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation not found")
        convo = dict(convo)

        if convo['opted_out_at']:
            return WhatsAppSendResponse(configured=True, message="This contact opted out and cannot be messaged.", conversation_id=convo['id'])

        ok, wa_message_id, error = _send_whatsapp_api_message(
            convo['wa_number'], message=payload.message, template_name=payload.template_name,
            template_language=payload.template_language, template_params=payload.template_params
        )
        _log_whatsapp_message(
            cursor, convo['id'], direction='out', status='sent' if ok else 'failed',
            message_type='template' if payload.template_name else 'text',
            template_name=payload.template_name, body=payload.message,
            wa_message_id=wa_message_id, error_message=error, created_by=current_user['user_id']
        )
        conn.commit()

    if ok:
        return WhatsAppSendResponse(configured=True, message="Message sent.", conversation_id=conversation_id)
    return WhatsAppSendResponse(configured=True, message=f"Send failed: {error}", conversation_id=conversation_id)

@app.put("/api/whatsapp/conversations/{conversation_id}/assign")
async def assign_whatsapp_conversation(conversation_id: int, payload: ConversationAssign, token: str = Query(None)):
    """Hand a conversation to a specific team member, or unassign it (user_id=null) -
    the 'human handover' step after an automated flow decides a person should take over."""
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE whatsapp_conversation SET assigned_user_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (payload.user_id, conversation_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation assignment updated"}

@app.put("/api/whatsapp/conversations/{conversation_id}/status")
async def update_whatsapp_conversation_status(conversation_id: int, payload: ConversationStatusUpdate, token: str = Query(None)):
    get_current_user(token)
    if payload.status not in ('open', 'closed', 'handed_off'):
        raise HTTPException(status_code=400, detail="status must be one of: open, closed, handed_off")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE whatsapp_conversation SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (payload.status, conversation_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation status updated"}

@app.post("/api/whatsapp/conversations/{conversation_id}/opt-out")
async def opt_out_whatsapp_conversation(conversation_id: int, token: str = Query(None)):
    """Manually mark a conversation opted-out (e.g. a customer asked verbally, not over
    WhatsApp) - the same stop condition the webhook applies automatically for a 'STOP' reply."""
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE whatsapp_conversation SET opted_out_at = CURRENT_TIMESTAMP, opt_out_reason = 'Marked opted-out manually', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,)
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation marked opted-out"}

# ============= WHATSAPP WEBHOOKS (Meta Cloud API) =============

@app.get("/api/webhooks/whatsapp")
async def verify_whatsapp_webhook(request: Request):
    """Meta calls this once, with a GET, when you register the webhook URL in the Meta App
    dashboard - it must be answered with the raw hub.challenge value to complete setup."""
    params = request.query_params
    mode = params.get("hub.mode")
    verify_token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge", "")
    expected_token = os.getenv("WHATSAPP_VERIFY_TOKEN")

    if mode == "subscribe" and expected_token and verify_token == expected_token:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Webhook verification failed")

@app.post("/api/webhooks/whatsapp")
async def receive_whatsapp_webhook(request: Request):
    """Receives inbound messages and delivery/read status updates from Meta. This endpoint has
    no user login - Meta can't carry our JWT - so it's protected instead by verifying Meta's
    HMAC signature (WHATSAPP_APP_SECRET). Always returns 200 quickly: Meta retries aggressively
    (and can eventually disable the webhook) if it doesn't get a fast 2xx, so processing errors
    are logged server-side rather than surfaced as an HTTP error."""
    raw_body = await request.body()

    app_secret = os.getenv("WHATSAPP_APP_SECRET")
    if app_secret:
        signature = request.headers.get("x-hub-signature-256", "")
        expected = "sha256=" + hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw_body or b"{}")
        _process_whatsapp_webhook_payload(payload)
    except Exception as e:
        print(f"[WARN] WhatsApp webhook processing failed: {e}")

    return {"status": "received"}

_STATUS_RANK = {'sent': 1, 'delivered': 2, 'read': 3, 'failed': 4}
_OPT_OUT_KEYWORDS = {'stop', 'unsubscribe', 'opt out', 'optout'}

def _process_whatsapp_webhook_payload(payload):
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            statuses = value.get("statuses", [])

            if messages:
                with get_db() as conn:
                    cursor = conn.cursor()
                    for msg in messages:
                        wa_number = normalize_phone(msg.get("from", ""))
                        if not wa_number:
                            continue
                        msg_type = msg.get("type", "text")
                        body = None
                        media_url = None
                        if msg_type == "text":
                            body = msg.get("text", {}).get("body")
                        elif msg_type == "button":
                            body = msg.get("button", {}).get("text")
                        elif msg_type == "interactive":
                            interactive = msg.get("interactive", {})
                            reply = interactive.get("button_reply") or interactive.get("list_reply") or {}
                            body = reply.get("title")
                        elif msg_type in ("image", "document", "audio", "video", "sticker"):
                            # Meta gives a media id here, not a URL - a follow-up GET to
                            # /{media-id} (then downloading the returned url) is needed to
                            # actually fetch the file. Stored as-is so nothing is lost.
                            media_url = (msg.get(msg_type) or {}).get("id")

                        referral = msg.get("referral")  # present on the first message of a click-to-WhatsApp ad
                        referral_json = json.dumps(referral) if referral else None

                        convo = _find_or_link_conversation(cursor, wa_number)
                        if not convo['contact_id'] and not convo['lead_id']:
                            source = 'WhatsApp Ad' if referral else 'WhatsApp'
                            cursor.execute(
                                "INSERT INTO leads (name, phone, status, source) VALUES (?, ?, 'New', ?)",
                                (f"WhatsApp {wa_number[-4:]}", wa_number, source)
                            )
                            lead_id = cursor.lastrowid
                            cursor.execute("UPDATE whatsapp_conversation SET lead_id = ? WHERE id = ?", (lead_id, convo['id']))
                            convo['lead_id'] = lead_id

                        _log_whatsapp_message(
                            cursor, convo['id'], direction='in', status='received',
                            message_type=msg_type, body=body, media_url=media_url,
                            wa_message_id=msg.get("id"), referral_json=referral_json
                        )

                        if body and body.strip().lower() in _OPT_OUT_KEYWORDS:
                            cursor.execute(
                                "UPDATE whatsapp_conversation SET opted_out_at = CURRENT_TIMESTAMP, opt_out_reason = 'Customer replied STOP' WHERE id = ?",
                                (convo['id'],)
                            )
                    conn.commit()

            if statuses:
                with get_db() as conn:
                    cursor = conn.cursor()
                    for st in statuses:
                        wa_message_id = st.get("id")
                        new_status = st.get("status")
                        if not (wa_message_id and new_status):
                            continue
                        cursor.execute("SELECT id, status FROM whatsapp_message WHERE wa_message_id = ?", (wa_message_id,))
                        row = cursor.fetchone()
                        if not row:
                            continue
                        current_rank = _STATUS_RANK.get(row['status'], 0)
                        new_rank = _STATUS_RANK.get(new_status, 0)
                        if new_status == 'failed' or new_rank >= current_rank:
                            error_text = None
                            if new_status == 'failed':
                                errors = st.get("errors") or []
                                if errors:
                                    error_text = errors[0].get("title")
                            cursor.execute(
                                "UPDATE whatsapp_message SET status = ?, error_message = COALESCE(?, error_message) WHERE id = ?",
                                (new_status, error_text, row['id'])
                            )
                    conn.commit()

# ============= TAGS & GROUPS =============

@app.get("/api/tags", response_model=list[TagResponse])
async def get_tags(token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tags ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

@app.post("/api/tags", response_model=TagResponse)
async def create_tag(tag: TagCreate, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO tags (name, color) VALUES (?, ?)", (tag.name, tag.color))
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="A tag with this name already exists")
        cursor.execute("SELECT * FROM tags WHERE id = ?", (cursor.lastrowid,))
        return dict(cursor.fetchone())

@app.delete("/api/tags/{tag_id}")
async def delete_tag(tag_id: int, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entity_tags WHERE tag_id = ?", (tag_id,))
        cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        conn.commit()
    return {"message": "Tag deleted"}

@app.post("/api/tags/assign")
async def assign_tag(payload: EntityTagRequest, token: str = Query(None)):
    get_current_user(token)
    if payload.entity_type not in ('contact', 'lead'):
        raise HTTPException(status_code=400, detail="entity_type must be 'contact' or 'lead'")
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO entity_tags (entity_type, entity_id, tag_id) VALUES (?, ?, ?)",
                (payload.entity_type, payload.entity_id, payload.tag_id)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # already tagged - not an error
    return {"message": "Tag assigned"}

@app.post("/api/tags/unassign")
async def unassign_tag(payload: EntityTagRequest, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM entity_tags WHERE entity_type = ? AND entity_id = ? AND tag_id = ?",
            (payload.entity_type, payload.entity_id, payload.tag_id)
        )
        conn.commit()
    return {"message": "Tag unassigned"}

@app.get("/api/tags/for/{entity_type}/{entity_id}", response_model=list[TagResponse])
async def get_tags_for_entity(entity_type: str, entity_id: int, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT t.* FROM tags t JOIN entity_tags et ON et.tag_id = t.id
               WHERE et.entity_type = ? AND et.entity_id = ? ORDER BY t.name""",
            (entity_type, entity_id)
        )
        return [dict(row) for row in cursor.fetchall()]

@app.get("/api/groups", response_model=list[GroupResponse])
async def get_groups(token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM groups ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

@app.post("/api/groups", response_model=GroupResponse)
async def create_group(group: GroupCreate, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO groups (name, description) VALUES (?, ?)", (group.name, group.description))
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="A group with this name already exists")
        cursor.execute("SELECT * FROM groups WHERE id = ?", (cursor.lastrowid,))
        return dict(cursor.fetchone())

@app.delete("/api/groups/{group_id}")
async def delete_group(group_id: int, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entity_groups WHERE group_id = ?", (group_id,))
        cursor.execute("DELETE FROM groups WHERE id = ?", (group_id,))
        conn.commit()
    return {"message": "Group deleted"}

@app.post("/api/groups/assign")
async def assign_group(payload: EntityGroupRequest, token: str = Query(None)):
    get_current_user(token)
    if payload.entity_type not in ('contact', 'lead'):
        raise HTTPException(status_code=400, detail="entity_type must be 'contact' or 'lead'")
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO entity_groups (entity_type, entity_id, group_id) VALUES (?, ?, ?)",
                (payload.entity_type, payload.entity_id, payload.group_id)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass
    return {"message": "Added to group"}

@app.post("/api/groups/unassign")
async def unassign_group(payload: EntityGroupRequest, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM entity_groups WHERE entity_type = ? AND entity_id = ? AND group_id = ?",
            (payload.entity_type, payload.entity_id, payload.group_id)
        )
        conn.commit()
    return {"message": "Removed from group"}

def _group_member_conversations(cursor, group_id):
    """Every open WhatsApp conversation belonging to a contact/lead in this group - the
    audience a broadcast campaign or automation targets."""
    cursor.execute(
        """SELECT wc.* FROM whatsapp_conversation wc
           JOIN entity_groups eg
             ON (eg.entity_type = 'contact' AND eg.entity_id = wc.contact_id)
             OR (eg.entity_type = 'lead' AND eg.entity_id = wc.lead_id)
           WHERE eg.group_id = ? AND wc.opted_out_at IS NULL""",
        (group_id,)
    )
    return [dict(row) for row in cursor.fetchall()]

# ============= CUSTOM FIELDS =============

@app.get("/api/custom-fields", response_model=list[CustomFieldResponse])
async def get_custom_fields(token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM custom_fields ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

@app.post("/api/custom-fields", response_model=CustomFieldResponse)
async def create_custom_field(field: CustomFieldCreate, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO custom_fields (name, field_type) VALUES (?, ?)", (field.name, field.field_type))
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="A custom field with this name already exists")
        cursor.execute("SELECT * FROM custom_fields WHERE id = ?", (cursor.lastrowid,))
        return dict(cursor.fetchone())

@app.delete("/api/custom-fields/{field_id}")
async def delete_custom_field(field_id: int, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM custom_field_values WHERE custom_field_id = ?", (field_id,))
        cursor.execute("DELETE FROM custom_fields WHERE id = ?", (field_id,))
        conn.commit()
    return {"message": "Custom field deleted"}

@app.put("/api/custom-fields/value")
async def set_custom_field_value(payload: CustomFieldValueSet, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO custom_field_values (custom_field_id, entity_type, entity_id, value)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(custom_field_id, entity_type, entity_id) DO UPDATE SET value = excluded.value""",
            (payload.custom_field_id, payload.entity_type, payload.entity_id, payload.value)
        )
        conn.commit()
    return {"message": "Custom field value saved"}

@app.get("/api/custom-fields/for/{entity_type}/{entity_id}")
async def get_custom_field_values(entity_type: str, entity_id: int, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT cf.id, cf.name, cf.field_type, cfv.value
               FROM custom_fields cf
               LEFT JOIN custom_field_values cfv
                 ON cfv.custom_field_id = cf.id AND cfv.entity_type = ? AND cfv.entity_id = ?
               ORDER BY cf.name""",
            (entity_type, entity_id)
        )
        return [dict(row) for row in cursor.fetchall()]

# ============= QUICK REPLIES =============

@app.get("/api/quick-replies", response_model=list[QuickReplyResponse])
async def get_quick_replies(token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quick_replies ORDER BY shortcut")
        return [dict(row) for row in cursor.fetchall()]

@app.post("/api/quick-replies", response_model=QuickReplyResponse)
async def create_quick_reply(reply: QuickReplyCreate, token: str = Query(None)):
    current_user = get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO quick_replies (shortcut, message, created_by) VALUES (?, ?, ?)",
                (reply.shortcut, reply.message, current_user['user_id'])
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="A quick reply with this shortcut already exists")
        cursor.execute("SELECT * FROM quick_replies WHERE id = ?", (cursor.lastrowid,))
        return dict(cursor.fetchone())

@app.put("/api/quick-replies/{reply_id}", response_model=QuickReplyResponse)
async def update_quick_reply(reply_id: int, reply: QuickReplyUpdate, token: str = Query(None)):
    get_current_user(token)
    updates, values = [], []
    if reply.shortcut is not None:
        updates.append("shortcut = ?"); values.append(reply.shortcut)
    if reply.message is not None:
        updates.append("message = ?"); values.append(reply.message)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    values.append(reply_id)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE quick_replies SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
        cursor.execute("SELECT * FROM quick_replies WHERE id = ?", (reply_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Quick reply not found")
        return dict(row)

@app.delete("/api/quick-replies/{reply_id}")
async def delete_quick_reply(reply_id: int, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quick_replies WHERE id = ?", (reply_id,))
        conn.commit()
    return {"message": "Quick reply deleted"}

# ============= AUTOMATIONS (drip sequences / simple flows) =============

def _automation_row_to_response(cursor, row):
    a = dict(row)
    cursor.execute("SELECT * FROM automation_steps WHERE automation_id = ? ORDER BY step_order", (a['id'],))
    a['steps'] = [dict(s) for s in cursor.fetchall()]
    return a

@app.get("/api/automations", response_model=list[AutomationResponse])
async def get_automations(token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM automations ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [_automation_row_to_response(cursor, r) for r in rows]

@app.post("/api/automations", response_model=AutomationResponse)
async def create_automation(automation: AutomationCreate, token: str = Query(None)):
    current_user = get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO automations (name, trigger_type, group_id, created_by) VALUES (?, ?, ?, ?)",
            (automation.name, automation.trigger_type, automation.group_id, current_user['user_id'])
        )
        automation_id = cursor.lastrowid
        for i, step in enumerate(automation.steps):
            cursor.execute(
                """INSERT INTO automation_steps (automation_id, step_order, wait_minutes, message_type, template_name, body)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (automation_id, i, step.wait_minutes, step.message_type, step.template_name, step.body)
            )
        conn.commit()
        cursor.execute("SELECT * FROM automations WHERE id = ?", (automation_id,))
        return _automation_row_to_response(cursor, cursor.fetchone())

@app.put("/api/automations/{automation_id}", response_model=AutomationResponse)
async def update_automation(automation_id: int, automation: AutomationUpdate, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM automations WHERE id = ?", (automation_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Automation not found")

        updates, values = [], []
        if automation.name is not None:
            updates.append("name = ?"); values.append(automation.name)
        if automation.status is not None:
            if automation.status not in ('active', 'paused'):
                raise HTTPException(status_code=400, detail="status must be 'active' or 'paused'")
            updates.append("status = ?"); values.append(automation.status)
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(automation_id)
            cursor.execute(f"UPDATE automations SET {', '.join(updates)} WHERE id = ?", values)

        if automation.steps is not None:
            cursor.execute("DELETE FROM automation_steps WHERE automation_id = ?", (automation_id,))
            for i, step in enumerate(automation.steps):
                cursor.execute(
                    """INSERT INTO automation_steps (automation_id, step_order, wait_minutes, message_type, template_name, body)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (automation_id, i, step.wait_minutes, step.message_type, step.template_name, step.body)
                )

        conn.commit()
        cursor.execute("SELECT * FROM automations WHERE id = ?", (automation_id,))
        return _automation_row_to_response(cursor, cursor.fetchone())

@app.delete("/api/automations/{automation_id}")
async def delete_automation(automation_id: int, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM automation_enrollments WHERE automation_id = ?", (automation_id,))
        cursor.execute("DELETE FROM automation_steps WHERE automation_id = ?", (automation_id,))
        cursor.execute("DELETE FROM automations WHERE id = ?", (automation_id,))
        conn.commit()
    return {"message": "Automation deleted"}

@app.post("/api/automations/{automation_id}/enroll")
async def enroll_conversation(automation_id: int, payload: AutomationEnrollRequest, token: str = Query(None)):
    """Start a single conversation on this automation now (its first step fires as soon as
    the scheduler's next tick runs, honoring that step's wait_minutes)."""
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT wait_minutes FROM automation_steps WHERE automation_id = ? ORDER BY step_order LIMIT 1", (automation_id,))
        first_step = cursor.fetchone()
        if not first_step:
            raise HTTPException(status_code=400, detail="This automation has no steps yet")
        next_run_at = (datetime.utcnow() + timedelta(minutes=first_step['wait_minutes'])).isoformat()
        try:
            cursor.execute(
                """INSERT INTO automation_enrollments (automation_id, conversation_id, current_step, status, next_run_at)
                   VALUES (?, ?, 0, 'active', ?)""",
                (automation_id, payload.conversation_id, next_run_at)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="This conversation is already enrolled in this automation")
    return {"message": "Enrolled"}

@app.post("/api/automations/{automation_id}/enroll-group/{group_id}")
async def enroll_group(automation_id: int, group_id: int, token: str = Query(None)):
    """Enroll every opted-in conversation in a group at once - the broadcast/drip-campaign
    entry point (e.g. 'start the Diwali sequence for the SIP Clients group')."""
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT wait_minutes FROM automation_steps WHERE automation_id = ? ORDER BY step_order LIMIT 1", (automation_id,))
        first_step = cursor.fetchone()
        if not first_step:
            raise HTTPException(status_code=400, detail="This automation has no steps yet")
        next_run_at = (datetime.utcnow() + timedelta(minutes=first_step['wait_minutes'])).isoformat()

        conversations = _group_member_conversations(cursor, group_id)
        enrolled = 0
        for convo in conversations:
            try:
                cursor.execute(
                    """INSERT INTO automation_enrollments (automation_id, conversation_id, current_step, status, next_run_at)
                       VALUES (?, ?, 0, 'active', ?)""",
                    (automation_id, convo['id'], next_run_at)
                )
                enrolled += 1
            except sqlite3.IntegrityError:
                continue  # already enrolled
        conn.commit()
    return {"message": f"Enrolled {enrolled} conversation(s)"}

@app.post("/api/automations/enrollments/{enrollment_id}/stop")
async def stop_enrollment(enrollment_id: int, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE automation_enrollments SET status = 'stopped', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (enrollment_id,))
        conn.commit()
    return {"message": "Enrollment stopped"}

async def _run_automation_scheduler():
    """The drip-sequence engine: once a minute, find every active enrollment whose next step
    is due, send it, and schedule the one after (or mark the enrollment completed). A reply
    from the customer or a STOP is not auto-detected here as a pause signal - conversation
    status/opt-out already blocks the send itself, which is the safety net that matters."""
    while True:
        try:
            _tick_automation_scheduler()
        except Exception as e:
            print(f"[WARN] Automation scheduler tick failed: {e}")
        await asyncio.sleep(60)

def _tick_automation_scheduler():
    now_iso = datetime.utcnow().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM automation_enrollments WHERE status = 'active' AND next_run_at <= ?",
            (now_iso,)
        )
        due = [dict(row) for row in cursor.fetchall()]

        for enrollment in due:
            cursor.execute("SELECT * FROM whatsapp_conversation WHERE id = ?", (enrollment['conversation_id'],))
            convo = cursor.fetchone()
            cursor.execute(
                "SELECT * FROM automation_steps WHERE automation_id = ? AND step_order = ?",
                (enrollment['automation_id'], enrollment['current_step'])
            )
            step = cursor.fetchone()

            if not convo or not step:
                cursor.execute("UPDATE automation_enrollments SET status = 'completed', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (enrollment['id'],))
                continue

            convo = dict(convo)
            step = dict(step)

            if convo['opted_out_at']:
                cursor.execute("UPDATE automation_enrollments SET status = 'stopped', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (enrollment['id'],))
                continue

            wa_token = os.getenv("WHATSAPP_TOKEN")
            phone_id = os.getenv("WHATSAPP_PHONE_ID")
            if wa_token and phone_id:
                ok, wa_message_id, error = _send_whatsapp_api_message(
                    convo['wa_number'],
                    message=step['body'] if step['message_type'] == 'text' else None,
                    template_name=step['template_name'] if step['message_type'] == 'template' else None
                )
                _log_whatsapp_message(
                    cursor, convo['id'], direction='out', status='sent' if ok else 'failed',
                    message_type=step['message_type'], template_name=step['template_name'],
                    body=step['body']
                )
            # else: WhatsApp isn't configured yet - skip the send but still advance the
            # enrollment, so a step doesn't retry forever once credentials are added later
            # with a very different current time.

            cursor.execute(
                "SELECT * FROM automation_steps WHERE automation_id = ? AND step_order = ?",
                (enrollment['automation_id'], enrollment['current_step'] + 1)
            )
            next_step = cursor.fetchone()
            if next_step:
                next_step = dict(next_step)
                next_run_at = (datetime.utcnow() + timedelta(minutes=next_step['wait_minutes'])).isoformat()
                cursor.execute(
                    "UPDATE automation_enrollments SET current_step = ?, next_run_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (enrollment['current_step'] + 1, next_run_at, enrollment['id'])
                )
            else:
                cursor.execute(
                    "UPDATE automation_enrollments SET status = 'completed', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (enrollment['id'],)
                )

        conn.commit()

# ============= DEVELOPER API KEYS =============

@app.get("/api/api-keys", response_model=list[ApiKeyResponse])
async def get_api_keys(token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM api_keys ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

@app.post("/api/api-keys", response_model=ApiKeyCreateResponse)
async def create_api_key(payload: ApiKeyCreate, token: str = Query(None)):
    """Creates a new developer API key for an external system (a click-to-WhatsApp ad tool, a
    Google Sheet, a landing-page form) to call POST /api/public/leads. The raw key is returned
    exactly once, here - only its hash is stored, so save it now, it can't be shown again."""
    current_user = get_current_user(token)
    raw_key = f"ai_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:10]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO api_keys (name, key_prefix, key_hash, created_by) VALUES (?, ?, ?, ?)",
            (payload.name, key_prefix, key_hash, current_user['user_id'])
        )
        conn.commit()
        key_id = cursor.lastrowid

    return ApiKeyCreateResponse(id=key_id, name=payload.name, api_key=raw_key)

@app.delete("/api/api-keys/{key_id}")
async def revoke_api_key(key_id: int, token: str = Query(None)):
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE api_keys SET revoked_at = CURRENT_TIMESTAMP WHERE id = ?", (key_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key revoked"}

@app.post("/api/public/leads")
async def create_lead_via_api_key(lead: LeadCreate, x_api_key: str = Header(None)):
    """Public (no user login) endpoint for external systems - a WhatsApp click-to-ad landing
    tool, a Google Sheet, a web form - to create a lead, authenticated with an API key instead
    of a JWT. Source defaults to whatever the caller sends (e.g. 'Facebook Ad', 'Website Form')."""
    require_api_key(x_api_key)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO leads (name, company, email, phone, product, source, status)
               VALUES (?, ?, ?, ?, ?, ?, 'New')""",
            (lead.name, lead.company, lead.email, lead.phone, lead.product, lead.source or 'API')
        )
        conn.commit()
        cursor.execute("SELECT * FROM leads WHERE id = ?", (cursor.lastrowid,))
        return dict(cursor.fetchone())

@app.post("/api/email/send", response_model=EmailSendResponse)
async def send_email_real(payload: EmailSendRequest, token: str = Query(None)):
    """Send a real email via SMTP. Returns configured=False when SMTP_* isn't set, so the
    frontend can fall back to a mailto: link."""
    get_current_user(token)

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM") or smtp_user

    if not (smtp_host and smtp_port and smtp_user and smtp_password):
        return EmailSendResponse(configured=False, message="Email service (SMTP) is not configured on this server.")

    try:
        msg = MIMEText(payload.body)
        msg["Subject"] = payload.subject
        msg["From"] = smtp_from
        msg["To"] = payload.to

        with smtplib.SMTP(smtp_host, int(smtp_port), timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, [payload.to], msg.as_string())

        return EmailSendResponse(configured=True, message=f"Email sent to {payload.to}.")
    except Exception as e:
        return EmailSendResponse(configured=True, message=f"Email failed: {str(e)}")

@app.post("/api/marketing/mailchimp/sync", response_model=MailchimpSyncResponse)
async def sync_mailchimp(token: str = Query(None)):
    """Push all contacts into a Mailchimp audience. Returns configured=False when
    MAILCHIMP_API_KEY/MAILCHIMP_AUDIENCE_ID aren't set."""
    get_current_user(token)

    api_key = os.getenv("MAILCHIMP_API_KEY")
    audience_id = os.getenv("MAILCHIMP_AUDIENCE_ID")

    if not (api_key and audience_id) or "-" not in (api_key or ""):
        return MailchimpSyncResponse(configured=False, message="Mailchimp is not configured on this server.")

    server_prefix = api_key.rsplit("-", 1)[-1]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, email FROM contacts WHERE email IS NOT NULL AND email != ''")
        contacts = [dict(row) for row in cursor.fetchall()]

    if not contacts:
        return MailchimpSyncResponse(configured=True, message="No contacts with an email address to sync.", synced_count=0)

    try:
        import requests
        synced = 0
        for c in contacts:
            subscriber_hash = hashlib.md5(c['email'].strip().lower().encode()).hexdigest()
            resp = requests.put(
                f"https://{server_prefix}.api.mailchimp.com/3.0/lists/{audience_id}/members/{subscriber_hash}",
                auth=("anystring", api_key),
                json={
                    "email_address": c['email'],
                    "status_if_new": "subscribed",
                    "merge_fields": {"FNAME": c['name'] or ""}
                },
                timeout=10
            )
            if resp.status_code < 400:
                synced += 1
        return MailchimpSyncResponse(configured=True, message=f"Synced {synced} of {len(contacts)} contact(s) to Mailchimp.", synced_count=synced)
    except Exception as e:
        return MailchimpSyncResponse(configured=True, message=f"Mailchimp sync failed: {str(e)}")

# ============= TEAM MANAGEMENT ENDPOINTS =============

TEAM_ROLE_ORDER = {"admin": 0, "team_lead": 1, "location_head": 2, "employee": 3}

@app.get("/api/team", response_model=list[TeamMemberResponse])
async def get_team(token: str = Query(None)):
    """List all team members, grouped by role hierarchy then name"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM team_members")
        members = [dict(row) for row in cursor.fetchall()]

    members.sort(key=lambda m: (TEAM_ROLE_ORDER.get(m['role'], 99), m['name']))
    return members

@app.post("/api/team", response_model=TeamMemberResponse)
async def create_team_member(member: TeamMemberCreate, token: str = Query(None)):
    """Add a new team member"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO team_members (name, role, email, phone) VALUES (?, ?, ?, ?)",
            (member.name, member.role, member.email, member.phone)
        )
        conn.commit()
        cursor.execute("SELECT * FROM team_members WHERE id = ?", (cursor.lastrowid,))
        return dict(cursor.fetchone())

@app.put("/api/team/{member_id}", response_model=TeamMemberResponse)
async def update_team_member(member_id: int, member: TeamMemberUpdate, token: str = Query(None)):
    """Update a team member's details"""
    get_current_user(token)

    field_map = {
        'name': member.name, 'role': member.role, 'email': member.email, 'phone': member.phone
    }
    updates = [(k, v) for k, v in field_map.items() if v is not None]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM team_members WHERE id = ?", (member_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Team member not found")

        if updates:
            set_clause = ', '.join(f"{k} = ?" for k, _ in updates)
            values = [v for _, v in updates] + [member_id]
            cursor.execute(f"UPDATE team_members SET {set_clause} WHERE id = ?", values)
            conn.commit()

        cursor.execute("SELECT * FROM team_members WHERE id = ?", (member_id,))
        return dict(cursor.fetchone())

@app.delete("/api/team/{member_id}")
async def delete_team_member(member_id: int, token: str = Query(None)):
    """Remove a team member"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM team_members WHERE id = ?", (member_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Team member not found")

    return {"message": "Team member removed"}

@app.get("/api/analytics/team", response_model=list[TeamProductivityRow])
async def get_team_analytics(token: str = Query(None)):
    """Real per-team-member productivity, computed from deals.owner_id / calls.created_by /
    leads.created_by. Only team members linked to a real login account (team_members.user_id)
    have any activity to report - everyone else genuinely has none yet (no assignment system
    exists beyond the single owning login), so their fields come back as None rather than a
    fabricated 0, and the frontend renders that as "no data yet" instead of implying poor
    performance."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM team_members")
        members = [dict(row) for row in cursor.fetchall()]

        rows = []
        for m in members:
            uid = m.get('user_id')
            if uid is None:
                rows.append(TeamProductivityRow(id=m['id'], name=m['name'], role=m['role']))
                continue

            cursor.execute("SELECT COUNT(*) as count FROM calls WHERE created_by = ?", (uid,))
            calls = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM deals WHERE owner_id = ? AND stage = 'closed'", (uid,))
            deals_closed = cursor.fetchone()['count']

            cursor.execute("SELECT COALESCE(SUM(deal_value), 0) as total FROM deals WHERE owner_id = ? AND stage = 'closed'", (uid,))
            revenue = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as count FROM leads WHERE created_by = ?", (uid,))
            total_leads = cursor.fetchone()['count']
            conversion_rate = round((deals_closed / total_leads * 100), 1) if total_leads > 0 else 0.0

            rows.append(TeamProductivityRow(
                id=m['id'], name=m['name'], role=m['role'],
                calls=calls, deals_closed=deals_closed, revenue=revenue, conversion_rate=conversion_rate
            ))

    rows.sort(key=lambda r: (TEAM_ROLE_ORDER.get(r.role, 99), r.name))
    return rows

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
