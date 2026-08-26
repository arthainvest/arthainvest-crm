from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import sqlite3
from typing import List, Optional
import os
import json
import uuid
import smtplib
import hashlib
from datetime import datetime
from email.mime.text import MIMEText
from dotenv import load_dotenv

from database_sqlite import get_db, init_db
from schemas import (
    UserLogin, UserCreate, UserResponse, Token,
    LeadCreate, LeadUpdate, LeadAssign, LeadResponse,
    DealCreate, DealMove, DealAssign, DealCompanyAssign, DealContactAssign, DealProcessStatusUpdate, DealResponse,
    CampaignCreate, CampaignUpdate, CampaignResponse,
    CampaignRecipientAdd, CampaignRecipientResponse, CampaignSendResult,
    IntegrationToggle, IntegrationResponse,
    SettingsUpdate, SettingsResponse,
    ContactCreate, ContactUpdate, ContactAssign, ContactCompanyAssign, ContactResponse, RenewalContact,
    ContactNoteCreate, ContactNoteUpdate, ContactNoteResponse,
    LeadNoteCreate, LeadNoteUpdate, LeadNoteResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    MeetingCreate, MeetingUpdate, MeetingResponse,
    CallCreate, CallAssign, CallContactAssign, CallResponse, EmployeeCallStats,
    CommunicationLogResponse,
    DialRequest, DialResponse, AISummaryResponse,
    DetectDateRequest, DetectDateResponse,
    GenerateContentRequest, GenerateContentResponse,
    ChatMessage, ChatRequest, ChatResponse,
    WhatsAppSendRequest, WhatsAppSendResponse,
    EmailSendRequest, EmailSendResponse,
    SmsSendRequest, SmsSendResponse,
    MailchimpSyncResponse,
    LinkedInConnectResponse, LinkedInPostRequest, LinkedInPostResponse,
    TeamMemberCreate, TeamMemberUpdate, TeamMemberResponse, TeamProductivityRow,
    VoiceCallTriggerRequest, VoiceCallTriggerResponse,
    DialerAssignRequest, DialerQueueItemResponse, DialerStatusUpdate,
    ActivityItem, CompanyCreate, CompanyUpdate, CompanyResponse,
    QuotationCreate, QuotationUpdate, QuotationContactAssign, QuotationCompanyAssign, QuotationResponse
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

def require_admin(token: str = None):
    """Same as get_current_user, but additionally requires the user's account role (looked up
    fresh from the users table, not baked into the JWT, so a role change takes effect on the
    very next request without needing to log back in) to be 'admin'. Used to gate
    creating/editing/removing team roster entries - currently anyone with a valid login could
    add or delete other people's records, which is the wrong default for something that
    affects the whole team, not just the person doing it."""
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (current_user['user_id'],))
        row = cursor.fetchone()

    if not row or row['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    return current_user

def fetch_deal_with_member_name(cursor, deal_id):
    """Read one deal back out joined against team_members, so the frontend gets the assigned
    employee's name alongside the raw id - avoids a second round-trip per row on the Pipeline
    table just to resolve id -> name. Also counts linked Quotations (same subquery pattern as
    companies.contact_count) and resolves the linked Company's name and Contact's name, if any."""
    cursor.execute(
        """
        SELECT deals.*, team_members.name as assigned_team_member_name,
               companies.name as company_name, contacts.name as contact_name,
               (SELECT COUNT(*) FROM quotations WHERE quotations.deal_id = deals.id) as quotation_count
        FROM deals
        LEFT JOIN team_members ON team_members.id = deals.assigned_team_member_id
        LEFT JOIN companies ON companies.id = deals.company_id
        LEFT JOIN contacts ON contacts.id = deals.contact_id
        WHERE deals.id = ?
        """,
        (deal_id,)
    )
    return dict(cursor.fetchone())

def fetch_lead_with_member_name(cursor, lead_id):
    """Same join-by-id pattern as fetch_deal_with_member_name, for leads - so admins/team
    leads can see which employee a lead is assigned to without a second round-trip. Also
    resolves converted_contact_id's name, if this lead has been converted to a Contact."""
    cursor.execute(
        """
        SELECT leads.*, team_members.name as assigned_team_member_name,
               converted_contact.name as converted_contact_name
        FROM leads
        LEFT JOIN team_members ON team_members.id = leads.assigned_team_member_id
        LEFT JOIN contacts AS converted_contact ON converted_contact.id = leads.converted_contact_id
        WHERE leads.id = ?
        """,
        (lead_id,)
    )
    return dict(cursor.fetchone())

def fetch_contact_with_member_name(cursor, contact_id):
    """Same join-by-id pattern as fetch_deal_with_member_name, for contacts - so admins/team
    leads can see which employee owns each contact in the client book, and which Companies
    record (if any) they're linked to. Also resolves converted_from_lead_id's name, the
    reverse of leads.converted_contact_id, if this contact originated from a converted lead."""
    cursor.execute(
        """
        SELECT contacts.*, team_members.name as assigned_team_member_name,
               companies.name as company_name,
               converted_from_lead.name as converted_from_lead_name
        FROM contacts
        LEFT JOIN team_members ON team_members.id = contacts.assigned_team_member_id
        LEFT JOIN companies ON companies.id = contacts.company_id
        LEFT JOIN leads AS converted_from_lead ON converted_from_lead.id = contacts.converted_from_lead_id
        WHERE contacts.id = ?
        """,
        (contact_id,)
    )
    return dict(cursor.fetchone())

def fetch_call_with_member_name(cursor, call_id):
    """Same join-by-id pattern as fetch_deal_with_member_name, for calls - so admins/team
    leads can see who made or handled each logged call, and which Lead/Contact record (if
    any) it was about."""
    cursor.execute(
        """
        SELECT calls.*, team_members.name as team_member_name,
               leads.name as lead_name, contacts.name as contact_name
        FROM calls
        LEFT JOIN team_members ON team_members.id = calls.team_member_id
        LEFT JOIN leads ON leads.id = calls.lead_id
        LEFT JOIN contacts ON contacts.id = calls.contact_id
        WHERE calls.id = ?
        """,
        (call_id,)
    )
    return dict(cursor.fetchone())

def fetch_task_with_member_name(cursor, task_id):
    """Same join-by-id pattern as fetch_deal_with_member_name, for tasks - also resolves the
    linked lead/contact name, if any, same as fetch_meeting_with_names."""
    cursor.execute(
        """
        SELECT tasks.*, team_members.name as assigned_team_member_name,
               leads.name as lead_name, contacts.name as contact_name
        FROM tasks
        LEFT JOIN team_members ON team_members.id = tasks.assigned_team_member_id
        LEFT JOIN leads ON leads.id = tasks.lead_id
        LEFT JOIN contacts ON contacts.id = tasks.contact_id
        WHERE tasks.id = ?
        """,
        (task_id,)
    )
    return dict(cursor.fetchone())

def fetch_meeting_with_names(cursor, meeting_id):
    """Same join-by-id pattern as fetch_deal_with_member_name, for meetings - also resolves
    the linked lead/contact name, if any, so the Today page doesn't need a second round-trip
    per meeting just to show who it's with."""
    cursor.execute(
        """
        SELECT meetings.*, team_members.name as assigned_team_member_name,
               leads.name as lead_name, contacts.name as contact_name
        FROM meetings
        LEFT JOIN team_members ON team_members.id = meetings.assigned_team_member_id
        LEFT JOIN leads ON leads.id = meetings.lead_id
        LEFT JOIN contacts ON contacts.id = meetings.contact_id
        WHERE meetings.id = ?
        """,
        (meeting_id,)
    )
    return dict(cursor.fetchone())

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
async def get_leads(
    token: str = Query(None), status: str = Query(None),
    source: str = Query(None), assigned_team_member_id: int = Query(None)
):
    """Get all leads, optionally filtered by status/source/assigned team member - the latter
    two power the Reports page's drill-downs (Lead Source ROI -> actual leads, Team
    Productivity -> a member's actual leads) without needing dedicated reverse-lookup routes."""
    get_current_user(token)

    base_query = """
        SELECT leads.*, team_members.name as assigned_team_member_name,
               converted_contact.name as converted_contact_name
        FROM leads
        LEFT JOIN team_members ON team_members.id = leads.assigned_team_member_id
        LEFT JOIN contacts AS converted_contact ON converted_contact.id = leads.converted_contact_id
        WHERE 1=1
    """
    conditions = []
    params = []
    if status:
        conditions.append("leads.status = ?")
        params.append(status)
    if source:
        # Mirrors the COALESCE(NULLIF(TRIM(source), ''), 'Not Specified') grouping used by
        # /api/analytics/lead-sources, so "Not Specified" here matches the same blank/null
        # leads that report groups under that label instead of matching nothing.
        if source == "Not Specified":
            conditions.append("(leads.source IS NULL OR TRIM(leads.source) = '')")
        else:
            conditions.append("leads.source = ?")
            params.append(source)
    if assigned_team_member_id is not None:
        conditions.append("leads.assigned_team_member_id = ?")
        params.append(assigned_team_member_id)

    with get_db() as conn:
        cursor = conn.cursor()
        query = base_query + (" AND " + " AND ".join(conditions) if conditions else "") + " ORDER BY leads.created_at DESC"
        cursor.execute(query, params)
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

        new_lead = fetch_lead_with_member_name(cursor, lead_id)

    return new_lead

@app.get("/api/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, token: str = Query(None)):
    """Get single lead"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM leads WHERE id = ?", (lead_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Lead not found")
        lead = fetch_lead_with_member_name(cursor, lead_id)

    return lead

@app.put("/api/leads/{lead_id}/assign", response_model=LeadResponse)
async def assign_lead(lead_id: int, assignment: LeadAssign, token: str = Query(None)):
    """Assign (or unassign, if team_member_id is null) a lead to a team member, so admins and
    the team lead can see who owns each lead."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM leads WHERE id = ?", (lead_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Lead not found")

        if assignment.team_member_id is not None:
            cursor.execute("SELECT 1 FROM team_members WHERE id = ?", (assignment.team_member_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Team member not found")

        cursor.execute(
            "UPDATE leads SET assigned_team_member_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (assignment.team_member_id, lead_id)
        )
        conn.commit()

        return fetch_lead_with_member_name(cursor, lead_id)

@app.post("/api/leads/{lead_id}/convert", response_model=ContactResponse)
async def convert_lead_to_contact(lead_id: int, token: str = Query(None)):
    """Turns a Lead into a real Contact once they've become an actual client - Leads and
    Contacts are otherwise two permanently separate universes with no path between them, so a
    won prospect's history had nowhere to go. Creates a new Contact carrying over
    name/company/email/phone/assigned_team_member_id, backfills contact_id onto every
    task/meeting/call/communication_log/campaign_recipients row already linked to this lead
    (so the new Contact's Activity Timeline shows the full prior history instead of starting
    blank - lead_id is left untouched, so the original lead's own timeline still shows the
    same rows too), and marks the lead as converted rather than deleting it - nothing is ever
    destroyed. Deliberately scoped to the Activity Timeline tables only: lead_notes (call
    transcripts) stay with the original lead rather than being copied into contact_notes,
    since that's a heavier duplication decision than backfilling a nullable FK."""
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        lead = cursor.fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        lead = dict(lead)

        if lead.get('converted_contact_id'):
            raise HTTPException(status_code=400, detail="This lead has already been converted to a contact")

        cursor.execute(
            """
            INSERT INTO contacts (name, company, email, phone, status, created_by, assigned_team_member_id, converted_from_lead_id)
            VALUES (?, ?, ?, ?, 'Active', ?, ?, ?)
            """,
            (lead['name'], lead.get('company'), lead.get('email'), lead.get('phone'),
             current_user['user_id'], lead.get('assigned_team_member_id'), lead_id)
        )
        contact_id = cursor.lastrowid

        for table in ['tasks', 'meetings', 'calls', 'communication_log', 'campaign_recipients', 'deals']:
            cursor.execute(
                f"UPDATE {table} SET contact_id = ? WHERE lead_id = ? AND contact_id IS NULL",
                (contact_id, lead_id)
            )

        cursor.execute(
            "UPDATE leads SET converted_contact_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (contact_id, lead_id)
        )
        conn.commit()

        new_contact = fetch_contact_with_member_name(cursor, contact_id)

    return new_contact

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

        cursor.execute("SELECT 1 FROM leads WHERE id = ?", (lead_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Lead not found")

        updated_lead = fetch_lead_with_member_name(cursor, lead_id)

    return updated_lead

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
async def get_deals(stage: str = Query(None), lead_id: int = Query(None), assigned_team_member_id: int = Query(None), token: str = Query(None)):
    """Get all deals, optionally filtered by stage, the originating lead (the reverse of
    deals.lead_id, so the Leads page can show whether a lead has already been converted into a
    real deal instead of that link only being visible from Pipeline), and/or assigned team
    member - the latter, combined with stage=closed, is what the Team/Reports pages' per-member
    drill-down uses so their "Closed"/"Revenue" figures have a real list of deals behind them.
    Matches get_team_analytics' exact OR-fallback (explicit assigned_team_member_id, or
    login-linked owner_id for legacy unassigned deals) so the drill-down's count and total
    never contradict those already-displayed figures."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()

        base_query = """
            SELECT deals.*, team_members.name as assigned_team_member_name,
                   companies.name as company_name, contacts.name as contact_name,
                   (SELECT COUNT(*) FROM quotations WHERE quotations.deal_id = deals.id) as quotation_count
            FROM deals
            LEFT JOIN team_members ON team_members.id = deals.assigned_team_member_id
            LEFT JOIN companies ON companies.id = deals.company_id
            LEFT JOIN contacts ON contacts.id = deals.contact_id
        """
        conditions = []
        params = []
        if stage:
            conditions.append("deals.stage = ?")
            params.append(stage)
        if lead_id is not None:
            conditions.append("deals.lead_id = ?")
            params.append(lead_id)
        if assigned_team_member_id is not None:
            cursor.execute("SELECT user_id FROM team_members WHERE id = ?", (assigned_team_member_id,))
            row = cursor.fetchone()
            uid_param = row['user_id'] if row and row['user_id'] is not None else -1
            conditions.append("(deals.assigned_team_member_id = ? OR (deals.owner_id = ? AND deals.assigned_team_member_id IS NULL))")
            params.extend([assigned_team_member_id, uid_param])

        query = base_query + (" WHERE " + " AND ".join(conditions) if conditions else "") + " ORDER BY deals.created_at DESC"
        cursor.execute(query, params)

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
            INSERT INTO deals (lead_id, deal_value, probability, loan_product, stage, owner_id, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (deal.lead_id, deal.deal_value, deal.probability, deal.loan_product, stage, current_user['user_id'], deal.company_id)
        )
        conn.commit()
        deal_id = cursor.lastrowid
        new_deal = fetch_deal_with_member_name(cursor, deal_id)

    return new_deal

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

        cursor.execute("SELECT 1 FROM deals WHERE id = ?", (deal_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Deal not found")

        updated_deal = fetch_deal_with_member_name(cursor, deal_id)

    return updated_deal

@app.put("/api/deals/{deal_id}/assign", response_model=DealResponse)
async def assign_deal(deal_id: int, assignment: DealAssign, token: str = Query(None)):
    """Assign (or unassign, if team_member_id is null) a deal to a team member, so admins and
    the team lead can see who's working each deal in the Pipeline table."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM deals WHERE id = ?", (deal_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Deal not found")

        if assignment.team_member_id is not None:
            cursor.execute("SELECT 1 FROM team_members WHERE id = ?", (assignment.team_member_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Team member not found")

        cursor.execute(
            "UPDATE deals SET assigned_team_member_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (assignment.team_member_id, deal_id)
        )
        conn.commit()

        return fetch_deal_with_member_name(cursor, deal_id)

@app.put("/api/deals/{deal_id}/company", response_model=DealResponse)
async def link_deal_company(deal_id: int, link: DealCompanyAssign, token: str = Query(None)):
    """Link (or unlink, if company_id is null) a deal to a Companies record - same
    dedicated-endpoint pattern as link_contact_company, needed because a generic PUT can't
    distinguish 'leave company_id alone' from 'clear it' once both are represented as null."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM deals WHERE id = ?", (deal_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Deal not found")

        if link.company_id is not None:
            cursor.execute("SELECT 1 FROM companies WHERE id = ?", (link.company_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Company not found")

        cursor.execute(
            "UPDATE deals SET company_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (link.company_id, deal_id)
        )
        conn.commit()

        return fetch_deal_with_member_name(cursor, deal_id)

@app.put("/api/deals/{deal_id}/contact", response_model=DealResponse)
async def link_deal_contact(deal_id: int, link: DealContactAssign, token: str = Query(None)):
    """Link (or unlink, if contact_id is null) a deal to a Contact - the Contact's own
    Activity Timeline then shows all the deal's activity (calls, tasks, etc)."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM deals WHERE id = ?", (deal_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Deal not found")

        if link.contact_id is not None:
            cursor.execute("SELECT 1 FROM contacts WHERE id = ?", (link.contact_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Contact not found")

        cursor.execute(
            "UPDATE deals SET contact_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (link.contact_id, deal_id)
        )
        conn.commit()

        return fetch_deal_with_member_name(cursor, deal_id)

@app.get("/api/deals/{deal_id}/quotations", response_model=list[QuotationResponse])
async def get_deal_quotations(deal_id: int, token: str = Query(None)):
    """Quotations linked to this deal - the reverse of quotations.deal_id, shown on the
    Pipeline page so a deal row can expand to show what's been quoted."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM deals WHERE id = ?", (deal_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Deal not found")

        cursor.execute("SELECT id FROM quotations WHERE deal_id = ? ORDER BY created_at DESC", (deal_id,))
        ids = [r['id'] for r in cursor.fetchall()]
        quotations = [fetch_quotation_with_details(cursor, qid) for qid in ids]

    return quotations

@app.put("/api/deals/{deal_id}/process-status", response_model=DealResponse)
async def update_deal_process_status(deal_id: int, payload: DealProcessStatusUpdate, token: str = Query(None)):
    """Update a deal's loan-specific sub-status (Login/Sanction/Hold/Disbursed), shown in the
    Pipeline "Sales Pipeline" table. Was frontend-only state before (reset to 'Login' on every
    page reload) - now persisted like everything else here."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM deals WHERE id = ?", (deal_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Deal not found")

        cursor.execute(
            "UPDATE deals SET process_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (payload.process_status, deal_id)
        )
        conn.commit()

        return fetch_deal_with_member_name(cursor, deal_id)

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

# Single source of truth for each Loan Pipeline bucket's WHERE clause, shared between the
# dashboard aggregate (counts/values) and GET /api/analytics/dashboard/loan-stage-deals (the
# drill-down list) - both were previously computed by the same duplicated logic in two places,
# risking exactly the kind of aggregate/drilldown mismatch caught earlier with Calls.
def _loan_stage_where(label):
    if label == "Deals Closed (This Month)":
        return "deals.stage = 'closed' AND strftime('%Y-%m', deals.updated_at) = strftime('%Y-%m', 'now')", []
    if label == "In Progress":
        return "deals.stage != 'closed'", []
    if label == "Rejected":
        return "deals.process_status IN (?, ?)", ['Rejected', 'Closed - Lost']
    if label == "On Hold":
        return "deals.process_status = ?", ['Hold']
    if label == "Login/Sanction":
        # Every pre-disbursement status folds in here - Document Collection through
        # Disbursement Pending are all "still being processed," which is what this
        # dashboard-level bucket is meant to summarize; the full breakdown is on Pipeline.
        return "deals.process_status IN (?, ?, ?, ?, ?, ?)", [
            'Document Collection', 'Login', 'Under Verification', 'Approved', 'Sanction', 'Disbursement Pending'
        ]
    if label == "Disbursed":
        return "deals.process_status = ?", ['Disbursed']
    return None, None

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics(token: str = Query(None)):
    """Get dashboard KPI data - every field here is computed live from real leads/deals/
    contacts/campaigns rows, including the Loan Pipeline and Pipeline Status widgets (both
    used to be hardcoded fake numbers on the frontend that never changed no matter what was
    actually in the database)."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM leads")
        total_leads = cursor.fetchone()['count']

        # status is stored Title-case ("Qualified") - this used to compare against lowercase
        # 'qualified' and so always matched zero rows.
        cursor.execute("SELECT COUNT(*) as count FROM leads WHERE LOWER(status) = 'qualified'")
        qualified = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM deals WHERE stage != 'closed'")
        active_deals = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM deals WHERE stage = 'closed'")
        closed_deals = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM contacts")
        total_contacts = cursor.fetchone()['count']

        cursor.execute("SELECT COALESCE(SUM(deal_value), 0) as total FROM deals")
        total_deals_value = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as count FROM campaigns WHERE status = 'Active'")
        active_campaigns = cursor.fetchone()['count']

        conversion_rate_pct = round((closed_deals / total_leads * 100), 1) if total_leads > 0 else 0

        loan_stages = []
        for label in ["Deals Closed (This Month)", "In Progress", "Rejected", "On Hold", "Login/Sanction", "Disbursed"]:
            where_clause, params = _loan_stage_where(label)
            cursor.execute(
                f"SELECT COUNT(*) as count, COALESCE(SUM(deal_value), 0) as value FROM deals WHERE {where_clause}",
                params
            )
            loan_stages.append({"label": label, **dict(cursor.fetchone())})

        def lead_status_count(status):
            cursor.execute("SELECT COUNT(*) as count FROM leads WHERE LOWER(status) = LOWER(?)", (status,))
            return cursor.fetchone()['count']

        pipeline_status = [
            {"label": "New Leads", "count": lead_status_count("New")},
            {"label": "Contacted", "count": lead_status_count("Contacted")},
            {"label": "Interested", "count": lead_status_count("Interested")},
            {"label": "Qualified", "count": lead_status_count("Qualified")},
        ]

    return {
        "total_leads": total_leads,
        "qualified_leads": qualified,
        "active_deals": active_deals,
        "closed_deals": closed_deals,
        "total_contacts": total_contacts,
        "total_deals_value": total_deals_value,
        "conversion_rate_pct": conversion_rate_pct,
        "active_campaigns": active_campaigns,
        "loan_stages": loan_stages,
        "pipeline_status": pipeline_status
    }

@app.get("/api/analytics/dashboard/loan-stage-deals", response_model=list[DealResponse])
async def get_loan_stage_deals(label: str = Query(...), token: str = Query(None)):
    """The actual deals behind one Dashboard Loan Pipeline bucket - reuses the exact same
    WHERE clause the aggregate count/value above is computed from (_loan_stage_where), so the
    drill-down can never disagree with the number already shown on the card."""
    get_current_user(token)

    where_clause, params = _loan_stage_where(label)
    if where_clause is None:
        raise HTTPException(status_code=404, detail=f"Unknown loan stage bucket: {label}")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT deals.*, team_members.name as assigned_team_member_name,
                   companies.name as company_name,
                   (SELECT COUNT(*) FROM quotations WHERE quotations.deal_id = deals.id) as quotation_count
            FROM deals
            LEFT JOIN team_members ON team_members.id = deals.assigned_team_member_id
            LEFT JOIN companies ON companies.id = deals.company_id
            WHERE {where_clause}
            ORDER BY deals.created_at DESC
            """,
            params
        )
        deals = [dict(row) for row in cursor.fetchall()]

    return deals

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

_CAMPAIGN_SELECT_SQL = """
    SELECT campaigns.*,
           (SELECT COUNT(*) FROM campaign_recipients WHERE campaign_recipients.campaign_id = campaigns.id) as linked_recipient_count,
           (SELECT COUNT(*) FROM campaign_recipients WHERE campaign_recipients.campaign_id = campaigns.id AND campaign_recipients.status = 'Sent') as sent_count
    FROM campaigns
"""

@app.get("/api/campaigns", response_model=list[CampaignResponse])
async def get_campaigns(token: str = Query(None)):
    """Get all marketing campaigns"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(_CAMPAIGN_SELECT_SQL + " ORDER BY campaigns.created_at DESC")
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
            INSERT INTO campaigns (name, type, status, recipients, opens, clicks, message, created_by)
            VALUES (?, ?, ?, ?, 0, 0, ?, ?)
            """,
            (campaign.name, campaign.type, campaign.status, campaign.recipients, campaign.message, current_user['user_id'])
        )
        conn.commit()
        campaign_id = cursor.lastrowid

        cursor.execute(_CAMPAIGN_SELECT_SQL + " WHERE campaigns.id = ?", (campaign_id,))
        new_campaign = cursor.fetchone()

    return campaign_row_to_dict(new_campaign)

@app.put("/api/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: int, campaign: CampaignUpdate, token: str = Query(None)):
    """Update a marketing campaign"""
    get_current_user(token)

    updates = []
    values = []

    for field in ['name', 'type', 'status', 'recipients', 'opens', 'clicks', 'message']:
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

        cursor.execute(_CAMPAIGN_SELECT_SQL + " WHERE campaigns.id = ?", (campaign_id,))
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
        cursor.execute("DELETE FROM campaign_recipients WHERE campaign_id = ?", (campaign_id,))
        cursor.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
        conn.commit()

    return {"message": "Campaign deleted"}

def _campaign_recipient_row_to_dict(r):
    d = dict(r)
    d['name'] = d.get('lead_name') or d.get('contact_name')
    d['phone'] = d.get('lead_phone') or d.get('contact_phone')
    d['email'] = d.get('lead_email') or d.get('contact_email')
    return d

_CAMPAIGN_RECIPIENT_SELECT_SQL = """
    SELECT campaign_recipients.*,
           leads.name as lead_name, leads.phone as lead_phone, leads.email as lead_email,
           contacts.name as contact_name, contacts.phone as contact_phone, contacts.email as contact_email
    FROM campaign_recipients
    LEFT JOIN leads ON leads.id = campaign_recipients.lead_id
    LEFT JOIN contacts ON contacts.id = campaign_recipients.contact_id
"""

@app.post("/api/campaigns/{campaign_id}/recipients")
async def add_campaign_recipients(campaign_id: int, payload: CampaignRecipientAdd, token: str = Query(None)):
    """Add real Leads/Contacts to a campaign, replacing the old plain `recipients` count with
    actual people. Skips anyone already added to this campaign, so re-selecting the same
    leads doesn't create duplicates."""
    get_current_user(token)

    lead_ids = payload.lead_ids or []
    contact_ids = payload.contact_ids or []
    if not lead_ids and not contact_ids:
        raise HTTPException(status_code=400, detail="Select at least one lead or contact to add")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM campaigns WHERE id = ?", (campaign_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Campaign not found")

        cursor.execute(
            "SELECT lead_id, contact_id FROM campaign_recipients WHERE campaign_id = ?",
            (campaign_id,)
        )
        existing = {(r['lead_id'], r['contact_id']) for r in cursor.fetchall()}

        added = 0
        for lead_id in lead_ids:
            if (lead_id, None) in existing:
                continue
            cursor.execute(
                "INSERT INTO campaign_recipients (campaign_id, lead_id, contact_id) VALUES (?, ?, NULL)",
                (campaign_id, lead_id)
            )
            added += 1
        for contact_id in contact_ids:
            if (None, contact_id) in existing:
                continue
            cursor.execute(
                "INSERT INTO campaign_recipients (campaign_id, lead_id, contact_id) VALUES (?, NULL, ?)",
                (campaign_id, contact_id)
            )
            added += 1
        conn.commit()

    return {"added": added, "skipped": len(lead_ids) + len(contact_ids) - added}

@app.get("/api/campaigns/{campaign_id}/recipients", response_model=list[CampaignRecipientResponse])
async def get_campaign_recipients(campaign_id: int, token: str = Query(None)):
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM campaigns WHERE id = ?", (campaign_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Campaign not found")

        cursor.execute(
            _CAMPAIGN_RECIPIENT_SELECT_SQL + " WHERE campaign_recipients.campaign_id = ? ORDER BY campaign_recipients.added_at DESC",
            (campaign_id,)
        )
        rows = [_campaign_recipient_row_to_dict(r) for r in cursor.fetchall()]

    return rows

@app.delete("/api/campaigns/{campaign_id}/recipients/{recipient_id}")
async def remove_campaign_recipient(campaign_id: int, recipient_id: int, token: str = Query(None)):
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM campaign_recipients WHERE id = ? AND campaign_id = ?",
            (recipient_id, campaign_id)
        )
        conn.commit()

    return {"message": "Recipient removed"}

@app.post("/api/campaigns/{campaign_id}/send", response_model=CampaignSendResult)
async def send_campaign(campaign_id: int, token: str = Query(None)):
    """Sends the campaign's message to every Pending recipient over its channel (Email/
    WhatsApp/SMS), reusing the same send endpoints (and communication_log/Activities feed)
    as any other send - so a campaign send shows up in each recipient's own Activity Timeline
    too. Stops attempting further recipients the moment the channel turns out to be
    unconfigured (nothing was actually attempted for those), matching the same
    graceful-degradation contract as every other send path."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        campaign_row = cursor.fetchone()
        if not campaign_row:
            raise HTTPException(status_code=404, detail="Campaign not found")
        campaign = dict(campaign_row)

        if not (campaign.get('message') or '').strip():
            raise HTTPException(status_code=400, detail="Add message content to this campaign before sending.")

        cursor.execute(
            _CAMPAIGN_RECIPIENT_SELECT_SQL + " WHERE campaign_recipients.campaign_id = ? AND campaign_recipients.status = 'Pending'",
            (campaign_id,)
        )
        recipients = [_campaign_recipient_row_to_dict(r) for r in cursor.fetchall()]

    if not recipients:
        return CampaignSendResult(sent=0, failed=0, skipped=0, message="No pending recipients to send to.")

    channel = campaign['type']
    sent = failed = skipped = 0
    not_configured_message = None

    for r in recipients:
        lead_id = r['lead_id']
        contact_id = r['contact_id']

        if channel == 'Email':
            if not r['email']:
                skipped += 1
                continue
            result = await send_email_real(
                EmailSendRequest(to=r['email'], subject=campaign['name'], body=campaign['message'], lead_id=lead_id, contact_id=contact_id),
                token
            )
        elif channel == 'WhatsApp':
            if not r['phone']:
                skipped += 1
                continue
            result = await send_whatsapp(
                WhatsAppSendRequest(to=r['phone'], message=campaign['message'], lead_id=lead_id, contact_id=contact_id),
                token
            )
        else:  # SMS
            if not r['phone']:
                skipped += 1
                continue
            result = await send_sms(
                SmsSendRequest(to=r['phone'], message=campaign['message'], lead_id=lead_id, contact_id=contact_id),
                token
            )

        if not result.configured:
            not_configured_message = result.message
            break

        new_status = 'Sent' if 'sent' in (result.message or '').lower() else 'Failed'
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE campaign_recipients SET status = ?, sent_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_status, r['id'])
            )
            conn.commit()

        if new_status == 'Sent':
            sent += 1
        else:
            failed += 1

    if not_configured_message:
        return CampaignSendResult(sent=sent, failed=failed, skipped=skipped, message=not_configured_message)

    summary = f"Sent to {sent} recipient(s)."
    if failed:
        summary += f" {failed} failed."
    if skipped:
        summary += f" {skipped} skipped (no {'email' if channel == 'Email' else 'phone'} on file)."
    return CampaignSendResult(sent=sent, failed=failed, skipped=skipped, message=summary)

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
    result['linkedin_connected'] = bool(result.get('linkedin_access_token'))
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

        # A user's own Profile Information (name/email/phone) is the authoritative source for
        # what to call them - if this login is linked to a team roster entry
        # (team_members.user_id), keep that entry's name/email/phone in sync automatically,
        # so Reports/Calls/Pipeline assignment dropdowns always show the current name without
        # an admin having to separately edit the Team page.
        roster_updates = [(k, v) for k, v in [('name', settings.full_name), ('email', settings.email), ('phone', settings.phone)] if v is not None]
        if roster_updates:
            roster_set_clause = ', '.join(f"{k} = ?" for k, _ in roster_updates)
            roster_values = [v for _, v in roster_updates] + [current_user['user_id']]
            cursor.execute(f"UPDATE team_members SET {roster_set_clause} WHERE user_id = ?", roster_values)

        conn.commit()
        cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (current_user['user_id'],))
        result = dict(cursor.fetchone())

    result['notifications'] = bool(result['notifications'])
    result['email_notifications'] = bool(result['email_notifications'])
    result['sms_notifications'] = bool(result['sms_notifications'])
    result['linkedin_connected'] = bool(result.get('linkedin_access_token'))
    return result

# ============= CONTACTS ENDPOINTS =============

@app.get("/api/contacts", response_model=list[ContactResponse])
async def get_contacts(token: str = Query(None), assigned_team_member_id: int = Query(None)):
    """Get all contacts, optionally filtered by assigned team member - powers the Reports
    page's Team Productivity drill-down (a member's actual contacts, not just a count)."""
    get_current_user(token)

    base_query = """
        SELECT contacts.*, team_members.name as assigned_team_member_name,
               companies.name as company_name,
               converted_from_lead.name as converted_from_lead_name
        FROM contacts
        LEFT JOIN team_members ON team_members.id = contacts.assigned_team_member_id
        LEFT JOIN companies ON companies.id = contacts.company_id
        LEFT JOIN leads AS converted_from_lead ON converted_from_lead.id = contacts.converted_from_lead_id
    """

    with get_db() as conn:
        cursor = conn.cursor()
        if assigned_team_member_id is not None:
            cursor.execute(base_query + " WHERE contacts.assigned_team_member_id = ? ORDER BY contacts.created_at DESC", (assigned_team_member_id,))
        else:
            cursor.execute(base_query + " ORDER BY contacts.created_at DESC")
        contacts = [dict(row) for row in cursor.fetchall()]

    return contacts

@app.get("/api/contacts/renewals", response_model=list[RenewalContact])
async def get_upcoming_renewals(token: str = Query(None)):
    """Contacts with a renewal_date set that's overdue or due within the next 30 days,
    sorted soonest first - the Dashboard's "Upcoming Renewals" widget. Registered before
    PUT/DELETE /api/contacts/{contact_id} isn't an issue (those are different methods), but
    this GET must stay above any future GET /api/contacts/{contact_id} route or FastAPI would
    try to parse "renewals" as a contact_id."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT contacts.*, team_members.name as assigned_team_member_name,
                   CAST(julianday(contacts.renewal_date) - julianday(date('now')) AS INTEGER) as days_until_renewal
            FROM contacts
            LEFT JOIN team_members ON team_members.id = contacts.assigned_team_member_id
            WHERE contacts.renewal_date IS NOT NULL
              AND julianday(contacts.renewal_date) - julianday(date('now')) <= 30
            ORDER BY contacts.renewal_date ASC
            """
        )
        rows = [dict(r) for r in cursor.fetchall()]

    results = []
    for r in rows:
        days = r['days_until_renewal']
        urgency = "overdue" if days < 0 else ("due_soon" if days <= 7 else "upcoming")
        results.append(RenewalContact(
            id=r['id'], name=r['name'], phone=r['phone'], email=r['email'], bank=r['bank'],
            amount=r['amount'], renewal_date=r['renewal_date'], days_until_renewal=days,
            urgency=urgency, assigned_team_member_name=r['assigned_team_member_name']
        ))
    return results

@app.post("/api/contacts", response_model=ContactResponse)
async def create_contact(contact: ContactCreate, token: str = Query(None)):
    """Create a new contact"""
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO contacts (name, company, company_id, email, phone, city, amount, bank, status, renewal_date, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (contact.name, contact.company, contact.company_id, contact.email, contact.phone, contact.city,
             contact.amount, contact.bank, contact.status or 'Active', contact.renewal_date, current_user['user_id'])
        )
        conn.commit()
        contact_id = cursor.lastrowid

        new_contact = fetch_contact_with_member_name(cursor, contact_id)

    return new_contact

@app.put("/api/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: int, contact: ContactUpdate, token: str = Query(None)):
    """Update a contact"""
    get_current_user(token)

    updates = []
    values = []

    for field in ['name', 'company', 'company_id', 'email', 'phone', 'city', 'score', 'amount', 'bank', 'status', 'renewal_date']:
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

        cursor.execute("SELECT 1 FROM contacts WHERE id = ?", (contact_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Contact not found")

        updated_contact = fetch_contact_with_member_name(cursor, contact_id)

    return updated_contact

@app.put("/api/contacts/{contact_id}/assign", response_model=ContactResponse)
async def assign_contact(contact_id: int, assignment: ContactAssign, token: str = Query(None)):
    """Assign (or unassign, if team_member_id is null) a contact to a team member, so admins
    and the team lead can see who owns each client in the contact book."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM contacts WHERE id = ?", (contact_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Contact not found")

        if assignment.team_member_id is not None:
            cursor.execute("SELECT 1 FROM team_members WHERE id = ?", (assignment.team_member_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Team member not found")

        cursor.execute(
            "UPDATE contacts SET assigned_team_member_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (assignment.team_member_id, contact_id)
        )
        conn.commit()

        return fetch_contact_with_member_name(cursor, contact_id)

@app.put("/api/contacts/{contact_id}/company", response_model=ContactResponse)
async def link_contact_company(contact_id: int, link: ContactCompanyAssign, token: str = Query(None)):
    """Link (or unlink, if company_id is null) a contact to a Companies record - same
    dedicated-endpoint pattern as assign_contact, needed because a generic PUT can't
    distinguish 'leave company_id alone' from 'clear it' once both are represented as null."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM contacts WHERE id = ?", (contact_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Contact not found")

        if link.company_id is not None:
            cursor.execute("SELECT 1 FROM companies WHERE id = ?", (link.company_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Company not found")

        cursor.execute(
            "UPDATE contacts SET company_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (link.company_id, contact_id)
        )
        conn.commit()

        return fetch_contact_with_member_name(cursor, contact_id)

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

def _ai_configured():
    """Whether at least one text-generation AI provider is set up on this server."""
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"))

def _friendly_ai_error(raw_error):
    """Translate a raw Claude/OpenAI exception string into a short, plain-language message.
    The raw exception (a JSON blob with request IDs, error type codes, etc.) is meaningless
    noise to a non-technical user reading it in the chatbot or Content Studio - this is what
    they see instead, while the real exception still gets logged server-side for debugging."""
    print(f"[AI ERROR] {raw_error}")
    lowered = raw_error.lower()
    if "credit balance is too low" in lowered or "insufficient_quota" in lowered or "exceeded your current quota" in lowered:
        return "AI credits have run out - add billing credit with the AI provider to keep using this feature."
    if "invalid_api_key" in lowered or "incorrect api key" in lowered or "authentication_error" in lowered or "invalid x-api-key" in lowered:
        return "The AI key saved on the server looks incorrect - double-check it in backend/.env."
    if "rate_limit" in lowered or " 429" in raw_error:
        return "The AI service is temporarily busy - please try again in a moment."
    if "timeout" in lowered or "timed out" in lowered:
        return "The AI request timed out - please try again."
    return "AI request failed - please try again in a moment."

def _call_ai_text(prompt_or_messages, max_tokens=400, system=None):
    """Shared AI call behind every text-generation feature (AI Suggest Follow-up, Detect
    Date, AI Content Studio, the CRM chatbot). Tries Claude (ANTHROPIC_API_KEY) first; if that
    key isn't set, OR the Claude call itself fails for any reason (e.g. "credit balance too
    low"), falls back to OpenAI (OPENAI_API_KEY) so the feature keeps working as long as at
    least one of the two is funded - useful since the two are billed separately and one may
    run dry before the other is set up. `prompt_or_messages` is either a single prompt string
    (wrapped as one user message) or a list of {"role", "content"} dicts for multi-turn chat;
    `system` is an optional system prompt, passed the native way for each provider. Returns
    (text, error_message, provider) - exactly one of text/error_message is set. Caller is
    responsible for the configured=False case via _ai_configured()."""
    messages = [{"role": "user", "content": prompt_or_messages}] if isinstance(prompt_or_messages, str) else prompt_or_messages
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    claude_error = None

    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            kwargs = {"model": "claude-sonnet-4-5", "max_tokens": max_tokens, "messages": messages}
            if system:
                kwargs["system"] = system
            response = client.messages.create(**kwargs)
            text = "".join(block.text for block in response.content if hasattr(block, 'text')).strip()
            return text, None, "Claude"
        except Exception as e:
            claude_error = str(e)

    if openai_key:
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            openai_messages = ([{"role": "system", "content": system}] if system else []) + messages
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=max_tokens,
                messages=openai_messages
            )
            text = (response.choices[0].message.content or "").strip()
            return text, None, ("OpenAI (Claude fallback)" if claude_error else "OpenAI")
        except Exception as e:
            if claude_error:
                print(f"[AI ERROR] Claude: {claude_error}")
            return None, _friendly_ai_error(str(e)), None

    return None, _friendly_ai_error(claude_error), None

def _generate_ai_suggestion(person_name, notes):
    """Draft a follow-up suggestion from a contact/lead's note history via Claude or OpenAI.
    Returns configured=False (not an error) when neither is set, so the frontend can show a
    clear "not set up" message instead of a generic failure."""
    if not _ai_configured():
        return AISummaryResponse(configured=False, message="Neither Claude AI nor OpenAI is configured on this server.")

    transcripts = [n['transcript'] for n in notes if n.get('transcript')]
    if not transcripts:
        return AISummaryResponse(configured=True, message="No notes yet to summarize.", suggestion=None)

    history = "\n".join(f"- {t}" for t in transcripts)
    prompt = (
        f"You are a sales assistant for an insurance/loan CRM. Here is the call "
        f"note history for {person_name}:\n{history}\n\n"
        "In 2-3 short sentences, suggest what the next follow-up conversation "
        "should cover. Be specific and actionable, not generic."
    )

    suggestion, error, provider = _call_ai_text(prompt, max_tokens=300)
    if error:
        return AISummaryResponse(configured=True, message=error)
    message = "Suggestion generated." if provider == "Claude" else f"Suggestion generated (via {provider})."
    return AISummaryResponse(configured=True, message=message, suggestion=suggestion)

def _detect_followup_date(text):
    """Ask Claude or OpenAI whether a note's text mentions a next-conversation date/time (e.g.
    someone dictating "next conversation is on 25th of August" via the voice-note recorder,
    which only transcribes speech - it doesn't itself understand instructions). Same
    configured=False / graceful-failure pattern as every other AI endpoint here."""
    if not _ai_configured():
        return DetectDateResponse(configured=False, message="Neither Claude AI nor OpenAI is configured on this server.")

    if not text or not text.strip():
        return DetectDateResponse(configured=True, message="No text to check.", detected_date=None)

    today = datetime.now().strftime("%Y-%m-%d (%A)")
    prompt = (
        f"Today's date is {today}. Read this call note and check whether it "
        f"mentions a date/time for a NEXT conversation or follow-up (not the call "
        f"that just happened today):\n\n\"{text}\"\n\n"
        "If it does, reply with ONLY that date/time in exactly this format: "
        "YYYY-MM-DDTHH:MM (use 09:00 if no time was mentioned). "
        "If it does not mention a future date, reply with exactly: NONE"
    )

    raw, error, provider = _call_ai_text(prompt, max_tokens=50)
    if error:
        return DetectDateResponse(configured=True, message=error)

    if raw == "NONE" or not raw:
        return DetectDateResponse(configured=True, message="No date mentioned in the note.", detected_date=None)

    # Validate the model's answer is actually a parseable date before handing it to the
    # frontend - if it replied with anything else, treat that as "nothing found" rather
    # than risk feeding a malformed value into a date input.
    try:
        datetime.strptime(raw, "%Y-%m-%dT%H:%M")
    except ValueError:
        return DetectDateResponse(configured=True, message="No date mentioned in the note.", detected_date=None)

    message = f"Detected {raw.replace('T', ' ')}." if provider == "Claude" else f"Detected {raw.replace('T', ' ')} (via {provider})."
    return DetectDateResponse(configured=True, message=message, detected_date=raw)

@app.post("/api/ai/detect-followup-date", response_model=DetectDateResponse)
async def detect_followup_date(payload: DetectDateRequest, token: str = Query(None)):
    """Check a note's text for a mentioned next-conversation date. Used by the Notes modal's
    "Detect Date" button on both Contacts and Leads."""
    get_current_user(token)
    return _detect_followup_date(payload.text)

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

# ============= TASKS & MEETINGS ENDPOINTS (TODAY PAGE) =============

@app.get("/api/tasks", response_model=list[TaskResponse])
async def get_tasks(token: str = Query(None), date: str = Query(None), view: str = Query(None), assigned_team_member_id: int = Query(None)):
    """Tasks for the Today page's Tasks tab. Three modes: the default "one day" view (tasks due
    on `date`, or today if omitted - what "Today"/"Tomorrow" already are, just by navigating
    the day arrows), view=high_priority, a cross-date smart filter for every open (incomplete)
    High-priority task regardless of due date - matching Kylas's "My High Priority Tasks" quick
    filter, which isn't day-scoped - and assigned_team_member_id, an all-dates filter used by
    the Team/Reports pages' per-member drill-down so it matches what /api/analytics/team's
    tasks_completed figure actually counts (every task ever assigned to them, not just today's)."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        if assigned_team_member_id is not None:
            cursor.execute(
                """
                SELECT tasks.*, team_members.name as assigned_team_member_name,
                       leads.name as lead_name, contacts.name as contact_name
                FROM tasks
                LEFT JOIN team_members ON team_members.id = tasks.assigned_team_member_id
                LEFT JOIN leads ON leads.id = tasks.lead_id
                LEFT JOIN contacts ON contacts.id = tasks.contact_id
                WHERE tasks.assigned_team_member_id = ?
                ORDER BY tasks.due_date DESC, tasks.created_at DESC
                """,
                (assigned_team_member_id,)
            )
        elif view == "high_priority":
            cursor.execute(
                """
                SELECT tasks.*, team_members.name as assigned_team_member_name,
                       leads.name as lead_name, contacts.name as contact_name
                FROM tasks
                LEFT JOIN team_members ON team_members.id = tasks.assigned_team_member_id
                LEFT JOIN leads ON leads.id = tasks.lead_id
                LEFT JOIN contacts ON contacts.id = tasks.contact_id
                WHERE tasks.priority = 'High' AND tasks.completed = 0
                ORDER BY tasks.due_date ASC, tasks.created_at ASC
                """
            )
        else:
            cursor.execute(
                """
                SELECT tasks.*, team_members.name as assigned_team_member_name,
                       leads.name as lead_name, contacts.name as contact_name
                FROM tasks
                LEFT JOIN team_members ON team_members.id = tasks.assigned_team_member_id
                LEFT JOIN leads ON leads.id = tasks.lead_id
                LEFT JOIN contacts ON contacts.id = tasks.contact_id
                WHERE tasks.due_date = COALESCE(?, date('now'))
                ORDER BY tasks.completed ASC, tasks.created_at ASC
                """,
                (date,)
            )
        tasks = [dict(row) for row in cursor.fetchall()]

    return tasks

@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate, token: str = Query(None)):
    """Add a new task"""
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, due_date, priority, created_by, assigned_team_member_id, lead_id, contact_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (task.title, task.due_date, task.priority or 'Normal', current_user['user_id'], task.assigned_team_member_id, task.lead_id, task.contact_id)
        )
        conn.commit()
        task_id = cursor.lastrowid
        new_task = fetch_task_with_member_name(cursor, task_id)

    return new_task

@app.put("/api/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task: TaskUpdate, token: str = Query(None)):
    """Update a task - including toggling it complete"""
    get_current_user(token)

    updates = []
    values = []
    for field in ['title', 'due_date', 'completed', 'priority', 'assigned_team_member_id', 'lead_id', 'contact_id']:
        value = getattr(task, field)
        if value is not None:
            updates.append(f"{field} = ?")
            values.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(task_id)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()

        cursor.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Task not found")

        updated_task = fetch_task_with_member_name(cursor, task_id)

    return updated_task

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int, token: str = Query(None)):
    """Remove a task"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task deleted"}

@app.get("/api/meetings", response_model=list[MeetingResponse])
async def get_meetings(token: str = Query(None), date: str = Query(None), assigned_team_member_id: int = Query(None)):
    """Meetings scheduled on a given date (defaults to today) - the Today page's Meetings tab.
    assigned_team_member_id switches to an all-dates filter instead, used by the Team/Reports
    pages' per-member drill-down so it matches what /api/analytics/team's meetings_conducted
    figure actually counts (every meeting ever assigned to them, not just today's)."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        if assigned_team_member_id is not None:
            cursor.execute(
                """
                SELECT meetings.*, team_members.name as assigned_team_member_name,
                       leads.name as lead_name, contacts.name as contact_name
                FROM meetings
                LEFT JOIN team_members ON team_members.id = meetings.assigned_team_member_id
                LEFT JOIN leads ON leads.id = meetings.lead_id
                LEFT JOIN contacts ON contacts.id = meetings.contact_id
                WHERE meetings.assigned_team_member_id = ?
                ORDER BY meetings.meeting_date DESC, meetings.meeting_time ASC
                """,
                (assigned_team_member_id,)
            )
        else:
            cursor.execute(
                """
                SELECT meetings.*, team_members.name as assigned_team_member_name,
                       leads.name as lead_name, contacts.name as contact_name
                FROM meetings
                LEFT JOIN team_members ON team_members.id = meetings.assigned_team_member_id
                LEFT JOIN leads ON leads.id = meetings.lead_id
                LEFT JOIN contacts ON contacts.id = meetings.contact_id
                WHERE meetings.meeting_date = COALESCE(?, date('now'))
                ORDER BY meetings.meeting_time ASC, meetings.created_at ASC
                """,
                (date,)
            )
        meetings = [dict(row) for row in cursor.fetchall()]

    return meetings

@app.post("/api/meetings", response_model=MeetingResponse)
async def create_meeting(meeting: MeetingCreate, token: str = Query(None)):
    """Schedule a new meeting"""
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO meetings (title, meeting_date, meeting_time, lead_id, contact_id, location, notes, created_by, assigned_team_member_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (meeting.title, meeting.meeting_date, meeting.meeting_time, meeting.lead_id, meeting.contact_id,
             meeting.location, meeting.notes, current_user['user_id'], meeting.assigned_team_member_id)
        )
        conn.commit()
        meeting_id = cursor.lastrowid
        new_meeting = fetch_meeting_with_names(cursor, meeting_id)

    return new_meeting

@app.put("/api/meetings/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(meeting_id: int, meeting: MeetingUpdate, token: str = Query(None)):
    """Update a meeting - including marking it Conducted/Cancelled"""
    get_current_user(token)

    updates = []
    values = []
    for field in ['title', 'meeting_date', 'meeting_time', 'lead_id', 'contact_id', 'location', 'notes', 'status', 'assigned_team_member_id']:
        value = getattr(meeting, field)
        if value is not None:
            updates.append(f"{field} = ?")
            values.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(meeting_id)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE meetings SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()

        cursor.execute("SELECT 1 FROM meetings WHERE id = ?", (meeting_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Meeting not found")

        updated_meeting = fetch_meeting_with_names(cursor, meeting_id)

    return updated_meeting

@app.delete("/api/meetings/{meeting_id}")
async def delete_meeting(meeting_id: int, token: str = Query(None)):
    """Cancel/remove a meeting"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Meeting not found")

    return {"message": "Meeting deleted"}

# ============= CALLS ENDPOINTS =============

@app.get("/api/calls", response_model=list[CallResponse])
async def get_calls(token: str = Query(None), team_member_id: int = Query(None)):
    """Get all logged calls, optionally filtered to one team member - used by the Team page's
    per-member drill-down so a card's "Calls" stat can be expanded into the real logged calls
    behind it, the same way Reports' Team Productivity drills into leads/contacts. Matches
    get_team_analytics' OR-fallback exactly (explicit team_member_id, or login-linked
    created_by for legacy unassigned calls) so the drill-down's count never contradicts the
    "N Calls" figure already shown on the same card."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT calls.*, team_members.name as team_member_name,
                   leads.name as lead_name, contacts.name as contact_name
            FROM calls
            LEFT JOIN team_members ON team_members.id = calls.team_member_id
            LEFT JOIN leads ON leads.id = calls.lead_id
            LEFT JOIN contacts ON contacts.id = calls.contact_id
        """
        params = []
        if team_member_id is not None:
            cursor.execute("SELECT user_id FROM team_members WHERE id = ?", (team_member_id,))
            row = cursor.fetchone()
            uid_param = row['user_id'] if row and row['user_id'] is not None else -1
            query += " WHERE (calls.team_member_id = ? OR (calls.created_by = ? AND calls.team_member_id IS NULL))"
            params.extend([team_member_id, uid_param])
        query += " ORDER BY calls.call_date DESC, calls.created_at DESC"
        cursor.execute(query, params)
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
            INSERT INTO calls (name, phone, duration_seconds, type, outcome, call_date, created_by, team_member_id, lead_id, contact_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (call.name, call.phone, call.duration_seconds, call.type, call.outcome, call.call_date,
             current_user['user_id'], call.team_member_id, call.lead_id, call.contact_id)
        )
        conn.commit()
        call_id = cursor.lastrowid

        new_call = call_row_to_dict(fetch_call_with_member_name(cursor, call_id))

    return new_call

@app.put("/api/calls/{call_id}/assign", response_model=CallResponse)
async def assign_call(call_id: int, assignment: CallAssign, token: str = Query(None)):
    """Assign (or unassign, if team_member_id is null) a logged call to a team member, so
    admins and the team lead can see who made/handled each call after the fact."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM calls WHERE id = ?", (call_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Call not found")

        if assignment.team_member_id is not None:
            cursor.execute("SELECT 1 FROM team_members WHERE id = ?", (assignment.team_member_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Team member not found")

        cursor.execute(
            "UPDATE calls SET team_member_id = ? WHERE id = ?",
            (assignment.team_member_id, call_id)
        )
        conn.commit()

        return call_row_to_dict(fetch_call_with_member_name(cursor, call_id))

@app.delete("/api/calls/{call_id}")
async def delete_call(call_id: int, token: str = Query(None)):
    """Delete a logged call"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM calls WHERE id = ?", (call_id,))
        conn.commit()

    return {"message": "Call deleted"}

@app.put("/api/calls/{call_id}/contact", response_model=CallResponse)
async def link_call_contact(call_id: int, link: CallContactAssign, token: str = Query(None)):
    """Link (or unlink, if contact_id is null) a call to a Contact."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM calls WHERE id = ?", (call_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Call not found")

        if link.contact_id is not None:
            cursor.execute("SELECT 1 FROM contacts WHERE id = ?", (link.contact_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Contact not found")

        cursor.execute(
            "UPDATE calls SET contact_id = ? WHERE id = ?",
            (link.contact_id, call_id)
        )
        conn.commit()

        return call_row_to_dict(fetch_call_with_member_name(cursor, call_id))

@app.get("/api/contacts/{contact_id}/calls", response_model=list[CallResponse])
async def get_contact_calls(contact_id: int, token: str = Query(None)):
    """Calls directly linked to this Contact."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM contacts WHERE id = ?", (contact_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Contact not found")

        cursor.execute(
            "SELECT id FROM calls WHERE contact_id = ? ORDER BY call_date DESC, created_at DESC",
            (contact_id,)
        )
        rows = cursor.fetchall()
        calls = []
        for row in rows:
            call = fetch_call_with_member_name(cursor, row['id'])
            if call:
                calls.append(call_row_to_dict(call))

    return calls

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
        call_id = _auto_log_dial(dial, current_user['user_id'])
        return DialResponse(configured=True, message=f"Calling you at {agent_number} now.", call_sid=call.sid, call_id=call_id)
    except TwilioRestException as e:
        return DialResponse(configured=True, message=f"Twilio couldn't place the call: {e.msg}")
    except Exception as e:
        return DialResponse(configured=True, message=f"Call failed: {str(e)}")

def _auto_log_dial(dial, user_id):
    """A click-to-call that actually rang counts as a real Attempted call even though its
    outcome/duration aren't known yet (there's no Twilio status webhook wired up to fill
    those in later) - logging it with outcome=None still lets Calls-by-Employee's Attempted
    count reflect what actually happened, since Connected only counts calls with a non-empty
    outcome. Without this, every click-to-call dial would be invisible to that report."""
    with get_db() as conn:
        cursor = conn.cursor()

        name = dial.to
        if dial.lead_id:
            cursor.execute("SELECT name FROM leads WHERE id = ?", (dial.lead_id,))
            row = cursor.fetchone()
            if row:
                name = row['name']
        elif dial.contact_id:
            cursor.execute("SELECT name FROM contacts WHERE id = ?", (dial.contact_id,))
            row = cursor.fetchone()
            if row:
                name = row['name']

        cursor.execute("SELECT id FROM team_members WHERE user_id = ?", (user_id,))
        member_row = cursor.fetchone()
        team_member_id = member_row['id'] if member_row else None

        cursor.execute(
            """
            INSERT INTO calls (name, phone, duration_seconds, type, outcome, call_date, created_by, team_member_id, lead_id, contact_id)
            VALUES (?, ?, 0, 'Outbound', NULL, date('now'), ?, ?, ?, ?)
            """,
            (name, dial.to, user_id, team_member_id, dial.lead_id, dial.contact_id)
        )
        conn.commit()
        return cursor.lastrowid

def _log_communication(channel, recipient, message, status, subject=None, error_detail=None, user_id=None, lead_id=None, contact_id=None):
    """Record a real send attempt (success or failure) to communication_log - the Calls page's
    Emails/WhatsApp tabs (and the unified Activities feed) read from this. Deliberately NOT
    called for the configured=False path (nothing was actually attempted then, just an
    unconfigured-integration response). lead_id/contact_id come from whichever Lead/Contact
    row the send was triggered from, letting that record's own activity timeline find it."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO communication_log (channel, recipient, subject, message, status, error_detail, created_by, lead_id, contact_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (channel, recipient, subject, message, status, error_detail, user_id, lead_id, contact_id)
        )
        conn.commit()

@app.post("/api/sms/send", response_model=SmsSendResponse)
async def send_sms(sms: SmsSendRequest, token: str = Query(None)):
    """Send a real SMS via Twilio, reusing the same credentials as click-to-call. Returns
    configured=False when TWILIO_* isn't set, so the frontend can fall back to an sms: link."""
    current_user = get_current_user(token)

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
        _log_communication("SMS", sms.to, sms.message, "Sent", user_id=current_user['user_id'], lead_id=sms.lead_id, contact_id=sms.contact_id)
        return SmsSendResponse(configured=True, message=f"SMS sent to {sms.to}.")
    except TwilioRestException as e:
        _log_communication("SMS", sms.to, sms.message, "Failed", error_detail=e.msg, user_id=current_user['user_id'], lead_id=sms.lead_id, contact_id=sms.contact_id)
        return SmsSendResponse(configured=True, message=f"SMS failed: {e.msg}")
    except Exception as e:
        _log_communication("SMS", sms.to, sms.message, "Failed", error_detail=str(e), user_id=current_user['user_id'], lead_id=sms.lead_id, contact_id=sms.contact_id)
        return SmsSendResponse(configured=True, message=f"SMS failed: {str(e)}")

@app.post("/api/whatsapp/send", response_model=WhatsAppSendResponse)
async def send_whatsapp(payload: WhatsAppSendRequest, token: str = Query(None)):
    """Send a real WhatsApp message via the Meta Cloud API. Returns configured=False when
    WHATSAPP_TOKEN/WHATSAPP_PHONE_ID aren't set, so the frontend can fall back to a wa.me link."""
    current_user = get_current_user(token)

    wa_token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")

    if not (wa_token and phone_id):
        return WhatsAppSendResponse(configured=False, message="WhatsApp Business API is not configured on this server.")

    try:
        import requests
        to_digits = ''.join(ch for ch in payload.to if ch.isdigit())
        resp = requests.post(
            f"https://graph.facebook.com/v19.0/{phone_id}/messages",
            headers={"Authorization": f"Bearer {wa_token}"},
            json={
                "messaging_product": "whatsapp",
                "to": to_digits,
                "type": "text",
                "text": {"body": payload.message}
            },
            timeout=10
        )
        if resp.status_code >= 400:
            _log_communication("WhatsApp", payload.to, payload.message, "Failed", error_detail=resp.text[:200], user_id=current_user['user_id'], lead_id=payload.lead_id, contact_id=payload.contact_id)
            return WhatsAppSendResponse(configured=True, message=f"WhatsApp send failed: {resp.text[:200]}")
        _log_communication("WhatsApp", payload.to, payload.message, "Sent", user_id=current_user['user_id'], lead_id=payload.lead_id, contact_id=payload.contact_id)
        return WhatsAppSendResponse(configured=True, message=f"WhatsApp message sent to {payload.to}.")
    except Exception as e:
        _log_communication("WhatsApp", payload.to, payload.message, "Failed", error_detail=str(e), user_id=current_user['user_id'], lead_id=payload.lead_id, contact_id=payload.contact_id)
        return WhatsAppSendResponse(configured=True, message=f"WhatsApp send failed: {str(e)}")

@app.post("/api/email/send", response_model=EmailSendResponse)
async def send_email_real(payload: EmailSendRequest, token: str = Query(None)):
    """Send a real email via SMTP. Returns configured=False when SMTP_* isn't set, so the
    frontend can fall back to a mailto: link."""
    current_user = get_current_user(token)

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

        _log_communication("Email", payload.to, payload.body, "Sent", subject=payload.subject, user_id=current_user['user_id'], lead_id=payload.lead_id, contact_id=payload.contact_id)
        return EmailSendResponse(configured=True, message=f"Email sent to {payload.to}.")
    except Exception as e:
        _log_communication("Email", payload.to, payload.body, "Failed", subject=payload.subject, error_detail=str(e), user_id=current_user['user_id'], lead_id=payload.lead_id, contact_id=payload.contact_id)
        return EmailSendResponse(configured=True, message=f"Email failed: {str(e)}")

@app.get("/api/communication-log", response_model=list[CommunicationLogResponse])
async def get_communication_log(token: str = Query(None), channel: str = Query(None), limit: int = Query(100)):
    """Real send history for Email/WhatsApp/SMS, most recent first - the Calls page's Emails
    and WhatsApp tabs (mirrors how Kylas groups Call Logs/Emails/WhatsApp together)."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        base_query = """
            SELECT communication_log.*, leads.name as lead_name, contacts.name as contact_name
            FROM communication_log
            LEFT JOIN leads ON leads.id = communication_log.lead_id
            LEFT JOIN contacts ON contacts.id = communication_log.contact_id
        """
        if channel:
            cursor.execute(base_query + " WHERE communication_log.channel = ? ORDER BY communication_log.created_at DESC LIMIT ?", (channel, limit))
        else:
            cursor.execute(base_query + " ORDER BY communication_log.created_at DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]

    return rows

def fetch_dialer_item(cursor, queue_id):
    """Read one dial_queue row back joined against its lead/contact (for name+phone) and
    team_members (for the assignee's name)."""
    cursor.execute(
        """
        SELECT dial_queue.*,
               team_members.name as team_member_name,
               COALESCE(users.full_name, users.username) as assigned_by_name,
               COALESCE(leads.name, contacts.name) as name,
               COALESCE(leads.phone, contacts.phone) as phone
        FROM dial_queue
        LEFT JOIN team_members ON team_members.id = dial_queue.team_member_id
        LEFT JOIN users ON users.id = dial_queue.assigned_by
        LEFT JOIN leads ON leads.id = dial_queue.lead_id
        LEFT JOIN contacts ON contacts.id = dial_queue.contact_id
        WHERE dial_queue.id = ?
        """,
        (queue_id,)
    )
    return dict(cursor.fetchone())

# ============= CALL DIALER (Kylas "My Call Dialer" parity) =============

@app.post("/api/dialer/assign")
async def assign_to_dialer(payload: DialerAssignRequest, token: str = Query(None)):
    """Bulk-assign leads/contacts to a team member's dial queue. Skips records already
    Pending for that same team member, so re-selecting the same leads doesn't create
    duplicate queue entries."""
    current_user = get_current_user(token)

    lead_ids = payload.lead_ids or []
    contact_ids = payload.contact_ids or []
    if not lead_ids and not contact_ids:
        raise HTTPException(status_code=400, detail="Select at least one lead or contact to assign")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM team_members WHERE id = ?", (payload.team_member_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Team member not found")

        cursor.execute(
            "SELECT lead_id, contact_id FROM dial_queue WHERE team_member_id = ? AND status = 'Pending'",
            (payload.team_member_id,)
        )
        existing = {(r['lead_id'], r['contact_id']) for r in cursor.fetchall()}

        assigned = 0
        for lead_id in lead_ids:
            if (lead_id, None) in existing:
                continue
            cursor.execute(
                "INSERT INTO dial_queue (lead_id, contact_id, team_member_id, assigned_by) VALUES (?, NULL, ?, ?)",
                (lead_id, payload.team_member_id, current_user['user_id'])
            )
            assigned += 1
        for contact_id in contact_ids:
            if (None, contact_id) in existing:
                continue
            cursor.execute(
                "INSERT INTO dial_queue (lead_id, contact_id, team_member_id, assigned_by) VALUES (NULL, ?, ?, ?)",
                (contact_id, payload.team_member_id, current_user['user_id'])
            )
            assigned += 1
        conn.commit()

    return {"assigned": assigned, "skipped": len(lead_ids) + len(contact_ids) - assigned}

@app.get("/api/dialer/queue", response_model=list[DialerQueueItemResponse])
async def get_dialer_queue(token: str = Query(None), team_member_id: int = Query(None), status: str = Query("Pending")):
    """A team member's dial queue - defaults to their Pending records, oldest-assigned first
    (a FIFO queue to work through), matching Kylas's My Call Dialer."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT dial_queue.*,
                   team_members.name as team_member_name,
                   COALESCE(users.full_name, users.username) as assigned_by_name,
                   COALESCE(leads.name, contacts.name) as name,
                   COALESCE(leads.phone, contacts.phone) as phone
            FROM dial_queue
            LEFT JOIN team_members ON team_members.id = dial_queue.team_member_id
            LEFT JOIN users ON users.id = dial_queue.assigned_by
            LEFT JOIN leads ON leads.id = dial_queue.lead_id
            LEFT JOIN contacts ON contacts.id = dial_queue.contact_id
            WHERE 1=1
        """
        params = []
        if team_member_id is not None:
            query += " AND dial_queue.team_member_id = ?"
            params.append(team_member_id)
        if status:
            query += " AND dial_queue.status = ?"
            params.append(status)
        query += " ORDER BY dial_queue.created_at ASC"
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]

    return rows

@app.put("/api/dialer/queue/{queue_id}", response_model=DialerQueueItemResponse)
async def update_dialer_status(queue_id: int, payload: DialerStatusUpdate, token: str = Query(None)):
    """Mark a queued record Called or Skipped, moving it out of the Pending queue."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM dial_queue WHERE id = ?", (queue_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Queue entry not found")

        cursor.execute(
            "UPDATE dial_queue SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (payload.status, queue_id)
        )
        conn.commit()

        return fetch_dialer_item(cursor, queue_id)

@app.delete("/api/dialer/queue/{queue_id}")
async def delete_dialer_item(queue_id: int, token: str = Query(None)):
    """Remove a record from the dial queue entirely (not the same as marking it Skipped)."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dial_queue WHERE id = ?", (queue_id,))
        conn.commit()

    return {"message": "Removed from dialer queue"}

# ============= UNIFIED ACTIVITIES FEED (Kylas "Campaigns > Activities" parity) =============

@app.get("/api/activities", response_model=list[ActivityItem])
async def get_activities(
    token: str = Query(None), channel: str = Query(None), limit: int = Query(100),
    lead_id: int = Query(None), contact_id: int = Query(None)
):
    """Merges communication_log (Email/WhatsApp/SMS sends), calls, tasks, meetings and campaign
    memberships into one chronological timeline, instead of checking five separate tabs - Kylas
    groups these under Campaigns > Activities. lead_id/contact_id scope the feed to a single
    Lead/Contact's own timeline - what the Notes & Follow-up modal's Activity tab shows on
    Leads/Contacts. Campaign membership (campaign_recipients) was previously only visible from
    the Marketing page's own recipient list - a one-way Campaign -> its recipients link with no
    way to see, from a Lead/Contact's own view, which campaigns they'd been added to."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        comm_query = """
            SELECT communication_log.*, leads.name as lead_name, contacts.name as contact_name
            FROM communication_log
            LEFT JOIN leads ON leads.id = communication_log.lead_id
            LEFT JOIN contacts ON contacts.id = communication_log.contact_id
            WHERE 1=1
        """
        comm_params = []
        if lead_id is not None:
            comm_query += " AND communication_log.lead_id = ?"
            comm_params.append(lead_id)
        if contact_id is not None:
            comm_query += " AND communication_log.contact_id = ?"
            comm_params.append(contact_id)
        comm_query += " ORDER BY communication_log.created_at DESC LIMIT ?"
        comm_params.append(limit)
        cursor.execute(comm_query, comm_params)
        comm_rows = [dict(r) for r in cursor.fetchall()]

        call_query = """
            SELECT calls.*, leads.name as lead_name, contacts.name as contact_name
            FROM calls
            LEFT JOIN leads ON leads.id = calls.lead_id
            LEFT JOIN contacts ON contacts.id = calls.contact_id
            WHERE 1=1
        """
        call_params = []
        if lead_id is not None:
            call_query += " AND calls.lead_id = ?"
            call_params.append(lead_id)
        if contact_id is not None:
            call_query += " AND calls.contact_id = ?"
            call_params.append(contact_id)
        call_query += " ORDER BY calls.call_date DESC, calls.created_at DESC LIMIT ?"
        call_params.append(limit)
        cursor.execute(call_query, call_params)
        call_rows = [dict(r) for r in cursor.fetchall()]

        task_query = """
            SELECT tasks.*, leads.name as lead_name, contacts.name as contact_name
            FROM tasks
            LEFT JOIN leads ON leads.id = tasks.lead_id
            LEFT JOIN contacts ON contacts.id = tasks.contact_id
            WHERE 1=1
        """
        task_params = []
        if lead_id is not None:
            task_query += " AND tasks.lead_id = ?"
            task_params.append(lead_id)
        if contact_id is not None:
            task_query += " AND tasks.contact_id = ?"
            task_params.append(contact_id)
        task_query += " ORDER BY tasks.created_at DESC LIMIT ?"
        task_params.append(limit)
        cursor.execute(task_query, task_params)
        task_rows = [dict(r) for r in cursor.fetchall()]

        meeting_query = """
            SELECT meetings.*, leads.name as lead_name, contacts.name as contact_name
            FROM meetings
            LEFT JOIN leads ON leads.id = meetings.lead_id
            LEFT JOIN contacts ON contacts.id = meetings.contact_id
            WHERE 1=1
        """
        meeting_params = []
        if lead_id is not None:
            meeting_query += " AND meetings.lead_id = ?"
            meeting_params.append(lead_id)
        if contact_id is not None:
            meeting_query += " AND meetings.contact_id = ?"
            meeting_params.append(contact_id)
        meeting_query += " ORDER BY meetings.created_at DESC LIMIT ?"
        meeting_params.append(limit)
        cursor.execute(meeting_query, meeting_params)
        meeting_rows = [dict(r) for r in cursor.fetchall()]

        campaign_recipient_query = """
            SELECT campaign_recipients.*, campaigns.name as campaign_name,
                   leads.name as lead_name, contacts.name as contact_name
            FROM campaign_recipients
            LEFT JOIN campaigns ON campaigns.id = campaign_recipients.campaign_id
            LEFT JOIN leads ON leads.id = campaign_recipients.lead_id
            LEFT JOIN contacts ON contacts.id = campaign_recipients.contact_id
            WHERE 1=1
        """
        campaign_recipient_params = []
        if lead_id is not None:
            campaign_recipient_query += " AND campaign_recipients.lead_id = ?"
            campaign_recipient_params.append(lead_id)
        if contact_id is not None:
            campaign_recipient_query += " AND campaign_recipients.contact_id = ?"
            campaign_recipient_params.append(contact_id)
        campaign_recipient_query += " ORDER BY campaign_recipients.added_at DESC LIMIT ?"
        campaign_recipient_params.append(limit)
        cursor.execute(campaign_recipient_query, campaign_recipient_params)
        campaign_recipient_rows = [dict(r) for r in cursor.fetchall()]

    items = []
    for r in comm_rows:
        items.append({
            "id": f"comm-{r['id']}",
            "channel": r['channel'],
            "contact": r.get('recipient'),
            "detail": r.get('subject') or (r.get('message') or '')[:80],
            "outcome": r['status'],
            "timestamp": r['created_at'],
            "lead_id": r.get('lead_id'),
            "lead_name": r.get('lead_name'),
            "contact_id": r.get('contact_id'),
            "contact_name": r.get('contact_name'),
        })
    for r in call_rows:
        items.append({
            "id": f"call-{r['id']}",
            "channel": "Call",
            "contact": r.get('name'),
            "detail": f"{r.get('type', 'Outbound')} call - {r.get('duration_seconds') or 0}s",
            "outcome": r.get('outcome'),
            "timestamp": r.get('created_at'),
            "lead_id": r.get('lead_id'),
            "lead_name": r.get('lead_name'),
            "contact_id": r.get('contact_id'),
            "contact_name": r.get('contact_name'),
        })
    for r in task_rows:
        items.append({
            "id": f"task-{r['id']}",
            "channel": "Task",
            "contact": r.get('lead_name') or r.get('contact_name'),
            "detail": f"{r['title']} - due {r['due_date']}",
            "outcome": "Completed" if r.get('completed') else "Pending",
            "timestamp": r.get('created_at'),
            "lead_id": r.get('lead_id'),
            "lead_name": r.get('lead_name'),
            "contact_id": r.get('contact_id'),
            "contact_name": r.get('contact_name'),
        })
    for r in meeting_rows:
        items.append({
            "id": f"meeting-{r['id']}",
            "channel": "Meeting",
            "contact": r.get('lead_name') or r.get('contact_name'),
            "detail": f"{r['title']} - {r['meeting_date']}" + (f" {r['meeting_time']}" if r.get('meeting_time') else ""),
            "outcome": r.get('status'),
            "timestamp": r.get('created_at'),
            "lead_id": r.get('lead_id'),
            "lead_name": r.get('lead_name'),
            "contact_id": r.get('contact_id'),
            "contact_name": r.get('contact_name'),
        })
    for r in campaign_recipient_rows:
        items.append({
            "id": f"campaign-{r['id']}",
            "channel": "Campaign",
            "contact": r.get('lead_name') or r.get('contact_name'),
            "detail": r.get('campaign_name') or 'Campaign',
            "outcome": r.get('status'),
            "timestamp": r.get('added_at'),
            "lead_id": r.get('lead_id'),
            "lead_name": r.get('lead_name'),
            "contact_id": r.get('contact_id'),
            "contact_name": r.get('contact_name'),
        })

    if channel and channel != "All":
        items = [i for i in items if i['channel'].lower() == channel.lower()]

    items.sort(key=lambda i: i['timestamp'], reverse=True)
    return items[:limit]

# ============= COMPANIES (Kylas parity - standalone directory) =============

_COMPANY_WITH_CONTACT_COUNT_SQL = """
    SELECT companies.*,
           (SELECT COUNT(*) FROM contacts WHERE contacts.company_id = companies.id) as contact_count,
           (SELECT COUNT(*) FROM deals WHERE deals.company_id = companies.id) as deal_count,
           (SELECT COUNT(*) FROM quotations JOIN deals ON deals.id = quotations.deal_id
            WHERE deals.company_id = companies.id) as quotation_count
    FROM companies
"""

@app.get("/api/companies", response_model=list[CompanyResponse])
async def get_companies(token: str = Query(None)):
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(_COMPANY_WITH_CONTACT_COUNT_SQL + " ORDER BY companies.name ASC")
        rows = [dict(r) for r in cursor.fetchall()]

    return rows

@app.get("/api/companies/{company_id}/contacts", response_model=list[ContactResponse])
async def get_company_contacts(company_id: int, token: str = Query(None)):
    """Contacts linked to this Company record - the reverse of contacts.company_id, shown on
    the Companies page so a company row can expand to show who works there."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM companies WHERE id = ?", (company_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Company not found")

        cursor.execute(
            """
            SELECT contacts.*, team_members.name as assigned_team_member_name,
                   companies.name as company_name
            FROM contacts
            LEFT JOIN team_members ON team_members.id = contacts.assigned_team_member_id
            LEFT JOIN companies ON companies.id = contacts.company_id
            WHERE contacts.company_id = ?
            ORDER BY contacts.name ASC
            """,
            (company_id,)
        )
        rows = [dict(r) for r in cursor.fetchall()]

    return rows

@app.get("/api/companies/{company_id}/deals", response_model=list[DealResponse])
async def get_company_deals(company_id: int, token: str = Query(None)):
    """Deals linked to this Company record - the reverse of deals.company_id, shown on the
    Companies page alongside linked contacts."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM companies WHERE id = ?", (company_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Company not found")

        cursor.execute(
            """
            SELECT deals.*, team_members.name as assigned_team_member_name,
                   companies.name as company_name, contacts.name as contact_name,
                   (SELECT COUNT(*) FROM quotations WHERE quotations.deal_id = deals.id) as quotation_count
            FROM deals
            LEFT JOIN team_members ON team_members.id = deals.assigned_team_member_id
            LEFT JOIN companies ON companies.id = deals.company_id
            LEFT JOIN contacts ON contacts.id = deals.contact_id
            WHERE deals.company_id = ?
            ORDER BY deals.created_at DESC
            """,
            (company_id,)
        )
        rows = [dict(r) for r in cursor.fetchall()]

    return rows

@app.get("/api/contacts/{contact_id}/deals", response_model=list[DealResponse])
async def get_contact_deals(contact_id: int, token: str = Query(None)):
    """Deals directly linked to this Contact record - the reverse of deals.contact_id."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM contacts WHERE id = ?", (contact_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Contact not found")

        cursor.execute(
            """
            SELECT deals.*, team_members.name as assigned_team_member_name,
                   companies.name as company_name, contacts.name as contact_name,
                   (SELECT COUNT(*) FROM quotations WHERE quotations.deal_id = deals.id) as quotation_count
            FROM deals
            LEFT JOIN team_members ON team_members.id = deals.assigned_team_member_id
            LEFT JOIN companies ON companies.id = deals.company_id
            LEFT JOIN contacts ON contacts.id = deals.contact_id
            WHERE deals.contact_id = ?
            ORDER BY deals.created_at DESC
            """,
            (contact_id,)
        )
        rows = [dict(r) for r in cursor.fetchall()]

    return rows

@app.get("/api/companies/{company_id}/quotations", response_model=list[QuotationResponse])
async def get_company_quotations(company_id: int, token: str = Query(None)):
    """Quotations linked to this Company - reached only indirectly, through the deals linked
    to it (quotations.deal_id -> deals.company_id), since quotations have no company_id of
    their own. Shown on the Companies page alongside linked contacts/deals, completing the
    same reverse-lookup that Quotations.jsx already resolves forward."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM companies WHERE id = ?", (company_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Company not found")

        cursor.execute(
            """
            SELECT quotations.id FROM quotations
            JOIN deals ON deals.id = quotations.deal_id
            WHERE deals.company_id = ?
            ORDER BY quotations.created_at DESC
            """,
            (company_id,)
        )
        ids = [r['id'] for r in cursor.fetchall()]
        quotations = [fetch_quotation_with_details(cursor, qid) for qid in ids]

    return quotations

@app.get("/api/companies/{company_id}/team_members", response_model=list[TeamMemberResponse])
async def get_company_team_members(company_id: int, token: str = Query(None)):
    """Team members who have worked with this Company - derived from all deals assigned to them
    that have this company_id. Each team member appears once even if they have multiple deals."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM companies WHERE id = ?", (company_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Company not found")

        cursor.execute(
            """
            SELECT DISTINCT team_members.* FROM team_members
            INNER JOIN deals ON (deals.assigned_team_member_id = team_members.id OR
                                (deals.owner_id = team_members.user_id AND deals.assigned_team_member_id IS NULL))
            WHERE deals.company_id = ?
            ORDER BY team_members.role, team_members.name
            """,
            (company_id,)
        )
        members = [dict(row) for row in cursor.fetchall()]

    return members

@app.post("/api/companies", response_model=CompanyResponse)
async def create_company(company: CompanyCreate, token: str = Query(None)):
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO companies (name, industry, city, phone, email, website, notes, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (company.name, company.industry, company.city, company.phone, company.email, company.website, company.notes, current_user['user_id'])
        )
        conn.commit()
        company_id = cursor.lastrowid
        cursor.execute(_COMPANY_WITH_CONTACT_COUNT_SQL + " WHERE companies.id = ?", (company_id,))
        new_company = dict(cursor.fetchone())

    return new_company

@app.put("/api/companies/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: int, company: CompanyUpdate, token: str = Query(None)):
    get_current_user(token)

    updates = []
    values = []
    for field in ['name', 'industry', 'city', 'phone', 'email', 'website', 'notes']:
        value = getattr(company, field)
        if value is not None:
            updates.append(f"{field} = ?")
            values.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(company_id)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE companies SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()

        cursor.execute(_COMPANY_WITH_CONTACT_COUNT_SQL + " WHERE companies.id = ?", (company_id,))
        updated = cursor.fetchone()
        if not updated:
            raise HTTPException(status_code=404, detail="Company not found")

    return dict(updated)

@app.delete("/api/companies/{company_id}")
async def delete_company(company_id: int, token: str = Query(None)):
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        # Unlink first - otherwise contacts/deals.company_id is left pointing at a row that no
        # longer exists instead of a clean "not linked" state.
        cursor.execute("UPDATE contacts SET company_id = NULL WHERE company_id = ?", (company_id,))
        cursor.execute("UPDATE deals SET company_id = NULL WHERE company_id = ?", (company_id,))
        cursor.execute("DELETE FROM companies WHERE id = ?", (company_id,))
        conn.commit()

    return {"message": "Company deleted"}

def fetch_quotation_with_details(cursor, quotation_id):
    """Read one quotation back joined against its linked lead/contact name and (if linked) its
    Deal - resolved into a human-readable deal_label since a deal has no name of its own, just
    a lead + loan product + value - plus its line items and a computed grand_total.
    Quotations have no company_id or assigned_team_member_id of their own; a linked Deal's
    Company (deals.company_id) and assigned team member (deals.assigned_team_member_id) are
    both resolved here too, since neither was previously reachable without leaving to
    Companies/Pipeline and finding the matching deal by hand."""
    cursor.execute(
        """
        SELECT quotations.*, leads.name as lead_name, contacts.name as contact_name,
               deals.loan_product as deal_loan_product, deals.deal_value as deal_deal_value,
               deal_leads.name as deal_lead_name,
               COALESCE(quotations.company_id, deals.company_id) as company_id,
               COALESCE(direct_companies.name, deals_companies.name) as company_name,
               deals.assigned_team_member_id as assigned_team_member_id,
               team_members.name as assigned_team_member_name
        FROM quotations
        LEFT JOIN leads ON leads.id = quotations.lead_id
        LEFT JOIN contacts ON contacts.id = quotations.contact_id
        LEFT JOIN deals ON deals.id = quotations.deal_id
        LEFT JOIN leads AS deal_leads ON deal_leads.id = deals.lead_id
        LEFT JOIN companies AS direct_companies ON direct_companies.id = quotations.company_id
        LEFT JOIN companies AS deals_companies ON deals_companies.id = deals.company_id
        LEFT JOIN team_members ON team_members.id = deals.assigned_team_member_id
        WHERE quotations.id = ?
        """,
        (quotation_id,)
    )
    row = cursor.fetchone()
    if not row:
        return None
    quotation = dict(row)
    if quotation.get('deal_id'):
        quotation['deal_label'] = (
            f"{quotation.get('deal_lead_name') or 'Deal'} - {quotation.get('deal_loan_product') or ''} "
            f"(Rs {quotation.get('deal_deal_value') or 0:,.0f})"
        )
    else:
        quotation['deal_label'] = None
    cursor.execute("SELECT * FROM quotation_items WHERE quotation_id = ? ORDER BY id ASC", (quotation_id,))
    items = [dict(r) for r in cursor.fetchall()]
    quotation['items'] = items
    quotation['grand_total'] = sum(i['amount'] for i in items)
    return quotation

# ============= QUOTATIONS (Kylas parity) =============

@app.get("/api/quotations", response_model=list[QuotationResponse])
async def get_quotations(token: str = Query(None)):
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM quotations ORDER BY created_at DESC")
        ids = [r['id'] for r in cursor.fetchall()]
        quotations = [fetch_quotation_with_details(cursor, qid) for qid in ids]

    return quotations

@app.get("/api/quotations/{quotation_id}", response_model=QuotationResponse)
async def get_quotation(quotation_id: int, token: str = Query(None)):
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        quotation = fetch_quotation_with_details(cursor, quotation_id)
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")

    return quotation

@app.post("/api/quotations", response_model=QuotationResponse)
async def create_quotation(quotation: QuotationCreate, token: str = Query(None)):
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO quotations (lead_id, contact_id, deal_id, title, valid_until, notes, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (quotation.lead_id, quotation.contact_id, quotation.deal_id, quotation.title, quotation.valid_until, quotation.notes, current_user['user_id'])
        )
        quotation_id = cursor.lastrowid

        # Number depends on the row's own id, so it's set in a second update right after insert.
        quotation_number = f"QT-{quotation_id:04d}"
        cursor.execute("UPDATE quotations SET quotation_number = ? WHERE id = ?", (quotation_number, quotation_id))

        for item in quotation.items:
            cursor.execute(
                "INSERT INTO quotation_items (quotation_id, description, amount) VALUES (?, ?, ?)",
                (quotation_id, item.description, item.amount)
            )
        conn.commit()

        new_quotation = fetch_quotation_with_details(cursor, quotation_id)

    return new_quotation

@app.put("/api/quotations/{quotation_id}", response_model=QuotationResponse)
async def update_quotation(quotation_id: int, quotation: QuotationUpdate, token: str = Query(None)):
    get_current_user(token)

    updates = []
    values = []
    for field in ['lead_id', 'contact_id', 'deal_id', 'title', 'valid_until', 'notes', 'status']:
        value = getattr(quotation, field)
        if value is not None:
            updates.append(f"{field} = ?")
            values.append(value)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM quotations WHERE id = ?", (quotation_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Quotation not found")

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(quotation_id)
            cursor.execute(f"UPDATE quotations SET {', '.join(updates)} WHERE id = ?", values)

        if quotation.items is not None:
            cursor.execute("DELETE FROM quotation_items WHERE quotation_id = ?", (quotation_id,))
            for item in quotation.items:
                cursor.execute(
                    "INSERT INTO quotation_items (quotation_id, description, amount) VALUES (?, ?, ?)",
                    (quotation_id, item.description, item.amount)
                )

        conn.commit()
        updated = fetch_quotation_with_details(cursor, quotation_id)

    return updated

@app.delete("/api/quotations/{quotation_id}")
async def delete_quotation(quotation_id: int, token: str = Query(None)):
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quotation_items WHERE quotation_id = ?", (quotation_id,))
        cursor.execute("DELETE FROM quotations WHERE id = ?", (quotation_id,))
        conn.commit()

    return {"message": "Quotation deleted"}

@app.post("/api/quotations/{quotation_id}/send", response_model=EmailSendResponse)
async def send_quotation(quotation_id: int, token: str = Query(None)):
    """Emails a formatted summary of the quotation to the linked lead/contact's address,
    reusing the same SMTP send (and communication_log/Activities feed) path as any other
    email. Moves a Draft quotation to Sent on a successful attempt."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        quotation = fetch_quotation_with_details(cursor, quotation_id)
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")

        recipient_email = None
        recipient_name = None
        if quotation['contact_id']:
            cursor.execute("SELECT name, email FROM contacts WHERE id = ?", (quotation['contact_id'],))
            row = cursor.fetchone()
        elif quotation['lead_id']:
            cursor.execute("SELECT name, email FROM leads WHERE id = ?", (quotation['lead_id'],))
            row = cursor.fetchone()
        else:
            row = None
        if row:
            recipient_name, recipient_email = row['name'], row['email']

    if not recipient_email:
        return EmailSendResponse(configured=True, message="No email address on file for the linked lead/contact.")

    lines = [f"Dear {recipient_name or 'Customer'},", "", f"Please find your quotation {quotation['quotation_number']} below:", ""]
    for item in quotation['items']:
        lines.append(f"- {item['description']}: Rs {item['amount']:,.2f}")
    lines.append("")
    lines.append(f"Grand Total: Rs {quotation['grand_total']:,.2f}")
    if quotation['valid_until']:
        lines.append(f"Valid until: {quotation['valid_until']}")
    if quotation['notes']:
        lines.append("")
        lines.append(quotation['notes'])
    lines.append("")
    lines.append("Regards,\nArthaInvest")
    body = "\n".join(lines)

    result = await send_email_real(
        EmailSendRequest(
            to=recipient_email, subject=f"Quotation {quotation['quotation_number']} - {quotation['title']}", body=body,
            lead_id=quotation['lead_id'], contact_id=quotation['contact_id']
        ),
        token
    )

    if result.configured and result.message.startswith("Email sent"):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE quotations SET status = 'Sent', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'Draft'",
                (quotation_id,)
            )
            conn.commit()

    return result

@app.put("/api/quotations/{quotation_id}/contact", response_model=QuotationResponse)
async def link_quotation_contact(quotation_id: int, link: QuotationContactAssign, token: str = Query(None)):
    """Link (or unlink, if contact_id is null) a quotation to a Contact."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM quotations WHERE id = ?", (quotation_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Quotation not found")

        if link.contact_id is not None:
            cursor.execute("SELECT 1 FROM contacts WHERE id = ?", (link.contact_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Contact not found")

        cursor.execute(
            "UPDATE quotations SET contact_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (link.contact_id, quotation_id)
        )
        conn.commit()

        return fetch_quotation_with_details(cursor, quotation_id)

@app.get("/api/contacts/{contact_id}/quotations", response_model=list[QuotationResponse])
async def get_contact_quotations(contact_id: int, token: str = Query(None)):
    """Quotations directly linked to this Contact."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM contacts WHERE id = ?", (contact_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Contact not found")

        cursor.execute(
            "SELECT id FROM quotations WHERE contact_id = ? ORDER BY created_at DESC",
            (contact_id,)
        )
        ids = [r['id'] for r in cursor.fetchall()]
        quotations = [fetch_quotation_with_details(cursor, qid) for qid in ids]

    return quotations

@app.put("/api/quotations/{quotation_id}/company", response_model=QuotationResponse)
async def link_quotation_company(quotation_id: int, link: QuotationCompanyAssign, token: str = Query(None)):
    """Link (or unlink, if company_id is null) a quotation to a Company."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM quotations WHERE id = ?", (quotation_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Quotation not found")

        if link.company_id is not None:
            cursor.execute("SELECT 1 FROM companies WHERE id = ?", (link.company_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Company not found")

        cursor.execute(
            "UPDATE quotations SET company_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (link.company_id, quotation_id)
        )
        conn.commit()

        return fetch_quotation_with_details(cursor, quotation_id)

@app.get("/api/companies/{company_id}/quotations", response_model=list[QuotationResponse])
async def get_company_quotations(company_id: int, token: str = Query(None)):
    """Quotations directly linked to this Company."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM companies WHERE id = ?", (company_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Company not found")

        cursor.execute(
            "SELECT id FROM quotations WHERE company_id = ? ORDER BY created_at DESC",
            (company_id,)
        )
        rows = cursor.fetchall()
        quotations = []
        for row in rows:
            quotation = fetch_quotation_with_details(cursor, row['id'])
            if quotation:
                quotations.append(quotation)

    return quotations

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

# ============= LINKEDIN (MARKETING TAB "POST TO LINKEDIN") =============
#
# OAuth 2.0, unlike every other integration here - there's no static API key to paste in.
# The user clicks "Connect LinkedIn" in the frontend, which hits /connect for an authorization
# URL, approves access on LinkedIn's own site, and LinkedIn redirects back to /callback with a
# code we exchange for an access token. That token (and the member's LinkedIn URN, needed to
# post as them) is stored on user_settings. Posts to the member's personal profile
# (w_member_social) - posting as the Company Page itself needs a separate LinkedIn approval
# (Community Management API) that isn't guaranteed instant, so it's out of scope here.

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
LINKEDIN_POSTS_URL = "https://api.linkedin.com/rest/posts"

@app.get("/api/integrations/linkedin/connect", response_model=LinkedInConnectResponse)
async def linkedin_connect(token: str = Query(None)):
    """Build the LinkedIn OAuth authorization URL for the frontend to open. The user's own
    auth token rides along in the `state` param (LinkedIn returns it verbatim) so the callback
    below - which LinkedIn calls directly, not through the frontend - knows which CRM user to
    attach the resulting LinkedIn token to."""
    get_current_user(token)

    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI")

    if not (client_id and redirect_uri):
        return LinkedInConnectResponse(configured=False, message="LinkedIn is not configured on this server.")

    from urllib.parse import urlencode
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": token,
        "scope": "openid profile w_member_social",
    }
    return LinkedInConnectResponse(
        configured=True,
        message="Redirect the user to auth_url to connect their LinkedIn account.",
        auth_url=f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"
    )

@app.get("/api/integrations/linkedin/callback")
async def linkedin_callback(code: str = Query(None), state: str = Query(None), error: str = Query(None)):
    """LinkedIn redirects here after the user approves (or denies) access. Exchanges the code
    for an access token, fetches the member's LinkedIn id, stores both, then bounces the
    browser back to the Marketing tab so the UI can show the connected state."""
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    if error or not code:
        return RedirectResponse(f"{frontend_url}/marketing?linkedin=error")

    current_user = get_current_user(state)

    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI")

    try:
        import requests
        token_resp = requests.post(
            LINKEDIN_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 60 * 24 * 60 * 60)  # LinkedIn default: 60 days

        userinfo_resp = requests.get(
            LINKEDIN_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        userinfo_resp.raise_for_status()
        member_urn = userinfo_resp.json()["sub"]

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM user_settings WHERE user_id = ?", (current_user['user_id'],))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO user_settings (user_id) VALUES (?)", (current_user['user_id'],))
            cursor.execute(
                """
                UPDATE user_settings
                SET linkedin_access_token = ?,
                    linkedin_token_expires_at = datetime('now', ? || ' seconds'),
                    linkedin_member_urn = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (access_token, str(expires_in), member_urn, current_user['user_id'])
            )
            conn.commit()

        return RedirectResponse(f"{frontend_url}/marketing?linkedin=connected")
    except Exception as e:
        print(f"[ERROR] LinkedIn OAuth callback failed: {e}")
        return RedirectResponse(f"{frontend_url}/marketing?linkedin=error")

@app.post("/api/marketing/linkedin/post", response_model=LinkedInPostResponse)
async def linkedin_post(payload: LinkedInPostRequest, token: str = Query(None)):
    """Publish a text post to the connected LinkedIn member's personal profile."""
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT linkedin_access_token, linkedin_member_urn FROM user_settings WHERE user_id = ?",
            (current_user['user_id'],)
        )
        row = cursor.fetchone()

    if not row or not row['linkedin_access_token']:
        return LinkedInPostResponse(
            configured=False,
            message="LinkedIn is not connected - go to Marketing and click Connect LinkedIn first."
        )

    try:
        import requests
        resp = requests.post(
            LINKEDIN_POSTS_URL,
            headers={
                "Authorization": f"Bearer {row['linkedin_access_token']}",
                "LinkedIn-Version": "202401",
                "X-Restli-Protocol-Version": "2.0.0",
                "Content-Type": "application/json",
            },
            json={
                "author": f"urn:li:person:{row['linkedin_member_urn']}",
                "commentary": payload.text,
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": []
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False
            },
            timeout=10
        )
        if resp.status_code >= 400:
            return LinkedInPostResponse(configured=True, message=f"LinkedIn couldn't publish the post: {resp.text[:300]}")
        post_urn = resp.headers.get("x-restli-id", "")
        return LinkedInPostResponse(configured=True, message="Posted to LinkedIn.", post_urn=post_urn)
    except Exception as e:
        return LinkedInPostResponse(configured=True, message=f"LinkedIn post failed: {str(e)}")

# ============= AI CONTENT STUDIO (MARKETING TAB) =============
#
# Text-content generation via Claude (falling back to OpenAI - see _call_ai_text) - drafts a
# WhatsApp/Email/LinkedIn-ready caption for a festival, promotion, or reminder. This does NOT
# create graphic designs; a real "generate a branded Canva creative automatically" pipeline
# needs Canva's Connect/Autofill API, which requires a Canva Developer app + brand template
# setup that's a separate project from this CRM. What's built here is the piece that's
# actually feasible today: real AI-written copy, same graceful-degradation pattern as every
# other AI endpoint (configured=False if neither provider is set, rather than erroring).

@app.post("/api/marketing/generate-content", response_model=GenerateContentResponse)
async def generate_marketing_content(payload: GenerateContentRequest, token: str = Query(None)):
    """Draft marketing copy for a festival/occasion + platform via Claude or OpenAI."""
    get_current_user(token)

    if not _ai_configured():
        return GenerateContentResponse(configured=False, message="Neither Claude AI nor OpenAI is configured on this server.")

    if not payload.occasion.strip():
        return GenerateContentResponse(configured=True, message="Enter an occasion or topic first.", content=None)

    platform_hint = {
        "WhatsApp": "Keep it short (under 400 characters), warm and personal, fine to use 1-2 emojis. No subject line.",
        "Email": "Include a short subject line on the first line prefixed 'Subject: ', then a brief email body with a clear closing call-to-action.",
        "LinkedIn": "Write it as a professional LinkedIn post, 3-6 short lines, no more than 1-2 emojis, end with a light call-to-action.",
        "SMS": "Keep it under 160 characters, plain text, no emojis.",
    }.get(payload.platform, "Keep it concise and platform-appropriate.")

    extra = f"\nAdditional context from the user: {payload.notes.strip()}" if payload.notes else ""
    prompt = (
        "You are writing marketing content for a solo Indian insurance & loan "
        f"distributor (ArthaInvest) to send to their clients for: {payload.occasion}.\n"
        f"Platform: {payload.platform}. {platform_hint}{extra}\n\n"
        "Write only the ready-to-send content itself - no preamble, no options, no "
        "explanation of what you wrote."
    )

    content, error, provider = _call_ai_text(prompt, max_tokens=400)
    if error:
        return GenerateContentResponse(configured=True, message=error)
    message = "Content generated." if provider == "Claude" else f"Content generated (via {provider})."
    return GenerateContentResponse(configured=True, message=message, content=content)

# ============= CRM CHATBOT (FLOATING "ASK AI" WIDGET, EVERY PAGE) =============
#
# Read-only Q&A over the CRM's own data - "how many leads are from Mumbai", "what's Amit
# Patel's loan amount", etc. Grounded in a compact snapshot of leads/deals/contacts/calls/team
# built fresh on every request (no vector DB or indexing needed at this data volume). It never
# modifies data or takes actions - if asked to do something, it's instructed to point the user
# at the right tab instead. Same Claude-then-OpenAI fallback as every other AI feature here.

def _build_crm_snapshot(cursor):
    """Compact text summary of current CRM data for the chatbot to ground its answers in.
    Dumps full records rather than aggregates only, since a solo/small-team distributor's
    dataset is small enough that this comfortably fits in a prompt - if that stops being true,
    this should become a targeted lookup instead of a full dump."""
    cursor.execute("SELECT id, name, company, status, product, source, ai_score FROM leads ORDER BY created_at DESC")
    leads = [dict(r) for r in cursor.fetchall()]

    cursor.execute(
        """
        SELECT deals.id, deals.lead_id, deals.deal_value, deals.stage, deals.loan_product,
               leads.name as lead_name, team_members.name as assigned_to
        FROM deals
        LEFT JOIN leads ON leads.id = deals.lead_id
        LEFT JOIN team_members ON team_members.id = deals.assigned_team_member_id
        ORDER BY deals.created_at DESC
        """
    )
    deals = [dict(r) for r in cursor.fetchall()]

    cursor.execute(
        """
        SELECT contacts.id, contacts.name, contacts.city, contacts.status, contacts.amount,
               contacts.bank, team_members.name as assigned_to
        FROM contacts
        LEFT JOIN team_members ON team_members.id = contacts.assigned_team_member_id
        ORDER BY contacts.created_at DESC
        """
    )
    contacts = [dict(r) for r in cursor.fetchall()]

    cursor.execute(
        """
        SELECT calls.name, calls.type, calls.outcome, calls.call_date, team_members.name as team_member_name
        FROM calls
        LEFT JOIN team_members ON team_members.id = calls.team_member_id
        ORDER BY calls.call_date DESC
        LIMIT 100
        """
    )
    calls = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT name, role, email, phone FROM team_members")
    team = [dict(r) for r in cursor.fetchall()]

    return (
        f"LEADS ({len(leads)}):\n{json.dumps(leads, default=str)}\n\n"
        f"DEALS ({len(deals)}):\n{json.dumps(deals, default=str)}\n\n"
        f"CONTACTS ({len(contacts)}):\n{json.dumps(contacts, default=str)}\n\n"
        f"CALLS - most recent 100 ({len(calls)}):\n{json.dumps(calls, default=str)}\n\n"
        f"TEAM ({len(team)}):\n{json.dumps(team, default=str)}"
    )

@app.post("/api/ai/chat", response_model=ChatResponse)
async def ai_chat(payload: ChatRequest, token: str = Query(None)):
    """Ask-AI chatbot grounded in a live snapshot of the CRM's own data. Read-only - answers
    questions, never modifies records or triggers actions."""
    get_current_user(token)

    if not _ai_configured():
        return ChatResponse(configured=False, message="Neither Claude AI nor OpenAI is configured on this server.")

    if not payload.message.strip():
        return ChatResponse(configured=True, message="Type a question first.", reply=None)

    with get_db() as conn:
        cursor = conn.cursor()
        snapshot = _build_crm_snapshot(cursor)

    system_prompt = (
        "You are the AI assistant built into ArthaInvest's CRM, used by a solo insurance & "
        "loan distributor in India. Answer the user's question using ONLY the CRM data "
        "snapshot below - never invent names, numbers, or facts that aren't in it. If the "
        "answer isn't in the data, say so plainly instead of guessing. Keep answers short and "
        "direct, in plain language (not JSON). You cannot create, edit, or delete any record - "
        "if asked to do something rather than answer a question, explain that and say which "
        "tab (Leads, Pipeline, Contacts, Calls, Marketing, Team) the user should use instead.\n\n"
        f"CRM DATA SNAPSHOT:\n{snapshot}"
    )

    history_messages = [{"role": m.role, "content": m.content} for m in (payload.history or [])][-8:]
    messages = history_messages + [{"role": "user", "content": payload.message}]

    reply, error, provider = _call_ai_text(messages, max_tokens=500, system=system_prompt)
    if error:
        return ChatResponse(configured=True, message=error)
    message = "Reply generated." if provider == "Claude" else f"Reply generated (via {provider})."
    return ChatResponse(configured=True, message=message, reply=reply)

# ============= AI VOICE CALLER (PRITI / VAPI) =============
#
# Outbound AI voice-agent calls via Vapi (https://vapi.ai). Deliberately does NOT include a
# mid-call lookup endpoint that Vapi's assistant could hit during a live call - every fact
# Priti needs (client name, why she's calling) is passed once at call-trigger time instead,
# which keeps this endpoint's data exposure to exactly what the caller here already chose to
# send, rather than opening a second unauthenticated endpoint into leads/contacts.
#
# Do not call POST /api/voice-agent/call until the compliance checklist is actually done:
# written sign-off from your insurer(s) and DSA principal, DLT Sender registration + a
# 140-series number wired in as the Vapi phone number, DND scrubbing on the call list, and
# call recording turned on. See the Priti plan artifact for the full checklist.

@app.post("/api/voice-agent/call", response_model=VoiceCallTriggerResponse)
async def trigger_voice_call(payload: VoiceCallTriggerRequest, token: str = Query(None)):
    """Trigger an outbound Priti call via Vapi for one lead or contact. Requires
    VAPI_API_KEY, VAPI_ASSISTANT_ID and VAPI_PHONE_NUMBER_ID - returns configured=False when
    any are missing, same fallback pattern as every other integration in this file."""
    current_user = get_current_user(token)

    api_key = os.getenv("VAPI_API_KEY")
    assistant_id = os.getenv("VAPI_ASSISTANT_ID")
    phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID")

    if not (api_key and assistant_id and phone_number_id):
        return VoiceCallTriggerResponse(configured=False, message="Priti (Vapi voice agent) is not configured on this server.")

    if not payload.lead_id and not payload.contact_id:
        raise HTTPException(status_code=400, detail="lead_id or contact_id is required")

    with get_db() as conn:
        cursor = conn.cursor()
        if payload.lead_id:
            cursor.execute("SELECT name, phone FROM leads WHERE id = ?", (payload.lead_id,))
        else:
            cursor.execute("SELECT name, phone FROM contacts WHERE id = ?", (payload.contact_id,))
        person = cursor.fetchone()

    if not person:
        raise HTTPException(status_code=404, detail="Lead or contact not found")
    if not person['phone']:
        return VoiceCallTriggerResponse(configured=True, message=f"{person['name']} has no phone number on file.")

    try:
        import requests
        resp = requests.post(
            "https://api.vapi.ai/call",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "assistantId": assistant_id,
                "phoneNumberId": phone_number_id,
                "customer": {"number": person['phone'], "name": person['name']},
                "assistantOverrides": {
                    "variableValues": {
                        "clientName": person['name'],
                        "reason": payload.reason,
                        "agentName": current_user.get('username', 'your advisor')
                    }
                }
            },
            timeout=15
        )
        if resp.status_code >= 400:
            return VoiceCallTriggerResponse(configured=True, message=f"Vapi call failed: {resp.text[:200]}")
        call_data = resp.json()
        vapi_call_id = call_data.get('id')
        if vapi_call_id:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM team_members WHERE user_id = ?", (current_user['user_id'],))
                member_row = cursor.fetchone()
                cursor.execute(
                    "INSERT INTO voice_call_context (vapi_call_id, lead_id, contact_id, team_member_id, created_by) VALUES (?, ?, ?, ?, ?)",
                    (vapi_call_id, payload.lead_id, payload.contact_id, member_row['id'] if member_row else None, current_user['user_id'])
                )
                conn.commit()
        return VoiceCallTriggerResponse(configured=True, message=f"Priti is calling {person['name']} now.", vapi_call_id=vapi_call_id)
    except Exception as e:
        return VoiceCallTriggerResponse(configured=True, message=f"Vapi call failed: {str(e)}")

@app.post("/api/voice-agent/webhook")
async def voice_agent_webhook(payload: dict):
    """Receives Vapi's end-of-call-report webhook and logs the outcome into the same `calls`
    table Twilio click-to-call and manual entries use. No auth token - Vapi calls this
    server-to-server, not from a logged-in browser session; set VAPI_WEBHOOK_SECRET and check
    it against Vapi's signature header once you've confirmed the exact header name against a
    real account (left undocumented by Vapi's public docs as of this writing rather than
    guessing). This endpoint must be internet-reachable to receive anything - it's unreachable
    from Vapi's cloud while the backend only runs on localhost (see PENDING_LIST.md)."""
    message = payload.get("message", {}) if isinstance(payload, dict) else {}
    if message.get("type") != "end-of-call-report":
        return {"received": True}

    call = message.get("call", {}) or {}
    customer = call.get("customer", {}) or {}
    analysis = message.get("analysis", {}) or {}
    vapi_call_id = call.get("id")

    with get_db() as conn:
        cursor = conn.cursor()

        # Resolve which lead/contact/team member this call was actually for, stashed by
        # trigger_voice_call under the same vapi_call_id - without this the call logs but is
        # permanently unlinked, invisible from that lead/contact's own Activity Timeline.
        lead_id = contact_id = team_member_id = created_by = None
        if vapi_call_id:
            cursor.execute(
                "SELECT lead_id, contact_id, team_member_id, created_by FROM voice_call_context WHERE vapi_call_id = ?",
                (vapi_call_id,)
            )
            context_row = cursor.fetchone()
            if context_row:
                lead_id, contact_id, team_member_id, created_by = (
                    context_row['lead_id'], context_row['contact_id'],
                    context_row['team_member_id'], context_row['created_by']
                )
                cursor.execute("DELETE FROM voice_call_context WHERE vapi_call_id = ?", (vapi_call_id,))

        cursor.execute(
            """
            INSERT INTO calls (name, phone, duration_seconds, type, outcome, call_date, created_by, team_member_id, lead_id, contact_id)
            VALUES (?, ?, ?, 'Voice Agent', ?, date('now'), ?, ?, ?, ?)
            """,
            (
                customer.get('name') or 'Unknown',
                customer.get('number'),
                int(message.get('durationSeconds') or 0),
                analysis.get('summary') or message.get('endedReason') or 'Completed',
                created_by, team_member_id, lead_id, contact_id
            )
        )
        conn.commit()

    return {"received": True}

# ============= TEAM MANAGEMENT ENDPOINTS =============

TEAM_ROLE_ORDER = {"admin": 0, "team_lead": 1, "location_head": 2, "business_manager": 3, "employee": 4}

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

@app.get("/api/team/me", response_model=Optional[TeamMemberResponse])
async def get_my_team_member(token: str = Query(None)):
    """The team roster entry (if any) linked to the logged-in account via
    team_members.user_id - surfaces the same link Reports/Calls already use internally for
    activity tracking, so Settings can show "you're listed on the roster as X" and keep that
    entry's name/email/phone in sync when the user edits their own profile. Returns null
    (not a 404) when this login isn't linked to any roster entry - that's an expected state
    for a login without a roster entry yet, not an error."""
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM team_members WHERE user_id = ?", (current_user['user_id'],))
        row = cursor.fetchone()

    return dict(row) if row else None

@app.post("/api/team", response_model=TeamMemberResponse)
async def create_team_member(member: TeamMemberCreate, token: str = Query(None)):
    """Add a new team member - admin only"""
    require_admin(token)

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
    """Update a team member's details - admin only"""
    require_admin(token)

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
    """Remove a team member - admin only"""
    require_admin(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM team_members WHERE id = ?", (member_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Team member not found")

    return {"message": "Team member removed"}

@app.get("/api/analytics/team", response_model=list[TeamProductivityRow])
async def get_team_analytics(token: str = Query(None)):
    """Real per-team-member productivity. Combines two signals: the original login-linked
    counting (deals.owner_id / calls.created_by / leads.created_by, matched via
    team_members.user_id - kept for members/records that predate assignment) and the explicit
    assignment columns added this session (calls.team_member_id, deals/leads
    .assigned_team_member_id), which work for every team member whether or not they have a
    login. The "AND x IS NULL" guards prevent double-counting a record that has both an old
    owning login and a newer explicit assignment. Every member now gets a real (possibly
    zero) count rather than the old None-for-unlinked-members placeholder, because assignment
    genuinely makes every member measurable now."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM team_members")
        members = [dict(row) for row in cursor.fetchall()]

        rows = []
        for m in members:
            mid = m['id']
            uid = m.get('user_id')
            uid_param = uid if uid is not None else -1

            cursor.execute(
                "SELECT COUNT(*) as count FROM calls WHERE team_member_id = ? OR (created_by = ? AND team_member_id IS NULL)",
                (mid, uid_param)
            )
            calls = cursor.fetchone()['count']

            cursor.execute(
                "SELECT COUNT(*) as count FROM deals WHERE stage = 'closed' AND (assigned_team_member_id = ? OR (owner_id = ? AND assigned_team_member_id IS NULL))",
                (mid, uid_param)
            )
            deals_closed = cursor.fetchone()['count']

            cursor.execute(
                "SELECT COALESCE(SUM(deal_value), 0) as total FROM deals WHERE stage = 'closed' AND (assigned_team_member_id = ? OR (owner_id = ? AND assigned_team_member_id IS NULL))",
                (mid, uid_param)
            )
            revenue = cursor.fetchone()['total']

            cursor.execute(
                "SELECT COUNT(*) as count FROM leads WHERE assigned_team_member_id = ? OR (created_by = ? AND assigned_team_member_id IS NULL)",
                (mid, uid_param)
            )
            total_leads = cursor.fetchone()['count']
            conversion_rate = round((deals_closed / total_leads * 100), 1) if total_leads > 0 else 0.0

            # tasks/meetings were built with real assignment from day one - no login-linked
            # predecessor to fall back to, so no OR-guard needed here unlike the four above.
            cursor.execute(
                "SELECT COUNT(*) as count FROM tasks WHERE assigned_team_member_id = ? AND completed = 1",
                (mid,)
            )
            tasks_completed = cursor.fetchone()['count']

            cursor.execute(
                "SELECT COUNT(*) as count FROM meetings WHERE assigned_team_member_id = ? AND status = 'Conducted'",
                (mid,)
            )
            meetings_conducted = cursor.fetchone()['count']

            rows.append(TeamProductivityRow(
                id=mid, name=m['name'], role=m['role'],
                calls=calls, deals_closed=deals_closed, revenue=revenue, conversion_rate=conversion_rate,
                tasks_completed=tasks_completed, meetings_conducted=meetings_conducted
            ))

    rows.sort(key=lambda r: (TEAM_ROLE_ORDER.get(r.role, 99), r.name))
    return rows

@app.get("/api/team/{team_member_id}/companies", response_model=list[CompanyResponse])
async def get_team_member_companies(team_member_id: int, token: str = Query(None)):
    """Companies this team member has worked with - derived from all deals assigned to them
    (explicitly via assigned_team_member_id, or via legacy login-linked owner_id). Each company
    appears once even if they have multiple deals with the same company."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM team_members WHERE id = ?", (team_member_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Team member not found")
        uid = row['user_id'] if row['user_id'] is not None else -1

        cursor.execute(
            """
            SELECT DISTINCT companies.* FROM companies
            INNER JOIN deals ON deals.company_id = companies.id
            WHERE deals.assigned_team_member_id = ? OR (deals.owner_id = ? AND deals.assigned_team_member_id IS NULL)
            ORDER BY companies.name
            """,
            (team_member_id, uid)
        )
        companies = [dict(row) for row in cursor.fetchall()]

    return companies

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

@app.get("/api/analytics/lead-sources")
async def get_lead_source_roi(token: str = Query(None)):
    """Per lead-source performance: how many leads came from each source, how many turned
    into deals, and how much pipeline/closed value they generated. This is conversion & value
    by source, not true ROI in the financial sense - the CRM has no field anywhere for what a
    source actually costs (ad spend, portal subscription fee, referral payout, etc.), so a
    real cost-adjusted ROI number can't be computed without fabricating a cost. leads.source is
    free text (not a fixed dropdown), so this groups by the exact string typed in - blank/null
    values are grouped together as "Not Specified" rather than dropped."""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                COALESCE(NULLIF(TRIM(l.source), ''), 'Not Specified') as source,
                COUNT(DISTINCT l.id) as total_leads,
                COUNT(DISTINCT d.id) as total_deals,
                COUNT(DISTINCT CASE WHEN d.stage = 'closed' THEN d.id END) as closed_deals,
                COALESCE(SUM(d.deal_value), 0) as total_deal_value,
                COALESCE(SUM(CASE WHEN d.stage = 'closed' THEN d.deal_value ELSE 0 END), 0) as closed_deal_value
            FROM leads l
            LEFT JOIN deals d ON d.lead_id = l.id
            GROUP BY source
            ORDER BY closed_deal_value DESC, total_leads DESC
            """
        )
        rows = [dict(r) for r in cursor.fetchall()]

    for r in rows:
        r['conversion_rate'] = round((r['total_deals'] / r['total_leads'] * 100), 1) if r['total_leads'] > 0 else 0.0

    return rows

# A call is "connected" if it has a real outcome - 'No Answer' and 'Not Connected' represent
# an attempt that never reached the person, everything else (Interested, Not Interested,
# Meeting Scheduled, Follow-up Needed, etc.) means someone actually picked up.
_UNCONNECTED_OUTCOMES = ('No Answer', 'Not Connected')

@app.get("/api/analytics/calls/by-employee", response_model=list[EmployeeCallStats])
async def get_calls_by_employee(token: str = Query(None)):
    """Per-employee call attempt/connect counts (today / this week / this month), computed
    from calls.team_member_id - the field an admin or team lead actually needs to answer
    'who called how many people today, and how many of those actually connected'."""
    get_current_user(token)

    placeholders = ",".join("?" for _ in _UNCONNECTED_OUTCOMES)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM team_members ORDER BY name")
        members = [dict(row) for row in cursor.fetchall()]

        rows = []
        for m in members:
            def counts(date_filter):
                cursor.execute(
                    f"""
                    SELECT
                        COUNT(*) as attempted,
                        SUM(CASE WHEN outcome IS NOT NULL AND outcome != '' AND outcome NOT IN ({placeholders}) THEN 1 ELSE 0 END) as connected
                    FROM calls
                    WHERE team_member_id = ? AND {date_filter}
                    """,
                    (*_UNCONNECTED_OUTCOMES, m['id'])
                )
                r = cursor.fetchone()
                return r['attempted'] or 0, r['connected'] or 0

            today_attempted, today_connected = counts("call_date = date('now')")
            week_attempted, week_connected = counts("call_date >= date('now', '-6 days')")
            month_attempted, month_connected = counts("strftime('%Y-%m', call_date) = strftime('%Y-%m', 'now')")

            rows.append(EmployeeCallStats(
                team_member_id=m['id'], name=m['name'],
                today_attempted=today_attempted, today_connected=today_connected,
                week_attempted=week_attempted, week_connected=week_connected,
                month_attempted=month_attempted, month_connected=month_connected
            ))

    return rows

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
