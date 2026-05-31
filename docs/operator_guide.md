# intelliOffice Operator Guide

**Audience:** 内部运营 / 客户开发 / 演示人员  
**Release:** D5 Final MVP (closed) · **Not Phase 2**

## Daily Startup

### Recommended - port 8014 (D7.6+ validation default)

Use `8014` for D7.6+ shipment/portal/staging validation and current D8 handoff checks:

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8014
```

Align scripts and frontend proxy:

```powershell
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"
```

Or set `frontend/.env.local` (gitignored):

```env
VITE_API_PROXY_TARGET=http://127.0.0.1:8014
```

### Legacy - port 8010 (D5/D6 local dev)

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

**Do not run multiple uvicorn instances with different code versions.** If 8014 or 8010 is occupied but `/health` fails, see [Runtime Startup Routine](#runtime-startup-routine).

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
2. Set `BACKEND_BASE_URL` / `VITE_API_PROXY_TARGET` to `http://127.0.0.1:8014` for D7.6+ and D8 validation.
3. Start backend **8014** as a single instance on the latest code.
4. 启动 frontend：`cd frontend; npm run dev`
5. 运行 `python scripts/dev_runtime_doctor.py`
6. 运行 `python scripts/smoke_all_d5.py`

**Stale port 8014 or 8010** (occupied but `/health` fails):

