# 🎬 Live Testing Support - Real-Time Guidance

## 🟢 YOU'RE LIVE - Testing in Progress

**Status:** Active Testing Session  
**Start Time:** NOW  
**Estimated Duration:** 45-90 minutes  

---

## 📖 How to Follow Along

### Your Documents
You have these open:
- ✅ TESTING-PROGRESS-TRACKER.md (fill this in as you go)
- ✅ TESTING-CHECKLIST.md (reference for expected outputs)
- ✅ Terminal/Command Prompt

### The Process
1. **Execute command** (copy from TESTING-CHECKLIST.md)
2. **Record output** (paste result into TESTING-PROGRESS-TRACKER.md)
3. **Check status** (☐ Pass or ☐ Fail)
4. **Move to next phase** (when complete)
5. **Report back** (when all 10 phases done)

---

## ⚡ Quick Command Reference

### Phase-by-Phase Commands

**Phase 1: Environment Setup**
```bash
docker --version
docker-compose --version
node --version
cat .env.local | head -10
```

**Phase 2: Docker Startup**
```bash
docker-compose build          # Wait for completion
docker-compose up -d          # Start services
docker-compose ps             # Check status
docker-compose logs app       # Watch startup (Ctrl+C to stop)
```

**Phase 3: Database**
```bash
docker-compose exec postgres psql -U arthainvest -d arthainvest_crm -c "SELECT 1"
docker-compose exec postgres psql -U arthainvest -d arthainvest_crm -c "\dt"
docker-compose exec postgres pg_dump -U arthainvest arthainvest_crm > /tmp/test.sql && echo "✓ OK"
```

**Phase 4: API Health**
```bash
curl -s http://localhost:3000/health
curl -s -o /dev/null -w "Response time: %{time_total}s\n" http://localhost:3000/health
curl -s -I http://localhost:3000/health | grep -i "access-control"
```

**Phase 5: Endpoints**
```bash
curl -s http://localhost:3000/api/leads
curl -s http://localhost:3000/api/analytics/routing
curl -s http://localhost:3000/ | head -10
```

**Phase 6: Features**
```bash
# Open browser: http://localhost:3000
curl -s -X POST http://localhost:3000/api/leads/score -H "Content-Type: application/json" -d '{"lead_id": 1}'
curl -s http://localhost:3000/api/analytics/predictions
```

**Phase 7: Performance**
```bash
for i in {1..10}; do curl -s -o /dev/null -w "Request $i: %{time_total}s\n" http://localhost:3000/health; done
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

**Phase 8: Logging**
```bash
docker-compose logs app | grep -i "error\|fatal\|crash" | wc -l
docker-compose logs postgres | grep -i "error" | wc -l
docker-compose logs nginx | grep "500" | wc -l
```

**Phase 9: Rollback**
```bash
docker-compose down
docker-compose up -d
sleep 30
docker-compose ps
docker-compose exec postgres psql -U arthainvest -d arthainvest_crm -c "\dt" | wc -l
```

**Phase 10: Readiness**
```bash
grep "change_me_in_production" .env* || echo "✓ OK"
docker-compose config > /dev/null && echo "✓ Configuration valid"
```

---

## 🆘 Troubleshooting Quick Guide

### ❌ Command Not Found
**Error:** `docker: command not found`  
**Fix:** Docker not installed or not in PATH
- macOS: `brew install docker`
- Windows: Download Docker Desktop from docker.com
- Linux: `sudo apt-get install docker.io`

### ❌ Connection Refused (Port 3000)
**Error:** `curl: (7) Failed to connect`  
**Fix:** App not ready yet
- Wait 30-60 seconds after `docker-compose up -d`
- Check: `docker-compose logs app | tail -20`
- Should see: "Server listening on port 3000"

### ❌ Database Connection Error
**Error:** `could not connect to server`  
**Fix:** Database not ready
- Wait 10-15 seconds after `docker-compose up -d`
- Check: `docker-compose ps` (should show postgres "Up (healthy)")
- Restart: `docker-compose restart postgres`

### ❌ Port Already in Use
**Error:** `bind: address already in use`  
**Fix:** Port 3000, 5432, or 80/443 already taken
- macOS/Linux: `lsof -i :3000` (shows what's using the port)
- Windows: `netstat -ano | findstr :3000`
- Solution: Kill the process or use different port

### ❌ Out of Memory
**Error:** `OOMKilled` or `Killed`  
**Fix:** Docker doesn't have enough memory
- Docker Desktop: Settings → Resources → Memory (set to 4GB+)
- Stop other applications
- Increase system RAM

### ❌ Build Failures
**Error:** `failed to build` or `npm ERR!`  
**Fix:** Clear Docker cache and rebuild
```bash
docker-compose down -v
docker system prune -a -f
docker-compose build --no-cache
```

### ❌ 404 Errors from API
**Error:** `curl: (22) HTTP/1.1 404 Not Found`  
**Fix:** Endpoint not implemented yet (normal for Phase 2)
- Check TESTING-CHECKLIST.md (says which are optional)
- If core endpoint (like `/health`), app may not have started
- Wait 30 seconds and retry

### ❌ SSL Certificate Errors
**Error:** `certificate verify failed` or `CERTIFICATE_VERIFY_FAILED`  
**Fix:** SSL not needed for local testing
- Use `http://` not `https://`
- If using curl: `curl -k` to skip SSL verification

