# FILE: scripts/Restart-AutoCLTLoop.ps1
param(
  [double]$Hours = 1,
  [int]$PauseSeconds = 300,
  [switch]$NoTail,
  [switch]$Force
)

$ErrorActionPreference = "Stop"

# --- Robust repo root detection (works inline or from file) ---
if ($PSScriptRoot) {
  $ScriptDir = $PSScriptRoot
} elseif ($MyInvocation.MyCommand.Path) {
  $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
} else {
  $ScriptDir = (Get-Location).Path
}

try {
  $RepoRoot = Split-Path $ScriptDir -Parent
  if (-not (Test-Path (Join-Path $RepoRoot 'scripts'))) {
    $RepoRoot = (Get-Location).Path
  }
} catch {
  $RepoRoot = (Get-Location).Path
}

$StartScript = Join-Path $RepoRoot 'scripts\Start-AutoCLTLoop.ps1'
$StopScript  = Join-Path $RepoRoot 'scripts\Stop-AutoCLTLoop.ps1'

if (-not (Test-Path $StopScript)) { throw "Missing: $StopScript" }
if (-not (Test-Path $StartScript)) { throw "Missing: $StartScript" }

Write-Host "[*] Restarting Auto CLT Loop..."
Write-Host "    Repo   : $RepoRoot"
Write-Host "    Hours  : $Hours"
Write-Host "    Pause  : $PauseSeconds s"
Write-Host "    NoTail : $NoTail"
Write-Host "    Force  : $Force"
Write-Host ""

# Stop first (force as requested)
& $StopScript -Force:$Force

# Start with requested knobs (pass -Force to ensure clean start if a stray proc lingers)
& $StartScript -Hours $Hours -PauseSeconds $PauseSeconds -NoTail:$NoTail -Force

Write-Host "[+] Restart issued."