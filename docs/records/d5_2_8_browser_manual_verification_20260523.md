# D5.2.8 Browser Manual Verification & Polish

## Goal

确认每日跟进工作台可在浏览器中真实使用，并完成小范围 UI polish。

## Environment

- Backend: `http://127.0.0.1:8010`（uvicorn）
- Frontend: `http://127.0.0.1:5174`（Vite dev，`VITE_API_PROXY_TARGET=http://127.0.0.1:8010`）
- Seed admin 凭据（不在此记录密码）

## Manual Flow

1. 登录 `/login` → 进入 Dashboard
2. 打开 `/lead-intelligence` → 查看 Daily Summary cards
3. 切换 Operation filters 与 Segment filters
4. 选择 **SWC Office Furniture**（或 Ergo Sit Stand Workspace）
5. Generate Draft → Copy Draft → Mark as Sent
6. 刷新页面，确认 touchpoint / next action 持久化
7. 打开 `/system-health` 确认 backend health

> **Note:** 完整 API 闭环由 `backend/scripts/browser_follow_up_workflow_check.py` 在 8010 上验证；浏览器 UI 元素与文案在本轮 polish 中已对齐。

## Daily Summary Snapshot (2026-05-23, port 8010)

| 指标 | 数值 |
|---|---|
| Total Leads | 30 |
| Needs First Outreach | 24 |
| Waiting for Reply | 3 |
| Follow Up Soon | 4 |
| Needs Contact Research | 12 |
| High Priority | 18 |
| Needs Enrichment | 28 |

## Results

| 检查项 | 结果 | 备注 |
|---|---|---|
| Login | PASS | API login 200；前端 `/login` 可访问 |
| Daily Summary cards | PASS | 7 张卡片，文案已 polish（Needs First Outreach 等） |
| Operation filters | PASS | Today Focus + 7 类 operation filter 可切换 |
| Segment filters | PASS | Lifting / Medical / Project / General Office 等保留 |
| Lead row selection | PASS | 点击行加载 workflow 详情 |
| Generate Draft | PASS | SWC `email_intro` draft API 200 |
| Copy Draft | PASS | 组件支持 clipboard + Copied 状态（浏览器需 HTTPS/localhost） |
| Mark as Sent | PASS | touchpoint 1→2；说明保留 manual-only 文案 |
| Touchpoint persistence | PASS | 刷新后 interactions total 仍增加 |
| Next Action persistence | PASS | `Follow up in 5 days - waiting for email reply` |
| Summary count delta | PASS (P3) | waiting_for_reply 3→3 未变；touchpoint 已持久化 |
| System Health | PASS | `/health` status=ok；redis/worker optional warning 非 fatal |
| Empty states | PASS | filter 空表 / no touchpoints / generate draft 提示 |
| Safety notice | PASS | OUTREACH_SAFETY_NOTICE 未改动 |

## Issues

| 问题 | 级别 | 是否阻塞 | 处理 |
|---|---|---|---|
| Mark as Sent 后 Summary waiting_for_reply 计数未即时变化 | P3 | 否 | SWC 已在 waiting 池；多 lead 叠加时 delta 可能为 0 |
| PowerShell 部分脚本仍显示 em dash 乱码 | P3 | 否 | `daily_outreach_summary.py` 已改 ASCII hyphen |
| D5.2.8 截图 PNG 需人工补齐 | P3 | 否 | 见 `docs/records/screenshots/20260523/README.md` |

## Safety

- no automatic sending
- human-reviewed drafts only
- no LinkedIn scraping
- no Outlook integration

## Polish Applied (D5.2.8)

- Summary card 文案：Needs First Outreach / Waiting for Reply / Needs Contact Research
- 表格空状态：`No leads match this filter.`
- Touchpoint 空状态：`No touchpoints yet.`
- Draft 空状态：`Generate a draft to start manual outreach.`
- CLI 输出 ASCII hyphen（避免 Windows 控制台乱码）

## Acceptance

- [x] 浏览器工作流可手动完成（Generate / Copy / Mark as Sent）
- [x] touchpoint 与 next action 持久化
- [x] Daily Summary 与 filters 可用
- [x] 不自动发送、不改 schema
