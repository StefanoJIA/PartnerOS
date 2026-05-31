# D8 Staging Operator Response Intake

**Status:** added on 2026-05-30; use when operations replies to the D8 staging access request.

## Purpose

This intake gate defines what the repository may receive after a staging operator runs or prepares the strict staging evidence flow. It keeps private staging values in private channels while preserving enough redacted context for review, rerun planning, and production coordination.

It is not staging proof by itself and must not be used as `STAGING_VALIDATED` or `STAGING_GAPS_OPEN` evidence. The repository remains `READY_FOR_STAGING` until strict staging evidence is saved and reviewed.

If local rehearsal output is saved where strict staging evidence is expected, production coordination remains at `WAITING_FOR_REAL_STAGING_EVIDENCE` until strict staging evidence from real staging values replaces it.

## Acceptable Repository Inputs

| Item | Acceptable value | Reject if |
|---|---|---|
| `BACKEND_BASE_URL` status | `provided privately` | URL contains credentials, tokens, or private infrastructure that should not be committed |
| `SERVICE_PORTAL_PARTNEROS_TOKEN` status | `provided privately` | Any token value, bearer header, cookie, or screenshot is present |
| `SERVICE_PORTAL_ORIGIN` | HTTPS origin such as `https://service.intelli-opus.com` | Origin includes cookies, paths with secrets, raw headers, or non-HTTPS staging origin |
| `DEPLOYED_COMMIT` | Short SHA, release tag, or deployment label | Raw deployment logs, secrets, or cloud console screenshots are attached |
| `TEST_DATA_SCOPE` | Short redacted fixture description | Real customer files, uploads, raw payloads, or production data are included |
| Evidence files | Canonical `d8_strict_staging_evidence_YYYYMMDD.json` and optional `d8_strict_staging_gaps_YYYYMMDD.md` | Raw response bodies, token values, backend storage paths, or noncanonical names are included |

## Intake Command

```powershell
cd backend
python scripts/d8_staging_operator_response_intake_check.py
python scripts/d8_staging_input_preflight_check.py
python scripts/d8_staging_records_check.py
python scripts/d8_staging_evidence_review_check.py
python scripts/d8_readiness_audit.py
```

## Response Template

The operator may share this redacted response in the repo or issue tracker:

```text
BACKEND_BASE_URL: provided privately
SERVICE_PORTAL_PARTNEROS_TOKEN: provided privately
SERVICE_PORTAL_ORIGIN: https://service.intelli-opus.com
DEPLOYED_COMMIT: <short-sha-or-release>
TEST_DATA_SCOPE: TEST customer/order/product/resource/feedback fixtures only
EVIDENCE_ARTIFACTS: d8_strict_staging_evidence_YYYYMMDD.json; d8_strict_staging_gaps_YYYYMMDD.md if failed
```

## Intake States

| State | Meaning | Next action |
|---|---|---|
| `WAITING_FOR_OPERATOR_RESPONSE` | No private values or evidence have been returned yet | Keep the access request open |
| `READY_FOR_STRICT_EVIDENCE_RUN` | Private values are available to the operator but no evidence is saved | Run strict staging evidence privately and save redacted artifacts |
| `READY_FOR_EVIDENCE_REVIEW` | Evidence artifacts are present and records hygiene passes | Run evidence review and readiness audit |

## Boundaries

- No `.env`, token value, bearer header, cookie, raw header, raw response body, customer file, upload, `local_data`, or `backend/storage` artifact may be committed.
- No email, webhook, carrier API, customer notification, supplier notification, order mutation, shipment mutation, payment action, inventory reservation, partner-selection mutation, nginx edit, cloud upstream edit, or `service.intelli-opus.com` deployment is authorized by intake.
- Internal cost, margin, pricing breakdown, supplier private note, backend path, storage key, token, database URL, and secret values remain excluded from repository, customer-facing APIs, and handoff artifacts.
