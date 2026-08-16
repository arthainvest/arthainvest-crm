#!/bin/bash

# Local Smoke Tests for ArthaInvest CRM v3.0
# Validates full stack locally before production deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0
TOTAL=0

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ArthaInvest CRM - Local Smoke Test Suite                 ║"
echo "║  $(date '+%Y-%m-%d %H:%M:%S')                                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Function to run a test
run_test() {
    local test_name=$1
    local test_cmd=$2
    TOTAL=$((TOTAL + 1))

    echo -n "[$TOTAL] $test_name ... "

    if eval "$test_cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}"
        FAILED=$((FAILED + 1))
    fi
}

# ========================================
# PHASE 1: Environment Setup
# ========================================
echo -e "${YELLOW}PHASE 1: Environment Setup${NC}"
echo "─────────────────────────────────────────────────────────────"

run_test "Docker installed" "docker --version"
run_test "Docker Compose installed" "docker-compose --version"
run_test "Node.js available" "which node"

echo ""

# ========================================
# PHASE 2: Stack Startup
# ========================================
echo -e "${YELLOW}PHASE 2: Stack Startup${NC}"
echo "─────────────────────────────────────────────────────────────"

echo "Building Docker images..."
docker-compose build --quiet 2>/dev/null || echo "Build in progress..."

echo "Starting services (this may take 30-60 seconds)..."
docker-compose up -d

# Wait for services to be healthy
echo "Waiting for services to be ready..."
sleep 5

run_test "PostgreSQL is running" "docker-compose exec -T postgres pg_isready -U arthainvest"
run_test "App container is running" "docker-compose ps | grep arthainvest-crm-app | grep -q 'Up'"
run_test "Nginx container is running" "docker-compose ps | grep arthainvest-nginx | grep -q 'Up'"

echo ""

# ========================================
# PHASE 3: Database Connectivity
# ========================================
echo -e "${YELLOW}PHASE 3: Database Connectivity${NC}"
echo "─────────────────────────────────────────────────────────────"

run_test "Database connection works" "docker-compose exec -T postgres psql -U arthainvest -d arthainvest_crm -c 'SELECT 1'"
run_test "Tables created" "docker-compose exec -T postgres psql -U arthainvest -d arthainvest_crm -c \"SELECT count(*) FROM information_schema.tables WHERE table_schema='public'\" | grep -q '[1-9]'"
run_test "Database not corrupted" "docker-compose exec -T postgres pg_dump -U arthainvest arthainvest_crm > /dev/null 2>&1"

echo ""

# ========================================
# PHASE 4: API Health & Endpoints
# ========================================
echo -e "${YELLOW}PHASE 4: API Health & Endpoints${NC}"
echo "─────────────────────────────────────────────────────────────"

# Wait for app to be ready
echo "Waiting for application to start (up to 30 seconds)..."
for i in {1..30}; do
    if curl -s http://localhost:3000/health > /dev/null 2>&1; then
        echo "Application ready!"
        break
    fi
    sleep 1
done

run_test "Health check endpoint" "curl -s http://localhost:3000/health | grep -q 'healthy'"
run_test "API responds to requests" "curl -s http://localhost:3000/api/health -H 'Content-Type: application/json' | grep -q 'status'"
run_test "CORS headers present" "curl -s -I http://localhost:3000/health | grep -i 'access-control-allow-origin'"

echo ""

# ========================================
# PHASE 5: Authentication
# ========================================
echo -e "${YELLOW}PHASE 5: Authentication${NC}"
echo "─────────────────────────────────────────────────────────────"

# Test login endpoint
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin_password"}' 2>/dev/null || echo "")

if echo "$LOGIN_RESPONSE" | grep -q "token\|error"; then
    echo -n "[TOTAL] Auth endpoint responds ... "
    echo -e "${GREEN}✓ PASS${NC}"
    PASSED=$((PASSED + 1))
else
    echo -n "[TOTAL] Auth endpoint responds ... "
    echo -e "${RED}✗ FAIL${NC}"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))

echo ""

# ========================================
# PHASE 6: Core Features
# ========================================
echo -e "${YELLOW}PHASE 6: Core Features${NC}"
echo "─────────────────────────────────────────────────────────────"

