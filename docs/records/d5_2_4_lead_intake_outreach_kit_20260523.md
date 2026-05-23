# D5.2.4 Lead Intake & Outreach Draft Kit

**Date**: 2026-05-23  
**Stage**: Pilot lead intake + human-reviewed outreach (not Phase 2)

---

## Goal

把 intelliOffice 用于真实客户开发前的 **lead intake**、**分段预判** 和 **人工审核外联草稿** 生成。

---

## Workflow

1. 准备 CSV — [templates/lead_import_template.csv](../templates/lead_import_template.csv)
2. 运行 preview（只读）：
   ```powershell
   cd backend
   python scripts/lead_import_preview.py ../docs/templates/lead_import_template.csv
   ```
3. 修正缺失字段（website、notes、contact 等）
4. 可选导入（需 backend 运行）：
   ```powershell
   python scripts/lead_import_preview.py ../docs/templates/lead_import_template.csv --apply --confirm
   ```
   - 不覆盖已有公司名（duplicate → SKIP）
5. 打开 `/lead-intelligence` 查看 segment 与 Lead Review
6. 生成外联草稿（CLI 或 UI **Generate Draft**）：
   ```powershell
   python scripts/generate_outreach_draft.py --company "Ergo Sit Stand Workspace" --channel linkedin_connect --product-focus hosun_lifting
   python scripts/generate_outreach_draft.py --company "Campus Learning Furniture" --channel email_intro --product-focus jooboo_education
   python scripts/generate_outreach_draft.py --company "Healthcare Lab Workspace" --channel email_intro --product-focus medical_workspace
   ```
7. **人工复制** 到 LinkedIn / Outlook，审核后发送
8. 发送后在 touchpoint 表单记录互动
9. 设置或采纳 suggested next action

---

## Safety Rules

- 不自动抓 LinkedIn
- 不自动发信
- 不绕过平台限制
- 所有草稿必须人工审核
- 草稿不含价格/交期/库存虚假承诺
- 不提交真实客户隐私到 git

---

## Branding

- **intelliOffice** = 平台 / 业务主线
- **HOSUN**、**JOOBOO** = 平级制造伙伴或供应来源，非唯一主品牌

---

## Business Focus

- HOSUN lifting systems（frames, columns, legs）
- JOOBOO education furniture
- Medical / lab workspace
- Project-based furniture contractors
- OEM / ODM opportunities (`oem_odm_fit` segment)

---

## API (additive)

`GET /api/a-domain/outreach-draft?company_id=...&channel=...&product_focus=...`

返回 copy-only 草稿 JSON；不发送、不持久化。

---

## Related

- [lead_import_template.md](../templates/lead_import_template.md)
- [lead_intelligence_scoring_notes.md](../lead_intelligence_scoring_notes.md)
- [d5_2_3_internal_pilot_workflow_20260523.md](d5_2_3_internal_pilot_workflow_20260523.md)
