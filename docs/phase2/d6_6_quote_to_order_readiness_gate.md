# D6.6 Quote-to-Order Readiness Gate

## Goal

判断 sent quote 是否具备进入人工转订单审查的条件，但不创建 Order。

## Scope

- Derived order readiness service (no new tables)
- Readiness checklist and scoring
- Future order input contract payload
- Quote detail UI section
- Order readiness board API
- Smoke check

## Not in Scope

- order table or order records
- order creation / convert-to-order
- production / shipment tracking
- payment processing
- customer acceptance portal

## Readiness Status

| Status | Meaning |
|--------|---------|
| `ready_for_order_review` | Reserved — all technical gates pass (rare in D6.6) |
| `needs_customer_confirmation` | Sent and complete; customer order acceptance not recorded (default) |
| `needs_internal_review` | Manual pricing, multi-partner, cost model, or review flags |
| `not_ready` | Not sent, expired, missing PDF, missing pricing, etc. |

## Safety

- `order_created=false`
- `production_started=false`
- `shipment_created=false`
- No automatic sending
- No inventory / certification / lead-time promises

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/quotes/{id}/order-readiness` | Full readiness for one quote |
| GET | `/api/v1/quotes/order-readiness-board` | Summary board for sent/ready quotes |

## Workflow

1. Create quote → export PDF → mark sent (D6.3–D6.5)
2. Open quote detail → **Order Readiness**
3. Review checklist, blocking/warning items, order input contract
4. Obtain customer confirmation outside intelliOffice
5. Future stage: manual order conversion (not D6.6)

## Acceptance Criteria

- [x] Readiness API works without creating orders
- [x] Quote detail shows readiness section
- [x] Safety flags false
- [x] Smoke passes

## Smoke

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8013"
python scripts/d6_6_quote_order_readiness_check.py
```
