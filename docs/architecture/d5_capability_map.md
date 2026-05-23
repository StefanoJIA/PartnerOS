# D5 Capability Map

**Status:** D5 closed · **Date:** 2026-05-23

This map indexes D5 deliverables by capability, domain, primary API, and UI entry point. All quote-related capabilities are **read-only / advisory** — no quote records are created.

| Capability | Domain | Main API | Main UI | Status |
|---|---|---|---|---|
| Lead Intake | Lead Intelligence | `POST /api/a-domain/lead-intake/preview`, `POST /api/a-domain/lead-intake/apply`, `GET /api/a-domain/lead-intake/template` | `/lead-intake` · LeadIntakePage | Closed |
| Lead Completeness | Lead Intelligence | `GET /api/a-domain/lead-completeness` | `/lead-intelligence` · Lead Completeness panel | Closed |
| Contact Research | Lead Intelligence | `POST /api/a-domain/leads/{lead_id}/contact-research` | `/lead-intelligence` · Contact Research drawer | Closed |
| Manual Outreach Queue | Lead Intelligence / Outreach | `GET /api/a-domain/leads/{lead_id}/workflow`, `GET /api/a-domain/outreach-draft` | `/lead-intelligence` · Manual Outreach Queue | Closed |
| Outreach Draft | Outreach | `GET /api/a-domain/outreach-draft` | `/lead-intelligence` · OutreachDraftPanel | Closed |
| Mark as Sent | Outreach | `POST /api/a-domain/leads/{lead_id}/touchpoint` | `/lead-intelligence` · touchpoint form | Closed |
| Product-Aware Draft | Product Planning / Outreach | `POST /api/a-domain/leads/{lead_id}/product-aware-draft` | `/lead-intelligence` · ProductAwareDraftPanel | Closed |
| Product Fit | Product Planning | `GET /api/a-domain/leads/{lead_id}/product-fit` | `/lead-intelligence` · ProductFitCard | Closed |
| Product Opportunity Board | Product Planning | `GET /api/a-domain/product-opportunity-board` | `/lead-intelligence` · ProductOpportunityBoard | Closed |
| Pre-Quote Prep | Quote Preparation | `GET /api/a-domain/leads/{lead_id}/pre-quote-brief`, `GET /api/a-domain/pre-quote-board` | `/lead-intelligence` · PreQuotePrepCard | Closed |
| Soft Quote Handoff | Quote Preparation | `GET /api/a-domain/leads/{lead_id}/quote-handoff-brief`, `GET /api/a-domain/quote-handoff-board` | `/lead-intelligence` · QuoteHandoffCard | Closed |
| Quote Input Contract | Phase 2 Handoff | `GET /api/a-domain/leads/{lead_id}/quote-input-contract`, `GET /api/a-domain/quote-input-contract-board` | `/lead-intelligence` · QuoteInputContractCard | Closed |
| Follow-up Queue | Follow-up | `GET /api/a-domain/follow-up-queue`, `POST /api/a-domain/leads/{lead_id}/follow-up-schedule` | `/lead-intelligence` · FollowUpScheduler + queue filters | Closed |
| Timeline | Lead Intelligence | `GET /api/a-domain/leads/{lead_id}/timeline` | `/lead-intelligence` · OutreachHistoryTimeline | Closed |
| Daily Dashboard | Daily Operations | `GET /api/a-domain/daily-ops-summary` | `/` · DailyOperationsPanel | Closed |
| End-of-Day Summary | Daily Operations | `GET /api/a-domain/daily-work-summary` | `/` · Dashboard EOD summary | Closed |
| Portal Read-only | Portal Integration | `GET /api/v1/portal/manifest`, `GET /api/v1/portal/summary`, `GET /api/v1/portal/a-domain/status` | `/system-health`, `/portal-consumer-mock` | Closed |
| Runtime Doctor / Smoke All | DevOps / Hardening | CLI: `dev_runtime_doctor.py`, `smoke_all_d5.py` | N/A (CLI) | Closed |

## Supporting APIs

| API | Purpose |
|---|---|
| `GET /api/a-domain/leads/{lead_id}/workflow` | Lead Intelligence workflow snapshot |
| `GET /health`, `GET /readiness` | Backend health and DB readiness |

## D5 to Phase 2 Boundary

### D5 (closed)

- **Derived intelligence** — product fit, opportunity scoring, completeness from existing CRM/lead data
- **Manual workflow** — human-reviewed drafts, Mark as Sent, follow-up scheduling
- **Quote preparation** — pre-quote brief, soft handoff, supplier prep notes
- **Quote input contract** — structured read-only payload for future Quote module; no quote record

### Phase 2 (not started)

- **Quote records** — persistent quote entities with status lifecycle
- **Quote line items** — SKU-linked rows with quantity, unit price, margin
- **Pricing** — partner pricing, discounts, validity dates
- **PDF quote** — customer-facing export
- **Quote approval** — internal review before customer send
- **Quote versioning** — revisions and audit trail
- **Order conversion** — quote → order handoff

Phase 2 must consume D5 **Quote Input Contract** as input boundary; it must not assume price, inventory, certification, or lead time are known.

## Smoke / Regression Scripts

| Script | Capability covered |
|---|---|
| `smoke_all_d5.py` | End-to-end D5 smoke |
| `dev_runtime_doctor.py` | Runtime + key API health |
| `d5_16_real_lead_uat_check.py` | Real lead UAT coverage |
| `d5_17_rule_tuning_check.py` | Product rule regression |
| `product_opportunity_check.py` | Product opportunity board |
| `pre_quote_brief_check.py` | Pre-quote brief |
| `product_aware_draft_check.py` | Product-aware draft |
| `quote_handoff_check.py` | Soft quote handoff |
| `d5_19_quote_input_contract_check.py` | Quote input contract |