```powershell
netstat -ano | findstr :8014
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

## D7.4 Partner Splits & Supplier Confirmations

| URL / API | Purpose |
|-----------|---------|
| `/orders/:id` | Partner splits, ensure, supplier confirmation |
| `POST /api/v1/orders/{id}/partner-splits/ensure` | Generate/update splits by partner |
| `GET /api/v1/orders/{id}/partner-splits` | List splits |
| `POST /api/v1/orders/{id}/partner-splits/{id}/supplier-confirmations` | Record supplier confirmation |
| `GET /api/v1/orders/{id}/supplier-confirmations` | List all supplier confirmations |

```powershell
python scripts/d7_4_partner_supplier_check.py
```

Supplier confirmation is manually recorded only; it does not notify suppliers or start production.

## D7.5 Production Milestones

| URL / API | Purpose |
|-----------|---------|
| `/orders/:id` | Production summary, milestones per split |
| `POST /api/v1/orders/{id}/partner-splits/{id}/production-milestones/ensure` | Generate milestones from template |
| `GET /api/v1/orders/{id}/production-milestones` | List all milestones |
| `PATCH /api/v1/orders/{id}/production-milestones/{id}` | Update milestone status/dates |

```powershell
python scripts/d7_5_production_milestone_check.py
```

Milestones are internal planning records; they do not create shipments or notify suppliers/customers.

## D7.5.1 Existing Cloud Portal Integration Review

Review-only stage: maps the **already-deployed HOSUN & intelli cloud customer portal** to PartnerOS as source of truth. No new migrations, APIs, or portal UI in this repo.

| Document | Purpose |
|----------|---------|
| [d7_5_1_existing_cloud_portal_integration_review.md](phase3/d7_5_1_existing_cloud_portal_integration_review.md) | Capability mapping, architecture, API boundary proposal |

```powershell
python scripts/d7_5_1_portal_integration_review_check.py
```

**Judgment:** retain existing cloud portal; integrate via the implemented D7.7 Portal Bridge API.

## D7.6 Shipment Tracking

| URL / API | Purpose |
|-----------|---------|
| `/orders/:id` | Shipment Plans list, create form, status update, customer-visible preview |
| `POST /api/v1/orders/{id}/shipment-plans` | Create manual shipment plan |
| `GET /api/v1/orders/{id}/shipment-plans` | List shipment plans |
| `PATCH /api/v1/orders/{id}/shipment-plans/{plan_id}` | Update fields or status |

```powershell
python scripts/d7_6_shipment_tracking_check.py
```

Shipment plans are manual logistics records only. They do not call carriers, send webhooks or email, notify suppliers/customers, or automatically change the order to shipped/delivered.

## D7.7 Customer Portal Bridge

PartnerOS is the internal source of truth. `service.intelli-opus.com` remains the customer-facing portal.

| URL / API | Purpose |
|-----------|---------|
| `GET /api/v1/portal/customer/products` | Customer-visible products |
| `GET /api/v1/portal/customer/orders` | Customer-visible orders |
| `GET /api/v1/portal/customer/orders/{id}` | Customer-visible order detail |
| `GET /api/v1/portal/customer/orders/{id}/production` | Production milestone view |
| `GET /api/v1/portal/customer/orders/{id}/shipment` | Shipment plan view |
| `GET /api/v1/portal/customer/orders/{id}/resources` | Customer-safe resource metadata |
| `POST /api/v1/portal/customer/feedback` | Feedback ticket intake |

```powershell
python scripts/d7_7_portal_bridge_check.py
```

Default bridge config is disabled and token-required. Real tokens must live in `.env` only. Portal bridge responses must not expose internal costs, margins, supplier private notes, storage keys, backend paths, or tokens.

## D7.8 Service Portal UAT & Feedback Operations

| URL / API | Purpose |
|-----------|---------|
| `/portal-customer-bridge` | Internal Portal API UAT page; masked token entry, endpoint checks, TEST feedback |
| `/feedback-tickets` | Internal feedback operations console |
| `GET /api/v1/portal/customer/readiness` | Internal readiness summary; no token value returned |
| `GET /api/v1/feedback-tickets` | List feedback tickets |
| `GET /api/v1/feedback-tickets/{id}` | Feedback ticket detail |
| `PATCH /api/v1/feedback-tickets/{id}` | Update status, priority, owner, response summary |

```powershell
python scripts/d7_8_portal_live_integration_check.py
```

Feedback status flow is `new -> in_review -> responded -> resolved -> closed`. The console records internal handling only; it does not send email, notify customers, upload attachments, or promise an SLA. Staging feedback must include `TEST` in the subject or message.

## D7.9 Resource Center / Document Center

| URL / API | Purpose |
|-----------|---------|
| `/orders/:id` | Resource Center block for upload, publish, unpublish, archive |
| `POST /api/v1/orders/{id}/resources` | Create an order resource from an uploaded file |
| `GET /api/v1/orders/{id}/resources` | Internal resource list |
| `PATCH /api/v1/orders/{id}/resources/{resource_id}` | Update resource metadata or visibility |
| `GET /api/v1/portal/customer/orders/{id}/resources` | Customer-visible resource metadata + signed URL |
| `GET /api/v1/portal/customer/resources/{resource_id}/download` | Signed customer download |

```powershell
python scripts/d7_9_resource_center_check.py
```

Only resources with `status=published` and `customer_visible=true` appear in the Portal bridge. Resource Center does not send email, notify customers, create permanent public URLs, or expose storage keys/backend paths.

## D8.1 RBAC / Scoped Access

Internal users now resolve to explicit permissions from their role. Admin receives `*`, operator-style roles can write orders/resources/feedback, and Viewer can read but cannot perform operational writes.

| Area | Read | Write |
|------|------|-------|
| Orders | `orders:read` | `orders:write` |
| Order resources | `resources:read` | `resources:write` |
| Feedback tickets | `feedback:read` | `feedback:write` |
| Market response intelligence | `market:read` | n/a |
| Portal readiness | `portal:readiness` | n/a |

```powershell
python scripts/d8_1_rbac_scoped_access_check.py
```

`/api/auth/me` returns `role_name` and `permissions` for future UI control hiding. Customer portal bridge routes remain token-scoped and do not expose internal-only fields.

## D8.2 Runtime Hardening

D8.2 adds a read-only runtime gate for local and staging-like environments.

```powershell
cd backend
python scripts/d8_2_runtime_hardening_check.py
```

Use strict staging mode before service portal cutover:

```powershell
$env:D8_2_STRICT_STAGING="true"
python scripts/d8_2_runtime_hardening_check.py
```

The check covers runtime mode, `SECRET_KEY`, `PUBLIC_BASE_URL`, DB connectivity, Alembic head, proxy alignment, portal token/CORS configuration, and gitignore coverage for local storage paths. It never prints secret or token values.

## D8.3 Service Portal Staging Contract

D8.3 adds an HTTP contract runner for the existing service portal staging integration. It checks token rejection, CORS preflight, customer-safe products/orders/production/shipment/resources reads, and forbidden field leakage.

```powershell
cd backend
$env:BACKEND_BASE_URL="https://<partneros-staging-backend-origin>"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<portal-server-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
python scripts/d8_3_service_portal_staging_check.py
```

The runner does not create feedback unless `D8_3_CREATE_TEST_FEEDBACK=true` is set. Keep all staging feedback subjects/messages prefixed with `TEST`.

## D8.4 Partner Operations Dashboard

D8.4 adds a read-only partner execution view at `/partner-operations`.

| Area | Signal |
|------|--------|
| Workload | partner split count, order count, line item count, subtotal by currency |
| Supplier | confirmation status counts |
| Production | milestone status counts, delayed and blocked counts |
| Shipment | shipment status counts, active shipment count |
| Risk | open supplier confirmation, delayed/blocked production, ready-to-ship without shipment |

```powershell
cd backend
python scripts/d8_4_partner_operations_check.py
```

The dashboard does not notify suppliers or customers, create shipments, change order status, or rank partners with hard-coded brand preference.

## D8.5 Market Response Intelligence

D8.5 upgrades `/market-intelligence` into a read-only response intelligence board.

| Area | Signal |
|------|--------|
| Feedback | inferred tags, short summaries, status and priority counts |
| Win-loss | quote status, order conversion, category-level wins/losses |
| Demand | market, feedback, quote, and order signals by product category |
| Product gaps | missing product parameters weighted by demand signals |
| Recommendations | advisory AI-assisted actions requiring human review |

```powershell
cd backend
python scripts/d8_5_market_response_check.py
```

The board does not execute AI actions, notify customers or suppliers, send email/webhooks, change quote or order status, or mutate partner selection.

## D8 Integration Hardening

D8 adds a bridge/deployment contract gate for D7.7-D8.5.

```powershell
cd backend
python scripts/d8_integration_hardening_check.py
```

Use it before staging or cloud coordination to confirm service portal CORS, no tracked local secrets/storage, portal readiness token safety, D8.4 read-only behavior, D8.5 advisory-only behavior, and forbidden field filtering. It does not deploy to `service.intelli-opus.com`, update nginx, print tokens, send notifications, or mutate business records.

For real staging evidence:

```powershell
cd backend
$env:BACKEND_BASE_URL="https://<partneros-staging-backend-origin>"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<portal-server-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
python scripts/d8_strict_staging_evidence_check.py
```

This strict check validates HTTPS, token rejection, CORS, readiness/manifest envelopes, customer portal product/order reads, optional order subresources, and forbidden-field leakage.
Add `--evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json` when you need a redacted evidence artifact for handoff or audit.
Add `--gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md` to generate a follow-up register for failed checks.

Before sharing the staging package, use [D8 Staging Handoff Bundle](phase3/d8_staging_handoff_bundle.md) and verify it with:

```powershell
python scripts/staging_evidence_boundary_check.py
python scripts/d8_staging_handoff_bundle_check.py
python scripts/d8_staging_execution_pack_check.py
```

Use [D8 Staging Operator Runbook](phase3/d8_staging_operator_runbook.md) for the exact sequence from `READY_FOR_STAGING_HANDOFF` through input preflight, strict evidence, records review, and production-coordination state:

```powershell
python scripts/d8_staging_operator_runbook_check.py
```

To rehearse strict staging command order against a local backend only, use [D8 Local Staging Rehearsal](phase3/d8_local_staging_rehearsal.md) and verify it with:

```powershell
python scripts/d8_local_staging_rehearsal_check.py
```

Local rehearsal output is not staging proof and must not change readiness to `STAGING_VALIDATED` or `STAGING_GAPS_OPEN`.
If local rehearsal evidence is ever saved by mistake, `d8_production_coordination_check.py` reports `WAITING_FOR_REAL_STAGING_EVIDENCE`; replace it with strict staging evidence from real staging values before production coordination.

After private staging values are available, but before running strict evidence, run:

```powershell
python scripts/d8_staging_input_preflight_check.py
```

If the real staging URL, portal token, portal origin, deployed commit, or TEST fixture scope is not available yet, use [D8 Staging Access Request](phase3/d8_staging_access_request.md) and verify it with:

```powershell
python scripts/d8_staging_access_request_check.py
```

When operations replies, use [D8 Staging Operator Response Intake](phase3/d8_staging_operator_response_intake.md) to keep token values, raw payloads, customer files, and unsafe artifacts out of the repo:

```powershell
python scripts/d8_staging_operator_response_intake_check.py
```

If strict staging evidence fails, use [D8 Staging Gap Triage](phase3/d8_staging_gap_triage.md) and verify the owner/status/rerun loop with:

```powershell
python scripts/d8_staging_gap_triage_check.py
```

Before committing staging records, run:

```powershell
python scripts/d8_staging_records_check.py
```

Keep D8 staging artifacts under canonical `docs/records/d8_*_YYYYMMDD` names. The record gate verifies redaction metadata, token placeholders, strict evidence schema, and matching gap registers for failed evidence. Saved strict staging evidence shows a remote backend as `https://<redacted-backend>` while the real `BACKEND_BASE_URL` stays in the private operator channel.

