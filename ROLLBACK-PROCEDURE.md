# Rollback Procedure Guide

## Overview

**Purpose:** Quickly revert to previous stable version if deployment fails  
**Estimated Duration:** 15-30 minutes  
**Data Loss Risk:** NONE (database backed up before deployment)  
**Required Approvals:** Manager + Deployment Lead  

---

## 🚨 When to Rollback

**Automatic Rollback Triggers:**

| Condition | Severity | Action |
|-----------|----------|--------|
| Cannot start containers | CRITICAL | Immediate rollback |
| Database migration fails | CRITICAL | Immediate rollback |
| >50% API endpoints return 500 | CRITICAL | Immediate rollback |
| SSL certificate invalid | CRITICAL | Immediate rollback |
| Cannot access database | CRITICAL | Immediate rollback |
| Data corruption detected | CRITICAL | Immediate rollback |
| CPU stuck at 100% | HIGH | Wait 5 min, then rollback |
| Memory exhausted | HIGH | Immediate rollback |
| Disk space < 1GB | HIGH | Immediate rollback |
| Application crashes repeatedly | HIGH | Immediate rollback |

**Manual Rollback Triggers:**

| Condition | Decision | Action |
|-----------|----------|--------|
| Critical security bug found | Manager decision | Rollback |
| Major feature broken | Manager decision | Rollback |
| User access impacted | Manager decision | Rollback |
| Business logic error | Manager decision | Rollback |
| Data loss risk detected | Tech Lead decision | Immediate rollback |

---

## 📋 Rollback Decision Process

### **Step 1: Assess the Issue (5 minutes)**

```
1. What is the problem?
   ☐ Application won't start
   ☐ Database unreachable
   ☐ High error rate (>10%)
   ☐ Performance degraded (>5x slower)
   ☐ Specific feature broken
   ☐ Other: _________________

2. Can it be fixed quickly?
   ☐ YES - Fix in place (< 15 min fix time expected)
   ☐ NO  - Proceed with rollback

3. Is data at risk?
   ☐ YES - Immediate rollback
   ☐ NO  - Assess further

4. Impact to users?
   ☐ Critical (complete outage)
   ☐ High (major features down)
   ☐ Medium (some features down)
   ☐ Low (minor issues)
```

### **Step 2: Get Approval**

```bash
# Contact required approvers
echo "ROLLBACK DECISION REQUIRED" | mail -s "URGENT" manager@arthainvestcapital.com

# Required approvals:
# [ ] Manager approval
# [ ] Deployment Lead approval
# [ ] If data loss risk: Tech Lead approval
```

### **Step 3: Announce Rollback**

```bash
# Notify team
curl -X POST "$SLACK_WEBHOOK" -d '{
  "text": "🚨 ROLLING BACK: [Reason]",
  "attachments": [{
    "color": "danger",
    "title": "Deployment Rollback Initiated",
    "text": "Issue: [Problem Description]\nETA: 15-30 minutes"
  }]
}'

# Update status page (if applicable)
echo "Status: Rolling back to previous version" > status.txt
```

---

## ✅ Rollback Execution

### **Phase 1: Stop Current Deployment (2 minutes)**

```bash
# SSH into production server
ssh deploy@arthainvestcapital.com
cd ~/arthainvest-crm

# Stop all containers
docker-compose down

# Verify stopped
docker-compose ps
# Should show no containers running

# Log the rollback
echo "[$(date)] ROLLBACK STARTED - Previous deployment failed" >> rollback.log
```

**Verification:**
- [ ] All containers stopped
- [ ] No processes running on ports 3000, 5432, 80, 443
- [ ] Rollback logged

---

### **Phase 2: Verify Backup (3 minutes)**

