# 浏览器 UI 截图目录（2026-05-23）

**归档状态：D5.2.12 — Procedure ready · PNG pending local capture · Not committed**

请在 backend + DB 就绪后打开 **http://127.0.0.1:5174**，登录后截取。详见 [D5.2.12 Demo Proof](../d5_2_12_browser_screenshots_demo_proof_20260523.md)。

**注意**：

- 截图中 **token、password 必须打码**
- **未打码截图不要提交**（`.gitignore` 排除 `docs/records/screenshots/**/*.png`）
- 真实客户 **邮箱必须打码**
- 推荐：**Stored locally only / not committed**

---

## D5.2.12 核心截图状态

| File | Required | Masked | Committed | Notes |
|------|----------|--------|-----------|-------|
| `login_success.png` | Yes | N/A | No | Stored locally only — post-login Dashboard |
| `lead_intelligence_daily_summary.png` | Yes | Review emails | No | Stored locally only |
| `operation_filters.png` | Yes | Review emails | No | Stored locally only |
| `manual_outreach_queue.png` | Yes | **Mask emails** | No | Stored locally only |
| `outreach_draft_panel.png` | Yes | No token | No | Stored locally only |
| `mark_as_sent_success.png` | Yes | No secrets | No | Stored locally only |
| `system_health_portal_readiness.png` | Yes | No secrets | No | Stored locally only |
| `portal_consumer_mock.png` | Yes | No email lists | No | Stored locally only |
| `company_detail_enrichment.png` | Optional | Public URLs only | No | Optional |

**Capture tool:** `python backend/scripts/capture_demo_screenshots.py` (requires Playwright + running DB)

---

## Screenshot Archive Plan

| # | 文件名 | 内容 |
|---|--------|------|
| 1 | `login_success.png` | 登录后 Dashboard |
| 2 | `lead_intelligence_daily_summary.png` | Daily Summary cards |
| 3 | `operation_filters.png` | Operation + Segment filters |
| 4 | `manual_outreach_queue.png` | Manual Outreach Queue 表格 |
| 5 | `outreach_draft_panel.png` | Generate Draft + Safety notice |
| 6 | `mark_as_sent_success.png` | Mark as Sent 后 touchpoint |
| 7 | `system_health_portal_readiness.png` | Portal Readiness |
| 8 | `portal_consumer_mock.png` | External Portal mock |

---

## 打码规则

**必须打码：** token · password · secret · 真实客户私人邮箱/电话 · API key

**可保留：** 公司名 · segment · score · summary counts · 公开业务描述

---

## 扩展清单（可选）

| 文件名 | 内容 |
|--------|------|
| `company_detail_enrichment.png` | Enrichment evidence / suggestions |
| `daily_outreach_summary_cli.png` | CLI 输出（可选） |
| `login_page.png` | 登录页（未登录） |

---

See also: [D5.2 Release Note](../../releases/d5_2_internal_mvp_release_20260523.md) · [Operator Guide](../../operator_guide.md)
