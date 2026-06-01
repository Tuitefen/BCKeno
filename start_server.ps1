$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not $env:BCKENO_DATA_DIR) {
  $env:BCKENO_DATA_DIR = Join-Path $Root "data"
}
if (-not $env:BCKENO_LOG_DIR) {
  $env:BCKENO_LOG_DIR = Join-Path $Root "logs"
}
if (-not $env:BCKENO_BACKUP_DIR) {
  $env:BCKENO_BACKUP_DIR = Join-Path $Root "backups"
}

New-Item -ItemType Directory -Force -Path $env:BCKENO_DATA_DIR, $env:BCKENO_LOG_DIR, $env:BCKENO_BACKUP_DIR | Out-Null

python .\keno_dashboard_server.py
