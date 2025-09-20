# FILE: scripts/Run-CLTDay.ps1
param(
  [string[]]$Variants,
  [int]$MaxParallel = 6,
  [int]$LinesChanged = 8,
  [switch]$LintOk,
  [switch]$PromoteOnGo,
  [switch]$WriteLatestPointers,
  [string]$SlackWebhook,
  [string]$Pack  # NEW: path to pack JSON (e.g., .\data\evals\pack_e8.json)
)

$ErrorActionPreference = "Stop"

# Repo root & Python
if     ($PSScriptRoot)                { $root = Split-Path $PSScriptRoot -Parent }
elseif ($MyInvocation.MyCommand.Path) { $root = Split-Path -Parent $MyInvocation.MyCommand.Path }
else                                  { $root = (Get-Location).Path }

$pyVenv = Join-Path $root ".venv\Scripts\python.exe"
$Py = (Test-Path $pyVenv) ? $pyVenv : "python"

$logs = Join-Path $root "logs"
$null = New-Item -ItemType Directory -Force -Path $logs | Out-Null

function Write-LatestPointer {
  param([string]$TargetPath, [string]$LatestPath)
  if (-not (Test-Path $TargetPath)) { throw "Target to mirror not found: $TargetPath" }
  Copy-Item $TargetPath $LatestPath -Force
}

# A) Core metrics refresh
Write-Host "[A] Refreshing core metrics..."
$null = & $Py (Join-Path $root "scripts\run_evals.py")
$beforeLatest = Resolve-Path (Join-Path $logs "metrics_latest.json")

# B) Variants in parallel
Write-Host "[B] Running variants in parallel (MaxParallel=$MaxParallel)..."
$runner = Join-Path $root "scripts\Run-VariantMatrix.ps1"
if (-not (Test-Path $runner)) { throw "Missing $runner. Run Step 6 setup." }
if ($Variants -and $Variants.Count -gt 0) {
  if ($Pack) { & $runner -Variants $Variants -MaxParallel $MaxParallel -Pack $Pack }
  else       { & $runner -Variants $Variants -MaxParallel $MaxParallel }
} else {
  if ($Pack) { & $runner -MaxParallel $MaxParallel -Pack $Pack }
  else       { & $runner -MaxParallel $MaxParallel }
}

# prefer stable pointer for matrix
$matrixPath = Join-Path $logs "tool_metrics_matrix_latest.json"
if (-not (Test-Path $matrixPath)) { $matrixPath = Join-Path $logs "tool_metrics_matrix.json" }
if (-not (Test-Path $matrixPath)) { throw "Matrix not found." }

# C) Pick best by rate desc, then steps asc, cost asc
Write-Host "[C] Selecting best variant..."
$files = Get-Content $matrixPath -Raw | ConvertFrom-Json
if (-not $files -or $files.Count -lt 1) { throw "No tool metrics files listed." }

$objs = foreach ($p in $files) {
  if (-not (Test-Path $p)) { continue }
  try {
    $j = Get-Content $p -Raw | ConvertFrom-Json
    [pscustomobject]@{
      Path     = $p
      Variant  = [string]$j.variant
      Rate     = [double]$j.rate
      AvgSteps = [double]$j.avg_steps
      AvgCost  = [double]$j.avg_cost_chars
    }
  } catch { Write-Warning "Skipping unreadable metrics file: $p" }
}
if (-not $objs -or $objs.Count -lt 1) { throw "No readable metrics files." }

