
# FILE: scripts/stop_ci.ps1
# Graceful stop for the CI loop. Creates STOP_CI.txt in the project root.
$root = Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..")
$stop = Join-Path $root "STOP_CI.txt"
"stop" | Out-File -FilePath $stop -Encoding ascii -Force
Write-Host "STOP_CI.txt created at $stop. The next cycle will exit."
