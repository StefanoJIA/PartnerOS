# D5.8 Daily Operations Command Center

## Goal

把每日客户开发最重要的信息集中到 Dashboard。

## Dashboard Flow

1. 登录。
2. 打开首页 `/`（Dashboard）。
3. 查看 **Daily Operations** 区块。
4. 处理 **Overdue** / **Due Today** 计数。
5. 查看 **Today Focus** Top 10 推荐线索。
6. 使用 **Quick Actions** 进入 Lead Intake / Lead Intelligence / System Health / Portal Mock。
7. 继续人工外联与跟进。

## API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/a-domain/daily-ops-summary` | 只读聚合：summary + today_focus + quick_actions + safety |

复用 follow-up queue 与 lead completeness 逻辑，无数据库写入。

## Safety

- no automatic sending
- no Outlook integration
- no LinkedIn automation
- manual workflow only

## Acceptance Criteria

- [x] Dashboard 显示 daily operations
- [x] Today Focus 可见
- [x] Quick actions 可用
- [x] tests pass
- [x] no DB migration

## Script

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8010"   # if needed
python scripts/daily_ops_summary_check.py
```
