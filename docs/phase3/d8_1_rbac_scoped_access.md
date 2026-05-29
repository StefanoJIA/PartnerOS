# D8.1 RBAC and Scoped Access

**Status:** implemented on 2026-05-29.

## Goal

D8.1 adds a lightweight internal permission layer so authenticated users no longer have one broad internal access shape. It prepares PartnerOS for staging and portal integration hardening without changing the customer portal API contract.

## Permission Model

Roles can define explicit JSON permissions in `roles.permissions`. If a role does not define them, the backend falls back to built-in presets:

| Role | Scope |
|---|---|
| Admin | `*` |
| Operations / Operator / Supplier Manager / Sales | order write, resource write, feedback write, portal readiness, system readiness |
| Viewer | order read, resource read, feedback read, portal readiness, system readiness |

The seed script now fills missing role permissions for existing demo roles. Test-only users without a role relationship continue to behave like operators so older smoke scripts do not need fixture churn.

## Guarded APIs

| API | Permission |
|---|---|
| `GET /api/v1/orders*` read routes | `orders:read` |
| `POST/PATCH /api/v1/orders*` operational routes | `orders:write` |
| `GET /api/v1/orders/{id}/resources` | `resources:read` |
| `POST/PATCH /api/v1/orders/{id}/resources*` | `resources:write` |
| `GET /api/v1/feedback-tickets*` | `feedback:read` |
| `PATCH /api/v1/feedback-tickets/{id}` | `feedback:write` |
| `GET /api/v1/portal/customer/readiness` | `portal:readiness` |

`/api/auth/me` now returns `role_name` and `permissions` so the frontend can hide unavailable controls in D8.1+ UI work.

## Portal Boundary

Customer portal data routes still use the D7.7 portal token dependency. D8.1 does not add internal user auth to customer-facing bridge reads, and it does not broaden any portal-visible fields.

## Safety Rules

- No new public customer route beyond the existing portal bridge.
- No internal cost, margin, storage path, backend path, or token exposure.
- No automatic customer notification, supplier notification, email, webhook, shipment, delivery, or order status mutation.

## Verification

```powershell
cd backend
python scripts/d8_1_rbac_scoped_access_check.py
python -m pytest backend/tests/test_rbac_permissions.py -q
python -m pytest -q
```
