# intelliOffice Operator Guide

**Audience:** 内部运营 / 客户开发 / 演示人员  
**Release:** D5 Final MVP (closed) · **Not Phase 2**

## Daily Startup

### Recommended — port 8010 (D5.11 default)

```powershell
# Optional: set env in one shot
.\scripts\dev_env_8010.ps1

cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

Or use helper (does not auto-kill stale processes):

```powershell
.\scripts\start_backend_8010.ps1
```

Align scripts and frontend proxy:

```powershell
$env:BACKEND_BASE_URL="http://127.0.0.1:8010"
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8010"
```

Or set `frontend/.env.local` (gitignored):

```env
VITE_API_PROXY_TARGET=http://127.0.0.1:8010
```

**Do not run multiple uvicorn instances with different code versions.** If 8010 is occupied but `/health` fails, see [Runtime Startup Routine](#runtime-startup-routine).

### Legacy — port 8000

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
$env:BACKEND_BASE_URL="http://127.0.0.1:8000"
```

### Frontend

```powershell
cd frontend
npm run dev
```

Open the URL printed by Vite (often `http://127.0.0.1:5173` or `5174`).

### Quick health check

```powershell
cd backend
python scripts/check_backend_runtime.py
python scripts/dev_runtime_doctor.py
```

## Runtime Startup Routine

1. 启动 Docker DB：`docker compose up -d db`
2. 设置环境：`.\scripts\dev_env_8010.ps1`（或手动 `BACKEND_BASE_URL` / `VITE_API_PROXY_TARGET`）
3. 启动 backend **8010**（单一实例，最新代码）
4. 启动 frontend：`cd frontend; npm run dev`
5. 运行 `python scripts/dev_runtime_doctor.py`
6. 运行 `python scripts/smoke_all_d5.py`

**Stale port 8010**（占用但 `/health` 失败）：

```powershell
netstat -ano | findstr :8010
tasklist /FI "PID eq <PID>"
Stop-Process -Id <PID> -Force
```

Fallback：`$env:BACKEND_BASE_URL="http://127.0.0.1:8013"` 与相同 `VITE_API_PROXY_TARGET`。

## D6 Final Quote Workflow

End-to-end operator flow for the closed D6 Quote MVP:

1. Maintain product catalog (`/quote-catalog` or seed/import scripts).
2. Maintain FX rate (`POST /api/v1/fx-rates` or seed).
3. Preview pricing (`/pricing-preview` — does not create a quote).
4. Create quote (`/quotes/new` or from lead contract).
5. Add line items.
6. Review totals and adjustments.
7. Create or review quote version.
8. Export customer PDF (`/quotes/:id` — **does not send the quote**).
9. Send PDF manually outside intelliOffice (email, WeChat, etc.).
10. Return to intelliOffice.
11. Mark as Sent (records manual external delivery only).
12. Review delivery log.
13. Review quote timeline.
14. Review order readiness checklist and order input contract.
15. **Do not convert to order until D7** — no Convert to Order action exists in D6.

### D6 safety (mandatory)

- **Export PDF does not send the quote.**
- **Mark as Sent** only records manual external delivery.
- **Order Readiness does not create an order.**
- No production or shipment exists in D6.

```powershell
$env:BACKEND_BASE_URL="http://127.0.0.1:8013"
python scripts/d6_final_closure_check.py
python scripts/d7_1_design_readiness_check.py
```

## D7.2 Customer Orders (from sent quotes)

| URL / API | Purpose |
|-----------|---------|
| `/orders` | Customer order list (D7.2) |
| `/orders/:id` | Order detail, confirm, cancel, timeline |
| `/quotes/:id` | Create Order button (Order Readiness section) |
| `POST /api/v1/orders/from-quote` | Manual order creation |

```powershell
python scripts/d7_2_order_crud_check.py
```

**Safety:** Creating an order does not start production, notify suppliers, or create shipments.

## D7.3 Customer Confirmations

| URL / API | Purpose |
|-----------|---------|
| `/orders/:id` | Confirmation list, add, void |
| `POST /api/v1/orders/{id}/confirm-customer` | Record confirmation |
| `GET /api/v1/orders/{id}/confirmations` | List confirmations |
| `POST /api/v1/orders/{id}/confirmations/{id}/void` | Void confirmation |

