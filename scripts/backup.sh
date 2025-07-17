#!/bin/bash

# LISWMC Database Backup Script
# This script creates regular backups of the LISWMC database

set -e

# Configuration
DB_HOST=${DB_HOST:-postgres}
DB_NAME=${POSTGRES_DB:-liswmc_db}
DB_USER=${POSTGRES_USER:-liswmc_user}
BACKUP_DIR=${BACKUP_DIR:-/backups}
RETENTION_DAYS=${RETENTION_DAYS:-7}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate timestamp for backup filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/liswmc_backup_$TIMESTAMP.sql"

echo "Starting database backup at $(date)"
echo "Database: $DB_NAME"
echo "Host: $DB_HOST"
echo "User: $DB_USER"

# Create database dump
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --format=plain \
    --no-owner \
    --no-privileges \
    > "$BACKUP_FILE"

# Compress the backup
gzip "$BACKUP_FILE"
BACKUP_FILE="$BACKUP_FILE.gz"

echo "Backup completed: $BACKUP_FILE"
echo "Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"

# Clean up old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "liswmc_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# List remaining backups
echo "Remaining backups:"
ls -lh "$BACKUP_DIR"/liswmc_backup_*.sql.gz 2>/dev/null || echo "No backups found"

echo "Backup process completed at $(date)"