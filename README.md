# intelliOffice PartnerOS

## A. Product vision（产品愿景 — 最终交付）

**intelliOffice PartnerOS** 的最终交付形态是 **Windows 桌面应用程序**：用户下载安装包、安装后 **双击图标** 即可使用 — **登录、Dashboard、Leads、伙伴与产品、RFQ、样品、订单、AI 与知识** 等均在 **同一桌面应用** 内完成。

- **最终用户不需要**：安装或管理 PostgreSQL、打开 pgAdmin、安装 Docker、理解 Alembic/迁移命令、手动运行 seed、分别启动「前端」和「后端」、配置 `DATABASE_URL` 或连接串。
- **应用内部** 负责：本地数据目录、**数据库生命周期**（初始化/迁移/扩展/健康）、**后端 sidecar** 启停、引导数据与配置、错误提示与（后续）诊断导出。
- **品牌与伙伴**：对外品牌为 **intelliOffice**。**HOSUN**、**重庆汇聚 / JOOBOO** 及未来工厂均为 **`manufacturing_partners` 中的平级行**；系统 **不得** hard-code 或默认优待任一厂牌；推荐与比价基于能力、认证、价格、交期、MOQ、打样、项目匹配等 **结构化信号**。
- **Lead Intelligence**（市场与客户发现、网站与需求信号、评分等）是 **市场与客户情报域** 的一部分，须与 CRM、RFQ、伙伴与订单链路 **贯通**，而不是独立孤岛产品。开发模式下登录后可通过 **`/lead-intelligence`**（A 域工作台）走通 **公司 → 联系人 → 情报/标签 → 评分 → 互动 → 下一步动作** 的最小闭环；详见 **[docs/migration_from_web_to_desktop.md](docs/migration_from_web_to_desktop.md)** §7。公司详情页 **D5.2 公开来源 Enrichment**（有限官网路径抓取、证据与待审阅建议、显式 apply）见 **[docs/public_source_enrichment_mvp.md](docs/public_source_enrichment_mvp.md)**；Lead Intelligence 概念对齐见 **[docs/lead_intelligence_mvp.md](docs/lead_intelligence_mvp.md)**。
- **市场焦点**：特别关注 **升降与人体工学支撑** 相关需求（如 adjustable frames、lifting columns、sit-stand workstations 等），与产品与伙伴能力、RFQ 需求分析长期对齐。

**当前代码仓库** 使用 Vue + FastAPI + PostgreSQL（pgvector）实现业务逻辑 — 这是 **实现技术栈**；**不是** 最终用户的手动部署形态。更完整的愿景与六域划分见 **[docs/product_vision.md](docs/product_vision.md)**；桌面目标架构见 **[docs/architecture_desktop_target.md](docs/architecture_desktop_target.md)**；阶段路线 **D0–D6** 见 **[docs/roadmap_desktop_transition.md](docs/roadmap_desktop_transition.md)**；路线调整总结与 **中英文总述（可作 Cursor 上下文）** 见 **[docs/project_reorientation_summary.md](docs/project_reorientation_summary.md)**。

**其他文档**：运行模式 [docs/runtime_modes.md](docs/runtime_modes.md) · 数据库生命周期 [docs/database_lifecycle.md](docs/database_lifecycle.md) · **运营指南** [docs/operator_guide.md](docs/operator_guide.md) · **D5 Final Release** [docs/releases/d5_final_mvp_release_20260523.md](docs/releases/d5_final_mvp_release_20260523.md) · **D6 Final Release** [docs/releases/d6_final_quote_mvp_release_20260523.md](docs/releases/d6_final_quote_mvp_release_20260523.md) · **D5 Capability Map** [docs/architecture/d5_capability_map.md](docs/architecture/d5_capability_map.md) · **D6 Capability Map** [docs/architecture/d6_quote_capability_map.md](docs/architecture/d6_quote_capability_map.md) · **Phase 2 Readiness** [docs/phase2/quote_module_readiness_brief.md](docs/phase2/quote_module_readiness_brief.md) · **D7 Readiness Brief** [docs/phase3/d7_order_module_readiness_brief.md](docs/phase3/d7_order_module_readiness_brief.md) · **D5.2 Release** [docs/releases/d5_2_internal_mvp_release_20260523.md](docs/releases/d5_2_internal_mvp_release_20260523.md) · **部署检查** [docs/deployment_readiness_checklist.md](docs/deployment_readiness_checklist.md) · **测试基线** [docs/testing_summary_d5_2.md](docs/testing_summary_d5_2.md) · 打包策略 [docs/packaging_strategy.md](docs/packaging_strategy.md) · Web→桌面迁移说明 [docs/migration_from_web_to_desktop.md](docs/migration_from_web_to_desktop.md) · 开放问题 [docs/open_questions_desktop.md](docs/open_questions_desktop.md) · **A 域人工测试与录入** [docs/manual_a_domain_test_plan.md](docs/manual_a_domain_test_plan.md) · **集成化后端标准（双轨 API / v1）** [docs/integrated_backend_standards.md](docs/integrated_backend_standards.md)。

