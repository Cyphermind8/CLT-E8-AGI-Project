# FILE: scripts/Open-CLTDashboard.ps1
$root = Split-Path $PSScriptRoot -Parent
$logs = Join-Path $root "logs"
$dash = Join-Path $logs "dashboard.html"
if (-not (Test-Path $dash)) {
  python (Join-Path $root "scripts\build_dashboard.py") | Out-Null
}
Start-Process $dash