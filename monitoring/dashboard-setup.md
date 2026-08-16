# Monitoring Dashboards Setup Guide

## Dashboard Overview

**Purpose:** Real-time visibility into production system health  
**Tools:** Docker stats, custom bash scripts, web UI dashboard  
**Update Frequency:** Every 30 seconds to 5 minutes  
**Accessible From:** Production server terminal or web browser  

---

## 📊 Dashboard 1: Real-Time System Health

### **How to Access**

```bash
# SSH to production server
ssh deploy@arthainvestcapital.com
cd ~/arthainvest-crm

# Launch real-time dashboard
bash monitoring/monitor-deployment.sh
```

### **What It Shows**

```
╔═══════════════════════════════════════════════════════════════╗
║  ArthaInvest CRM - Real-time Monitoring Dashboard            ║
║  2024-08-16 14:30:45                                          ║
╚═══════════════════════════════════════════════════════════════╝

CONTAINER STATUS:
✓ arthainvest-app        Up (5 hours)
✓ arthainvest-postgres   Up (5 hours)
✓ arthainvest-nginx      Up (5 hours)

APPLICATION HEALTH:
✓ Web Server (3000):     Healthy
✓ Database (5432):       Ready
✓ Reverse Proxy (80/443): Listening

RESOURCE USAGE:
  app         7%        512MB / 2GB
  postgres    12%       850MB / 2GB
  nginx       2%        45MB / 2GB

RECENT ERRORS: (Last 5)
  (None)

LATEST LOGS: (Last 3)
  [INFO] Request processed in 145ms
  [INFO] Database query executed in 23ms
  [INFO] Backup completed successfully

Last updated: 2024-08-16 14:30:45
Press Ctrl+C to exit
```

### **Monitoring:**
- ✓ Container status (running/stopped/crashed)
- ✓ Application health (responding)
- ✓ Database availability
- ✓ CPU & Memory usage per container
- ✓ Error patterns in logs
- ✓ Latest activity

---

## 📊 Dashboard 2: Performance Metrics

### **How to Access**

```bash
ssh deploy@arthainvestcapital.com
cd ~/arthainvest-crm

# Generate performance report
bash monitoring/performance-monitor.sh
```

### **Report Output**

```
╔═══════════════════════════════════════════════════════════════╗
║  ArthaInvest CRM - Performance Report                         ║
║  2024-08-16 14:30:45                                          ║
╚═══════════════════════════════════════════════════════════════╝

API RESPONSE TIMES:
/health                    18ms avg (Min: 12ms, Max: 45ms)
/api/analytics/routing     198ms avg (Min: 80ms, Max: 350ms)
/api/leads/:id/score       152ms avg (Min: 60ms, Max: 260ms)

THROUGHPUT TEST (30 seconds):
Requests completed:        45
Success rate:             100%
Average RPS:             1.5 req/s

DATABASE PERFORMANCE:
Active Connections:        8 / 100
Cache Hit Ratio:          95%
Avg Query Time:           23ms
Slow Queries (>1s):       0

SYSTEM INFORMATION:
CPU Load Average:         0.45, 0.52, 0.48
Memory Usage:             2.1 GB / 8 GB (26%)
Disk Usage:              12 GB / 100 GB (12%)
Network:                 Inbound: 0.8 Mbps, Outbound: 1.2 Mbps

HEALTH STATUS:
✓ All metrics within normal range
✓ No performance degradation detected
✓ System capacity: 35% used
```

---

## 📊 Dashboard 3: Alerting System

### **How to Access**

```bash
# View alert logs
tail -f logs/alerts/alert_$(date +%Y%m%d).log

# Test alert configuration
bash monitoring/alerting-system.sh

# Verify Slack notifications
# Check Slack channel for alerts
```

### **Alert Types**

```
🟢 HEALTHY (Green)
   - All systems operational
   - Metrics within normal range
   - No action required

🟡 WARNING (Yellow)
   - CPU > 75% for > 5 minutes
   - Memory > 80% for > 5 minutes
   - Response time > 500ms
   - Error rate > 1%
   - Action: Investigate, prepare scaling

🔴 CRITICAL (Red)
   - CPU > 95%
   - Memory > 95%
   - Error rate > 10%
   - Database unreachable
   - Disk space < 5%
   - Action: Immediate intervention required

⚫ INFO (Blue)
   - Scheduled maintenance
   - Backup completed
   - Regular status update
```

---

## 📊 Dashboard 4: Backup Status

### **How to Access**

```bash
ssh deploy@arthainvestcapital.com
cd ~/arthainvest-crm

# Check backup status
bash scripts/monitor-backups.sh
```

### **Output Example**

```
╔═══════════════════════════════════════════════════════════════╗
║  Backup Status & Monitoring                                  ║
╚═══════════════════════════════════════════════════════════════╝

LATEST BACKUP:
  File: db_backup_20240816_020000.sql.gz
  Size: 245MB
  Time: 2024-08-16 02:00:15

BACKUP INVENTORY:
  Total backups: 30 (30-day retention)
  Backup ages:
    - db_backup_20240816_020000.sql.gz: 0d 12h ago
    - db_backup_20240815_020000.sql.gz: 1d 12h ago
    - db_backup_20240814_020000.sql.gz: 2d 12h ago
    ...

STORAGE USAGE:
  Total backup size: 7.5 GB
  Available space: 88 GB
  Storage usage: 8%

BACKUP VERIFICATION:
  Valid: 30
  Invalid: 0
  Status: ✓ All backups valid
```

