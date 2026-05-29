# D8 Integration Hardening

**Status:** foundation implemented on 2026-05-29.

## Goal

D8 integration hardening turns the D7.7-D8.5 bridge and operations features into a repeatable deployment-readiness gate. It does not deploy or modify `service.intelli-opus.com`; it validates PartnerOS contracts locally or in staging before cloud coordination.

## Check Script

```powershell
cd backend
python scripts/d8_integration_hardening_check.py
```

The script is read-only and uses local TestClient fixtures for D8.4 and D8.5 so it can run even when local Postgres is unavailable.

## Coverage

| Area | Check |
|---|---|
| Documentation | Confirms D7.7-D8.5 docs are present |
| Secrets/storage | Fails if `.env`, `local_data/`, or `backend/storage/` are tracked |
| CORS | Verifies `https://service.intelli-opus.com` preflight is allowed when configured |
| Portal readiness | Confirms readiness does not expose customer portal token |
| Partner operations | Confirms dashboard remains read-only and does not notify or mutate order status |
| Market response | Confirms D8.5 recommendations remain advisory and non-executing |
| Forbidden fields | Scans bridge-facing payloads for internal cost, margin, storage, backend path, and token markers |

## Recommended D8 Gate

```powershell
cd backend
python scripts/d8_integration_hardening_check.py
python scripts/d8_3_service_portal_staging_check.py
python scripts/d8_4_partner_operations_check.py
python scripts/d8_5_market_response_check.py
python scripts/d8_2_runtime_hardening_check.py
python -m pytest -q

cd ../frontend
npm run test -- --run
```

For strict staging environment checks:

```powershell
cd backend
$env:D8_2_STRICT_STAGING="true"
python scripts/d8_2_runtime_hardening_check.py
```

## Safety

- no customer portal deployment
- no nginx or cloud upstream changes
- no token printing
- no email, webhook, or carrier API call
- no quote/order/partner mutation
- no customer or supplier notification
