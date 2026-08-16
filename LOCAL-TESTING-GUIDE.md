# Local Testing Guide - ArthaInvest CRM v3.0

## Pre-Deployment Validation Checklist

**Purpose:** Verify all components work correctly in a local environment before production deployment.  
**Estimated Time:** 30-60 minutes  
**Requirements:** Docker, Docker Compose, curl, Node.js 16+

---

## ✅ Step 1: Environment Setup (5 minutes)

### 1.1 Verify Prerequisites

```bash
# Check Docker
docker --version
# Expected: Docker version 20.x or higher

# Check Docker Compose
docker-compose --version
# Expected: Docker Compose version 1.29.x or higher

# Check Node.js
node --version
# Expected: Node v16.x or higher
```

### 1.2 Verify .env.local Configuration

```bash
cd ~/arthainvest-crm

# Check .env.local exists
cat .env.local
```

**Expected Contents:**
```
NODE_ENV=development
PORT=3000
DB_HOST=postgres
DB_USER=arthainvest
DB_PASSWORD=local_dev_password_123
DB_NAME=arthainvest_crm
JWT_SECRET=local_jwt_secret_key_for_testing_only_not_production
API_URL=http://localhost:3000
CORS_ORIGIN=http://localhost:3000,http://localhost
```

---

## ✅ Step 2: Docker Stack Startup (15 minutes)

### 2.1 Build Docker Images

```bash
# Build all images
docker-compose build

# Expected output:
# [+] Building 12.5s (25/25) FINISHED
# ✓ postgres built
# ✓ arthainvest-crm-app built
# ✓ arthainvest-nginx built
```

**Troubleshooting:**
- If build fails: `docker system prune -a` then rebuild
- If memory issues: Increase Docker Desktop memory limit to 4GB+

### 2.2 Start All Services

```bash
# Start services in background
docker-compose up -d

# Verify startup
docker-compose ps
```

**Expected Output:**
```
NAME                        IMAGE                     STATUS
arthainvest-postgres       postgres:15-alpine        Up (healthy)
arthainvest-crm-app        arthainvest-crm:latest    Up (healthy)
arthainvest-nginx          nginx:alpine              Up (healthy)
```

### 2.3 Monitor Startup (wait 30-60 seconds)

```bash
# Watch logs in real-time
docker-compose logs -f app

# Expected sequence:
# [INFO] Server starting...
# [INFO] Connecting to database...
# [INFO] Database connection established
# [INFO] Server listening on port 3000
# [INFO] All systems operational
```

**Stop watching logs:** Press `Ctrl+C`

---

## ✅ Step 3: Database Verification (5 minutes)

### 3.1 Test Database Connection

```bash
# Connect to PostgreSQL directly
docker-compose exec postgres psql -U arthainvest -d arthainvest_crm -c "SELECT 1"

# Expected: 
#  ?column? 
# ----------
#        1
# (1 row)
```

### 3.2 Verify Database Schema

```bash
# List all tables
docker-compose exec postgres psql -U arthainvest -d arthainvest_crm -c "\dt"

# Expected tables:
# leads
# deals
# clients
# users
# routing_history
# performance_metrics
# (at least 6+ core tables)
```

### 3.3 Database Health Check

```bash
# Run integrity check
docker-compose exec postgres pg_dump -U arthainvest arthainvest_crm > /dev/null && echo "✓ Database backup successful"

# Expected: ✓ Database backup successful
```

---

## ✅ Step 4: API Health Checks (5 minutes)

### 4.1 Health Endpoint

```bash
# Test basic health
curl -s http://localhost:3000/health | jq .

# Expected:
# {
#   "status": "healthy",
#   "timestamp": "2024-08-16T14:30:45Z",
#   "uptime": 45,
#   "database": "connected"
# }
```

### 4.2 Response Time Benchmark

```bash
# Measure response time
curl -s -o /dev/null -w "Response time: %{time_total}s\n" http://localhost:3000/health

# Expected: < 100ms (< 0.1s)
```

### 4.3 CORS Headers

```bash
# Verify CORS headers
curl -s -I http://localhost:3000/health | grep -i "access-control"

# Expected output:
# access-control-allow-origin: http://localhost:3000
# access-control-allow-methods: GET, POST, PUT, DELETE
# access-control-allow-headers: Content-Type, Authorization
```

