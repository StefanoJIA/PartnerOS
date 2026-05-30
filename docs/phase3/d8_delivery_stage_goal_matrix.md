# D8 Delivery Stage Goal Matrix

**Status:** maintained on 2026-05-30.

This matrix turns the D7.9-D8 work into a compact execution and evidence map. It is meant to answer four questions before the next sprint:

1. What is the stage goal?
2. What artifact proves the stage exists?
3. What command proves the stage still works?
4. What remains before production coordination?

## Matrix

| Stage | Stage goal | Primary artifact | Verification command | Evidence status | Next gap |
|---|---|---|---|---|---|
| D7.9 Resource Center | Customer-safe order resources and signed downloads | `docs/phase3/d7_9_resource_center.md` | `python scripts/d7_9_resource_center_check.py` | Implemented | Run in staging with real customer-safe sample resources |
| D8.1 RBAC / Scoped Access | Internal permission presets and guarded v1 routes | `docs/phase3/d8_1_rbac_scoped_access.md` | `python scripts/d8_1_rbac_scoped_access_check.py` | Implemented | Confirm role assignments in staging seed/admin data |
| D8.2 Runtime Hardening | Staging/local readiness, token, CORS, storage checks | `docs/phase3/d8_2_runtime_hardening.md` | `python scripts/d8_2_runtime_hardening_check.py` | Implemented | Run strict mode with real staging env values |
| D8.3 Service Portal Staging | HTTP contract runner for existing service portal bridge | `docs/phase3/d8_3_service_portal_staging_integration.md` | `python scripts/d8_3_service_portal_staging_check.py` | Contract runner implemented | Execute against deployed staging backend and real portal token |
| D8.4 Partner Operations | Read-only multi-partner execution and risk board | `docs/phase3/d8_4_multi_partner_operations_dashboard.md` | `python scripts/d8_4_partner_operations_check.py` | Implemented | Browser/UAT review with representative partner split data |
| D8.5 Market Response | Feedback, win-loss, demand, product-gap, advisory board | `docs/phase3/d8_5_market_response_intelligence.md` | `python scripts/d8_5_market_response_check.py` | Implemented | Validate signal usefulness with real feedback and market notes |
| D8 Integration Hardening | Local bridge/deployment contract gate | `docs/phase3/d8_integration_hardening.md` | `python scripts/d8_integration_hardening_check.py` | Foundation implemented | Keep as preflight before every staging run |
| Strict Staging / Cloud Validation | Real staging evidence and gap register | `docs/phase3/d8_strict_staging_cloud_validation.md` | `python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md` | Evidence workflow added | Needs real `BACKEND_BASE_URL`, `SERVICE_PORTAL_PARTNEROS_TOKEN`, and portal origin |
| D8 Readiness Audit | Summarize local readiness vs staging evidence state | `docs/phase3/d8_readiness_audit.md` | `python scripts/d8_readiness_audit.py` | Added | Use before and after each strict staging evidence run |
| D8 Staging Operator Handoff | Generate an executable handoff for the staging operator | `docs/phase3/d8_staging_operator_handoff.md` | `python scripts/d8_staging_operator_handoff.py --output ../docs/records/d8_staging_operator_handoff_YYYYMMDD.md` | Added | Send to the operator who owns real staging values |
| D8 Staging Execution Pack | Verify the handoff chain is internally consistent | `docs/phase3/d8_staging_execution_pack.md` | `python scripts/d8_staging_execution_pack_check.py` | Added | Run before sharing the staging handoff |
| D8 Staging Records Policy | Keep real staging records canonical and redacted | `docs/phase3/d8_staging_records_policy.md` | `python scripts/d8_staging_records_check.py` | Added | Run before committing staging evidence artifacts |
| D8 Production Coordination | Define the post-`STAGING_VALIDATED` handoff and Go / No-Go path | `docs/phase3/d8_production_coordination_plan.md` | `python scripts/d8_production_coordination_check.py` | Added | Wait for strict staging evidence to report `STAGING_VALIDATED` |
| D9 Post-Launch Operating Loop | Plan the monitored operating loop after production coordination | `docs/phase3/d9_post_launch_operating_loop.md` | `python scripts/d9_post_launch_plan_check.py` | Planned | Starts only after D8 production coordination |
| D9 Operating Records Policy | Keep post-launch operating records canonical and redacted | `docs/phase3/d9_operating_records_policy.md` | `python scripts/d9_operating_records_check.py` | Planned | Run before committing D9 operating records |

## Safety Invariants

- No automatic customer or supplier notification.
- No email, webhook, carrier API, nginx, or customer portal deployment from this repository.
- No automatic order, shipment, delivery, payment, or partner-selection mutation.
- No customer-facing internal cost, margin, pricing breakdown, supplier private note, storage key, backend path, token, or secret.
- AI remains advisory and human-reviewed.

## Immediate Stage Goal

Run the strict staging evidence command with real staging values and save both artifacts:

```powershell
cd backend
$env:BACKEND_BASE_URL="https://partneros-staging.example.com"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<portal-server-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md
```

If the evidence result is `FAIL`, the gap register becomes the next sprint input. If the result is `PASS`, the next sprint can move to production coordination using [D8 Production Coordination Plan](d8_production_coordination_plan.md) without changing `service.intelli-opus.com` from PartnerOS.
