# ArthaInvest CRM - Backend API Setup Guide

**This guide builds your FastAPI backend step-by-step.**

---

## 📋 What We're Building

Your FastAPI backend will:
- ✅ Handle user authentication (login/logout)
- ✅ Manage leads (create, read, update, delete)
- ✅ Handle pipeline/deals operations (Kanban drag-drop)
- ✅ Provide analytics data for dashboard
- ✅ Serve data to both web and desktop apps

---

## 🚀 Step 1: Local Setup (Your Computer)

### 1.1 Check Python Installation

```bash
python --version
# Should show Python 3.9 or higher
```

If not installed:
- Download from https://www.python.org/
- Install with "Add Python to PATH" checked

### 1.2 Create Project Structure

```bash
# Navigate to your ArthaInvest folder
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest

# Create backend directory
mkdir backend
cd backend

# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# You should see (venv) at start of terminal line
```

### 1.3 Install Dependencies

```bash
# Install required packages
pip install fastapi uvicorn psycopg2-binary pydantic python-jose bcrypt python-multipart

# Create requirements.txt for later
pip freeze > requirements.txt
```

**Your requirements.txt should have:**
```
fastapi==0.104.1
uvicorn==0.24.0
psycopg2-binary==2.9.9
pydantic==2.5.0
python-jose==3.3.0
bcrypt==4.1.1
python-multipart==0.0.6
```

---

## 📁 Step 2: Create Project Structure

Inside `backend/` folder, create these files:

```
backend/
├── venv/                 (virtual environment - created automatically)
├── main.py              (main FastAPI app)
├── models.py            (database models)
├── database.py          (database connection)
├── schemas.py           (request/response schemas)
├── auth.py              (authentication logic)
├── requirements.txt     (dependencies)
└── .env                 (secrets - DON'T commit this)
```

---

## 🔧 Step 3: Create Core Files

### 3.1 Create `.env` File

**File: `backend/.env`**

```
# Database Connection
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=arthainvest_crm
DB_PORT=5432

# API Settings
SECRET_KEY=your-secret-key-here-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
```

**For Hostinger later, you'll update these with your Hostinger database credentials.**

### 3.2 Create `database.py`

**File: `backend/database.py`**

```python
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'port': os.getenv('DB_PORT', 5432)
}

@contextmanager
def get_db():
    """Get database connection"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()

def execute_query(query, params=None, fetch=False):
    """Execute a database query"""
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.rowcount
        cursor.close()
        return result

def init_db():
    """Initialize database with schema"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'employee',
                full_name VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                company VARCHAR(100),
                email VARCHAR(100),
                phone VARCHAR(20),
                product VARCHAR(50),
                ai_score INTEGER,
                lead_tier VARCHAR(10),
                status VARCHAR(20) DEFAULT 'new',
                source VARCHAR(50),
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                id SERIAL PRIMARY KEY,
                lead_id INTEGER NOT NULL REFERENCES leads(id),
                deal_value DECIMAL(10,2),
                stage VARCHAR(20) DEFAULT 'new',
                probability DECIMAL(3,2),
                expected_close_date DATE,
                owner_id INTEGER REFERENCES users(id),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                action VARCHAR(100),
                entity_type VARCHAR(20),
                entity_id INTEGER,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        print("✓ Database initialized successfully!")
```

### 3.3 Create `schemas.py`

**File: `backend/schemas.py`**

```python
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# User Schemas
class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str = "employee"

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True

# Lead Schemas
class LeadCreate(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    product: Optional[str] = None
    source: Optional[str] = None

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    product: Optional[str] = None
    status: Optional[str] = None
    ai_score: Optional[int] = None
    lead_tier: Optional[str] = None

class LeadResponse(BaseModel):
    id: int
    name: str
    company: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    product: Optional[str]
    ai_score: Optional[int]
    lead_tier: Optional[str]
    status: str
    source: Optional[str]
    created_at: datetime
    updated_at: datetime

# Deal Schemas
class DealCreate(BaseModel):
    lead_id: int
    deal_value: float
    probability: float = 0.5

class DealMove(BaseModel):
    stage: str  # new, qualified, proposal, negotiation, closed

class DealResponse(BaseModel):
    id: int
    lead_id: int
    deal_value: float
    stage: str
    probability: float
    expected_close_date: Optional[datetime]
    created_at: datetime

# Token
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str
```

### 3.4 Create `auth.py`

**File: `backend/auth.py`**

```python
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against hash"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None
        return {"user_id": user_id, "username": payload.get("username")}
    except JWTError:
        return None
```

### 3.5 Create `main.py` (The Main API)

**File: `backend/main.py`**

