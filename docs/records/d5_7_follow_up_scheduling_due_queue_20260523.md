# D5.7 Follow-up Scheduling & Due Queue

## Goal

将 next action 升级为结构化 follow-up date，用于每日跟进节奏。

## Workflow

1. 打开 `/lead-intelligence`。
2. 选择 lead。
3. Generate Draft。
4. 人工发送。
5. Mark as Sent。
6. 在 **Follow-up Scheduler** 中选择 5 天后（或 quick button）。
7. Save Follow-up。
8. 第二天查看 **Due Queue** filters（Overdue / Due Today / Due Soon）。
9. 按 hint 继续跟进。

## Data model

复用现有 `leads.next_action_due_date`（API 字段名 `next_follow_up_date`）。`due_status` 为 derived，不入库。

## API

| Method | Path | 说明 |
|--------|------|------|
| PATCH | `/api/a-domain/leads/{lead_id}/follow-up` | 设置 follow-up date + touchpoint |
| GET | `/api/a-domain/follow-up-queue` | Due queue summary + rows |

## Safety

- no automatic sending
- no Outlook integration
- no calendar creation
- manual follow-up only

## Acceptance Criteria

- [x] 可设置 follow-up date
- [x] 可筛选 overdue / due today / due soon
- [x] timeline 可显示 follow-up 状态
- [x] tests pass
