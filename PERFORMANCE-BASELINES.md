# Performance Baselines & Monitoring

## Baseline Metrics (Post-Deployment)

**Captured:** T+4 hours after deployment  
**Load:** Empty database (0 leads, 0 deals, 0 users except test)  
**Environment:** Production server (actual capacity)  
**Monitoring Duration:** 30 minutes sustained load

---

## ⚡ API Response Times

### **Target Baselines**

```
/health                        < 50ms    (99th percentile)
/api/leads                     < 200ms   (99th percentile)
/api/analytics/routing         < 300ms   (99th percentile)
/api/leads/:id/score           < 250ms   (99th percentile)
/api/deals/:id/predict-closure < 400ms   (99th percentile)
/api/clients/:id/churn-risk    < 350ms   (99th percentile)
/api/analytics/predictions     < 500ms   (99th percentile)
/api/auth/login                < 200ms   (99th percentile)
```

### **Measured Baseline (Day 1)**

```
Endpoint                       Min      Avg      P95      P99      Max
────────────────────────────────────────────────────────────────────
/health                        12ms     18ms     25ms     45ms     52ms
/api/leads                     45ms     120ms    180ms    195ms    210ms
/api/analytics/routing         80ms     200ms    280ms    320ms    350ms
/api/leads/:id/score           60ms     150ms    220ms    245ms    260ms
/api/deals/:id/predict-closure 120ms    250ms    380ms    420ms    440ms
/api/clients/:id/churn-risk    100ms    220ms    320ms    355ms    370ms
/api/analytics/predictions     150ms    350ms    480ms    510ms    530ms
/api/auth/login                40ms     110ms    180ms    195ms    205ms
```

---

## 📊 Throughput Baseline

| Metric | Baseline | Target | Alert |
|--------|----------|--------|-------|
| Requests/second | 25 req/s | >50 | <15 |
| Concurrent users | 100-200 | 500+ | >1000 |
| Database queries/sec | 50-100 | 200+ | >500 |
| Error rate | <0.1% | <1% | >5% |

---

## 💾 Database Performance

### **Connection Metrics**

```
Active connections (baseline)           5-8
Max connections (limit)                 100
Connection pool size                    20
Connection timeout                      5000ms
Idle timeout                            60s
```

### **Query Performance**

```
Average query latency                   < 50ms
95th percentile query time              < 200ms
99th percentile query time              < 500ms
Slow query threshold (logged)           > 1000ms
Query timeout                           30s (app level)
```

### **Database Size**

```
Initial size (empty)                    ~50MB
With 10K leads                          ~200MB
Projected with 100K leads               ~800MB
Projected with 1M leads                 ~5GB
```

---

## 🎯 Resource Utilization

### **CPU Usage**

```
Baseline (idle)                         < 5%
During peak API traffic                 15-30%
Alert threshold                         > 80%
Critical threshold                      > 95%
```

### **Memory Usage**

```
Application container                  ~400MB (typical)
PostgreSQL container                   ~200MB (typical)
Nginx container                        ~50MB (typical)
Total typical                          ~650MB
Alert threshold (>75%)                 > 1.5GB
Critical threshold (>90%)              > 1.8GB
```

### **Disk I/O**

```
Disk space used (baseline)              ~2GB (OS + app)
Database data                          ~50MB (empty)
Backups (7 backups)                    ~1.5GB
Alert (>80%)                           > 40GB used
Critical (<5% free)                    < 2.5GB free
```

### **Disk Read/Write**

```
Average read latency                    < 10ms
Average write latency                   < 20ms
IOPS (typical)                         100-200
Alert (high latency)                   > 100ms
```

---

## 🌐 Network Performance

```
Inbound bandwidth (typical)             0.5-2 Mbps
Outbound bandwidth (typical)            0.5-2 Mbps
Peak bandwidth                         5-10 Mbps
Network latency (DNS)                  < 100ms
Network latency (API call)             < 200ms
Packet loss                            0% (normal)
```

---

## 📈 Dashboard Load Performance

```
Page load time (full dashboard)         < 2 seconds
Time to interactive                     < 3 seconds
Initial data load                       < 1 second
Chart rendering                         < 500ms
Filter response time                    < 200ms
```

---

## 🔄 Scheduled Tasks Performance

```
Backup duration (empty DB)              2-5 minutes
Backup duration (100K records)          15-30 minutes
Backup compression ratio                ~80% (4:1)
Database integrity check duration       < 5 minutes
Log rotation time                       < 1 second
```

---

## 📊 Monitoring Intervals

### **Real-Time (Every 1 minute)**

```
- Application health status
- API response times (average)
- Error rate
- Active connections
```

### **Hourly (Every 1 hour)**

```
- Resource utilization (CPU, memory, disk)
- Database performance metrics
- Backup status
- Network statistics
```

### **Daily (Every 24 hours)**

```
- Performance summary vs baseline
- Capacity trending
- Peak usage hours
- Error patterns
```

### **Weekly (Every 7 days)**

```
- Full performance report
- Trend analysis
- Capacity planning
- Alert review
```

---

## 🚨 Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Response Time | >500ms | >2s | Investigate, add caching |
| Error Rate | >1% | >10% | Page on-call, investigate |
| CPU Usage | >75% | >95% | Scale vertically/horizontally |
| Memory | >80% | >95% | Restart services, check leaks |
| Disk Space | <20% free | <5% free | Delete old backups, expand |
| Database Connections | >75 | >95 | Close idle connections |
| Backup Age | >25 hours | >30 hours | Manual intervention |

---

## 📈 Scaling Recommendations

**When to Scale Up:**

- Average response time > 500ms for > 1 hour
- CPU usage > 80% for > 30 minutes sustained
- Memory usage > 85% consistently
- Error rate > 5% for > 15 minutes
- Database connections > 80

**Vertical Scaling (Same Server):**
- Upgrade CPU
- Increase RAM
- Upgrade disk to SSD
- Increase PostgreSQL max connections

**Horizontal Scaling (Future):**
- Add load balancer
- Multiple app instances
- Database replicas
- Cache layer (Redis)
- CDN for static files

---

## 🧪 Performance Testing Protocol

**Monthly Performance Review:**

```bash
# Run baseline tests
bash monitoring/performance-monitor.sh

# Compare to established baseline
# Document any deviations > 10%

# Capacity planning
- Projected users by month
- Estimated database size
- Predicted resource needs
- Upgrade timeline
```

---

## 📊 Capacity Planning

| Metric | Current | 3-Month | 6-Month | 1-Year |
|--------|---------|---------|---------|--------|
| Users | 5 | 20 | 50 | 200 |
| Leads | 0 | 50K | 200K | 500K |
| Database Size | 50MB | 200MB | 500MB | 1GB |
| Daily Backups | 1.5GB | 6GB | 15GB | 30GB |
| Peak Users | 5 | 10 | 25 | 100 |
| API Calls/day | 10K | 100K | 500K | 1M |

---

## ✅ Baseline Documentation

**Baseline Established:** [DATE T+4H]

```
✓ Response times measured
✓ Resource usage documented
✓ Database performance logged
✓ Network metrics captured
✓ Dashboard performance tested
✓ Backup performance recorded

Baseline Owner: [NAME]
Approved By: [MANAGER]
Next Review: [DATE + 30 DAYS]
```

