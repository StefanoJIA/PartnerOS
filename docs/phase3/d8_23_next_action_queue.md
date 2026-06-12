# D8.23 Next Action Queue

## Status

- Current state: READY_FOR_STAGING_HANDOFF
- External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE
- Purpose: define follow-up action categories after real partner rehearsal
- Boundary: no D9 entry, no proof record expansion, no real staging validation claim

Use this queue after real partner rehearsal. If no real partner session has occurred, keep partner-specific action details pending.

## Action Status Values

- pending
- in review
- ready
- blocked
- deferred
- done

## Priority Values

- P0: staging / pilot 前必须解决
- P1: partner rehearsal 后优先解决
- P2: pilot 期间增强
- P3: 长期平台化能力

## Queue

| Category | Action | Owner | Due Date | Priority | Dependency | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| staging credential request | Request backend HTTPS origin, `PORTAL_CUSTOMER_API_TOKEN`, `PORTAL_CUSTOMER_ALLOWED_ORIGINS`, `PUBLIC_BASE_URL`, and real `service.intelli-opus.com` origin. | infrastructure / backend operator | pending | P0 | secure credential channel | pending | Required before real staging validation. |
| security review | Review token handling, CORS, forbidden fields, logs, secret exposure, and customer-safe whitelist. | security reviewer | pending | P0 | staging request pack | pending | Must complete before customer-facing UAT. |
| business UAT | Confirm customer-visible fields, UAT records, pilot conditions, and partner-specific visibility rules. | business owner | pending | P0 | partner rehearsal feedback | pending | Must distinguish customer-safe and internal-only fields. |
| partner follow-up | Schedule or complete real HOSUN, JOOBOO, Chongqing Huiju, or future partner rehearsal follow-up. | partner owner | pending | P1 | real partner session | pending | No real partner feedback should be invented. |
| product data cleanup | Prepare partner/customer/product/order records for staging-safe UAT. | product operations | pending | P0/P1 | business owner sign-off | pending | Do not import real data without approved process. |
| HOSUN market response refinement | Refine load, stability, noise, delivery, installation, after-sales, packaging, warranty, test cycle, certification, and project demand metrics. | HOSUN business owner | pending | P1 | HOSUN rehearsal feedback | pending | Keep internal-only signals out of Portal. |
| JOOBOO project furniture refinement | Refine school procurement timing, delivery consistency, installation, resource needs, feedback after use, and project acceptance criteria. | JOOBOO business owner | pending | P1 | JOOBOO rehearsal feedback | pending | Keep project risk notes internal until reviewed. |
| future partner onboarding refinement | Define onboarding data, product family, quote logic, delivery requirement, resource taxonomy, customer-visible fields, and Market Response metrics. | partner operations | pending | P1/P2 | future partner rehearsal feedback | pending | Avoid hardcoding one partner's assumptions into shared core. |

## Action Detail Template

### Action

- Category:
- Action:
- Owner:
- Due date:
- Priority:
- Dependency:
- Status:
- Related partner:
- Related module:
- Decision source:
- Notes:

### Safety Review

- Requires real staging credentials: yes / no
- Requires security review: yes / no
- Requires business owner sign-off: yes / no
- Customer-safe: yes / no / pending
- Internal-only: yes / no / pending
- Blocks pilot: yes / no / pending

## Queue Rules

- Do not mark a partner-specific action as ready unless it is based on real partner feedback or approved internal planning.
- Do not mark staging credential actions as done until values are provided through approved secure channels.
- Do not mark security review as done without reviewer sign-off.
- Do not move any item into D9 while external staging remains WAITING_FOR_REAL_STAGING_EVIDENCE.
- Do not create proof records from this queue.
- Do not write STAGING_VALIDATED from this queue.
- Do not automatically send email, SMS, LinkedIn messages, or customer notifications from this queue.
- Do not automatically change quote/order status from this queue.

## Current Queue Decision

The immediate queue is ready to support real partner rehearsal execution. All partner-specific details remain pending until actual HOSUN, JOOBOO, Chongqing Huiju, or future partner sessions occur.
