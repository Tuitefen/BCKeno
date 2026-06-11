#!/bin/bash
set -e

DATE=$(date +%F)
BACKUP_ROOT=/www/backup/cpgame/$DATE
DATA_DIR=/www/cpgame-runtime/data

mkdir -p "$BACKUP_ROOT"

if command -v sqlite3 >/dev/null 2>&1; then
  sqlite3 "$DATA_DIR/prediction_tracking.sqlite3" ".backup '$BACKUP_ROOT/prediction_tracking.sqlite3'"
else
  cp "$DATA_DIR/prediction_tracking.sqlite3" "$BACKUP_ROOT/prediction_tracking.sqlite3"
fi

cp "$DATA_DIR"/bc_*_history.csv "$BACKUP_ROOT"/
cp "$DATA_DIR"/prediction_auto_config.json "$BACKUP_ROOT"/
cp "$DATA_DIR"/telegram_bot_config.local.json "$BACKUP_ROOT"/
cp "$DATA_DIR"/telegram_bot_state.local.json "$BACKUP_ROOT"/

find /www/backup/cpgame -maxdepth 1 -type d -mtime +14 -exec rm -rf {} \;
