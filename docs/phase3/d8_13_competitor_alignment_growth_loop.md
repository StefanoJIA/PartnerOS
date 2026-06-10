# D8.13 Competitor Alignment Growth Loop MVP

Status: READY_FOR_STAGING_HANDOFF

## Objective

D8.13 adapts CRM and campaign-management strengths into PartnerOS without copying or integrating external tools. The MVP creates a Chinese-first growth operations loop:

`campaign planning -> customer segment -> manual outreach -> quote attribution -> order attribution -> feedback / shipment / market response loop`

## Implementation

- Backend aggregation: `GET /api/v1/growth/operations-console`
- Frontend route: `/growth-operations`
- Navigation: second-level item under `客户开发`, keeping the primary navigation at 8 groups.
- Data sources: existing Company, Contact, Lead, Quote, CustomerOrder, FeedbackTicket, ShipmentPlan, and MarketIntelligenceItem records.
- Manual action recording: the page records selected manual outreach events through the existing Lead touchpoint API.

## Campaign Planning

The MVP includes three equal partner directions:

- HOSUN lifting systems: lifting systems, desk frames, desk legs, lifting columns, heavy-duty lifting.
- JOOBOO education/project furniture: education furniture, classroom furniture, project furniture.
- Future Partner project supply: multi-brand catalog, project supply, custom furniture, dealer program.

Each campaign exposes:

- partner focus
- product focus
- target segment
- goal
- status
- next action
- linked operational entry points

## Customer Segments

Segments are lightweight and computed from current company/contact/lead data. They are not a new source of truth and do not require a migration. Each segment shows company count, lead count, contact count, campaign ids, source, and recommended use.

## Manual Outreach Sequence

Each campaign returns Chinese and English draft copy, a follow-up task suggestion, and manual event options:

- manually sent
- replied
- interested
- quote requested

The system records only operator-confirmed manual actions. It does not send email, SMS, LinkedIn, webhook, or portal notifications.

## Attribution And Feedback Loop

Campaign attribution is computed from product/partner keyword matches against quote lines and order lines. This supports internal review only; it does not change quote/order status.

Feedback loop rows connect campaign focus to:

- feedback ticket count
- shipment risk count
- market signal count
- recommended review action

This closes the growth loop by feeding service and delivery signals back into segment targeting and campaign review.

## Safety Boundary

D8.13 keeps the repository in `READY_FOR_STAGING_HANDOFF`.

The growth operations page and API do not:

- connect Tencent SalesEasy
- connect Constant Contact
- auto-send email, SMS, LinkedIn, or webhook
- notify customers or suppliers
- change quote status
- change order status
- mark staging as validated
- enter D9
- create proof records

## Verification

Run:

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
python scripts/d8_13_growth_loop_alignment_check.py

cd ../frontend
npm run test -- --run
npm run build
```
