# Lead Import Template Guide

**File:** [lead_import_template.csv](lead_import_template.csv)

Use this CSV as a manual import and review guide for Lead Intelligence testing. Template rows must be fictional or redacted. Do not treat sample rows as live customers.

## Current Boundary

Lead import supports the A-domain workflow:

```text
Company -> Contact -> Lead -> Score / Segments -> Interaction -> Next Action
```

It does not send outreach, scrape LinkedIn, create RFQs, create quotes, create orders, create shipments, notify customers, notify suppliers, or call carrier APIs.

## Field Reference

| Column | Required | Lead Intelligence impact | Notes |
|---|---|---|---|
| `company_name` | Yes | Context | Legal or trade name shown in Companies list |
| `website` | Recommended | Enables enrichment | Public URL only; keep private portals out |
| `company_type` | Recommended | Scoring context | Use stable CRM-facing values |
| `industry` | Optional | Scoring context | Include vertical keywords when known |
| `city` / `state` / `country` | Optional | Territory context | Redact where needed |
| `contact_name` | Recommended | Contact score | Split into first/last in UI when needed |
| `contact_title` | Optional | Qualification | Helps identify decision-maker context |
| `contact_email` / `contact_phone` | Optional | Manual follow-up | Redact in committed records |
| `linkedin_url` | Optional | Manual reference only | No LinkedIn automation |
| `source` | Recommended | Audit context | Trade show, referral, website inbound, etc. |
| `notes` | Highly recommended | Scoring and segments | Use redacted evidence summaries |
| `initial_interest` | Recommended | Maps to lead product interest | Include product context such as desk frame or lifting column |
| `priority` | Optional | Scoring hint | High / Medium / Low |
| `next_action` | Optional | Workflow | Seeds manual next action |

## Segment Signals

| Signal | Segment |
|---|---|
| height-adjustable desk, lifting column, desk frame, sit-stand workstation | `lift_system_signal` |
| contract interiors, installation package, project rollout | `project_based_furniture` |
| campus, classroom, school, learning environment | `education_vertical` |
| medical, healthcare, lab, clinical workstation | `medical_vertical` |
| office furniture without lift evidence | `general_office_furniture_only` |
| OEM/ODM plus lifting context | `oem_odm_fit` |
| heavy-duty or industrial adjustable products | `heavy_duty_fit` |

Use `oem_odm_fit`; do not invent `oem_odm_signal` without a migration plan.

## Recommended Manual Workflow

1. Preview the CSV before import.
2. Create or import the company.
3. Create or link the contact.
4. Create the lead with product interest, priority, and next action.
5. Open `/lead-intelligence`.
6. Verify score and segment output.
7. Run public-source enrichment only when enabled and appropriate.
8. Review suggestions before applying.
9. Log a human-reviewed touchpoint.

## Validation

```powershell
cd backend
python scripts/manual_a_domain_test_plan_check.py
python scripts/lead_intelligence_docs_check.py
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
python scripts/d8_staging_execution_pack_check.py
python scripts/project_execution_acceptance_audit_check.py
```
