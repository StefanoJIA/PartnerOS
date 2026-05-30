# D9 Operating Records Policy

**Status:** planned on 2026-05-30.

## Purpose

D9 records preserve post-launch operating evidence without storing secrets, raw API payloads, customer files, internal cost, supplier private notes, or deployment instructions.

Use `docs/records` only for redacted summaries. Do not store `.env`, raw response bodies, screenshots containing tokens, uploads, `local_data`, or files from `backend/storage`.

## Canonical Names

| D9 loop | Path |
|---|---|
| Operating health | `docs/records/d9_operating_health_YYYYMMDD.md` |
| Order operations | `docs/records/d9_order_operations_YYYYMMDD.md` |
| Market response | `docs/records/d9_market_response_YYYYMMDD.md` |
| Improvement backlog | `docs/records/d9_improvement_backlog_YYYYMMDD.md` |

## Record Gate

Run this before committing any D9 operating records:

```powershell
cd backend
python scripts/d9_operating_records_check.py
```

The check verifies canonical names and scans D9 records for token assignments, internal cost/margin markers, storage paths, local data paths, backend secrets, and raw response body markers.

## Template

```markdown
# D9 Operating Review - YYYY-MM-DD

Loop: Operating health | Order operations | Market response | Improvement backlog
Evidence source: redacted summary only
Owner: TBD
Status: open

## Signals

- Signal:
- Evidence:
- Customer-visible impact:
- Operator action:

## Follow-Up

- Owner:
- Next action:
- Due:

## Safety

- No tokens or raw response bodies included.
- No internal cost, margin, supplier private note, backend path, storage key, database URL, or secret included.
- No automatic customer/supplier notification or business-status mutation triggered.
```
