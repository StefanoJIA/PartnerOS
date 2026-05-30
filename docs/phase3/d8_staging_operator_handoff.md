# D8 Staging Operator Handoff

**Status:** generator added on 2026-05-30.

## Purpose

The staging operator handoff converts the current D8 readiness state into a redacted, executable handoff document for whoever has the real staging backend URL and service portal token.

It is useful when the implementation work is ready but the real cloud environment values are held by operations or the portal team.

## Command

```powershell
cd backend
python scripts/d8_staging_operator_handoff.py --output ../docs/records/d8_staging_operator_handoff_YYYYMMDD.md
```

The generated document includes:

- current `d8_readiness_audit.py` output
- required environment variables
- preflight commands
- strict staging evidence command
- local staging rehearsal check
- staging handoff bundle check
- staging input preflight check
- staging access request check
- staging gap triage check
- staging records redaction check
- staging evidence review check
- production coordination state check
- D9 post-launch plan check
- D9 operating records redaction check
- Phase 3 roadmap consistency check
- IE Auto project plan consistency check
- project execution chain check
- project execution status summary
- project execution acceptance audit
- project execution records check
- expected evidence/gap artifacts
- safety boundaries

## Safety

The generator does not read `.env`, print tokens, call staging, create feedback, send notifications, or mutate business records. It only reads local repository artifacts and writes a Markdown handoff outside `local_data/` and `backend/storage/`.
