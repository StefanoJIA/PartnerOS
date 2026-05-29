# D8.2 Runtime Hardening

**Status:** implemented on 2026-05-29.

## Goal

D8.2 adds a staging-oriented runtime check before the service portal integration work. It does not change deployment topology; it makes misconfigured local and staging environments visible earlier.

## Check Script

```powershell
cd backend
python scripts/d8_2_runtime_hardening_check.py
```

For stricter staging gates:

```powershell
$env:D8_2_STRICT_STAGING="true"
python scripts/d8_2_runtime_hardening_check.py
```

Strict mode upgrades unsafe production/staging states to failures, including development runtime mode, non-HTTPS public base URL, missing or unsafe portal token, disabled portal token requirement, and missing service portal CORS origin.

## Coverage

| Area | What It Checks |
|---|---|
| Runtime mode | Flags development mode in local; fails it in strict staging |
| Secrets | Detects missing/default/short `SECRET_KEY` without printing the value |
| Public URL | Requires HTTPS in strict staging |
| DB and migrations | Masks `DATABASE_URL`, checks connectivity, checks Alembic head |
| Proxy alignment | Compares `BACKEND_BASE_URL` and `VITE_API_PROXY_TARGET` |
| Portal bridge | Checks enabled state, token requirement, token safety, and allowed origins |
| Storage hygiene | Confirms local sensitive paths are gitignored |

## Safety

- The script is read-only.
- It does not print token or secret values.
- It does not start, stop, migrate, seed, email, webhook, or notify.
- Portal bridge field whitelisting remains covered by D7.7-D7.9 smoke scripts.

## Recommended Gate

```powershell
cd backend
python scripts/d8_1_rbac_scoped_access_check.py
python scripts/d8_2_runtime_hardening_check.py
python scripts/dev_runtime_doctor.py
python scripts/d7_8_portal_live_integration_check.py
python scripts/d7_9_resource_center_check.py
python -m pytest -q
```

Then run frontend tests:

```powershell
cd ../frontend
npm run test -- --run
```
