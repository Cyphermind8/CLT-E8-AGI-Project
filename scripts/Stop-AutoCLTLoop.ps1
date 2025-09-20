param([switch]$Force)

$ErrorActionPreference = "Stop"

# Robust root
if ($PSScriptRoot) { $ScriptDir = $PSScriptRoot }
elseif ($MyInvocation.MyCommand.Path) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
else { $ScriptDir = (Get-Location).Path }
try {
  $RepoRoot = Split-Path $ScriptDir -Parent
  if (-not (Test-Path (Join-Path $RepoRoot 'scripts'))) { $RepoRoot = (Get-Location).Path }
} catch { $RepoRoot = (Get-Location).Path }

$PidFile  = Join-Path $RepoRoot "pids\auto_loop.pid"
$MetaFile = Join-Path $RepoRoot "pids\auto_loop.meta"

if (-not (Test-Path $PidFile)) {
  Write-Host "[i] No PID file found at $PidFile. Nothing to stop."
  exit 0
}

try { $pid = [int](Get-Content $PidFile -Raw).Trim() } catch {
  Write-Warning "Invalid PID file; removing."
  Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
  Remove-Item $MetaFile -Force -ErrorAction SilentlyContinue
  exit 0
}

# Kill any children first (python/cmd)
Get-CimInstance Win32_Process -Filter "ParentProcessId=$pid" -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force:$Force -ErrorAction SilentlyContinue }

# Kill wrapper last
Stop-Process -Id $pid -Force:$Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 200

Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
Remove-Item $MetaFile -Force -ErrorAction SilentlyContinue
Write-Host "[+] Auto loop stopped (or already not running)."