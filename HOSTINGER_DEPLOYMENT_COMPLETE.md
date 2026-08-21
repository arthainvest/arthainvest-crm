# ArthaInvest CRM - Hostinger Deployment Guide

**Status**: ✅ Complete System Ready for Production  
**Date**: August 21, 2026  
**Components**: React Frontend + FastAPI Backend + SQLite → PostgreSQL

---

## 📋 Pre-Deployment Checklist

- [x] Frontend React app fully functional (localhost:3000)
- [x] Backend API operational (localhost:8000 / 13 endpoints)
- [x] Database initialized (SQLite with 4 tables)
- [x] Test data loaded (6 leads, 4 active deals)
- [x] Authentication working (JWT + bcrypt)
- [x] All pages tested (Dashboard, Leads, Pipeline)
- [x] Kanban drag-drop workflow validated
- [ ] Production build created
- [ ] Hostinger account configured
- [ ] PostgreSQL database provisioned
- [ ] Domain DNS configured
- [ ] SSL certificate installed

---

## 🎯 Deployment Steps

### Phase 1: Production Build (Local)

```bash
# Frontend build
cd C:\ArthaInvest\frontend
npm run build
# Output: build/ directory (ready for static hosting)

# Backend packaging
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest\backend
# Create requirements.txt
pip freeze > requirements-prod.txt
```

**Build Output:**
- `frontend/build/` → 5-20MB (optimized React bundle)
- `backend/main_sqlite.py` → Ready for import to PostgreSQL
- `backend/requirements-prod.txt` → 15+ dependencies

---

### Phase 2: Hostinger Configuration

#### 2.1 Hostinger Control Panel Setup

1. **Login to Hostinger**
   - Dashboard → Your Domain
   - Go to "File Manager"

2. **Create Project Structure**
   ```
   public_html/
   ├── crm/                (React build output)
   │   ├── index.html
   │   ├── static/
   │   └── favicon.ico
   ├── api/                (FastAPI backend)
   │   ├── main.py
   │   ├── database.py
   │   ├── auth.py
   │   └── requirements.txt
   └── .htaccess          (routing config)
   ```

#### 2.2 Upload Files

**Via FTP/File Manager:**
```
1. Upload frontend/build/* → public_html/crm/
2. Upload backend files → public_html/api/
3. Create .htaccess for routing
```

#### 2.3 .htaccess Configuration

```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  
  # React routing: send all requests to index.html
  RewriteBase /crm/
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule ^ index.html [QSA,L]
  
  # API CORS headers
  <IfModule mod_headers.c>
    Header set Access-Control-Allow-Origin "*"
    Header set Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS"
    Header set Access-Control-Allow-Headers "Content-Type, Authorization"
  </IfModule>
</IfModule>
```

---

### Phase 3: Database Migration (SQLite → PostgreSQL)

#### 3.1 Create PostgreSQL Database on Hostinger

1. **Hostinger Dashboard**
   - Databases → PostgreSQL
   - Create new database: `arthainvest_crm`
   - Note credentials: hostname, user, password, port

2. **Environment Variables**
   ```bash
   # Create .env file in api/
   DB_HOST=your-hostinger-postgres-host.com
   DB_USER=arthainvest_user
   DB_PASSWORD=your-secure-password
   DB_NAME=arthainvest_crm
   DB_PORT=5432
   SECRET_KEY=your-secure-random-key
   ENVIRONMENT=production
   ```

#### 3.2 Migrate Data from SQLite to PostgreSQL

**Run migration script:**
```bash
python3 migrate_sqlite_to_postgres.py
# This reads arthainvest_crm.db and inserts into PostgreSQL
```

**Migration script** (`migrate_sqlite_to_postgres.py`):
```python
import sqlite3
import psycopg2

# Read from SQLite
sqlite_conn = sqlite3.connect('arthainvest_crm.db')
sqlite_cursor = sqlite_conn.cursor()

# Connect to PostgreSQL
pg_conn = psycopg2.connect(
    host="your-host",
    database="arthainvest_crm",
    user="arthainvest_user",
    password="your-password"
)
pg_cursor = pg_conn.cursor()

# Copy users
sqlite_cursor.execute("SELECT * FROM users")
for row in sqlite_cursor.fetchall():
    pg_cursor.execute(
        "INSERT INTO users VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        row
    )

# Copy leads, deals, activity_log similarly...
pg_conn.commit()
print("✓ Migration complete!")
```

---

### Phase 4: Backend Deployment

#### 4.1 Install Python & Dependencies

**SSH to Hostinger:**
```bash
ssh user@your-domain.com

# Install Python 3.9+
python3 --version

# Navigate to api directory
cd public_html/api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-prod.txt
```

#### 4.2 Configure Gunicorn (Production Server)

```bash
# Install gunicorn
pip install gunicorn

# Test startup
gunicorn -w 4 -b 0.0.0.0:8000 main:app

# Create startup script (startup.sh)
#!/bin/bash
cd /home/your-user/public_html/api
source venv/bin/activate
gunicorn -w 4 -b 127.0.0.1:8000 \
  --log-level info \
  --access-logfile access.log \
  --error-logfile error.log \
  main:app
```