---

## ✅ Step 5: API Endpoints Testing (10 minutes)

### 5.1 Leads Endpoint

```bash
# Get leads list
curl -s http://localhost:3000/api/leads \
  -H "Content-Type: application/json" | jq .

# Expected:
# {
#   "data": [],
#   "total": 0,
#   "page": 1,
#   "limit": 10
# }
```

### 5.2 Analytics Endpoint

```bash
# Get analytics/routing data
curl -s http://localhost:3000/api/analytics/routing \
  -H "Content-Type: application/json" | jq .

# Expected:
# {
#   "routing_metrics": {...},
#   "performance": {...},
#   "timestamp": "2024-08-16T14:30:45Z"
# }
```

### 5.3 Dashboard Data

```bash
# Get dashboard data
curl -s http://localhost:3000/api/dashboard \
  -H "Content-Type: application/json" | jq .

# Expected:
# {
#   "kpis": {...},
#   "recent_leads": [...],
#   "performance_summary": {...}
# }
```

### 5.4 Authentication

```bash
# Test login endpoint
curl -s -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin_password"}' | jq .

# Expected:
# {
#   "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "user": {"id": 1, "username": "admin"},
#   "expires_in": 3600
# }
```

---

## ✅ Step 6: Features Testing (10 minutes)

### 6.1 Auto-Lead Routing

```bash
# Test lead scoring
curl -s -X POST http://localhost:3000/api/leads/:id/score \
  -H "Content-Type: application/json" \
  -d '{"lead_id": 1}' | jq .

# Expected:
# {
#   "score": 85,
#   "factors": {
#     "product_specialization": 30,
#     "capacity": 20,
#     "performance": 15,
#     "geography": 15,
#     "quality": 20
#   },
#   "recommended_rep": "sales_rep_id"
# }
```

### 6.2 Predictive Analytics

```bash
# Get deal closure predictions
curl -s http://localhost:3000/api/analytics/predictions \
  -H "Content-Type: application/json" | jq .

# Expected:
# {
#   "deals": [...],
#   "closure_probability": {...},
#   "churn_risk": {...},
#   "recommendations": [...]
# }
```

### 6.3 Dashboard HTML

```bash
# Test dashboard loads
curl -s http://localhost:3000/ | grep -o "<title>.*</title>"

# Expected:
# <title>ArthaInvest CRM - Dashboard</title>
```

---

## ✅ Step 7: Performance Validation (5 minutes)

### 7.1 Load Test (Simple)

```bash
# Test with 10 sequential requests
for i in {1..10}; do
  curl -s -o /dev/null -w "Request $i: %{time_total}s\n" http://localhost:3000/health
done

# Expected: All < 200ms
```

### 7.2 Database Performance

```bash
# Measure database query time
time docker-compose exec postgres psql -U arthainvest -d arthainvest_crm -c "SELECT COUNT(*) FROM information_schema.tables"

# Expected: < 100ms
```

### 7.3 Container Resource Usage

```bash
# Check memory/CPU usage
docker stats --no-stream arthainvest-crm-app arthainvest-postgres

# Expected:
# arthainvest-crm-app    2.5%    450MB / 2GB    
# arthainvest-postgres   1.2%    200MB / 2GB    
```

---

## ✅ Step 8: Monitoring & Logging (5 minutes)

### 8.1 Application Logs

```bash
# Get last 50 lines of app logs
docker-compose logs app --tail 50

# Check for errors
docker-compose logs app | grep -i "error\|fatal\|crash"

# Expected: No CRITICAL errors (warnings OK)
```

### 8.2 Database Logs

```bash
# Check database logs
docker-compose logs postgres | grep -i "error"

# Expected: No critical errors
```

### 8.3 Nginx Logs

```bash
# Check reverse proxy logs
docker-compose logs nginx | tail -20

# Expected: 200 OK responses, no 500 errors
```

---

## ✅ Step 9: Rollback Verification (5 minutes)

### 9.1 Test Graceful Shutdown

```bash
# Stop services gracefully
docker-compose down

# Expected:
# Stopping arthainvest-nginx ... done
# Stopping arthainvest-crm-app ... done
# Stopping arthainvest-postgres ... done
# Removing networks ...
```

### 9.2 Test Data Persistence

