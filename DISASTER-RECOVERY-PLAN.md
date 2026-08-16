# Disaster Recovery Plan (DRP)

## Executive Summary

**Recovery Time Objective (RTO):** 4 hours  
**Recovery Point Objective (RPO):** 1 hour (daily backups, max 1 hour data loss)  
**Disaster Categories:** Infrastructure, Data, Application, Security  
**Recovery Cost:** Minimal (automation-first approach)  
**Last Updated:** [DATE]  
**Next Review:** Quarterly  

---

## 📋 Disaster Scenarios

### **1. Database Corruption (RTO: 2 hours)**

**Symptoms:**
- Query errors on core tables
- Referential integrity violations
- Unexplained data inconsistencies
- Slow queries suddenly failing

**Immediate Response (0-15 min):**
```bash
# Step 1: Stop application
docker-compose down

# Step 2: Diagnose
docker-compose up -d postgres
docker-compose exec -T postgres pg_dump -U arthainvest arthainvest_crm | pg_restore -t table_name 2>&1 | head -50

# Step 3: Assess damage
docker-compose exec -T postgres psql -U arthainvest -d arthainvest_crm -c "SELECT pg_catalog.pg_database.datname, pg_catalog.pg_stat_user_tables.n_tup_ins, pg_catalog.pg_stat_user_tables.n_tup_upd, pg_catalog.pg_stat_user_tables.n_tup_del FROM pg_catalog.pg_database JOIN pg_catalog.pg_stat_user_tables ON pg_catalog.pg_database.datname = current_database();"
```

**Recovery Steps (15-120 min):**
```bash
# 1. List available backups (choose most recent before corruption)
ls -lh backups/db_backup_*.sql.gz

# 2. Restore from backup
docker-compose exec -T postgres dropdb -U arthainvest arthainvest_crm
docker-compose exec -T postgres createdb -U arthainvest arthainvest_crm  
docker-compose exec -T postgres psql -U arthainvest arthainvest_crm < backups/db_backup_20240115_020000.sql.gz

# 3. Verify tables
docker-compose exec -T postgres psql -U arthainvest -d arthainvest_crm -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"

# 4. Restart application
docker-compose up -d
```

**Follow-up (2+ hours):**
- Investigate cause of corruption
- Run VACUUM ANALYZE
- Check database logs
- Enable more aggressive backups if needed

---

### **2. Server Disk Full (RTO: 1 hour)**

**Symptoms:**
- "No space left on device" errors
- Docker build failures
- Database operations fail
- Log files stop being written

**Immediate Response (0-5 min):**
```bash
# Check disk
df -h /
# Alert if < 1GB free

# Stop non-critical services
docker-compose down nginx  # Keep app & DB

# Emergency cleanup
rm -rf /tmp/*
rm -rf ~/.cache
docker system prune -a -f  # Remove unused Docker data
find logs/ -type f -mtime +7 -delete  # Remove logs > 7 days old

# Verify space
df -h /
# Must have > 5GB free before restart
```

**Recovery (5-60 min):**
```bash
# Move large files if needed
du -sh /var/lib/docker/*
# Move old backups to external storage

# Restart services
docker-compose up -d nginx
```

---

### **3. Complete Server Failure (RTO: 4 hours)**

**If Server Becomes Unreachable:**

**Immediate (0-30 min):**
1. Contact hosting provider
2. Request server restart
3. Start recovery from backup

**If Restart Fails:**
1. Provision new server (same specs)
2. Install Docker & Docker Compose
3. Clone repository
4. Copy SSL certificates
5. Copy .env.production file

**Recovery (30-240 min):**
```bash
# On new server
git clone https://github.com/arthainvest/arthainvest-crm.git
cd arthainvest-crm
git checkout production

# Copy certificates & config
scp -r old-server:/path/to/ssl ./ssl
scp old-server:/path/to/.env.production ./.env.production

# Copy latest backup
scp old-server:/path/to/backups/db_backup_latest.sql.gz ./backups/

# Deploy
bash quick-deploy.sh
```

---

### **4. Data Breach / Security Incident (RTO: Immediate)**

**Immediate Actions (0-15 min):**
1. Isolate affected system
2. Disable compromised accounts
3. Revoke API tokens
4. Alert security team
5. Begin forensics

```bash
# Step 1: Disconnect application
docker-compose down

# Step 2: Preserve evidence
tar -czf /backup/incident_evidence_$(date +%Y%m%d_%H%M%S).tar.gz /var/lib/docker/volumes

# Step 3: Secure backups
cp -r backups/ /external/backup_evidence/

# Step 4: Change credentials
# - Database password
# - Jwt secrets (rotate all tokens)
# - GitHub deploy key
# - Docker registry credentials
```

**Recovery (15+ min depending on severity):**
```bash
# If data breached but system clean:
# 1. Restore from pre-breach backup (if available)
# 2. Or continue with current state + security patches

# If system compromised:
# 1. Full server rebuild
# 2. Database restore from known-good backup
# 3. Code audit for backdoors
```

---

### **5. Application Code Bug Causing Data Loss (RTO: 2 hours)**

**Example:** Unintended DELETE on all records

**Immediate (0-5 min):**
```bash
# STOP the application immediately
docker-compose down

# Preserve logs for forensics
cp -r logs/ /backup/incident_logs_$(date +%Y%m%d_%H%M%S)/

# Do NOT restart application
```

