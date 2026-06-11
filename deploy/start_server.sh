#!/bin/bash
set -e

APP_DIR=$(cd "$(dirname "$0")/.." && pwd)
RUNTIME_DIR="${APP_DIR}/cpgame-runtime"

export BCKENO_DATA_DIR="${BCKENO_DATA_DIR:-${RUNTIME_DIR}/data}"
export BCKENO_LOG_DIR="${BCKENO_LOG_DIR:-${RUNTIME_DIR}/logs}"
export BCKENO_BACKUP_DIR="${BCKENO_BACKUP_DIR:-${RUNTIME_DIR}/backups}"
export TZ=Asia/Shanghai

mkdir -p "$BCKENO_DATA_DIR" "$BCKENO_LOG_DIR" "$BCKENO_BACKUP_DIR"

cd "$APP_DIR"

if [ -x "$APP_DIR/.venv/bin/python" ]; then
  exec "$APP_DIR/.venv/bin/python" "$APP_DIR/keno_dashboard_server.py"
fi

exec python3 "$APP_DIR/keno_dashboard_server.py"
