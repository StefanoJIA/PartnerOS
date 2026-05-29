# D7.6 Shipment Tracking Foundation

**Status:** Implemented - **Date:** 2026-05-29 - **Migration:** `0014_shipment_plans`

## Goal

Allow Operators to manually maintain shipment plans for customer-confirmed orders, while preparing real shipment data for the D7.7 customer portal read API.

## Scope

- `shipment_plans`
- `shipment_tracking_events` foundation table
- create shipment plan
- list shipment plans
- patch shipment plan fields/status
- cancel by patching `status=cancelled`
- order timeline shipment events
- order detail Shipment Plans UI
- D7.7-ready `PortalShipmentSummary` schema and `portal_visible_fields` response field

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/orders/{id}/shipment-plans` | Create a manual shipment plan |
| GET | `/api/v1/orders/{id}/shipment-plans` | List shipment plans |
| PATCH | `/api/v1/orders/{id}/shipment-plans/{plan_id}` | Update fields or status |

POST is allowed only after customer confirmation (`confirmed` or later order lifecycle states). Pending and cancelled orders are blocked.

## Timeline Events

- `shipment_plan_created`
- `shipment_plan_updated`
- `shipment_status_changed`

## Safety

- no automatic shipment booking
- no carrier API calls
- no webhook
- no email
- no supplier or customer notification
- no automatic `order.status` change to `shipped` or `delivered`

All shipment plan responses include:

```json
{
  "safety": {
    "shipment_created": false,
    "supplier_notified": false,
    "customer_notified": false
  }
}
```

## Portal Preparation

D7.6 does not add `/portal/customer/*` routes. It only stores and exposes customer-visible shipment fields so D7.7 can implement a strict read-only portal DTO:

- status
- shipment method
- estimated ship date
- estimated arrival date
- tracking number

## Smoke

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
python scripts/d7_6_shipment_tracking_check.py
```
