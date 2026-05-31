# D8 Strict Staging / Cloud Validation

**Status:** evidence workflow added on 2026-05-30.

## Purpose

This stage turns the D8 integration hardening foundation into a real staging/cloud evidence workflow. It keeps PartnerOS as the system of record and validates the deployed bridge contract without modifying `service.intelli-opus.com`, nginx, customer data, supplier data, orders, shipments, or feedback.

## Stage Goals

| Stage | Goal | Evidence |
|---|---|---|
| S1 - Configuration proof | Confirm staging uses HTTPS public URL, non-default portal token, and HTTPS service portal origin | `d8_strict_staging_evidence_check.py` environment checks |
| S2 - Runtime proof | Confirm deployed backend health, `/api/v1/system/readiness`, and `/api/v1/portal/manifest` respond with v1 envelopes | script output |
| S3 - Portal bridge proof | Confirm missing/wrong portal tokens are rejected and correct token can read products/orders | script output |
| S4 - CORS proof | Confirm `https://service.intelli-opus.com` is allowed for portal bridge preflight | script output |
| S5 - Customer field safety | Confirm bridge responses omit internal cost, margin, pricing breakdowns, storage paths, backend paths, secrets, and tokens | forbidden-field scan |
| S6 - Follow-up register | Record any failing staging evidence as D8 hardening gaps before production coordination | docs or issue tracker |

## Command

```powershell
cd backend
$env:BACKEND_BASE_URL="https://<partneros-staging-backend-origin>"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<portal-server-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
python scripts/d8_strict_staging_evidence_check.py
```

To preserve a redacted JSON evidence record:

```powershell
python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json
```

The JSON record stores check labels, pass/fail states, sanitized URLs, and safety metadata. For a remote staging backend, `backend_base_url` is saved as `https://<redacted-backend>` instead of the real host; local rehearsal URLs may remain local. It does not store the portal token or response bodies.

Before running strict evidence with real values, run `python scripts/d8_staging_input_preflight_check.py`. It performs local-only checks for HTTPS URL shape and non-default token values without calling staging or printing secrets. For local command-order practice only, use [D8 Local Staging Rehearsal](d8_local_staging_rehearsal.md); rehearsal output is not staging evidence and must not be saved under `docs/records`.

To also create a follow-up register for failed checks:

```powershell
python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md
```

The gap register lists failing checks, sanitized details, recommended actions, owner placeholders, and open/closed status. `Owner: TBD` is allowed only as a human owner placeholder until the staging operator assigns a named operator or team; it is not an auto-assignee, notification target, or permission to create tickets.

When a gap register is produced, use [D8 Staging Gap Triage](d8_staging_gap_triage.md) and `python scripts/d8_staging_gap_triage_check.py` to keep ownership, status, and rerun criteria explicit.

For local rehearsal only:

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<local-non-default-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
$env:D8_STRICT_ALLOW_LOCAL_HTTP="true"
python scripts/d8_strict_staging_evidence_check.py
```

## Pass Criteria

- `BACKEND_BASE_URL` is HTTPS for staging/cloud.
- `SERVICE_PORTAL_PARTNEROS_TOKEN` is present, non-default, and not printed.
- placeholder URL/token values are rejected before any network evidence call.
- missing token returns 401 and wrong token returns 403.
- portal CORS preflight allows only the configured service portal origin.
- product and order bridge endpoints return customer-safe envelopes.
- order detail/production/shipment/resources endpoints pass when at least one order exists.
- no forbidden internal markers or the portal token appear in response bodies.

## Boundaries

- no customer portal deployment
- no nginx or upstream edits
- no carrier, webhook, or email calls
- no feedback creation by default
- no quote/order/shipment status mutation
- no secrets, backend paths, storage keys, or local files in evidence output
