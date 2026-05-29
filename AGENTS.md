# PartnerOS Agent Guide

## Mission

PartnerOS is the internal source of truth for intelliOffice operations. The public customer-facing portal remains `service.intelli-opus.com`; this repository provides internal workflows and carefully filtered bridge APIs.

## Runtime

- Backend: FastAPI from `backend/`.
- Frontend: Vue/Vite from `frontend/`.
- Preferred local backend smoke port: `8014` for D7.6+ validation.
- Docker Postgres: `127.0.0.1:5435`, managed by `docker compose up -d db`.

## Safety

- Never commit `.env`, `local_data/`, `backend/storage/`, uploads, generated logs, or real tokens.
- Never expose internal cost, margin, pricing breakdowns, cost snapshots, supplier private notes, backend file paths, or tokens through customer-facing APIs.
- D7 customer portal APIs are server-to-server bridge APIs only. Do not deploy or modify `service.intelli-opus.com` from this repo.
- Do not auto-send email/webhooks, call carrier APIs, notify suppliers/customers, or automatically change order status to shipped/delivered.

## D7 Boundaries

- D7.1-D7.6 are complete: orders, customer confirmations, partner splits, supplier confirmations, production milestones, and shipment plans.
- D7.7 adds `/api/v1/portal/customer/*` with strict customer-visible field whitelists and feedback intake.
- Feedback tickets do not auto-reply, notify customers, or promise resolution time.

## Validation

Before committing D7 work, run the relevant matrix:

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
alembic upgrade head
python scripts/d7_7_portal_bridge_check.py
python scripts/d7_6_shipment_tracking_check.py
python scripts/d7_5_production_milestone_check.py
python scripts/smoke_all_d5.py
python scripts/dev_runtime_doctor.py
python -m pytest -q

cd ../frontend
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"
npm run test -- --run
```

Commit and push only after the requested checks pass.
