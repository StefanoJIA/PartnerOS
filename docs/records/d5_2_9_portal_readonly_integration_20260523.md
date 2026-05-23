# D5.2.9 Portal Read-only Integration

## Goal

为未来统一 Portal 提供只读状态、能力、每日客户开发摘要。

## Read-only Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/portal/manifest` | 模块、能力、Portal URL |
| GET | `/api/v1/portal/summary` | 每日 lead intelligence 摘要 |
| GET | `/api/v1/portal/a-domain/status` | A 域 readiness 标志 |
| GET | `/api/v1/system/readiness` | 系统 readiness（已有） |

所有 v1 端点使用 envelope：`{ ok, data, meta }`。

## Safety

- no automatic sending
- no LinkedIn automation
- no Outlook integration
- no database writes
- no secret exposure
- no private email lists in summary

## Portal Use Case

统一 Portal 可以显示：

- intelliOffice 是否在线
- A 域是否 ready
- 今日客户开发摘要（total / high priority / waiting reply）
- manual outreach 是否可用
- automatic sending 是否 disabled

## UI

`/system-health` 增加 **Portal Readiness** 只读卡片，展示 summary 关键数字与安全说明。

## Check Script

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8010"  # optional
python scripts/portal_readiness_check.py
```

## Acceptance Criteria

- [x] `GET /api/v1/portal/summary` works
- [x] `GET /api/v1/portal/a-domain/status` works
- [x] `/system-health` displays portal readiness
- [x] `portal_readiness_check.py` PASS
- [x] no database migration
- [x] no Phase 2
