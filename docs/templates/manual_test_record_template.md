# 人工测试记录与客户录入矩阵（模板）

与主计划配套使用：[manual_a_domain_test_plan.md](../manual_a_domain_test_plan.md)

---

## 1. 测试执行记录表（可复制）

| Test ID | Module | Scenario | Company | Expected | Actual | Pass/Fail | Issue Type | Notes |
|---------|--------|----------|---------|------------|--------|-----------|------------|-------|
| | | | | | | | | |
| | | | | | | | | |

**Issue Type**：`data_entry` · `scoring_rule` · `segment_rule` · `enrichment_fetch` · `evidence_quality` · `review_ui` · `backend_error` · `frontend_error` · `desktop_sidecar` · `documentation` · `business_judgment`

---

## 2. 客户录入矩阵（每条客户一行）

| Field | Value |
|-------|-------|
| Test Case ID | |
| Company Name | |
| Website | |
| City / State / Country | |
| Business Type（枚举） | |
| Business Summary（business_description） | |
| Source | |
| Source URL（写入 notes） | |
| Initial Notes（notes） | |
| Primary Contact Name | |
| Title / Email / Phone | |
| LinkedIn URL | |
| Role Type（contact_type） | |
| Decision Power（decision_maker_level） | |
| Do Not Contact（notes 约定） | |
| Lead Name（若单独测线索） | |
| Lead product_interest | |
| Expected Segment(s) | |
| Expected Non-Segment(s) | |
| Tester / Date | |

---

## 3. Interaction 自由文本块（直至 D5.3 结构化）

当工作台仅支持 `subject` / `summary` 时，可将下列键值 **粘贴到 `summary` 末尾**（或 API 写入 `content`）：

```text
--- structured_stub ---
intent_level: medium
product_interest: height_adjustable_desk
customer_need: （一句话）
objection: （如有）
occurred_context: inbound|outbound
raw_note: （原始纪要）
---
```

评审时若字段与 UI 不一致，Issue Type 选 `documentation` 并指向 `manual_a_domain_test_plan.md` Part C。

---

## 4. D5.2 Enrichment 单条 Run 记录

| Run ID | Company | Started | Status | Pages | Pending Suggestions | Fail Reason | Reviewer |
|--------|---------|---------|--------|-------|---------------------|-------------|----------|
| | | | | | | | |

---

## 5. Segment / 评分人工对照（抽样）

| TC ID | company_id | market_fit_segments（实际） | 人工认为应对/应错 | Pass/Fail | 备注 |
|-------|--------------|------------------------------|---------------------|-------------|------|
| | | | | | |
