# D7.9 Resource Center / Document Center

**Status:** Implemented - **Date:** 2026-05-29 - **Migration:** `0017_order_resources`

## Goal

D7.9 completes the customer portal loop with customer-safe order resources. Operators can upload a file, classify it as an order resource, publish or unpublish it for the customer portal, and expose a short-lived signed download URL without leaking backend storage details.

PartnerOS remains the source of truth. `service.intelli-opus.com` remains customer-facing.

## Internal Operator API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/files/upload` | Existing internal authenticated upload |
| POST | `/api/v1/orders/{order_id}/resources` | Create an order resource from an uploaded file |
| GET | `/api/v1/orders/{order_id}/resources` | List internal resources for an order |
| PATCH | `/api/v1/orders/{order_id}/resources/{resource_id}` | Update metadata, publish, unpublish, archive |

Resource statuses:

```text
draft -> published -> archived
```

`customer_visible=true` and `status=published` are both required before a resource appears in the customer portal API.

## Customer Portal API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/portal/customer/orders/{order_id}/resources` | Customer-visible resource list |
| GET | `/api/v1/portal/customer/resources/{resource_id}/download?expires_at=...&token=...` | Signed resource download |

Portal list responses include safe metadata only:

- resource id
- order id
- file id
- title
- category
- description
- status
- customer_visible
- published_at
- filename
- mime
- size
- signed `download_url`
- download expiry
- safety flags

They never include `storage_key`, backend path, filesystem path, or token configuration.

## Frontend

Order detail now includes **Resource Center**:

- upload resource
- title/category/description form
- publish now checkbox
- resource list
- publish / unpublish / archive actions
- customer-visible preview
- safety note

## Safety Rules

D7.9 does not:

- email customers
- notify customers
- create public permanent URLs
- expose storage keys or backend paths
- promise file availability forever
- auto-publish files from quote/order/shipment actions

## Validation

```powershell
cd backend
alembic upgrade head
python scripts/d7_9_resource_center_check.py
python -m pytest tests/test_order_resources.py -q
```

Recommended regression:

```powershell
python scripts/d7_8_portal_live_integration_check.py
python scripts/d7_7_portal_bridge_check.py
python scripts/d7_6_shipment_tracking_check.py
python scripts/d7_5_production_milestone_check.py
python scripts/smoke_all_d5.py
python scripts/dev_runtime_doctor.py
python -m pytest -q
```
