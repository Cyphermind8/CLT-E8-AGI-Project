param(
  [double]$Hours = 1,
  [int]$PauseSeconds = 300,
  [switch]$NoTail,
  [switch]$Force
)

$ErrorActionPreference = "Stop"

# Robust repo root detection
if ($PSScriptRoot) { $ScriptDir = $PSScriptRoot }
elseif ($MyInvocation.MyCommand.Path) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
else { $ScriptDir = (Get-Location).Path }
try {
  $RepoRoot = Split-Path $ScriptDir -Parent
  if (-not (Test-Path (Join-Path $RepoRoot 'scripts'))) { $RepoRoot = (Get-Location).Path }
} catch { $RepoRoot = (Get-Location).Path }

# Paths
$LogDir   = Join-Path $RepoRoot "logs"
$PidDir   = Join-Path $RepoRoot "pids"
$PidFile  = Join-Path $PidDir   "auto_loop.pid"
$MetaFile = Join-Path $PidDir   "auto_loop.meta"
$null = New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$null = New-Item -ItemType Directory -Force -Path $PidDir | Out-Null

$Ts      = Get-Date -Format 'yyyyMMdd_HHmmss'
$LogFile = Join-Path $LogDir "auto_loop_$Ts.log"

# Ensure the log file exists so tailing never 404s
if (-not (Test-Path )) { New-Item -ItemType File -Path  -Force | Out-Null }

# Python path (prefer venv)
$PyVenv = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Python = (Test-Path $PyVenv) ? $PyVenv : "python"

# Stop existing if requested
if (Test-Path $PidFile) {
  try { $oldPid = [int](Get-Content $PidFile -Raw).Trim() } catch { $oldPid = $null }
  if ($oldPid) {
    $proc = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
    if ($proc) {
      if ($Force) { Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue; Start-Sleep -Milliseconds 300 }
      else { throw "Already running (PID $oldPid). Use -Force or run Stop-AutoCLTLoop.ps1." }
    }
  }
  Remove-Item $PidFile -ErrorAction SilentlyContinue
  Remove-Item $MetaFile -ErrorAction SilentlyContinue
}

# Build a cmd.exe line that appends BOTH stdout+stderr and records EXITCODE
$CmdCore = `"$Python`" -u -m scripts.run_auto_clt_loop --hours $Hours --pause-seconds $PauseSeconds"
$CmdLine = "$CmdCore >> `"$LogFile`" 2>&1 & echo EXITCODE=%ERRORLEVEL% >> `"$LogFile`""

# Launch hidden via cmd.exe (rock-solid redirection everywhere)
$proc = Start-Process -FilePath "cmd.exe" `
  -ArgumentList "/c", $CmdLine `
  -WorkingDirectory $RepoRoot `
  -WindowStyle Hidden `
  -PassThru

# Persist PID + meta
$proc.Id | Out-File -FilePath $PidFile -Encoding ascii -Force
$meta = @{
  pid     = $proc.Id
  log     = $LogFile
  started = (Get-Date).ToString("s")
  hours   = $Hours
  pause   = $PauseSeconds
  python  = $Python
  repo    = $RepoRoot
}
$meta | ConvertTo-Json -Depth 4 | Out-File -FilePath $MetaFile -Encoding utf8 -Force

Write-Host "[+] Started auto loop. PID $($proc.Id)"
Write-Host "[+] Log: $LogFile"
Write-Host "[i] Tail will follow; Ctrl+C stops the tail (loop keeps running)."

if (-not $NoTail) {
  try { Get-Content -Path $LogFile -Wait -Tail 50 } catch { Write-Warning "Tail stopped: $($_.Exception.Message)" }
} else {
  Write-Host "[i] Tail disabled by -NoTail."
}