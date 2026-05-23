# Lead Import Template — intelliOffice Pilot

**File**: [lead_import_template.csv](lead_import_template.csv)

Use this CSV as a **manual entry guide** when onboarding real pilot leads. Rows in the template are **fictional examples** — do not treat them as live customers.

---

## Field reference

| Column | Required | Affects Lead Intelligence | Notes |
|--------|----------|---------------------------|-------|
| `company_name` | Yes | Indirect (context) | Legal or trade name shown in Companies list |
| `website` | Recommended | **Yes** — enables Enrichment | Must be reachable public URL for D5.2 enrichment |
| `company_type` | Yes | **Yes** — scoring context | Use values from CRM enum (e.g. `Office Furniture Dealer`, `Education Furniture Company`) |
| `industry` | Optional | **Yes** | Free text; include vertical keywords (education, healthcare, contract) |
| `city` / `state` / `country` | Optional | Low | Territory planning only |
| `contact_name` | Recommended | **Yes** — contact score | Split into first/last when creating Contact in UI |
| `contact_title` | Optional | Low | Helps qualify decision-maker |
| `contact_email` / `contact_phone` | Optional | Low | Not used in scoring; needed for outreach |
| `linkedin_url` | Optional | Low | Manual follow-up only (no automation in pilot) |
| `source` | Recommended | Medium | Trade show, referral, website inbound, etc. |
| `notes` | **Highly recommended** | **Yes** | Primary place for lift-system, project, medical, education cues |
| `initial_interest` | Recommended | **Yes** | Maps to Lead `product_interest` and Company tags |
| `priority` | Optional | **Yes** | `High` / `Medium` / `Low` — boosts score when set |
| `next_action` | Optional | Workflow | Seeds Lead `next_action` after create |

---

## What influences segments & score

Lead Intelligence scoring reads **Company** fields (`business_description`, `product_interest_tags`, `strategic_level`) and **Lead** fields (`product_interest`, `priority`), plus market intel count and primary contact presence.

**Strongest pilot signals** (put in `notes` + `initial_interest` + Company description after import):

### Height-adjustable / lifting (→ `lift_system_signal`)

- height-adjustable desk frame, lifting column, sit-stand workstation
- desk leg, electric desk, ergonomic workstation
- Example note: *"Dealer catalog refresh — needs HOSUN-compatible frames and 2-stage columns."*

### Project-based / contract (→ `project_based_furniture`)

- contract furniture, installation package, multi-floor rollout, interiors contractor
- Example note: *"GC-led office fit-out; furniture package incl. adjustable benching pods."*

### Education (→ `education_vertical`)

- campus, university, K-12, education furniture, learning environment
- Example note: *"District RFP for STEM lab tables and adjustable instructor desks."*

### Healthcare / lab (→ `medical_vertical`)

- medical workstation, clinical, lab furniture, healthcare facility
- Example note: *"Hospital nurse station refresh; anti-microbial sit-stand carts."*

### General office without lift cue (→ `general_office_furniture_only`)

- office furniture dealer with no explicit lift keywords yet — not negative; enrich or follow up lightly

### OEM / ODM (→ `oem_odm_fit` when present)

- OEM/ODM, private label, lifting solution partner
- Backend slug is `oem_odm_fit` (not `oem_odm_signal`). Document only — no new rules in this pilot.

---

## Recommended import workflow (manual)

1. Create **Company** from CSV row (Companies → New).
2. Paste `notes` into Company notes / business description; set `product_interest_tags` from `initial_interest`.
3. Create **Contact** linked to company.
4. Create **Lead** with `product_interest`, `priority`, `next_action`.
5. Open **Lead Intelligence** → verify score & segments.
6. Run **Enrichment** if website present → review suggestions.
7. Log **touchpoint** and update **next action** daily.

See [d5_2_3_internal_pilot_workflow_20260523.md](../records/d5_2_3_internal_pilot_workflow_20260523.md).

---

## Scoring reference

Detailed rule notes (read-only): [lead_intelligence_scoring_notes.md](../lead_intelligence_scoring_notes.md).