---

## D5 Final MVP Status

**D5 is closed** as an internal MVP for lead intelligence, product opportunity planning, manual outreach, and quote-preparation handoff.

- Full pre-quote workflow: Lead Intake → Completeness → Contact Research → Product Fit → Pre-Quote → Manual Outreach → Follow-up → Soft Quote Handoff → **Quote Input Contract**
- **Manual outreach only** — no automatic sending
- **No formal quotes** — Quote Input Contract is the Phase 2 boundary object
- **No Phase 2 implementation** — see [D5 Final Release](docs/releases/d5_final_mvp_release_20260523.md) · [Closure Record](docs/records/d5_final_closure_20260523.md)

## D6 Final Quote MVP Status

**D6 is closed** as a Quote MVP covering product catalog, pricing foundation, quote records, quote line items, quote versioning, PDF export, manual delivery tracking, and quote-to-order readiness.

- Full quote workflow: Catalog → Pricing Preview → Quote CRUD → PDF Export → Manual Send → Delivery Log → Timeline → **Order Readiness Gate**
- **Manual delivery only** — export PDF does not send; Mark as Sent records external action
- **No orders, production, or shipment** — Order Readiness produces Order Input Contract only
- See [D6 Final Release](docs/releases/d6_final_quote_mvp_release_20260523.md) · [D6 Closure Record](docs/records/d6_final_closure_20260523.md) · [D6 Capability Map](docs/architecture/d6_quote_capability_map.md)

## Current Major Boundary

| Stage | Scope |
|---|---|
| **D5** | Lead Intelligence and Pre-Quote Preparation |
| **D6** | Quote MVP (closed) |
| **D7** | Order / Production / Shipment (not started) |

## Next Major Stage

**D7** is Order / Production / Shipment.

D7 should not start until order schema, supplier confirmation, production milestone, and shipment tracking boundaries are reviewed. See [D7 Order Module Readiness Brief](docs/phase3/d7_order_module_readiness_brief.md) · [Phase 2 Roadmap](docs/phase2/phase2_roadmap.md).

D6 implementation references:

- [D6.1 Design Review](docs/phase2/d6_1_quote_schema_api_design_review.md)
- [D6.2 Product Catalog & Pricing Foundation](docs/phase2/d6_2_product_catalog_pricing_foundation.md)
- [D6.5 Quote Send Tracking & Delivery Log](docs/phase2/d6_5_quote_send_tracking_delivery_log.md)
- [D6.6 Quote-to-Order Readiness Gate](docs/phase2/d6_6_quote_to_order_readiness_gate.md)

---

## Current MVP Status（D5.2 Internal MVP — superseded by D5 Final）

- **D5.2 Internal MVP ready** — Lead Intelligence、Manual Outreach Queue、Daily Follow-up、Portal 只读集成
- **Manual outreach only** — Generate Draft → Copy → 系统外发送 → Mark as Sent
- **Portal read-only integration ready** — `/api/v1/portal/*` · `/system-health` · `/portal-consumer-mock`
- **No automatic sending** · **No LinkedIn scraping** · **No Outlook API**
- **No Phase 2 yet** — 见 [docs/releases/d5_2_internal_mvp_release_20260523.md](docs/releases/d5_2_internal_mvp_release_20260523.md)