$best = $objs | Sort-Object `
  @{Expression='Rate';Descending=$true}, `
  @{Expression='AvgSteps';Descending=$false}, `
  @{Expression='AvgCost';Descending=$false} | Select-Object -First 1
Write-Host ("[pick] {0}  rate={1}  steps={2}  cost≈{3}" -f $best.Variant, $best.Rate, $best.AvgSteps, $best.AvgCost)

# Tool baseline preference: use stable baseline if present, else first in matrix
$toolBaseline = Join-Path $logs "tool_metrics_baseline.json"
if (Test-Path $toolBaseline) { $toolBefore = $toolBaseline } else { $toolBefore = $files[0] }
$toolAfter  = $best.Path

# D) Gate promotion
Write-Host "[D] Running promotion gate..."
$afterOut  = (& $Py (Join-Path $root "scripts\run_evals.py")).Trim()
if (-not (Test-Path $afterOut)) { throw "After metrics not found: $afterOut" }
$afterPath = (Resolve-Path $afterOut).Path

$promArgs = @(
  '-m','scripts.promote_if',
  '--before', $beforeLatest.Path,
  '--after',  $afterPath,
  '--tool-before', $toolBefore,
  '--tool-after',  $toolAfter,
  '--lines-changed', $LinesChanged
)
if ($LintOk) { $promArgs += '--lint-ok' }

$promOut = & $Py $promArgs 2>&1
$exit = $LASTEXITCODE
$promText = ($promOut -join "`n")

$match = [regex]::Match($promText, '(?s)\{.*\}\s*$')
if (-not $match.Success) { throw "Could not parse decision JSON from promotion output.`n$promText" }
$rep = $match.Value | ConvertFrom-Json

# E) Daily report
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$md = @()
$md += "# CLT-E8 Daily Report ($ts)"
$md += ""
$md += "**Decision:** " + ($(if ($rep.approved) {"GO"} else {"NO-GO"})) + "  "
$md += "**Score:** " + ("{0:N3}" -f $rep.score)
$md += ""
$md += "## Variant Selection"
$md += "- Best: **$($best.Variant)**"
$md += "- Rate: **$($best.Rate)**; Steps: **$($best.AvgSteps)**; Cost≈**$($best.AvgCost)**"
$md += ""
$md += "## Gate Reasons"
$md += ($rep.reasons | ForEach-Object { "- $_" })
$md += ""
$md += "## Metrics"
$kv = $rep.metrics.PSObject.Properties | Sort-Object Name
foreach ($p in $kv) { $md += "- **$($p.Name)**: $($p.Value)" }
$md += ""
$mdPath = Join-Path $logs ("daily_report_{0}.md" -f $ts)
$md -join "`r`n" | Set-Content -Path $mdPath -Encoding utf8
Write-Host "[report] $mdPath"

# F) Latest pointers
if ($WriteLatestPointers) {
  Write-LatestPointer -TargetPath $mdPath -LatestPath (Join-Path $logs "daily_report_latest.md")
  $promJson = Join-Path $logs ("promotion_{0}.json" -f $ts)
  ($match.Value) | Set-Content -Path $promJson -Encoding utf8
  Write-LatestPointer -TargetPath $promJson -LatestPath (Join-Path $logs "promotion_latest.json")
}

# G) Auto-promote on GO
if ($PromoteOnGo -and $exit -eq 0) {
  Write-Host "[Promo] Gate passed; updating baselines..."
  Copy-Item $afterPath (Join-Path $logs "metrics_baseline.json") -Force
  Copy-Item $toolAfter  (Join-Path $logs "tool_metrics_baseline.json") -Force
  "$($best.Variant)" | Set-Content -Path (Join-Path $logs "best_variant.txt") -Encoding utf8
  Write-Host "[Promo] Baselines updated."
}

# H) Slack notification
if ($SlackWebhook) {
  try {
    $emoji = $(if ($rep.approved) {":white_check_mark:"} else {":no_entry:"})
    $text  = "$emoji *CLT-E8 Daily* ($ts)`nDecision: *$($(if($rep.approved){"GO"}else{"NO-GO"}))*  Score: *$("{0:N3}" -f $rep.score)*`nBest: *$($best.Variant)*  rate=$($best.Rate) steps=$($best.AvgSteps) cost≈$($best.AvgCost)"
    $payload = @{ text = $text } | ConvertTo-Json -Depth 3
    Invoke-RestMethod -Method Post -Uri $SlackWebhook -Body $payload -ContentType "application/json" | Out-Null
    Write-Host "[notify] Slack posted."
  } catch {
    Write-Warning "Slack post failed: $($_.Exception.Message)"
  }
}

if ($exit -eq 0) { Write-Host "[OK] Promotion gate passed." } else { Write-Host "[NO-GO] Promotion gate rejected." }
exit $exit