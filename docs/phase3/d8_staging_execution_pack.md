# D8 Staging Execution Pack

**Status:** added on 2026-05-30.

## Purpose

The staging execution pack verifies that the D8 handoff chain is complete before anyone runs real staging validation.

It checks that the repository contains:

- README current-stage checker
- deployment readiness checklist and checker
- testing guide and checker
- readiness audit
- stage goal matrix
- integration hardening gate
- strict staging evidence runner
- local staging rehearsal runbook and checker
- operator handoff generator
- operator guide and handoff gate checker
- staging handoff bundle manifest and checker
- staging operator runbook and checker
- staging input preflight checker
- staging access request doc and checker
- staging operator response intake runbook and checker
- staging gap triage runbook and checker
- staging records policy and redaction checker
- staging evidence review gate
- production coordination plan checker
- production coordination runbook checker
- D9 post-launch operating loop plan checker
- D9 operating execution pack checker
- D9 operating records redaction checker
- project execution chain gate doc
- Phase 3 roadmap consistency checker
- IE Auto project plan consistency checker
- project execution chain checker
- project execution status summary
- project execution acceptance audit
- project execution records checker
- agent guide checker
- product vision checker
- desktop target architecture checker
- runtime modes checker
- database lifecycle checker
- desktop packaging docs checker
- Web-to-desktop migration checker
- desktop transition roadmap checker
- project reorientation summary checker
- developer guide checker
- integrated backend standards checker
- Lead Intelligence docs checker
- Codex skill pack checker
- activity actions doc checker
- matching phase 3 docs

It also runs the agent guide checker, README checker, product vision checker, desktop target architecture checker, runtime modes checker, database lifecycle checker, desktop packaging docs checker, Web-to-desktop migration checker, desktop transition roadmap checker, project reorientation summary checker, developer guide checker, integrated backend standards checker, Lead Intelligence docs checker, Codex skill pack checker, activity actions doc checker, deployment readiness checklist checker, testing guide checker, local staging rehearsal checker, staging handoff bundle checker, staging operator runbook checker, staging input preflight checker, staging access request checker, staging gap triage checker, staging records checker, staging evidence review checker, production coordination checker, production coordination runbook checker, D9 plan checker, D9 operating execution pack checker, D9 records checker, Phase 3 roadmap checker, IE Auto project plan checker, operator guide checker, project execution chain checker, project execution status summary, and project execution acceptance audit, generates a temporary handoff, and checks that the handoff includes required environment variables, preflight commands, evidence/gap artifact commands, and safety boundaries.

The project execution chain gate is documented separately in [Project Execution Chain Gate](project_execution_chain_gate.md). It is the local aggregate proof for `READY_FOR_STAGING_HANDOFF`; it does not replace strict staging evidence or produce `STAGING_VALIDATED`.

## Command

```powershell
cd backend
python scripts/d8_staging_execution_pack_check.py
```

For a redacted top-level execution-chain report:

```powershell
cd backend
python scripts/project_execution_chain_check.py --report-markdown ../docs/records/project_execution_chain_YYYYMMDD.md
```

The report stores gate labels, status, and one-line summaries only. It does not store raw command output, response bodies, tokens, customer files, or backend storage paths. Before committing generated reports, run `python scripts/project_execution_records_check.py`.

## Result Meaning

| Result | Meaning |
|---|---|
| `PASS` | The local staging execution pack is internally consistent and ready to hand to a staging operator |
| `FAIL` | A script, doc, handoff command, or safety marker is missing and should be fixed before staging |

The check is local and read-only. It does not call staging, read tokens, print secrets, create feedback, deploy the customer portal, or mutate business records.