```bash
# Check available backups
ls -lh backups/db_backup_*.sql.gz

# Expected output: Multiple backup files with timestamps
# Pick the MOST RECENT backup created BEFORE failed deployment

ROLLBACK_BACKUP=$(ls -t backups/db_backup_*.sql.gz | head -1)
echo "Using backup: $ROLLBACK_BACKUP" >> rollback.log

# Verify backup integrity
sha256sum -c $ROLLBACK_BACKUP.sha256
# Must show: OK

# Check backup size (should be reasonable)
du -h $ROLLBACK_BACKUP
# Typical: 50MB - 500MB
```

**Verification:**
- [ ] Backup file exists
- [ ] Checksum validates
- [ ] Backup size reasonable
- [ ] Backup timestamp noted

---

### **Phase 3: Restore Database (10-20 minutes)**

```bash
# Start only PostgreSQL
docker-compose up -d postgres
sleep 10

# Wait for database to be ready
docker-compose exec -T postgres pg_isready -U arthainvest
# Should show: accepting connections

# Drop current database
echo "Dropping current database..."
docker-compose exec -T postgres dropdb -U arthainvest arthainvest_crm --if-exists

# Create fresh database
echo "Creating fresh database..."
docker-compose exec -T postgres createdb -U arthainvest arthainvest_crm

# Restore from backup
echo "Restoring from backup: $ROLLBACK_BACKUP"
docker-compose exec -T postgres psql -U arthainvest arthainvest_crm < $ROLLBACK_BACKUP

# Verify restoration
docker-compose exec -T postgres psql -U arthainvest -d arthainvest_crm -c "SELECT count(*) FROM information_schema.tables;"
# Should return > 0 (tables exist)

echo "[$(date)] Database restored successfully" >> rollback.log
```

**Verification:**
- [ ] PostgreSQL running
- [ ] Old database dropped
- [ ] New database created
- [ ] Backup data restored
- [ ] Tables exist in restored database

---

### **Phase 4: Restore Previous Application Version**

```bash
# Option A: Revert to previous Git commit
echo "Reverting to previous stable version..."
git log --oneline -5 > /tmp/recent_commits.log

# Check out previous version
git checkout HEAD~1  # Previous commit

# Verify code is correct
git log --oneline -2
```

**OR**

```bash
# Option B: Use previous Docker image (if still available)
docker images | grep arthainvest/crm-app

# Use previous tag
docker-compose.yml: image: arthainvest/crm-app:previous-stable-tag
```

---

### **Phase 5: Rebuild & Restart (5-10 minutes)**

```bash
# Rebuild Docker images
docker-compose build --pull app

# Start all services
docker-compose up -d

# Wait for startup
sleep 15

# Verify all containers running
docker-compose ps

# All should show "Up" status
```

**Verification:**
- [ ] Docker image rebuilt
- [ ] All 3 containers running
- [ ] No restart loops
- [ ] No error patterns in logs

---

### **Phase 6: Verify Rollback Success (5 minutes)**

```bash
# Check application health
curl -s http://localhost:3000/health
# Should respond: healthy

# Test key endpoints
curl -s http://localhost:3000/api/leads | jq . | head -20
curl -s http://localhost:3000/api/analytics/routing | jq . | head -20

# Database connectivity
docker-compose exec -T postgres pg_isready -U arthainvest
# Should return: accepting connections

# Check logs
docker-compose logs --tail=50 app | grep -i "error" | head -10
# Should show NONE or very few errors

# Performance check
for i in {1..3}; do
    RESPONSE=$(curl -s -o /dev/null -w "%{time_total}" http://localhost:3000/health)
    echo "Response time: ${RESPONSE}s"
done
# All should be < 500ms
```

**Verification Checklist:**
- [ ] Application responding
- [ ] API endpoints accessible
- [ ] Database connected
- [ ] No critical errors in logs
- [ ] Response times normal
- [ ] Previous data intact

---

## 📊 Verification Checklist

**Rollback Complete When:**

