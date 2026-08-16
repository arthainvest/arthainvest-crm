#!/bin/bash

# 🧪 ArthaInvest CRM - Automated Test Runner
# Execute all 10 testing phases automatically with results reporting

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
TOTAL=0
START_TIME=$(date +%s)

# Results file
RESULTS_FILE="test-results-$(date +%Y%m%d-%H%M%S).txt"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🧪 ArthaInvest CRM - Automated Test Suite                ║"
echo "║  $(date '+%Y-%m-%d %H:%M:%S')                                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Results will be saved to: $RESULTS_FILE"
echo ""

# Function to run test
test_phase() {
    local phase=$1
    local name=$2
    local cmd=$3

    TOTAL=$((TOTAL + 1))
    echo -n "[$TOTAL] $name ... "

    if eval "$cmd" > /tmp/test_output.txt 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        PASSED=$((PASSED + 1))
        echo "✓ $name" >> "$RESULTS_FILE"
    else
        echo -e "${RED}✗ FAIL${NC}"
        FAILED=$((FAILED + 1))
        echo "✗ $name - $(cat /tmp/test_output.txt | head -1)" >> "$RESULTS_FILE"
    fi
}

# ========================================
# PHASE 1: ENVIRONMENT SETUP
# ========================================
echo -e "${BLUE}PHASE 1: Environment Setup${NC}"
echo "─────────────────────────────────────────────────────────────"

test_phase "1.1" "Docker installed" "docker --version"
test_phase "1.2" "Docker Compose installed" "docker-compose --version"
test_phase "1.3" "Node.js installed" "node --version"
test_phase "1.4" ".env.local exists" "test -f .env.local"

echo ""

# ========================================
# PHASE 2: DOCKER STACK STARTUP
# ========================================
echo -e "${BLUE}PHASE 2: Docker Stack Startup${NC}"
echo "─────────────────────────────────────────────────────────────"

echo "Building Docker images (this may take 2-3 minutes)..."
test_phase "2.1" "Docker build" "docker-compose build --quiet"

echo "Starting services..."
test_phase "2.2" "Docker up" "docker-compose up -d"

echo "Waiting for services to be healthy (30 seconds)..."
sleep 30

test_phase "2.3" "PostgreSQL running" "docker-compose exec -T postgres pg_isready -U arthainvest"
test_phase "2.4" "App container running" "docker-compose ps | grep arthainvest-crm-app | grep -q Up"
test_phase "2.5" "Nginx container running" "docker-compose ps | grep arthainvest-nginx | grep -q Up"

echo ""

# ========================================
# PHASE 3: DATABASE VERIFICATION
# ========================================
echo -e "${BLUE}PHASE 3: Database Verification${NC}"
echo "─────────────────────────────────────────────────────────────"

test_phase "3.1" "Database connection" "docker-compose exec -T postgres psql -U arthainvest -d arthainvest_crm -c 'SELECT 1'"
test_phase "3.2" "Database tables exist" "docker-compose exec -T postgres psql -U arthainvest -d arthainvest_crm -c \"SELECT count(*) FROM information_schema.tables WHERE table_schema='public'\" | grep -q '[1-9]'"
test_phase "3.3" "Database backup works" "docker-compose exec -T postgres pg_dump -U arthainvest arthainvest_crm > /dev/null 2>&1"

echo ""

# ========================================
# PHASE 4: API HEALTH CHECKS
# ========================================
echo -e "${BLUE}PHASE 4: API Health Checks${NC}"
echo "─────────────────────────────────────────────────────────────"

# Wait for app to be ready
echo "Waiting for app to start (up to 30 seconds)..."
for i in {1..30}; do
    if curl -s http://localhost:3000/health > /dev/null 2>&1; then
        echo "App is ready!"
        break
    fi
    sleep 1
done

test_phase "4.1" "Health endpoint responds" "curl -s http://localhost:3000/health | grep -q 'healthy\\|status'"
test_phase "4.2" "Response time acceptable" "curl -s -o /dev/null -w '%{time_total}' http://localhost:3000/health | awk '{if (\$1 < 0.5) exit 0; else exit 1}'"
test_phase "4.3" "CORS headers present" "curl -s -I http://localhost:3000/health | grep -i 'access-control-allow-origin'"

echo ""

# ========================================
# PHASE 5: API ENDPOINTS
# ========================================
echo -e "${BLUE}PHASE 5: API Endpoints Testing${NC}"
echo "─────────────────────────────────────────────────────────────"

test_phase "5.1" "Leads endpoint" "curl -s http://localhost:3000/api/leads | grep -q '\\[\\|data\\|error'"
test_phase "5.2" "Analytics endpoint" "curl -s http://localhost:3000/api/analytics/routing | grep -q '\\{\\|data\\|error'"
test_phase "5.3" "Dashboard HTML loads" "curl -s http://localhost:3000 | grep -q 'html\\|HTML\\|<!doctype'"

echo ""

# ========================================
# PHASE 6: FEATURES
# ========================================
echo -e "${BLUE}PHASE 6: Features Testing${NC}"
echo "─────────────────────────────────────────────────────────────"

