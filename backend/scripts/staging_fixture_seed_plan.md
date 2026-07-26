# Staging Fixture Seed Plan (Agent C)

**Status:** READY_FOR_STAGING_HANDOFF  
**External staging state:** WAITING_FOR_REAL_STAGING_EVIDENCE  
**Base commit reference:** `04ebcb5` (`feat/e2e-supplier-convergence`)  
**Safety:** synthetic data only — no real customer PII, no real tokens, no production records.

## Purpose

Minimal staging-safe fixture set so `d8_3_service_portal_staging_check.py` and `d8_strict_staging_evidence_check.py` can exercise the full portal bridge contract after operators deploy with private credentials.

This plan does **not** approve real staging UAT. Business owner sign-off remains pending per `docs/phase3/d8_26_staging_seed_selection_checklist.md`.

## Fixture Checklist

### Customers (2 synthetic companies)

| Marker | Company Name | Contact | Email | Segment | Partner focus |
|---|---|---|---|---|---|
| `STG-CUST-ALPHA` | Staging Test Alpha Corp | Alex Staging | `staging-alpha@example.com` | Distributor / project buyer | HOSUN lifting systems |
| `STG-CUST-BETA` | Staging Test Beta LLC | Bailey Staging | `staging-beta@example.com` | School / institution buyer | JOOBOO education furniture |

Rules:

- Names must include `Staging Test` so operators can distinguish from real customers.
- Use `@example.com` only — never real customer domains.
- No real addresses, PO numbers, contracts, or phone numbers.

### Products (minimum 2 active catalog rows)

| Marker | Partner | Product family | Customer-visible name | Status |
|---|---|---|---|---|
| `STG-PROD-HOSUN-001` | HOSUN | lifting systems | STAGING TEST Dual Motor Desk Frame | active |
| `STG-PROD-JOOBOO-001` | JOOBOO | education furniture | STAGING TEST School Desk Set | active |

Required for: `GET /api/v1/portal/customer/products`

### Orders (minimum 2, different companies)

| Marker | Order number | Company | Partner | Status | Coverage goal |
|---|---|---|---|---|---|
| `STG-ORD-ALPHA-001` | `ORD-STG-ALPHA-001` | Staging Test Alpha Corp | HOSUN | in_production | production + shipment + resources |
| `STG-ORD-BETA-001` | `ORD-STG-BETA-001` | Staging Test Beta LLC | JOOBOO | shipped | shipment + resources + feedback history |

Each order needs:

- ≥1 customer-visible line item linked to a staging product
- customer-safe notes only (no internal cost, margin, supplier notes)

### Production milestones (Alpha order)

| Sequence | Milestone | Status | Customer-safe label |
|---|---|---|---|
| 1 | materials_confirmed | completed | Materials confirmed (planned) |
| 2 | production_started | in_progress | Production started (planned) |
| 3 | quality_check | pending | Quality check (planned) |

Required for: `GET /api/v1/portal/customer/orders/{id}/production`

Wording must use planned / 预计 semantics — not delivery guarantees.

### Shipment (both orders)

| Order | Plan status | Customer-safe summary |
|---|---|---|
| Alpha | planned | Ocean freight planned — Yantian to LA (planned window) |
| Beta | in_transit | Shipment in transit — customer-safe tracking summary |

Required for: `GET /api/v1/portal/customer/orders/{id}/shipment`

No real carrier API calls. No real tracking numbers from production systems.

### Resources (one published resource per order)

| Marker | Order | Title | Category | Status | customer_visible |
|---|---|---|---|---|---|
| `STG-RES-ALPHA-001` | Alpha | STAGING TEST Installation Guide | installation_guide | published | true |
| `STG-RES-BETA-001` | Beta | STAGING TEST Product Spec Sheet | spec_sheet | published | true |

Required for:

- `GET /api/v1/portal/customer/orders/{id}/resources`
- Signed download via returned `download_url`

Files must be synthetic PDF placeholders stored through normal admin upload — no `backend/storage` paths or `storage_key` in portal responses.

