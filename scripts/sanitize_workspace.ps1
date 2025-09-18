# FILE: scripts/sanitize_workspace.ps1
# CLT–E8 FenceGuard-lite (hardened):
# - Excludes quarantine/, .venv/, .git/, .pytest_cache/
# - Guarantees unique destination filenames
# - Never re-moves items already in quarantine
# - PS5-safe (no multi-arg .ArgumentList), single-string args only

param()

$ErrorActionPreference = "Stop"

$root   = Get-Location
$qdir   = Join-Path -Path $root -ChildPath "quarantine"
$skip   = @(
  (Join-Path $root "quarantine"),
  (Join-Path $root ".venv"),
  (Join-Path $root ".git"),
  (Join-Path $root ".pytest_cache")
)

# Ensure quarantine directory
if (-not (Test-Path $qdir)) {
  New-Item -ItemType Directory -Path $qdir | Out-Null
}

# Patterns considered risky to keep in the active workspace
$risky = @(
  "*_cand_*.py",
  "*.md",
  "*.markdown",
  "*.ipynb"
)

# Helper: is path under any skip directory?
function Is-SkippedPath([string]$FullPath, [string[]]$SkipRoots) {
  foreach ($s in $SkipRoots) {
    if ($FullPath.StartsWith($s, [System.StringComparison]::OrdinalIgnoreCase)) {
      return $true
    }
  }
  return $false
}

# Helper: generate a unique destination path in quarantine
function New-UniqueDestination([string]$BaseName, [string]$Ext) {
  $ts = Get-Date -Format "yyyyMMdd_HHmmss"
  $dest = Join-Path $qdir "$BaseName`_$ts$Ext"
  $i = 0
  while (Test-Path $dest) {
    $i += 1
    $dest = Join-Path $qdir "$BaseName`_${ts}_$i$Ext"
  }
  return $dest
}

foreach ($pat in $risky) {
  Get-ChildItem -File -Path $root -Filter $pat -Recurse -ErrorAction SilentlyContinue |
    Where-Object {
      # Skip anything inside skip roots
      -not (Is-SkippedPath $_.FullName $skip)
    } |
    ForEach-Object {
      $base = $_.BaseName
      $ext  = $_.Extension
      # If the file is already in quarantine, ignore it
      if (Is-SkippedPath $_.FullName @($qdir)) {
        return
      }
      $dest = New-UniqueDestination -BaseName $base -Ext $ext
      Move-Item -Path $_.FullName -Destination $dest
      Write-Host "[sanitize] moved $($_.FullName) -> $dest"
    }
}

Write-Host "[sanitize] done"