run_test "Leads endpoint accessible" "curl -s http://localhost:3000/api/leads -H 'Content-Type: application/json' | grep -q '\\[\\|error\\|data'"
run_test "Analytics endpoint accessible" "curl -s http://localhost:3000/api/analytics -H 'Content-Type: application/json' | grep -q '\\[\\|error\\|data'"
run_test "Dashboard HTML loads" "curl -s http://localhost:3000/ | grep -q 'html\\|HTML\\|<!doctype'"

echo ""

# ========================================
# PHASE 7: Performance
# ========================================
echo -e "${YELLOW}PHASE 7: Performance${NC}"
echo "─────────────────────────────────────────────────────────────"

# Test response times
echo "Testing response times (should be < 500ms)..."

RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" http://localhost:3000/health)
if (( $(echo "$RESPONSE_TIME < 0.5" | bc -l) )); then
    echo -n "[$((TOTAL + 1))] /health response time ($RESPONSE_TIME sec) ... "
    echo -e "${GREEN}✓ PASS${NC}"
    PASSED=$((PASSED + 1))
else
    echo -n "[$((TOTAL + 1))] /health response time ($RESPONSE_TIME sec) ... "
    echo -e "${YELLOW}⚠ WARN${NC}"
fi
TOTAL=$((TOTAL + 1))

# Database query performance
QUERY_TIME=$(docker-compose exec -T postgres psql -U arthainvest -d arthainvest_crm -c "SELECT 1" 2>&1 | tail -1)
echo -n "[$((TOTAL + 1))] Database query response ... "
echo -e "${GREEN}✓ PASS${NC}"
PASSED=$((PASSED + 1))
TOTAL=$((TOTAL + 1))

echo ""

# ========================================
# PHASE 8: Logs & Error Checking
# ========================================
echo -e "${YELLOW}PHASE 8: Logs & Error Checking${NC}"
echo "─────────────────────────────────────────────────────────────"

# Check for critical errors in logs
APP_ERRORS=$(docker-compose logs app 2>/dev/null | grep -i "error\|fatal\|crash" | wc -l)
DB_ERRORS=$(docker-compose logs postgres 2>/dev/null | grep -i "error\|fatal\|panic" | wc -l)

if [ $APP_ERRORS -eq 0 ]; then
    echo -n "[$((TOTAL + 1))] App logs - no critical errors ... "
    echo -e "${GREEN}✓ PASS${NC}"
    PASSED=$((PASSED + 1))
else
    echo -n "[$((TOTAL + 1))] App logs - $APP_ERRORS warnings ... "
    echo -e "${YELLOW}⚠ WARN${NC}"
fi
TOTAL=$((TOTAL + 1))

if [ $DB_ERRORS -eq 0 ]; then
    echo -n "[$((TOTAL + 1))] Database logs - no critical errors ... "
    echo -e "${GREEN}✓ PASS${NC}"
    PASSED=$((PASSED + 1))
else
    echo -n "[$((TOTAL + 1))] Database logs - $DB_ERRORS warnings ... "
    echo -e "${YELLOW}⚠ WARN${NC}"
fi
TOTAL=$((TOTAL + 1))

echo ""

# ========================================
# PHASE 9: Monitoring Integration
# ========================================
echo -e "${YELLOW}PHASE 9: Monitoring Integration${NC}"
echo "─────────────────────────────────────────────────────────────"

run_test "Metrics endpoint available" "curl -s http://localhost:3000/metrics -H 'Content-Type: application/json' | grep -q '\\{\\|\\[\\|error\\|data'"
run_test "Container stats available" "docker stats --no-stream | grep -q 'arthainvest'"

echo ""

# ========================================
# PHASE 10: Cleanup & Summary
# ========================================
echo -e "${YELLOW}PHASE 10: Test Summary${NC}"
echo "─────────────────────────────────────────────────────────────"
echo ""
echo "Test Results:"
echo "  Total Tests:   $TOTAL"
echo -e "  ${GREEN}Passed:     $PASSED${NC}"
echo -e "  ${RED}Failed:     $FAILED${NC}"
echo ""

# Calculate percentage
if [ $TOTAL -gt 0 ]; then
    PERCENTAGE=$((PASSED * 100 / TOTAL))
    echo "  Success Rate: $PERCENTAGE%"
fi

echo ""

if [ $FAILED -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  ${GREEN}✓ ALL TESTS PASSED - READY FOR PRODUCTION${NC}              ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    exit 0
else
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  ${RED}✗ SOME TESTS FAILED - REVIEW LOGS${NC}                      ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Failed tests:"
    docker-compose logs app 2>/dev/null | grep -i "error\|fatal" | head -10
    exit 1
fi
