# Release Candidate Audit — 2026-07-25

Branch: `feat/e2e-supplier-convergence`  
**Baseline:** `master@c2c2064`  
**Audited commit range:** `6b2bec3..244d133` (inclusive of RC hardening commits on branch)  
Stage: `READY_FOR_STAGING_HANDOFF` (**not** `STAGING_VALIDATED`)  
Auditor scope: PR-level release hardening and reproducibility — no new business features.

> Document revision history is recorded in the PR merge timeline; this file intentionally does **not** embed its own final commit hash.

## Commits in audited range

| Hash | Summary | Scope |
|---|---|---|
| `6b2bec3` | Interval catalog pricing + PDF parity | Pricing validation, quote snapshot, PDF table parity, migration `0025_pricing_assumptions` |
| `3e0b98f` | Lifting project expectations + lead→quote bridge | Market intelligence API, Admin lead/quote bridge UI |
| `c237960` | Portal gate + customer site compat + static assets | **Mixed commit**: D7.7 field whitelist, `CUSTOMER_SITE_COMPAT_ENABLED`, imported customer-site HTML/static, Docker/PRD/docs |
| `29b3487` | Demo order intake UX + portal field filter hardening | Stub order UI, missing PDF degradation, internal field filter |
| `244d133` | RC contract tests + smoke script + initial audit record | `test_release_candidate_contracts.py`, `release_candidate_check.py` |

Subsequent `chore(rc)` commits (migration idempotency, audit correction) appear in the same PR branch after `244d133`.

## Authoritative test evidence (clean worktree)

Protocol: git worktree at branch HEAD, **no** `backend/.env`, only `DATABASE_URL=postgresql+psycopg://partneros:partneros@127.0.0.1:5435/partneros` for collection/import tests that require a configured URL.

| Command | Exit | Result |
|---|---|---|
| `pytest -q -rs` | 0 | **798 passed, 4 skipped** (802 collected) |
| `pytest --collect-only -q` | 0 | **802 tests** collected |
| `npm ci && npm test` | 0 | **148 passed** |
| `npm run build` | 0 | PASS |

### Why clean worktree differs from main workspace (801 passed / 1 skipped)

Both environments collect **802** tests. The delta is **optional local fixtures**, not code drift:

| Skipped test | Trigger | Clean worktree | Main workspace (typical) |
|---|---|---|---|
| `tests/test_business_flow_integration.py` (module) | `PARTNEROS_TEST_DATABASE_URL` unset | SKIPPED | Runs when dedicated test DB URL is set (+1 passed) |
| `tests/test_import_pricing_excel.py::test_import_dry_run_reads_sheets_and_candidates` | `local_data/报价模型与格式.xlsx` missing | SKIPPED | Runs when local Excel present (+1 passed) |
| `tests/test_import_pricing_excel.py::test_import_dry_run_nonzero_summary` | same + port 5435 reachable | SKIPPED | Runs when Excel + DB up (+1 passed) |
| `tests/test_pricing_excel_parser.py::test_real_workbook_nonzero_candidates` | local Excel missing | SKIPPED | Runs when Excel present (+1 passed) |

**Clean authoritative count:** 798 passed / 4 skipped.  
**Main workspace inflation (+3 passed, −3 skipped):** local Excel workbook and/or `PARTNEROS_TEST_DATABASE_URL` — must **not** be used as PR evidence.

PR and RC sign-off use the clean worktree numbers only.

## Empty-database migration evidence

Database: one-time empty PostgreSQL `partneros_rc_empty_20260726` on Docker host port **5435**.

```powershell
$env:DATABASE_URL="postgresql+psycopg://partneros:partneros@127.0.0.1:5435/partneros_rc_empty_20260726"
cd backend
alembic upgrade head
alembic current
```

| Step | Result |
|---|---|
| `alembic upgrade head` (empty DB) | **PASS** → `0025_pricing_assumptions` |
| `alembic current` | `0025_pricing_assumptions (head)` |

**Note:** `0001_initial` uses `Base.metadata.create_all`, so later migrations `0023`–`0025` require idempotent guards for empty-database bootstrap. Fixed in post-`244d133` `chore(rc)` commit (no new revision id).

## Staging status

| Check | Status |
|---|---|
| Strict staging env vars (`BACKEND_BASE_URL`, `SERVICE_PORTAL_PARTNEROS_TOKEN`, `SERVICE_PORTAL_ORIGIN`) | **MISSING** in process env and `backend/.env` |
| Real `service.intelli-opus.com` smoke | **BLOCKED** — see `docs/records/d8_strict_staging_evidence_20260726.json` |
| Project stage | **`READY_FOR_STAGING_HANDOFF`** (unchanged) |

## Feature flags (production defaults)

| Flag | Default | When off |
|---|---|---|
| `PORTAL_CUSTOMER_API_ENABLED` | `false` | `/api/v1/portal/customer/*` → 503 |
| `CUSTOMER_SITE_COMPAT_ENABLED` | `false` | `/api/site/*` not mounted |
| `VITE_CUSTOMER_SITE_ENABLED` | unset | Vite customer-site routes disabled |

## Demo / staging boundaries

1. `POST /api/site/customer/orders` → `draft_intake_not_persisted` (non-persistent demo).
2. JOOBOO Education group `is_pending: true`, 0 production-ready SKUs in compat API.
3. ~103 MB JOOBOO catalog PDF gitignored; UI degrades when absent.
4. No real staging evidence in this PR.

## PR readiness

**PR_READY: yes** for code review and local/RC gates.  
**STAGING_VALIDATED: no** — blocked on private staging credentials and deployed SHA verification.