#### 4.3 Configure Hostinger to Route API Calls

**In Hostinger Control Panel:**
- Proxy settings for `/api/` → `localhost:8000`
- Or use subdomain: `api.yourdomain.com` → direct to Gunicorn

---

### Phase 5: Frontend Configuration

#### 5.1 Update API Endpoint

**Edit `frontend/src/services/api.js`:**
```javascript
const API_URL = process.env.REACT_APP_API_URL || 'https://yourdomain.com/api';
// For production
```

**Create `.env.production`:**
```
REACT_APP_API_URL=https://yourdomain.com/api
REACT_APP_ENV=production
```

#### 5.2 Rebuild & Upload

```bash
npm run build
# Upload build/ folder contents to public_html/crm/
```

---

### Phase 6: SSL & Security

1. **Enable HTTPS** (Hostinger Auto SSL)
   - Control Panel → SSL Certificate
   - Enable AutoSSL (automatic renewal)

2. **Update Frontend URL**
   - Change `http://` → `https://` in all API calls

3. **Security Headers** (add to .htaccess)
   ```apache
   <IfModule mod_headers.c>
     Header set X-Content-Type-Options "nosniff"
     Header set X-Frame-Options "SAMEORIGIN"
     Header set X-XSS-Protection "1; mode=block"
     Header set Referrer-Policy "strict-origin-when-cross-origin"
   </IfModule>
   ```

---

## 🌐 Domain Routing

### DNS Configuration

**Hostinger DNS Records:**
```
Type  | Name     | Value                    | TTL
------|----------|--------------------------|-----
A     | @        | Your-Hostinger-IP       | 3600
A     | www      | Your-Hostinger-IP       | 3600
CNAME | api      | yourdomain.com          | 3600
```

### URL Structure (After Deployment)

```
Frontend:  https://yourdomain.com
API:       https://yourdomain.com/api
Admin:     https://yourdomain.com/admin (optional)
```

---

## 📊 Testing After Deployment

### Health Checks

```bash
# 1. Frontend loads
curl https://yourdomain.com
# Should return React app HTML

# 2. API health check
curl https://yourdomain.com/api/health
# Should return: {"status":"ok","message":"ArthaInvest API is running"}

# 3. Login test
curl -X POST https://yourdomain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"TestPass123"}'
# Should return access token

# 4. Load dashboard
curl https://yourdomain.com/api/analytics/dashboard?token=YOUR_TOKEN
# Should return KPI data
```

### Performance Monitoring

**Check via Hostinger:**
- CPU usage
- Memory consumption
- Disk space
- Bandwidth usage
- Error logs

---

## 🔧 Maintenance & Scaling

### Regular Tasks

**Weekly:**
- [ ] Check API error logs
- [ ] Monitor database size
- [ ] Verify backups running

**Monthly:**
- [ ] Review performance metrics
- [ ] Update dependencies
- [ ] Test login functionality

### Scaling Strategy

**When traffic increases:**
1. Upgrade Hostinger plan → more CPU/RAM
2. Add database replicas for read scaling
3. Implement Redis caching for API responses
4. Use CDN for static assets (Cloudflare free tier)

---

## 💰 Cost Breakdown

| Component | Hostinger Plan | Cost/Month | Notes |
|-----------|---|---|---|
| Web Hosting | Business/Premium | ₹300-500 | CPU, RAM, SSL included |
| Database | PostgreSQL add-on | ₹100-200 | Managed service |
| Email (optional) | Included | Free | Up to 300 accounts |
| Domain renewal | Annual | ₹400-600 | Your existing domain |
| **Total** | | **₹400-700** | Fully managed |

---

## 🚀 Quick Deploy Checklist

```
□ Frontend build created (npm run build)
□ Backend requirements.txt updated
□ .env file configured with Hostinger credentials
□ PostgreSQL database created on Hostinger
□ Data migrated from SQLite to PostgreSQL
□ Files uploaded to public_html/
□ Gunicorn running on Hostinger (port 8000)
□ API_URL updated in frontend (.env.production)
□ SSL certificate installed
□ Health checks passing
□ Test login working
□ Dashboard showing data
□ Live domain accessible
□ Team users invited
```

---

## 📞 Support & Troubleshooting

**Common Issues:**

| Issue | Solution |
|-------|----------|
| 404 on React routes | Check .htaccess RewriteRule configuration |
| API 401 Unauthorized | Verify token expiration, update SECRET_KEY |
| Database connection failed | Check .env credentials, verify PostgreSQL service running |
| CORS errors | Enable CORS headers in .htaccess |
| Slow performance | Check Hostinger resource usage, upgrade if needed |

---

## ✅ Deployment Complete!

Once all steps are finished:
- [ ] Production frontend live at yourdomain.com
- [ ] API serving at yourdomain.com/api
- [ ] PostgreSQL database backing system
- [ ] Team can access via web browser
- [ ] Mobile-friendly responsive design
- [ ] Automatic SSL/HTTPS
- [ ] Daily backups enabled

**Estimated Time:** 2-4 hours  
**Team Access:** Add via dashboard settings  
**Support:** Hostinger 24/7 chat support  

---

**Ready to deploy? Follow Phase 1-6 in order, and you'll have your CRM live!**
