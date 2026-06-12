# D8.21 Business UAT Request

## Purpose

Request business owner input for real staging UAT records, customer-visible field approval, and pilot conditions.

Do not automatically expose customer data or change quote/order status from this request.

Current state: READY_FOR_STAGING_HANDOFF.

External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE.

## Business Owner Decisions Needed

### Customer-Visible Fields

Please confirm which fields customers may see in the Portal:

- Product display name.
- Product family.
- Customer-safe specifications.
- Customer-safe resource titles and descriptions.
- Customer order number or customer-safe reference.
- Order status label.
- Customer-visible current step.
- Planned production dates.
- Planned shipment dates.
- Shipment status.
- Feedback status.
- Customer-safe Market Response preview.

Please confirm which fields must remain internal:

- Cost.
- Margin.
- Pricing breakdown.
- Supplier private notes.
- Internal-only comments.
- Private partner notes.
- Backend paths.
- Storage keys.
- Token values.
- Unsafe raw database IDs.

### Staging Records

Please identify staging-safe records for:

- HOSUN lifting systems.
- HOSUN desk frames.
- HOSUN desk legs.
- HOSUN lifting columns.
- HOSUN heavy-duty supply.
- JOOBOO education furniture.
- JOOBOO school desks/chairs.
- JOOBOO project furniture.
- Chongqing Huiju or future partner sample products.
- At least one order with production milestones.
- At least one order with shipment status.
- At least one feedback ticket.
- At least one customer-safe Market Response preview.

### UAT Scenarios

Please confirm UAT scenarios:

1. Customer opens Portal order list.
2. Customer opens order detail.
3. Customer reads production progress.
4. Customer reads shipment status.
5. Customer opens resources.
6. Customer submits feedback.
7. Operator sees feedback in PartnerOS.
8. Operator verifies Market Response signal context.

### Pilot Conditions

Please define pilot entry conditions:

- Which partner participates first?
- Which customer segment participates first?
- Which product family participates first?
- Who approves customer-visible wording?
- Who approves pilot data import?
- Who owns issue triage during pilot?
- What blocks pilot launch?

## HOSUN-Specific Business Input

Please confirm which HOSUN fields can be customer-visible:

- load
- stability
- noise
- delivery
- installation
- after-sales
- project demand
- warranty
- test cycle
- certification
- packaging

Please confirm which HOSUN fields must remain internal-only:

- raw test notes
- complaint details
- risk analysis
- warranty cost exposure
- supplier private notes
- internal Market Response scoring

## JOOBOO-Specific Business Input

Please confirm which JOOBOO fields can be customer-visible:

- education furniture product family
- school desks/chairs
- project furniture
- school procurement timing
- delivery consistency
- feedback after use

## Requested Business Sign-Off

- Approved customer-visible field set:
- Required wording changes:
- Approved staging records:
- UAT owner:
- Pilot owner:
- Pilot entry condition:
- Pilot blocker:
- Business owner:
- Date:

PartnerOS remains READY_FOR_STAGING_HANDOFF until real staging credentials, security review, and business UAT are complete.
