# PartnerOS Agent Guide

## 1. Mission

PartnerOS is the internal operating system for intelliOffice's multi-brand U.S.-facing agency business. It connects customer development, product and partner management, interval quoting, customer ordering, production and shipment tracking, feedback, and commercial intelligence into one operational source of truth.

The primary product reference is:

- `docs/product/partneros_prd.md`

Agents must use the PRD as the product direction before making feature or architecture decisions.

## 2. Product Priority

The first priority is internal team efficiency.

Every meaningful change should improve at least one of these outcomes:

- operators can discover, organize, and follow up with customers more effectively;
- quote creation and PDF delivery are more accurate and professional;
- products and partners are governed through a clean multi-brand model;
- customers can browse, order, track, and give feedback through the customer portal;
- orders, production, shipment, and feedback become easier to operate;
- commercial intelligence helps the team decide which customers to pursue, which products to sell, and which quote experience to reuse;
- the system becomes more reliable for local-server Docker deployment.

Avoid low-value changes that only add decorative UI, duplicate navigation, raw status dumps, or isolated documents without improving the operating loop.

## 3. Product Model

The long-term product model is:

```text
Partner -> Product family -> Product model -> Configuration options -> Quote intervals -> Order line item
```

HOSUN, JOOBOO, and future partners are peer manufacturing partners. Do not hard-code HOSUN as the main brand or assume any partner has special status unless the task explicitly requires a temporary migration rule.

Current partner expectations:

- HOSUN: lifting systems, desk frames, desk legs, lifting columns, heavy-duty supply, hand controls, color swatch sample set, SKU governance, cost/weight/shipping/margin pricing data.
- JOOBOO: education furniture, school desks and chairs, project furniture, brochures/catalog resources, project procurement attributes.
- Future partners: must enter through the same partner/product structure.

## 4. Quote System Rules

The quote system is a priority module.

Quotes are interval-based. Do not design quotes around a single input quantity or reference total. A customer quote must show the selected products and each product's full quantity interval table.

Current customer-visible quote output should focus on:

- Quantity;
- FOB Unit Price;
- DDP Unit Price.

Quote logic must support:

- automatic quote number sequence;
- quote drafts and archive history;
- selecting existing customers/contacts or creating new ones during quote creation;
- no duplicate product lines in one quote;
- product-specific target margin;
- global ocean freight assumption, currently RMB 22/kg unless updated;
- real-time or refreshable USD/CNY exchange rate, not a stale spreadsheet value;
- professional PDF export;
- PDF deletion or retention management;
- editable terms and instructions;
- no automatic email sending in the current stage.

Never expose internal cost, margin, cost breakdown, supplier private notes, or pricing assumptions to customer-facing APIs or customer UI.

## 5. Customer Portal Rules

The customer-facing portal is separate from the admin system. It should be clean, partner-neutral, and customer-safe.

Customer portal scope:

- public landing pages;
- product browsing;
- sample inventory;
- resource center;
- login;
- customer order creation;
- order dashboard;
- order detail and tracking;
- production/shipment summary;
- feedback submission.

Do not expose internal operations, readiness gates, margin, cost, supplier notes, internal scoring, raw database IDs, backend file paths, or tokens.

Track Order should not be a redundant standalone top-level experience when the same function belongs in the customer order dashboard.

## 6. Admin System Rules

The admin frontend should use Chinese operating language by default. English is acceptable for product names, customer names, quote PDF customer-facing output, and technical identifiers that should not be translated.

Admin pages should not dump raw enums or backend attributes directly into the UI. Translate status and operational fields into language the business team can understand.

Required admin areas include:

- dashboard / workbench;
- customer development;
- companies and contacts;
- growth operations;
- products and partners;
- quote catalog;
- quote creation and quote detail;
- orders and order detail;
- production and logistics;
- feedback tickets;
- market/commercial intelligence;
- resource management;
- system health and deployment readiness.

## 7. Commercial Intelligence Rules

Commercial intelligence is a near-term product capability, not an optional long-term report.

Prioritize features that help answer:

- Which customers are most worth following?
- Which products are worth selling?
- Which quote experience should be reused?

Support structures may include:

- win/loss capture;
- customer decision factors;
- product factors;
- partner factors;
- quote playbook;
- repeat business recommendations;
- product/partner commercial playbooks;
- Account 360 commercial memory.

All intelligence outputs must be internal recommendations. Do not invent real customer feedback, partner feedback, sign-off, credentials, or external evidence. Do not automatically change quote, order, or opportunity status.

## 8. Runtime

Backend:

- FastAPI from `backend/`.
- Preferred local backend smoke port: `8014`.
- Health endpoint: `http://127.0.0.1:8014/health`.

Admin frontend:

- Vue/Vite from `frontend/`.
- Typical dev target: `http://127.0.0.1:5173`.
- Use `VITE_API_PROXY_TARGET=http://127.0.0.1:8014`.

Customer/local portal:

- Static/customer site assets under `frontend/public/site`, `frontend/public/css`, and related public assets.
- Local-server Docker frontend may run on `http://127.0.0.1:8080`.

Database:

- PostgreSQL via Docker.
- Existing compose target commonly uses `127.0.0.1:5435`.

Local-server deployment is the current deployment direction. Windows desktop packaging may remain a future option, but it is not the active priority.

## 9. Safety Rules

Never commit or expose:

- `.env`;
- real tokens or API keys;
- `local_data/`;
- `backend/storage/`;
- uploads containing customer/private files;
- generated logs;
- raw customer files unless explicitly approved;
- backend file paths;
- storage keys.

Never expose customer-facing data that includes:

- internal cost;
- margin;
- pricing breakdowns;
- cost snapshots;
- supplier private notes;
- internal scoring;
- internal-only comments;
- raw unsafe database IDs.

