# D8 Local Staging Rehearsal

**Status:** added on 2026-05-30; optional rehearsal before real staging values arrive.

## Purpose

The local staging rehearsal lets an operator practice the strict evidence command order against a local backend without creating real staging evidence or implying `STAGING_VALIDATED`.

This rehearsal is useful for checking shell syntax, command sequencing, redaction checks, and handoff flow. It is not a substitute for the real staging run.

## Command

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<local-non-default-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
$env:D8_STRICT_ALLOW_LOCAL_HTTP="true"
python scripts/d8_staging_input_preflight_check.py
python scripts/d8_strict_staging_evidence_check.py
```

## Optional Scratch Artifacts

If a rehearsal needs files, write scratch files outside committed records or delete them before committing:

```powershell
$evidence = Join-Path $env:TEMP "d8_strict_staging_evidence_YYYYMMDD.json"
$gaps = Join-Path $env:TEMP "d8_strict_staging_gaps_YYYYMMDD.md"
python scripts/d8_strict_staging_evidence_check.py --evidence-json $evidence --gap-markdown $gaps
```

Do not commit rehearsal evidence as staging proof. If local rehearsal artifacts are kept for debugging, keep them outside `docs/records`, or remove them before handoff.

## Expected Result

- `d8_staging_input_preflight_check.py` may report `INPUTS_UNSAFE` for local HTTP unless the rehearsal intentionally uses `D8_STRICT_ALLOW_LOCAL_HTTP=true`.
- `d8_strict_staging_evidence_check.py` may pass or fail depending on local backend, DB, token, and sample data.
- `d8_readiness_audit.py` must remain `READY_FOR_STAGING` unless real staging evidence is saved.

## Boundaries

- No local rehearsal artifact proves `STAGING_VALIDATED`.
- No `.env`, real staging token, raw response body, customer file, upload, `local_data`, or `backend/storage` artifact may be committed.
- No email, webhook, carrier API, customer notification, supplier notification, order mutation, shipment mutation, payment action, inventory reservation, partner-selection mutation, nginx edit, cloud upstream edit, or `service.intelli-opus.com` deployment is authorized by rehearsal.