```powershell
python scripts/d7_3_customer_confirmation_check.py
```

Recording confirmation does not notify suppliers or start production.

## D7.1 Order Design Review

## D6.6 Quote-to-Order Readiness Gate

D6.6 evaluates whether a **sent quote** is ready for **manual order review** — no order is created.

| URL / API | Purpose |
|-----------|---------|
| `/quotes/:id` | Order Readiness section, checklist, order input contract |
| `GET /api/v1/quotes/{id}/order-readiness` | Full readiness payload |
| `GET /api/v1/quotes/order-readiness-board` | Board summary |

```powershell
python scripts/d6_6_quote_order_readiness_check.py
```

## D6.5 Quote Send Tracking & Delivery Log

D6.5 records **manual quote delivery** — mark-sent creates a delivery log; intelliOffice does not send email or attachments.

| URL / API | Purpose |
|-----------|---------|
| `/quotes/:id` | Mark as Sent form, delivery logs, timeline |
| `POST /api/v1/quotes/{id}/mark-sent` | Record manual delivery |
| `GET /api/v1/quotes/{id}/delivery-logs` | Delivery history |
| `GET /api/v1/quotes/{id}/timeline` | Quote timeline |
| `GET /api/v1/quotes/delivery-due` | Follow-up due queue |

```powershell
python scripts/d6_5_quote_send_tracking_check.py
```

## D6.4 Quote PDF Export

D6.4 adds **customer PDF generation and download** — export does not send the quote or create orders.

| URL / API | Purpose |
|-----------|---------|
| `/quotes/:id` | Export Customer PDF, export list, download |
| `POST /api/v1/quotes/{id}/export-pdf` | Generate PDF |
| `GET /api/v1/quotes/{id}/pdf-exports` | List exports |
| `GET /api/v1/quotes/{id}/pdf-exports/{export_id}/download` | Download file |

```powershell
python scripts/d6_4_quote_pdf_export_check.py
```

Generated PDFs are stored under `backend/storage/quote_pdfs/` (gitignored).

## D6.3 Customer Quotes

D6.3 adds **formal quote records** — manual mark-sent only; PDF export is D6.4.

| URL | Purpose |
|-----|---------|
| `/quotes` | Customer quote list |
| `/quotes/new` | Minimal quote builder |
| `/quotes/:id` | Quote detail, PDF export, mark-ready, mark-sent (manual only) |

```powershell
python scripts/d6_3_quote_crud_check.py
```

## D6.2 Product Catalog & Pricing (Phase 2 foundation)

D6.2 adds **catalog + pricing preview only** — pricing preview does not create quotes.

### One-time setup

```powershell
cd backend
alembic upgrade head
python scripts/seed_quote_catalog.py --apply --confirm
```

### Daily / demo URLs

| URL | Purpose |
|-----|---------|
| `/quote-catalog` | Product catalog list (partner / category filters) |
| `/pricing-preview` | Pricing preview — **does not create a quote** |

### Excel import (local only — never commit workbook)

Place workbook at `local_data/报价模型与格式.xlsx` (gitignored):

```powershell
cd backend
python scripts/import_pricing_excel.py --file "../local_data/报价模型与格式.xlsx" --dry-run
python scripts/import_pricing_excel.py --file "../local_data/报价模型与格式.xlsx" --apply --confirm
python scripts/import_pricing_excel.py --file "../local_data/报价模型与格式.xlsx" --apply --confirm --overwrite
```

### D6.2 smoke

```powershell
$env:BACKEND_BASE_URL="http://127.0.0.1:8013"
python scripts/d6_2_pricing_foundation_check.py
```

**Safety:** Pricing preview returns `quote_created=false` and does not promise inventory, certification, or lead time.

## D5 Final Daily Workflow

D5 is closed — use this as the standard daily operator path:

1. **Import leads** — `/lead-intake` → Preview → Confirm Import
2. **Check completeness** — `/lead-intelligence` → Lead Completeness filters
3. **Research contacts** — Needs Contact Research → Research / Edit drawer
4. **Review product fit** — Product Fit card per lead
5. **Review product opportunity** — Product Opportunity Board filters
6. **Generate pre-quote questions** — Pre-Quote & Sample Prep → Copy brief / questions
7. **Generate product-aware draft** — Product-Aware Draft panel
8. **Send manually outside intelliOffice** — Copy draft → LinkedIn / Email client
9. **Mark as sent** — Record touchpoint in Lead Intelligence
10. **Set follow-up** — Follow-up Scheduler + queue filters
11. **Review timeline** — Outreach History timeline
12. **Quote handoff when ready** — Soft Quote Handoff → Copy brief / supplier notes
13. **Quote input contract when ready** — Quote Input Contract → Copy summary / JSON (Phase 2 handoff only; no quote created)
14. **End-of-day summary** — Dashboard → Copy Summary

**Safety:** All outreach is human-reviewed. Quote handoff and input contract are advisory only — no pricing, inventory, certification, or lead-time commitments.

## Daily Workflow

0. 登录后打开 **Dashboard `/`** → **Daily Operations Command Center**（D5.8 / D5.9）：summary cards、Today Focus、Recent Manual Outreach、Recent Contact Research、Quick Actions
1. 登录 `/login`（seed 凭据见 README，**勿在记录中写密码**）
2. **（新 lead）** 打开 `/lead-intake` → 粘贴或上传 CSV → **Preview** → 检查 missing / duplicate / segment → **Confirm Import**
3. 打开 `/lead-intelligence` → 查看 **Lead Completeness** → 筛选 **Needs Contact Research** → 点击 **Research / Edit** 在 drawer 中补资料（D5.5）
4. 选择 lead → 查看 **Product Fit & Project Opportunity** card（D5.12）：产品方向、quote readiness、discovery questions
5. 查看 **Product Opportunity Board**（D5.13）→ 筛选 High Opportunity / Quote Ready / Lifting Systems
6. 查看 **Pre-Quote & Sample Prep**（D5.14）→ Copy brief / customer questions
8. 查看 **Soft Quote Handoff**（D5.18）→ Copy brief / supplier notes / customer questions
9. 查看 **Quote Input Contract**（D5.19）→ Copy summary / JSON / customer questions
10. 使用 **Product-Aware Draft**（D5.15）→ 按 product focus 生成 discovery 草稿
8. 选择 lead → 查看 **Outreach History** timeline 与 follow-up hint（D5.6）
7. 打开 `/lead-intelligence` → Manual Outreach Queue
8. 查看 **Daily Summary** cards
9. 筛选 **High Priority** → 优先处理
10. 筛选 **Needs First Outreach** → 首次外联
11. 筛选 **Waiting for Reply** → 跟进已发送未回复
12. 选择 lead → **Generate Draft**
13. **Copy Draft** → 在 LinkedIn / Email **系统外**粘贴发送
14. 回到系统 → **Mark as Sent**（仅记录，不自动发送）
15. 确认 **Outreach History** timeline 已更新
16. 在 **Follow-up Scheduler** 设置下次跟进日期（D5.7）
17. 使用 **Due queue filters** 查看 Overdue / Due Today / Due Soon
18. 确认 **next action** 已更新
19. 收工时 Dashboard **End-of-Day Summary** → **Copy Summary**（D5.10）
20. 每日结束（可选 CLI）：

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8010"   # if using 8010
python scripts/daily_outreach_summary.py
python scripts/daily_follow_up_summary.py
python scripts/daily_work_summary.py
```

## Useful URLs

| URL | Purpose |
|-----|---------|
| `/` | Dashboard · Daily Operations Command Center（D5.8） |
| `/login` | 登录 |
| `/lead-intake` | CSV lead 导入与批量预检（D5.3） |
| `/lead-intelligence` | 每日跟进工作台 |
| `/system-health` | 系统与 Portal readiness |
| `/portal-consumer-mock` | 模拟外部 Portal 只读消费 |
| `/companies` | CRM 公司列表 |
| `/contacts` | 联系人 |

## Useful Scripts

| Script | Purpose |
|--------|---------|
| `check_backend_runtime.py` | 后端是否可达 |
| `check_database_config.py` | 数据库与迁移 |
| `config_readiness_check.py` | 部署前配置一致性 |
| `smoke_demo_ready.py` | Demo 数据 smoke |
| `pilot_workflow_check.py` | Pilot 工作流 |
| `outreach_queue_check.py` | 外联队列 |
| `real_lead_batch_check.py` | 真实批次 pilot |
| `daily_outreach_summary.py` | 每日只读摘要 |
| `daily_follow_up_summary.py` | 每日 follow-up 摘要（D5.7） |
| `daily_ops_summary_check.py` | Daily Operations API smoke（D5.8） |
| `daily_work_summary.py` | End-of-day work summary CLI（D5.10） |
| `dev_runtime_doctor.py` | 统一 runtime 诊断（D5.11） |
| `smoke_all_d5.py` | 一键 D5.x smoke（D5.11） |
| `product_opportunity_check.py` | Product opportunity board smoke（D5.13） |
| `pre_quote_brief_check.py` | Pre-quote brief smoke（D5.14） |
| `product_aware_draft_check.py` | Product-aware draft smoke（D5.15） |
| `d5_16_real_lead_uat_check.py` | Real lead UAT API coverage（D5.16） |
| `d5_17_rule_tuning_check.py` | Lifting / product rule tuning regression（D5.17） |
| `quote_handoff_check.py` | Soft quote handoff smoke（D5.18） |
| `d5_19_quote_input_contract_check.py` | Quote input contract UAT smoke（D5.19） |
| `seed_quote_catalog.py` | D6.2 demo catalog seed |
| `import_pricing_excel.py` | D6.2 / D6.2.1 Excel import (local_data only) |
| `d6_2_1_excel_import_check.py` | D6.2.1 Excel import alignment smoke |
| `d6_3_quote_crud_check.py` | D6.3 quote CRUD smoke |
| `d6_4_quote_pdf_export_check.py` | D6.4 quote PDF export smoke |
| `d6_5_quote_send_tracking_check.py` | D6.5 send tracking smoke |
| `d6_6_quote_order_readiness_check.py` | D6.6 order readiness smoke |
| `d6_final_closure_check.py` | D6.7 final closure gate |
| `d7_3_customer_confirmation_check.py` | D7.3 customer confirmation smoke |
| `d6_2_pricing_foundation_check.py` | D6.2 pricing foundation smoke |
| `portal_readiness_check.py` | Portal v1 端点 |
| `portal_consumer_check.py` | 外部 Portal 契约 |

## Safety Rules

- 所有草稿 **人工审核** 后再发送
- **不自动发送** 任何消息
- **不抓 LinkedIn**、不绕过平台限制
- **不提交** `local_data/` 私有 CSV
- **不提交** `.env` / token / secret
- **不提交** 未打码截图

## Troubleshooting

| 问题 | 处理 |
|------|------|
| 前端 API 404 / 502 | 确认 backend 运行；`BACKEND_BASE_URL` 与 `VITE_API_PROXY_TARGET` 端口一致 |
| 8000 被占用 | 改用 8010，见 [dev_guide.md](dev_guide.md) § Changing backend port |
| migration pending | `cd backend && alembic upgrade head` |
| Portal summary 空 | 确认 DB 有 leads；backend 为新代码实例 |

## Further Reading

- [D5 Final MVP Release](releases/d5_final_mvp_release_20260523.md)
- [D5 Final Closure Record](records/d5_final_closure_20260523.md)
- [D5 Capability Map](architecture/d5_capability_map.md)
- [Phase 2 Quote Readiness Brief](phase2/quote_module_readiness_brief.md)
- [D5.2 Release Note](releases/d5_2_internal_mvp_release_20260523.md)
- [Deployment Readiness Checklist](deployment_readiness_checklist.md)
- [D5.2.12 Screenshot Demo Proof](records/d5_2_12_browser_screenshots_demo_proof_20260523.md)
- [Manual A-Domain Test Plan](manual_a_domain_test_plan.md)