Never perform these actions unless a future task explicitly adds safety gates:

- automatic email sending;
- SMS sending;
- LinkedIn sending;
- customer notifications;
- supplier notifications;
- carrier API calls;
- payment actions;
- automatic order status changes to shipped/delivered;
- automatic quote/order/opportunity state mutation from background logic.

Do not write `STAGING_VALIDATED` unless real staging credentials, real staging smoke evidence, business sign-off, and security sign-off exist.

## 10. Development Rules

Before changing code, identify the domain:

```text
Domain:
Business goal:
Internal or customer-facing:
Customer-visible fields:
Database change:
Manual-only safety impact:
Tests or smoke checks:
```

Prefer additive changes over broad rewrites. Preserve existing routes unless a task explicitly asks for a migration.

Keep admin and customer portal behavior separate:

- admin routes may show internal data to authenticated administrators;
- customer-facing routes must use explicit whitelists.

For UI work:

- avoid duplicate navigation;
- avoid raw enum/status labels;
- avoid excessive demo data;
- make operator-facing UI Chinese-first;
- make customer-facing pages professional, concise, and partner-neutral;
- do not use HOSUN product imagery as generic homepage branding.

For product/catalog work:

- maintain product governance;
- avoid demo-sample pollution in real catalog views;
- preserve image consistency;
- keep SKU and product-family rules explicit and testable.

## 11. Validation

Run the smallest relevant validation set for the change. Do not claim broad validation if only a narrow check was run.

Backend common checks:

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
python scripts/dev_runtime_doctor.py
python -m pytest -q
```

Frontend common checks:

```powershell
cd frontend
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"
npm run test -- --run
npm run build
```

Customer portal checks, when relevant:

```powershell
python scripts/customer_portal_site_check.py
cd frontend
npm run site:check
```

Quote checks, when relevant:

```powershell
cd backend
python scripts/d6_4_quote_pdf_export_check.py
python -m pytest tests/test_api_v1_quotes.py tests/test_api_v1_quote_pdf.py tests/test_pdf_generator.py -q
```

Product/catalog checks, when relevant:

```powershell
cd backend
python scripts/hosun_catalog_governance_check.py
python -m pytest tests/test_hosun_product_catalog_import.py tests/test_hosun_classification_sync.py tests/test_quote_catalog_enrichment.py -q
```

Docker/local-server checks, when relevant:

```powershell
docker compose ps
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8014/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/
```

## 12. Git And Commit Hygiene

The worktree may contain unrelated user changes. Do not revert or overwrite them.

Do not use broad staging commands unless explicitly requested. Prefer explicit paths:

```powershell
git add path/to/file1 path/to/file2
```

Do not commit:

- `.env`;
- tokens;
- local storage;
- generated private PDFs unless explicitly approved;
- unrelated `docs/activity_actions.md` changes;
- user-provided source files that are not meant for the repo.

Only commit after relevant checks pass and the user asked for commit/push or the task explicitly includes commit instructions.

## 13. Decision Standard For Agents

When in doubt, choose the option that makes the system better at the full operating loop:

```text
customer discovery -> product fit -> quote -> customer order -> production/logistics -> feedback -> commercial memory -> next action
```

If a change does not improve this loop, reduce operational confusion, strengthen safety, or make deployment more reliable, question whether it should be done.

## 14. Operational Runtime & Validation (D7–D9)

PartnerOS remains the internal source of truth for operators. Customer portal integration targets `service.intelli-opus.com` through explicit staging handoff; do not mark `STAGING_VALIDATED` without real staging credentials and evidence.

Current stage: `READY_FOR_STAGING_HANDOFF`. Real strict staging evidence may remain `WAITING_FOR_REAL_STAGING_EVIDENCE` until operators replace local rehearsal output. Production coordination requires `READY_FOR_PRODUCTION_COORDINATION_REVIEW` and a human Go/No-Go handoff before D9 operating loops.

D7 is closed through D7.9 (orders, production milestones, shipment tracking, portal bridge, resource center, feedback tickets). Feedback tickets do not auto-reply, auto-notify suppliers, or mutate order/shipment status.

### Runtime defaults

- Preferred local backend smoke port: `8014` for D7.6+ and D8 handoff validation
- Docker Postgres: `127.0.0.1:5435`
- Admin frontend proxy: `VITE_API_PROXY_TARGET=http://127.0.0.1:8014`

### Safety boundaries (never bypass)

- Never commit `.env`, `local_data/`, `backend/storage/`, tokens, or customer private uploads
- Never expose internal cost, margin, pricing breakdowns, supplier private notes, or internal scoring to customer-facing APIs/UI
- Do not auto-send email/webhooks, SMS, LinkedIn messages, or customer/supplier notifications
- Do not call carrier APIs or automatically change order status to shipped/delivered from background logic

### Common validation commands

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
python -m pytest -q
python scripts/dev_runtime_doctor.py
python scripts/smoke_all_d5.py
python scripts/d7_5_production_milestone_check.py
python scripts/d7_6_shipment_tracking_check.py
python scripts/d7_7_portal_bridge_check.py
python scripts/readme_check.py
python scripts/deployment_readiness_checklist_check.py
python scripts/testing_guide_check.py
python scripts/staging_evidence_boundary_check.py
python scripts/operator_guide_check.py
python scripts/codex_skill_pack_check.py
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
python scripts/project_execution_status.py
python scripts/d8_staging_execution_pack_check.py
python scripts/d9_operating_execution_pack_check.py
python scripts/project_execution_acceptance_audit_check.py

cd ../frontend
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"
npm run test -- --run
```

Commit and push only after the requested checks pass.