```
☑ Docker containers all running
☑ Application responds to /health
☑ Database connected and populated
☑ API endpoints returning 2xx status
☑ No "error" patterns in recent logs
☑ Response times < 500ms
☑ Nginx reverse proxy working
☑ Previous data visible in application
☑ Dashboard loads without errors
☑ User can log in successfully
```

---

## 🔄 Post-Rollback Actions

### **Step 1: Verify User Access (10 minutes)**

```bash
# Test login
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin_password"}'

# Should return JWT token

# Access dashboard
curl -s http://localhost:3000/analytics-dashboard.html | grep -q "Dashboard" && echo "✓ Dashboard accessible" || echo "✗ Dashboard error"

# Verify data
docker-compose exec -T postgres psql -U arthainvest -d arthainvest_crm -c "SELECT count(*) FROM leads;" 
# Should show number of leads
```

### **Step 2: Document Rollback (5 minutes)**

```bash
# Create rollback report
cat > rollback_report_$(date +%Y%m%d_%H%M%S).txt << EOF
ROLLBACK REPORT
===============
Date: $(date)
Reason: [Describe what went wrong]
Triggered By: [Name]
Approved By: [Name]

Previous Version: $(git rev-parse HEAD)
Backup Used: $ROLLBACK_BACKUP
Database Records Restored: [Count]

Timeline:
- Decision Time: T+[X] minutes after deployment start
- Rollback Start: $(date)
- Database Restore: [Duration]
- Container Restart: [Duration]
- Verification: [Status]
- Completion Time: $(date)

Status: ☑ Successful / ☐ Partial / ☐ Failed

Next Steps:
1. Investigate root cause
2. Schedule post-mortem
3. Plan fixes for next attempt
4. Team notification

Signed:
Deployment Lead: _________________ Date: _______
Manager: ________________________ Date: _______
EOF

echo "Rollback report generated"
```

### **Step 3: Notify Stakeholders**

```bash
# Slack notification
curl -X POST "$SLACK_WEBHOOK" -d '{
  "text": "✅ ROLLBACK SUCCESSFUL",
  "attachments": [{
    "color": "good",
    "title": "Deployment Rolled Back",
    "text": "System restored to previous stable version.\nData integrity verified.\nAll services operational.",
    "fields": [
      {"title": "Duration", "value": "[X] minutes"},
      {"title": "Root Cause", "value": "[Brief description]"},
      {"title": "Status", "value": "Fully Operational"}
    ]
  }]
}'

# Email notification
cat << EOF | mail -s "Deployment Rollback Complete" team@arthainvestcapital.com
DEPLOYMENT ROLLBACK COMPLETE

The deployment has been successfully rolled back to the previous stable version.

Status: All systems operational
Data: Fully restored
Users: Can access normally

Next Steps:
- Investigating root cause
- Post-mortem scheduled for [Date/Time]
- New deployment plan being developed

Questions? Contact: [Support Contact]
EOF
```

---

## 🔍 Root Cause Investigation

**After Rollback Completes:**

```bash
# Collect diagnostic data
mkdir -p rollback_diagnostics

# Collect logs
docker-compose logs app > rollback_diagnostics/app_logs.txt 2>&1
docker-compose logs postgres > rollback_diagnostics/postgres_logs.txt 2>&1
docker-compose logs nginx > rollback_diagnostics/nginx_logs.txt 2>&1

# System info
docker-compose ps > rollback_diagnostics/container_status.txt
docker stats --no-stream > rollback_diagnostics/resource_usage.txt
df -h > rollback_diagnostics/disk_space.txt

# Git info
git log --oneline -10 > rollback_diagnostics/git_log.txt
git status > rollback_diagnostics/git_status.txt

# Archive diagnostics
tar -czf rollback_diagnostics_$(date +%Y%m%d_%H%M%S).tar.gz rollback_diagnostics/
```

