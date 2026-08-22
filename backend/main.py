from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sqlite3
from typing import List
import os
from dotenv import load_dotenv

from database_sqlite import get_db, init_db
from schemas import (
    UserLogin, UserCreate, UserResponse, Token,
    LeadCreate, LeadUpdate, LeadResponse,
    DealCreate, DealMove, DealResponse,
    CampaignCreate, CampaignUpdate, CampaignResponse,
    IntegrationToggle, IntegrationResponse,
    SettingsUpdate, SettingsResponse
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
             lead.source, current_user['user_id'], 'new')
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
        cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        conn.commit()

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

@app.post("/api/deals", response_model=DealResponse)
async def create_deal(deal: DealCreate, token: str = Query(None)):
    """Create new deal"""
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO deals (lead_id, deal_value, probability, owner_id)
            VALUES (?, ?, ?, ?)
            """,
            (deal.lead_id, deal.deal_value, deal.probability, current_user['user_id'])
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

    valid_stages = ['new', 'qualified', 'proposal', 'negotiation', 'closed']

    if move.stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of {valid_stages}")

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

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
