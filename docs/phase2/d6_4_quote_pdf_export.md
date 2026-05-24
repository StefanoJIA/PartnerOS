# D6.4 Quote PDF Export

## Goal

基于 quote / quote_version 生成客户报价 PDF，但不自动发送、不转订单。

## Scope

- `quote_pdf_exports` metadata table
- ReportLab customer PDF generation
- PDF download API
- Quote detail PDF export UI

## Not in Scope

- automatic sending
- Outlook email
- order conversion
- production / shipment tracking
- e-signature
- customer portal acceptance

## PDF Layout

| Section | Content |
|---------|---------|
| Header | IntelliOpus Engineering / intelliOffice; address; quote number, date, valid until |
| Bill To / Ship To | Two-column customer addresses |
| Metadata | Payment terms, shipping terms, optional incoterm |
| Line items | #, partner (source), product, description, qty, unit price, total |
| Totals | Subtotal, discount, shipping, sample fee, tax, grand total |
| Terms | Payment, shipping, validity, notes |
| Footer | Subject to confirmation safety note |

Partner names may appear on line items only — not as the primary PDF brand.

## Storage

- Generated files: `backend/storage/quote_pdfs/` (or `LOCAL_STORAGE_PATH/quote_pdfs/`)
- PDF binaries are **not** stored in the database or git

## Safety

- `automatic_sending_enabled=false`
- `inventory_promised=false`
- `certification_promised=false`
- `lead_time_promised=false`
- `order_created=false`
- No internal cost / margin / pricing breakdown in customer PDF
- Export does **not** change quote status
- Export does **not** mark quote sent

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/quotes/{quote_id}/export-pdf` | Generate customer PDF |
| GET | `/api/v1/quotes/{quote_id}/pdf-exports` | List exports |
| GET | `/api/v1/quotes/{quote_id}/pdf-exports/{export_id}/download` | Download PDF file |

## Acceptance Criteria

- [x] Export PDF works from quote or version snapshot
- [x] Download works via export_id
- [x] Quote status unchanged after export
- [x] Safety flags false in API response
- [x] Backend + frontend tests pass
- [x] `d6_4_quote_pdf_export_check.py` PASS

## Smoke

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8013"
python scripts/d6_4_quote_pdf_export_check.py
```
