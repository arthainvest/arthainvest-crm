from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

from database import get_db, init_db
from schemas import (
    UserLogin, UserCreate, UserResponse, Token,
    LeadCreate, LeadUpdate, LeadResponse,
    DealCreate, DealMove, DealResponse
)
from auth import hash_password, verify_password, create_access_token, decode_token

load_dotenv()

# Lifespan event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        init_db()
        print("✓ Database ready!")
    except Exception as e:
        print(f"✗ Database error: {e}")
    yield
    # Shutdown
    print("✓ Server shutting down")

# Create FastAPI app
app = FastAPI(
    title="ArthaInvest CRM API",
    version="1.0.0",
    description="Backend API for ArthaInvest CRM",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development. Change to your domain later
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
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT * FROM users WHERE username = %s",
            (credentials.username,)
        )
        user = cursor.fetchone()
        cursor.close()

    if not user or not verify_password(credentials.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user['is_active']:
        raise HTTPException(status_code=403, detail="User inactive")

    # Update last login
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_login = NOW() WHERE id = %s",
            (user['id'],)
        )
        conn.commit()
        cursor.close()

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
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, username, email, full_name, role, is_active
                """,
                (user.username, user.email, hash_password(user.password),
                 user.full_name, user.role)
            )
            new_user = cursor.fetchone()
            conn.commit()
            cursor.close()

            return UserResponse(**new_user)

        except psycopg2.IntegrityError:
            conn.rollback()
            cursor.close()
            raise HTTPException(status_code=400, detail="Username or email already exists")

# ============= LEADS ENDPOINTS =============

@app.get("/api/leads", response_model=list[LeadResponse])
async def get_leads(token: str = Query(None), status: str = Query(None)):
    """Get all leads, optionally filtered by status"""
    get_current_user(token)

    query = "SELECT * FROM leads"
    params = []

    if status:
        query += " WHERE status = %s"
        params.append(status)

    query += " ORDER BY created_at DESC"

    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        leads = cursor.fetchall()
        cursor.close()

    return leads

@app.post("/api/leads", response_model=LeadResponse)
async def create_lead(lead: LeadCreate, token: str = Query(None)):
    """Create new lead"""
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            INSERT INTO leads (name, company, email, phone, product, source, created_by, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (lead.name, lead.company, lead.email, lead.phone, lead.product,
             lead.source, current_user['user_id'], 'new')
        )
        new_lead = cursor.fetchone()
        conn.commit()
        cursor.close()

    return new_lead

@app.get("/api/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, token: str = Query(None)):
    """Get single lead"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM leads WHERE id = %s", (lead_id,))
        lead = cursor.fetchone()
        cursor.close()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return lead

@app.put("/api/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: int, lead: LeadUpdate, token: str = Query(None)):
    """Update lead"""
    get_current_user(token)

    updates = []
    values = []

    if lead.name is not None:
        updates.append("name = %s")
        values.append(lead.name)
    if lead.company is not None:
        updates.append("company = %s")
        values.append(lead.company)
    if lead.email is not None:
        updates.append("email = %s")
        values.append(lead.email)
    if lead.phone is not None:
        updates.append("phone = %s")
        values.append(lead.phone)
    if lead.product is not None:
        updates.append("product = %s")
        values.append(lead.product)
    if lead.status is not None:
        updates.append("status = %s")
        values.append(lead.status)
    if lead.ai_score is not None:
        updates.append("ai_score = %s")
        values.append(lead.ai_score)
    if lead.lead_tier is not None:
        updates.append("lead_tier = %s")
        values.append(lead.lead_tier)

    updates.append("updated_at = NOW()")
    values.append(lead_id)

    query = f"UPDATE leads SET {', '.join(updates)} WHERE id = %s RETURNING *"

    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, values)
        updated_lead = cursor.fetchone()
        conn.commit()
        cursor.close()

    if not updated_lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return updated_lead

@app.delete("/api/leads/{lead_id}")
async def delete_lead(lead_id: int, token: str = Query(None)):
    """Delete lead"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM leads WHERE id = %s", (lead_id,))
        conn.commit()
        cursor.close()

    return {"message": "Lead deleted"}

# ============= DEALS/PIPELINE ENDPOINTS =============

@app.get("/api/deals", response_model=list[DealResponse])
async def get_deals(stage: str = Query(None), token: str = Query(None)):
    """Get all deals, optionally filtered by stage"""
    get_current_user(token)

    query = "SELECT * FROM deals"
    params = []

    if stage:
        query += " WHERE stage = %s"
        params.append(stage)

    query += " ORDER BY created_at DESC"

    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        deals = cursor.fetchall()
        cursor.close()

    return deals

@app.post("/api/deals", response_model=DealResponse)
async def create_deal(deal: DealCreate, token: str = Query(None)):
    """Create new deal"""
    current_user = get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            INSERT INTO deals (lead_id, deal_value, probability, owner_id)
            VALUES (%s, %s, %s, %s)
            RETURNING *
            """,
            (deal.lead_id, deal.deal_value, deal.probability, current_user['user_id'])
        )
        new_deal = cursor.fetchone()
        conn.commit()
        cursor.close()

    return new_deal

@app.put("/api/deals/{deal_id}/move")
async def move_deal(deal_id: int, move: DealMove, token: str = Query(None)):
    """Move deal to different stage (Kanban drag-drop)"""
    get_current_user(token)

    valid_stages = ['new', 'qualified', 'proposal', 'negotiation', 'closed']

    if move.stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of {valid_stages}")

    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            UPDATE deals SET stage = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING *
            """,
            (move.stage, deal_id)
        )
        updated_deal = cursor.fetchone()
        conn.commit()
        cursor.close()

    if not updated_deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    return updated_deal

# ============= ANALYTICS ENDPOINTS =============

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics(token: str = Query(None)):
    """Get dashboard KPI data"""
    get_current_user(token)

    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT COUNT(*) as count FROM leads")
        total_leads = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM leads WHERE status = 'qualified'")
        qualified = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM deals WHERE stage != 'closed'")
        active_deals = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM deals WHERE stage = 'closed'")
        closed_deals = cursor.fetchone()['count']

        cursor.close()

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
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT COUNT(*) as count FROM leads")
        total_leads = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM deals")
        total_deals = cursor.fetchone()['count']

        cursor.close()

    conversion_rate = (total_deals / total_leads * 100) if total_leads > 0 else 0

    return {
        "total_leads": total_leads,
        "total_deals": total_deals,
        "conversion_rate": round(conversion_rate, 2)
    }

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