**Investigation (5-30 min):**
```bash
# Determine when deletion occurred
docker-compose up -d postgres
docker-compose exec -T postgres psql -U arthainvest -d arthainvest_crm

# Find most recent backup before deletion
ls -lht backups/db_backup_*.sql.gz | head -5

# Determine data loss window
CORRUPT_BACKUP="backups/db_backup_20240115_130000.sql.gz"  # When deleted
GOOD_BACKUP="backups/db_backup_20240115_020000.sql.gz"     # Before deletion
```

**Recovery (30-120 min):**
```bash
# 1. Restore good backup
docker-compose exec -T postgres dropdb -U arthainvest arthainvest_crm
docker-compose exec -T postgres createdb -U arthainvest arthainvest_crm
docker-compose exec -T postgres psql -U arthainvest arthainvest_crm < $GOOD_BACKUP

# 2. Review code change
git log --oneline | head -5
git diff HEAD~1 HEAD

# 3. Fix the bug
# (Fix code and commit)

# 4. Restart with fix
docker-compose up -d
```

---

## 🔄 Backup & Recovery Strategy

### **Backup Schedule**

```
Daily Backups:     2:00 AM IST
Retention:         30 days (daily)
Compression:       SQL.gz format
Location:          ./backups/ (server) + /external/ (offsite)
Encryption:        At rest (optional)
Verification:      SHA256 checksums
```

### **Backup Verification**

```bash
# Weekly backup verification (Friday)
for backup in backups/db_backup_*.sql.gz; do
    echo "Verifying $backup..."
    if sha256sum -c "$backup.sha256"; then
        echo "✓ Valid"
    else
        echo "✗ CORRUPTED"
        echo "Alert: Backup corrupted - $backup" | mail admin@arthainvestcapital.com
    fi
done
```

### **Multi-Location Backup**

```
Location 1: Server /backups/ (hot)      - daily, 30-day retention
Location 2: External storage (warm)     - weekly copy, 3-month retention
Location 3: Cloud backup (cold)         - monthly archive, 1-year retention (optional)
```

---

## 📊 RTO/RPO Matrix

| Scenario | Severity | RTO | RPO | Primary Recovery |
|----------|----------|-----|-----|------------------|
| Database Corruption | High | 2h | 1h | Restore backup |
| Disk Full | Medium | 1h | 0h | Cleanup + restart |
| App Bug | High | 2h | 1h | Rollback + fix |
| Server Failure | Critical | 4h | 1h | New server + restore |
| Security Breach | Critical | 4h | 1h | Forensics + restore |
| Network Outage | High | 1h | 0h | Wait/failover |
| SSL Certificate Expired | High | 1h | 0h | Renew certificate |
| DNS Misconfiguration | Medium | 30m | 0h | Fix DNS records |

---

## 🚀 Failover Strategy (Future)

**If fully implemented:**
- Backup server on standby
- DNS failover to secondary
- Database replication
- Load balancer
- CDN for static assets

**Current Status:** Not implemented (single-server setup)  
**Recommendation:** Implement after Phase 2

---

## 📱 Communication Plan

**During Disaster:**

1. **Immediate (0-15 min):**
   - Alert on-call engineer
   - Page manager
   - Internal status: "Investigating"

2. **Short-term (15-60 min):**
   - Team Slack channel update
   - External status page (if public)
   - Initial ETA to recovery

3. **Ongoing (hourly):**
   - Status updates to stakeholders
   - ETA updates
   - Impact assessment

4. **Resolution:**
   - Full incident report
   - Root cause analysis
   - Lessons learned
   - Preventive measures

**Status Levels:**
- 🔴 Critical: Complete outage
- 🟠 High: Major features unavailable
- 🟡 Medium: Some features degraded
- 🟢 Resolved: System operational

---

## 🧪 Recovery Testing

**Quarterly Disaster Recovery Drill:**

```bash
# Month 1: Database recovery test
# - Take latest backup
# - Restore to test environment
# - Verify data integrity
# - Test application with restored data

# Month 2: Server failover test
# - Simulate server loss
# - Provision new server
# - Deploy application
# - Verify all services

# Month 3: Full scenario test
# - Simulate complete outage
# - Execute full recovery plan
# - Time the entire process
# - Document any issues
```

**Success Criteria:**
- RTO met (within 4 hours)
- RPO met (no more than 1 hour data loss)
- Data integrity verified
- All services operational
- Team familiar with process

---

## 📋 DR Kit Checklist

**Keep this checklist updated:**

```
☑ Latest backups available (< 24h old)
☑ Backup verification script tested
☑ Recovery procedure documented
☑ SSL certificates backed up
☑ .env.production backed up
☑ Docker images documented
☑ Server access credentials secure
☑ Hosting provider contact info current
☑ Team trained on recovery
☑ Communication template ready
☑ Monitor alerting tested
☑ Rollback procedure verified
```

---

## 🎓 Team Training

**All ops staff must be trained on:**
1. Backup creation and verification
2. Database restore procedure
3. Server provisioning (if applicable)
4. Application deployment
5. Communication protocols
6. Escalation paths

---

## 📞 Emergency Contacts

| Role | Name | Phone | Email | Escalation |
|------|------|-------|-------|------------|
| On-Call | | | | Page immediately |
| Manager | | | | Within 30 min |
| CTO | | | | Critical only |
| Hosting Provider | | | | Emergency line |

---

**Last Tested:** [DATE]  
**Next Drill:** [DATE]  
**Approved By:** [SIGNATURE]

