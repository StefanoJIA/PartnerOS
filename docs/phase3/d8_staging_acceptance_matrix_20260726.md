# D8 Staging Acceptance Matrix (2026-07-26)

**Agent:** C — Staging Acceptance Data & Contract  
**Base:** `feat/e2e-supplier-convergence@04ebcb5`  
**Repository stage:** `READY_FOR_STAGING_HANDOFF`  
**External staging:** `WAITING_FOR_REAL_STAGING_EVIDENCE`  
**Current blocker:** `docs/records/d8_staging_preflight_blocker_20260726.json`

## Scope

Maps portal bridge endpoints to fixture requirements, validation scripts, and evidence contract fields. No secrets, no real customer data, no fabricated PASS evidence.

## Endpoint × Fixture × Script Matrix

| ID | Endpoint | Method | Fixture requirement | Primary script check | Pass criteria |
|---|---|---|---|---|---|
| A-01 | `/health` | GET | none | `d8_strict_staging_evidence_check` | HTTP 200 |
| A-02 | `/api/v1/system/readiness` | GET | DB migrated | strict evidence | envelope `ok=true` |
| A-03 | `/api/v1/portal/manifest` | GET | `PUBLIC_BASE_URL` configured | strict evidence | envelope ok; HTTPS base_url |
| A-04 | `/api/v1/portal/customer/manifest` | GET | portal API enabled | `d8_3_service_portal_staging_check` | D8.1 contract fields present |
| A-05 | `/api/v1/portal/customer/products` | GET | ≥1 active product | both | HTTP 200; no forbidden fields |
| A-06 | `/api/v1/portal/customer/orders` | GET | ≥1 non-cancelled order | both | HTTP 200 |
| A-07 | `/api/v1/portal/customer/orders/{id}` | GET | order UUID from list | d8_3 | HTTP 200 |
| A-08 | `/api/v1/portal/customer/orders/{id}/snapshot` | GET | order with milestones/shipment | d8_3 | `customer_status`, `progress_steps`, `planned_dates_are_guarantees=false` |
| A-09 | `/api/v1/portal/customer/orders/{id}/production` | GET | Alpha order milestones | both | HTTP 200 |
| A-10 | `/api/v1/portal/customer/orders/{id}/shipment` | GET | shipment plan on order | both | HTTP 200 |
| A-11 | `/api/v1/portal/customer/orders/{id}/resources` | GET | published customer-visible resource | both | HTTP 200; no storage_key |
| A-12 | `/api/v1/portal/customer/resources/{id}/download` | GET | signed URL from A-11 | manual / contract tests | valid signature only |
| A-13 | `/api/v1/portal/customer/feedback` | POST | optional TEST payload | d8_3 when `D8_3_CREATE_TEST_FEEDBACK=true` | HTTP 201; no auto-notify |
| A-14 | portal auth missing token | GET | none | both | HTTP 401 |
| A-15 | portal auth wrong token | GET | none | both | HTTP 403 |
| A-16 | CORS preflight | OPTIONS | `PORTAL_CUSTOMER_ALLOWED_ORIGINS` | both | allow-origin = `SERVICE_PORTAL_ORIGIN` |
| A-17 | forbidden field scan | all above | seeded data must be clean | both | no cost/margin/storage_key/token leak |

Fixture detail: `backend/scripts/staging_fixture_seed_plan.md`

## Script Contract Audit

### `d8_staging_input_preflight_check.py`

| Field / check | Bound? | Notes |
|---|---|---|
| `BACKEND_BASE_URL` | yes | HTTPS or local rehearsal with flag |
| `SERVICE_PORTAL_PARTNEROS_TOKEN` | yes | length + blocklist |
| `SERVICE_PORTAL_ORIGIN` | yes | HTTPS required |
| `DEPLOYED_COMMIT_SHA` | **no** | preflight only — not required before input presence check |
| execution timestamp | no | not an output artifact |

State outputs: `INPUTS_READY`, `WAITING_FOR_PRIVATE_VALUES`, `INPUTS_UNSAFE`, `LOCAL_REHEARSAL_READY`.

### `d8_3_service_portal_staging_check.py`

