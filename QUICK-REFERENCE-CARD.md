# ⚡ Quick Reference Card - Testing Execution

## 🎯 Your Testing Mission

Execute all 10 phases, record outputs, report results.

---

## 📋 THE 10 PHASES (Print this!)

### PHASE 1️⃣: Environment (5 min)
```bash
docker --version                    # Docker 20.x+
docker-compose --version            # Compose 1.29.x+
node --version                      # Node v16+
cat .env.local | head -10           # Check config
```
✓ All working? → **PASS**

---

### PHASE 2️⃣: Docker Startup (15 min)
```bash
docker-compose build                # Build images
docker-compose up -d                # Start services
docker-compose ps                   # Check status - all should be "Up (healthy)"
docker-compose logs app | tail -10  # Watch startup
```
✓ All 3 services Up (healthy)? → **PASS**

---

### PHASE 3️⃣: Database (5 min)
```bash
docker-compose exec postgres psql -U arthainvest -d arthainvest_crm -c "SELECT 1"
# Expected: ?column? = 1

docker-compose exec postgres psql -U arthainvest -d arthainvest_crm -c "\dt"
# Expected: 6+ tables (leads, deals, clients, users, etc.)

docker-compose exec postgres pg_dump -U arthainvest arthainvest_crm > /tmp/test.sql && echo "✓ OK"
# Expected: ✓ OK
```
✓ All three work? → **PASS**

---

### PHASE 4️⃣: API Health (5 min)
```bash
curl -s http://localhost:3000/health
# Expected: JSON with "status": "healthy"

curl -s -o /dev/null -w "Response time: %{time_total}s\n" http://localhost:3000/health
# Expected: < 0.1 seconds

curl -s -I http://localhost:3000/health | grep -i "access-control"
# Expected: CORS header present
```
✓ All three work? → **PASS**

---

### PHASE 5️⃣: Endpoints (10 min)
```bash
curl -s http://localhost:3000/api/leads
# Expected: JSON response

curl -s http://localhost:3000/api/analytics/routing
# Expected: JSON response

curl -s http://localhost:3000/ | head -10
# Expected: HTML
```
✓ All three work? → **PASS**

---

### PHASE 6️⃣: Features (10 min)
```bash
# Open browser: http://localhost:3000
# Check: Dashboard loads, sidebar visible, no errors

curl -s -X POST http://localhost:3000/api/leads/score -H "Content-Type: application/json" -d '{"lead_id": 1}'
# Expected: JSON or "not implemented" (both OK)

curl -s http://localhost:3000/api/analytics/predictions
# Expected: JSON or "not implemented" (both OK)
```
✓ Dashboard loads and no errors? → **PASS**

---

### PHASE 7️⃣: Performance (5 min)
```bash
for i in {1..10}; do curl -s -o /dev/null -w "Request $i: %{time_total}s\n" http://localhost:3000/health; done
# Expected: All < 0.2 seconds

docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
# Expected: CPU < 5%, Memory < 1GB total
```
✓ All fast and memory OK? → **PASS**

---

### PHASE 8️⃣: Logging (5 min)
```bash
docker-compose logs app | grep -i "error\|fatal\|crash" | wc -l
# Expected: 0

docker-compose logs postgres | grep -i "error" | wc -l
# Expected: 0

docker-compose logs nginx | grep "500" | wc -l
# Expected: 0
```
✓ All show 0 errors? → **PASS**

---

### PHASE 9️⃣: Rollback (5 min)
```bash
docker-compose down
# Wait for it to complete

docker-compose up -d
sleep 30

docker-compose ps
# Expected: All "Up (healthy)"

docker-compose exec postgres psql -U arthainvest -d arthainvest_crm -c "\dt" | wc -l
# Expected: Same number of tables as before
```
✓ Everything restarts cleanly? → **PASS**

---

### PHASE 🔟: Readiness (5 min)
```bash
grep "change_me_in_production" .env* || echo "✓ OK"
# Expected: ✓ OK

docker-compose config > /dev/null && echo "✓ Configuration valid"
# Expected: ✓ Configuration valid
```
✓ Both show OK? → **PASS**

---

## 📊 SCORING

| # Passed | Status |
|----------|--------|
| 10 | ✅ **READY FOR PRODUCTION** |
| 9 | ⚠️ Check minor issue, likely OK |
| 7-8 | ⚠️ Review issue, may need fix |
| < 7 | ❌ Fix issues before proceeding |

---

## 🚨 IF STUCK

**Problem:** Docker not found  
→ `brew install docker` or download Docker Desktop

**Problem:** Connection refused (port 3000)  
→ Wait 30 seconds, app still starting

**Problem:** Database error  
→ Wait 15 seconds, database still starting

**Problem:** Port in use  
→ `lsof -i :3000` to find what's using it

**Problem:** Out of memory  
→ Docker Desktop → Settings → Resources → Memory (4GB+)

**Problem:** Build failure  
→ `docker-compose down -v && docker system prune -a -f && docker-compose build`

**Still stuck?**  
→ Check LIVE-TESTING-SUPPORT.md

---

## 📝 WHEN COMPLETE

Report back with:

```
✅ All 10 phases: PASS
Success Rate: 100%
Duration: __ minutes

Ready for Production: YES
```

Or:

```
⚠️ Phases Passed: 9/10
Failed Phase: #5 (Endpoints)
Issue: Connection timeout on /api/analytics/routing

Action Taken: Restarted app
Result: Still failing

Need help with: Phase 5
```

---

## ⏱️ TIMER

- Start: __________
- Phase 1-2 (17m): __________
- Phase 5-6 (52m): __________
- Phase 10 (72m): __________
- Finished: __________

---

**Print this page. Good luck! 🍀**

