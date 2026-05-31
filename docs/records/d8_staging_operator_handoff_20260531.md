# D8 Strict Staging Operator Handoff

Generated at: 2026-05-31T20:06:43.650478+00:00
Repository commit: `a249246`
Readiness status: `READY_FOR_STAGING`

## Purpose

Run the PartnerOS D8 strict staging evidence flow against the real deployed staging backend and preserve redacted proof for follow-up.

## Required Inputs

| Variable | Required value |
|---|---|
| `BACKEND_BASE_URL` | HTTPS PartnerOS staging backend origin |
| `SERVICE_PORTAL_PARTNEROS_TOKEN` | Non-default portal server token; do not paste into docs or screenshots |
| `SERVICE_PORTAL_ORIGIN` | `https://service.intelli-opus.com` unless the portal team confirms another HTTPS origin |

## Operator Runbooks

| Runbook | When to use |
|---|---|
| `docs/operator_guide.md` | Review the operator-facing D8/D9 handoff gates and manual-only safety boundaries |
| `docs/phase3/d8_staging_handoff_bundle.md` | Confirm the operator-facing package, commands, evidence command, and exclusions |
| `docs/phase3/d8_staging_operator_runbook.md` | Execute the sequence from `READY_FOR_STAGING_HANDOFF` through input preflight, strict evidence, records review, and next state |
| `docs/phase3/d8_staging_records_policy.md` | Confirm canonical record names, current handoff/access-request requirements, and redaction rules |
| `docs/phase3/d8_production_coordination_runbook.md` | Use only after `STAGING_VALIDATED` for the human Go / No-Go and rollback handoff |

## Preflight

```powershell
cd backend
python scripts/agent_guide_check.py
python scripts/readme_check.py
python scripts/product_vision_check.py
python scripts/desktop_target_architecture_check.py
python scripts/runtime_modes_check.py
python scripts/database_lifecycle_doc_check.py
python scripts/desktop_packaging_docs_check.py
python scripts/web_to_desktop_migration_doc_check.py
python scripts/desktop_transition_roadmap_check.py
python scripts/project_reorientation_summary_check.py
python scripts/dev_guide_check.py
python scripts/integrated_backend_standards_check.py
python scripts/lead_intelligence_docs_check.py
python scripts/manual_a_domain_test_plan_check.py
python scripts/codex_skill_pack_check.py
python scripts/activity_actions_doc_check.py
python scripts/deployment_readiness_checklist_check.py
python scripts/testing_guide_check.py
python scripts/testing_summary_d5_2_check.py
python scripts/d8_readiness_audit.py
python scripts/d8_stage_goal_matrix_check.py
python scripts/d8_integration_hardening_check.py
python scripts/d8_local_staging_rehearsal_check.py
python scripts/d8_staging_handoff_bundle_check.py
python scripts/d8_staging_operator_runbook_check.py
python scripts/d8_staging_input_preflight_check.py
python scripts/d8_staging_access_request_check.py
python scripts/d8_staging_operator_response_intake_check.py
python scripts/d8_staging_gap_triage_check.py
python scripts/d8_staging_records_check.py
python scripts/d8_staging_evidence_review_check.py
python scripts/d8_production_coordination_check.py
python scripts/d8_production_coordination_runbook_check.py
python scripts/d9_post_launch_plan_check.py
python scripts/d9_operating_execution_pack_check.py
python scripts/d9_operating_loop_kickoff_check.py
python scripts/d9_1_operating_health_review_check.py
python scripts/d9_2_order_operations_loop_check.py
python scripts/d9_3_market_response_loop_check.py
python scripts/d9_4_improvement_backlog_check.py
python scripts/d9_operating_records_check.py
python scripts/phase3_roadmap_check.py
python scripts/ie_auto_project_plan_check.py
python scripts/operator_guide_check.py
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
python scripts/project_execution_status.py
python scripts/project_execution_acceptance_audit_check.py
python scripts/project_execution_records_check.py
```

## Strict Staging Evidence Run

```powershell
cd backend
$env:BACKEND_BASE_URL="<partneros-staging-backend-origin>"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<portal-server-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md
```

## Expected Output

- Console result is `PASS` or `FAIL`.
- Evidence JSON is redacted and contains check labels, statuses, sanitized URLs, and safety metadata.
- Gap Markdown is generated when checks fail and can be used as the next fix list.

## Safety Boundaries

- Do not deploy or modify `service.intelli-opus.com` from PartnerOS.
- Do not edit nginx or cloud upstreams from this repository.
- Do not create non-TEST feedback during staging.
- Do not print, screenshot, commit, or paste portal tokens.
- Do not expose internal cost, margin, pricing breakdowns, supplier private notes, storage keys, backend paths, or secrets.
- Do not trigger email, webhook, carrier API, customer notification, supplier notification, or quote/order/shipment mutation.

## Current Readiness Audit

```text
D8 Readiness Audit
[PASS] D8 docs present (31 docs)
[PASS] D8 scripts present (33 scripts)
[PASS] stage matrix safety invariants (documented)
[PASS] staging records hygiene (PASS)
[PASS] strict staging evidence state (READY_FOR_STAGING: no strict staging evidence JSON found)
Overall: READY_FOR_STAGING
Next: run scripts/d8_strict_staging_evidence_check.py with real staging values and save evidence/gap artifacts.
```
