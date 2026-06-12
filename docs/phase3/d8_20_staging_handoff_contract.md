# D8.20 Staging Handoff Contract and P0 Readiness Checklist

## 1. Current Status Boundary

Current PartnerOS state:

- Internal status: READY_FOR_STAGING_HANDOFF.
- External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE.
- PartnerOS remains the internal source of truth for intelliOffice operations.
- `service.intelli-opus.com` remains the customer-facing Portal.

This contract is a handoff document only. It does not validate real external staging, does not deploy anything, does not connect real third-party APIs, and does not change runtime behavior.

Hard boundary:

- Do not write a real staging validated status until real external staging evidence exists.
- Do not enter D9 from this document.
- Do not add proof records from this document.
- Do not claim production ready.
- Do not treat local rehearsal as external staging validation.

## 2. Required Real Staging Configuration

Real service Portal staging requires the following private configuration values and runtime boundaries.

| Item | Required Value / Meaning | Owner | Verification |
| --- | --- | --- | --- |
| Backend HTTPS origin | Public HTTPS origin where PartnerOS backend staging can be reached by `service.intelli-opus.com`. | Infrastructure / deployment operator | `GET /health` succeeds from the Portal network path over HTTPS. |
| `PORTAL_CUSTOMER_API_ENABLED` | Must be set to `true` only for the intended staging environment. | intelliOffice backend operator | Portal bridge readiness endpoint reports enabled state. |
| `PORTAL_CUSTOMER_API_TOKEN` | Private server-to-server token used by the Portal when calling PartnerOS customer-safe bridge APIs. | intelliOffice backend operator + security reviewer | Correct token succeeds; wrong token fails. Token is never committed. |
| `PORTAL_CUSTOMER_ALLOWED_ORIGINS` | Comma-separated allowlist containing the real Portal origin. | intelliOffice backend operator + infrastructure operator | Allowed origin succeeds; disallowed origin fails. |
| `PUBLIC_BASE_URL` | Customer-safe public base URL used for links, manifests, and externally visible references. | Infrastructure / deployment operator | API responses and manifests use the expected public base URL. |
| `service.intelli-opus.com` real origin | Exact HTTPS origin used by the customer-facing Portal. | service Portal operator | Origin matches the allowed origin configured in PartnerOS. |

### Access Boundary

- Portal access is server-to-server.
- The Portal must call only customer-facing bridge APIs.
- The Portal must send the configured token through the approved server-to-server path.
- Browser clients must not receive or store `PORTAL_CUSTOMER_API_TOKEN`.
- CORS allowlist must include only the real Portal origin and approved staging origins.
- Disallowed origins and missing/wrong tokens must be rejected.

## 3. Responsibility Matrix

### intelliOffice Backend Operator

Provides:

- Backend staging runtime.
- `PORTAL_CUSTOMER_API_ENABLED=true` only when staging is intended.
- `PORTAL_CUSTOMER_API_TOKEN` through secure secret management.
- `PORTAL_CUSTOMER_ALLOWED_ORIGINS` containing approved Portal origins only.
- Customer-safe Portal bridge API readiness.
- Rollback toggle for disabling the Portal bridge.

Verifies:

- Backend health.
- Migration at head.
- Portal bridge readiness.
- Correct token accepted.
- Wrong token rejected.
- Forbidden fields absent from bridge responses.

### `service.intelli-opus.com` Portal Operator

Provides:

- Real Portal staging origin.
- Server-side API client that calls PartnerOS bridge APIs.
- Portal UI that renders only customer-safe fields.
- Confirmation that token is never exposed to browser clients.

Verifies:

- Portal can fetch products, orders, production, shipment, resources, feedback, and customer-safe market signal preview.
- Portal handles rejected token/origin errors safely.
- Portal does not display internal-only fields.

### Infrastructure / Deployment Operator

Provides:

- HTTPS routing for backend staging origin.
- TLS certificate.
- DNS and network reachability.
- Secret injection mechanism.
- Log and monitoring access.
- Rollback mechanism.

Verifies:

- HTTPS health check.
- Origin/cors behavior.
- Environment variable injection.
- No token in logs.
- Backup and restore readiness for staging.

### Business Owner

Provides:

- UAT scenarios.
- Which customer-visible fields are acceptable.
- Which HOSUN, JOOBOO, Chongqing Huiju, and future partner records should be used for staging.
- Approval for pilot readiness.

Verifies:

- Portal views are understandable for customers.
- Order, production, shipment, resource, feedback, and market signal preview match business expectations.
- No production-ready claim is made before pilot criteria are met.

### Security Reviewer

Provides:

- Token handling review.
- Forbidden-field review.
- Origin allowlist review.
- Logging and secret exposure review.
- Data access approval before external staging UAT.

Verifies:

- No cost, margin, pricing breakdown, supplier private notes, backend file paths, storage keys, token values, internal-only comments, private partner notes, or unsafe raw database IDs are exposed.

