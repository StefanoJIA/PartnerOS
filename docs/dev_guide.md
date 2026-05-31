# PartnerOS Developer Guide

**Status:** current on 2026-05-30. This guide describes the local developer workflow for the PartnerOS repository. It is not a final-user installation guide, not a production deploy runbook, and not a `service.intelli-opus.com` operations guide.

Related entry points:

- [README](../README.md)
- [Operator Guide](operator_guide.md)
- [Testing Guide](testing.md)
- [Project Reorientation Summary](project_reorientation_summary.md)
- [D8 Staging Handoff Bundle](phase3/d8_staging_handoff_bundle.md)
- [D8 Staging Operator Runbook](phase3/d8_staging_operator_runbook.md)

## Current State

The repository is in `READY_FOR_STAGING_HANDOFF` when the aggregate local gates pass. That means local docs, scripts, tests, and handoff records agree. It does not mean `STAGING_VALIDATED`.

Current local execution priorities:

1. Keep D5, D6, and D7 closed behavior stable.
2. Keep D8 handoff gates executable on local port `8014`.
3. Obtain real staging values through the D8 access request process.
4. Run strict staging evidence only with those private values.
5. Start D9 operating loops only after `STAGING_VALIDATED`, evidence review, and production coordination.

## Product Boundaries

PartnerOS is the internal source of truth for intelliOffice operations. The public customer-facing portal remains `service.intelli-opus.com`; this repository provides internal workflows and carefully filtered bridge APIs.

Manufacturing partners are peer rows in `manufacturing_partners`. Do not hard-code, default, or prioritize any partner by trade name. Business rules should use statuses, capabilities, structured fields, and explicit operator decisions.

No product path may require final users to run pgAdmin, PostgreSQL, Docker, Alembic, or raw SQL. Those tools are developer and operator infrastructure only.

## Safety Rules

Do not commit `.env`, `local_data/`, `backend/storage/`, uploads, generated logs, customer files, real tokens, raw response bodies, or backend file paths.

Do not expose internal cost, margin, pricing breakdowns, cost snapshots, supplier private notes, backend file paths, storage keys, or tokens through customer-facing APIs.

Do not auto-send email, webhooks, carrier API calls, customer notifications, supplier notifications, order status changes to shipped/delivered, shipment mutations, payment actions, nginx edits, or service portal deployments from this repository.

## Local Runtime

Backend:

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8014
```

Frontend:

```powershell
cd frontend
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"
npm run dev
```

Docker PostgreSQL:

```powershell
docker compose up -d db
```

The preferred host database port is `5435`, mapped to the container's PostgreSQL port. Keep `DATABASE_URL` in `backend/.env` local and uncommitted.

## Environment Variables

For D7.6+ and D8 local validation, prefer:

```powershell
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"
```

For strict staging evidence, the staging operator supplies private values outside the repository:

- `BACKEND_BASE_URL`
- `SERVICE_PORTAL_PARTNEROS_TOKEN`
- `SERVICE_PORTAL_ORIGIN`

Use placeholders in docs. Never paste real token values into committed files, screenshots, terminal transcripts, or handoff records.

## Database Setup

From the repository root:

```powershell
docker compose up -d db
```

From `backend/`:

```powershell
python scripts/check_database_config.py
alembic upgrade head
python -m app.scripts.seed
python -m app.scripts.seed_business_flow
```

Default seeded admin login:

```text
admin@example.com / admin123
```

Do not use production or staging databases for local test runs. Test databases must follow the safety naming rules in [Testing Guide](testing.md).

## Backend Validation

Current local gate matrix:

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
alembic upgrade head
python scripts/d7_7_portal_bridge_check.py
python scripts/d7_6_shipment_tracking_check.py
python scripts/d7_5_production_milestone_check.py
python scripts/smoke_all_d5.py
python scripts/dev_runtime_doctor.py
python scripts/readme_check.py
python scripts/deployment_readiness_checklist_check.py
python scripts/testing_guide_check.py
python scripts/operator_guide_check.py
python scripts/dev_guide_check.py
python scripts/project_execution_chain_check.py
python scripts/project_execution_status.py
python -m pytest -q
```

Local validation on `8014` does not prove `STAGING_VALIDATED`. Strict staging evidence is separate and must use the operator-supplied staging values.

## Frontend Validation

```powershell
cd frontend
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"
npm run test -- --run
```

The frontend should keep internal operator workflows separate from customer-visible bridge data. Portal-facing fields must remain explicitly whitelisted.

## API Conventions

New bridge and operations APIs should live under `/api/v1/*` unless an existing legacy route owns the behavior. Customer-facing bridge APIs must use strict whitelists and must not expose internal pricing, supplier notes, storage paths, or implementation details.

Manual records remain manual:

- Customer confirmations are operator-recorded.
- Supplier confirmations are operator-recorded.
- Production milestones are operator-recorded.
- Shipment plans are operator-recorded.
- Feedback intake does not auto-reply or promise resolution time.

## Desktop Shell

The Tauri desktop shell remains a developer and packaging path, not a requirement for final users to operate infrastructure. The desktop launch flow consumes `GET /health` and then enters the existing Vue app. Browser-first `npm run dev` remains the normal development loop.

Managed sidecar builds may use the packaged backend port described in runtime docs, but D7.6+ smoke and D8 handoff validation should continue to use `8014` unless a specific check says otherwise.

## Troubleshooting

- `GET /` returning `404 Not Found` is expected; use `GET /health`.
- If the backend port is occupied, stop the known local process or choose a documented temporary port and align both `BACKEND_BASE_URL` and `VITE_API_PROXY_TARGET`.
- If Alembic reports pending migrations, run `alembic upgrade head` against the intended local database.
- If auth or database checks fail, use redacted diagnostics from `python scripts/check_database_config.py`; do not paste raw credentials into docs or issue comments.
- If a staging evidence run fails, record the redacted gap through the D8 staging gap triage flow. Do not relabel local evidence as staging proof.

## Handoff Discipline

Use these docs and gates before giving work to a staging operator:

```powershell
cd backend
python scripts/d8_staging_handoff_bundle_check.py
python scripts/d8_staging_operator_runbook_check.py
python scripts/d8_staging_access_request_check.py
python scripts/project_execution_chain_check.py
python scripts/project_execution_status.py
```

The correct next action at `READY_FOR_STAGING_HANDOFF` is to use the D8 handoff bundle and operator runbook, obtain private staging values through `d8_staging_access_request.md`, and then run strict staging evidence.
