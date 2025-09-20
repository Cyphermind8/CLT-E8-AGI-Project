# FILE: scripts/Schedule-AutoCLTLoop.ps1
param(
  [string]$TaskName      = "CLT-AutoLoop",
  [string]$DailyTime     = "02:00",    # HH:mm
  [double]$Hours         = 1,
  [int]$PauseSeconds     = 300,
  [switch]$AtStartup,
  [switch]$Install,
  [switch]$Remove,
  [switch]$RunNow,
  [switch]$Enable,
  [switch]$Disable
)

$ErrorActionPreference = "Stop"

# --- Robust repo root detection ---
if ($PSScriptRoot) { $ScriptDir = $PSScriptRoot }
elseif ($MyInvocation.MyCommand.Path) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
else { $ScriptDir = (Get-Location).Path }
try {
  $RepoRoot = Split-Path $ScriptDir -Parent
  if (-not (Test-Path (Join-Path $RepoRoot 'scripts'))) { $RepoRoot = (Get-Location).Path }
} catch { $RepoRoot = (Get-Location).Path }

$StartScript = Join-Path $RepoRoot 'scripts\Start-AutoCLTLoop.ps1'
if (-not (Test-Path $StartScript)) { throw "Missing Start script at $StartScript. Create it first." }

function New-TaskAction {
  $shell = (Get-Command pwsh -ErrorAction SilentlyContinue) ? "pwsh" : "powershell"
  $args  = @(
    "-NoProfile","-ExecutionPolicy","Bypass",
    "-File", ('"{0}"' -f $StartScript),
    "-Hours", $Hours,
    "-PauseSeconds", $PauseSeconds,
    "-NoTail",
    "-Force"
  ) -join ' '
  New-ScheduledTaskAction -Execute $shell -Argument $args
}

function Resolve-DailyTime([string]$timeText) {
  # Parse HH:mm or H:mm using TimeSpan only (robust across PS/.NET versions)
  $ts = [TimeSpan]::Zero
  if ([TimeSpan]::TryParse($timeText, [ref]$ts)) {
    return (Get-Date -Hour $ts.Hours -Minute $ts.Minutes -Second 0)
  }
  throw "Invalid -DailyTime '$timeText'. Use HH:mm (e.g., 02:00 or 18:30)."
}

function New-TaskTriggers {
  $at = Resolve-DailyTime -timeText $DailyTime
  $trigs = @()
  $trigs += (New-ScheduledTaskTrigger -Daily -At $at)
  if ($AtStartup) { $trigs += (New-ScheduledTaskTrigger -AtStartup) }
  return ,$trigs
}

function New-TaskPrincipal {
  $uid = "$($env:USERDOMAIN)\$($env:USERNAME)"
  # Run whether user is logged on or not (no stored password)
  New-ScheduledTaskPrincipal -UserId $uid -LogonType S4U -RunLevel Highest
}

function New-TaskSettings {
  New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 24) `
    -WakeToRun:$false
}

if ($Install) {
  $action    = New-TaskAction
  $triggers  = New-TaskTriggers
  $principal = New-TaskPrincipal
  $settings  = New-TaskSettings

  $task = New-ScheduledTask -Action $action -Trigger $triggers -Principal $principal -Settings $settings
  Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null

  Write-Host "[+] Task '$TaskName' installed."
  Write-Host "    Daily : $DailyTime"
  Write-Host "    Boot  : $AtStartup"
  Write-Host "    Hours : $Hours"
  Write-Host "    Pause : $PauseSeconds s"
  exit 0
}

if ($Remove)   { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false; Write-Host "[+] Task '$TaskName' removed.";   exit 0 }
if ($RunNow)   { Start-ScheduledTask     -TaskName $TaskName;                           Write-Host "[+] Task '$TaskName' started.";  exit 0 }
if ($Enable)   { Enable-ScheduledTask    -TaskName $TaskName;                           Write-Host "[+] Task '$TaskName' enabled.";  exit 0 }
if ($Disable)  { Disable-ScheduledTask   -TaskName $TaskName;                           Write-Host "[+] Task '$TaskName' disabled."; exit 0 }

# Default summary
try {
  $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
  $info = Get-ScheduledTaskInfo -TaskName $TaskName
  Write-Host "Task    : $TaskName"
  Write-Host "State   : $($t.State)"
  Write-Host "LastRun : $($info.LastRunTime) (Result: $($info.LastTaskResult))"
  Write-Host "NextRun : $($info.NextRunTime)"
  Write-Host "Action  : $($t.Actions[0].Execute) $($t.Actions[0].Arguments)"
} catch {
  Write-Host "Task '$TaskName' is not installed. Use -Install to create it."
}