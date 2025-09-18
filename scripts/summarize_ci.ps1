# scripts/summarize_ci.ps1
param([string]$Workspace="C:\AI_Project",[int]$LastN=5)
$ErrorActionPreference="Stop"; Set-Location $Workspace
$reports = Get-ChildItem "reports\micro_workspace_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First $LastN
if(-not $reports){ Write-Host "No micro reports found."; exit 0 }
$rows=@(); foreach($r in $reports){ $d=Get-Content $r.FullName -Raw | ConvertFrom-Json; $s=$d.outputs.summary
  $rows += [pscustomobject]@{ Timestamp=$s.timestamp; Runs=$s.runs_per_task; AvgLatencyMs=[double]$s.aggregate.avg_latency_ms; AllOk=[bool]$s.aggregate.all_ok; Path=$r.FullName } }
$avg = ($rows | Measure-Object -Property AvgLatencyMs -Average).Average
$ok = ($rows | Where-Object {$_.AllOk}).Count
$tot = $rows.Count
$rows | Format-Table -AutoSize
"`nAggregate: $ok/$tot all_ok; mean latency {0:N3} ms" -f $avg | Write-Host
