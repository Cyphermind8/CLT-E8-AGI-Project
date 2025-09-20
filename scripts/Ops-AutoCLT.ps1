# FILE: scripts/Ops-AutoCLT.ps1
[CmdletBinding()]
param(
  [ValidateSet("start","stop","status","restart","schedule","clean")]
  [string]$Cmd,
  [double]$Hours = 1,
  [int]$PauseSeconds = 300,
  [switch]$NoTail,
  [switch]$Force,
  [string]$DailyTime = "02:00",
  [switch]$AtStartup,
  [int]$KeepDays = 7,
  [int]$KeepMin = 3,
  [int]$MaxTotalMB = 200
)

# Robust pathing: figure out scripts dir and repo root
if ($PSScriptRoot) {
  $scriptsDir = $PSScriptRoot
} elseif ($MyInvocation.MyCommand.Path) {
  $scriptsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
} else {
  # fallback if someone dot-sources or runs inline
  $scriptsDir = Join-Path (Get-Location).Path "scripts"
}
$root = Split-Path $scriptsDir -Parent

function Use-Helper([string]$name) {
  $p = Join-Path $scriptsDir $name
  if (-not (Test-Path $p)) { throw "Missing helper: $p" }
  return $p
}

function Show-Usage {
@"
Usage:
  .\scripts\Ops-AutoCLT.ps1 start    [-Hours H] [-PauseSeconds S] [-NoTail] [-Force]
  .\scripts\Ops-AutoCLT.ps1 stop     [-Force]
  .\scripts\Ops-AutoCLT.ps1 status
  .\scripts\Ops-AutoCLT.ps1 restart  [-Hours H] [-PauseSeconds S] [-NoTail] [-Force]
  .\scripts\Ops-AutoCLT.ps1 schedule [-DailyTime HH:mm] [-AtStartup] [-Hours H] [-PauseSeconds S]
  .\scripts\Ops-AutoCLT.ps1 clean    [-KeepDays N] [-KeepMin N] [-MaxTotalMB MB]

Examples:
  .\scripts\Ops-AutoCLT.ps1 start -Hours 1 -PauseSeconds 300 -NoTail
  .\scripts\Ops-AutoCLT.ps1 status
  .\scripts\Ops-AutoCLT.ps1 schedule -DailyTime "02:00" -AtStartup
"@ | Write-Host
}

if (-not $Cmd) { Show-Usage; exit 0 }

switch ($Cmd) {
  'start'    { & (Use-Helper 'Start-AutoCLTLoop.ps1')    -Hours $Hours -PauseSeconds $PauseSeconds -NoTail:$NoTail -Force:$Force }
  'stop'     { & (Use-Helper 'Stop-AutoCLTLoop.ps1')     -Force:$Force }
  'status'   { & (Use-Helper 'Status-AutoCLTLoop.ps1') }
  'restart'  { & (Use-Helper 'Restart-AutoCLTLoop.ps1')  -Hours $Hours -PauseSeconds $PauseSeconds -NoTail:$NoTail -Force:$Force }
  'schedule' { & (Use-Helper 'Schedule-AutoCLTLoop.ps1') -Install -DailyTime $DailyTime -AtStartup:$AtStartup -Hours $Hours -PauseSeconds $PauseSeconds }
  'clean'    { & (Use-Helper 'Clean-AutoCLTLogs.ps1')    -KeepDays $KeepDays -KeepMin $KeepMin -MaxTotalMB $MaxTotalMB }
  default    { Show-Usage }
}