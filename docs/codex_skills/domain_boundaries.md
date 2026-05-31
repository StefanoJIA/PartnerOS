# Domain Boundaries

- D5/D6 are closed baselines.
- D7 is closed through D7.9: internal order lifecycle, shipment plans, customer portal bridge APIs, feedback intake, and resource center foundations.
- D8 is `READY_FOR_STAGING_HANDOFF`; local gates are ready, but strict staging evidence still requires private staging values.
- `WAITING_FOR_REAL_STAGING_EVIDENCE` means local rehearsal evidence must be replaced with real staging evidence before production coordination.
- D9 operating loops remain planned behind `STAGING_VALIDATED`, `READY_FOR_PRODUCTION_COORDINATION_REVIEW`, production coordination, and the human Go / No-Go handoff. If committed, the handoff record uses `docs/records/d8_production_go_no_go_YYYYMMDD.md`.
- Customer confirmation, supplier confirmation, production milestones, and shipment plans are manual records.
- No automatic shipment creation, production start, supplier/customer notification, carrier API call, webhook, or email is allowed.
- Shipment status does not automatically change `customer_orders.status`.
- Customer portal bridge fields must remain explicit allowlists; do not expose internal cost, margin, supplier notes, backend paths, storage keys, or tokens.
