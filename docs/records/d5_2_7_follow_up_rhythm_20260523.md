# D5.2.7 Follow-up Rhythm & Daily Operations

## Goal

每天打开 intelliOffice，就知道今天该推进哪些客户。

## Daily Workflow

1. 打开 `/lead-intelligence`。
2. 看 **Daily Summary** 卡片（Total / First Outreach / Waiting Reply 等）。
3. 筛选 **Today Focus**。
4. 先处理 **High Priority**。
5. 再处理 **Needs First Outreach**。
6. 对 **Waiting for Reply** 的客户进行 follow-up。
7. 对 **Needs Contact Research** 的客户补联系人。
8. 对 **Ready for Catalog / Quote** 的客户准备资料。
9. **Generate Draft**。
10. 人工在外部渠道发送。
11. **Mark as Sent**。
12. 记录 next action。

## CLI Summary

```powershell
cd backend
python scripts/daily_outreach_summary.py
```

可选备用端口：

```powershell
$env:BACKEND_BASE_URL="http://127.0.0.1:8010"
python scripts/daily_outreach_summary.py
```

## Safety Rules

- 不自动发送。
- 不自动抓 LinkedIn。
- 不绕过平台限制。
- 所有草稿人工审核。
- 所有发送动作由用户在系统外完成。

## Acceptance Criteria

- [x] 能看到每日 summary（UI cards + CLI script）
- [x] 能筛选 follow-up 类别（Operation filters）
- [x] 能识别 high priority
- [x] 能识别 waiting reply
- [x] 能识别 needs contact research
- [x] 能继续使用 Generate Draft / Mark as Sent
- [x] 不改数据库 schema
