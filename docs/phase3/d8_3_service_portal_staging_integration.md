# D8.3 service.intelli-opus.com Staging Integration

**Status:** implemented as a staging contract runner on 2026-05-29.

## Goal

D8.3 prepares the existing `service.intelli-opus.com` portal to consume PartnerOS staging APIs without changing cloud nginx or rebuilding the portal UI. PartnerOS remains the source of truth; the service portal remains the customer-facing frontend.

## Contract Runner

```powershell
cd backend
$env:BACKEND_BASE_URL="https://<partneros-staging-backend-origin>"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<portal-server-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
python scripts/d8_3_service_portal_staging_check.py
```

For local verification:

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
$env:PORTAL_CUSTOMER_API_ENABLED="true"
$env:PORTAL_CUSTOMER_API_REQUIRE_TOKEN="true"
$env:PORTAL_CUSTOMER_API_TOKEN="test-portal-token"
$env:PORTAL_CUSTOMER_ALLOWED_ORIGINS="https://service.intelli-opus.com"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8014
python scripts/d8_3_service_portal_staging_check.py
```

`D8_3_CREATE_TEST_FEEDBACK=true` enables a TEST feedback write. It is disabled by default so the runner can be read-only against staging unless UAT explicitly opts in.

## Checks

| Check | Purpose |
|---|---|
| `/health` | Confirms PartnerOS backend is reachable |
| missing/wrong token | Confirms 401/403 token boundary |
| CORS preflight | Confirms `SERVICE_PORTAL_ORIGIN` is allowed |
| products/orders | Confirms customer bridge reads work |
| order detail/production/shipment/resources | Confirms the customer order lifecycle reads consistently |
| optional TEST feedback | Confirms portal feedback creation without customer notification |
| forbidden field scan | Blocks internal cost, margin, storage keys, backend paths, secrets, token leakage |

## Safety Rules

- Do not store PartnerOS portal tokens in browser JavaScript.
- Prefer a service portal backend proxy that injects the PartnerOS token server-side.
- Do not expose internal fields, backend paths, storage keys, or tokens in portal responses.
- Do not create non-TEST feedback during staging UAT.
- Do not change cloud nginx or service portal routing in this PartnerOS PR.

## Next Step

D8.4 should build multi-partner operations visibility inside PartnerOS after D8.3 has a repeatable staging contract runner.
