# Local Pilot Validation — Customer Project Request Revenue Loop

**Date:** 2026-07-26  
**Branch:** `feat/pilot-ready-revenue-loop`  
**Status:** `LOCAL_PILOT_VALIDATED: YES`  
**Prior stage:** `PILOT_FEATURE_COMPLETE` → **Local pilot validated on clean PostgreSQL**

## Environment

| Component | Value |
|-----------|-------|
| PostgreSQL (primary) | `127.0.0.1:5435` — Docker `projectconnecting-db-1`, fresh volume |
| PostgreSQL (incremental) | `127.0.0.1:5436` — `partneros_incr`, upgrade path 0025→0026 |
| Backend | `http://127.0.0.1:8014` — `CUSTOMER_SITE_COMPAT_ENABLED=true` |
| Frontend | `http://127.0.0.1:5173` — `VITE_API_PROXY_TARGET=http://127.0.0.1:8014` |
| Alembic head | `0026_customer_project_requests` |

## Database migration evidence

### Fresh empty DB

```powershell
cd backend
$env:DATABASE_URL="postgresql+psycopg://partneros:partneros@127.0.0.1:5435/partneros"
alembic upgrade head
alembic current
# → 0026_customer_project_requests (head)
```

### Incremental path (0025 → 0026)

```powershell
$env:DATABASE_URL="postgresql+psycopg://partneros:partneros@127.0.0.1:5436/partneros_incr"
alembic upgrade 0025_pricing_assumptions
alembic current   # → 0025_pricing_assumptions
alembic upgrade head
alembic current   # → 0026_customer_project_requests (head)
```

### `customer_project_requests` schema (verified)

- **PK:** `id` (UUID)
- **Unique:** `request_reference`, `idempotency_key`
- **JSONB:** `requirements_json`, `attachment_refs`, `fit_summary_json`, `completeness_json`
- **Traceability FKs:** `company_id`, `contact_id`, `partner_id`, `product_catalog_id`, `lead_id`, `rfq_id`, `quote_id`
- **Timestamps:** `submitted_at`, `triaged_at`, `quote_ready_at`, `resolved_at`, `created_at`, `updated_at`
- **Indexes:** status, priority, source, company_id, partner_id, sku, owner_user_id (+ link indexes on lead/rfq/quote)

## Synthetic pilot data (no real PII)

| Field | Value |
|-------|-------|
| Customer | Demo Heavy-Duty Dealer (Synthetic) |
| Contact | Pilot Demo Buyer / `pilot.demo@example.com` |
| HOSUN SKU | `HS90602HRDDFZ` (300kg heavy-duty frame, post catalog sync) |
| JOOBOO SKU | `JB-DEMO-SCHOOL-DESK` (pending catalog → UNKNOWN fit) |
| Scenario | 300kg/660lb multi-leg low-noise project with custom mounting |

## End-to-end revenue loop (API)

Synthetic request reference from final E2E run: **`CPR-4502E2E1`**

| Step | Result |
|------|--------|
| 1. `POST /api/site/customer/orders` | `project_request_submitted`, `order_created=false` |
| 2. Admin `GET /api/project-requests` | Record visible |
| 3. Assign owner/priority/partner/SKU | Fit: overall **MATCH**, heavy_load **MATCH** |
| 4. `POST .../quote-input-contract` | QIC generated |
| 5. Status `triage` → `quote_ready` | Blocked without fit; illegal jumps return 400 |
| 6. `POST /api/v1/quotes` (manual interval table) | Quote created, PDF exported |
| 7. `POST .../promote-market-signal` | MR review queued |
| 8. `GET /api/dashboard/daily-decision-queue` | CPR item present |
| 9. Traceability | CPR → QIC → Quote → MR (IDs redacted in logs) |

### Linkage (redacted)

- Request reference: `CPR-4502E2E1`
- Request ID prefix: `9161713e…`
- Quote ID prefix: `1b44d654…`
- MR review ID prefix: `bc942bba…`

## Security / partner neutrality (verified)

- Unauthenticated admin project-requests → 401/403
- Idempotency key dedupe → same `request_reference`
- Illegal status jump `quote_ready` → `submitted` → 400
- JOOBOO pending SKU → `overall_status=UNKNOWN`, `partner_pending=true` (no HOSUN default)
- `CUSTOMER_SITE_COMPAT_ENABLED` default **off** in config schema
- Portal bridge negative tests pass via `d7_7_portal_bridge_check.py`

## Test commands & results

```powershell
# Backend
cd backend
$env:DATABASE_URL="postgresql+psycopg://partneros:partneros@127.0.0.1:5435/partneros"
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
python -m pytest -q -rs
# → 813 passed, 1 skipped

python scripts/pilot_revenue_loop_e2e_check.py
# → PASS 16/16

python scripts/release_candidate_check.py
# → PASS (migration head 0026, d6_4, hosun, d7_7, d8_0, e2e convergence)

# Frontend
cd ../frontend
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"
npm run test -- --run
# → 148 passed
npm run build
# → OK (vue-tsc + vite)
```

## Fixes applied in this validation

1. **`ProductCatalog.internal_sku`** lookup in site intake (was `.sku`)
2. **HOSUN `load_capacity` string** → `load_capacity_kg` in capability normalization
3. **Status transition guards** for CPR workflow + quote_ready prerequisites
4. **Manual interval quote** path when catalog lacks price tiers (QIC handoff)
5. **QIC → Quote deep link** via `?projectRequestId=` on quote creation page
6. **Migration head 0026** in release candidate / e2e convergence scripts
7. **Pilot E2E script** `backend/scripts/pilot_revenue_loop_e2e_check.py`
8. **Demo catalog seed** products for HOSUN/JOOBOO pilot SKUs

## Staging still missing

- Real staging credentials and `PORTAL_CUSTOMER_API_TOKEN`
- Strict staging smoke evidence (`STAGING_VALIDATED` not claimed)
- Production Go/No-Go human handoff for D9 operating loops

**Do not mark `STAGING_VALIDATED` until real staging credentials and business/security sign-off exist.**