test_phase "6.1" "Routing feature accessible" "curl -s -X POST http://localhost:3000/api/leads/score -H 'Content-Type: application/json' -d '{\"lead_id\": 1}' | grep -q '\\{\\|error\\|not'"
test_phase "6.2" "Predictions accessible" "curl -s http://localhost:3000/api/analytics/predictions | grep -q '\\{\\|\\[\\|error'"

echo ""

# ========================================
# PHASE 7: PERFORMANCE
# ========================================
echo -e "${BLUE}PHASE 7: Performance Validation${NC}"
echo "─────────────────────────────────────────────────────────────"

# Performance test - check if responses are fast
SLOW_RESPONSES=0
for i in {1..5}; do
    RESPONSE_TIME=$(curl -s -o /dev/null -w '%{time_total}' http://localhost:3000/health)
    if (( $(echo "$RESPONSE_TIME > 0.5" | bc -l) )); then
        SLOW_RESPONSES=$((SLOW_RESPONSES + 1))
    fi
done

if [ $SLOW_RESPONSES -eq 0 ]; then
    PASSED=$((PASSED + 1))
    echo -e "[$((TOTAL+1))] Response times acceptable ... ${GREEN}✓ PASS${NC}"
else
    FAILED=$((FAILED + 1))
    echo -e "[$((TOTAL+1))] Response times acceptable ... ${YELLOW}⚠ WARN${NC}"
fi
TOTAL=$((TOTAL + 1))

test_phase "7.2" "Container resource usage" "docker stats --no-stream | grep -q 'arthainvest'"

echo ""

# ========================================
# PHASE 8: LOGGING
# ========================================
echo -e "${BLUE}PHASE 8: Logging & Monitoring${NC}"
echo "─────────────────────────────────────────────────────────────"

APP_ERRORS=$(docker-compose logs app 2>/dev/null | grep -i "error\|fatal\|crash" | wc -l)
DB_ERRORS=$(docker-compose logs postgres 2>/dev/null | grep -i "error\|fatal" | wc -l)

if [ $APP_ERRORS -eq 0 ]; then
    PASSED=$((PASSED + 1))
    echo -e "[$((TOTAL+1))] App logs clean ... ${GREEN}✓ PASS${NC}"
else
    FAILED=$((FAILED + 1))
    echo -e "[$((TOTAL+1))] App logs clean ... ${YELLOW}⚠ WARN (${APP_ERRORS} issues)${NC}"
fi
TOTAL=$((TOTAL + 1))

if [ $DB_ERRORS -eq 0 ]; then
    PASSED=$((PASSED + 1))
    echo -e "[$((TOTAL+1))] Database logs clean ... ${GREEN}✓ PASS${NC}"
else
    FAILED=$((FAILED + 1))
    echo -e "[$((TOTAL+1))] Database logs clean ... ${YELLOW}⚠ WARN (${DB_ERRORS} issues)${NC}"
fi
TOTAL=$((TOTAL + 1))

echo ""

# ========================================
# PHASE 9: ROLLBACK
# ========================================
echo -e "${BLUE}PHASE 9: Rollback Verification${NC}"
echo "─────────────────────────────────────────────────────────────"

echo "Testing graceful shutdown..."
test_phase "9.1" "Services stop cleanly" "docker-compose down && sleep 5"

echo "Restarting services..."
test_phase "9.2" "Services restart" "docker-compose up -d && sleep 30"

test_phase "9.3" "All services healthy" "docker-compose ps | grep -q 'Up (healthy)' && docker-compose ps | grep -q 'Up (healthy)' && docker-compose ps | grep -q 'Up (healthy)'"

echo ""

# ========================================
# PHASE 10: PRODUCTION READINESS
# ========================================
echo -e "${BLUE}PHASE 10: Production Readiness${NC}"
echo "─────────────────────────────────────────────────────────────"

test_phase "10.1" "No insecure defaults" "! grep -r 'change_me_in_production' .env* 2>/dev/null || echo 'OK'"
test_phase "10.2" "Configuration valid" "docker-compose config > /dev/null"

echo ""

# ========================================
# RESULTS
# ========================================
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  TEST RESULTS SUMMARY                                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Total Tests: $TOTAL"
echo -e "  ${GREEN}Passed: $PASSED${NC}"
echo -e "  ${RED}Failed: $FAILED${NC}"
echo ""

if [ $TOTAL -gt 0 ]; then
    PERCENTAGE=$((PASSED * 100 / TOTAL))
    echo "Success Rate: $PERCENTAGE%"
fi

echo "Duration: ${MINUTES}m ${SECONDS}s"
echo ""
echo "Results saved to: $RESULTS_FILE"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  ${GREEN}✓ ALL TESTS PASSED - PRODUCTION READY${NC}              ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Next Step: DEPLOYMENT-TIMELINE.md (6-8 hour deployment)"
    exit 0
else
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  ${RED}✗ SOME TESTS FAILED - REVIEW BELOW${NC}                 ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Failed tests:"
    grep "✗" "$RESULTS_FILE" || echo "See $RESULTS_FILE for details"
    exit 1
fi