After records pass, review the saved evidence state with:

```powershell
python scripts/d8_staging_evidence_review_check.py
```

This reports `WAITING_FOR_STAGING_EVIDENCE`, `READY_FOR_PRODUCTION_COORDINATION_REVIEW`, or `STAGING_GAPS_REQUIRE_TRIAGE`. It is a review gate only; it does not call staging or authorize deployment.

After `python scripts/d8_readiness_audit.py` reports `STAGING_VALIDATED`, run:

```powershell
python scripts/d8_production_coordination_check.py
python scripts/d8_production_coordination_runbook_check.py
```

These checks keep production coordination separate from deployment. They confirm the Go / No-Go plan, rollback boundary, redacted evidence policy, and the rule that PartnerOS does not modify `service.intelli-opus.com`, nginx, notifications, carrier APIs, or business statuses from this repository.

The next planned operating loop is D9:

```powershell
python scripts/d9_post_launch_plan_check.py
python scripts/d9_operating_execution_pack_check.py
python scripts/d9_operating_loop_kickoff_check.py
python scripts/d9_1_operating_health_review_check.py
python scripts/d9_2_order_operations_loop_check.py
python scripts/d9_3_market_response_loop_check.py
python scripts/d9_4_improvement_backlog_check.py
```

D9 starts only after `STAGING_VALIDATED`, `READY_FOR_PRODUCTION_COORDINATION_REVIEW`, production coordination, and the human Go / No-Go handoff. If that handoff is committed, use the redacted `docs/records/d8_production_go_no_go_YYYYMMDD.md` record. D9 keeps Portal feedback, order operations, Market response intelligence, and improvement backlog under human review. The execution pack runs the full D9 gate set, including the saved evidence review check; the kickoff check defines the first redacted D9 operating review session; D9.1 defines health signals; D9.2 defines order operations follow-up; D9.3 defines advisory market response signals; D9.4 converts repeated gaps into reviewed backlog candidates without automatic ticket creation.

