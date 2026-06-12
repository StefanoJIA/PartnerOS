# D8.21 Pre-Staging Readiness Drill

## Status

- Current state: READY_FOR_STAGING_HANDOFF
- External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE
- Scope: local pre-staging drill, Portal bridge dry-run, and handoff request preparation
- Boundary: no real staging validation, no D9 entry, no proof record expansion, no deployment

This drill confirms that the local PartnerOS demo and the D8.20 staging handoff contract remain aligned before requesting real staging credentials and partner rehearsal participation.

## Runtime Used

- Backend: `http://127.0.0.1:8014`
- Frontend: `http://127.0.0.1:5173`
- Frontend proxy: `VITE_API_PROXY_TARGET=http://127.0.0.1:8014`
- Login path: UI login with the local seeded demo account

## Browser Drill Path

The drill opens the following routes after UI login:

1. `/`
2. `/growth-operations`
3. `/quotes`
4. `/orders`
5. one Order Detail route
6. `/portal-operations`
7. `/feedback-tickets`
8. `/market-response`
9. `/partner-onboarding`
10. `/demo-walkthrough`
11. `/system-health`

## Expected Pass Criteria

Workbench:

- Workbench remains the daily entry point.
- Daily operating map is visible.
- Business development, delivery operations, and management decision paths remain visible.

Growth Operations / Campaign:

- Campaign / marketing activity remains explainable.
- HOSUN, JOOBOO, and future partner positioning remains peer-level.
- Manual Outreach creates drafts and manual tasks only.
- No automatic email, SMS, LinkedIn message, customer notification, supplier notification, or external CRM action is triggered.

Quotes and Orders:

- Quotes and orders remain operator-controlled.
- Portal reads and feedback submission do not automatically change quote or order status.
- Order Detail shows customer-visible summary, partner split, production, shipment, and feedback.

Portal Operations:

- Portal Operations explains that PartnerOS is the internal source of truth.
- `service.intelli-opus.com` remains the customer-facing Portal.
- Readiness remains handoff-only until real staging credentials exist.

Feedback:

- Feedback can be handled internally.
- Feedback does not auto-reply to customers.
- Feedback does not promise SLA or trigger customer notification.

Market Response:

- HOSUN lifting systems are explained with desk frames, desk legs, lifting columns, and heavy-duty supply.
- JOOBOO education furniture / project furniture remains visible.
- Market Response remains advisory and requires human review.

Partner Onboarding:

- HOSUN, JOOBOO, Chongqing Huiju, and future partners remain part of one multi-partner operating loop.
- Partner-specific readiness and next actions remain visible.

Demo Walkthrough:

- The 10-15 minute story remains present:
  customer development -> Campaign -> Manual Outreach -> Quote -> Order -> Production -> Shipment -> Customer Portal -> Feedback -> Market Response -> Partner Onboarding.

System Health:

- Local runtime health remains visible for operators.

## Portal Bridge Dry-Run

This drill does not use real staging credentials. It only verifies local contract behavior:

- Readiness must not claim real external staging validation.
- Disabled or missing token state must fail safely.
- Wrong token must be rejected.
- Correct local test token may be used only inside the dry-run script.
- Customer-safe payload examples are limited to:
  - products
  - orders
  - production milestones
  - shipment status
  - resources
  - feedback status
  - customer-safe market signal preview
- Forbidden fields must be absent:
  - cost
  - margin
  - pricing breakdown
  - supplier private notes
  - backend file paths
  - storage keys
  - token values
  - internal-only comments
  - private partner notes
  - unsafe raw database IDs

## Pass Items

- Local backend and frontend can be started on the expected ports.
- The browser drill can log in through the UI.
- Core pages render without white screen.
- Required business markers are visible across Workbench, Growth Operations, Orders, Portal Operations, Feedback, Market Response, Partner Onboarding, Demo Walkthrough, and System Health.
- Portal dry-run confirms disabled/missing/wrong token safety behavior.
- Portal dry-run scans customer-facing payload examples for forbidden fields.
- No automatic external send behavior is enabled.
- No quote/order auto-status-change behavior is enabled.

## Fix Items

No D8.21 product fix is expected unless a page is blank, a route is broken, or the D8.17-D8.20 story contradicts the current UI.

## Deferred Issues

Still requires real external input:

- Backend HTTPS origin reachable by `service.intelli-opus.com`.
- Real `PORTAL_CUSTOMER_API_TOKEN`.
- Real `PORTAL_CUSTOMER_ALLOWED_ORIGINS`.
- Real `PUBLIC_BASE_URL`.
- Real Portal origin confirmation.
- Business owner approval of customer-visible fields and UAT records.
- Security review of token, CORS, logs, secret exposure, and forbidden-field controls.

## Decision Boundary

If the local drill passes, D8.21 is ready to request real staging credentials and schedule partner rehearsal. It still must remain READY_FOR_STAGING_HANDOFF until real external staging evidence exists.
