# 浏览器 UI 截图目录（2026-05-23）

**归档状态：PARTIAL — D5.2.8 截图需人工补齐**

请在浏览器打开 **http://127.0.0.1:5174**（或 Vite 终端显示的端口），使用 **默认 seed admin 凭据** 登录后截取。

**注意**：

- 截图中 **token、password 必须打码**
- **未打码截图不要提交**（已在根目录 `.gitignore` 排除 `docs/records/screenshots/**/*.png` 等）
- PNG 文件由人工放置于本目录

---

## D5.2.2 最小演示截图清单（9 张）

| 文件名 | 内容 |
|--------|------|
| `login_success.png` | 登录后 Dashboard（含 System Status 卡片） |
| `dashboard_system_status.png` | Dashboard 或 `/system-health` 系统状态区域 |
| `companies_list.png` | `/companies` 列表（含 UAT 测试公司） |
| `company_detail_ergo.png` | Ergo Sit Stand Workspace 公司详情 |
| `lead_workflow_ergo.png` | Ergo lead workflow（score + Lifting System Signal） |
| `lead_workflow_healthcare_medical.png` | Healthcare lead — Medical / Healthcare Vertical |
| `lead_workflow_contract_project.png` | Contract Project — Project-Based Furniture |
| `enrichment_panel_results_ergo.png` | Ergo Enrichment 审阅抽屉（证据 + suggestions） |
| `touchpoint_next_action.png` | Touchpoint 历史 + Next Action 字段 |

---

## D5.2.8 每日跟进工作台（6 张）

| 文件名 | 内容 |
|--------|------|
| `daily_summary_cards.png` | `/lead-intelligence` 顶部 7 张 Daily Summary cards |
| `operation_filters.png` | Operation filters + Segment filters 两组筛选 |
| `outreach_draft_panel.png` | Generate Draft 后面板（含 Safety notice） |
| `mark_as_sent_success.png` | Mark as Sent 成功提示（manual-only 文案可见） |
| `touchpoint_persisted.png` | 最近触达记录含 `[manually_sent=true]` 条目 |
| `system_health_page.png` | `/system-health` backend ok + optional redis/worker warning |

---

## 扩展清单（可选）

| 文件名 | 内容 |
|--------|------|
| `login_page.png` | `/login` 页面 |
| `localstorage_token_masked.png` | DevTools → localStorage（token 打码） |
| `network_login_200.png` | Network → POST `/api/auth/login` 200 |
| `company_detail_healthcare.png` | Healthcare 公司详情 |
| `contacts_list.png` | `/contacts` |
| `lead_intelligence_list.png` | `/lead-intelligence` 列表 |

---

**当前目录**：结构已就绪；**PNG 尚未生成 — Manual screenshot required.**
