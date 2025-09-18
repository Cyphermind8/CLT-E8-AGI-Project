
param(
    [int]$Determinism = 2,
    [int]$MicroRuns = 3
)

$ErrorActionPreference = "Stop"

# Project root
Set-Location -Path "C:\AI_Project"

# Ensure standard dirs exist (idempotent)
@("reports","logs","backup","data","experiments") | ForEach-Object {
    if (-not (Test-Path $_)) { New-Item -ItemType Directory -Force $_ | Out-Null }
}

# Activate venv
$venv = ".\.venv\Scripts\Activate.ps1"
if (-not (Test-Path $venv)) {
    Write-Host "ERROR: venv not found at $venv" -ForegroundColor Red
    exit 1
}
. $venv
$env:PYTHONPATH = "."

# 1) Connectivity check to LM Studio
try {
    $resp = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:1234/v1/models
    $json = $resp.Content | ConvertFrom-Json
    $ids = @()
    if ($null -ne $json.data) {
        $ids = $json.data | ForEach-Object { $_.id }
    }
    $hasModel = $ids -contains "openai/gpt-oss-20b"
    Write-Host "LM Studio models: $($ids -join ', ')"
    Write-Host "Model 'openai/gpt-oss-20b' present: $hasModel"
}
catch {
    Write-Host "ERROR: LM Studio connectivity failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2) Re-validate environment
Write-Host "`n=== Running pytest ==="
pytest -q
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: pytest failed" -ForegroundColor Red; exit 1 }
Write-Host "pytest OK"

Write-Host "`n=== Running full bench (determinism = $Determinism) ==="
$null = & python bench\run_bench.py --determinism $Determinism 2>&1

# Find latest bench JSON
$benchFile = (Get-ChildItem -Path reports -Filter "bench_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
if (-not $benchFile) { Write-Host "ERROR: Bench JSON report not found under reports\" -ForegroundColor Red; exit 1 }
$benchJson = Get-Content $benchFile -Raw | ConvertFrom-Json
$benchRate   = [double]$benchJson.outputs.summary.success.rate
$benchPassed = [int]$benchJson.outputs.summary.success.passed
$benchTotal  = [int]$benchJson.outputs.summary.success.total
$benchAvgS   = [double]$benchJson.outputs.summary.latency.avg_s
$benchDetOK  = [bool]$benchJson.outputs.summary.determinism_ok

Write-Host "`n=== Running micro bench (runs = $MicroRuns) ==="
$null = & python -m bench.run_workspace_micro --runs $MicroRuns 2>&1
$microFile = (Get-ChildItem -Path reports -Filter "micro_workspace_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
if (-not $microFile) { Write-Host "ERROR: Micro JSON report not found under reports\" -ForegroundColor Red; exit 1 }
$microJson   = Get-Content $microFile -Raw | ConvertFrom-Json
$microAvgMs  = [double]$microJson.outputs.summary.aggregate.avg_latency_ms
$microSteps  = [double]$microJson.outputs.summary.aggregate.avg_steps

Write-Host "`n=== Running smoke ==="
$null = & python run_smoke.py 2>&1
$smokeOK = $LASTEXITCODE -eq 0

# 3) Baseline comparison (from last good run shared previously)
$baselinePass       = 1.0
$baselineBenchAvgS  = 4.129
$baselineMicroAvgMs = 0.6283333333333333

$deltaPass  = $benchRate - $baselinePass
$deltaBench = $benchAvgS - $baselineBenchAvgS
$deltaMicro = $microAvgMs - $baselineMicroAvgMs

# 4) Output summary
Write-Host "`n================= SUMMARY ================="
Write-Host ("Bench: {0}/{1} (rate={2:N3}), avg latency={3:N3}s, determinism_ok={4}" -f $benchPassed, $benchTotal, $benchRate, $benchAvgS, $benchDetOK)
Write-Host ("Micro: steps={0:N0}, avg latency={1:N3} ms" -f $microSteps, $microAvgMs)
Write-Host ("Smoke: {0}" -f ($(if ($smokeOK) {"OK"} else {"FAILED"})))

Write-Host ("Δ vs baseline — pass rate: {0:N3}, bench latency: {1:N3}s, micro latency: {2:N3} ms" -f $deltaPass, $deltaBench, $deltaMicro)

if ($benchAvgS -gt 8) {
    Write-Host ""
    Write-Host "Bench latency is high (>8s). Tune LM Studio:" -ForegroundColor Yellow
    Write-Host "  • Maximize GPU Offload (reduce by 1 if OOM)"
    Write-Host "  • Offload KV cache to GPU: ON"
    Write-Host "  • Evaluation batch size: 512 (or 256 if VRAM-limited)"
    Write-Host "  • Serve on Local Network: OFF (use 127.0.0.1)"
    Write-Host "  • Ensure model is READY before running"
}
Write-Host "==========================================="
exit 0
