# Lead Intelligence — scoring notes (D5.2.3 pilot)

Read-only documentation for internal pilot users. **No runtime change** in D5.2.3.

Implementation: `backend/app/services/a_domain/intelligence_score.py`

---

## Score (0–100)

Deterministic breakdown from:

| Dimension | Source |
|-----------|--------|
| Primary contact | Lead has `primary_contact_id` |
| Market intel count | `MarketIntelligenceItem` rows for company |
| Product / business text | Company tags, description, lead `product_interest` |
| Priority & strategic level | Lead `priority`, company `strategic_level` |

---

## Market fit segments (display slugs)

| Slug | UI label | Typical trigger |
|------|----------|-----------------|
| `lift_system_signal` | Lifting System Signal | sit-stand, lifting column, desk frame, ergonomic workstation keywords |
| `general_office_furniture_only` | General Office Furniture | office/contract furniture without lift keywords |
| `education_vertical` | Education Vertical | campus, education furniture, learning environment |
| `medical_vertical` | Medical / Healthcare Vertical | medical/lab/clinical workstation cues |
| `project_based_furniture` | Project-Based Furniture | contract interiors, installation, project rollout |
| `oem_odm_fit` | OEM / ODM Signal | OEM/ODM, private label, lifting solution partner |
| `heavy_duty_fit` | Heavy-Duty / Industrial | heavy-duty adjustable / industrial lift cues |

Multiple segments may appear. Empty segments → enrich company text or run public-source enrichment.

---

## Pilot tuning (D5.2.1)

- **Healthcare Lab Workspace** → `medical_vertical`
- **Contract Project Interiors** → `project_based_furniture`
- **Ergo Sit Stand Workspace** → `lift_system_signal`
- **Campus Learning Furniture** → `education_vertical`

Restart backend after scoring code changes for live API to reflect updates.

---

## Not in scope (pilot)

- No Outlook / LinkedIn automation
- No CRM v1 façade
- No new segment slug `oem_odm_signal` — use existing `oem_odm_fit`
