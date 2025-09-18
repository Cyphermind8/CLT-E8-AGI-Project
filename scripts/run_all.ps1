# scripts/run_all.ps1
param([int]$Determinism=2,[int]$MicroRuns=5,[string]$Workspace="C:\AI_Project")
$ErrorActionPreference="Stop"; Set-Location $Workspace
@("reports","logs","backup","data","experiments")|%{ if(-not(Test-Path $_)){ New-Item -ItemType Directory -Force $_ | Out-Null } }
$ts = Get-Date -Format "yyyyMMdd_HHmmss"; $log = "logs\run_all_$ts.log"
"=== run_all $ts ===" | Tee-Object -FilePath $log
$venv="$Workspace\.venv\Scripts\Activate.ps1"; if(Test-Path $venv){ . $venv }; $env:PYTHONPATH="."
"--- pytest -q ---" | Tee-Object -FilePath $log -Append; pytest -q 2>&1 | Tee-Object -FilePath $log -Append
"--- bench (det=$Determinism) ---" | Tee-Object -FilePath $log -Append; python bench\run_bench.py --determinism $Determinism 2>&1 | Tee-Object -FilePath $log -Append
"--- micro (runs=$MicroRuns) ---" | Tee-Object -FilePath $log -Append; python -m bench.run_workspace_micro --runs $MicroRuns 2>&1 | Tee-Object -FilePath $log -Append
"--- smoke ---" | Tee-Object -FilePath $log -Append; python run_smoke.py 2>&1 | Tee-Object -FilePath $log -Append
"Log: $log" | Tee-Object -FilePath $log -Append; Write-Host "Log: $log"
