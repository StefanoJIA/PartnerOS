# D5.11 — backend startup helper (does not auto-kill stale processes)
$ErrorActionPreference = "Continue"
$port = 8010
$base = "http://127.0.0.1:$port"

Write-Host "Checking port $port ..."
$conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    try {
        $r = Invoke-WebRequest -Uri "$base/health" -UseBasicParsing -TimeoutSec 5
        if ($r.StatusCode -eq 200) {
            Write-Host "[OK] Backend already running at $base"
            exit 0
        }
    } catch {
        Write-Host "[WARN] Port $port is in use but /health is not OK — possible stale uvicorn."
    }
    Write-Host "Manual cleanup:"
    Write-Host "  netstat -ano | findstr :$port"
    Write-Host "  tasklist /FI `"PID eq <PID>`""
    Write-Host "  Stop-Process -Id <PID> -Force"
    Write-Host 'Fallback: .\\scripts\\dev_env_8010.ps1 then use port 8013 manually'
    exit 1
}

$env:BACKEND_BASE_URL = $base
Write-Host "Starting uvicorn on $base ..."
Set-Location -Path (Join-Path $PSScriptRoot "backend")
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $port
