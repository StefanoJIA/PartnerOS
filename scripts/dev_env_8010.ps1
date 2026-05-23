# D5.11 — set recommended local backend env (8010)
$env:BACKEND_BASE_URL = "http://127.0.0.1:8010"
$env:VITE_API_PROXY_TARGET = "http://127.0.0.1:8010"
Write-Host "BACKEND_BASE_URL=$env:BACKEND_BASE_URL"
Write-Host "VITE_API_PROXY_TARGET=$env:VITE_API_PROXY_TARGET"
Write-Host "Run backend: cd backend; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8010"
Write-Host "Run frontend: cd frontend; npm run dev"
