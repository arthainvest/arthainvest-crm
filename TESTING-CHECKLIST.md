# ArthaInvest CRM - Local Testing Checklist

## 🎯 Interactive Testing Execution

**Your Mission:** Execute all 10 testing phases on your local machine, validate outputs, and sign off.

**Duration:** 45-90 minutes  
**Start Time:** _______________  
**Target End Time:** _______________

---

## Pre-Testing Setup (2 minutes)

### ✓ Checklist Item 1: Terminal Ready
- [ ] Open terminal/command prompt
- [ ] Navigate to project: `cd ~/arthainvest-crm`
- [ ] Verify current directory: `pwd` (should end with `/arthainvest-crm`)

**Command:**
```bash
pwd
```

**Expected:** `/Users/[user]/arthainvest-crm` or `C:\Users\...\CRM_APP`

---

### ✓ Checklist Item 2: Docker Verification
- [ ] Docker installed and running
- [ ] Docker Compose available

**Commands:**
```bash
docker --version
docker-compose --version
```

**Expected:**
```
Docker version 20.10.x or higher
Docker Compose version 1.29.x or higher
```

**Status:** ☐ Pass ☐ Fail

---

## Phase 1: Environment Setup (5 minutes)

### ✓ Step 1.1: Verify .env.local
- [ ] .env.local file exists
- [ ] Contains all required settings

**Command:**
```bash
cat .env.local
```

**Check for these lines:**
- [ ] `NODE_ENV=development`
- [ ] `DB_HOST=postgres`
- [ ] `DB_PASSWORD=local_dev_password_123`
- [ ] `JWT_SECRET=` (has a value)

**Status:** ☐ Pass ☐ Fail

---

## Phase 2: Docker Stack Startup (15 minutes)

### ✓ Step 2.1: Build Docker Images
- [ ] Started build
- [ ] No build errors

**Command:**
```bash
docker-compose build
```

**Watch for:**
- ✓ `[+] Building ...`
- ✓ `(XX/XX) FINISHED`
- ✓ `Successfully tagged`

**Time taken:** _______ minutes

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 2.2: Start Services
- [ ] All 3 services started

**Command:**
```bash
docker-compose up -d
```

**Expected output:**
```
Creating arthainvest-postgres ... done
Creating arthainvest-crm-app ... done
Creating arthainvest-nginx ... done
```

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 2.3: Verify Service Status
- [ ] All services show "Up (healthy)"

**Command:**
```bash
docker-compose ps
```

**Expected output:**
```
NAME                   STATUS
arthainvest-postgres   Up (healthy)
arthainvest-crm-app    Up (healthy)
arthainvest-nginx      Up (healthy)
```

**Check each:**
- [ ] PostgreSQL: Up (healthy)
- [ ] App: Up (healthy)
- [ ] Nginx: Up (healthy)

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 2.4: Wait for App Startup
- [ ] App is ready (wait 30-60 seconds)

**Command:**
```bash
docker-compose logs app | tail -20
```

**Look for:**
```
[INFO] Server listening on port 3000
[INFO] Server ready at http://localhost:3000
```

**Status:** ☐ Pass ☐ Fail

---

## Phase 3: Database Verification (5 minutes)

### ✓ Step 3.1: Test DB Connection
- [ ] Database responds

**Command:**
```bash
docker-compose exec postgres psql -U arthainvest -d arthainvest_crm -c "SELECT 1"
```

**Expected:**
```
 ?column? 
----------
        1
(1 row)
```

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 3.2: Verify Schema
- [ ] Tables exist

**Command:**
```bash
docker-compose exec postgres psql -U arthainvest -d arthainvest_crm -c "\dt"
```

**Expected:** List of tables (minimum 4+)
- [ ] leads table exists
- [ ] deals table exists
- [ ] clients table exists
- [ ] users table exists

**Number of tables found:** _______

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 3.3: Database Backup Test
- [ ] Can create backup

**Command:**
```bash
docker-compose exec postgres pg_dump -U arthainvest arthainvest_crm > /tmp/test_backup.sql && echo "✓ Backup successful"
```

**Expected:**
```
✓ Backup successful
```

**Status:** ☐ Pass ☐ Fail

---

## Phase 4: API Health Checks (5 minutes)

### ✓ Step 4.1: Health Endpoint
- [ ] App responds to health check

**Command:**
```bash
curl -s http://localhost:3000/health | jq . 2>/dev/null || curl -s http://localhost:3000/health
```

**Expected:** JSON response with `"status": "healthy"`

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 4.2: Response Time
- [ ] Response time < 100ms

