# D8 Staging Access Request

**Status:** added on 2026-05-30; use after `READY_FOR_STAGING_HANDOFF`.

## Purpose

This request gives the staging operator the exact inputs needed to run strict staging evidence without placing secrets, customer data, cloud deployment steps, or service portal changes in this repository.

It is the handoff before `STAGING_VALIDATED`, not a substitute for evidence. The repository remains at `READY_FOR_STAGING` until `scripts/d8_strict_staging_evidence_check.py` runs against real staging values and saves redacted evidence.

## Requested Inputs

| Input | Required shape | Commit policy |
|---|---|---|
| `BACKEND_BASE_URL` | HTTPS PartnerOS staging backend origin | Do not commit if it reveals private infrastructure |
| `SERVICE_PORTAL_PARTNEROS_TOKEN` | Non-default server-to-server portal token | Never commit, screenshot, paste, or echo |
| `SERVICE_PORTAL_ORIGIN` | HTTPS service portal origin, normally `https://service.intelli-opus.com` | Safe to document only as an origin, not with cookies or headers |
| Staging commit or release tag | PartnerOS backend commit deployed to staging | Safe if it is a commit SHA or release label |
| Staging database seed description | Short statement that representative TEST orders/resources/feedback exist | Do not include customer files, raw payloads, or production data |

## Operator Response Format

Use a private channel for secrets. The repository should receive only this redacted confirmation:

```text
BACKEND_BASE_URL: provided privately
SERVICE_PORTAL_PARTNEROS_TOKEN: provided privately
SERVICE_PORTAL_ORIGIN: https://service.intelli-opus.com
DEPLOYED_COMMIT: <short-sha-or-release>
TEST_DATA_SCOPE: TEST customer/order/product/resource/feedback fixtures only
```

## Evidence Command

```powershell
cd backend
$env:BACKEND_BASE_URL="https://partneros-staging.example.com"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<portal-server-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md
python scripts/d8_staging_records_check.py
python scripts/d8_readiness_audit.py
```

Before the evidence command, run `python scripts/d8_staging_input_preflight_check.py` to catch missing, placeholder, non-HTTPS, or known default input values without calling staging.

## Safety Boundaries

- Do not commit `.env`, token values, cookies, raw headers, screenshots with secrets, customer files, uploads, `local_data`, or `backend/storage`.
- Do not deploy or modify `service.intelli-opus.com`, nginx, or cloud upstreams from this repository.
- Do not create non-TEST feedback during staging.
- Do not call carrier APIs, send email/webhooks, notify customers/suppliers, or automatically change quote, order, shipment, delivery, payment, inventory, or partner-selection status.
- Do not expose internal cost, margin, pricing breakdowns, supplier private notes, backend paths, storage keys, or secrets.