| Field / check | Bound? | Notes |
|---|---|---|
| `SERVICE_PORTAL_ORIGIN` | yes | printed redacted |
| `BACKEND_BASE_URL` | yes | redacted in output |
| `deployed_commit_sha` | **no** | contract runner only — no evidence JSON |
| execution timestamp | no | console output only |
| order subresources | conditional | skips detail checks when no orders (`no order rows` PASS) |

Optional feedback: `D8_3_CREATE_TEST_FEEDBACK=true`.

### `d8_strict_staging_evidence_check.py`

| Field / check | Bound? | Notes |
|---|---|---|
| `generated_at` | yes | ISO UTC in evidence JSON |
| `execution_timestamp_utc` | yes (after fix) | duplicate UTC marker for audit clarity |
| `service_portal_origin` | yes | from `SERVICE_PORTAL_ORIGIN` |
| `backend_base_url` | yes | redacted HTTPS |
| `deployed_commit_sha` | yes (after fix) | from `DEPLOYED_COMMIT_SHA` or `DEPLOYED_COMMIT` |
| `allow_local_http` | yes | blocks docs/records for local rehearsal |
| `safety.token_redacted` | yes | always true |
| `safety.response_bodies_stored` | yes | always false |

Downstream gates requiring `deployed_commit_sha` on PASS:

- `d8_staging_evidence_review_check.py`
- `d8_staging_records_check.py`
- `d8_readiness_audit.py`

### `test_portal_staging_security_contract.py`

Covers negative auth, CORS allowlist, field filter, cross-customer UUID access documentation, resource 404, signed download rejection. Runs locally without staging network.

## Acceptance States

| State | Condition |
|---|---|
| `WAITING_FOR_PRIVATE_VALUES` | preflight missing HTTPS URL / token / origin |
| `INPUTS_READY` | preflight pass; smoke not yet run |
| `EVIDENCE_INCOMPLETE` | PASS evidence missing `deployed_commit_sha` (fixed in collector) |
| `READY_FOR_PRODUCTION_COORDINATION_REVIEW` | strict evidence PASS + SHA + HTTPS + redaction |
| `STAGING_VALIDATED` | readiness audit only after real staging evidence chain |

## Contract Gaps Found (Agent C)

| Gap | Severity | Status |
|---|---|---|
| Strict evidence collector did not write `deployed_commit_sha` | **high** | **fixed** on `agent/staging-test-fixtures` |
| Strict evidence had no input gate for `DEPLOYED_COMMIT_SHA` | medium | **fixed** — new check before network |
| No minimal synthetic fixture plan with cross-customer cases | medium | **fixed** — `staging_fixture_seed_plan.md` |
| No dedicated acceptance matrix doc | low | **fixed** — this document |
| `d8_3` passes subresource checks when zero orders | low | **documented** — seed plan requires ≥2 orders |
| Portal token is service-level; per-customer isolation not enforced server-side | informational | **documented** — ISO-01..06 in seed plan |
| `d8_staging_input_preflight_check` does not validate `DEPLOYED_COMMIT_SHA` | low | **accepted** — SHA validated at evidence collection |
| No automated staging seed script in repo | low | **deferred** — operator admin seed per plan; business approval pending |

## Operator Run Sequence (when unblocked)

```powershell
cd backend
$env:BACKEND_BASE_URL="https://<partneros-staging-backend>"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<private-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
$env:DEPLOYED_COMMIT_SHA="04ebcb56883eff81cc8c3b953dfef4c3b47ccd72"

python scripts/d8_staging_input_preflight_check.py
python scripts/d8_3_service_portal_staging_check.py
python scripts/d8_strict_staging_evidence_check.py `
  --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json `
  --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md
python scripts/d8_staging_records_check.py
python scripts/d8_staging_evidence_review_check.py
python scripts/d8_readiness_audit.py
```

## Related Artifacts

- `backend/scripts/staging_fixture_seed_plan.md`
- `docs/phase3/d8_portal_staging_contract_runbook.md`
- `docs/records/d8_staging_preflight_blocker_20260726.json`
- `backend/tests/test_portal_staging_security_contract.py`

## Boundary

Do not write `STAGING_VALIDATED` until real staging credentials, deployed commit SHA, and HTTPS evidence exist. Local rehearsal output must stay outside `docs/records`.
