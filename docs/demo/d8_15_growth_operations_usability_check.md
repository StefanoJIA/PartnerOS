# D8.15 Growth Operations Usability Check

## Status

- Current state: READY_FOR_STAGING_HANDOFF
- External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE
- D9 state: not entered
- Proof records: not expanded

This pass is a small usability polish for Chinese business users. It does not add external integrations, does not auto-send outreach, does not modify quote/order status, and does not claim real staging validation.

## Local Runtime Requirement

For local demo and login, keep the backend on 8014 and start the frontend with the backend proxy target:

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"

cd ../frontend
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"
npm run dev -- --host 127.0.0.1 --port 5173
```

If `VITE_API_PROXY_TARGET=http://127.0.0.1:8014` is missing, the login page can render but login and API calls can fail because the frontend dev proxy is not pointing at the local backend.

## Acceptance Scope

Checked user-visible polish for:

- Login page: Chinese labels for email, password, login action, seeded local account, and local proxy hint.
- Growth Operations: Campaign / 营销活动 terminology, Chinese save/read/status messages, empty states, and table labels.
- Operation order: 规划活动 → 选择分群 → 创建外联任务 → 更新状态 → 查看报价/订单/反馈/市场响应.
- Multi-partner positioning: HOSUN and JOOBOO remain equal partner directions; HOSUN is not presented as the only brand.
- Safety boundary: manual outreach drafts and task statuses are recorded, but PartnerOS does not send email, SMS, LinkedIn messages, webhooks, customer notifications, or supplier notifications.

## Manual Browser Walkthrough

Use UI login at `http://127.0.0.1:5173/login`, then check:

- `/growth-operations`
- `/market-response`
- `/orders`
- `/feedback-tickets`
- `/partner-onboarding`
- `/demo-walkthrough`

Expected result:

- Pages do not white-screen.
- Main labels and guidance are Chinese-first.
- Campaign / 营销活动 is explained.
- HOSUN lifting systems and JOOBOO education furniture remain peer demo directions.
- Growth Operations keeps the business order visible from planning to attribution.
- Customer-facing bridge safety remains intact and staging is still READY_FOR_STAGING_HANDOFF.

## Deferred Items

No new large module or external integration is included in D8.15. Real service portal staging still needs real HTTPS origin, private portal token, allowed origins, and public base URL before any real staging validation claim.