**Release pack（D5.2.11）：** [Release Note](docs/releases/d5_2_internal_mvp_release_20260523.md) · [Operator Guide](docs/operator_guide.md) · [Deployment Checklist](docs/deployment_readiness_checklist.md) · [Testing Summary](docs/testing_summary_d5_2.md)

## Quick Start

### Port 8010 (recommended default — D5.11)

```powershell
# Terminal 1 — backend
.\scripts\dev_env_8010.ps1
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8010

# Terminal 2 — frontend
cd frontend
npm run dev
```

### Quick Runtime Check

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8010"
python scripts/dev_runtime_doctor.py
python scripts/smoke_all_d5.py
python scripts/d5_16_real_lead_uat_check.py   # D5.16 real lead UAT (read-only)
python scripts/d5_17_rule_tuning_check.py     # D5.17 product rule tuning
python scripts/quote_handoff_check.py         # D5.18 soft quote handoff
python scripts/d5_19_quote_input_contract_check.py  # D5.19 quote input contract UAT
python scripts/smoke_all_d5.py                  # D5 full smoke (closure regression)
python scripts/seed_quote_catalog.py --dry-run  # D6.2 demo catalog seed preview
python scripts/seed_quote_catalog.py --apply --confirm  # D6.2 demo catalog seed
python scripts/import_pricing_excel.py --file "../local_data/报价模型与格式.xlsx" --dry-run
python scripts/d6_2_1_excel_import_check.py   # D6.2.1 Excel import alignment
python scripts/d6_3_quote_crud_check.py  # D6.3 quote CRUD smoke
python scripts/d6_4_quote_pdf_export_check.py  # D6.4 quote PDF export smoke
python scripts/d6_5_quote_send_tracking_check.py  # D6.5 send tracking smoke
python scripts/d6_6_quote_order_readiness_check.py  # D6.6 order readiness smoke
python scripts/d6_final_closure_check.py  # D6.7 final closure gate
```

### Port 8000 (legacy)

```powershell
# Terminal 1 — backend
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev

# Scripts
$env:BACKEND_BASE_URL="http://127.0.0.1:8000"
cd backend
python scripts/check_backend_runtime.py
```

First-time setup: `python scripts/init_local_env.py` → edit `backend/.env` → `alembic upgrade head` → `python -m app.scripts.seed`. See [docs/dev_guide.md](docs/dev_guide.md).

## Main Workflows

| Workflow | Entry |
|----------|-------|
| **Daily operations command center** | **`/`** (Dashboard) · summary + Today Focus + Recent Activity + EOD Summary (D5.8–D5.10) |
| Daily outreach | `/lead-intelligence` · [operator_guide.md](docs/operator_guide.md) |
| **Lead intake (CSV)** | **`/lead-intake`** · template: `docs/templates/lead_import_template.csv` |
| **Lead completeness** | **`/lead-intelligence`** · Lead Completeness section (D5.4) |
| **Contact research (in-place edit)** | **`/lead-intelligence`** · Research / Edit drawer (D5.5) |
| **Outreach history timeline** | **`/lead-intelligence`** · Outreach History panel (D5.6) |
| **Follow-up scheduling / due queue** | **`/lead-intelligence`** · Follow-up Scheduler + Due filters (D5.7) |
| **Product fit & project opportunity** | **`/lead-intelligence`** · Product Fit Card + Opportunity Board (D5.12–D5.13) |
| **Product opportunity dashboard** | **`/`** · Product Opportunity Summary strip (D5.13) |
| **Pre-quote & sample prep** | **`/lead-intelligence`** · Pre-Quote Prep Card (D5.14) |
| **Product-aware discovery draft** | **`/lead-intelligence`** · Product-Aware Draft panel (D5.15) |
| **Soft quote handoff** | **`/lead-intelligence`** · Soft Quote Handoff panel (D5.18) |
| **Quote input contract** | **`/lead-intelligence`** · Quote Input Contract panel (D5.19) |
| **Customer quotes (D6.3–D6.6)** | **`/quotes`** · CRUD · PDF · delivery log · **order readiness (D6.6)** |
| **Quote catalog (D6.2)** | **`/quote-catalog`** · partner/category filters · read-only list |
| **Pricing preview (D6.2)** | **`/pricing-preview`** · preview only — no quote created |
| **Daily ops dashboard** | **`/`** · Daily Operations + Recent Activity + End-of-Day Summary (D5.8–D5.10) |
| Lead import preview (CLI) | `backend/scripts/lead_import_preview.py` |
| Outreach draft | Generate Draft in Lead Intelligence |
| Portal readiness | `/system-health` · `portal_readiness_check.py` |
| Daily CLI summary | `daily_outreach_summary.py` |
| Demo screenshots | `python backend/scripts/capture_demo_screenshots.py` · [D5.2.12 demo proof](docs/records/d5_2_12_browser_screenshots_demo_proof_20260523.md) |

---

## B. Development mode（开发模式 — 当前仓库日常）

### Current MVP Status（D5.2.2+ detail）

- **阶段**：D5.2.2 Internal MVP Stabilization（demo-ready 半产品 → 可内部试用）
- **后端**（在 `backend` 目录）：`python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **前端**（在 `frontend` 目录）：`npm run dev`（端口常见 **5173** 或 **5174**）
- **健康检查**：默认 `http://127.0.0.1:8000/health` · 备用本地端口 **8010** · 前端只读页 `/system-health`
- **Backend URL**：脚本 `BACKEND_BASE_URL` · 前端 Vite proxy `VITE_API_PROXY_TARGET`（见 [docs/dev_guide.md](docs/dev_guide.md) § Changing backend port）
- **Smoke**：`cd backend && python scripts/smoke_demo_ready.py`（需 backend 运行；可先 `python scripts/check_backend_runtime.py`）
- **Portal 只读集成（D5.2.9–D5.2.10）**：v1 endpoints `/api/v1/portal/*` · UI `/system-health` · mock `/portal-consumer-mock` · 脚本 `portal_readiness_check.py` / `portal_consumer_check.py` / `config_readiness_check.py` · 记录 [docs/records/d5_2_10_portal_consumer_deployment_readiness_20260523.md](docs/records/d5_2_10_portal_consumer_deployment_readiness_20260523.md)
- **演示脚本**：[docs/records/demo_script_20260523.md](docs/records/demo_script_20260523.md) · **D5.2.2 记录**：[docs/records/d5_2_2_internal_mvp_20260523.md](docs/records/d5_2_2_internal_mvp_20260523.md)

以下内容 **仅供开发者、测试与 CI**，**不代表**最终用户流程：

1. **环境**：PostgreSQL（建议带 **pgvector**）、Python 3、Node.js。可用 `docker compose up -d db`（主机 **5435** → 容器 5432，避免与 WSL/本机 Postgres 冲突；需 **Docker Desktop**）或自建实例 — 见 **[docs/dev_guide.md](docs/dev_guide.md)**。
2. **配置**：**不要**依赖「隐式」数据库连接串。若无 `backend/.env`，`DATABASE_URL` 默认为空，`GET /health` 在 **development** 下会报告 `database_status: not_configured`（见 [docs/database_lifecycle.md](docs/database_lifecycle.md)）。首次请在 `backend` 目录执行：
   ```powershell
   python scripts/init_local_env.py
   python scripts/check_database_config.py
   ```
   然后按需编辑 `backend/.env`。模板见 `backend/.env.example`（示例口令仅用于本机；真实 `.env` 勿提交）。`SECRET_KEY` 与旧文档中的 `JWT_SECRET` 等价（任填其一）。**D5.2** 可选 **`PUBLIC_ENRICHMENT_ENABLED=false`**（CI/无外网）见 [docs/public_source_enrichment_mvp.md](docs/public_source_enrichment_mvp.md)。
