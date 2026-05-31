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

## Current Proof Records

| Record | Meaning |
|---|---|
| `docs/records/project_execution_chain_20260531.md` | Redacted local chain proof for the current handoff state |
| `docs/records/d8_staging_operator_handoff_20260531.md` | Redacted operator handoff generated from local gates |
| `docs/records/d8_staging_access_request_20260531.md` | Redacted request for private staging values |

## Gate Chain

| Gate | Purpose |
|---|---|
| Agent guide | Confirms `AGENTS.md` names the current runtime port, D7 boundaries, validation matrix, and safety rules for future agents |
| README | Confirms the repository entrypoint names the current D8/D9 handoff state and next action |
| Product vision | Confirms the top-level product framing matches current D7-D9 execution, portal boundaries, and manual-only safety rules |
| Desktop target architecture | Confirms the desktop/local-first target architecture is reconciled with current D8 staging handoff boundaries |
| Runtime modes | Confirms runtime mode semantics, local port guidance, health contract, and staging boundaries are current |
| Database lifecycle | Confirms PostgreSQL lifecycle semantics, health fields, migration behavior, and final-user database boundaries are current |
| Desktop packaging docs | Confirms packaging strategy and desktop open questions match the current D8 handoff boundary |
| Web-to-desktop migration | Confirms the current browser-based implementation is mapped to the desktop target without forking business logic or bypassing staging gates |
| Desktop transition roadmap | Confirms the desktop-first product roadmap is reconciled with the current D7-D9 execution state |
| Project reorientation summary | Confirms the strategic reorientation summary no longer points to stale D0/D1 kickoff priorities |
| Developer guide | Confirms the developer workflow uses current `8014` D7.6+/D8 handoff validation and avoids stale D0/D5 setup guidance |
| Integrated backend standards | Confirms backend/API/portal bridge standards match current D7-D9 safety and handoff boundaries |
| Lead Intelligence docs | Confirms Lead Intelligence, public-source enrichment, and scoring docs match current evidence-first and human-review rules |
| Manual A-domain test plan | Confirms manual Lead Intelligence UAT, data-entry rules, and record hygiene match current D8 handoff boundaries |
| Codex skill pack | Confirms project-specific agent rules match current D7-D9 execution state, ports, and safety boundaries |
| Activity actions | Confirms canonical activity/timeline actions and manual-only side-effect boundaries |
| Deployment readiness checklist | Confirms the staging handoff checklist matches D8/D9 evidence gates and no longer carries D5-era deploy steps |
| Testing guide | Confirms the local validation matrix uses the current D7.6+/D8 `8014` checks and separates local validation from strict staging evidence |
| D5.2 testing summary | Confirms the historical D5.2 testing record is clearly superseded by current D8/D9 validation |
| IE Auto project plan | Confirms product positioning, lifecycle, safety rules, and current D7-D9 execution order |
| Phase 3 roadmap | Confirms D7-D9 stages, dependency graph, related docs, and safety boundaries |
| D8 stage goal matrix | Confirms stage artifacts, smoke commands, evidence state, and next gaps |
| Operator guide | Confirms operator-facing D8/D9 handoff instructions, evidence gates, and safety boundaries |
| D8 readiness audit | Classifies local readiness and saved strict staging evidence |
| D8 local staging rehearsal | Confirms the optional local command-order rehearsal is documented and not treated as staging proof |
| D8 staging handoff bundle | Confirms the operator-facing handoff manifest is complete and redacted |
| D8 staging operator runbook | Confirms the operator sequence from handoff through evidence review is complete and redacted |
| D8 staging input preflight | Confirms provided staging inputs are missing-but-waiting or safe to use |
| D8 staging access request | Confirms the private staging input request is complete and redacted |
| D8 staging operator response intake | Confirms operator replies can be accepted without token values, raw payloads, or unsafe artifacts |
| D8 staging gap triage | Confirms failed staging evidence has an owner/status/rerun loop |
| D8 staging evidence review | Interprets saved strict staging evidence as waiting, production-coordination-ready, or requiring triage |
| D8 production coordination | Keeps production coordination blocked until strict staging has validated and evidence review is ready |
| D8 production coordination runbook | Confirms the human Go / No-Go and rollback handoff sequence is complete and redacted |
| D9 post-launch plan | Confirms post-launch loop remains planned behind `STAGING_VALIDATED`, `READY_FOR_PRODUCTION_COORDINATION_REVIEW`, production coordination, and human Go / No-Go handoff |
| D9 operating execution pack | Confirms the full D9 local operating gate set runs together and references `docs/records/d8_production_go_no_go_YYYYMMDD.md` if committed |
| D9 operating loop kickoff | Confirms the first D9 review session remains gated behind D8 production coordination, evidence review, and human Go / No-Go handoff |
| D9.1 operating health review | Confirms the first D9 health track has redacted signal and record rules after the D8 Go / No-Go gate |
| D9.2 order operations loop | Confirms the D9 order execution track has redacted signal and follow-up rules after the D8 Go / No-Go gate |
| D9.3 market response loop | Confirms the D9 market response track remains advisory and redacted after the D8 Go / No-Go gate |
| D9.4 improvement backlog | Confirms repeated operating gaps become reviewed backlog candidates only after the D8 Go / No-Go gate |
| D9 operating records | Confirms D9 record naming and redaction policy |
| Project execution acceptance audit | Maps the current project-planning objective to evidence and missing external staging proof |
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
