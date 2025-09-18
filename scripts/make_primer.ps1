# FILE: scripts/make_primer.ps1
# Purpose: Regenerate primer files, open PRIMER.md, and copy its contents to clipboard.
# Usage:   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\make_primer.ps1

param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path) | Out-Null
# Move to repo root (parent of scripts/)
Set-Location .. | Out-Null

Write-Host "[make_primer.ps1] Running Python primer generator..."
python .\scripts\make_primer.py

$primer = Join-Path (Get-Location) "primer\PRIMER.md"
if (!(Test-Path $primer)) {
  throw "[make_primer.ps1] Expected $primer to exist."
}

# Copy entire primer to clipboard
Get-Content $primer -Raw | Set-Clipboard
Write-Host "[make_primer.ps1] Primer copied to clipboard."

# Open PRIMER.md in default editor/viewer
Start-Process $primer | Out-Null
Write-Host "[make_primer.ps1] Opened PRIMER.md."

# Warn if stale (> 24h)
$ageHrs = ((Get-Date) - (Get-Item $primer).LastWriteTime).TotalHours
if ($ageHrs -gt 24) {
  Write-Warning "[make_primer.ps1] Primer is stale ($([math]::Round($ageHrs,1))h old). Regenerate before use."
}