---

## 📊 Dashboard 5: Web UI Monitoring (Coming Soon)

### **Planned Features:**

```
[ ] Real-time metrics graph
[ ] Historical trending
[ ] Alert timeline
[ ] Resource utilization heatmap
[ ] Performance comparison
[ ] Capacity forecast
[ ] Team activity log
```

### **Access URL (When Available)**

```
https://arthainvestcapital.com/monitoring
```

---

## 🔔 Setting Up Slack Alerts

### **Step 1: Create Slack Webhook**

1. Go to: https://api.slack.com/apps
2. Create New App → "From scratch"
3. Name: "ArthaInvest Alerts"
4. Workspace: Select your workspace
5. Go to: "Incoming Webhooks"
6. Toggle: "Activate Incoming Webhooks"
7. Click: "Add New Webhook to Workspace"
8. Select channel: #production-alerts
9. Copy webhook URL

### **Step 2: Configure in Alerting System**

```bash
# Set environment variable
export SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Or add to monitoring/alerting-system.sh
sed -i 's|SLACK_WEBHOOK=.*|SLACK_WEBHOOK="your-webhook-url"|' monitoring/alerting-system.sh
```

### **Step 3: Test Alert**

```bash
# Test message
curl -X POST "$SLACK_WEBHOOK" \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "✅ Test: ArthaInvest monitoring is working",
    "attachments": [{
      "color": "good",
      "title": "Test Alert",
      "text": "If you see this, Slack integration is working!"
    }]
  }'

# Should appear in #production-alerts channel
```

---

## 📅 Monitoring Schedule

### **Every Minute**

```bash
# Automated by cron
*/1 * * * * docker stats --no-stream >> /var/log/docker-stats.log
*/1 * * * * curl -s http://localhost:3000/health >> /var/log/app-health.log
```

### **Every 5 Minutes**

```bash
# Automated by monitoring-system.sh
*/5 * * * * bash /path/to/monitoring/alerting-system.sh
```

### **Hourly**

```bash
# Automated
0 * * * * bash /path/to/monitoring/performance-monitor.sh
```

### **Daily**

```bash
# 7 AM - Daily review
0 7 * * * bash /path/to/scripts/monitor-backups.sh | mail admin@arthainvestcapital.com

# 3 PM - Afternoon check
0 15 * * * bash /path/to/monitoring/performance-monitor.sh >> /var/log/daily-performance.log
```

### **Weekly**

```bash
# Monday 9 AM - Weekly report
0 9 * * MON bash /path/to/generate-weekly-report.sh | mail team@arthainvestcapital.com
```

---

## 📊 Custom Dashboard Creation

### **Option 1: Simple Web Dashboard (DIY)**

```html
<!-- Create monitoring/web-dashboard.html -->
<html>
<head>
    <title>ArthaInvest Monitoring</title>
    <script>
        setInterval(() => {
            // Fetch metrics every 30 seconds
            fetch('/api/metrics')
                .then(r => r.json())
                .then(data => updateDashboard(data))
        }, 30000)
    </script>
</head>
<body>
    <div id="metrics">Loading...</div>
</body>
</html>
```

### **Option 2: Use Existing Tools**

**Prometheus + Grafana Setup (Advanced):**
```bash
# Not currently implemented but available in Phase 2
# Would require Docker containers for Prometheus & Grafana
# Provides professional-grade dashboarding
```

---

## 🎯 Dashboard Maintenance

### **Daily Checks (9 AM)**

```
☑ All alerts in Slack reviewed
☑ Any yellow warnings investigated
☑ Backup status confirmed
☑ Error logs reviewed
☑ Resource usage within baseline
```

### **Weekly Review (Monday 9 AM)**

```
☑ Performance vs baseline
☑ Capacity trending
☑ Backup retention verified
☑ Alert tuning (if needed)
☑ Trend analysis for scaling
```

### **Monthly Review (First of month)**

```
☑ Complete performance report
☑ Identify optimization opportunities
☑ Plan for growth/scaling
☑ Update baselines if drifted
☑ Team feedback on monitoring
```

---

## 📞 Alert Escalation

**When Alert Received:**

1. **Warning (Yellow)** - Next 30 minutes
   - Monitor closely
   - Investigate cause
   - Plan preventive action

2. **Critical (Red)** - Immediate
   - Page on-call engineer
   - Begin troubleshooting
   - Consider rollback if recent deployment

3. **No Alert for 60+ minutes** - Possible probe failure
   - Check monitoring system health
   - Restart monitoring if needed
   - Investigate why alerts stopped

---

## ✅ Monitoring Readiness Checklist

```
☑ Real-time dashboard running (monitor-deployment.sh)
☑ Performance monitoring configured (performance-monitor.sh)
☑ Alerting system active (alerting-system.sh)
☑ Slack webhook connected
☑ Backup monitoring enabled (monitor-backups.sh)
☑ Cron jobs scheduled
☑ Alert thresholds tuned
☑ Team trained on dashboards
☑ Escalation procedures documented
☑ 24/7 on-call schedule established
```

---

**Monitoring Status:** ✅ ACTIVE  
**Last Updated:** [DATE]  
**Next Review:** [DATE]

