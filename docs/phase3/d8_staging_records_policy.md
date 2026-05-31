# D8 Staging Records Policy

**Status:** added on 2026-05-30.

## Purpose

D8 staging evidence must be durable enough for handoff, but narrow enough to avoid leaking tokens, customer data, supplier notes, storage paths, or internal pricing signals.

Use `docs/records` for redacted staging artifacts only. Do not store `.env`, screenshots containing secrets, raw response bodies, uploads, `local_data`, or files from `backend/storage`.

## Canonical Names

| Artifact | Path |
|---|---|
| Operator handoff | `docs/records/d8_staging_operator_handoff_YYYYMMDD.md` |
| Staging access request | `docs/records/d8_staging_access_request_YYYYMMDD.md` |
| Strict staging evidence | `docs/records/d8_strict_staging_evidence_YYYYMMDD.json` |
| Strict staging gaps | `docs/records/d8_strict_staging_gaps_YYYYMMDD.md` |
| Production Go / No-Go decision | `docs/records/d8_production_go_no_go_YYYYMMDD.md` |

The evidence JSON should come from:

```powershell
cd backend
python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md
```

The operator handoff should come from:

```powershell
cd backend
python scripts/d8_staging_operator_handoff.py --output ../docs/records/d8_staging_operator_handoff_YYYYMMDD.md
```

The staging access request record may be committed only when it contains placeholders or `provided privately` status lines, not the actual backend URL if it reveals private infrastructure and never the portal token.

## Record Gate

Run this before committing any D8 staging evidence:

```powershell
cd backend
python scripts/d8_staging_records_check.py
```

The check verifies canonical names, the current operator handoff and staging access request records, redaction markers, strict evidence safety metadata, required safety markers for any committed production Go / No-Go decision record, and the matching gap register for failed evidence. In strict staging evidence, any remote backend host is stored as `https://<redacted-backend>`; local rehearsal URLs such as `http://127.0.0.1:8014` may remain visible because they do not reveal private infrastructure.

Canonical evidence with `result=PASS` must come from real staging, not local rehearsal. A PASS evidence record with `allow_local_http=true` or a localhost `backend_base_url` is rejected by the records gate and must not produce `STAGING_VALIDATED`.

Strict staging evidence and gap records are not required before the real staging run. Until then, the records gate should pass with the current handoff and access request records while evidence review remains `WAITING_FOR_STAGING_EVIDENCE`.

For failed evidence, use [D8 Staging Gap Triage](d8_staging_gap_triage.md) before production coordination. Each gap row should retain a recommended action, owner, and status until a rerun proves it fixed or superseded.

After records pass, use [D8 Staging Evidence Review](d8_staging_evidence_review.md) and `python scripts/d8_staging_evidence_review_check.py` to interpret the latest saved evidence as waiting, ready for production coordination review, or requiring gap triage.

If a production Go / No-Go decision record is committed, it must include `Decision:`, `Evidence source: redacted summary only`, and a Safety section confirming no nginx/upstream change from this repository, no customer or supplier notification, no automatic business-status mutation, and no tokens, raw response bodies, internal costs, supplier private notes, backend paths, storage keys, database URLs, or secrets.

## Boundaries

- Do not paste real `SERVICE_PORTAL_PARTNEROS_TOKEN` or `PORTAL_CUSTOMER_API_TOKEN` values into records.
- Do not store raw API response bodies.
- Do not store internal cost, margin, pricing breakdown, supplier private note, backend path, storage key, database URL, password hash, or secret key values.
- Do not use staging records as deployment instructions for `service.intelli-opus.com`; that portal stays outside this repo.
