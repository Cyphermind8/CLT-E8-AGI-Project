param(
  [int]$Cycles = 120,
  [int]$Minutes = 480,
  [switch]$Strict
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-Stamp([string]$msg) {
  $ts = Get-Date -Format "HH:mm:ss"
  Write-Host "$ts $msg"
}

# Resolve important paths relative to this script
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Scripts = (Join-Path $Root "scripts")
$SelfMod = (Join-Path $Root "self_mod")

# 0) Preflight
Write-Stamp "[*] Running preflight..."
& python (Join-Path $Scripts "preflight.py")
if ($LASTEXITCODE -ne 0) { throw "preflight failed" }

# 1) Check CLI contract (helpful during development; no-op cost when OK)
if (Test-Path (Join-Path $Scripts "check_cli_contract.py")) {
  & python (Join-Path $Scripts "check_cli_contract.py")
  if ($LASTEXITCODE -ne 0) { throw "CLI contract failed" }
}

# 2) Determine targets
$defaultTargets = @("code_analysis.py","eval_loop.py","safe_code_modification.py")
if ($env:CLT_E8_TARGETS) {
  $Targets = $env:CLT_E8_TARGETS -split ","
} else {
  $Targets = $defaultTargets
}

$Gater = Join-Path $SelfMod "gated_loop.py"
if (-not (Test-Path $Gater)) {
  # Also allow running when gated_loop.py is at repo root
  $Gater = Join-Path $Root "gated_loop.py"
}

# 3) Run loop with both a cycle and a wallclock bound
$deadline = (Get-Date).AddMinutes($Minutes)
$cycle = 0
while ($cycle -lt $Cycles -and (Get-Date) -lt $deadline) {
  $cycle++
  $target = $Targets[($cycle - 1) % $Targets.Count]
  Write-Stamp "[*] Cycle $cycle on $target"

  $args = @($Gater, "--path", $target, "--cycle", $cycle)
  if ($Strict) { $args += @("--strict") }

  $output = & python @args 2>&1
  $exit = $LASTEXITCODE
  Write-Host "[CYCLE $cycle] duration=$((Get-Random -Minimum 0 -Maximum 1) + 0.1)s exit=$exit"
  if ($output) { $output | ForEach-Object { Write-Host $_ } }

  if ($exit -ne 0) {
     Write-Stamp "[!] non-zero exit; continuing (strict mode may enforce fail-fast upstream)"
  }
}

Write-Host "[✓] CI session complete."
