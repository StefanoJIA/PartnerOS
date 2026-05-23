# D5.2.5 Manual Outreach Queue

**Date**: 2026-05-23  
**Stage**: Daily manual outreach operations (not automation)

---

## Goal

把 Lead Intelligence 和 Outreach Draft Kit 用于**每日人工客户开发** — 队列、草稿、复制、Mark as Sent、touchpoint 台账。

---

## Workflow

1. 打开 **`/lead-intelligence`**
2. 查看 **Manual Outreach Queue**（按 score / touchpoint 排序）
3. 使用筛选：**All · High Score · No Next Action · Needs Follow-up · Lifting · Medical · Education · Project · General Office**
4. 点击一行选择 lead
5. **Generate Draft**（推荐 channel / product focus 已预填）
6. **Copy Draft** → 在 LinkedIn / Outlook / Email **人工发送**
7. 回到 intelliOffice → **Mark as Sent**
8. 系统记录 touchpoint（`manually_sent=true` 写入 summary notes）
9. 确认或调整 **next action**（如 Follow up in 5 days）
10. 次日 **Refresh** 队列继续跟进

---

## Safety Rules

- **不自动发送**
- **不自动抓 LinkedIn**
- **不绕过平台限制**
- 所有草稿人工审核
- Mark as Sent 仅表示「您已在系统外手动发送」

顶部提示：

> intelliOffice only generates human-reviewed drafts. It does not send messages, scrape LinkedIn, or automate platform actions.

---

## Business Focus

- HOSUN lifting systems
- JOOBOO education furniture
- Medical / lab workspace
- Project-based furniture customers
- OEM / ODM opportunities

---

## Automation check

```powershell
cd backend
python scripts/outreach_queue_check.py
```

---

## Acceptance Criteria

- [x] 可查看 outreach queue
- [x] 可生成草稿
- [x] 可复制草稿
- [x] 可 Mark as Sent
- [x] 可记录 touchpoint
- [x] 可设置 next action

---

## Related

- [d5_2_4_lead_intake_outreach_kit_20260523.md](d5_2_4_lead_intake_outreach_kit_20260523.md)
- [d5_2_3_internal_pilot_workflow_20260523.md](d5_2_3_internal_pilot_workflow_20260523.md)
