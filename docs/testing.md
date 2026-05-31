# Testing Guide

**Status:** current for D7.6+ and D8/D9 handoff validation on 2026-05-30.
**Preferred local validation port:** `8014`.
**Current project state:** `READY_FOR_STAGING_HANDOFF`.

This guide is for developers, CI, and staging operators. It is not an end-user install guide and not a production deploy runbook.

## Current Validation Matrix

Run the local D7.6+ and D8 handoff checks against a single backend instance on `8014`:

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
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
python scripts/project_execution_status.py
python -m pytest -q
```

Run frontend tests against the same backend origin:

```powershell
cd frontend
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"
npm run test -- --run
```

Expected local result before external staging validation:

- `project_execution_status.py` reports `READY_FOR_STAGING_HANDOFF`.
- `d8_readiness_audit.py` reports `READY_FOR_STAGING`.
- `d8_production_coordination_check.py` reports `WAITING_FOR_STAGING_VALIDATION`.
- D8 strict staging evidence remains pending until real staging values are supplied.

## Strict Staging Evidence

Strict staging evidence is separate from local validation. Run it only after operations supplies real private staging values and input preflight is safe:

```powershell
cd backend
$env:BACKEND_BASE_URL="https://<partneros-staging-backend-origin>"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<portal-server-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
python scripts/d8_staging_input_preflight_check.py
python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md
python scripts/d8_staging_records_check.py
python scripts/d8_staging_evidence_review_check.py
python scripts/d8_readiness_audit.py
```

This is the only path that can produce `STAGING_VALIDATED`. Local smoke, pytest, and frontend tests do not prove staging.

## Integration Database Tests

Most backend tests run without a live PostgreSQL test database. Integration tests that need a database are skipped unless `PARTNEROS_TEST_DATABASE_URL` is set.

Safety rule: the database name in `PARTNEROS_TEST_DATABASE_URL` must contain `test` or `testing`.

Example:

```powershell
cd backend
$env:PARTNEROS_TEST_DATABASE_URL="<partneros-test-database-url>"
$env:DATABASE_URL="<partneros-test-database-url>"
alembic upgrade head
python -m pytest tests/test_business_flow_integration.py -q
```

Do not point `PARTNEROS_TEST_DATABASE_URL` at a development, staging, or production database.

## Legacy D5/D6 Checks

Historical D5/D6 docs and release records may mention `8000`, `8010`, `portal_readiness_check.py`, `portal_consumer_check.py`, or `smoke_demo_ready.py`. Treat those as historical or targeted legacy checks, not the current D7.6+/D8 validation matrix.

Current D8/D9 readiness is governed by:

- [Deployment Readiness Checklist](deployment_readiness_checklist.md)
- [Operator Guide](operator_guide.md)
- [Project Execution Chain Gate](phase3/project_execution_chain_gate.md)
- [Project Execution Acceptance Audit](phase3/project_execution_acceptance_audit.md)
- [D8 Staging Handoff Bundle](phase3/d8_staging_handoff_bundle.md)

## Safety Boundaries

- Do not commit `.env`, `local_data`, `backend/storage`, uploads, generated logs, raw response bodies, tokens, cookies, or customer files.
- Do not expose internal cost, margin, pricing breakdown, supplier private notes, backend file paths, storage keys, or tokens.
- Do not send email/webhooks, call carrier APIs, notify customers or suppliers, edit nginx/cloud upstreams, deploy `service.intelli-opus.com`, or mutate quote/order/shipment/payment state as part of tests.
- Feedback and D9 operating records remain human-reviewed and redacted.
