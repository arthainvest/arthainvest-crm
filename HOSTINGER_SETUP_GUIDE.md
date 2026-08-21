# ArthaInvest CRM - Hostinger Deployment Guide

**Your Setup:** Hostinger Hosting + Your Domain + DIY Development (Path A)

---

## 🎯 Quick Overview

**What You Have:**
- ✅ Domain purchased
- ✅ Hostinger hosting account
- ✅ Your desktop CRM (PyQt5 app working)

**What We'll Do:**
- ✅ Deploy web version to your Hostinger account
- ✅ Use your domain to access it
- ✅ Keep desktop version running locally
- ✅ Share data between both versions

---

## 🌐 Hostinger Hosting Setup

### Step 1: Hostinger HPanel Access

**Login to Hostinger:**
1. Go to https://hostinger.com
2. Click "Login"
3. Enter your email and password
4. Go to "My Hosting" → Your domain

### Step 2: Check Your Hosting Type

**In Hostinger Hpanel, look for:**
- Is it "Business" plan or higher? (Recommended for web apps)
- Do you have SSH access? (Essential for deploying Python apps)
- PHP/MySQL available? (We'll use PostgreSQL instead)

**Check SSH Access:**
1. Go to Account → SSH Keys & Settings
2. Verify SSH is enabled
3. Note your SSH credentials

### Step 3: Create a Subdomain for API

**For your architecture:**
```
yourdomain.com → React Frontend
api.yourdomain.com → FastAPI Backend
```

**Create subdomain:**
1. Go to Domains → Your domain
2. Click "Manage"
3. Create subdomain "api"
4. Point to your hosting account

---

## 🚀 Deployment Architecture for Hostinger

### Current Setup (Desktop)
```
Your Computer
    ↓
PyQt5 App → SQLite Database
```

### New Setup (Web + Desktop)
```
yourdomain.com → Frontend (React on Hostinger)
        ↓
api.yourdomain.com → Backend (FastAPI on Hostinger)
        ↓
PostgreSQL Database (on Hostinger)

Your Computer (still works)
    ↓
PyQt5 Desktop App (can sync with web)
```

---

## 📋 Week 1-2: Setup on Hostinger

### Task 1: SSH into Your Server

**From your computer (Windows PowerShell or terminal):**

```bash
# Connect to Hostinger via SSH
ssh username@your-domain.com

# Your Hostinger username is usually something like:
# u123456789 or root (check in Hpanel)
```

**If SSH key needed:**
1. Go to Hostinger → SSH Keys & Settings
2. Generate new key pair
3. Download private key
4. Use: `ssh -i /path/to/key.pem user@domain.com`

### Task 2: Setup Python Environment

**Once logged in via SSH:**

```bash
# Check Python installed
python3 --version

# If not installed, install it (varies by Hostinger plan):
# Contact Hostinger support: "I need Python 3.9+ installed"

# Create project directory
mkdir /home/username/arthainvest-crm
cd /home/username/arthainvest-crm

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn psycopg2-binary python-jose python-multipart
```

### Task 3: Setup PostgreSQL Database

**Option A: PostgreSQL on Hostinger (Easiest)**
1. Go to Hostinger → Databases
2. Create new PostgreSQL database
3. Note: hostname, username, password, database name
4. Save credentials - you'll need them

**Option B: Use Hostinger MySQL (then convert)**
```bash
# Convert SQLite to MySQL format
# Contact support or use online converter
```

**Connection Test:**

```bash
# After getting credentials
psql -h [hostname] -U [username] -d [database_name]
# Enter password when prompted
# If it connects, you're good!
```

### Task 4: Migrate Your Data

**Export from SQLite (done on your computer):**

```bash
# On your Windows computer in PowerShell:
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest

# Export SQLite data
sqlite3 arthainvest_crm.db .dump > backup.sql
```

**Create PostgreSQL tables on Hostinger:**

```bash
# Connect to PostgreSQL (via SSH on Hostinger)
psql -h [hostname] -U [username] -d [database_name]

# Create tables (paste your schema):
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password VARCHAR(255),
    role VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    company VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    product VARCHAR(50),
    ai_score INTEGER,
    lead_tier VARCHAR(10),
    status VARCHAR(20),
    source VARCHAR(50),
    created_by INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE deals (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER,
    deal_value DECIMAL(10,2),
    stage VARCHAR(20),
    probability DECIMAL(3,2),
    expected_close_date DATE,
    owner_id INTEGER,
    created_at TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

CREATE TABLE activity_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(100),
    entity_type VARCHAR(20),
    entity_id INTEGER,
    details TEXT,
    timestamp TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**Import your data:**

```bash
# Exit psql
\q

# Import data (from your backup.sql)
psql -h [hostname] -U [username] -d [database_name] < backup.sql
```

---

## 🔧 Week 2-3: Build & Deploy Backend

### Step 1: Create FastAPI App on Hostinger

**Create main.py in your Hostinger project:**

```bash
# Via SSH, create the file
nano ~/arthainvest-crm/main.py
```

**Paste this (copy-paste from your Python knowledge):**

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = FastAPI()

# Allow your domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["yourdomain.com", "www.yourdomain.com", "api.yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Test endpoint
@app.get("/api/health")
async def health():
    return {"status": "ok"}

# Login endpoint
@app.post("/api/auth/login")
async def login(username: str, password: str):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and user['password'] == password:  # In production, use hashing
        return {"user_id": user['id'], "role": user['role']}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Get all leads
@app.get("/api/leads")
async def get_leads():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM leads")
    leads = cursor.fetchall()
    conn.close()
    return leads

# Add more endpoints as needed...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 2: Create Environment Variables

**On Hostinger (via SSH):**

```bash
# Create .env file
nano ~/arthainvest-crm/.env
```

**Add your database credentials:**

```
DB_HOST=your-hostinger-db-host
DB_USER=your-db-username
DB_PASSWORD=your-db-password
DB_NAME=your-database-name
```

### Step 3: Setup Gunicorn (Production Server)

**Install and configure:**

```bash
# Activate virtual environment
source ~/arthainvest-crm/venv/bin/activate

# Install gunicorn
pip install gunicorn

# Create startup script
nano ~/arthainvest-crm/start_app.sh
```

**Paste this script:**

```bash
#!/bin/bash
cd /home/username/arthainvest-crm
source venv/bin/activate
export $(cat .env | xargs)
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

**Make it executable:**

```bash
chmod +x ~/arthainvest-crm/start_app.sh
```

---

## 🎨 Week 3-4: Build & Deploy Frontend

### Step 1: Build React Locally

**On your Windows computer:**

```bash
# Create React app
npx create-react-app frontend
cd frontend

# Install dependencies
npm install axios react-router-dom react-beautiful-dnd chart.js react-chartjs-2

# Create your components
# (Copy components from your design)
```

### Step 2: Configure for Your Domain

**In frontend/.env:**

```
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_DOMAIN=https://yourdomain.com
```

### Step 3: Build for Production

```bash
# Create production build
npm run build

# This creates a 'build' folder with all static files
```

### Step 4: Upload to Hostinger

**Via SSH, create frontend directory:**

```bash
# On Hostinger
mkdir ~/public_html/web

# Then upload build files
# Method 1: Using SCP from your computer
scp -r C:\path\to\frontend\build/* username@yourdomain.com:~/public_html/web/

# Method 2: Via Hostinger File Manager
# 1. Go to Hostinger → File Manager
# 2. Upload all files from build/ folder to public_html/web/
```

### Step 5: Configure Web Server

**In Hostinger Hpanel:**

1. Go to Domains → Your domain
2. Point main domain to public_html/web
3. Verify DNS settings are correct

---

## 🔗 Connect Frontend to Backend

**In frontend/src/services/api.js:**

```javascript
const API_URL = process.env.REACT_APP_API_URL || 'https://api.yourdomain.com';

export const loginUser = async (username, password) => {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  });
  
  if (!response.ok) {
    throw new Error('Login failed');
  }
  
  return response.json();
};

export const getLeads = async () => {
  const response = await fetch(`${API_URL}/api/leads`);
  if (!response.ok) {
    throw new Error('Failed to fetch leads');
  }
  return response.json();
};

// Add more API functions...
```

---

## 🚀 Week 5-6: Test & Go Live

### Local Testing

**Before deploying:**

```bash
# Start backend locally
python main.py

# In another terminal, start frontend
npm start

# Test all functionality
# Test login
# Test adding leads
# Test Kanban board
# Test analytics
```

### On Hostinger Testing

**After uploading:**

1. Visit yourdomain.com
2. Try to log in
3. Check browser console for errors
4. Check Hostinger logs for backend errors

**Access Hostinger Logs:**
```bash
# SSH into server
ssh username@yourdomain.com

# View application logs
tail -f ~/arthainvest-crm/gunicorn.log
```

### SSL Certificate (HTTPS)

**Hostinger includes free SSL:**
1. Go to Hostinger → Domains → Your domain
2. Click "SSL Certificate"
3. Install (usually already installed)
4. Verify https://yourdomain.com works

---

## 🐛 Troubleshooting

### Problem: "Connection refused to database"
```
Solution:
1. Verify database is running (Hostinger dashboard)
2. Check .env has correct credentials
3. Verify firewall allows connection from your IP
4. Contact Hostinger support if database not accessible
```

### Problem: "Frontend can't connect to backend"
```
Solution:
1. Check CORS is enabled in FastAPI
2. Verify api.yourdomain.com DNS points to same server
3. Check backend is running (SSH in and check)
4. Use browser dev tools → Network tab to see request
```

### Problem: "502 Bad Gateway"
```
Solution:
1. Check gunicorn process is running
2. Check main.py has no syntax errors
3. Check .env variables are set
4. Restart the application
```

### Problem: "404 - Page not found"
```
Solution:
1. Verify React build was uploaded to correct folder
2. Check index.html exists in public_html/web
3. Setup .htaccess for React routing (see below)
```

**For React Routing (.htaccess):**

Create `public_html/web/.htaccess`:
```
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>
```

---

## 📊 Monitoring on Hostinger

### Check Running Processes

```bash
# SSH in and check
ps aux | grep gunicorn
ps aux | grep python

# If not running, start it
~/arthainvest-crm/start_app.sh &
```

### Monitor Logs

```bash
# Backend logs
tail -f ~/arthainvest-crm/gunicorn.log

# Hostinger error logs
tail -f /var/log/apache2/error.log

# Exit with Ctrl+C
```

### Restart Application

```bash
# Kill existing process
pkill -f gunicorn

# Start fresh
~/arthainvest-crm/start_app.sh &
```

---

## ✅ Success Checklist

**Week 1-2:**
- [ ] SSH access working
- [ ] Python installed on server
- [ ] PostgreSQL database created
- [ ] Data migrated from SQLite
- [ ] Connection test successful

**Week 2-3:**
- [ ] FastAPI backend running on Hostinger
- [ ] All API endpoints working
- [ ] Database queries returning data
- [ ] CORS configured correctly

**Week 3-4:**
- [ ] React frontend built
- [ ] Static files uploaded
- [ ] Domain pointing to frontend
- [ ] Frontend loads correctly

**Week 4-5:**
- [ ] Frontend connects to backend
- [ ] Login works
- [ ] Data displays on dashboard
- [ ] All features functional

**Week 5-6:**
- [ ] Full end-to-end testing complete
- [ ] SSL certificate active
- [ ] Monitoring setup
- [ ] Documentation ready
- [ ] **GO LIVE!** 🚀

---

## 🎯 Total Cost Breakdown

**Initial:**
- Your domain (already purchased): ✅
- Hostinger hosting (already purchased): ✅

**Ongoing:**
- Hostinger monthly: ₹300-500 (depends on plan)
- PostgreSQL database: Included with Hostinger
- SSL Certificate: FREE (Let's Encrypt)

**Total Monthly: ₹300-500** (very cheap!)

---

## 💡 Pro Tips for Hostinger

1. **Use SSH, not FTP** - Faster and more reliable for code deployment
2. **Monitor disk space** - Keep an eye on file storage
3. **Enable auto-backups** - Set up in Hostinger → Backups
4. **Use .env files** - Never hardcode database credentials
5. **Keep Python updated** - Request latest version from Hostinger
6. **Setup uptime monitoring** - Hostinger has monitoring tools built-in

---

## 📞 Hostinger Support

**When to contact Hostinger:**
- SSH access issues
- Database creation/connectivity
- Python installation
- Domain/DNS configuration
- SSL certificate problems

**Email:** support@hostinger.com (available 24/7)
**Response time:** Usually 1-4 hours

---

## 🚀 You're Ready!

You now have:
✅ A clear step-by-step plan
✅ Code examples ready to use
✅ Hostinger-specific guidance
✅ Troubleshooting solutions
✅ Success metrics to track

**Start with Week 1 today!**

---

*Last Updated: August 20, 2026*
*For: ArthaInvest CRM on Hostinger*
