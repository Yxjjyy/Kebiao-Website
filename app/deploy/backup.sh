#!/bin/bash
set -euo pipefail

# 备份 v2 数据库（生产库），保留 7 天
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/home/kebiao/backups
DB_PATH=/home/kebiao/data/app-v2.db

mkdir -p "$BACKUP_DIR"
sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/app-v2-$DATE.db'"
find "$BACKUP_DIR" -name "app-v2-*.db" -mtime +7 -delete
echo "备份完成: $BACKUP_DIR/app-v2-$DATE.db"
