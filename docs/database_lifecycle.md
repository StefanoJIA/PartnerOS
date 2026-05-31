# Database Lifecycle

**Status:** current on 2026-05-30.

## Purpose

PostgreSQL + pgvector remains the authoritative data and vector store for PartnerOS. This document defines the current database lifecycle contract for local development, desktop-target planning, D8 staging handoff, and future packaging work.

This is a runtime architecture reference. It is not staging proof, not a production deployment runbook, and not permission to change cloud infrastructure.

Current local project state is `READY_FOR_STAGING_HANDOFF`. `STAGING_VALIDATED` still requires the strict staging evidence workflow with real private environment values and redacted saved records. If local rehearsal output is saved where strict evidence is expected, production coordination remains at `WAITING_FOR_REAL_STAGING_EVIDENCE` until real staging evidence replaces it.

## Current Implementation

The database lifecycle manager lives in `backend/app/core/database_lifecycle.py`. It coordinates:

- database URL detection without implicit default credentials
- connectivity classification
- Alembic current/head revision comparison
- product-like automatic migration with `alembic upgrade head`
- health payload fields for runtime diagnostics

The health contract includes `database_status`, `database_lifecycle_phase`, `migration_pending`, `alembic_current_revision`, and `alembic_head_revision`. Optional diagnostic detail may be present, but it must not expose passwords, tokens, raw connection strings, backend storage paths, or private files.

Related tests and checks include `backend/tests/test_database_lifecycle.py`, `backend/tests/test_health.py`, `backend/tests/test_database_connection_diag.py`, and `backend/scripts/dev_runtime_doctor.py`.

## Mode Behavior

`development` is inspect-only. If no database URL is configured, `/health` reports `database_status: not_configured` and `database_lifecycle_phase: not_configured`; it must not silently fall back to a bundled username or password. If configured credentials fail, the status is `auth_failed`. If the configured database is missing, the status is `database_missing`. Other connection failures are classified as unavailable with redacted detail.

Product-like modes such as `desktop`, `demo`, and `future_cloud` are strict. Missing configuration, authentication failure, database absence, migration failure, or migration mismatch keeps `/health` in an error state. Product-like modes may run `alembic upgrade head` through the lifecycle manager; they must not hide failures as a development-only degraded state.

Local D7.6+/D8 validation uses:

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
python scripts/dev_runtime_doctor.py
```

## Responsibilities

The database lifecycle manager owns:

- configuration detection
- connection diagnostics
- migration revision comparison
- product-like migration execution
- health snapshot fields
- redacted diagnostics for operator troubleshooting
- future backup/restore extension points

It does not own final-user installation UX yet. Packaging decisions, embedded PostgreSQL service management, backup/restore UI, and desktop installer behavior remain future desktop-delivery work.

## Final User Boundary

Do not require final users to run PostgreSQL, pgAdmin, Docker, Alembic, or raw SQL. Those tools are developer and operator utilities only.

Final desktop users should eventually install and launch the application without manually creating databases, running migrations, editing connection strings, or using pgAdmin. Until that packaging work is complete, local developers and staging operators still use the documented backend commands.

## Staging Boundary

Local database checks do not prove `STAGING_VALIDATED`. They only support `READY_FOR_STAGING_HANDOFF`.

Strict staging validation must use real, private values supplied outside the repository:

- `BACKEND_BASE_URL`
- `SERVICE_PORTAL_PARTNEROS_TOKEN`
- `SERVICE_PORTAL_ORIGIN`

The D8 Staging Operator Runbook and strict evidence runner decide whether saved redacted evidence is production-coordination-ready. Do not commit `.env`, local database dumps, `local_data/`, `backend/storage/`, raw response bodies, screenshots containing tokens, or private customer files.

## Safety Boundaries

The database lifecycle path must remain infrastructure-only. It must not:

- call carrier APIs
- send email or webhooks
- notify customers or suppliers
- create shipments
- create feedback tickets
- mutate quote, order, shipment, delivery, payment, inventory, or partner-selection state
- deploy or modify `service.intelli-opus.com`
- edit nginx or cloud upstreams

Order status changes such as shipped or delivered remain manual business actions outside the lifecycle manager.

## Related Docs

- [Runtime Modes](runtime_modes.md)
- [Desktop Target Architecture](architecture_desktop_target.md)
- [Developer Guide](dev_guide.md)
- [Testing Guide](testing.md)
- [D8 Staging Handoff Bundle](phase3/d8_staging_handoff_bundle.md)
- [D8 Staging Operator Runbook](phase3/d8_staging_operator_runbook.md)
