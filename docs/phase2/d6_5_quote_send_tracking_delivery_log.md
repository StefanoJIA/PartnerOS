# D6.5 Quote Send Tracking & Delivery Log

## Goal

记录报价 PDF 被人工发送的事实，但不自动发送。

## Scope

- `quote_delivery_logs` audit table
- Enhanced `POST /api/v1/quotes/{id}/mark-sent`
- Delivery history list
- Quote timeline
- Follow-up date on quote

## Not in Scope

- automatic email / LinkedIn
- Outlook integration
- order conversion
- customer acceptance / e-signature
- payment / production / shipment

## Safety

- `automatic_sending_enabled=false`
- `email_sent_by_system=false`
- `linkedin_sent_by_system=false`
- `attachment_sent_by_system=false`
- `order_created=false`
- Mark sent only records manual external delivery

## Workflow

1. Create quote → mark ready → export PDF
2. Send manually outside intelliOffice
3. Return to quote detail → Mark as Sent
4. Record channel, recipient, PDF export, version, follow-up
5. Review delivery log and timeline

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/quotes/{id}/mark-sent` | Record manual delivery (enhanced) |
| GET | `/api/v1/quotes/{id}/delivery-logs` | Delivery history |
| GET | `/api/v1/quotes/{id}/timeline` | Quote timeline |
| GET | `/api/v1/quotes/delivery-due` | Follow-up due queue |

## Acceptance Criteria

- [x] Delivery log created on mark-sent
- [x] Quote status → sent (first send); append log if already sent
- [x] Timeline includes PDF export and manual sent
- [x] No automatic sending
- [x] Tests pass

## Smoke

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8013"
python scripts/d6_5_quote_send_tracking_check.py
```