### Feedback (optional write test)

Use `D8_3_CREATE_TEST_FEEDBACK=true` only during controlled smoke:

```json
{
  "order_id": "<alpha-order-uuid>",
  "feedback_type": "tracking",
  "subject": "TEST D8.3 service portal staging feedback",
  "message": "TEST: D8.3 staging contract runner. No customer notification expected.",
  "priority": "normal",
  "customer_name": "TEST Service Portal",
  "customer_email": "portal-staging@example.com"
}
```

Expected: HTTP 201, `customer_notified=false`, `feedback_received=true`.

Do not seed real complaint content or real customer identity.

## Cross-Customer Isolation Test Cases

Portal bridge token is **service-level** (one token for `service.intelli-opus.com`). PartnerOS does not enforce per-customer token scoping. Isolation is a **consumer-side contract**.

| Case ID | Action | Expected | Owner |
|---|---|---|---|
| ISO-01 | `GET /orders` without `company_id` | Returns all non-cancelled orders (both Alpha and Beta visible) | Documented — consumer must filter |
| ISO-02 | `GET /orders?company_id={alpha_uuid}` | Returns only Alpha orders | PartnerOS filter works when param supplied |
| ISO-03 | `GET /orders?company_id={beta_uuid}` | Returns only Beta orders | PartnerOS filter works when param supplied |
| ISO-04 | `GET /orders/{beta_order_id}` with service token | HTTP 200 — order reachable by UUID | Consumer must not expose other customers' UUIDs |
| ISO-05 | `GET /orders/{random_uuid}/resources` | HTTP 404 when order does not exist | Verified in `test_portal_staging_security_contract.py` |
| ISO-06 | service.intelli-opus.com session for Alpha user | Must not render Beta order IDs in UI | Operator/UAT on portal side — out of repo scope |

Reference tests: `backend/tests/test_portal_staging_security_contract.py::test_cross_customer_order_access_is_not_scoped_by_portal_token`

## Operator Seed Sequence (after deploy)

1. Confirm staging DB migrated to target commit (`DEPLOYED_COMMIT_SHA`).
2. Create companies, contacts, products via admin UI or idempotent admin API — use markers above.
3. Create orders with line items; attach production milestones and shipment plans.
4. Publish one customer-visible resource per order with synthetic PDF.
5. Verify admin-side records show `Staging Test` markers before running portal smoke.
6. Run preflight, then D8.3 / strict evidence scripts with private env vars.

Local rehearsal may reuse `python -m app.scripts.seed_business_flow` for demo shape, but **real staging smoke must use the synthetic markers in this plan**, not Jefferson demo names.

## Environment Variables for Evidence Binding

| Variable | Required for strict evidence | Notes |
|---|---|---|
| `BACKEND_BASE_URL` | yes | HTTPS deployed backend |
| `SERVICE_PORTAL_PARTNEROS_TOKEN` | yes | ≥24 chars, non-default |
| `SERVICE_PORTAL_ORIGIN` | yes | `https://service.intelli-opus.com` |
| `DEPLOYED_COMMIT_SHA` | yes | Git SHA of deployed build — written into evidence JSON |
| `D8_3_CREATE_TEST_FEEDBACK` | optional | `true` only for controlled feedback smoke |

## Validation Commands

```powershell
cd backend
python -m pytest tests/test_portal_staging_security_contract.py tests/test_d8_strict_staging_evidence_check.py -q
python scripts/d8_staging_input_preflight_check.py
# After private values + seed data on staging:
python scripts/d8_3_service_portal_staging_check.py
$env:D8_3_CREATE_TEST_FEEDBACK="true"
python scripts/d8_3_service_portal_staging_check.py
python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md
```

## Boundary

- No real tokens in this document or in committed records.
- No STAGING_VALIDATED until real HTTPS evidence with `deployed_commit_sha` replaces rehearsal output.
- Pending fixture rows are not business-approved for customer-facing display without owner sign-off.