**Command:**
```bash
curl -s -o /dev/null -w "Response time: %{time_total} seconds\n" http://localhost:3000/health
```

**Expected:**
```
Response time: 0.045 seconds (or similar, < 0.1)
```

**Actual response time:** _______ seconds

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 4.3: CORS Headers
- [ ] CORS properly configured

**Command:**
```bash
curl -s -I http://localhost:3000/health | grep -i "access-control"
```

**Expected:** Headers present (at least one line)

**Status:** ☐ Pass ☐ Fail

---

## Phase 5: API Endpoints Testing (10 minutes)

### ✓ Step 5.1: Leads Endpoint
- [ ] Returns valid JSON

**Command:**
```bash
curl -s http://localhost:3000/api/leads \
  -H "Content-Type: application/json" | jq . 2>/dev/null || curl -s http://localhost:3000/api/leads
```

**Expected:** JSON with `"data": []` or similar

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 5.2: Analytics Endpoint
- [ ] Returns analytics data

**Command:**
```bash
curl -s http://localhost:3000/api/analytics/routing \
  -H "Content-Type: application/json" | jq . 2>/dev/null || curl -s http://localhost:3000/api/analytics/routing
```

**Expected:** JSON response with routing metrics

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 5.3: Dashboard HTML
- [ ] Dashboard page loads

**Command:**
```bash
curl -s http://localhost:3000/ | head -10
```

**Expected:** HTML content starting with `<!DOCTYPE` or `<html>`

**Status:** ☐ Pass ☐ Fail

---

## Phase 6: Features Testing (10 minutes)

### ✓ Step 6.1: Open Dashboard in Browser
- [ ] Navigate to http://localhost:3000
- [ ] Dashboard loads without errors
- [ ] Sidebar visible
- [ ] KPI cards displayed

**Open in browser:**
```
http://localhost:3000
```

**Visual checklist:**
- [ ] Page title: "ArthaInvest CRM"
- [ ] No red error boxes
- [ ] Navigation sidebar visible
- [ ] Dashboard content loads

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 6.2: Auto-Lead Routing Feature
- [ ] Feature endpoint accessible

**Command:**
```bash
curl -s -X POST http://localhost:3000/api/leads/score \
  -H "Content-Type: application/json" \
  -d '{"lead_id": 1}' | jq . 2>/dev/null || echo "Endpoint not yet implemented"
```

**Expected:** Either JSON response OR "not yet implemented" (both are OK)

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 6.3: Predictive Analytics
- [ ] Feature endpoint accessible

**Command:**
```bash
curl -s http://localhost:3000/api/analytics/predictions 2>/dev/null | jq . || echo "Feature not yet implemented"
```

**Expected:** Either JSON response OR "not yet implemented" (both are OK)

**Status:** ☐ Pass ☐ Fail

---

## Phase 7: Performance Validation (5 minutes)

### ✓ Step 7.1: Response Time Benchmark
- [ ] All 10 requests complete
- [ ] All < 200ms

**Command:**
```bash
for i in {1..10}; do 
  curl -s -o /dev/null -w "Request $i: %{time_total}s\n" http://localhost:3000/health
done
```

**Expected:** 10 responses, all < 0.2 seconds

**Results:**
```
Request 1: _____ s
Request 2: _____ s
Request 3: _____ s
Request 4: _____ s
Request 5: _____ s
Request 6: _____ s
Request 7: _____ s
Request 8: _____ s
Request 9: _____ s
Request 10: _____ s
```

**Average:** _______ seconds

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 7.2: Resource Usage
- [ ] Memory usage acceptable
- [ ] CPU usage acceptable

