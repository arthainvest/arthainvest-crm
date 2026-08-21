# ArthaInvest CRM - Architecture & Deployment Guide

**Date:** August 20, 2026  
**Status:** Ready for Web Deployment  
**Domain:** [Your Domain Here]

---

## 📋 Table of Contents
1. [Current Architecture](#current-architecture)
2. [Technology Stack](#technology-stack)
3. [Database Structure](#database-structure)
4. [Deployment Roadmap](#deployment-roadmap)
5. [Web Migration Strategy](#web-migration-strategy)
6. [Domain Setup](#domain-setup)
7. [Timeline & Costs](#timeline--costs)

---

## 🏗️ Current Architecture

### Phase 1: Desktop Application (Current)
```
┌─────────────────────────────────────────────────────┐
│          ArthaInvest CRM Desktop App                │
│                                                     │
│  ┌─────────────────┐        ┌──────────────────┐   │
│  │   PyQt5 GUI     │        │  SQLite Database │   │
│  │  (Frontend)     │◄──────►│   (Local File)   │   │
│  │                 │        │                  │   │
│  │ • Dashboard     │        │ • Leads Table    │   │
│  │ • Kanban Board  │        │ • Deals Table    │   │
│  │ • Lead Mgmt     │        │ • Users Table    │   │
│  │ • Analytics     │        │ • Activity Log   │   │
│  │ • Settings      │        │ • Config Data    │   │
│  └─────────────────┘        └──────────────────┘   │
│                                                     │
│  Deployment: Windows Desktop Application            │
│  Users: Single computer or networked (LAN)          │
│  Data: Local SQLite file (arthainvest_crm.db)      │
└─────────────────────────────────────────────────────┘
```

**Current Tech:**
- **Frontend:** PyQt5 (Python GUI framework)
- **Backend Logic:** Python (same codebase)
- **Database:** SQLite (file-based)
- **Authentication:** Built-in user table with password hashing
- **Deployment:** Batch file installer (INSTALLER.bat)

**Advantages:**
✅ Works offline completely
✅ Lightning-fast performance
✅ Simple setup (2-minute install)
✅ No internet required
✅ Data stays on computer

**Limitations:**
❌ Only works on Windows
❌ Single computer per installation
❌ No team sync across machines
❌ Not accessible remotely
❌ Difficult to backup/sync data

---

## 🔧 Technology Stack

### Current Stack (Desktop)
```
Application Layer:
├── PyQt5 (Desktop UI Framework)
│   ├── QMainWindow (Main application window)
│   ├── QWidget (UI components)
│   ├── QTableWidget (Data tables)
│   ├── QDragDropEvent (Kanban drag-drop)
│   └── QSqlDatabase (Database connection)
│
Logic Layer:
├── Python 3.8+ (Core application logic)
├── Custom Classes (Lead, Deal, User, Activity)
├── AI Lead Scoring Algorithm
└── Role-based Access Control
│
Database Layer:
└── SQLite 3
    ├── File-based database
    ├── ACID compliance
    └── ~500KB database file
```

### Proposed Web Stack (Recommended)
```
CLIENT SIDE (Frontend):
├── React.js or Vue.js
│   ├── Dashboard Component
│   ├── Kanban Board (React Beautiful DnD)
│   ├── Lead Management
│   ├── Analytics Charts (Chart.js/D3.js)
│   └── Real-time Notifications
│
API LAYER (Communication):
└── RESTful API or GraphQL
    ├── HTTP/HTTPS endpoints
    └── JWT Authentication
│
SERVER SIDE (Backend):
├── Python (Flask or FastAPI)
│   ├── User authentication
│   ├── Lead management endpoints
│   ├── Kanban operations
│   ├── AI lead scoring
│   └── File uploads
│
DATABASE:
├── PostgreSQL (Production)
│   ├── User accounts (encrypted passwords)
│   ├── Leads (indexed for fast queries)
│   ├── Deals/Pipeline (with relationships)
│   ├── Activity logs
│   └── Team data
│
INFRASTRUCTURE:
├── Web Server (Nginx/Apache)
├── Application Server (Gunicorn/uWSGI)
├── Load Balancer (if scaling)
├── SSL/TLS (HTTPS encryption)
└── Backup Storage (AWS S3/Google Cloud)
```

---

## 💾 Database Structure

### Current SQLite Schema

**Users Table**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password VARCHAR(255),  -- SHA256 hashed
    role VARCHAR(20),       -- Admin, TeamLead, Employee
    email VARCHAR(100),
    created_at TIMESTAMP,
    last_login TIMESTAMP
);
```

**Leads Table**
```sql
CREATE TABLE leads (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    company VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    product VARCHAR(50),
    ai_score INTEGER,       -- 0-100 score
    lead_tier VARCHAR(10),  -- HOT, WARM, COOL, COLD
    status VARCHAR(20),     -- New, Qualified, Proposal, etc
    source VARCHAR(50),     -- Organic, Referral, Campaign
    created_by INTEGER,     -- User ID
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

**Deals/Pipeline Table**
```sql
CREATE TABLE deals (
    id INTEGER PRIMARY KEY,
    lead_id INTEGER,
    deal_value DECIMAL(10,2),
    stage VARCHAR(20),      -- New, Qualified, Proposal, etc
    probability DECIMAL(3,2), -- 0.0 to 1.0
    expected_close_date DATE,
    owner_id INTEGER,
    created_at TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
```

**Activity Log Table**
```sql
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(100),    -- "added_lead", "moved_deal", etc
    entity_type VARCHAR(20),-- "lead", "deal", "user"
    entity_id INTEGER,
    details TEXT,
    timestamp TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Migration to PostgreSQL (For Web)
- Same schema structure
- Add UUID primary keys (better for distributed systems)
- Add indexing for performance
- Add replication for redundancy
- Add connection pooling
- Add backup automation

---

## 🚀 Deployment Roadmap

### Phase 1: Current State (Desktop) ✅ COMPLETE
- **Status:** Live and operational
- **Users:** Individual installations
- **Deployment:** Batch file installer
- **Timeline:** August 2026

### Phase 2: Web MVP (Next 4-6 weeks) 🎯 RECOMMENDED FIRST STEP
**Goal:** Get a working web version online ASAP

**Requirements:**
- Python backend (Flask or FastAPI)
- Basic React frontend
- PostgreSQL database
- Simple hosting (Heroku, Railway, or DigitalOcean)
- Your domain pointing to web server

**Deliverables:**
- Login page
- Dashboard (read-only)
- Lead listing
- Basic add/edit functionality
- Not production-ready yet

**Effort:** 4-6 weeks (1 developer)
**Cost:** $0 - $100/month hosting

### Phase 3: Feature Parity (6-8 weeks after Phase 2)
**Goal:** Match desktop app features in web version

**Features:**
- ✅ Kanban board with drag-drop
- ✅ Full CRUD operations
- ✅ Lead scoring and tiers
- ✅ Analytics and charts
- ✅ User management
- ✅ Activity logging
- ✅ Role-based access

**Effort:** 6-8 weeks
**Cost:** $150-300/month hosting (with backups)

### Phase 4: Team Collaboration (4 weeks after Phase 3)
**Goal:** Real-time features for team

**Features:**
- Real-time notifications
- Team activity feed
- Shared views and filters
- Email notifications
- Mobile responsive design
- Offline sync capability

**Effort:** 4 weeks
**Cost:** $200-400/month (increased traffic)

### Phase 5: Mobile App (8-12 weeks after Phase 4)
**Goal:** iOS/Android apps

**Options:**
- React Native (shared codebase with web)
- Flutter (separate but powerful)
- PWA (Progressive Web App - fastest)

**Effort:** 8-12 weeks
**Cost:** $300-500/month (CDN, API scaling)

---

## 🌐 Web Migration Strategy

### Step 1: Choose Your Stack

**Option A: Python-based (Recommended - Reuse Code)**
```
Backend: Flask or FastAPI (Python)
Frontend: React.js or Vue.js
Database: PostgreSQL
Hosting: DigitalOcean / Heroku / AWS
Cost: $100-300/month
Speed: Medium (reuse Python logic)
Complexity: Medium
```

**Option B: Full JavaScript Stack**
```
Backend: Node.js + Express
Frontend: React.js or Vue.js
Database: PostgreSQL
Hosting: Vercel / Netlify / Railway
Cost: $50-200/month
Speed: Fast (same language frontend/backend)
Complexity: High (rewrite backend)
```

**Option C: Managed Solution (Fastest)**
```
Platform: Firebase, Supabase, or AppWrite
Frontend: React.js
Database: Managed PostgreSQL
Hosting: Built-in
Cost: $200-400/month (pay-as-you-go)
Speed: Very Fast (quick launch)
Complexity: Low (less control)
```

**🎯 Recommendation:** Option A (Python-based)
- Reuse 70% of existing Python logic
- Add REST API layer (2-3 weeks)
- Add React frontend (3-4 weeks)
- Migrate SQLite to PostgreSQL (1 week)

### Step 2: Create Backend API

Convert existing Python code to FastAPI:

```python
# fastapi_app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2

app = FastAPI()

# Enable CORS for your domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["yourdomain.com", "www.yourdomain.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication endpoint
@app.post("/api/auth/login")
async def login(username: str, password: str):
    # Validate user credentials
    # Return JWT token
    pass

# Lead endpoints
@app.get("/api/leads")
async def get_leads():
    # Return all leads
    pass

@app.post("/api/leads")
async def create_lead(lead_data: dict):
    # Create new lead
    pass

@app.put("/api/leads/{id}")
async def update_lead(id: int, lead_data: dict):
    # Update lead
    pass

# Deal/Pipeline endpoints
@app.get("/api/deals")
async def get_deals():
    # Return deals by stage
    pass

@app.post("/api/deals/{id}/move")
async def move_deal(id: int, new_stage: str):
    # Move deal to new stage
    pass

# Analytics endpoints
@app.get("/api/analytics/dashboard")
async def dashboard_stats():
    # Return KPI metrics
    pass
```

### Step 3: Create Frontend (React)

```javascript
// Dashboard.jsx - Main dashboard component
import React, { useState, useEffect } from 'react';
import KanbanBoard from './KanbanBoard';
import LeadsList from './LeadsList';
import Analytics from './Analytics';

function Dashboard() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [leads, setLeads] = useState([]);
  const [deals, setDeals] = useState([]);

  useEffect(() => {
    // Fetch data from API
    fetch('/api/leads')
      .then(res => res.json())
      .then(data => setLeads(data));
  }, []);

  return (
    <div className="dashboard">
      <nav className="sidebar">
        <button onClick={() => setActiveTab('dashboard')}>Dashboard</button>
        <button onClick={() => setActiveTab('pipeline')}>Pipeline</button>
        <button onClick={() => setActiveTab('leads')}>Leads</button>
        <button onClick={() => setActiveTab('analytics')}>Analytics</button>
      </nav>

      <main className="content">
        {activeTab === 'dashboard' && <Analytics />}
        {activeTab === 'pipeline' && <KanbanBoard deals={deals} />}
        {activeTab === 'leads' && <LeadsList leads={leads} />}
      </main>
    </div>
  );
}

export default Dashboard;
```

### Step 4: Database Migration

```sql
-- Create PostgreSQL database
CREATE DATABASE arthainvest_crm;

-- Migrate tables from SQLite
-- (Most SQL is compatible, just minor adjustments)

-- Add these production features:
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_created ON leads(created_at);
CREATE INDEX idx_deals_stage ON deals(stage);

-- Add backup table
CREATE TABLE backups_log (
    id SERIAL PRIMARY KEY,
    backup_date TIMESTAMP,
    backup_size BIGINT,
    status VARCHAR(20)
);
```

---

## 🌍 Domain Setup

### Your Domain: [yourdomain.com]

#### Step 1: Domain Provider (GoDaddy, Namecheap, Google Domains)
- You already have this ✅
- Keep your current registrar

#### Step 2: Point Domain to Web Server

**Option A: Using Hosting Provider (Recommended for beginners)**
```
1. Buy hosting on DigitalOcean / Heroku / Railway
2. Get server IP address or CNAME record
3. Go to domain registrar dashboard
4. Update DNS settings:
   - Type: A Record
   - Name: @ (for yourdomain.com)
   - Value: [Server IP Address]
   
5. For www.yourdomain.com:
   - Type: CNAME
   - Name: www
   - Value: yourdomain.com

6. Wait 24-48 hours for DNS propagation
7. Test: Visit yourdomain.com in browser
```

**Option B: Using Cloudflare (Recommended for features)**
```
1. Create Cloudflare account (free)
2. Add your domain to Cloudflare
3. Update nameservers at registrar:
   - ns1.cloudflare.com
   - ns2.cloudflare.com
   
4. In Cloudflare dashboard, create:
   - A record: yourdomain.com → Server IP
   - CNAME: www → yourdomain.com
   
5. Enable SSL/TLS (free with Cloudflare)
6. Setup email routing if needed
```

#### Step 3: SSL Certificate (HTTPS)

**Option A: Free (Recommended)**
```
- Use Let's Encrypt (free)
- Most hosting providers include it
- Auto-renewal every 90 days
- Installation: 5 minutes
```

**Option B: Paid Certificates**
```
- Comodo, DigiCert, GeoTrust
- More trust badges for security-conscious users
- Cost: $50-200/year
- Not necessary for starting
```

#### Step 4: Email Setup (Optional but Recommended)

**Setup email like hello@yourdomain.com**

Option A: Free with Cloudflare
```
1. Go to Cloudflare → Email Routing
2. Create email rule:
   hello@yourdomain.com → your-actual-email@gmail.com
3. Set up catch-all rule
```

Option B: Paid Email Hosting
```
- Google Workspace: $6/user/month
- Zoho Mail: $1/user/month
- Setup custom domain email with full features
```

---

## 🏢 Hosting Options Comparison

| Provider | Cost/month | Ease | Speed | Support | Best For |
|----------|-----------|------|-------|---------|----------|
| **Heroku** | $7-50 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Good | Beginners |
| **Railway** | $5-100 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Good | Quick start |
| **DigitalOcean** | $4-40 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Good | Developers |
| **AWS** | $10-200 | ⭐⭐ | ⭐⭐⭐⭐⭐ | Excellent | Enterprise |
| **Vercel** | $0-100 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Good | Frontend only |
| **Supabase** | $0-100 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Good | Managed DB |

**🎯 Recommendation for Starting:** Railway or DigitalOcean App Platform
- Easy deployment from GitHub
- Good performance
- Affordable ($15-30/month)
- Scales well as you grow

---

## 📊 Timeline & Costs

### Timeline Breakdown

```
Total Time: 16-22 weeks (4-5 months)

Phase 1: Desktop ✅ DONE
├─ Design & Development: 8 weeks
├─ Testing: 2 weeks
└─ Deployment: Done

Phase 2: Web MVP (4-6 weeks) 🎯 START HERE
├─ Backend API: 2-3 weeks
├─ Frontend: 2-3 weeks
└─ Deployment setup: 1 week

Phase 3: Feature Parity (6-8 weeks)
├─ Kanban board: 2 weeks
├─ Analytics: 2 weeks
├─ Polish & testing: 2-4 weeks
└─ Documentation: 1 week

Phase 4: Team Features (4 weeks)
├─ Real-time updates: 2 weeks
├─ Notifications: 1 week
└─ Optimization: 1 week

Phase 5: Mobile (8-12 weeks) - Optional
├─ React Native setup: 2 weeks
├─ Feature migration: 4-6 weeks
└─ Testing & store submission: 2-4 weeks
```

### Cost Breakdown

**One-time Costs:**
```
Domain (already purchased):        ₹500-1000/year
SSL Certificate:                   FREE (Let's Encrypt)
Development (if you hire):         ₹100k-300k
Total One-time:                    ₹100.5k-301k
```

**Monthly Recurring Costs:**
```
Hosting (Railway/DigitalOcean):   $15-30/month      ≈ ₹1,200-2,400
Database (PostgreSQL managed):     $15/month         ≈ ₹1,200
Email service (Mailgun):           $0-20/month       ≈ ₹0-1,600
CDN (Cloudflare):                  $0-20/month       ≈ ₹0-1,600
Monitoring (Sentry, LogRocket):    $0-29/month       ≈ ₹0-2,300
Domain renewal:                    ₹40/month avg     ≈ ₹40

Total Monthly (starting):          $45-99/month      ≈ ₹3,600-8,000
Total Monthly (at scale):          $100-200/month    ≈ ₹8,000-16,000
```

---

## 🎯 Step-by-Step: Your Next Actions

### Week 1: Planning & Setup
- [ ] Choose hosting provider (Recommend: Railway)
- [ ] Set up GitHub repository (if not already)
- [ ] Create project on Railway
- [ ] Update DNS records for your domain

### Week 2-3: Backend API
- [ ] Set up FastAPI project
- [ ] Create database models
- [ ] Migrate SQLite data to PostgreSQL
- [ ] Create authentication endpoints
- [ ] Test all API endpoints

### Week 3-4: Frontend
- [ ] Set up React project
- [ ] Create login page
- [ ] Create dashboard components
- [ ] Connect to backend API
- [ ] Deploy to production

### Week 4+: Polish & Scale
- [ ] Set up monitoring & error tracking
- [ ] Optimize performance
- [ ] Create user documentation
- [ ] Marketing & user onboarding
- [ ] Plan Phase 3 features

---

## 💡 Pro Tips

1. **Start with MVP (Phase 2)**
   - Get something online ASAP
   - Get user feedback early
   - Iterate based on real usage

2. **Use GitHub for Version Control**
   - Free with Railway/Vercel deployment
   - Easy rollback if something breaks
   - Track all changes

3. **Monitor Your App**
   - Set up error tracking (Sentry - free tier)
   - Monitor uptime (Uptime Robot - free)
   - Check performance regularly

4. **Get Early Users**
   - Deploy to 2-3 team members first
   - Get feedback before full rollout
   - Find bugs in real usage

5. **Scale Step by Step**
   - Start with 1-2 concurrent users
   - Optimize when needed
   - Add features based on demand

---

## 🔗 Useful Resources

**Backend (Python/FastAPI):**
- FastAPI Documentation: https://fastapi.tiangolo.com
- PostgreSQL: https://www.postgresql.org/docs
- SQLAlchemy ORM: https://www.sqlalchemy.org

**Frontend (React):**
- React Official: https://react.dev
- React Beautiful DnD (Kanban): https://github.com/atlassian/react-beautiful-dnd
- Chart.js (Analytics): https://www.chartjs.org

**Hosting & Deployment:**
- Railway: https://railway.app
- DigitalOcean: https://www.digitalocean.com
- Vercel: https://vercel.com
- Cloudflare: https://www.cloudflare.com

**Security:**
- OWASP Top 10: https://owasp.org/www-project-top-ten
- Let's Encrypt: https://letsencrypt.org
- JWT Authentication: https://jwt.io

---

## ❓ FAQ

**Q: How much will it cost to deploy?**
A: Starting cost is ₹3,600-8,000/month for hosting. No development cost if you do it yourself.

**Q: Can I keep the desktop version while building web?**
A: Yes! Both can run simultaneously. Users can choose which version to use.

**Q: How long until my domain shows the web app?**
A: 5-10 minutes after DNS update (after 24-48 hour propagation).

**Q: Will existing data work with web version?**
A: Yes! We'll migrate all SQLite data to PostgreSQL during Phase 2.

**Q: Can I use my domain with multiple apps?**
A: Yes! Using subdomains:
   - yourdomain.com → Web CRM
   - api.yourdomain.com → Backend API
   - admin.yourdomain.com → Admin panel

**Q: What if users prefer the desktop version?**
A: Keep both! Let users choose. Desktop works offline, web works from anywhere.

---

## 📞 Next Steps

1. **This week:** Decide on hosting provider
2. **Next week:** Set up backend API infrastructure  
3. **Following week:** Start building React frontend
4. **In 4 weeks:** Have basic web version live on your domain
5. **In 8-10 weeks:** Full feature parity with desktop

**Ready to launch your web app? Let's go! 🚀**

---

*Document prepared August 20, 2026*
*ArthaInvest CRM v2.0 - Web Ready*
