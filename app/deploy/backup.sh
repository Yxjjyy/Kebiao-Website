#!/bin/bash
set -euo pipefail

DATE=$(date +%Y%m%d)
BACKUP_DIR=/home/kebiao/backups
DB_PATH=/home/kebiao/data/app.db

mkdir -p "$BACKUP_DIR"
sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/app-$DATE.db'"
find "$BACKUP_DIR" -name "app-*.db" -mtime +7 -delete
