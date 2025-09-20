param([string[]]$Variants,[int]$MaxParallel=6,[string]$Pack)
$ErrorActionPreference="Stop"
if ($PSScriptRoot){$root=Split-Path $PSScriptRoot -Parent}else{$root=(Get-Location).Path}
$pyVenv=Join-Path $root ".venv\Scripts\python.exe"; $Py=(Test-Path $pyVenv)?$pyVenv:"python"
if ($Pack){$pp = [IO.Path]::IsPathRooted($Pack) ? $Pack : (Join-Path $root $Pack); if(-not(Test-Path $pp)){throw "Pack not found: $pp"}; $Pack=$pp}
if(-not $Variants -or $Variants.Count -eq 0){ $varsText=& $Py -m scripts.eval_long_horizon --list; if($LASTEXITCODE -ne 0){throw "Failed to list variants."}; $Variants=($varsText -split "`r?`n")|?{$_} }
Write-Host "[*] Variants: $($Variants -join ', ')"
$logDir=Join-Path $root "logs"; $jobLogDir=Join-Path $logDir "variant_jobs"
$null=New-Item -ItemType Directory -Force -Path $jobLogDir | Out-Null
function Start-VariantJob([string]$v,[string]$pack,[string]$jobLogDir){
  $ts=Get-Date -Format 'yyyyMMdd_HHmmss'; $vlog=Join-Path $jobLogDir ("job_{0}_{1}.log" -f $v,$ts)
  Start-Job -Name "var:$v" -ScriptBlock {
    param($root,$Py,$v,$pack,$vlog)
    Set-Location $root
    try {
      $args=@('-m','scripts.eval_long_horizon','--variant',$v); if($pack){$args+=@('--pack',$pack)}
      $p=& $Py $args 2>&1; $p | Out-File -FilePath $vlog -Encoding utf8; $p
    } catch { $_ | Out-File -FilePath $vlog -Encoding utf8 -Append; throw }
  } -ArgumentList $root,$Py,$v,$pack,$vlog
}
$jobs=@(); foreach($v in $Variants){ $jobs+= (Start-VariantJob $v $Pack $jobLogDir); while($jobs.Count -ge $MaxParallel){ $done=Wait-Job -Job $jobs -Any; Receive-Job $done | % {$_}; $jobs=$jobs | ? {$_.State -in 'Running','NotStarted'} } }
Wait-Job -Job $jobs | Out-Null
$outs=@(); $fail=@()
foreach($j in $jobs){
  $o=Receive-Job $j; if($o){ $outs += ($o | ? { $_ -match '\.json$' }) }
  $errRec=$j.ChildJobs | % { $_.Error } | ? { $_ }; if($errRec){ $fail += ("[{0}] {1}" -f $j.Name, ($errRec | Out-String)) }
  Remove-Job $j | Out-Null
}
if(-not $outs -or $outs.Count -lt 1){
  Write-Host "[!] No metrics paths captured from variant runs."
  if($fail.Count -gt 0){ Write-Host "---- Variant job errors (summary) ----"; $fail | % {Write-Host $_}; Write-Host "---- Inspect per-variant logs under: $(Join-Path $logDir 'variant_jobs') ----" }
  throw "No metrics paths captured from variant runs."
}
$outs=$outs | Select-Object -Unique
$matrix=Join-Path $logDir "tool_metrics_matrix.json"; $outs | ConvertTo-Json | Set-Content -Encoding utf8 $matrix
Copy-Item $matrix (Join-Path $logDir "tool_metrics_matrix_latest.json") -Force
Write-Host "[+] Matrix written: $matrix"; $outs | % { Write-Host $_ }