Before committing D9 operating review records, run:

```powershell
python scripts/d9_operating_records_check.py
```

Use canonical `docs/records/d9_*_YYYYMMDD.md` names and store redacted summaries only.

After changing Phase 3 stage docs or gates, run:

```powershell
python scripts/phase3_roadmap_check.py
```

This keeps the D7-D9 roadmap, dependency graph, related docs, and manual-action safety boundaries aligned.

For the source-derived project plan, run:

```powershell
python scripts/ie_auto_project_plan_check.py
```

This keeps product positioning, partner neutrality, operating lifecycle, current state mapping, immediate staging brief, and D8/D9 references aligned with `docs/phase3/ie_auto_project_plan.md`.

For a single local planning gate, run:

```powershell
python scripts/project_execution_chain_gate_check.py
python scripts/staging_evidence_boundary_check.py
python scripts/project_execution_chain_check.py
```

This aggregates the IE Auto plan, Phase 3 roadmap, D8 matrix, readiness audit, local staging rehearsal, operator runbook, evidence review, production coordination, production coordination runbook, D9 plan, and D9 records checks.
See [Project Execution Chain Gate](phase3/project_execution_chain_gate.md) for the state meanings and safety boundaries.

For a concise current-stage summary:

```powershell
python scripts/project_execution_status.py
```

Before claiming the project-planning objective is complete, run the acceptance audit:

```powershell
python scripts/project_execution_acceptance_audit_check.py
```

To preserve a redacted local planning report:

```powershell
python scripts/project_execution_chain_check.py --report-markdown ../docs/records/project_execution_chain_YYYYMMDD.md
```

The report records only gate names, pass/fail state, and one-line summaries.

Before committing generated project execution reports, run:

```powershell
python scripts/project_execution_records_check.py
```

After changing this operator guide or the D8/D9 handoff gates, run:

```powershell
python scripts/agent_guide_check.py
python scripts/product_vision_check.py
python scripts/desktop_target_architecture_check.py
python scripts/runtime_modes_check.py
python scripts/database_lifecycle_doc_check.py
python scripts/desktop_packaging_docs_check.py
python scripts/web_to_desktop_migration_doc_check.py
python scripts/desktop_transition_roadmap_check.py
python scripts/project_reorientation_summary_check.py
python scripts/dev_guide_check.py
python scripts/integrated_backend_standards_check.py
python scripts/lead_intelligence_docs_check.py
python scripts/manual_a_domain_test_plan_check.py
python scripts/codex_skill_pack_check.py
python scripts/activity_actions_doc_check.py
python scripts/deployment_readiness_checklist_check.py
python scripts/testing_guide_check.py
python scripts/testing_summary_d5_2_check.py
python scripts/operator_guide_check.py
python scripts/project_execution_chain_gate_check.py
```

This keeps the operator instructions, testing guide, and deployment readiness checklist aligned with `READY_FOR_STAGING_HANDOFF`, strict staging evidence review, production coordination, D9 gates, and manual-only safety boundaries.

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
| `d7_5_production_milestone_check.py` | D7.5 production milestone smoke |
| `d7_5_1_portal_integration_review_check.py` | D7.5.1 cloud portal integration review gate |
| `d7_6_shipment_tracking_check.py` | D7.6 shipment tracking smoke |
| `d7_7_portal_bridge_check.py` | D7.7 customer portal bridge smoke |
| `d7_4_partner_supplier_check.py` | D7.4 partner split & supplier confirmation smoke |
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
| Backend port occupied | Prefer the current `8014` validation port and keep `BACKEND_BASE_URL` / `VITE_API_PROXY_TARGET` aligned; see [dev_guide.md](dev_guide.md) |
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
