#!/bin/bash

################################################################################
# ArthaInvest CRM - Real-time Monitoring Script
# Monitor deployment health in real-time
# Usage: bash monitor-deployment.sh
################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DOMAIN="arthainvestcapital.com"

clear

while true; do
    clear
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  ArthaInvest CRM - Real-time Monitoring Dashboard          ║${NC}"
    echo -e "${BLUE}║  $(date '+%Y-%m-%d %H:%M:%S') $(printf '%27s' "")║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Container Status
    echo -e "${YELLOW}CONTAINER STATUS:${NC}"
    docker-compose ps 2>/dev/null | tail -n +2 | while read line; do
        if echo "$line" | grep -q "Up"; then
            echo -e "${GREEN}✓ $line${NC}"
        else
            echo -e "${RED}✗ $line${NC}"
        fi
    done
    echo ""

    # Application Health
    echo -e "${YELLOW}APPLICATION HEALTH:${NC}"
    echo -n "  Web Server (3000): "
    if curl -f -s http://localhost:3000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
    else
        echo -e "${RED}✗ Unhealthy${NC}"
    fi

    echo -n "  Database (5432): "
    if docker-compose exec -T postgres pg_isready -U arthainvest &> /dev/null; then
        echo -e "${GREEN}✓ Ready${NC}"
    else
        echo -e "${RED}✗ Not ready${NC}"
    fi

    echo -n "  Reverse Proxy (80/443): "
    if nc -zv localhost 80 &> /dev/null; then
        echo -e "${GREEN}✓ Listening${NC}"
    else
        echo -e "${RED}✗ Not listening${NC}"
    fi
    echo ""

    # Resource Usage
    echo -e "${YELLOW}RESOURCE USAGE:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | grep -E "app|postgres|nginx|CONTAINER" || echo "  Unable to retrieve stats"
    echo ""

    # Recent Errors
    echo -e "${YELLOW}RECENT ERRORS (Last 5):${NC}"
    ERROR_COUNT=$(docker-compose logs app 2>/dev/null | grep -i "error\|failed" | tail -5 | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        docker-compose logs app 2>/dev/null | grep -i "error\|failed" | tail -5 | sed 's/^/  /'
    else
        echo -e "${GREEN}  ✓ No recent errors${NC}"
    fi
    echo ""

    # Database Status
    echo -e "${YELLOW}DATABASE STATUS:${NC}"
    CONNECTIONS=$(docker-compose exec -T postgres psql -U arthainvest -d arthainvest_crm -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | tail -1 | xargs)
    echo "  Active Connections: $CONNECTIONS"

    TABLES=$(docker-compose exec -T postgres psql -U arthainvest -d arthainvest_crm -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tail -1 | xargs)
    echo "  Database Tables: $TABLES"
    echo ""

    # Disk Space
    echo -e "${YELLOW}DISK SPACE:${NC}"
    df -h . | tail -1 | awk '{print "  Used: " $3 " / Total: " $2 " (Available: " $4 ")"}'
    echo ""

    # Latest Logs
    echo -e "${YELLOW}LATEST LOGS:${NC}"
    docker-compose logs --tail=3 app 2>/dev/null | sed 's/^/  /'
    echo ""

    # Instructions
    echo -e "${BLUE}CONTROLS:${NC}"
    echo "  [Ctrl+C] Exit monitoring"
    echo "  [Enter] Refresh (auto-refreshes every 10 seconds)"
    echo ""
    echo -e "${GREEN}Last updated: $(date '+%H:%M:%S')${NC}"

    # Auto-refresh every 10 seconds
    sleep 10
done
