# Release Candidate Audit — 2026-07-25

Branch: `feat/e2e-supplier-convergence`  
Base: `master@c2c2064`  
Stage: `READY_FOR_STAGING_HANDOFF` (**not** `STAGING_VALIDATED`)  
Auditor scope: PR-level release hardening — no new business features, no staging deployment.

## Commits on branch (pre-RC hardening)

| Hash | Summary | Scope |
|---|---|---|
| `6b2bec3` | Interval catalog pricing + PDF parity | Pricing validation, quote snapshot, PDF table parity, migration `0025_pricing_assumptions` |
| `3e0b98f` | Lifting project expectations + lead→quote bridge | Market intelligence API, Admin lead/quote bridge UI |
| `c237960` | Portal gate + customer site compat + static assets | **Mixed commit**: D7.7 field whitelist, `CUSTOMER_SITE_COMPAT_ENABLED`, imported customer-site HTML/static, Docker/PRD/docs — acceptable for RC; further split would require history rewrite |

RC hardening commits (this audit):

| Hash | Summary |
|---|---|
| `29b3487` | `fix(rc): demo order intake UX and portal field filter hardening` |
| `f151cb2` | `test(rc): release candidate contracts, smoke script, and audit record` |

## Security / artifact scan

| Check | Result |
|---|---|
| `frontend/public/static/documents/jobo-school-furniture-catalog.pdf` (~103 MB) in Git | **No** — listed in `.gitignore`, not tracked, not in history |
| Local-only PDF present on dev machine | Optional; reference-center degrades when HEAD 404 |
| `.env` / tokens in Git diff | **No** real secrets committed |
| Large build artifacts in branch diff | Static site assets under `frontend/public/site/` are intentional demo imports |

## Feature flags (production defaults)

| Flag | `config.py` default | Behavior when off |
|---|---|---|
| `PORTAL_CUSTOMER_API_ENABLED` | `false` | `/api/v1/portal/customer/*` → HTTP 503 |
| `PORTAL_CUSTOMER_API_REQUIRE_TOKEN` | `true` | Token required when portal enabled |
| `CUSTOMER_SITE_COMPAT_ENABLED` | `false` | `/api/site/*` routes **not mounted** (404) |
| `VITE_CUSTOMER_SITE_ENABLED` | unset / not `true` | Vite dev customer-site route fallback **disabled** |

Local `.env` may enable portal for D7.7 rehearsal; **schema defaults** remain off for production handoff.

## Known demo / staging boundaries

1. **`POST /api/site/customer/orders`** returns `order_created: false`, `status: draft_intake_not_persisted` — **non-persistent demo intake**. Customer-site UI labels success as **`[演示/意向提交]`**.
2. **JOOBOO Education Furniture** product group is `is_pending: true` until catalog approval; group listing shows zero available SKUs.
3. **JOOBOO school catalog PDF** is not bundled in Git; download link shows “Local copy unavailable” when file missing.
4. **Market lifting project expectations** are read-only analysis with `single_feedback_is_not_conclusion: true` — not operational conclusions.
5. **No real staging smoke evidence** in this PR.

## Migration

Expected Alembic head: **`0025_pricing_assumptions`**

```powershell
cd backend
alembic upgrade head
alembic current
```

## Verification commands (clean-environment protocol)

Run from a fresh worktree or clone; do **not** rely on untracked local PDFs or uncommitted WIP.

### Backend

```powershell
cd backend
pip install -r requirements.txt
alembic upgrade head
python -m pytest -q
python scripts/release_candidate_check.py
```

With backend listening on **8014** (`BACKEND_BASE_URL=http://127.0.0.1:8014`):

```powershell
python scripts/d6_4_quote_pdf_export_check.py
python scripts/hosun_catalog_governance_check.py
python scripts/d7_7_portal_bridge_check.py
python scripts/d8_0_staging_build_readiness_check.py
python scripts/e2e_supplier_convergence_check.py
```

### Frontend

```powershell
cd frontend
npm ci
npm test
npm run build
```

## Results (2026-07-25 local RC run)

| Command | Exit | Result |
|---|---|---|
| `pytest -q` (backend) | 0 | **801 passed**, 1 skipped |
| `npm test` (frontend) | 0 | **148 passed** |
| `npm run build` (frontend) | 0 | PASS (vue-tsc + vite build) |
| `release_candidate_check.py` | 0 | PASS |
| `d6_4_quote_pdf_export_check.py` | 0 | PASS |
| `hosun_catalog_governance_check.py` | 0 | PASS |
| `d7_7_portal_bridge_check.py` | 0 | PASS |
| `d8_0_staging_build_readiness_check.py` | 0 | PASS |
| `e2e_supplier_convergence_check.py` | 0 | PASS |
| `test_release_candidate_contracts.py` | 0 | **15 passed** |

## Contract tests added

`backend/tests/test_release_candidate_contracts.py` covers:

- Feature-flag matrix (portal on/off × site compat on/off)
- Site order POST stub contract
- Portal token negative paths
- Product bridge margin/pricing stripping
- Field filter: supplier notes, margin keys, internal attachment paths, fit/risk
- JOOBOO pending group vs HOSUN groups
- Lifting expectations demo boundary
- PDF interval table ↔ pricing validator parity

## Module diff review (master…HEAD)

| Module | Purpose | Risk | Tests | Keep? |
|---|---|---|---|---|
| Pricing + migration 0025 | Interval pricing assumptions persistence | Medium | PDF parity, pricing tests | Yes |
| `customer_site_compat.py` | Legacy `/api/site/*` | Medium — gated | RC contracts + e2e | Yes |
| `customer_field_filter.py` | Portal whitelist | High — security | portal bridge + RC | Yes |
| `frontend/public/site/*` | Imported customer portal | Medium — demo | site:check | Yes |
| `site-order-intake.js` | Demo order messaging | Low | RC contracts | Yes |
| `vite.config.ts` | Customer-site Vite gate | Medium | build | Yes |
| Docker/PRD in `c237960` | Local-server handoff | Low | d8_0 | Yes — mixed commit noted |

## Rollback

1. Revert merge on `master` or reset branch to `c2c2064`.
2. Alembic: review before `alembic downgrade -1` from `0025_pricing_assumptions`.
3. Set `CUSTOMER_SITE_COMPAT_ENABLED=false`, `PORTAL_CUSTOMER_API_ENABLED=false`; unset `VITE_CUSTOMER_SITE_ENABLED`.

## Residual risks

| Risk | Mitigation |
|---|---|
| Real staging not validated | Status stays `READY_FOR_STAGING_HANDOFF` |
| Site order intake is stub | UI + API labeled demo |
| JOOBOO SKUs pending | `is_pending` on Education group |
| `c237960` mixed scope | Documented; no history rewrite |

## PR readiness

**PR_READY: yes** — pending post-push clean worktree confirmation.

Draft PR target: `master`