3. **后端**（在 `backend` 目录，且 **已能通过 `check_database_config.py`** 后）：
   ```bash
   pip install -r requirements.txt
   alembic upgrade head
   python -m app.scripts.seed
   python -m app.scripts.seed_business_flow   # 可选 demo 链
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. **前端**（在 `frontend` 目录）：
   ```bash
   npm install
   npm run dev
   ```
   Vite 将 `/api` 与 **`/health`（D2 桌面启动页）** 代理到后端（默认 `http://127.0.0.1:8000`，可通过 `VITE_API_PROXY_TARGET` 改为 **8010** — 见 [frontend/vite.config.ts](frontend/vite.config.ts) 与 [docs/dev_guide.md](docs/dev_guide.md)）。
5. **桌面壳（D2/D3，可选）**：需本机安装 **Rust** 与（若需本地冻结 sidecar）**Python + PyInstaller**。日常开发可 **只**跑手动 `uvicorn :8000` + `$env:INTELLIOFFICE_EXTERNAL_BACKEND='1'; npm run tauri:dev`（debug 默认 **不**派生 sidecar，`/health` 仍走 Vite 代理）。要验证 **产品路径**：先 `cd frontend; npm run sidecar:prepare`，再例如 `$env:INTELLIOFFICE_MANAGE_SIDECAR='1'; npm run tauri:dev`（sidecar 默认 **`127.0.0.1:17888`**）。正式包 `npm run tauri:build` 会在 `beforeBuildCommand` 中自动 `sidecar:prepare`。详见 **[docs/dev_guide.md](docs/dev_guide.md)**、**[docs/testing.md](docs/testing.md)（D2 Gate + D3 sidecar）**。**不替代**浏览器下的 `npm run dev` 流程。

Default login after `seed`: `admin@example.com` / `admin123`。

- **测试与集成库**（`PARTNEROS_TEST_DATABASE_URL` 等）：仅开发者/CI — 见 **[docs/testing.md](docs/testing.md)**。
- **Activity 词汇**：[docs/activity_actions.md](docs/activity_actions.md)。

---

## Principles（原则）

- **intelliOffice** 为前台品牌；所有工厂为数据表中的平级伙伴，**无**硬编码默认供应商。
- AI 使用 OpenAI 兼容 API；无 key 时后端可返回占位文本以便 UI 联调（见 backend AI client）。
- Knowledge：`POST /api/files/upload` → `POST /api/knowledge/ingest` → `POST /api/knowledge/query`。

## Docker Compose（开发可选用）

`docker compose up --build` 可启动 db、backend、frontend、nginx（见 [docker-compose.yml](docker-compose.yml)）。根目录 `.env` 可覆盖 `DATABASE_URL` 等。

## Tests

- Backend: `cd backend && pytest`（含 `test_database_lifecycle`、`test_sidecar_entry`、`test_health` 等）— **[docs/testing.md](docs/testing.md)**  
- Frontend: `cd frontend && npm run build`；契约单测：`cd frontend && npm run test`（`healthGate`、`backendOrigin`、**`CompanyEnrichmentPanel`**）  
- Health: **后端自检地址为** `http://127.0.0.1:8000/health`。直接访问根路径 `http://127.0.0.1:8000/` 若得到 `{"detail":"Not Found"}` **属于预期**（未注册 `/` 路由）。开发代理下桌面启动页仍通过 Vite 访问 **`/health`**（见 [frontend/vite.config.ts](frontend/vite.config.ts)）；托管 sidecar 默认 **`http://127.0.0.1:17888/health`** — 返回 JSON：D1 字段 + **D4** `database_lifecycle_phase`、`migration_pending`、`alembic_*`（见 [database_lifecycle.md](docs/database_lifecycle.md)、[runtime_modes.md](docs/runtime_modes.md)）；端口以当前模式为准。

---

## 暂缓（至桌面基础夯实前）

不优先启动：`Field Visit` 大功能详情、`Constant Contact`/`Campaign`、正式 **报价 PDF**、重网页采集、本地大模型训练、云同步、完整企业 RBAC 产品化 — 见 **[docs/roadmap_desktop_transition.md](docs/roadmap_desktop_transition.md)**。
