# PartnerOS Agent Guide

## Mission

PartnerOS is the internal source of truth for intelliOffice operations. The public customer-facing portal remains `service.intelli-opus.com`; this repository provides internal workflows and carefully filtered bridge APIs.

## Runtime

- Backend: FastAPI from `backend/`.
- Frontend: Vue/Vite from `frontend/`.
- Preferred local backend smoke port: `8014` for D7.6+ and D8 handoff validation.
- Docker Postgres: `127.0.0.1:5435`, managed by `docker compose up -d db`.

## Safety

- Never commit `.env`, `local_data/`, `backend/storage/`, uploads, generated logs, or real tokens.
- Never expose internal cost, margin, pricing breakdowns, cost snapshots, supplier private notes, backend file paths, or tokens through customer-facing APIs.
- D7 customer portal APIs are server-to-server bridge APIs only. Do not deploy or modify `service.intelli-opus.com` from this repo.
- Do not auto-send email/webhooks, call carrier APIs, notify suppliers/customers, or automatically change order status to shipped/delivered.

## D7/D8 Boundaries

- D7 is closed through D7.9: orders, customer confirmations, partner splits, supplier confirmations, production milestones, shipment plans, customer portal bridge APIs, UAT, and resource center.
- Feedback tickets do not auto-reply, notify customers, or promise resolution time.
- Current D8 state is `READY_FOR_STAGING_HANDOFF`, not `STAGING_VALIDATED`.
- D9 remains gated behind `STAGING_VALIDATED`, `READY_FOR_PRODUCTION_COORDINATION_REVIEW`, production coordination, and the human Go/No-Go handoff.

## Validation

Before committing D7/D8 handoff work, run the relevant matrix:

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
python scripts/codex_skill_pack_check.py
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
python scripts/project_execution_status.py
python scripts/d8_staging_execution_pack_check.py
python scripts/d9_operating_execution_pack_check.py
python scripts/project_execution_acceptance_audit_check.py
python -m pytest -q

cd ../frontend
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"
npm run test -- --run
```

Commit and push only after the requested checks pass.
