# Manual Test Record Template

Use with [Manual A-Domain Test Plan](../manual_a_domain_test_plan.md).

This template is for redacted UAT summaries only. Do not paste raw response bodies, real tokens, private customer files, screenshots with secrets, backend storage paths, or `.env` values.

## Test Execution Matrix

| Test ID | Module | Scenario | Company | Expected | Actual | Pass/Fail | Issue Type | Notes |
|---|---|---|---|---|---|---|---|---|
| TC-A-001 | Lead Intelligence | Segment review | Redacted company | `lift_system_signal` |  |  |  |  |
| TC-A-002 | Enrichment | Evidence review | Redacted company | Pending suggestions only |  |  |  |  |

Allowed Issue Type values:

- `data_entry`
- `frontend_error`
- `backend_error`
- `scoring_rule`
- `segment_rule`
- `enrichment_evidence`
- `documentation`
- `safety_boundary`

## Customer Entry Matrix

| Field | Value |
|---|---|
| Test Case ID |  |
| Company Name | Redacted or test company only |
| Website | Public test URL or redacted domain |
| City / State / Country |  |
| Business Type |  |
| Business Summary |  |
| Source |  |
| Source URL |  |
| Initial Notes |  |
| Primary Contact Name | Redacted or test contact only |
| Title / Email / Phone | Redacted if real |
| LinkedIn URL | Manual reference only; no automation |
| Lead product_interest |  |
| Expected Segment(s) |  |
| Expected Non-Segment(s) |  |
| Tester / Date |  |

## Interaction Stub

When a UI field is not yet structured, paste a compact stub into a note or summary:

```text
--- structured_stub ---
intent_level: medium
product_interest: height_adjustable_desk
customer_need: redacted one-line summary
objection: redacted if any
occurred_context: inbound|outbound|internal
raw_note: redacted summary only
---
```

## Enrichment Run Record

| Run ID | Company | Started | Status | Pages | Pending Suggestions | Fail Reason | Reviewer |
|---|---|---|---|---|---|---|---|
|  | Redacted company |  |  |  |  |  |  |

## Segment Review Record

| Test ID | company_id | Actual market_fit_segments | Human expectation | Pass/Fail | Notes |
|---|---|---|---|---|---|
|  | redacted |  |  |  |  |

## Validation

```powershell
cd backend
python scripts/manual_a_domain_test_plan_check.py
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
python scripts/d8_staging_execution_pack_check.py
python scripts/project_execution_acceptance_audit_check.py
```
