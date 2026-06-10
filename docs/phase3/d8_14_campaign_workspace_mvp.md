# D8.14 Campaign Workspace MVP

Status: READY_FOR_STAGING_HANDOFF

## Goal

D8.14 turns the D8.13 growth operations loop into a lightweight, persistent campaign workspace. PartnerOS can now save growth campaigns, create manual outreach tasks, and track human-updated task status while keeping the existing PartnerOS source-of-truth boundary.

This stage does not enter D9, does not create proof records, and does not claim staging validation. Real service portal staging still requires private token and origin configuration outside this repository.

中文边界：本阶段不自动发送任何客户、供应商或营销触达；不进入 D9；不新增 proof records；不写 staging validated。

## Scope

- Persist `growth_campaigns`.
- Persist `growth_campaign_tasks`.
- Keep `/api/v1/growth/operations-console` available.
- Add campaign CRUD API under `/api/v1/growth/campaigns`.
- Add task create/update API under `/api/v1/growth/campaigns/{id}/tasks` and `/api/v1/growth/tasks/{id}`.
- Add a Chinese-first Campaign Workspace inside `/growth-operations`.
- Support HOSUN lifting systems and JOOBOO education furniture as equal demo partners.

## Campaign Data

Campaign fields:

- `name`
- `partner_focus`
- `product_focus`
- `target_segment`
- `goal`
- `status`
- `owner`
- `next_action`
- `notes`
- timestamps and user audit fields

Allowed campaign status values stay as English enum values in the API and database:

- `planned`
- `active`
- `paused`
- `completed`
- `archived`

The frontend displays Chinese labels such as `已规划`, `推进中`, `已暂停`, `已完成`, and `已归档`.

## Task Data

Task fields:

- `campaign_id`
- optional `company_id`
- optional `contact_id`
- `task_type`
- `language`
- `draft_subject`
- `draft_body`
- `status`
- `due_date`
- `notes`
- timestamps and user audit fields

Allowed manual task status values:

- `planned`
- `manual_sent`
- `replied`
- `interested`
- `quote_requested`
- `closed`

These are manual operating statuses only. PartnerOS does not send email, SMS, LinkedIn messages, webhooks, or customer notifications.

## Read-only Business Aggregation

Campaign detail includes a read-only summary across existing business data:

- quotes
- customer orders
- feedback tickets
- shipment plans and shipment risks
- market intelligence signals

The aggregation uses campaign partner/product/segment/notes keywords to match existing records. It does not fake conversions, does not create orders, does not update quote or order status, and does not infer customer-visible facts outside the existing data.

## Demo Partners

HOSUN example:

- lifting systems
- desk frames
- desk legs
- lifting columns
- heavy-duty supply

JOOBOO example:

- education furniture
- project furniture
- classroom furniture
- collaborative table

Both are treated as equal PartnerOS operating scenarios. HOSUN is not the only primary brand.

## API Safety

All campaign and task responses keep safety flags false:

- `email_sent`
- `sms_sent`
- `linkedin_sent`
- `customer_notified`
- `supplier_notified`
- `quote_status_changed`
- `order_status_changed`
- `external_crm_connected`

This remains an internal operating workspace. Customer-facing service portal integration is still handled by filtered bridge APIs and remains gated by real staging configuration.

## Validation

Run from `backend` with `BACKEND_BASE_URL=http://127.0.0.1:8014`:

```powershell
python scripts/d8_14_campaign_workspace_check.py
```

Required broader validation for this stage:

```powershell
python -m pytest -q
python scripts/dev_runtime_doctor.py
python scripts/d8_12_release_candidate_check.py
python scripts/d8_13_growth_loop_alignment_check.py
python scripts/d8_14_campaign_workspace_check.py
```

Run from `frontend`:

```powershell
npm run test -- --run
npm run build
```

## Boundaries

- Do not enter D9.
- Do not add proof records.
- Do not write staging validated claims.
- Do not auto-send messages.
- Do not connect external CRM or marketing platforms.
- Do not change quote, order, shipment, feedback, supplier, or customer status automatically.
- Do not expose internal cost, margin, pricing breakdown, supplier private notes, backend paths, tokens, or private staging configuration.
