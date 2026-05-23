# D5.5 Contact Research Action Flow

## Goal

让用户可以直接在 Lead Completeness 队列中补全联系人和公司基础资料，无需跳转到 Company / Contact 页面。

## Workflow

1. 打开 `/lead-intelligence`。
2. 筛选 **Needs Contact Research**。
3. 点击 **Research / Edit**。
4. 填写联系人或公司网站。
5. 保存。
6. 系统记录 contact research touchpoint（`contact_research` / `manual_research`）。
7. completeness score 更新。
8. lead 进入 **Ready for Outreach**（资料足够时）。
9. **Generate Draft**。
10. **Mark as Sent**。

## API

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/a-domain/leads/{lead_id}/contact-research` | 手动补资料 + touchpoint + 返回最新 completeness row |

请求示例：

```json
{
  "company": { "website": "https://example.com", "company_type": "Office Furniture Dealer", "notes": "Found on trade show list" },
  "contact": { "name": "Alex Buyer", "title": "VP Sales", "email": "alex@example.com", "phone": "+1-555-0100", "linkedin_url": "https://linkedin.com/in/alex" },
  "lead": { "next_action": "Send intro email" },
  "touchpoint_note": "Updated contact research information manually."
}
```

## UI

- Lead Completeness 表格每行 **Research / Edit** 按钮
- **Contact Research** drawer：公司 / 联系人 / next action 字段
- 安全提示：不自动搜索 LinkedIn、不抓取网站、不发送消息

## Safety

- no automatic LinkedIn search
- no scraping
- no Outlook integration
- no automatic sending
- manually researched information only

## Acceptance Criteria

- [x] 可编辑缺失字段
- [x] 可创建/关联 contact
- [x] 可更新 company website
- [x] 可记录 touchpoint
- [x] completeness score 更新
- [x] tests pass
