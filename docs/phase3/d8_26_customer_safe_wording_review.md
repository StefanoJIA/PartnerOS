# D8.26 Customer-Safe Wording Review

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Review status: pending

No real business owner sign-off recorded yet. This document is a customer-safe wording review checklist for partner rehearsal, staging UAT, and pilot preparation. It does not approve real wording until reviewed by the responsible business owner.

## Wording Review Rules

| Topic | Rule | Status |
| --- | --- | --- |
| planned dates | planned dates must say planned / 预计 | pending |
| shipment risk | shipment risk must be rewritten into customer-safe wording | pending |
| production delay | production delay must not expose internal responsibility assignment | pending |
| Market Response | Market Response may show high-level preview only | pending |
| technical metrics | technical metrics must distinguish validated claim / internal note / draft wording | pending |
| forbidden fields | cost, margin, pricing breakdown, supplier private notes, internal comments, private partner notes, backend paths, storage keys, token values, and unsafe raw database IDs must stay hidden | pending |

## Planned Dates

Planned dates must be written as planned / 预计. A planned date must not be written as confirmed, shipped, delivered, completed, or contractually guaranteed unless the source record and business owner approval support that wording.

Allowed wording:

- `预计生产节点：2026-07-15`
- `Planned shipment window: mid July 2026`
- `Delivery timing is planned and subject to operations confirmation.`

Blocked wording:

- `Guaranteed delivery on 2026-07-15`
- `Shipment confirmed` when the record is only planned
- `Delivered` when the order status has not been manually updated

## Shipment Risk

Shipment risk must be converted into customer-safe wording.

Allowed wording:

- `物流计划正在运营跟进，客户可见时间仍为预计窗口。`
- `Shipment plan is under operations review; customer-facing schedule remains planned.`

Blocked wording:

- direct carrier negotiation notes
- supplier blame
- internal route risk analysis
- backend paths
- storage keys
- private escalation comments

## Production Delay

Production delay must not directly expose internal responsibility assignment. The customer-safe wording should explain the visible status and next review step without disclosing supplier accountability or private escalation.

Allowed wording:

- `生产节点需要跟进，更新后的客户可见时间待运营确认。`
- `Production milestone needs follow-up; updated customer-safe timing is pending review.`

Blocked wording:

- `Supplier failed inspection because of internal issue`
- `Factory caused delay`
- raw test notes
- private partner notes

## Market Response Preview

Market Response must remain a high-level preview:

- no internal scoring
- no ranking
- no watchlist formula
- no internal margin logic
- no supplier private analysis

Allowed wording:

- `市场响应预览：近期产品兴趣和运营反馈显示该产品线值得继续跟进。`
- `Market signal preview: recent interest and operating feedback suggest this product family should remain in active follow-up.`

## Forbidden Fields

Customer-safe wording must not expose:

- cost
- margin
- pricing breakdown
- supplier private notes
- internal comments
- private partner notes
- backend paths
- storage keys
- token values
- unsafe raw database IDs
- raw test notes
- complaint details
- delivery risk analysis
- warranty cost exposure
- internal Market Response scoring
- internal ranking

## Technical Metrics Classification

Every technical metric must be classified before it appears in external wording.

| Classification | Meaning | External Use |
| --- | --- | --- |
| validated claim | Supported by approved material and business owner wording | May be customer-visible after approval |
| internal note | Used for operations, supplier follow-up, risk, or quality review | Internal-only |
| draft wording | Candidate text not yet approved | Pending; not customer-visible |

HOSUN metrics such as load, stability, noise, test cycle, certification, and warranty must be treated as pending until there is both business confirmation and supporting material.

## Partner Coverage

HOSUN wording must cover lifting systems, desk frames, desk legs, lifting columns, and heavy-duty supply only with approved customer-safe claims.

JOOBOO wording must cover education furniture, school desks/chairs, project furniture, school procurement timing, delivery consistency, installation, resource needs, feedback after use, and project acceptance criteria without exposing private project details.

Future partner wording must review onboarding data, product family, quote logic, delivery requirement, resource taxonomy, customer-visible fields, and Market Response metrics before any customer-visible summary.

## Boundary

- Pending wording is not approved wording.
- No real business owner sign-off recorded yet.
- Do not write STAGING_VALIDATED.
- Do not enter D9.
- Do not create proof records.
- Do not fabricate real sign-off or real partner feedback.
