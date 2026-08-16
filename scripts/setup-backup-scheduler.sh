#!/bin/bash

################################################################################
# ArthaInvest CRM - Automated Backup Scheduler Setup
# Sets up automated daily backups with retention policy
# Usage: bash setup-backup-scheduler.sh
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ArthaInvest CRM - Backup Scheduler Setup                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
BACKUP_DIR="./backups"
BACKUP_SCRIPT="./scripts/backup-database.sh"
RETENTION_DAYS=30
BACKUP_TIME="02:00"  # 2 AM

# Create backup directory
mkdir -p "$BACKUP_DIR"
chmod 755 "$BACKUP_DIR"

# Create database backup script
cat > "$BACKUP_SCRIPT" << 'EOF'
#!/bin/bash

# Database backup script
# Backs up PostgreSQL database with timestamp and compression

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
BACKUP_COMPRESSED="$BACKUP_FILE.gz"
LOG_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d).log"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Create directory
mkdir -p "$BACKUP_DIR"

log "Starting database backup..."

# Backup database
if docker-compose exec -T postgres pg_dump -U arthainvest arthainvest_crm > "$BACKUP_FILE" 2>> "$LOG_FILE"; then
    log "Database dumped successfully"

    # Compress backup
    if gzip "$BACKUP_FILE" 2>> "$LOG_FILE"; then
        log "Backup compressed successfully"
        log "Backup file: $BACKUP_COMPRESSED ($(du -h $BACKUP_COMPRESSED | cut -f1))"

        # Create checksum
        sha256sum "$BACKUP_COMPRESSED" > "$BACKUP_COMPRESSED.sha256"
        log "Checksum created"
    else
        log "ERROR: Failed to compress backup"
        exit 1
    fi
else
    log "ERROR: Failed to backup database"
    exit 1
fi

# Backup configuration files
log "Backing up configuration files..."
tar -czf "$BACKUP_DIR/config_backup_$TIMESTAMP.tar.gz" \
    .env.production \
    docker-compose.yml \
    nginx.conf \
    2>> "$LOG_FILE" || log "WARNING: Config backup failed"

# Cleanup old backups (retention policy)
RETENTION_DAYS=30
log "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "config_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Count remaining backups
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/db_backup_*.sql.gz 2>/dev/null | wc -l)
log "Backup complete. $BACKUP_COUNT backups retained."

# Verify backup integrity
log "Verifying backup integrity..."
if sha256sum -c "$BACKUP_COMPRESSED.sha256" >> "$LOG_FILE" 2>&1; then
    log "Backup verified successfully"
else
    log "WARNING: Backup verification failed"
fi

log "Backup process finished"
EOF

chmod +x "$BACKUP_SCRIPT"

echo -e "${GREEN}✓ Backup script created at: $BACKUP_SCRIPT${NC}"
echo ""

# Setup cron job
echo -e "${YELLOW}Setting up automated backup via cron...${NC}"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "backup-database.sh"; then
    echo -e "${YELLOW}Cron job already exists. Skipping...${NC}"
else
    # Create cron job
    # Daily backup at 2:00 AM
    CRON_CMD="0 2 * * * cd $(pwd) && bash $BACKUP_SCRIPT"

    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

    echo -e "${GREEN}✓ Cron job created${NC}"
    echo -e "   Schedule: Daily at $BACKUP_TIME"
    echo -e "   Command: $CRON_CMD"
fi

echo ""

# Create backup verification script
cat > "$BACKUP_DIR/.verify-backups.sh" << 'EOF'
#!/bin/bash

# Verify all backups are valid

echo "Verifying backups..."
FAILED=0

for backup in *.sql.gz; do
    if [ -f "$backup" ]; then
        SHA_FILE="$backup.sha256"
        if [ -f "$SHA_FILE" ]; then
            if sha256sum -c "$SHA_FILE" &> /dev/null; then
                echo "✓ $backup"
            else
                echo "✗ $backup (FAILED)"
                ((FAILED++))
            fi
        else
            echo "⚠ $backup (no checksum)"
        fi
    fi
done

if [ $FAILED -eq 0 ]; then
    echo "All backups verified successfully"
    exit 0
else
    echo "WARNING: $FAILED backups failed verification"
    exit 1
fi
EOF

chmod +x "$BACKUP_DIR/.verify-backups.sh"

echo -e "${GREEN}✓ Backup verification script created${NC}"

# Setup backup monitoring
cat > "./scripts/monitor-backups.sh" << 'EOF'
#!/bin/bash

# Monitor backup status and health

