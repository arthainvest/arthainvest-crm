#!/bin/bash

################################################################################
# ArthaInvest CRM - Post-Deployment Verification Script
# Run after deployment to verify everything is working
# Usage: bash verify-deployment.sh
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DOMAIN="arthainvestcapital.com"
FAILED=0
PASSED=0

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ArthaInvest CRM - Deployment Verification                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Test 1: Docker containers running
echo -e "${YELLOW}[1] Checking Docker containers...${NC}"
RUNNING=$(docker-compose ps -q | wc -l)
HEALTHY=$(docker-compose ps | grep "healthy\|Up" | wc -l)

if [ "$RUNNING" -ge 3 ]; then
    echo -e "${GREEN}✓ Containers running: $RUNNING${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Not all containers running${NC}"
    docker-compose ps
    ((FAILED++))
fi

# Test 2: Application health
echo -e "${YELLOW}[2] Checking application health...${NC}"
if curl -f -s http://localhost:3000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Application is healthy${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Application not responding${NC}"
    echo "Command: curl http://localhost:3000/health"
    ((FAILED++))
fi

# Test 3: Database connectivity
echo -e "${YELLOW}[3] Checking database connection...${NC}"
if docker-compose exec -T postgres pg_isready -U arthainvest &> /dev/null; then
    echo -e "${GREEN}✓ Database is ready${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Database not responding${NC}"
    ((FAILED++))
fi

# Test 4: Database tables
echo -e "${YELLOW}[4] Checking database tables...${NC}"
TABLES=$(docker-compose exec -T postgres psql -U arthainvest -d arthainvest_crm -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tail -1 | xargs)

if [ "$TABLES" -gt 0 ]; then
    echo -e "${GREEN}✓ Database tables found: $TABLES${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ No tables found (migrations may need to run)${NC}"
fi

# Test 5: Nginx reverse proxy
echo -e "${YELLOW}[5] Checking Nginx reverse proxy...${NC}"
if docker-compose logs nginx 2>/dev/null | grep -q "started" || curl -s -I http://localhost:80/ &> /dev/null; then
    echo -e "${GREEN}✓ Nginx is operational${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Nginx status unclear${NC}"
fi

# Test 6: SSL certificates
echo -e "${YELLOW}[6] Checking SSL certificates...${NC}"
if [ -f "ssl/arthainvestcapital.com.crt" ]; then
    EXPIRY=$(openssl x509 -enddate -noout -in ssl/arthainvestcapital.com.crt 2>/dev/null | cut -d= -f2)
    echo -e "${GREEN}✓ Certificate found (expires: $EXPIRY)${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Certificate file not found${NC}"
    ((FAILED++))
fi

# Test 7: Environment variables
echo -e "${YELLOW}[7] Checking environment configuration...${NC}"
if grep -q "DB_PASSWORD" .env.production && ! grep -q "CHANGE_TO_STRONG_PASSWORD" .env.production; then
    echo -e "${GREEN}✓ Environment properly configured${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Environment configuration incomplete${NC}"
    ((FAILED++))
fi

# Test 8: Disk space
echo -e "${YELLOW}[8] Checking disk space...${NC}"
DISK_FREE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$DISK_FREE" -gt 10 ]; then
    echo -e "${GREEN}✓ Sufficient disk space: ${DISK_FREE}GB free${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Low disk space: ${DISK_FREE}GB free${NC}"
    ((FAILED++))
fi

# Test 9: Docker images
echo -e "${YELLOW}[9] Checking Docker images...${NC}"
IMAGES=$(docker-compose config --services | wc -l)
IMAGES_BUILT=$(docker images | grep -E "arthainvest|postgres|nginx" | wc -l)
if [ "$IMAGES_BUILT" -gt 0 ]; then
    echo -e "${GREEN}✓ Docker images present${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Docker images not found${NC}"
    ((FAILED++))
fi

# Test 10: Logs
echo -e "${YELLOW}[10] Checking logs for errors...${NC}"
ERROR_COUNT=$(docker-compose logs app 2>/dev/null | grep -i "error\|failed" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ No errors in application logs${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Found $ERROR_COUNT error lines in logs${NC}"
    echo "Recent errors:"
    docker-compose logs app 2>/dev/null | grep -i "error\|failed" | tail -5
fi

# Summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Verification Summary                                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Passed: ${GREEN}$PASSED/10${NC}"
echo -e "Failed: ${RED}$FAILED/10${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo -e "${BLUE}Service URLs:${NC}"
    echo "  Application: https://$DOMAIN"
    echo "  API: https://$DOMAIN/api"
    echo "  Dashboard: https://$DOMAIN/analytics-dashboard.html"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "  View logs: docker-compose logs -f app"
    echo "  Check status: docker-compose ps"
    echo "  Restart: docker-compose restart"
    echo "  Stop: docker-compose down"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some checks failed${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "  1. Check logs: docker-compose logs app"
    echo "  2. Restart services: docker-compose restart"
    echo "  3. Review DEPLOYMENT.md for common issues"
    echo ""
    exit 1
fi
