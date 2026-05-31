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
| `STAGING_EVIDENCE_LOCAL_REHEARSAL` | Latest strict evidence used local HTTP rehearsal or localhost backend | Re-run strict staging evidence with real staging values |
| `STAGING_EVIDENCE_NONCANONICAL` | A strict staging evidence-like file exists but does not use the canonical `YYYYMMDD` name | Rename/regenerate evidence with canonical names before review |
| `STAGING_EVIDENCE_UNREADABLE` | Latest canonical strict staging evidence cannot be parsed as valid evidence JSON | Regenerate evidence and rerun records/review gates |

## Evidence Inputs

The audit looks for:

- D8 delivery stage matrix
- D8 hardening and strict staging docs
- D8 smoke/check scripts
- D8 local staging rehearsal runbook
- D8 staging handoff bundle
- D8 staging input preflight
- D8 staging access request
- D8 staging operator response intake
- D8 staging gap triage runbook
- safety invariants in the stage matrix
- `scripts/d8_staging_records_check.py` result
- D8 staging evidence review artifact
- production coordination plan artifact
- D9 post-launch operating loop plan artifact
- D9 operating records policy artifact
- Phase 3 roadmap artifact
- IE Auto project plan artifact
- project execution chain artifact
- project execution records checker
- optional canonical `docs/records/d8_strict_staging_evidence_YYYYMMDD.json`
- optional paired canonical `docs/records/d8_strict_staging_gaps_YYYYMMDD.md`

The audit never reads or prints portal tokens, response bodies, `.env`, `local_data/`, or `backend/storage/`.