## 4. Portal Customer-Safe Field Contract

The customer-facing Portal may read the following customer-safe field types through the bridge APIs.

### Allowed Customer-Safe Field Types

Products:

- Product display name.
- Customer-safe product family.
- Public description.
- Public specifications.
- Customer-safe images or resource references.
- Availability or readiness label if reviewed for customer display.

Orders:

- Customer order number or customer-safe reference.
- Order status label.
- Customer-visible current step.
- Planned dates clearly marked as planned.
- Customer-safe partner/product display context.
- Customer-safe order summary.

Production milestones:

- Milestone label.
- Customer-safe milestone status.
- Planned or completed date when approved.
- Customer-safe progress summary.

Shipment status:

- Shipment status label.
- Planned dispatch or delivery windows.
- Carrier-neutral status summary.
- Tracking reference only if approved for customer display.
- Risk summary only if phrased for customer use.

Resources:

- Customer-safe resource title.
- Resource type.
- Download manifest or signed/customer-safe access reference.
- Public description.
- Version or last updated date if approved.

Feedback status:

- Feedback ticket customer-safe reference.
- Submitted date.
- Status label.
- Customer-safe resolution or handling summary.

Customer-safe market signal preview:

- Product or partner focus label.
- High-level demand signal.
- Customer-safe trend summary.
- No internal scoring details unless explicitly approved.

### Forbidden Fields

The Portal must not expose:

- Cost.
- Margin.
- Pricing breakdown.
- Cost snapshots.
- Supplier private notes.
- Backend file paths.
- Storage keys.
- Token values.
- Internal-only comments.
- Private partner notes.
- Raw database IDs if not customer-safe.
- Internal audit events.
- Internal owner notes.
- Unreviewed production risk notes.
- Unreviewed shipment risk notes.
- Internal Market Response scoring or ranking details.

## 5. Staging Smoke Test Flow

Run this sequence only when real staging configuration values are available. Passing local checks alone is not enough to claim real external staging validation.

1. Backend health
   - From the staging-facing network path, call the backend HTTPS origin health endpoint.
   - Expected: healthy response, migration at head, database ready.

2. Portal bridge readiness
   - Confirm customer Portal API is enabled only in staging.
   - Expected: bridge readiness reports enabled state and correct public base URL.

3. Token auth success
   - Call one customer-safe bridge endpoint with the correct server-to-server token.
   - Expected: HTTP success and customer-safe payload.

4. Wrong token rejected
   - Call the same endpoint with a wrong token.
   - Expected: rejected request; no data returned.

5. Disallowed origin rejected
   - Call from or simulate a disallowed origin.
   - Expected: rejected by origin/CORS boundary.

6. Customer-safe order list
   - Fetch customer-safe order list.
   - Expected: only customer-safe order fields are present.

7. Order detail field whitelist
   - Fetch one order detail.
   - Expected: customer-visible summary, production, shipment, resource, and feedback summary contain no forbidden fields.

8. Resources download manifest
   - Fetch resource listing or manifest.
   - Expected: no backend file path, storage key, local filesystem path, or token is exposed.

9. Feedback submit/read boundary
   - Submit a test feedback item.
   - Confirm it appears in PartnerOS Feedback Tickets.
   - Expected: no automatic customer reply, no customer notification, no SLA promise.

10. Forbidden fields absent
    - Scan all returned payloads for cost, margin, pricing breakdown, supplier private notes, backend paths, storage keys, token values, internal-only comments, private partner notes, and unsafe raw database IDs.
    - Expected: forbidden fields absent.

11. No automatic external messages
    - Confirm no email, SMS, LinkedIn message, customer notification, supplier notification, webhook, or external CRM action is triggered.

12. No quote/order status auto-change
    - Confirm Portal reads and feedback submission do not automatically change quote or order status.

## 6. Rollback / Disable Flow

If staging validation fails, immediately return to internal-only mode.

### Disable Portal Customer API

1. Set `PORTAL_CUSTOMER_API_ENABLED=false`.
2. Restart or reload the backend runtime according to the deployment process.
3. Verify Portal bridge endpoints reject external access or report disabled state.
4. Confirm PartnerOS internal UI still works.

### Revoke Token

1. Remove the current `PORTAL_CUSTOMER_API_TOKEN` from secret storage.
2. Generate a replacement token only after root cause review.
3. Confirm old token is rejected.
4. Confirm token value is not present in logs, commits, screenshots, or handoff documents.

### Clear Allowed Origins

1. Set `PORTAL_CUSTOMER_ALLOWED_ORIGINS` to an empty value or approved internal-only value.
2. Restart or reload the backend runtime.
3. Confirm `service.intelli-opus.com` and all external origins are rejected until re-approved.

### Return to Internal-Only Mode