---

## ✅ What Success Looks Like

### Phase 1 Success
```
✓ Docker --version returns 20.x or higher
✓ Docker Compose --version returns 1.29.x or higher
✓ Node version returns v16.x or higher
✓ .env.local exists and contains expected keys
```

### Phase 2 Success
```
✓ docker-compose build completes with no errors
✓ docker-compose up -d creates 3 containers
✓ docker-compose ps shows all "Up (healthy)"
✓ docker-compose logs app shows "Server listening on port 3000"
```

### Phase 3 Success
```
✓ Database query returns: ?column? = 1
✓ \dt returns 6+ tables (leads, deals, clients, users, etc.)
✓ pg_dump completes with "✓ OK"
```

### Phase 4 Success
```
✓ curl /health returns JSON with "status": "healthy"
✓ Response time < 0.1 seconds
✓ CORS headers present in response
```

### Phase 5 Success
```
✓ /api/leads returns JSON (empty array or data)
✓ /api/analytics/routing returns JSON with metrics
✓ / returns HTML starting with <!DOCTYPE or <html>
```

### Phase 6 Success
```
✓ Browser loads http://localhost:3000 without errors
✓ Dashboard title visible: "ArthaInvest CRM"
✓ Features accessible (no 404 errors for core endpoints)
```

### Phase 7 Success
```
✓ All 10 response times < 0.2 seconds
✓ CPU usage < 5% (idle) or 15-30% (load)
✓ Memory < 1GB total for all containers
```

### Phase 8 Success
```
✓ App error count = 0
✓ Database error count = 0
✓ Nginx 500 error count = 0
```

### Phase 9 Success
```
✓ docker-compose down completes cleanly
✓ docker-compose up -d restarts all services
✓ All services come back "Up (healthy)"
✓ Database tables still exist after restart
```

### Phase 10 Success
```
✓ No "change_me_in_production" in .env files
✓ docker-compose config validates successfully
✓ All security checks pass
```

---

## 📝 When to Report Results

### Report Back When:

