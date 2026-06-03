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
