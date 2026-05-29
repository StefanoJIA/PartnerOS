# Testing Matrix

Backend D7.7 acceptance:

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
alembic upgrade head
python scripts/d7_7_portal_bridge_check.py
python scripts/d7_6_shipment_tracking_check.py
python scripts/d7_5_production_milestone_check.py
python scripts/smoke_all_d5.py
python scripts/dev_runtime_doctor.py
python -m pytest -q
```

Frontend acceptance:

```powershell
cd frontend
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"
npm run test -- --run
```

Warnings from optional Redis/worker/PUBLIC_BASE_URL checks are acceptable in local development if the scripts still report PASS.
