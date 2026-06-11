#!/bin/bash
set -e

APP_DIR=$(cd "$(dirname "$0")/.." && pwd)
DATE=$(date +%F)
RUNTIME_DIR="${APP_DIR}/cpgame-runtime"
DATA_DIR="${BCKENO_DATA_DIR:-${RUNTIME_DIR}/data}"
BACKUP_ROOT="${BCKENO_BACKUP_DIR:-${RUNTIME_DIR}/backups}/$DATE"

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

find "${BCKENO_BACKUP_DIR:-${RUNTIME_DIR}/backups}" -maxdepth 1 -type d -mtime +14 -exec rm -rf {} \;
