# Testing Matrix

Use this matrix for Codex/agent validation of current PartnerOS D7.6+ and D8 handoff work.

## Backend Acceptance

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
alembic upgrade head
python scripts/d7_7_portal_bridge_check.py
python scripts/d7_6_shipment_tracking_check.py
python scripts/d7_5_production_milestone_check.py
python scripts/smoke_all_d5.py
python scripts/dev_runtime_doctor.py
python scripts/readme_check.py
python scripts/deployment_readiness_checklist_check.py
python scripts/testing_guide_check.py
python scripts/operator_guide_check.py
python scripts/codex_skill_pack_check.py
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
python scripts/project_execution_status.py
python scripts/d8_staging_execution_pack_check.py
python scripts/d9_operating_execution_pack_check.py
python scripts/project_execution_acceptance_audit_check.py
python -m pytest -q
```

## Frontend Acceptance

```powershell
cd frontend
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"
npm run test -- --run
```

## Meaning

- `READY_FOR_STAGING_HANDOFF` means local docs, gates, and handoff runbooks agree.
- Local validation does not prove `STAGING_VALIDATED`.
- D8/D9 execution packs and the acceptance audit must pass locally before claiming the handoff package is ready.
- Strict staging evidence requires real private staging values and `python scripts/d8_strict_staging_evidence_check.py --evidence-json ... --gap-markdown ...`.

Warnings from optional Redis/worker/PUBLIC_BASE_URL checks are acceptable in local development if the scripts still report PASS.