```bash
# Restart services
docker-compose up -d

# Wait 30 seconds for startup
sleep 30

# Verify data still exists
docker-compose exec postgres psql -U arthainvest -d arthainvest_crm -c "SELECT COUNT(*) FROM information_schema.tables"

# Expected: Same number of tables as before
```

### 9.3 Volume Backup

```bash
# Verify backup was created
ls -lh ~/arthainvest-crm/backups/

# Expected: At least one .sql.gz file
```

---

## ✅ Step 10: Production Readiness Check (5 minutes)

### 10.1 Security Verification

```bash
# Check no default credentials in use
grep "change_me_in_production" .env.local
# Expected: No output (or only in .env.local)

# Verify JWT secret is set
grep "JWT_SECRET" .env.local | grep -v "local"
# Expected: Production secret (if testing prod config)
```

### 10.2 SSL Certificate Check

```bash
# Verify SSL directory
ls -la ssl/
# Expected: ssl certificates exist (for production)
```

### 10.3 Configuration Review

```bash
# Verify all required configs
docker-compose config | grep -E "image|ports|depends_on" | head -30

# Expected: All services configured correctly
```

---

## 📊 Test Results Summary Template

```
╔══════════════════════════════════════════════════════════╗
║  ArthaInvest CRM - Local Test Results                   ║
║  Date: [YYYY-MM-DD HH:MM:SS]                             ║
╚══════════════════════════════════════════════════════════╝

Phase 1: Environment Setup              [✓ PASS / ✗ FAIL]
Phase 2: Docker Stack Startup           [✓ PASS / ✗ FAIL]
Phase 3: Database Verification          [✓ PASS / ✗ FAIL]
Phase 4: API Health Checks              [✓ PASS / ✗ FAIL]
Phase 5: API Endpoints Testing          [✓ PASS / ✗ FAIL]
Phase 6: Features Testing               [✓ PASS / ✗ FAIL]
Phase 7: Performance Validation         [✓ PASS / ✗ FAIL]
Phase 8: Monitoring & Logging           [✓ PASS / ✗ FAIL]
Phase 9: Rollback Verification          [✓ PASS / ✗ FAIL]
Phase 10: Production Readiness          [✓ PASS / ✗ FAIL]

Overall Status: [✓ READY FOR PRODUCTION / ✗ ISSUES FOUND]

Test Coverage: __% (tests passed / total)
Duration: __m __s

Known Issues:
- [Issue 1]
- [Issue 2]

Sign-off:
Tested By: ________________  Date: __________
Verified By: _______________  Date: __________
```

---

## 🔧 Troubleshooting Guide

### Docker Build Fails

```bash
# Clear build cache
docker-compose build --no-cache

# Prune system
docker system prune -a -f

# Try again
docker-compose build
```

### Database Connection Fails

```bash
# Check PostgreSQL health
docker-compose exec postgres pg_isready -U arthainvest

# View database logs
docker-compose logs postgres | tail -30

# Restart database
docker-compose restart postgres
```

### App Won't Start

```bash
# Check app logs
docker-compose logs app

# Common issues:
# - Port 3000 already in use: lsof -i :3000 (macOS/Linux) or netstat -ano | findstr :3000 (Windows)
# - Database not ready: Wait 30-60 seconds after docker-compose up
# - Insufficient memory: docker-compose down && increase Docker memory limit
```

### API Endpoints Return 404

```bash
# Verify app is running
curl -s http://localhost:3000/health

# Check Nginx configuration
docker-compose exec nginx nginx -t

# View Nginx logs
docker-compose logs nginx
```

---

## 🚀 Next Steps After Testing

✅ **All Tests Pass?**
1. Review test results summary
2. Document any warnings
3. Proceed to PRODUCTION DEPLOYMENT (see DEPLOYMENT-TIMELINE.md)
4. Follow deployment timeline phases T-24H through T+1440M

❌ **Tests Failed?**
1. Review troubleshooting section
2. Fix identified issues
3. Run tests again
4. Document root causes
5. Get approval before proceeding

---

## 📝 Notes

- Keep this guide open during testing
- Document any issues encountered
- Save test results for audit trail
- Estimated total time: 45-90 minutes
- Do NOT proceed to production until all tests pass

---

**Local Testing Version:** 3.0.0  
**Last Updated:** 2024-08-16  
**Next Review:** After each deployment iteration

