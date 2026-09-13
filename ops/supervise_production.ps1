# AcademicCheck AI — supervised production start (Windows)
# Keeps API + worker + watchdog alive. Billing stays disabled.
#
# Usage (PowerShell, repo root):
#   .\ops\supervise_production.ps1
#
# Stop: Ctrl+C in this window (child processes are stopped).

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path "$Root\backend\.venv\Scripts\python.exe")) {
  throw "Missing backend\.venv — create venv and install requirements first."
}

$Py = "$Root\backend\.venv\Scripts\python.exe"
$Evidence = "$Root\ops\evidence"
New-Item -ItemType Directory -Force -Path $Evidence | Out-Null

$env:ALERT_SINK_FILE = if ($env:ALERT_SINK_FILE) { $env:ALERT_SINK_FILE } else { "$Evidence\alerts.jsonl" }
$env:WATCHDOG_URL = if ($env:WATCHDOG_URL) { $env:WATCHDOG_URL } else { "http://127.0.0.1:8000" }
$env:WATCHDOG_RESTART_WORKER = "1"
$env:PYTHONUNBUFFERED = "1"

function Start-Supervised($Name, $FilePath, $ArgumentList, $WorkDir, $OutLog, $ErrLog) {
  Write-Host "[supervise] starting $Name"
  return Start-Process -FilePath $FilePath -ArgumentList $ArgumentList `
    -WorkingDirectory $WorkDir -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog
}

Write-Host "AcademicCheck supervise — API :8000, worker, watchdog"
Write-Host "Alerts -> $($env:ALERT_SINK_FILE)"

$api = Start-Supervised "api" $Py @("-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000") `
  "$Root\backend" "$Evidence\api.out.log" "$Evidence\api.err.log"
Start-Sleep -Seconds 3
$worker = Start-Supervised "worker" $Py @("-m","app.workers.rq_worker") `
  "$Root\backend" "$Evidence\worker.out.log" "$Evidence\worker.err.log"
$worker.Id | Set-Content -Path "$Evidence\worker.pid"
$watch = Start-Supervised "watchdog" $Py @("$Root\ops\watchdog.py") `
  $Root "$Evidence\watchdog.out.log" "$Evidence\watchdog.err.log"

Write-Host "PIDs api=$($api.Id) worker=$($worker.Id) watchdog=$($watch.Id)"
Write-Host "Probe: http://127.0.0.1:8000/api/ready"

try {
  while ($true) {
    if ($api.HasExited) {
      Write-Host "[supervise] API exited $($api.ExitCode) — restarting"
      $api = Start-Supervised "api" $Py @("-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000") `
        "$Root\backend" "$Evidence\api.out.log" "$Evidence\api.err.log"
    }
    if ($worker.HasExited) {
      Write-Host "[supervise] worker exited $($worker.ExitCode) — restarting"
      $worker = Start-Supervised "worker" $Py @("-m","app.workers.rq_worker") `
        "$Root\backend" "$Evidence\worker.out.log" "$Evidence\worker.err.log"
      $worker.Id | Set-Content -Path "$Evidence\worker.pid"
    }
    if ($watch.HasExited) {
      Write-Host "[supervise] watchdog exited — restarting"
      $watch = Start-Supervised "watchdog" $Py @("$Root\ops\watchdog.py") `
        $Root "$Evidence\watchdog.out.log" "$Evidence\watchdog.err.log"
    }
    Start-Sleep -Seconds 15
  }
} finally {
  Write-Host "[supervise] stopping children"
  foreach ($p in @($watch, $worker, $api)) {
    if ($p -and -not $p.HasExited) {
      Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    }
  }
}
