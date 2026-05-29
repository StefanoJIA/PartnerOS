# Domain Boundaries

- D5/D6 are closed baselines.
- D7.1-D7.6 cover internal order lifecycle through shipment tracking.
- D7.7 covers customer portal bridge APIs and feedback intake.
- Customer confirmation, supplier confirmation, production milestones, and shipment plans are manual records.
- No automatic shipment creation, production start, supplier/customer notification, carrier API call, webhook, or email is allowed.
- Shipment status does not automatically change `customer_orders.status`.
