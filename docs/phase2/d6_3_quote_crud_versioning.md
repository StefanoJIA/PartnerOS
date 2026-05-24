# D6.3 Quote CRUD & Versioning

## Goal

建立正式 Customer Quote record、line items、adjustments、totals、versions，但不做 PDF 和 Order。

## Scope

- `quotes`, `quote_line_items`, `quote_adjustments`, `quote_versions`, `quote_terms`
- Quote number generation (`Q-YYYY-0001`)
- Create from catalog pricing / manual lines / Quote Input Contract
- Quote totals recalculation
- Status: internal_review → ready_to_send → sent
- Manual mark-sent (records only — no auto-send)
- Version v1 auto-created; manual revised versions
- UI: `/quotes`, `/quotes/new`, `/quotes/:id`

## Not in Scope

- PDF export
- Automatic sending / email / Outlook / LinkedIn
- Order conversion
- Production / Shipment
- Customer approval / payment

## Safety

- `automatic_sending_enabled: false` on all quote responses
- No inventory / certification / lead-time promises
- Pricing from catalog / pricing service / manual input only
- Manual price requires review flag

## API (v1)

| Method | Path |
|---|---|
| POST | `/api/v1/quotes` |
| POST | `/api/v1/quotes/from-contract` |
| GET | `/api/v1/quotes` |
| GET | `/api/v1/quotes/{id}` |
| PATCH | `/api/v1/quotes/{id}` |
| POST | `/api/v1/quotes/{id}/line-items` |
| POST | `/api/v1/quotes/{id}/adjustments` |
| GET/POST | `/api/v1/quotes/{id}/versions` |
| POST | `/api/v1/quotes/{id}/mark-ready` |
| POST | `/api/v1/quotes/{id}/mark-sent` |
| POST | `/api/v1/quotes/{id}/mark-expired` |

## Acceptance Criteria

- Quote created with priced line item
- Totals calculate correctly
- Version v1 created
- mark-sent records manual action only
- `d6_3_quote_crud_check.py` PASS
- pytest + frontend vitest pass