**Investigation Questions:**
```
1. What was the deployment change?
   - Which files were modified?
   - Which dependencies were updated?
   - Database migrations run?

2. When did it fail?
   - During build?
   - During startup?
   - During first request?
   - After period of time?

3. What were the error messages?
   - Docker build errors?
   - Application startup errors?
   - Database errors?
   - Network errors?

4. What was the impact?
   - Immediate failure?
   - Gradual degradation?
   - Intermittent errors?
   - Complete outage?

5. What can be fixed?
   - Configuration issue? (fix and retry)
   - Code issue? (require code review)
   - Dependency issue? (rollback dependency)
   - Migration issue? (review migration logic)
```

---

## ⚠️ Rollback Complications

### **If Database Restore Fails**

```bash
# Backup is corrupted or incompatible
# ACTION: Try earlier backup

# List earlier backups
ls -lt backups/db_backup_*.sql.gz | head -10

# Use second-most-recent backup
EARLIER_BACKUP=$(ls -t backups/db_backup_*.sql.gz | sed -n '2p')
echo "Trying earlier backup: $EARLIER_BACKUP"

# Repeat database restore with earlier backup
docker-compose exec -T postgres dropdb -U arthainvest arthainvest_crm
docker-compose exec -T postgres createdb -U arthainvest arthainvest_crm
docker-compose exec -T postgres psql -U arthainvest arthainvest_crm < $EARLIER_BACKUP

# If all backups fail:
# → Contact database admin immediately
# → Consider recovery service
# → Determine data loss window
```

### **If Previous Docker Image Not Available**

```bash
# Need to rebuild previous version
git checkout [previous-stable-commit]
docker-compose build app

# If that fails:
# → Check Git history for working commit
# → May need to skip a version
# → Last resort: rebuild from known-good branch
```

### **If Containers Won't Start**

```bash
# Remove containers and try again
docker-compose down -v  # -v removes volumes (careful!)
docker-compose up -d

# Check logs for specific errors
docker-compose logs app | tail -100

# If still fails:
# → Manually start PostgreSQL first
# → Debug app connection issues
# → Check network configuration
# → May need to restore from snapshot
```

### **If Disk Space is Critical**

```bash
# Emergency cleanup
rm -rf backup files older than rollback backup

# Remove old Docker images
docker image prune -a -f

# Clean up logs
truncate -s 0 logs/*.log

# Check disk space
df -h
# Must have > 500MB free before retry
```

---

## 🔄 Retry After Rollback

**After Root Cause Fixed:**

1. **Code Review (24 hours)**
   - Review problematic code change
   - Identify the bug
   - Fix and test locally
   - Get peer review

2. **Staging Test (Before Retry)**
   - Deploy to staging environment
   - Run full test suite
   - Load test
   - Security scan

3. **Careful Retry**
   - Monitor intensively
   - Smaller deployment window
   - Extra checkpoints
   - Faster rollback ready

---

## 📞 Emergency Escalation

**If Rollback Fails:**

```
1. STOP all remediation attempts
2. Escalate to:
   - CTO/VP Engineering
   - Database team lead
   - Infrastructure team
3. Initiate:
   - Data recovery service
   - Incident management team
   - Communication to all stakeholders
4. Do NOT:
   - Make additional changes
   - Attempt recovery without expertise
   - Assume data is lost
```

**Emergency Contact:**
- On-Call: [Phone]
- CTO: [Email]
- Escalation: [Procedure]

---

## ✅ Post-Rollback Checklist

```
ROLLBACK COMPLETION:
☑ All containers running
☑ Database verified
☑ Data integrity confirmed
☑ Users can access system
☑ Stakeholders notified
☑ Team assembled for post-mortem
☑ Diagnostics collected
☑ Rollback report written
☑ Root cause identified
☑ Fix planned for retry

TIME TO RECOVER: [Document actual time]
DATA LOSS: NONE (verified)
USER IMPACT: [Describe outage window]
```

---

**Rollback Authorized By:** _____________________ Date: _______  
**Rolled Back By:** ______________________________ Time: _______  
**Verified By:** ________________________________ Time: _______

