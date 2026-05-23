# D5.2.6 Real Lead Batch Pilot

## Goal

用过往真实客户记录验证 intelliOffice 是否可支持实际客户开发试运行（CSV 导入 → segment → 草稿 → Manual Outreach Queue → Mark as Sent → touchpoint / next action）。

## Customer Batch

本地文件（**不提交 git**）：`local_data/real_leads_d5_2_6_20260523.private.csv`

| # | 公司 | 联系人（摘要） | 预期 segment |
|---|------|----------------|--------------|
| 1 | SWC Office Furniture | James Riffice | lift / project |
| 2 | Jefferson Group | Anna; Steve | project |
| 3 | Yony's Office Furniture | Jeffer Linares; Bladimir Guerra | project / lift |
| 4 | Commercial Furniture Resource | Lorraine Gomez | general office |
| 5 | Human Active Technology | A. Harty | lift / OEM |
| 6 | OCI Office Concepts Inc. | Rick Vitale | lift / project |
| 7 | LABERS Furniture | Mark Raidt | general office |
| 8 | Overnight Office | Craig Horn | general office |
| 9 | Dancker | John Horn | project |
| 10 | Transfer Enterprises | （待调研） | general office + contact research |

## Backend Test

### CSV preview

```bash
cd backend
python scripts/lead_import_preview.py ../local_data/real_leads_d5_2_6_20260523.private.csv
```

- 10/10 行可读，无 missing `company_name`
- 缺 email 为 WARN，不阻塞
- Transfer Enterprises → `Research contact before outreach`
- HAT → `lift_system_signal`
- Jefferson / Yony's / Dancker → `project_based_furniture`
- CFR / LABERS / Overnight / Transfer → `general_office_furniture_only`

### Apply import

```bash
python scripts/lead_import_preview.py ../local_data/real_leads_d5_2_6_20260523.private.csv --apply --confirm
```

- 首次导入创建 company + lead；重跑为 SKIP duplicate 并补 contact / 公司字段
- 已存在 seed 公司（如 Jefferson Group）不重复创建公司名

### Draft generation

对 SWC、Jefferson、Yony's、CFR、HAT 各生成一条草稿（CLI，不自动发送）：

```bash
python scripts/generate_outreach_draft.py --company "SWC Office Furniture" --channel email_intro --product-focus hosun_lifting
python scripts/generate_outreach_draft.py --company "Jefferson Group" --channel email_followup --product-focus project_supply
python scripts/generate_outreach_draft.py --company "Yony's Office Furniture" --channel linkedin_followup --product-focus hosun_lifting
python scripts/generate_outreach_draft.py --company "Commercial Furniture Resource" --channel email_intro --product-focus general
python scripts/generate_outreach_draft.py --company "Human Active Technology" --channel email_intro --product-focus hosun_lifting
```

### real_lead_batch_check

```bash
python scripts/real_lead_batch_check.py
```

结果：**PASS**（10 公司、segment 分布、5 草稿、touchpoint/next action、安全措辞）

## Frontend Test

在 `http://127.0.0.1:5174/login` 使用 seed admin 登录后：

1. `/lead-intelligence` → Manual Outreach Queue 可见 10 家 pilot 公司
2. 筛选：All / Lifting / Project / General Office / No Next Action
3. Generate Draft → Copy Draft（不自动发送）
4. Mark as Sent → touchpoint 增加、next action 更新、刷新后持久化
5. 至少 SWC、Jefferson、CFR、HAT 完成 Generate 或 Mark as Sent

Mark as Sent 文案说明：仅记录人工在外部渠道已发送，系统不代发。

## Safety

- 不自动发送邮件或 LinkedIn 消息
- 不接 Outlook / LinkedIn API
- 不提交真实客户 CSV（`local_data/`、`* .private.csv` 已在 `.gitignore`）
- 所有外联草稿需人工审核后再复制到外部工具

## Acceptance Criteria

- [x] 10 个客户可进入系统
- [x] segment 基本合理（lift / project / general 分布符合预期）
- [x] 草稿可生成（含 subject/body 或 LinkedIn ≤300 字符）
- [x] 至少 3 个客户完成 Mark as Sent（SWC、Jefferson、CFR）
- [x] next action 可持续跟进
- [x] `real_lead_batch_check.py` PASS
- [x] pytest + smoke + pilot + outreach_queue PASS

## D5.2.6 P2 Closure

### duplicate import issue

重复运行 `lead_import_preview.py --apply --confirm` 时，若 lead 已存在但 `primary_contact_id` 为空，脚本会尝试 `PUT /api/leads/{id}` 补齐关联。此前该 PUT 返回 **500**，导致 contact 无法挂到 lead。

### root cause

`update_lead` 将 `body.model_dump()` 原样传入 `log_activity(..., diff=data)`。当 `diff` 含 `UUID` 类型（如 `primary_contact_id`）时，SQLAlchemy JSONB 序列化失败：

`TypeError: Object of type UUID is not JSON serializable`

### fix summary

1. 新增 `app/services/json_safe.py` → `serialize_for_json()`，在 `log_activity` 写入前转换 UUID / datetime / Decimal。
2. 新增 `app/services/a_domain/lead_import_apply.py`：contact 按 email / name 匹配；`build_lead_link_payload` 安全补 `primary_contact_id`（不覆盖已有 contact 或 next_action）。
3. `lead_import_preview.py` 重复 apply 输出 `SKIP` / `LINKED` / `UPDATED`，不再 500。

### repeated apply result

连续两次 apply 应全部为 `SKIP duplicate` 或 `LINKED`（首次补齐 contact 关联），无 `FAIL link` / 500。

### tests

- `tests/test_activity_json.py` — UUID/datetime JSON 安全序列化
- `tests/test_lead_import_apply.py` — contact 匹配与 link payload 幂等
