# BCKeno Local Run And Paths

## Start

```powershell
.\start_server.ps1
```

Or directly:

```powershell
python .\keno_dashboard_server.py
```

Default URL:

```text
http://127.0.0.1:8787
```

## Runtime Directories

By default, runtime files are grouped under:

```text
data/      CSV history, SQLite tracking database, JSON runtime state
logs/      reserved for logs
backups/   reserved for backups
web/       static frontend
```

The server creates these directories on startup.

## Environment Overrides

Set these before starting the server if you want runtime data somewhere else:

```powershell
$env:BCKENO_DATA_DIR = "D:\BCKeno\data"
$env:BCKENO_LOG_DIR = "D:\BCKeno\logs"
$env:BCKENO_BACKUP_DIR = "D:\BCKeno\backups"
python .\keno_dashboard_server.py
```

## Important Files In `data/`

```text
bc_spain_l_express_20_70_history.csv
bc_poland_keno_20_70_history.csv
bc_russia_rapido_8_20_history.csv
bc_italy_win_for_life_10_20_history.csv
prediction_tracking.sqlite3
prediction_tracking.json
prediction_auto_config.json
simulated_bets.jsonl
```

## aaPanel / GitHub Deploy

Recommended server layout:

```text
/www/wwwroot/cpgame/       code cloned from GitHub
/www/wwwroot/cpgame/cpgame-runtime/data/  runtime data, SQLite, CSV, local Telegram config
/www/wwwroot/cpgame/cpgame-runtime/logs/
/www/wwwroot/cpgame/cpgame-runtime/backups/
```

Clone code:

```bash
cd /www/wwwroot
git clone https://github.com/Tuitefen/BCKeno.git cpgame
cd /www/wwwroot/cpgame
python3 -m venv .venv
chmod +x deploy/start_server.sh
chmod +x deploy/backup_cpgame.sh
/www/wwwroot/cpgame/.venv/bin/python -m py_compile keno_dashboard_server.py
```

Create runtime directories:

```bash
mkdir -p /www/wwwroot/cpgame/cpgame-runtime/data
mkdir -p /www/wwwroot/cpgame/cpgame-runtime/logs
mkdir -p /www/wwwroot/cpgame/cpgame-runtime/backups
```

Upload local runtime data manually to:

```text
/www/wwwroot/cpgame/cpgame-runtime/data/
```

Do not commit or upload runtime secrets to GitHub:

```text
data/prediction_tracking.sqlite3
data/telegram_bot_config.local.json
data/telegram_bot_state.local.json
```

aaPanel Supervisor:

```text
Name: cpgame
Run dir: /www/wwwroot/cpgame
Start command: /www/wwwroot/cpgame/deploy/start_server.sh
User: root
Autostart: enabled
Autorestart: enabled
```

Production note:

```text
The current server manages cpgame from the aaPanel Super/Supervisor plugin UI.
The `supervisorctl` command may not exist in SSH. After `git pull`, restart
`cpgame` from the aaPanel Super UI, then verify the new process from SSH.
```

Update existing server:

```bash
cd /www/wwwroot/cpgame
git pull origin main
/www/wwwroot/cpgame/.venv/bin/python -m py_compile keno_dashboard_server.py fetch_official_supplements.py
```

Then restart `cpgame` from the aaPanel Super/Supervisor plugin UI.

Verify after restart:

```bash
ps -ef | grep keno_dashboard_server.py | grep -v grep
ss -ltnp | grep 8787
curl -m 10 -sS http://127.0.0.1:8787/api/prediction-auto > /tmp/cpgame_auto.json
python3 -m json.tool /tmp/cpgame_auto.json | head -80
```

C-plan daily miss display can be checked with:

```bash
curl -m 20 -sS "http://127.0.0.1:8787/api/predictions?game=poland_keno_20_70&panel=m&autoSync=0" > /tmp/cpgame_prediction_m.json
python3 -m json.tool /tmp/cpgame_prediction_m.json | grep -A2 dailyMissStreak
```

C-plan naming and current backtest mapping can be checked with:

```bash
curl -m 20 -sS "http://127.0.0.1:8787/api/current-staking-backtest?game=poland_keno_20_70&source=m&slot=p3_1&startDateTime=2026-06-12%2000:00&endDateTime=2026-06-12%2023:59&timeZone=Asia/Shanghai" > /tmp/cpgame_current_backtest_p3_1.json
python3 -m json.tool /tmp/cpgame_current_backtest_p3_1.json | grep -E '"label": "3码候选#3"|"wins"|"totalPayout"' | head -40
```

The current backtest UI labels should match prediction/tracking labels:

```text
2码候选#1
2码候选#2
3码候选#3
3码候选#4
```

The deploy script automatically reads runtime data from:

```text
/www/wwwroot/cpgame/cpgame-runtime/data/
```

Nginx reverse proxy target:

```text
http://127.0.0.1:8787
```

Recommended Nginx location:

```nginx
location / {
    proxy_pass http://127.0.0.1:8787;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_read_timeout 300;
    proxy_connect_timeout 60;
    proxy_send_timeout 300;
}
```

Do not expose port `8787` publicly.

Daily backup command for aaPanel scheduled task:

```bash
/www/wwwroot/cpgame/deploy/backup_cpgame.sh
```
