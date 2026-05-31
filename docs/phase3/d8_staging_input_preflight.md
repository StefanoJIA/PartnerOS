# D8 Staging Input Preflight

**Status:** added on 2026-05-30; run before strict staging evidence when private values are available.

## Purpose

This preflight checks the operator-provided staging inputs before any network evidence run. It does not call staging, does not read `.env` directly, does not print token values, and does not write records.

## Command

```powershell
cd backend
$env:BACKEND_BASE_URL="https://<partneros-staging-backend-origin>"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<portal-server-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
python scripts/d8_staging_input_preflight_check.py
```

## States

| State | Meaning | Next action |
|---|---|---|
| `WAITING_FOR_PRIVATE_VALUES` | One or more required values are missing, but no unsafe provided value was found | Use [D8 Staging Access Request](d8_staging_access_request.md) |
| `INPUTS_UNSAFE` | A provided value is unsafe, such as non-local HTTP URL, placeholder URL/token, known default token, or token shorter than 24 characters | Fix private configuration before evidence |
| `INPUTS_READY` | Required values are present, HTTPS or explicit local HTTP rehearsal, non-default, and token length is at least 24 characters | Run strict staging evidence |

## Safety Boundaries

- Do not commit `.env` or token values.
- Do not paste real `SERVICE_PORTAL_PARTNEROS_TOKEN` or `PORTAL_CUSTOMER_API_TOKEN` into docs, issues, screenshots, or terminal transcripts.
- Do not run strict evidence with HTTP staging URLs unless doing explicit local rehearsal with `D8_STRICT_ALLOW_LOCAL_HTTP=true`.
- `D8_STRICT_ALLOW_LOCAL_HTTP=true` only permits `localhost`, `127.0.0.1`, or `::1`; it must not be used for remote staging/cloud origins.
- This preflight does not send email/webhooks, notify customers/suppliers, call carrier APIs, mutate orders/shipments/payments, edit nginx, or deploy `service.intelli-opus.com`.
