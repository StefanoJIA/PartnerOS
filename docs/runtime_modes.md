# Runtime Modes

**Status:** current on 2026-05-30. Runtime modes describe how PartnerOS is started, where configuration comes from, and which safety assumptions apply. This document is a local/runtime architecture reference, not a production deploy runbook and not staging proof.

## Current State

The current repository state is `READY_FOR_STAGING_HANDOFF` when the local execution chain passes. Local D7.6+/D8 validation uses backend port `8014`. This does not prove `STAGING_VALIDATED`; strict staging evidence requires real staging values supplied outside the repository.

## Mode List

| Mode | Purpose | Current rule |
|---|---|---|
| `development` | Local developer workflow with explicit backend/frontend processes, local `.env`, optional Docker Postgres, manual Alembic, and verbose diagnostics | Allowed for repository development and CI-style local validation |
| `desktop` | Desktop product runtime where a shell or sidecar owns startup, health checks, and guided local configuration | Product target; final users must not manage database tooling manually |
| `demo` | Controlled local demo runtime with optional seeded demo data and constrained diagnostics | Demo data must remain clearly marked and must not be confused with staging proof |
| `future_cloud` | Reserved future deployment/runtime mode | Not permission to deploy or modify `service.intelli-opus.com` from this repository |

## Behavior Matrix

| Behavior | `development` | `desktop` | `demo` | `future_cloud` |
|---|---|---|---|---|
| Backend launch | Manual `uvicorn` or test runner | Shell/sidecar managed | Shell/sidecar or controlled local runner | Future deployment runner |
| Preferred local D7.6+/D8 validation port | `8014` | N/A for product runtime; local smoke still uses `8014` | N/A unless explicitly rehearsing locally | Real staging/prod URL only |
| Database URL | Developer `.env` / environment | Guided or managed local configuration | Guided/managed or demo-specific configuration | Remote managed configuration |
| Alembic | Manual in development | Lifecycle-managed | Lifecycle-managed | Deployment-managed |
| Seed data | Manual scripts | Bootstrap/admin setup only | Demo seed allowed | No implicit demo seed |
| Diagnostics | Verbose allowed | Redacted and user-safe | Redacted and demo-safe | Redacted and operator-safe |
| Vite dev proxy | Allowed | No, built frontend assets | Usually no | No |
| Customer portal bridge | Local/test only unless staging values supplied | Internal bridge APIs only | TEST data only | Strict allowlist and deployed secret handling |

## Health Contract

`GET /health` remains the compatibility contract consumed by browser development, desktop launch, and runtime checks. It includes database and migration fields such as:

- `database_status`
- `database_lifecycle_phase`
- `migration_pending`
- `alembic_current_revision`
- `alembic_head_revision`
- optional `database_lifecycle_detail`

In product-like modes (`desktop`, `demo`, `future_cloud`), migration or database failures should remain strict errors. They must not be quietly downgraded to development-only degraded semantics.

## D8 Validation Boundary

Local validation:

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
python scripts/project_execution_status.py
python scripts/d8_staging_execution_pack_check.py
python scripts/project_execution_acceptance_audit_check.py
```

Strict staging evidence:

- uses the real staging `BACKEND_BASE_URL`
- requires `SERVICE_PORTAL_PARTNEROS_TOKEN`
- requires `SERVICE_PORTAL_ORIGIN`
- stores only redacted evidence/gap records
- is the only path that can move readiness toward `STAGING_VALIDATED`

## Safety Rules

- Do not commit `.env`, token values, raw response bodies, customer files, `local_data/`, or `backend/storage/`.
- Do not deploy or modify `service.intelli-opus.com`, nginx, or cloud upstreams from this repository.
- Do not send email, webhooks, carrier API calls, customer notifications, or supplier notifications from runtime checks.
- Do not automatically mutate orders to shipped/delivered from shipment plans.
- Do not require final users to run PostgreSQL, pgAdmin, Docker, Alembic, or raw SQL.

## Related Documents

- [Desktop Target Architecture](architecture_desktop_target.md)
- [Database Lifecycle](database_lifecycle.md)
- [Developer Guide](dev_guide.md)
- [Testing Guide](testing.md)
- [D8 Staging Handoff Bundle](phase3/d8_staging_handoff_bundle.md)
- [D8 Staging Operator Runbook](phase3/d8_staging_operator_runbook.md)