BACKUP_DIR="./backups"
DAYS_AGO=7  # Check backups from last 7 days

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Backup Status & Monitoring                               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Last backup
echo "Latest Backup:"
LATEST=$(ls -1t "$BACKUP_DIR"/db_backup_*.sql.gz 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
    LATEST_TIME=$(stat -c %y "$LATEST" | cut -d' ' -f1,2)
    LATEST_SIZE=$(du -h "$LATEST" | cut -f1)
    echo "  File: $(basename $LATEST)"
    echo "  Size: $LATEST_SIZE"
    echo "  Time: $LATEST_TIME"
else
    echo "  No backups found!"
fi

echo ""

# Backup count
echo "Backup Inventory:"
TOTAL_COUNT=$(ls -1 "$BACKUP_DIR"/db_backup_*.sql.gz 2>/dev/null | wc -l)
echo "  Total backups: $TOTAL_COUNT"

# Backup ages
echo "  Backup ages:"
ls -1t "$BACKUP_DIR"/db_backup_*.sql.gz 2>/dev/null | while read backup; do
    AGE=$(($(date +%s) - $(stat -c %Y "$backup")))
    DAYS=$((AGE / 86400))
    HOURS=$(((AGE % 86400) / 3600))
    echo "    - $(basename $backup): ${DAYS}d ${HOURS}h ago"
done

echo ""

# Disk space used by backups
echo "Storage Usage:"
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "  Total backup size: $TOTAL_SIZE"

# Available space
AVAILABLE=$(df -h "$BACKUP_DIR" | tail -1 | awk '{print $4}')
echo "  Available space: $AVAILABLE"

echo ""

# Backup verification status
echo "Backup Verification:"
VALID=0
INVALID=0
for backup in "$BACKUP_DIR"/db_backup_*.sql.gz; do
    if [ -f "$backup" ]; then
        SHA_FILE="$backup.sha256"
        if [ -f "$SHA_FILE" ]; then
            if sha256sum -c "$SHA_FILE" &> /dev/null; then
                ((VALID++))
            else
                echo "  ✗ $(basename $backup) - FAILED"
                ((INVALID++))
            fi
        fi
    fi
done
echo "  Valid: $VALID"
echo "  Invalid: $INVALID"

if [ $INVALID -gt 0 ]; then
    echo ""
    echo "⚠️  WARNING: Some backups failed verification!"
fi

echo ""
echo "Retention Policy:"
echo "  Keep: 30 days"
echo "  Status: Enabled"
echo ""
EOF

chmod +x "./scripts/monitor-backups.sh"

echo -e "${GREEN}✓ Backup monitoring script created${NC}"

# Create backup rotation script
cat > "./scripts/rotate-backups.sh" << 'EOF'
#!/bin/bash

# Manually rotate (delete old) backups

BACKUP_DIR="./backups"
RETENTION_DAYS=${1:-30}

echo "Rotating backups older than $RETENTION_DAYS days..."

DELETED=0
for backup in "$BACKUP_DIR"/db_backup_*.sql.gz; do
    if [ -f "$backup" ]; then
        if [ $(( $(date +%s) - $(stat -c %Y "$backup") )) -gt $((RETENTION_DAYS * 86400)) ]; then
            rm "$backup"
            rm -f "$backup.sha256"
            echo "  Deleted: $(basename $backup)"
            ((DELETED++))
        fi
    fi
done

echo "✓ Deleted $DELETED old backups"
EOF

chmod +x "./scripts/rotate-backups.sh"

echo -e "${GREEN}✓ Backup rotation script created${NC}"

# Create README for backups
cat > "$BACKUP_DIR/README.md" << 'EOF'
# Database Backups

This directory contains automated database backups.

## Backup Schedule

- **Frequency:** Daily
- **Time:** 2:00 AM IST
- **Retention:** 30 days
- **Format:** Compressed SQL dumps (.sql.gz)

## Backup Files

Each backup includes:
- Full PostgreSQL database dump
- Configuration files
- SHA256 checksums for verification

## Available Scripts

### Monitor Backups
```bash
cd ..
bash scripts/monitor-backups.sh
```

### Verify Backup Integrity
```bash
cd ..
bash backups/.verify-backups.sh
```

### Rotate/Cleanup Backups
```bash
cd ..
bash scripts/rotate-backups.sh 30
```

### Manual Backup
```bash
cd ..
bash scripts/backup-database.sh
```

### Restore Backup
```bash
cd ..
bash backup-restore.sh restore db_backup_20240101_020000.sql.gz
```

## Storage

- **Current size:** See `monitor-backups.sh` output
- **Typical size per backup:** 50MB - 500MB (depends on data)
- **Storage requirements:** 30 * avg_size (30-day retention)

## Verification

All backups include SHA256 checksums. Verify with:

```bash
sha256sum -c db_backup_20240101_020000.sql.gz.sha256
```

## Recovery

If you need to restore:

```bash
bash ../backup-restore.sh restore db_backup_20240101_020000.sql.gz
```

This will:
1. Stop the application
2. Drop current database
3. Restore from backup
4. Restart the application

## Monitoring

Check backup status daily:

```bash
bash ../scripts/monitor-backups.sh
```

## Alerts

The alerting system monitors:
- Backup completion (daily)
- Backup size (unusual changes)
- Backup age (staleness)
- Verification failures
- Disk space available

EOF

echo -e "${GREEN}✓ Backup README created${NC}"

# Display crontab
echo ""
echo -e "${BLUE}Current Cron Schedule:${NC}"
crontab -l 2>/dev/null | grep -E "backup|cron" || echo "No cron jobs found"

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✓ Backup Scheduler Setup Complete!${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}Scheduled Backups:${NC}"
echo "  Daily: 2:00 AM IST"
echo "  Retention: 30 days"
echo "  Location: ./backups/"
echo ""

echo -e "${BLUE}Available Commands:${NC}"
echo "  Monitor:      bash scripts/monitor-backups.sh"
echo "  Verify:       bash backups/.verify-backups.sh"
echo "  Rotate:       bash scripts/rotate-backups.sh"
echo "  Manual:       bash scripts/backup-database.sh"
echo "  Restore:      bash backup-restore.sh restore <filename>"
echo ""

echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Test backup: bash scripts/backup-database.sh"
echo "  2. Monitor:     bash scripts/monitor-backups.sh"
echo "  3. Schedule:    crontab -l (verify job is there)"
echo ""

echo -e "${GREEN}✓ Setup complete! Backups will run automatically.${NC}"
