# 浏览器 UI 截图目录（2026-05-23）

**归档状态：PARTIAL — 截图需人工补齐（D5.2.11 Release Pack）**

请在浏览器打开 **http://127.0.0.1:5174**（或 Vite 终端显示的端口），使用 **默认 seed admin 凭据** 登录后截取。

**注意**：

- 截图中 **token、password 必须打码**
- **未打码截图不要提交**（已在根目录 `.gitignore` 排除 `docs/records/screenshots/**/*.png` 等）
- 真实客户 **邮箱建议打码**
- PNG 文件由人工放置于本目录，或仅保存在本地 ignored 路径

---

# Screenshot Archive Plan（D5.2.11 最小集）

| # | 文件名 | 内容 |
|---|--------|------|
| 1 | `login_success.png` | 登录后 Dashboard |
| 2 | `lead_intelligence_daily_summary.png` | `/lead-intelligence` Daily Summary cards |
| 3 | `operation_filters.png` | Operation + Segment filters |
| 4 | `outreach_draft_panel.png` | Generate Draft 面板 + Safety notice |
| 5 | `mark_as_sent_success.png` | Mark as Sent 成功（manual-only 文案） |
| 6 | `touchpoint_persisted.png` | 触达记录含 `[manually_sent=true]` |
| 7 | `system_health_portal_readiness.png` | `/system-health` Portal Readiness |
| 8 | `portal_consumer_mock.png` | `/portal-consumer-mock` 只读 mock |

---

## D5.2.2 扩展演示截图（9 张，可选）

| 文件名 | 内容 |
|--------|------|
| `dashboard_system_status.png` | Dashboard 或 system status |
| `companies_list.png` | `/companies` UAT 公司 |
| `company_detail_ergo.png` | Ergo 公司详情 |
| `lead_workflow_ergo.png` | Ergo score + Lifting Signal |
| `lead_workflow_healthcare_medical.png` | Healthcare medical segment |
| `lead_workflow_contract_project.png` | Contract project segment |
| `enrichment_panel_results_ergo.png` | Enrichment 审阅抽屉 |
| `touchpoint_next_action.png` | Touchpoint + Next Action |

---

## D5.2.8 别名对照

| D5.2.8 文件名 | D5.2.11 等价 |
|---------------|--------------|
| `daily_summary_cards.png` | `lead_intelligence_daily_summary.png` |
| `system_health_page.png` | `system_health_portal_readiness.png` |

---

## 扩展清单（可选）

| 文件名 | 内容 |
|--------|------|
| `login_page.png` | `/login` |
| `localstorage_token_masked.png` | DevTools token 打码 |
| `network_login_200.png` | POST login 200 |
| `contacts_list.png` | `/contacts` |

---

**当前目录**：结构已就绪；**PNG 尚未生成 — Manual screenshot required.**

See also: [D5.2 Release Note](../../releases/d5_2_internal_mvp_release_20260523.md) · [Operator Guide](../../operator_guide.md)