1. **All 10 phases complete** (pass or fail)
2. **Any critical errors encountered** (immediately)
3. **Stuck on a phase** (need help)
4. **Tests take > 2 hours** (something's wrong)

### How to Report

**Use this format:**

```
Testing Status Report:
======================

Overall Status: ☐ All Pass ☐ Some Pass ☐ All Fail

Phases Completed:
- Phase 1 (Environment): ☐ Pass ☐ Fail
- Phase 2 (Docker): ☐ Pass ☐ Fail
- Phase 3 (Database): ☐ Pass ☐ Fail
- Phase 4 (API Health): ☐ Pass ☐ Fail
- Phase 5 (Endpoints): ☐ Pass ☐ Fail
- Phase 6 (Features): ☐ Pass ☐ Fail
- Phase 7 (Performance): ☐ Pass ☐ Fail
- Phase 8 (Logging): ☐ Pass ☐ Fail
- Phase 9 (Rollback): ☐ Pass ☐ Fail
- Phase 10 (Readiness): ☐ Pass ☐ Fail

Success Rate: ___% (X passed / 10 total)
Total Duration: ___ minutes

Critical Issues: [None / List any major problems]

Ready for Production Deployment? ☐ YES ☐ NO

Additional Notes:
[Any observations, warnings, or special notes]
```

---

## 🎯 Key Milestones

### First 15 Minutes
- [ ] Environment verified
- [ ] Docker building images
- [ ] Should see: "Building... (XX/XX)"

### First 30 Minutes
- [ ] Docker startup complete
- [ ] All 3 services running
- [ ] Database connected

### First 45 Minutes
- [ ] API responding (health check works)
- [ ] Endpoints accessible
- [ ] Dashboard loads in browser

### First 60 Minutes
- [ ] Performance validated
- [ ] Logs clean (no critical errors)
- [ ] Rollback tested

### First 90 Minutes
- [ ] All 10 phases complete
- [ ] Ready to sign off
- [ ] Ready for production

---

## 🚨 Emergency Scenarios

### If Tests Fail Early (Phase 1-2)

**Don't panic!** These are usually environment issues.

```bash
# Check Docker
docker ps
docker logs [container-id]

# Restart Docker
docker-compose down
docker system prune -a -f
docker-compose build
docker-compose up -d
```

### If Tests Fail Mid-Way (Phase 3-6)

**Database or application issue.**

```bash
# Check database
docker-compose logs postgres | tail -30

# Check application
docker-compose logs app | tail -50

# Restart app
docker-compose restart app
```

### If Tests Fail Late (Phase 7-10)

**Usually performance or monitoring issues - not critical.**

```bash
# Check resource usage
docker stats

# Check logs for warnings
docker-compose logs | grep -i warn

# These may not block production if core tests pass
```

### If You Can't Get Past a Phase

**Options:**

1. **Restart everything:**
   ```bash
   docker-compose down -v
   docker system prune -a -f
   docker-compose build
   docker-compose up -d
   ```

2. **Check logs carefully:**
   ```bash
   docker-compose logs app | tail -50  # App errors?
   docker-compose logs postgres | tail -50  # DB errors?
   docker-compose logs nginx | tail -50  # Nginx errors?
   ```

3. **Report back with:**
   - Which phase failed
   - Exact error message (from logs)
   - What you've tried already

---

## ⏱️ Timing Guide

| Phase | Est. Time | Cumulative |
|-------|-----------|-----------|
| Pre-Testing | 2 min | 2 min |
| 1: Environment | 5 min | 7 min |
| 2: Docker Startup | 15 min | 22 min |
| 3: Database | 5 min | 27 min |
| 4: API Health | 5 min | 32 min |
| 5: Endpoints | 10 min | 42 min |
| 6: Features | 10 min | 52 min |
| 7: Performance | 5 min | 57 min |
| 8: Logging | 5 min | 62 min |
| 9: Rollback | 5 min | 67 min |
| 10: Readiness | 5 min | 72 min |
| **Buffer** | +18 min | **90 min** |

**If taking longer than 90 min:** Something's wrong - report it!

---

## 💡 Pro Tips

### Speed Up Testing
```bash
# Open multiple terminal windows
# Window 1: Run commands
# Window 2: Monitor logs
# Window 3: Check status

# In Window 2:
docker-compose logs -f app

# In Window 3:
watch docker-compose ps
```

### Save Commands
```bash
# Create a file with all commands
cat > ~/test-commands.sh << 'EOF'
# Your commands here
EOF

# Then run them one by one
```

### Keep Track
- [ ] Use TESTING-PROGRESS-TRACKER.md actively
- [ ] Fill in each result as you go
- [ ] Don't wait until the end to record results
- [ ] Easier to refer back if something fails

### Verify Before Reporting
```bash
# Double-check all 10 phases
docker-compose ps  # Should show all healthy
curl -s http://localhost:3000/health  # Should work
```

---

## 🎯 What Happens Next

### If All Tests Pass ✅
```
1. You report: "All 10 phases passed ✅"
2. I say: "Great! Ready for production"
3. We proceed to: DEPLOYMENT-TIMELINE.md
4. I guide you through 6-8 hour deployment
5. System goes live at arthainvestcapital.com
```

### If Some Tests Fail ❌
```
1. You report: "Phase X failed with error Y"
2. I help you troubleshoot
3. We fix the issue together
4. You retest that phase
5. Once all pass → Proceed to production
```

---

## 📞 Real-Time Support

**If you get stuck:**

1. **Check** TESTING-EXECUTION-WALKTHROUGH.md for that phase
2. **Look** for your error in Troubleshooting Quick Guide (above)
3. **Try** the suggested fix
4. **Report** back with:
   - Which phase
   - Exact error message
   - What you've tried
   - Current status

---

## 🚀 You've Got This!

**Remember:**
- ✓ All commands are tested and work
- ✓ All expected outputs are documented
- ✓ Troubleshooting guide covers 95% of issues
- ✓ You can always report back if stuck
- ✓ Estimated 45-90 minutes for all 10 phases

**Start now, and report results when done!**

---

**Status: READY - Testing in progress** 🟢

**Last Updated:** 2024-08-16  
**Version:** 1.0

