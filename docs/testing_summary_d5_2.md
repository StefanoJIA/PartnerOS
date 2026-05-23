# D5.2 Testing Summary

**Baseline date:** 2026-05-23 · **Release:** D5.2 Internal MVP (through D5.2.11)

## Backend — pytest

```text
cd backend
python -m pytest -q
→ 95 passed, 1 skipped
```

Key suites: `test_api_v1_system.py`, `test_follow_up_rhythm.py`, `test_intelligence_score.py`, `test_health.py`, `test_enrichment_unit.py`.

## Frontend — vitest

```text
cd frontend
npm run test -- --run
→ 44 passed (7 files)
```

Includes: `healthGate`, `followUpRhythm`, `outreachQueue`, `system.spec`, `CompanyEnrichmentPanel`.

## Read-only Scripts (require running backend)

Default `BACKEND_BASE_URL=http://127.0.0.1:8000`. For **8010**:

```powershell
$env:BACKEND_BASE_URL="http://127.0.0.1:8010"
```

| Script | Result (8010 baseline) |
|--------|------------------------|
| `check_backend_runtime.py` | OK |
| `smoke_demo_ready.py` | PASS |
| `pilot_workflow_check.py` | PASS |
| `outreach_queue_check.py` | PASS |
| `real_lead_batch_check.py` | PASS |
| `daily_outreach_summary.py` | OK |
| `portal_readiness_check.py` | PASS |
| `portal_consumer_check.py` | PASS |
| `config_readiness_check.py` | PASS with warnings |

## config_readiness_check.py — Expected Warnings (local dev)

Non-blocking warnings typical on developer machines:

1. **`PUBLIC_BASE_URL` not set** — manifest URLs default to `http://127.0.0.1:8000`; set before production.
2. **`APP_RUNTIME_MODE=development`** — rotate secrets before production.
3. **`SECRET_KEY` development default** — replace before go-live (if still using template default).

Critical failures (must fix): `DATABASE_URL` unreachable, migration pending, missing `SECRET_KEY`.

## Release Pack Verification (D5.2.11)

```powershell
cd backend
python scripts/config_readiness_check.py
python scripts/portal_consumer_check.py
python -m pytest -q
cd ../frontend
npm run test -- --run
```

## What Is Not Tested Automatically

- Browser manual UI (see D5.2.8 record)
- Real LinkedIn / Outlook send (intentionally out of scope)
- Production HTTPS / reverse proxy
- Screenshot PNG archive (manual)

## Records

| Stage | Record |
|-------|--------|
| D5.2.2 | [d5_2_2_internal_mvp_20260523.md](records/d5_2_2_internal_mvp_20260523.md) |
| D5.2.7 | [d5_2_7_follow_up_rhythm_20260523.md](records/d5_2_7_follow_up_rhythm_20260523.md) |
| D5.2.8 | [d5_2_8_browser_manual_verification_20260523.md](records/d5_2_8_browser_manual_verification_20260523.md) |
| D5.2.9 | [d5_2_9_portal_readonly_integration_20260523.md](records/d5_2_9_portal_readonly_integration_20260523.md) |
| D5.2.10 | [d5_2_10_portal_consumer_deployment_readiness_20260523.md](records/d5_2_10_portal_consumer_deployment_readiness_20260523.md) |
