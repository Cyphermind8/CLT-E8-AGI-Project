# FILE: scripts/Clean-AutoCLTLogs.ps1
[CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact="Low")]
param(
  [int]$KeepDays = 14,      # delete logs older than this many days
  [int]$KeepMin  = 5,       # always keep at least this many newest logs
  [int]$MaxTotalMB          # optional: cap total size; delete oldest until under cap
)

$ErrorActionPreference = "Stop"

# Robust root detection
if ($PSScriptRoot)      { $ScriptDir = $PSScriptRoot }
elseif ($MyInvocation.MyCommand.Path) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
else                   { $ScriptDir = (Get-Location).Path }
try {
  $RepoRoot = Split-Path $ScriptDir -Parent
  if (-not (Test-Path (Join-Path $RepoRoot 'scripts'))) { $RepoRoot = (Get-Location).Path }
} catch { $RepoRoot = (Get-Location).Path }

$LogDir  = Join-Path $RepoRoot "logs"
$PidDir  = Join-Path $RepoRoot "pids"
$Meta    = Join-Path $PidDir  "auto_loop.meta"

if (-not (Test-Path $LogDir)) {
  Write-Host "[i] No log directory found at $LogDir. Nothing to clean."
  exit 0
}

$logs = Get-ChildItem $LogDir -File -Filter 'auto_loop_*.log' -ErrorAction SilentlyContinue
if (-not $logs) {
  Write-Host "[i] No logs to clean in $LogDir."
  exit 0
}

# Prefer not to delete the active log noted in meta (if any)
$activeLog = $null
if (Test-Path $Meta) {
  try {
    $obj = ([System.IO.File]::ReadAllText($Meta) | ConvertFrom-Json)
    if ($obj.log -and (Test-Path $obj.log)) { $activeLog = (Resolve-Path $obj.log).Path }
  } catch {}
}

# Build keep-set (active + newest KeepMin)
$sortedDesc = $logs | Sort-Object LastWriteTime -Descending
$keepNewest = $sortedDesc | Select-Object -First ([Math]::Max(0,$KeepMin))
$KeepSet    = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
foreach ($f in $keepNewest) { $null = $KeepSet.Add((Resolve-Path $f.FullName).Path) }
if ($activeLog) { $null = $KeepSet.Add($activeLog) }

# Phase 1: by age
$cutoff = (Get-Date).AddDays(-$KeepDays)
$candidates = $logs | Where-Object { $_.LastWriteTime -lt $cutoff }

# Exclude protected
$toDelete = @()
foreach ($f in $candidates) {
  $path = (Resolve-Path $f.FullName).Path
  if (-not $KeepSet.Contains($path)) { $toDelete += $f }
}

# Phase 2 (optional): cap total size
$totalBytes = ($logs | Measure-Object Length -Sum).Sum
$maxBytes   = $null
if ($PSBoundParameters.ContainsKey('MaxTotalMB')) { $maxBytes = [int64]$MaxTotalMB * 1MB }

if ($maxBytes -and $totalBytes -gt $maxBytes) {
  $deleteSet = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
  foreach ($f in $toDelete) { $null = $deleteSet.Add((Resolve-Path $f.FullName).Path) }

  $bytesToDelete = ($toDelete | Measure-Object Length -Sum).Sum
  $sortedAsc = $logs | Sort-Object LastWriteTime  # oldest first
  foreach ($f in $sortedAsc) {
    $path = (Resolve-Path $f.FullName).Path
    if ($KeepSet.Contains($path)) { continue }
    if ($deleteSet.Contains($path)) { continue }
    if ( ($totalBytes - $bytesToDelete) -le $maxBytes ) { break }
    $bytesToDelete += $f.Length
    $null = $deleteSet.Add($path)
  }
  # Rebuild $toDelete from deleteSet
  $toDelete = $logs | Where-Object { $deleteSet.Contains((Resolve-Path $_.FullName).Path) }
}

# Execute deletions
$freed = [int64]0
$count = 0
foreach ($f in ($toDelete | Sort-Object LastWriteTime)) {
  if ($PSCmdlet.ShouldProcess($f.FullName, "Remove")) {
    try {
      $len = $f.Length
      Remove-Item -LiteralPath $f.FullName -Force -ErrorAction Stop
      $freed += $len
      $count += 1
      Write-Verbose ("Removed: {0}  ({1:n1} MB)" -f $f.Name, ($len/1MB))
    } catch {
      Write-Warning "Failed to remove $($f.FullName): $($_.Exception.Message)"
    }
  }
}

# Summary
$remain = Get-ChildItem $LogDir -File -Filter 'auto_loop_*.log' -ErrorAction SilentlyContinue
$remainBytes = ($remain | Measure-Object Length -Sum).Sum
Write-Host ("[+] Deleted {0} file(s), freed {1:n1} MB. Remaining: {2} file(s), {3:n1} MB" -f `
  $count, ($freed/1MB), ($remain.Count), ($remainBytes/1MB))