#!/bin/bash

################################################################################
# ArthaInvest CRM - Backup & Restore Script
# Safe backup and recovery of database and configuration
# Usage: bash backup-restore.sh [backup|restore]
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ArthaInvest CRM - Backup & Restore                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

# Create backups directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Function: Create backup
backup() {
    echo -e "${YELLOW}Creating backup at $BACKUP_DIR/backup_$TIMESTAMP...${NC}"

    # Backup database
    echo -e "${YELLOW}Backing up database...${NC}"
    docker-compose exec -T postgres pg_dump -U arthainvest arthainvest_crm > "$BACKUP_DIR/db_$TIMESTAMP.sql"
    echo -e "${GREEN}✓ Database backed up${NC}"

    # Backup configuration
    echo -e "${YELLOW}Backing up configuration...${NC}"
    cp .env.production "$BACKUP_DIR/env_$TIMESTAMP.bak"
    cp docker-compose.yml "$BACKUP_DIR/docker-compose_$TIMESTAMP.yml.bak"
    echo -e "${GREEN}✓ Configuration backed up${NC}"

    # Backup Docker volumes (if space permits)
    echo -e "${YELLOW}Creating compressed backup archive...${NC}"
    tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" \
        "$BACKUP_DIR/db_$TIMESTAMP.sql" \
        "$BACKUP_DIR/env_$TIMESTAMP.bak" \
        "$BACKUP_DIR/docker-compose_$TIMESTAMP.yml.bak" \
        2>/dev/null || true

    echo ""
    echo -e "${GREEN}✓ Backup complete!${NC}"
    echo -e "${BLUE}Backup location: $BACKUP_DIR/backup_$TIMESTAMP.tar.gz${NC}"
    echo ""
    echo -e "${BLUE}Backup files:${NC}"
    ls -lh "$BACKUP_DIR"/backup_$TIMESTAMP* | awk '{print "  " $9 " (" $5 ")"}'
}

# Function: List backups
list_backups() {
    echo -e "${BLUE}Available backups:${NC}"
    ls -lh "$BACKUP_DIR"/ 2>/dev/null | grep -E "db_|env_|docker-compose_|backup_.*\.tar\.gz" | awk '{printf "  %s (%s)\n", $9, $5}' | sort -r
}

# Function: Restore backup
restore() {
    if [ -z "$1" ]; then
        echo -e "${YELLOW}Which backup to restore?${NC}"
        list_backups
        echo ""
        read -p "Enter backup filename: " BACKUP_FILE
    else
        BACKUP_FILE="$1"
    fi

    BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILE"

    if [ ! -f "$BACKUP_PATH" ]; then
        echo -e "${RED}✗ Backup file not found: $BACKUP_PATH${NC}"
        exit 1
    fi

    echo -e "${YELLOW}⚠ WARNING: This will restore the database to a previous state${NC}"
    echo -e "${YELLOW}Current data will be lost. Continue? (yes/no)${NC}"
    read -p "Continue? " CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        echo -e "${YELLOW}Restore cancelled${NC}"
        exit 0
    fi

    echo -e "${YELLOW}Stopping application...${NC}"
    docker-compose down

    echo -e "${YELLOW}Dropping current database...${NC}"
    docker-compose up -d postgres
    sleep 5
    docker-compose exec -T postgres dropdb -U arthainvest arthainvest_crm 2>/dev/null || true
    docker-compose exec -T postgres createdb -U arthainvest arthainvest_crm

    echo -e "${YELLOW}Restoring database from backup...${NC}"
    docker-compose exec -T postgres psql -U arthainvest arthainvest_crm < "$BACKUP_PATH"

    echo -e "${YELLOW}Starting application...${NC}"
    docker-compose up -d

    sleep 5

    if docker-compose exec -T postgres pg_isready -U arthainvest &> /dev/null; then
        echo -e "${GREEN}✓ Restore complete!${NC}"
        echo -e "${BLUE}Database restored from: $BACKUP_FILE${NC}"
    else
        echo -e "${RED}✗ Restore may have failed${NC}"
        exit 1
    fi
}

# Main logic
case "${1:-menu}" in
    backup)
        backup
        ;;
    restore)
        restore "$2"
        ;;
    list)
        list_backups
        ;;
    *)
        echo -e "${BLUE}Usage:${NC}"
        echo "  bash backup-restore.sh backup              Create backup"
        echo "  bash backup-restore.sh restore <file>      Restore from backup"
        echo "  bash backup-restore.sh list                List backups"
        echo ""
        echo -e "${BLUE}Examples:${NC}"
        echo "  bash backup-restore.sh backup"
        echo "  bash backup-restore.sh restore db_20240101_120000.sql"
        echo "  bash backup-restore.sh list"
        ;;
esac
