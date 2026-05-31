# D8 Staging Access Request - 2026-05-31

Status: open
Repository state: `READY_FOR_STAGING_HANDOFF`
Evidence target: strict staging validation

## Requested Private Inputs

| Input | Requested status | Commit policy |
|---|---|---|
| `BACKEND_BASE_URL` | provided privately | Do not commit if it reveals private infrastructure |
| `SERVICE_PORTAL_PARTNEROS_TOKEN` | provided privately | Never commit, screenshot, paste, or echo |
| `SERVICE_PORTAL_ORIGIN` | `https://service.intelli-opus.com` | Safe as origin only; no cookies, headers, or token values |
| `DEPLOYED_COMMIT` | short staging commit or release label | Safe if it is a public commit SHA or redacted release label |
| `TEST_DATA_SCOPE` | TEST customer/order/product/resource/feedback fixtures only | Do not include production data, customer files, or raw payloads |

## Operator Reply Format

```text
BACKEND_BASE_URL: provided privately
SERVICE_PORTAL_PARTNEROS_TOKEN: provided privately
SERVICE_PORTAL_ORIGIN: https://service.intelli-opus.com
DEPLOYED_COMMIT: <short-sha-or-release>
TEST_DATA_SCOPE: TEST customer/order/product/resource/feedback fixtures only
```

## Validation After Reply

```powershell
cd backend
python scripts/d8_staging_input_preflight_check.py
python scripts/d8_staging_operator_response_intake_check.py
python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md
python scripts/d8_staging_records_check.py
python scripts/d8_readiness_audit.py
python scripts/d8_staging_evidence_review_check.py
```

## Boundaries

- No `.env`, token value, bearer header, cookie, full API payload, screenshot with secrets, customer file, upload, local data directory artifact, or backend storage artifact may be committed.
- Do not deploy or modify `service.intelli-opus.com`, nginx, or cloud upstreams from this repository.
- Do not create non-TEST feedback during staging.
- Do not call carrier APIs, send email/webhooks, notify customers/suppliers, or automatically change quote, order, shipment, delivery, payment, inventory, or partner-selection status.
- Do not expose internal cost, margin, pricing breakdowns, supplier private notes, backend paths, storage keys, or secrets.