```python
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import timedelta

from database import get_db, init_db, DB_CONFIG, execute_query
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
app = FastAPI(title="ArthaInvest CRM API", version="1.0.0", lifespan=lifespan)

# Add CORS middleware (allow frontend to connect)
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
async def get_leads(token: str = None, status_filter: str = None):
    """Get all leads, optionally filtered by status"""
    get_current_user(token)  # Verify token
    
    query = "SELECT * FROM leads"
    params = []
    
    if status_filter:
        query += " WHERE status = %s"
        params.append(status_filter)
    
    query += " ORDER BY created_at DESC"
    
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        leads = cursor.fetchall()
        cursor.close()
    
    return leads

@app.post("/api/leads", response_model=LeadResponse)
async def create_lead(lead: LeadCreate, token: str = None):
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
async def get_lead(lead_id: int, token: str = None):
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
async def update_lead(lead_id: int, lead: LeadUpdate, token: str = None):
    """Update lead"""
    get_current_user(token)
    
    # Build dynamic update query
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
async def delete_lead(lead_id: int, token: str = None):
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
async def get_deals(stage: str = None, token: str = None):
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
async def create_deal(deal: DealCreate, token: str = None):
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
async def move_deal(deal_id: int, move: DealMove, token: str = None):
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
async def get_dashboard_analytics(token: str = None):
    """Get dashboard KPI data"""
    get_current_user(token)
    
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Total leads
        cursor.execute("SELECT COUNT(*) as count FROM leads")
        total_leads = cursor.fetchone()['count']
        
        # Qualified leads
        cursor.execute("SELECT COUNT(*) as count FROM leads WHERE status = 'qualified'")
        qualified = cursor.fetchone()['count']
        
        # Active deals
        cursor.execute("SELECT COUNT(*) as count FROM deals WHERE stage != 'closed'")
        active_deals = cursor.fetchone()['count']
        
        # Closed deals
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
async def get_conversion_rate(token: str = None):
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
```

---

## ▶️ Step 4: Test Your Backend Locally

### 4.1 Start the Backend

```bash
# Make sure you're in backend folder and venv is activated
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest\backend
venv\Scripts\activate

# Start the API server
python main.py

# You should see:
# ✓ Database ready!
# Uvicorn running on http://127.0.0.1:8000
```

### 4.2 Test with API

**Open browser and go to:** http://localhost:8000/docs

You'll see **Swagger UI** - an interactive API documentation tool. You can test all endpoints here!

### 4.3 Test Steps

1. **Health Check:**
   - Click "GET /api/health"
   - Click "Try it out"
   - Click "Execute"
   - Should see: `{"status": "ok"}`

2. **Create a User (for testing):**
   - Click "POST /api/auth/register"
   - Fill in the request body
   - Execute

3. **Login:**
   - Click "POST /api/auth/login"
   - Use username/password you created
   - Copy the token from response

4. **Create Lead:**
   - Click "POST /api/leads"
   - In "token" field, paste your token
   - Add lead data
   - Execute

---

## 📊 Step 5: Migrate Your Data (From SQLite)

### 5.1 Export SQLite Data

```bash
# In PowerShell, go to your CRM folder
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest

# Export data to SQL file
sqlite3 arthainvest_crm.db .dump > export.sql
```

### 5.2 Import to PostgreSQL

**When you have Hostinger PostgreSQL set up:**

```bash
# Create a file to import data
# Edit export.sql to:
# 1. Remove SQLite-specific commands
# 2. Keep only CREATE TABLE and INSERT statements
# 3. Save as import.sql

# Then connect to Hostinger database and import
psql -h [hostinger-host] -U [username] -d [database] < import.sql
```

---

## 🔐 Security Tips

1. **Never commit .env file** - Add to .gitignore
2. **Change SECRET_KEY** - Generate a strong one:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
3. **Use HTTPS on production** - Hostinger provides free SSL
4. **Update CORS origins** - Change from "*" to your domain only

---

## 🆘 Common Issues

### Issue: "ModuleNotFoundError: No module named 'fastapi'"
**Solution:** Activate virtual environment first
```bash
venv\Scripts\activate
```

### Issue: "Connection refused" to database
**Solution:** Make sure PostgreSQL is running (or SQLite file exists)

### Issue: "ImportError" in auth.py
**Solution:** Install missing package
```bash
pip install python-jose bcrypt
```

---

## ✅ Success Checklist

- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] .env file created with DB credentials
- [ ] main.py runs without errors
- [ ] http://localhost:8000/docs works
- [ ] Health check returns 200
- [ ] Can register a user
- [ ] Can login and get token
- [ ] Can create a lead
- [ ] Can get leads list

---

**Next: Once the backend is working locally, we'll build the React frontend!**

