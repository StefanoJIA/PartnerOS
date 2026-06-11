# D8.17 Full-Chain Manual Acceptance

## Status

- Current state: READY_FOR_STAGING_HANDOFF
- External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE
- D9: not entered
- Proof records: not expanded
- External automation: not connected

D8.17 is a manual business acceptance pass. It verifies the existing PartnerOS flow in a real local browser and does not add a large module, does not connect Constant Contact or sales CRM APIs, does not auto-send email/SMS/LinkedIn/customer notifications, and does not deploy or modify `service.intelli-opus.com`.

## Runtime Used

- Backend: `http://127.0.0.1:8014`
- Frontend: `http://127.0.0.1:5173`
- Frontend proxy: `VITE_API_PROXY_TARGET=http://127.0.0.1:8014`
- Login: local seeded admin user through the UI

## Browser Acceptance Path

### 1. Workbench

Opened `/` after UI login.

Passed:

- “每日操作地图” is visible.
- Three views are visible: 业务开发, 运营交付, 管理决策.
- Daily entry cards link to 客户开发, Growth Operations, Quotes, Orders, Feedback Tickets, Market Response, Partner Onboarding, and Demo Walkthrough.
- The workbench can serve as the daily starting point.

### 2. Customer Development

Opened:

- `/companies`
- `/contacts`
- `/lead-intelligence`

Passed:

- Pages render without white screen.
- Chinese operating labels are usable.
- Lead Intelligence provides partner/product fit context for customer development.

### 3. Growth Operations / Campaign

Opened `/growth-operations`.

Passed:

- HOSUN and JOOBOO are shown as peer partner directions.
- The page explains Campaign / 营销活动.
- The page clearly states it does not auto-send email, SMS, LinkedIn, customer notifications, or external CRM messages.
- Created and saved:
  - `TEST D8.17 HOSUN Campaign`
  - `TEST D8.17 JOOBOO Campaign`
- Saved campaigns reappeared in the workspace and displayed target segment, product focus, next action, quote/order/feedback/shipment/market signal aggregation.

### 4. Manual Outreach

Created a manual outreach task under the D8.17 JOOBOO campaign.

Passed:

- Chinese draft was generated in the manual task table.
- The page also exposes the Chinese / English outreach draft area in the manual sequence section.
- Status was updated through the UI from 待人工执行 to 有兴趣 and then 已请求报价.
- The page continued to state that PartnerOS does not send messages automatically.

### 5. Quote / Order / Production / Shipment

Opened:

- `/quotes`
- `/orders`
- Order detail for `O-D83-DEMO-001`

Passed:

- Quotes list shows manual quote safety boundary.
- Orders list shows order safety boundary.
- Order detail shows:
  - customer-visible summary
  - partner split / supplier confirmation
  - production summary and milestones
  - shipment plans
  - feedback summary
  - Portal-safe metadata
- The order detail does not auto-start production, notify suppliers, create shipments, or change order status.

### 6. Feedback

Opened `/feedback-tickets`, then opened `FB-2026-0123`.

Passed:

- Feedback list and detail render correctly.
- Status, priority, owner, and response summary controls are visible.
- Saved internal owner and handling summary.
- Marked the ticket resolved, then closed.
- The page continued to state that feedback handling is internal and will not notify customers or promise SLA.

### 7. Market Response

Opened `/market-response`.

Passed:

- Market Response explains signals from orders, logistics, production friction, customer feedback, and watchlist/product gaps.
- HOSUN focus terms are visible: lifting systems, desk frames, desk legs, lifting columns, heavy-duty supply.
- JOOBOO focus terms are visible: education furniture, project furniture.
- The page explains that all recommendations require human review and do not modify quote/order/partner selection.

### 8. Partner Onboarding

Opened `/partner-onboarding`.

Passed:

- HOSUN, JOOBOO, and future partner framing is peer-level.
- Readiness checklist and next action are visible.
- The page remains in READY_FOR_STAGING_HANDOFF and does not enter D9.

### 9. Demo Walkthrough

Opened `/demo-walkthrough`.

Passed:

- The demo can support a 10-15 minute story:
  客户开发 → Campaign / 营销活动 → 人工外联 → 报价 → 订单 → 生产 → 物流 → Portal → Feedback → Market Response → Partner 接入.
- HOSUN lifting systems and JOOBOO education furniture narratives are visible.
- Safety language remains clear: no customer/supplier notification, no webhook, no carrier API, no token/cost/margin/private-note exposure.

## Fixes Made During Acceptance

- Market Response now explicitly explains HOSUN lifting systems, desk frames, desk legs, lifting columns, heavy-duty supply, and JOOBOO education/project furniture.
- Demo Walkthrough now explicitly includes Campaign / 营销活动 and manual outreach in the business story.

## Deferred Issues

No blocking issue found. Remaining production/staging work still requires real service portal credentials and origin configuration before real staging validation can be claimed.

## Acceptance Decision

D8.17 full-chain manual acceptance is ready for partner-facing business rehearsal while the system remains READY_FOR_STAGING_HANDOFF.
