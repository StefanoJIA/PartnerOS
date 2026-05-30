# D8 Readiness Audit

**Status:** added on 2026-05-30.

## Purpose

The readiness audit summarizes whether D8 is locally complete, ready for real staging evidence, blocked by staging gaps, or validated by a saved staging evidence artifact.

It does not call cloud services. It reads repository artifacts, runs the local staging records gate, and inspects optional redacted records under `docs/records/`.

## Command

```powershell
cd backend
python scripts/d8_readiness_audit.py
```

## Statuses

| Status | Meaning | Next action |
|---|---|---|
| `LOCAL_ARTIFACTS_INCOMPLETE` | Required D8 docs/scripts or safety markers are missing | Fix local artifacts before staging |
| `READY_FOR_STAGING` | Local D8 artifacts are present, but no strict staging evidence JSON exists | Run strict staging evidence with real env values |
| `STAGING_GAPS_OPEN` | Latest strict staging evidence failed | Close the generated gap register and rerun evidence |
| `STAGING_VALIDATED` | Latest strict staging evidence passed | Move to production coordination planning |

## Evidence Inputs

The audit looks for:

- D8 delivery stage matrix
- D8 hardening and strict staging docs
- D8 smoke/check scripts
- safety invariants in the stage matrix
- `scripts/d8_staging_records_check.py` result
- production coordination plan artifact
- D9 post-launch operating loop plan artifact
- D9 operating records policy artifact
- Phase 3 roadmap artifact
- IE Auto project plan artifact
- project execution chain artifact
- project execution records checker
- optional `docs/records/d8_strict_staging_evidence_*.json`
- optional paired `docs/records/d8_strict_staging_gaps_*.md`

The audit never reads or prints portal tokens, response bodies, `.env`, `local_data/`, or `backend/storage/`.