1. Keep PartnerOS as the internal source of truth.
2. Keep local RC and internal demo flow intact.
3. Do not delete or rewrite internal PartnerOS records due to a Portal staging failure.
4. Record the failure as a staging handoff issue, not as proof that local PartnerOS RC is invalid.

Staging failure must not affect the local release candidate, internal operator workflow, or PartnerOS internal source of truth.

## 7. Pre-Pilot Prohibitions

Before pilot approval:

- Do not automatically send email.
- Do not automatically send SMS.
- Do not automatically send LinkedIn messages.
- Do not automatically notify customers.
- Do not automatically notify suppliers.
- Do not connect real Constant Contact APIs.
- Do not connect real sales CRM / salesforce-style / 销售易 APIs.
- Do not automatically change quote status.
- Do not automatically change order status.
- Do not expose cost, margin, pricing breakdown, supplier private notes, private partner notes, backend paths, storage keys, token values, or internal-only comments.
- Do not commit `.env`, token values, PDFs, `local_data/`, `backend/storage/`, `IE Auto.pdf`, or `docs/activity_actions.md`.
- Do not claim production ready.
- Do not claim real staging validation from local rehearsal.

## 8. HOSUN Lifting Systems Field Preparation

HOSUN staging/pilot preparation should separate customer-safe fields from internal-only fields.

Product focus:

- lifting systems
- desk frames
- desk legs
- lifting columns
- heavy-duty supply

### Customer-Safe HOSUN Fields

These may be prepared for customer-facing Portal display after business review:

- Product family: lifting systems, desk frames, desk legs, lifting columns, heavy-duty supply.
- Load capacity range when approved.
- Stability description in customer-safe language.
- Noise level claim only if validated by product data.
- Delivery window clearly marked as planned.
- Installation requirement summary.
- After-sales support summary.
- Project demand category.
- Warranty summary.
- Test cycle summary if reviewed for public use.
- Certification summary.
- Packaging summary.
- Customer-safe product resources.
- Customer-safe production milestone label.
- Customer-safe shipment status.

### Internal-Only HOSUN Fields

These must remain internal unless explicitly reviewed and transformed into customer-safe copy:

- Raw load test notes.
- Stability issue notes.
- Noise complaint details.
- Delivery risk analysis.
- Installation failure details.
- After-sales dispute notes.
- Project margin or discount assumptions.
- Warranty cost exposure.
- Test cycle failure notes.
- Certification gap notes.
- Packaging damage root-cause notes.
- Supplier private notes.
- Internal product scoring.
- Internal Market Response ranking.
- Partner private roadmap or capacity notes.

### HOSUN Readiness Checks

Before staging/pilot:

1. Confirm which load, stability, noise, delivery, installation, after-sales, project demand, warranty, test cycle, certification, and packaging fields are customer-safe.
2. Confirm which fields remain internal-only.
3. Confirm Portal payloads never expose internal-only HOSUN fields.
4. Confirm Market Response preview uses customer-safe summaries only.

## 9. Multi-Partner Expansion Preparation

HOSUN, JOOBOO, Chongqing Huiju, and future partners should share the same Portal bridge and customer-safe access boundary.

Shared Portal bridge surfaces:

- Products.
- Orders.
- Production milestones.
- Shipment status.
- Resources.
- Feedback status.
- Customer-safe market signal preview.

Partner-specific configuration must remain possible for:

- Product fields.
- Quote logic.
- Delivery requirements.
- Resource taxonomy.
- Portal-visible copy.
- Market Response metrics.
- Feedback categories.
- Shipment risk categories.
- Production milestone templates.

### Partner-Specific Examples

HOSUN:

- lifting systems
- desk frames
- desk legs
- lifting columns
- heavy-duty supply
- load / stability / noise / installation / after-sales metrics

JOOBOO:

- education furniture
- school desks/chairs
- project furniture
- school procurement timing
- delivery consistency
- feedback after use

Chongqing Huiju and future partners:

- Product families and customer segments to be defined during Partner Onboarding.
- Quote logic and delivery requirements to be captured before pilot.
- Resource and Market Response metrics to be reviewed before customer Portal exposure.

### Multi-Partner Rule

The shared Portal bridge should remain stable, while partner-specific product fields and metrics should be configured through reviewed customer-safe mappings. Do not hardcode one partner's product assumptions into the shared Portal contract.

## 10. Acceptance Criteria for Handoff

D8.20 is acceptable when:

- The required real staging configuration is known.
- Each responsibility owner understands what they must provide.
- Customer-safe and forbidden fields are explicitly defined.
- Smoke test steps are executable.
- Rollback / disable steps are clear.
- Pre-pilot prohibitions are explicit.
- HOSUN staging/pilot field preparation is separated into customer-safe and internal-only fields.
- Multi-partner extension rules are explicit.
- Status remains READY_FOR_STAGING_HANDOFF until real external staging evidence exists.
