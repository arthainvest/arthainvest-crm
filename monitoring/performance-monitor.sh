#!/bin/bash

################################################################################
# ArthaInvest CRM - Performance Monitoring & Analytics
# Track response times, throughput, and performance metrics
# Usage: bash performance-monitor.sh
################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

METRICS_DIR="./logs/metrics"
REPORT_DIR="./logs/reports"
mkdir -p "$METRICS_DIR" "$REPORT_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
METRICS_FILE="$METRICS_DIR/metrics_$TIMESTAMP.json"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ArthaInvest CRM - Performance Monitoring                  ║${NC}"
echo -e "${BLUE}║  $(date '+%Y-%m-%d %H:%M:%S')                                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function: Measure API response time
measure_api_response() {
    local endpoint=$1
    local total_time=0
    local count=10

    echo -n "Testing endpoint: $endpoint ... "

    for i in $(seq 1 $count); do
        local response_time=$(curl -s -o /dev/null -w "%{time_total}" "http://localhost:3000$endpoint" 2>/dev/null)
        if [ -n "$response_time" ]; then
            total_time=$(echo "$total_time + $response_time" | bc)
        fi
    done

    local avg_time=$(echo "scale=3; $total_time / $count" | bc)
    echo -e "${GREEN}${avg_time}s avg${NC}"
    echo "$avg_time"
}

# Function: Measure database query performance
measure_db_performance() {
    echo -n "Database connection latency... "

    local start=$(date +%s%N)
    docker-compose exec -T postgres pg_isready -U arthainvest &> /dev/null
    local end=$(date +%s%N)

    local latency=$(( ($end - $start) / 1000000 ))  # Convert to milliseconds
    echo -e "${GREEN}${latency}ms${NC}"
}

# Function: Measure throughput (requests per second)
measure_throughput() {
    echo -n "Measuring throughput (30 seconds)... "

    local start=$(date +%s)
    local count=0

    while [ $(($(date +%s) - $start)) -lt 30 ]; do
        curl -s -o /dev/null -w "" "http://localhost:3000/health" 2>/dev/null && ((count++))
    done

    local rps=$(echo "scale=2; $count / 30" | bc)
    echo -e "${GREEN}${rps} req/s${NC}"
}

# Function: Analyze container performance
analyze_containers() {
    echo -e "${YELLOW}Container Performance:${NC}"

    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null | while read line; do
        if echo "$line" | grep -qE "app|postgres|nginx"; then
            echo "  $line"
        fi
    done
}

# Function: Get database statistics
get_db_stats() {
    echo -e "${YELLOW}Database Statistics:${NC}"

    # Connection count
    echo -n "  Active Connections: "
    docker-compose exec -T postgres psql -U arthainvest -d arthainvest_crm -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | tail -1 | xargs

    # Cache hit ratio
    echo -n "  Cache Hit Ratio: "
    docker-compose exec -T postgres psql -U arthainvest -d arthainvest_crm -c "SELECT sum(heap_blks_read) as heap_read, sum(heap_blks_hit) as heap_hit FROM pg_statio_user_tables;" 2>/dev/null | grep -E "[0-9]" | tail -1

    # Table sizes
    echo -e "  Table Sizes:"
    docker-compose exec -T postgres psql -U arthainvest -d arthainvest_crm -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema') ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 5;" 2>/dev/null | tail -n +3 | sed 's/^/    /'
}

# Function: Get system resources
get_system_resources() {
    echo -e "${YELLOW}System Resources:${NC}"

    # CPU load
    echo -n "  CPU Load Average: "
    uptime | awk -F'load average:' '{print $2}'

    # Memory usage
    echo -n "  Memory Usage: "
    free -h | tail -1 | awk '{printf "%s / %s (%.1f%%)\n", $3, $2, ($3/$2)*100}'

    # Disk usage
    echo -n "  Disk Usage: "
    df -h . | tail -1 | awk '{printf "%s / %s (%.1f%%)\n", $3, $2, ($3/$2)*100}'

    # Network stats
    echo -e "  Network Interfaces:"
    ip -s link | grep -A1 "eth0\|ens0\|docker0" | grep -E "bytes" | sed 's/^/    /'
}

# Function: Generate performance report
generate_report() {
    local report_file="$REPORT_DIR/performance_report_$TIMESTAMP.txt"

    {
        echo "ArthaInvest CRM - Performance Report"
        echo "Generated: $(date)"
        echo ""
        echo "API Endpoints Response Time:"
        echo "  /health: $(measure_api_response '/health')"
        echo "  /api/analytics/routing: $(measure_api_response '/api/analytics/routing')"
        echo ""
        echo "Database Performance:"
        measure_db_performance
        echo ""
        echo "Throughput:"
        measure_throughput
        echo ""
        echo "System Information:"
        get_system_resources
    } > "$report_file"

    echo -e "${GREEN}Report saved to: $report_file${NC}"
}

# Main execution
echo -e "${YELLOW}Running Performance Tests...${NC}"
echo ""

# Measure API response times
echo -e "${YELLOW}API Response Times:${NC}"
measure_api_response '/health'
measure_api_response '/api/analytics/routing'
echo ""

# Measure database
echo -e "${YELLOW}Database Performance:${NC}"
measure_db_performance
echo ""

# Measure throughput
echo -e "${YELLOW}Throughput Test:${NC}"
measure_throughput
echo ""

# Container analysis
analyze_containers
echo ""

# Database stats
get_db_stats
echo ""

# System resources
get_system_resources
echo ""

# Generate report
generate_report

echo ""
echo -e "${GREEN}✓ Performance monitoring complete${NC}"
echo ""
echo -e "${BLUE}Metrics stored in: $METRICS_DIR${NC}"
echo -e "${BLUE}Reports stored in: $REPORT_DIR${NC}"
