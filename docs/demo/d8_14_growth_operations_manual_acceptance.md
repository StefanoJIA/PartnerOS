# D8.14 Growth Operations Manual Acceptance

Status: READY_FOR_STAGING_HANDOFF

## Test Runtime

- Backend: `http://127.0.0.1:8014`
- Frontend: `http://127.0.0.1:5173`
- Browser: local Chrome headless with a real frontend session
- Login path: `/login` using the seeded local operator account
- Acceptance page: `/growth-operations`

This was a local manual acceptance rehearsal only. It is not staging validation and does not enter D9.

## Walkthrough Path

1. Opened `/login`.
2. Logged in through the UI.
3. Opened `/growth-operations`.
4. Reviewed the Campaign Workspace list and summary.
5. Applied and saved the HOSUN campaign template.
6. Applied and saved the JOOBOO campaign template.
7. Created a manual outreach task under the selected campaign.
8. Updated the task status to `interested`.
9. Reviewed campaign summary fields for quote, order, feedback, shipment risk, and market signal.
10. Opened core related pages:
    - `/market-response`
    - `/orders`
    - `/feedback-tickets`
    - `/partner-onboarding`
    - `/demo-walkthrough`

## Passed Items

- `/growth-operations` renders without blank screen or fatal console error.
- The page is usable in Chinese for a business operator.
- Campaign list displays saved campaigns.
- HOSUN and JOOBOO appear as equal partner scenarios.
- HOSUN campaign can cover lifting systems, desk frames, desk legs, lifting columns, and heavy-duty supply.
- JOOBOO campaign can cover education furniture and project furniture.
- Campaign fields show partner focus, product focus, target segment, status, goal, and next action.
- Campaign save persists and can be read back from the API.
- Manual outreach task can be created.
- Manual task status can be updated through the same authenticated browser session.
- The generated draft is explicit that PartnerOS does not automatically send email, SMS, or customer notifications.
- Campaign detail summary exposes quote count, order count, feedback count, shipment risk count, and market signal count.
- Safety flags remain false for email, SMS, LinkedIn, customer notification, supplier notification, quote status change, and order status change.
- Market Response, Orders, Feedback Tickets, Partner Onboarding, and Demo Walkthrough still render after D8.14.

## Fixes Made During Acceptance

- Localized visible Growth Operations copy:
  - `Campaign Planning` -> `Campaign 规划视图`
  - `English Draft` -> `英文草稿`
  - `Campaign → Quote → Order 归因` -> `Campaign 到报价和订单的归因`
  - Partner placeholder now explains `Partner 方向，例如 HOSUN / JOOBOO`
  - Campaign planning helper text now explains Partner direction, product direction, target segment, business goal, status, and next manual action in Chinese.
- Updated the D8.13 check marker to match the localized attribution heading.

## Deferred Issues

- The login page still shows `Email`, `Password`, and `Sign in`. This does not block Growth Operations acceptance, but it should be part of a future Chinese operating language pass.
- The Campaign Workspace still uses the business term `Campaign`. This is intentional for now because the project documentation and API use campaign language, but the page pairs it with Chinese explanations.
- The local 5173 dev server must be started with `VITE_API_PROXY_TARGET=http://127.0.0.1:8014`; otherwise the browser can reach the page shell but API login fails.

## Business Assessment

For a business development user, the workspace is usable for the intended manual loop:

`campaign planning -> manual outreach task -> quote/order attribution -> feedback/shipment risk review -> market response decision`.

For an operations user, the workspace is usable to judge whether a partner/product focus should continue:

- customer reaction is represented by task status and feedback;
- quote and order activity are visible as read-only counts;
- shipment risk and market signals are visible;
- no automatic external communication occurs.

## Boundary

- Remains `READY_FOR_STAGING_HANDOFF`.
- Does not enter D9.
- Does not add proof records.
- Does not write `STAGING_VALIDATED`; the external staging boundary remains `WAITING_FOR_REAL_STAGING_EVIDENCE`.
- Does not connect Constant Contact, Sales Yi, carrier APIs, email, SMS, LinkedIn, or customer notification channels.
