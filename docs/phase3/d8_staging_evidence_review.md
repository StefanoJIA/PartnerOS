# D8 Staging Evidence Review

**Status:** added on 2026-05-30; use after strict staging evidence is generated.

## Purpose

This review gate explains how to read saved D8 strict staging evidence after the staging operator runs the real command. It sits between the evidence/records checks and production coordination.

It does not call staging, deploy the customer portal, edit nginx, send notifications, or mutate orders, shipments, payments, feedback, inventory, or partner selection.

## Inputs

| Artifact | Expected name |
|---|---|
| Strict staging evidence | `docs/records/d8_strict_staging_evidence_YYYYMMDD.json` |
| Strict staging gap register, when evidence fails | `docs/records/d8_strict_staging_gaps_YYYYMMDD.md` |

The evidence JSON must come from:

```powershell
cd backend
python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md
```

## Review Command

```powershell
cd backend
python scripts/d8_staging_records_check.py
python scripts/d8_readiness_audit.py
python scripts/d8_staging_evidence_review_check.py
```

## Review States

| State | Meaning | Next action |
|---|---|---|
| `WAITING_FOR_STAGING_EVIDENCE` | No saved strict staging evidence exists yet | Obtain private staging values and run strict staging evidence |
| `READY_FOR_PRODUCTION_COORDINATION_REVIEW` | Latest evidence is `PASS`, redacted, and schema-readable | Run production coordination checks before any external release action |
| `STAGING_GAPS_REQUIRE_TRIAGE` | Latest evidence is `FAIL` or has a matching gap register need | Use D8 Staging Gap Triage, assign owners, fix, and rerun evidence |
| `EVIDENCE_LOCAL_REHEARSAL` | Latest strict evidence used `allow_local_http=true` or a localhost backend | Re-run strict staging evidence with real staging values |

## Human Review Checklist

- Confirm `d8_staging_records_check.py` passes before sharing or committing records.
- Confirm `d8_readiness_audit.py` reports the same state implied by the latest evidence.
- Confirm the saved canonical evidence did not use `allow_local_http=true` or a localhost `backend_base_url`.
- For `PASS`, verify the evidence date, deployed commit, backend origin, and portal origin with the staging operator. The saved evidence should show a remote backend as `https://<redacted-backend>`, with the real `BACKEND_BASE_URL` kept in the private operator channel.
- For `FAIL`, verify each gap has an owner, status, recommended action, and rerun date before production coordination.
- Do not treat local rehearsal output as `STAGING_VALIDATED` or `STAGING_GAPS_OPEN`.

## Boundaries

- No `.env`, token value, raw response body, customer file, upload, `local_data`, or `backend/storage` artifact may be committed.
- No email, webhook, carrier API, customer notification, supplier notification, order mutation, shipment mutation, payment action, inventory reservation, partner-selection mutation, nginx edit, cloud upstream edit, or `service.intelli-opus.com` deployment is authorized by this review.
- Internal cost, margin, pricing breakdown, supplier private note, backend path, storage key, token, database URL, and secret values remain excluded from customer-facing and handoff artifacts.
