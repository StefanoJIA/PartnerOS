# Project Execution Chain Gate

**Status:** added on 2026-05-30.

## Purpose

The project execution chain gate is the top-level local proof that the D7-D9 planning, handoff, readiness, and records checks still agree before a staging operator uses real environment values.

It is intentionally local and read-only. It does not call staging, read `.env`, print tokens, create feedback, send notifications, mutate orders, mutate shipments, mutate payments, edit nginx, deploy `service.intelli-opus.com`, or call carrier APIs.

## Command

```powershell
cd backend
python scripts/project_execution_chain_check.py
python scripts/project_execution_status.py
```

For a redacted handoff report:

```powershell
cd backend
python scripts/project_execution_chain_check.py --report-markdown ../docs/records/project_execution_chain_YYYYMMDD.md
python scripts/project_execution_records_check.py
```

The report stores gate labels, pass/fail status, and one-line summaries only. It must not store raw command output, response bodies, portal tokens, customer files, backend storage paths, `local_data` paths, cost or margin details, supplier private notes, or secrets.

## Gate Chain

| Gate | Purpose |
|---|---|
| IE Auto project plan | Confirms product positioning, lifecycle, safety rules, and current D7-D9 execution order |
| Phase 3 roadmap | Confirms D7-D9 stages, dependency graph, related docs, and safety boundaries |
| D8 stage goal matrix | Confirms stage artifacts, smoke commands, evidence state, and next gaps |
| D8 readiness audit | Classifies local readiness and saved strict staging evidence |
| D8 staging handoff bundle | Confirms the operator-facing handoff manifest is complete and redacted |
| D8 staging access request | Confirms the private staging input request is complete and redacted |
| D8 staging gap triage | Confirms failed staging evidence has an owner/status/rerun loop |
| D8 production coordination | Keeps production coordination blocked until strict staging has validated |
| D9 post-launch plan | Confirms post-launch loop remains planned behind D8 validation |
| D9 operating records | Confirms D9 record naming and redaction policy |
| Project execution records | Confirms generated execution reports are canonical and redacted |

`project_execution_status.py` is a companion summary, not a replacement gate. It reads the project execution chain, D8 readiness audit, and D8 production coordination check, then prints the current stage and next action.

## States

| State | Meaning | Next action |
|---|---|---|
| `READY_FOR_STAGING_HANDOFF` | Local planning, readiness, handoff, and records gates passed | Give the staging operator the D8 handoff and run strict staging evidence with real values |
| `LOCAL_EXECUTION_CHAIN_INCOMPLETE` | At least one local gate failed or the optional report could not be written safely | Fix the failed gate before staging handoff |

This state is not the same as `STAGING_VALIDATED`. The repository can be ready for handoff while still waiting for real `BACKEND_BASE_URL`, `SERVICE_PORTAL_PARTNEROS_TOKEN`, and `SERVICE_PORTAL_ORIGIN` values.

## Safety Boundaries

- No automatic customer or supplier notification.
- No email, webhook, carrier API, nginx edit, or customer portal deployment from this repository.
- No automatic order, shipment, delivery, payment, inventory, or partner-selection mutation.
- No customer-facing internal cost, margin, pricing breakdown, supplier private note, backend path, storage key, token, or secret.
- AI recommendations and execution summaries remain advisory and human-reviewed.
