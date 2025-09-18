# FILE: C:\AI_Project\scripts\schedule_ci.ps1
Param(
  [switch]$Register,
  [int]$Cycles = 30,
  [int]$TimeBudgetMin = 180
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$RunScript  = Join-Path $PSScriptRoot 'run_ci.ps1'
$LogsDir    = Join-Path $ProjectRoot 'logs'
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

if ($Register) {
  $taskName = 'AI_Project_Nightly_CI'
  $ps = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
  $taskCmd = "$ps -NoProfile -ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Path)`""
  schtasks /Create /TN $taskName /SC DAILY /ST 02:00 /RU "SYSTEM" /TR $taskCmd /F | Out-Null
  Write-Output "Registered scheduled task '$taskName' (daily 02:00 local) to run this script."
  exit 0
}

# ----- Run CI now (used by the scheduled task) -----
Set-Location $ProjectRoot

# Activate venv + env
$venv = Join-Path $ProjectRoot '.venv\Scripts\Activate.ps1'
if (Test-Path $venv) { & $venv }
$env:PYTHONPATH = "."
$env:CLT_E8_USE_LLM = "1"
$env:OPENAI_TEMPERATURE = "0"
$env:OPENAI_MAX_TOKENS = "600"
$env:OPENAI_REQUEST_TIMEOUT = "180"
$env:HTTPX_TIMEOUT = "180"
$env:REQUESTS_TIMEOUT = "180"
$env:MODEL = "openai/gpt-oss-20b"

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$log   = Join-Path $LogsDir "ci_scheduled_$stamp.log"

# Strict gates
$args = @(
  '-Cycles', $Cycles,
  '-TimeBudgetMin', $TimeBudgetMin,
  '-Determinism', 1,
  '-Population', 1,
  '-MinRate', 1.0,
  '-EqualSpeed', 0.03,
  '-MicroGate',
  '-MicroSpeed', 0.03,
  '-BenchTimeout', 300,
  '-PytestTimeout', 120
)

# Run and capture output
"[$(Get-Date -Format o)] Starting CI..." | Tee-Object -FilePath $log -Append | Out-Null
& $RunScript @args *>> $log 2>&1
"[$(Get-Date -Format o)] CI finished." | Tee-Object -FilePath $log -Append | Out-Null
