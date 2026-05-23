# D5.19 Soft Quote Handoff UAT & Quote Input Contract

## Goal

验证 Soft Quote Handoff（D5.18）是否足以承接未来正式 Quote 模块，并定义只读 **Quote Input Contract** 作为 Phase 2 输入边界。本阶段不创建 quote record、不生成价格、不改数据库 schema。

## UAT Leads

脱敏结论表（无邮箱/电话/私人信息）：

| Company | Route | Readiness | Result |
|---|---|---|---|
| SWC Office Furniture | HOSUN lifting systems | Needs more customer information | Contract generated; adjustable desk frames scope; missing qty/timeline |
| Yony's Office Furniture | HOSUN lifting systems | Needs more customer information | Lifting / project interest; clarification questions present |
| Jefferson Group | Project supply | Needs more customer information | Project supply route; missing delivery / volume |
| Dancker | Project supply | Needs more customer information | FF&E / project supply scope |
| Human Active Technology | HOSUN lifting systems | Needs more customer information | Lifting / OEM potential flagged |
| Campus Learning Furniture | JOOBOO education | Needs more customer information | Education route; sample readiness noted |
| Metro Lab Workspace Co | Medical / lab workspace | Not quote ready / needs info | Medical workspace route |
| Transfer Enterprises | — | Not quote ready | Needs research; not quote-ready boundary respected |
| Commercial Furniture Resource | HOSUN lifting systems | Needs more customer information | General office / adjustable frame intro |
| OCI Office Concepts | HOSUN lifting systems | Needs more customer information | Lifting / project potential |

## Contract Fields

- **customer** — company name, contact name (if known), contact method availability
- **product_intent** — product focus, project type, sample/quote readiness
- **known_requirements** — only explicitly detected values; otherwise null
- **missing_requirements** — checklist from handoff
- **recommended_questions** — customer clarification prompts
- **supplier_preparation_notes** — internal prep only
- **copyable_json** — Phase 2 handoff payload (no quote record)
- **copyable_handoff_summary** — human-readable internal summary
- **safety** — quote_created/pricing/inventory/certification/lead-time/automatic_sending all false

## Findings

- **接近 quote draft**：少数 lead 在补齐 quantity、product type、delivery 后可达 `ready_for_phase2_quote_draft`（仍不自动报价）。
- **需客户补充**：多数 dealer / project lead 处于 `needs_more_customer_info`，missing requirements 3–6 项。
- **不适合 quote**：Transfer Enterprises 等 not_ready lead 正确落在 `not_quote_ready`。
- **Catalog / SKU**：当前 contract 依赖 product fit + handoff 文本；正式 Quote 模块仍需 SKU / catalog 结构化数据（Phase 2）。

## Safety

- no quote created
- no pricing generated
- no inventory promise
- no certification promise
- no lead-time promise
- no automatic sending

## Acceptance Criteria

- [x] `GET /api/a-domain/leads/{lead_id}/quote-input-contract` 可用
- [x] `GET /api/a-domain/quote-input-contract-board` 可用
- [x] copyable JSON 合法且可复制
- [x] UAT route coverage（HOSUN / project / education / not_ready）
- [x] `d5_19_quote_input_contract_check.py` PASS
- [x] pytest / frontend vitest PASS
- [x] no DB migration

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/a-domain/leads/{lead_id}/quote-input-contract` | Single-lead quote input contract |
| GET | `/api/a-domain/quote-input-contract-board` | Board summary + rows |
