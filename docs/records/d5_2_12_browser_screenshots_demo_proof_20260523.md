# D5.2.12 Browser Screenshots Archive & Demo Proof

**Date:** 2026-05-23 · **Release:** D5.2 Internal MVP · **Stage:** D5.2.12

## Goal

为 D5.2 Internal MVP 留下浏览器层面的可视化证明，供团队、客户或未来开发者查阅。

## Screenshot List

| Screenshot | Page | Purpose | Sensitive Info Masked | Status |
|---|---|---|---|---|
| `login_success.png` | `/login` → Dashboard | 成功进入系统，不显示密码 | N/A (no password in frame) | **Pending** — stored locally only / not committed |
| `lead_intelligence_daily_summary.png` | `/lead-intelligence` | Daily Summary cards | Emails in table if visible | **Pending** |
| `operation_filters.png` | `/lead-intelligence` | Operation + segment filters | Emails if visible | **Pending** |
| `manual_outreach_queue.png` | `/lead-intelligence` | Manual Outreach Queue 表格 | **Mask customer emails** | **Pending** |
| `outreach_draft_panel.png` | Lead detail → Generate Draft | Human-reviewed draft | No token in panel | **Pending** |
| `mark_as_sent_success.png` | After Mark as Sent | Touchpoint / next action 更新 | No secrets | **Pending** |
| `system_health_portal_readiness.png` | `/system-health` | Portal Readiness, auto-send disabled | No secrets | **Pending** |
| `portal_consumer_mock.png` | `/portal-consumer-mock` | External Portal mock | No email lists | **Pending** |
| `company_detail_enrichment.png` (optional) | Company detail | Enrichment evidence | Public URLs only | **Optional / Pending** |

> **Archive policy:** PNG files live under `docs/records/screenshots/20260523/` and are **gitignored**. Do **not** commit unmasked screenshots. This commit includes **markdown proof + capture script only**.

## How to Capture (when DB + backend are up)

```powershell
# Terminal 1 — backend (8000 or 8010)
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8010

# Terminal 2 — frontend
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8010"
cd frontend
npm run dev

# Terminal 3 — automated capture (optional; requires: pip install playwright && playwright install chromium)
$env:FRONTEND_BASE_URL="http://127.0.0.1:5174"
python backend/scripts/capture_demo_screenshots.py
```

**Manual capture:** Log in with seed admin → visit each page → screenshot → mask emails/tokens in image editor → save to `docs/records/screenshots/20260523/`.

**Automated run note (2026-05-23):** PostgreSQL/Docker was unavailable during agent capture (`database_status=unavailable`, login API 500). Re-run capture when `check_database_config.py` passes.

## Demo Narrative

This demo shows that intelliOffice can support a daily manual lead development workflow:

1. User logs in.
2. Reviews Daily Summary on `/lead-intelligence`.
3. Filters high-priority or follow-up leads (Today Focus, High Priority, Waiting Reply).
4. Generates a **human-reviewed draft** (no auto-send).
5. Copies and sends externally by hand (LinkedIn / email client).
6. Marks the message as sent in intelliOffice.
7. The system records touchpoint and next action.
8. Portal read-only status can be consumed by a future unified dashboard (`/portal-consumer-mock`).

## Safety Confirmation

- **No automatic sending**
- **No LinkedIn scraping**
- **No Outlook integration**
- **Human-reviewed drafts only**
- **Screenshots masked before sharing** (token, password, private emails)
- **PNG not committed** to git by default

## Current Release Links

- [D5.2 Internal MVP Release](../releases/d5_2_internal_mvp_release_20260523.md)
- [Operator Guide](../operator_guide.md)
- [Deployment Readiness Checklist](../deployment_readiness_checklist.md)
- [Screenshot README](screenshots/20260523/README.md)

## Verification (no logic changes)

```powershell
cd backend
python scripts/config_readiness_check.py
python scripts/portal_consumer_check.py
```

Release test baseline unchanged: **pytest 95 passed, 1 skipped** · **vitest 44 passed**.
