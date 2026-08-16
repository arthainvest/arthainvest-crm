#!/bin/bash

################################################################################
# ArthaInvest CRM - Advanced Alerting System with Slack Integration
# Monitors services and sends alerts via Slack webhooks
# Setup cron: */5 * * * * /path/to/alerting-system.sh
################################################################################

set -e

# Configuration
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-https://hooks.slack.com/services/YOUR/WEBHOOK/URL}"
CHECK_INTERVAL=300  # 5 minutes
ALERT_DIR="./logs/alerts"
STATE_FILE="$ALERT_DIR/.alert_state"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create alert directory
mkdir -p "$ALERT_DIR"

# Initialize state file
if [ ! -f "$STATE_FILE" ]; then
    echo "app_status=healthy" > "$STATE_FILE"
    echo "db_status=healthy" >> "$STATE_FILE"
    echo "disk_status=healthy" >> "$STATE_FILE"
    echo "memory_status=healthy" >> "$STATE_FILE"
fi

# Load previous state
source "$STATE_FILE"

# Function: Send Slack alert
send_slack_alert() {
    local severity=$1
    local service=$2
    local message=$3
    local color=$4

    if [ -z "$SLACK_WEBHOOK" ] || [ "$SLACK_WEBHOOK" == "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" ]; then
        echo "⚠ Slack webhook not configured"
        return
    fi

    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local hostname=$(hostname)

    curl -X POST "$SLACK_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d @- << EOF 2>/dev/null || true
{
    "attachments": [
        {
            "color": "$color",
            "title": "🚨 $severity Alert: $service",
            "text": "$message",
            "fields": [
                {"title": "Server", "value": "$hostname", "short": true},
                {"title": "Time", "value": "$timestamp", "short": true},
                {"title": "Environment", "value": "Production", "short": true}
            ],
            "footer": "ArthaInvest CRM Monitoring",
            "ts": $(date +%s)
        }
    ]
}
EOF
}

# Function: Check application health
check_app_health() {
    if curl -f -s http://localhost:3000/health > /dev/null 2>&1; then
        return 0  # Healthy
    else
        return 1  # Unhealthy
    fi
}

# Function: Check database health
check_db_health() {
    if docker-compose exec -T postgres pg_isready -U arthainvest &> /dev/null; then
        return 0  # Healthy
    else
        return 1  # Unhealthy
    fi
}

# Function: Check disk space
check_disk_space() {
    local disk_free=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')

    if [ "$disk_free" -lt 5 ]; then
        return 2  # Critical
    elif [ "$disk_free" -lt 10 ]; then
        return 1  # Warning
    else
        return 0  # Healthy
    fi
}

# Function: Check memory usage
check_memory_usage() {
    local mem_free=$(free -g | tail -1 | awk '{print $7}')

    if [ "$mem_free" -lt 1 ]; then
        return 2  # Critical
    elif [ "$mem_free" -lt 2 ]; then
        return 1  # Warning
    else
        return 0  # Healthy
    fi
}

# Function: Check error rate in logs
check_error_rate() {
    local error_count=$(docker-compose logs --tail=100 app 2>/dev/null | grep -i "error\|failed\|exception" | wc -l)

    if [ "$error_count" -gt 10 ]; then
        return 2  # Critical
    elif [ "$error_count" -gt 5 ]; then
        return 1  # Warning
    else
        return 0  # Healthy
    fi
}

# Function: Check container count
check_containers() {
    local running=$(docker-compose ps -q | wc -l)
    local expected=3  # app, postgres, nginx

    if [ "$running" -lt "$expected" ]; then
        return 2  # Critical - Missing containers
    else
        return 0  # Healthy
    fi
}

# Main monitoring logic
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running health checks..."

# Check Application
echo -n "Checking application... "
if check_app_health; then
    echo -e "${GREEN}✓ Healthy${NC}"
    new_app_status="healthy"
    if [ "$app_status" != "healthy" ]; then
        send_slack_alert "RECOVERED" "Application" "Web server is back online and responding" "good"
    fi
else
    echo -e "${RED}✗ Unhealthy${NC}"
    new_app_status="unhealthy"
    if [ "$app_status" == "healthy" ]; then
        send_slack_alert "CRITICAL" "Application" "Web server is not responding on port 3000" "danger"
    fi
fi

# Check Database
echo -n "Checking database... "
if check_db_health; then
    echo -e "${GREEN}✓ Healthy${NC}"
    new_db_status="healthy"
    if [ "$db_status" != "healthy" ]; then
        send_slack_alert "RECOVERED" "Database" "PostgreSQL database is back online" "good"
    fi
else
    echo -e "${RED}✗ Unhealthy${NC}"
    new_db_status="unhealthy"
    if [ "$db_status" == "healthy" ]; then
        send_slack_alert "CRITICAL" "Database" "PostgreSQL database is not responding" "danger"
    fi
fi

# Check Disk Space
echo -n "Checking disk space... "
if check_disk_space; then
    result=$?
    if [ "$result" -eq 0 ]; then
        echo -e "${GREEN}✓ OK${NC}"
        new_disk_status="healthy"
    elif [ "$result" -eq 1 ]; then
        echo -e "${YELLOW}⚠ Warning${NC}"
        new_disk_status="warning"
        send_slack_alert "WARNING" "Disk Space" "Disk space is running low (< 10GB available)" "warning"
    else
        echo -e "${RED}✗ Critical${NC}"
        new_disk_status="critical"
        send_slack_alert "CRITICAL" "Disk Space" "Critical disk space (< 5GB available). Immediate action required!" "danger"
    fi
else
    echo -e "${GREEN}✓ OK${NC}"
    new_disk_status="healthy"
fi

# Check Memory Usage
echo -n "Checking memory usage... "
if check_memory_usage; then
    result=$?
    if [ "$result" -eq 0 ]; then
        echo -e "${GREEN}✓ OK${NC}"
        new_memory_status="healthy"
    else
        echo -e "${YELLOW}⚠ Warning${NC}"
        new_memory_status="warning"
        send_slack_alert "WARNING" "Memory Usage" "Server memory usage is high" "warning"
    fi
fi

# Check Container Status
echo -n "Checking containers... "
if check_containers; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ Critical${NC}"
    send_slack_alert "CRITICAL" "Docker" "One or more containers are not running" "danger"
fi

# Check Error Rate
echo -n "Checking error rate... "
if check_error_rate; then
    result=$?
    if [ "$result" -eq 0 ]; then
        echo -e "${GREEN}✓ OK${NC}"
    else
        echo -e "${YELLOW}⚠ Warning${NC}"
        send_slack_alert "WARNING" "Errors" "High error rate detected in application logs" "warning"
    fi
fi

# Update state file
cat > "$STATE_FILE" << EOF
app_status=$new_app_status
db_status=$new_db_status
disk_status=$new_disk_status
memory_status=$new_memory_status
EOF

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Health checks complete"
