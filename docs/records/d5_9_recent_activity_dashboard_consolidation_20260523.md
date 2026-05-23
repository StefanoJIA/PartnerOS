# D5.9 Recent Activity & Dashboard Consolidation

## Goal

将 daily operations、recent outreach、contact research、due queue、system status 集中到 Dashboard。

## Dashboard Workflow

1. 登录。
2. 打开 Dashboard `/`。
3. 查看 Due / Priority / Research summary cards（点击可跳转 Lead Intelligence 筛选）。
4. 查看 Today Focus Top 10。
5. 查看 Recent Manual Outreach 与 Recent Contact Research。
6. 使用 Quick Actions 进入 Lead Intake / Lead Intelligence / System Health。
7. 需要 RFQ/样品/订单时展开「更多行动看板」。

## API

增强 `GET /api/a-domain/daily-ops-summary`：

- `recent_activity` — 综合最近活动（最多 10 条）
- `recent_manual_outreach` — `manually_sent=true`（最多 5 条）
- `recent_contact_research` — contact research touchpoint（最多 5 条）

## Safety

- no automatic sending
- no Outlook integration
- no LinkedIn automation
- manual workflow only
- summary 中 email 已 mask

## Acceptance Criteria

- [x] Dashboard 显示 summary
- [x] Today Focus 可见
- [x] Recent Activity 可见
- [x] Quick Actions 可用
- [x] tests pass
- [x] no DB migration