**Command:**
```bash
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

**Expected:** CPU < 5%, Memory < 1GB total

**Results:**
```
arthainvest-postgres:  CPU _____, Memory _____
arthainvest-crm-app:   CPU _____, Memory _____
arthainvest-nginx:     CPU _____, Memory _____
```

**Status:** ☐ Pass ☐ Fail

---

## Phase 8: Monitoring & Logging (5 minutes)

### ✓ Step 8.1: App Logs
- [ ] No critical errors

**Command:**
```bash
docker-compose logs app | grep -i "error\|fatal\|crash" | wc -l
```

**Expected:** 0 (zero errors)

**Errors found:** _______

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 8.2: Database Logs
- [ ] No critical errors

**Command:**
```bash
docker-compose logs postgres | grep -i "error" | wc -l
```

**Expected:** 0 (zero errors)

**Errors found:** _______

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 8.3: Nginx Logs
- [ ] No 500 errors

**Command:**
```bash
docker-compose logs nginx | grep "500" | wc -l
```

**Expected:** 0 (zero 500 errors)

**500 errors found:** _______

**Status:** ☐ Pass ☐ Fail

---

## Phase 9: Rollback Verification (5 minutes)

### ✓ Step 9.1: Graceful Shutdown
- [ ] Services stop cleanly

**Command:**
```bash
docker-compose down
```

**Expected:**
```
Stopping arthainvest-nginx ... done
Stopping arthainvest-crm-app ... done
Stopping arthainvest-postgres ... done
```

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 9.2: Restart Services
- [ ] Services come back up
- [ ] Data persists

**Command:**
```bash
docker-compose up -d
sleep 30
docker-compose ps
```

**Expected:** All services "Up (healthy)"

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 9.3: Data Persistence
- [ ] Database schema still intact

**Command:**
```bash
docker-compose exec postgres psql -U arthainvest -d arthainvest_crm -c "\dt" | wc -l
```

**Expected:** Same number of tables as before (should be ~9 or more)

**Tables found:** _______

**Status:** ☐ Pass ☐ Fail

---

## Phase 10: Production Readiness (5 minutes)

### ✓ Step 10.1: Security Check
- [ ] No insecure defaults

**Command:**
```bash
grep -r "change_me_in_production" .env* 2>/dev/null || echo "✓ No insecure defaults found"
```

**Expected:**
```
✓ No insecure defaults found
```

**Status:** ☐ Pass ☐ Fail

---

### ✓ Step 10.2: Configuration Valid
- [ ] docker-compose.yml is valid

**Command:**
```bash
docker-compose config > /dev/null && echo "✓ Configuration valid"
```

**Expected:**
```
✓ Configuration valid
```

**Status:** ☐ Pass ☐ Fail

---

## 📊 Test Summary

### Phase Completion

| Phase | Status | Issues |
|-------|--------|--------|
| 1: Environment | ☐ Pass ☐ Fail | __________ |
| 2: Stack Startup | ☐ Pass ☐ Fail | __________ |
| 3: Database | ☐ Pass ☐ Fail | __________ |
| 4: API Health | ☐ Pass ☐ Fail | __________ |
| 5: Endpoints | ☐ Pass ☐ Fail | __________ |
| 6: Features | ☐ Pass ☐ Fail | __________ |
| 7: Performance | ☐ Pass ☐ Fail | __________ |
| 8: Logging | ☐ Pass ☐ Fail | __________ |
| 9: Rollback | ☐ Pass ☐ Fail | __________ |
| 10: Readiness | ☐ Pass ☐ Fail | __________ |

---

## 🎯 Overall Result

### All Phases Passed?

- [ ] **YES - All 10 phases passed!** ✅
- [ ] **NO - Some phases failed** ❌

### If All Passed:

You are **READY FOR PRODUCTION DEPLOYMENT**

Next step: Follow **DEPLOYMENT-TIMELINE.md** for 6-8 hour production deployment

### If Any Failed:

Check troubleshooting in:
- TESTING-EXECUTION-WALKTHROUGH.md (detailed guide)
- LOCAL-TESTING-GUIDE.md (reference)

Then retest the failed phase(s)

---

## 📝 Sign-Off

### Test Execution Details

**Test Start Time:** _______________  
**Test End Time:** _______________  
**Total Duration:** _______________  

**Tested By:** _______________  
**Date:** _______________  

**Critical Issues Found:** 
```
☐ None
☐ Minor (doesn't block production)
☐ Major (needs fixing before production)
```

**Issue Details (if any):**
```
_________________________________________________________________

_________________________________________________________________

_________________________________________________________________
```

### Approval to Proceed to Production

- [ ] **I confirm all tests passed ✓**
- [ ] **I am ready to proceed with production deployment**
- [ ] **I understand the 6-8 hour timeline**
- [ ] **I have reviewed DEPLOYMENT-TIMELINE.md**

**Signed:** _______________

**Date:** _______________

---

## 🚀 Next Step

### If All Tests Passed:

```bash
# You're ready for production!
# Open and follow:
cat DEPLOYMENT-TIMELINE.md

# Then run deployment phases:
# T-24H: Preparation
# T-60m: Pre-checks
# T+0-4H: Deployment
# T+4-24H: Monitoring
```

### Timeline for Production:
- **Preparation:** 24 hours before
- **Deployment:** 6-8 hours (T+0 to T+360)
- **Monitoring:** 24 hours (T+360 to T+1440)
- **Total:** 48+ hours

---

**Status: Ready for Testing**  
**Last Updated:** 2024-08-16  
**Version:** 1.0

