# Integrated Backend Standards

**Status:** current on 2026-05-30. This document defines backend standards for PartnerOS internal workflows and strictly filtered bridge APIs. It replaces early-stage planning language with the current D7-D9 execution state.

Current state:

- D5 Lead Intelligence is closed.
- D6 Quote MVP is closed.
- D7 order, confirmation, partner/supplier, production milestone, portal bridge, feedback intake, and shipment plan foundations are closed through D7.9.
- D8 is `READY_FOR_STAGING_HANDOFF`: local gates are ready, but real strict staging evidence still needs private staging values.
- If local rehearsal output is saved where strict evidence is expected, production coordination remains at `WAITING_FOR_REAL_STAGING_EVIDENCE` until real staging evidence replaces it.
- D9 operating loops remain planned behind `STAGING_VALIDATED`, `READY_FOR_PRODUCTION_COORDINATION_REVIEW`, production coordination, and the human Go / No-Go handoff. If committed, that handoff uses `docs/records/d8_production_go_no_go_YYYYMMDD.md`.

Related docs:

- [Project Reorientation Summary](project_reorientation_summary.md)
- [Developer Guide](dev_guide.md)
- [Testing Guide](testing.md)
- [Operator Guide](operator_guide.md)
- [D8 Staging Handoff Bundle](phase3/d8_staging_handoff_bundle.md)
- [D8 Staging Operator Runbook](phase3/d8_staging_operator_runbook.md)

## Core Rule

PartnerOS is the internal source of truth. The public customer-facing portal remains `service.intelli-opus.com`. This repository must not deploy or modify that service; it provides internal workflows and carefully whitelisted bridge APIs.

## Feature Intake Checklist

Every backend feature or route change should answer these questions before implementation:

```text
Feature:
Business goal:
Domain: CRM | LeadIntelligence | Quote | Order | Production | Shipment | Task | File | System | Integration | PortalBridge
API surface: legacy /api, /api/v1 internal, or /api/v1/portal/customer bridge
Customer-visible fields: explicit whitelist, or none
Database change: Alembic revision id and rollback notes
Permission change: role/dependency/scope
Timeline or activity events:
Manual-only safety impact:
Environment variables:
Tests and smoke scripts:
Docs and operator guide updates:
Risks:
```

## API Surface

| Surface | Use | Response shape | Notes |
|---|---|---|---|
| `/api/*` legacy routes | Existing internal app behavior | Existing FastAPI/Pydantic responses | Keep compatibility unless a task explicitly migrates a route |
| `/api/v1/*` internal routes | New internal modules and system APIs | Prefer existing v1 envelope helpers where already used | Do not expose secrets or customer-only summaries by accident |
| `/api/v1/portal/customer/*` bridge routes | Server-to-server customer portal bridge | Strict customer-visible DTOs only | No internal pricing, margin, supplier notes, backend paths, or raw files |

Use additive changes unless the roadmap explicitly calls for a breaking migration. Do not perform a broad route rewrite just to normalize style.

## Customer Portal Bridge

Customer bridge APIs must be explicit allowlists. A field is not customer-visible merely because it exists on an ORM model or internal schema.

Allowed bridge themes:

- order summary and public identifiers
- customer confirmation state
- production milestone summaries
- shipment summaries from manual shipment plans
- feedback intake with human review

Forbidden bridge data:

- internal cost, margin, price breakdown, cost snapshots
- supplier private notes or partner-only comments
- backend storage paths, local file paths, upload paths
- tokens, raw response bodies, request debug dumps
- unreviewed internal timelines that contain private operator notes

## Manual-Only Operations

These domains are records of human work, not automation triggers:

- customer confirmations
- partner splits
- supplier confirmations
- production milestones
- shipment plans and shipment tracking summaries
- customer feedback tickets

Do not auto-send email, webhooks, carrier API calls, supplier notifications, customer notifications, payment actions, or order status changes to shipped/delivered. Shipment and production state changes must remain operator-controlled unless a future task explicitly changes that rule and adds a safety gate.

## Domain Boundaries

| Domain | Owns | Must not own |
|---|---|---|
| CRM | companies, contacts, interactions | quote pricing decisions, production schedule mutation |
| LeadIntelligence | scoring, enrichment suggestions, market signals | automatic outreach, final formal scoring without review |
| Quote | catalog, quote records, line items, versions, PDF export, manual delivery record | automatic order creation |
| Order | order records, confirmations, partner splits, supplier confirmations | automatic shipment or payment actions |
| Production | manual milestone plans and status events | supplier notification or factory system integration |
| Shipment | manual shipment plans, customer-visible shipment summaries | carrier API calls, webhooks, automatic shipped/delivered status |
| PortalBridge | customer-visible DTOs and feedback intake | internal operations screens or service portal deployment |
| System | health, readiness, doctor, manifest, runtime checks | business CRUD |

Manufacturing partners are peer rows in `manufacturing_partners`. Do not hard-code, default, or prioritize any partner by trade name.

## Database And Migrations

- Use Alembic for schema changes.
- Keep migration revision ids within Alembic limits and project conventions.
- Prefer nullable/additive fields for staged rollouts unless a migration is explicitly breaking.
- Foreign keys should match ownership boundaries and use existing model conventions.
- Never require final users to run PostgreSQL, pgAdmin, Docker, Alembic, or raw SQL.

## Security And Redaction

Do not commit `.env`, `local_data/`, `backend/storage/`, uploads, generated logs, customer files, real tokens, raw response bodies, or backend file paths.

Diagnostic and handoff artifacts must be redacted. Use placeholders such as `<portal-server-token>` and route private values through the D8 staging access request process.

## Runtime And Validation

Current local D7.6+/D8 validation uses port `8014`:

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
python scripts/project_execution_status.py
python scripts/d8_staging_execution_pack_check.py
python scripts/d9_operating_execution_pack_check.py
python scripts/project_execution_acceptance_audit_check.py
```

Frontend local validation should align the proxy:

```powershell
cd frontend
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"
npm run test -- --run
```

Local validation does not prove `STAGING_VALIDATED`. Strict staging evidence requires real staging values from the operator:

- `BACKEND_BASE_URL`
- `SERVICE_PORTAL_PARTNEROS_TOKEN`
- `SERVICE_PORTAL_ORIGIN`

## Required Gates For Standards Changes

After changing this document or backend integration rules, run:

```powershell
cd backend
python scripts/integrated_backend_standards_check.py
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
python scripts/d8_staging_execution_pack_check.py
python scripts/d9_operating_execution_pack_check.py
python scripts/project_execution_acceptance_audit_check.py
python -m pytest tests/test_integrated_backend_standards_check.py -q
```

This keeps backend standards aligned with the current D8 staging handoff, D9 gate order, customer-visible field whitelists, and manual-only safety boundaries.
