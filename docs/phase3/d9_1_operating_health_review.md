# D9.1 Operating Health Review

**Status:** planned on 2026-05-30; starts only after D8 production coordination, evidence review, and D9 kickoff.

## Purpose

D9.1 is the first post-launch operating review track. It checks whether the PartnerOS backend and existing service portal bridge remain healthy after production coordination and evidence review, without exposing tokens, raw API payloads, customer files, or deployment details.

It is a review loop, not a deployment or remediation mechanism.

## Entry Criteria

| Gate | Required evidence |
|---|---|
| D8 staging validation | `python scripts/d8_readiness_audit.py` reports `STAGING_VALIDATED` |
| D8 production coordination | `python scripts/d8_production_coordination_check.py` reports `READY_FOR_PRODUCTION_COORDINATION` |
| D8 evidence review | `python scripts/d8_staging_evidence_review_check.py` reports `READY_FOR_PRODUCTION_COORDINATION_REVIEW` |
| D9 kickoff | `python scripts/d9_operating_loop_kickoff_check.py` passes |
| D9 records hygiene | `python scripts/d9_operating_records_check.py` passes |

## Review Signals

| Signal | Review question | Record field |
|---|---|---|
| Readiness | Does `/api/v1/system/readiness` remain healthy enough for portal reads? | Readiness summary |
| Manifest | Does `/api/v1/portal/manifest` expose the expected customer-safe bridge contract? | Manifest summary |
| Token rejection | Are missing and wrong portal tokens still rejected? | Auth summary |
| CORS | Is only the approved service portal origin accepted? | CORS summary |
| Customer-safe reads | Do products, orders, production, shipment, resources, and feedback-status reads remain customer-safe? | Portal read summary |
| Forbidden fields | Are cost, margin, supplier private notes, backend paths, storage keys, tokens, and secrets absent? | Safety summary |

## Review Command

```powershell
cd backend
python scripts/d9_1_operating_health_review_check.py
python scripts/d9_operating_loop_kickoff_check.py
python scripts/d9_operating_records_check.py
```

## Record Template

Use a canonical redacted record name such as `docs/records/d9_operating_health_YYYYMMDD.md`.

```markdown
# D9 Operating Health - YYYY-MM-DD

Loop: Operating health
Evidence source: redacted summary only
Owner: TBD
Status: open

## Signals

- Readiness summary:
- Manifest summary:
- Auth summary:
- CORS summary:
- Portal read summary:
- Safety summary:

## Follow-Up

- Owner:
- Next action:
- Due:

## Safety

- No tokens or raw response bodies included.
- No internal cost, margin, supplier private note, backend path, storage key, database URL, or secret included.
- No automatic customer/supplier notification or business-status mutation triggered.
```

## Boundaries

- No `.env`, token value, bearer header, cookie, raw header, raw response body, customer file, upload, `local_data`, or `backend/storage` artifact may be committed.
- No email, webhook, carrier API, customer notification, supplier notification, order mutation, shipment mutation, payment action, inventory reservation, partner-selection mutation, nginx edit, cloud upstream edit, or `service.intelli-opus.com` deployment is authorized by D9.1.
- Internal cost, margin, pricing breakdown, supplier private note, backend path, storage key, token, database URL, and secret values remain excluded from D9 records and customer-facing artifacts.
