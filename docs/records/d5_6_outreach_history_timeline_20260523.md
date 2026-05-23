# D5.6 Outreach History & Follow-up Timeline

## Goal

让每个客户的联系历史、人工发送记录、contact research、next action 可视化。

## Workflow

1. 打开 `/lead-intelligence`。
2. 选择 lead。
3. 查看 **Outreach History**（Outreach Draft 下方）。
4. **Generate Draft**。
5. 人工发送。
6. **Mark as Sent**。
7. Timeline 自动增加记录。
8. 查看 **follow-up hint**。
9. 第二天根据 hint 继续跟进。

## API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/a-domain/leads/{lead_id}/timeline` | 只读 outreach history + stats + follow-up hint |

## Follow-up hint 优先级

Needs contact research > Needs first outreach > Follow up soon > Waiting for reply > Ready to prepare outreach > Review next action

## Safety

- no automatic sending
- no LinkedIn automation
- no Outlook integration
- manual actions only

## Acceptance Criteria

- [x] timeline 可见
- [x] 空状态清楚
- [x] Mark as Sent 后刷新
- [x] Contact Research 后刷新
- [x] tests pass
