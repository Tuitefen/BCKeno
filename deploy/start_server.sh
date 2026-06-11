#!/bin/bash
set -e

export BCKENO_DATA_DIR=/www/cpgame-runtime/data
export BCKENO_LOG_DIR=/www/cpgame-runtime/logs
export BCKENO_BACKUP_DIR=/www/cpgame-runtime/backups
export TZ=Asia/Shanghai

cd /www/wwwroot/cpgame

if [ -x /www/wwwroot/cpgame/.venv/bin/python ]; then
  exec /www/wwwroot/cpgame/.venv/bin/python /www/wwwroot/cpgame/keno_dashboard_server.py
fi

exec python3 /www/wwwroot/cpgame/keno_dashboard_server.py
