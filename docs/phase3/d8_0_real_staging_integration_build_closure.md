# D8.0 Real Staging Integration & Build Closure

**Status:** `READY_FOR_STAGING_HANDOFF`

D8.0 closes the local build/runtime readiness gap before any real staging validation. It is a build and integration checklist, not a proof record workflow and not a D9 entry point.

## Scope

- Make the frontend production build pass with `npm run build`.
- Verify backend tests and local runtime checks against the preferred D8 handoff port `8014`.
- Verify Docker/Postgres can start cleanly.
- Verify Alembic can migrate an empty database to latest head.
- Verify the Portal Customer API contract under staging-style configuration.
- Document the exact service portal environment variables required for `service.intelli-opus.com` integration.

## Boundaries

- Do not deploy or modify `service.intelli-opus.com`.
- Do not edit nginx, cloud upstreams, carrier APIs, webhooks, or email systems.
- Do not auto-notify suppliers or customers.
- Do not mutate orders, shipments, payments, or production state as part of staging checks.
- Do not create or refresh proof records.
- Do not change readiness to `STAGING_VALIDATED`; missing real staging remains `WAITING_FOR_REAL_STAGING_EVIDENCE`.
- Do not enter D9 from this checklist.
- Do not commit tokens, `.env`, PDFs, `local_data/`, uploads, logs, or `backend/storage/`.

## Build Closure Checks

Run the backend matrix from a clean shell:

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
python -m pytest -q
python scripts/dev_runtime_doctor.py
python scripts/smoke_all_d5.py
python scripts/d7_8_portal_live_integration_check.py
```

Run the frontend matrix:

```powershell
cd frontend
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"
npm run test -- --run
npm run build
```

## Clean Docker/Postgres Start

```powershell
docker compose up -d db
docker compose ps db
```

The database container must be healthy before backend clean-start or migration checks are considered complete.

## Empty Database Migration

Use a scratch database only. Do not point this check at staging or production data.

```powershell
cd backend
docker compose exec -T db psql -U partneros -d postgres -c "DROP DATABASE IF EXISTS partneros_migration_check;"
docker compose exec -T db psql -U partneros -d postgres -c "CREATE DATABASE partneros_migration_check OWNER partneros;"
$env:DATABASE_URL="<scratch-db-url>"
alembic upgrade head
```

After a successful check, remove the scratch database:

```powershell
docker compose exec -T db psql -U partneros -d postgres -c "DROP DATABASE IF EXISTS partneros_migration_check;"
```

## Portal Customer API Staging Environment

`service.intelli-opus.com` needs these PartnerOS backend environment variables configured in the staging backend runtime. Token values must be stored only in the hosting secret manager or shell session, never in repository files.

| Variable | Staging value |
|---|---|
| `PORTAL_CUSTOMER_API_ENABLED` | `true` |
| `PORTAL_CUSTOMER_API_TOKEN` | A rotated server-to-server token shared only with the service portal backend |
| `PORTAL_CUSTOMER_ALLOWED_ORIGINS` | `https://service.intelli-opus.com` |
| `PUBLIC_BASE_URL` | The public HTTPS origin for the PartnerOS staging backend |

`PORTAL_CUSTOMER_API_REQUIRE_TOKEN` remains `true`.

## Portal Staging Smoke

For local contract readiness:

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
python scripts/d7_8_portal_live_integration_check.py
```

For a real deployed staging backend, use the staging backend origin and secret token in the shell/session only:

```powershell
cd backend
$env:BACKEND_BASE_URL="https://<partneros-staging-backend-origin>"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<portal-server-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
python scripts/d8_3_service_portal_staging_check.py
```

The D8.3 runner is read-oriented by default. It creates no feedback unless `D8_3_CREATE_TEST_FEEDBACK=true` is set, and any staging feedback must be prefixed with `TEST`.

## Closure Rule

D8.0 is closed only when frontend build, backend runtime checks, Docker/Postgres clean start, empty-database migration, and Portal staging smoke are all verified. Until a real staging backend is checked, the project remains `READY_FOR_STAGING_HANDOFF`.
