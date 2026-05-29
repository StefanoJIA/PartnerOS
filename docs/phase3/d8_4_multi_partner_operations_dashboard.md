# D8.4 Multi-Partner Operations Dashboard

**Status:** implemented on 2026-05-29.

## Goal

D8.4 turns partner execution data into a read-only operating view across HOSUN, JOOBOO, and future manufacturing partners without hard-coded brand preference.

## Backend

| API | Purpose |
|---|---|
| `GET /api/v1/operations/partner-dashboard` | Aggregates partner splits, supplier confirmation status, production milestone status, shipment status, and risk flags |

The dashboard uses existing D7 data:

- `order_partner_splits`
- `supplier_confirmations` through split status fields
- `order_production_milestones`
- `shipment_plans`
- `manufacturing_partners`

## Frontend

Operator view:

```text
/partner-operations
```

The page shows summary metrics and per-partner workload, supplier confirmation coverage, production delay/block counts, shipment counts, next expected ready date, and risk flags.

## Safety

The dashboard is read-only:

- no supplier notification
- no customer notification
- no shipment creation
- no order status mutation
- no automatic sending
- no partner preference hard-coding

## Verification

```powershell
cd backend
python scripts/d8_4_partner_operations_check.py
python -m pytest backend/tests/test_partner_operations_dashboard.py -q

cd ../frontend
npm run test -- --run
```
