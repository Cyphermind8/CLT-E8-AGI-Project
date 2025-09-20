# FILE: scripts/Status-AutoCLTLoop.ps1
param([int]$Tail=20,[switch]$NoTail,[switch]$Json)
$ErrorActionPreference="Stop"

if($PSScriptRoot){$ScriptDir=$PSScriptRoot}
elseif($MyInvocation.MyCommand.Path){$ScriptDir=Split-Path -Parent $MyInvocation.MyCommand.Path}
else{$ScriptDir=(Get-Location).Path}
try{$RepoRoot=Split-Path $ScriptDir -Parent;if(-not (Test-Path (Join-Path $RepoRoot "scripts"))){$RepoRoot=(Get-Location).Path}}catch{$RepoRoot=(Get-Location).Path}

$LogDir = Join-Path $RepoRoot "logs"
$PidDir = Join-Path $RepoRoot "pids"
$PidFile= Join-Path $PidDir  "auto_loop.pid"
$Meta   = Join-Path $PidDir  "auto_loop.meta"

function Format-Duration([TimeSpan]$ts){'{0:dd}d {0:hh}h {0:mm}m {0:ss}s' -f [TimeSpan]::FromSeconds([math]::Max(0,[int]$ts.TotalSeconds))}

$pidVal=$null;if(Test-Path $PidFile){try{$pidVal=[int](Get-Content $PidFile -Raw).Trim()}catch{}}
$proc=$null;if($pidVal){$proc=Get-Process -Id $pidVal -ErrorAction SilentlyContinue}

$metaLog=$null;$metaObj=$null
if(Test-Path $Meta){ try{$metaObj=[System.IO.File]::ReadAllText($Meta) | ConvertFrom-Json;$metaLog=$metaObj.log}catch{} }
$fallback=$null;if(Test-Path $LogDir){$last=Get-ChildItem $LogDir -File -Filter "auto_loop_*.log" | Sort-Object LastWriteTime | Select-Object -Last 1;if($last){$fallback=$last.FullName}}
$tailTarget = if($metaLog -and (Test-Path $metaLog)){$metaLog}else{$fallback}

# Try to extract last EXITCODE
$exitcode=$null
if($tailTarget){ try{ $m = Select-String -Path $tailTarget -Pattern "EXITCODE=(\d+)" -AllMatches | Select-Object -Last 1; if($m){$exitcode=[int]$m.Matches[0].Groups[1].Value} }catch{} }

if($Json){
  $payload = [ordered]@{
    repo = $RepoRoot
    pid  = $proc.Id
    state= $(if($proc){"RUNNING"}elseif($pidVal){"STALE"}else{"STOPPED"})
    started = $proc.StartTime
    uptime  = $(if($proc){ (Get-Date) - $proc.StartTime }else{$null}) | ForEach-Object { $_.TotalSeconds }
    log     = $tailTarget
    exitcode= $exitcode
  }
  $payload | ConvertTo-Json -Depth 5
  return
}

Write-Host "=== Auto CLT Loop Status ==="
Write-Host "Repo: $RepoRoot"
Write-Host "PID file: $PidFile`n"

if($proc){
  $start=$proc.StartTime;$uptime=(Get-Date)-$start
  Write-Host "State     : RUNNING"
  Write-Host ("PID       : {0}" -f $proc.Id)
  Write-Host ("Started   : {0}" -f $start)
  Write-Host ("Uptime    : {0}" -f (Format-Duration $uptime))
  try{Write-Host ("CPU Time  : {0:n1}s" -f $proc.CPU)}catch{}
  try{Write-Host ("Memory    : {0:n1} MB" -f ($proc.WorkingSet64/1MB))}catch{}
}else{
  if($pidVal){Write-Host ("State     : NOT RUNNING (stale PID {0})" -f $pidVal)}else{Write-Host "State     : NOT RUNNING (no PID file)"}
}

Write-Host ""
Write-Host ("Active log (meta) : {0}" -f ($metaLog -and (Test-Path $metaLog) ? $metaLog : "(none / missing)"))
if($fallback){Write-Host ("Fallback (latest) : {0}" -f $fallback)}

if(-not $NoTail -and $tailTarget){
  Write-Host "`n--- Last $Tail lines ---"
  try{ Get-Content -Path $tailTarget -Tail $Tail }catch{ Write-Warning "Failed to read log: $($_.Exception.Message)" }
}

if($exitcode -ne $null){ Write-Host ("`nResult   : EXITCODE={0}" -f $exitcode) }