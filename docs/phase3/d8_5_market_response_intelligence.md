# D8.5 Market Response Intelligence

**Status:** implemented on 2026-05-29.

## Goal

D8.5 closes the loop from portal feedback, quote outcomes, order conversion, product parameters, and market notes back into product fit, quote prep, partner selection, and outreach planning.

## Backend

| API | Purpose |
|---|---|
| `GET /api/v1/market/response-intelligence` | Read-only market response board with feedback tags, win-loss signals, demand rows, product gaps, and advisory recommendations |

The route requires `market:read`. It accepts optional `related_company_id=<uuid>` so operators can review the same feedback, quote, order, and market-note signals for one customer account without mixing in other brands.

The service aggregates existing records only:

- `feedback_tickets`
- `quotes`
- `quote_line_items`
- `customer_orders`
- `order_line_items`
- `market_intelligence_items`
- `products`

No migration is required for the D8.5 foundation because the first version derives intelligence from existing source-of-truth tables.

The demand board labels priority focus categories for the intelliOffice market loop:

- adjustable desk frames
- desk legs
- lifting columns
- education furniture
- project furniture

## Frontend

Operator view:

```text
/market-intelligence
```

The page now shows:

- feedback tag extraction and summaries
- quote / order win-loss by category
- demand signal board with adjustable-frame focus detection
- focus category counts and company-filter status
- product parameter gaps
- AI-assisted recommendations that remain advisory
- the existing market intelligence item list

## Safety

D8.5 is advisory and auditable:

- no AI execution
- no customer notification
- no supplier notification
- no email or webhook
- no quote status mutation
- no order status mutation
- no partner selection mutation
- all recommendations require human review

## Verification

```powershell
cd backend
python scripts/d8_5_market_response_check.py
python -m pytest tests/test_market_response_intelligence.py -q

cd ../frontend
npm run test -- --run
```
