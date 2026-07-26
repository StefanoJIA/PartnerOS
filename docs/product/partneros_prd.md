# PartnerOS Product Requirements Document

**Version:** v1.0  
**Date:** 2026-06-22  
**Owner:** intelliOffice / IntelliOpus  
**Status:** Active product direction

## 1. Product Definition

PartnerOS is the internal operating system for intelliOffice's multi-brand U.S.-facing agency business. It connects market discovery, customer development, product matching, quoting, customer ordering, production coordination, shipment tracking, feedback, and commercial intelligence into one operational source of truth.

PartnerOS is not only a CRM, not only a quote tool, and not only a customer portal. Its purpose is to optimize the full path from product-to-market discovery to customer acquisition, quote execution, order placement, delivery follow-up, and repeat business learning.

## 2. Primary Goal

The first priority is internal team efficiency.

The system must help the internal team:

- discover and organize potential customers;
- collect and maintain customer and contact data;
- match customer needs with partner products;
- generate professional interval-based quotes;
- support customer self-service ordering through a separate customer-facing portal;
- track orders, production, shipment, samples, resources, and feedback;
- reuse quote, customer, product, and partner experience as commercial intelligence.

## 3. Users And Roles

### 3.1 Current Roles

The current product only needs two practical roles:

| Role | Purpose |
|---|---|
| Administrator | Internal operator. Handles customer development, products, quotes, orders, production, logistics, feedback, commercial intelligence, and system configuration. |
| Customer | External portal user. Browses approved products/resources, checks sample inventory, places orders, tracks order status, and submits feedback. |

### 3.2 Deferred Roles

Sales, quotation, order, logistics, and operations roles may be split later, but should not complicate the current product. Partner/supplier users are not required now because intelliOffice communicates with partners directly outside the system.

## 4. Product Principles

1. Internal efficiency first.
2. Customer-visible data must be strictly whitelisted.
3. HOSUN, JOOBOO, and future partners are peer manufacturing partners.
4. Quote logic is interval-based, not single-quantity total-first.
5. PDF quote output is a formal deliverable.
6. Customer orders should originate from the customer-facing portal when possible.
7. Commercial intelligence is a near-term capability, not a distant reporting layer.
8. Deployment target is local-server Docker deployment.
9. Automation must not override human decisions.
10. The system must reduce repeated manual coordination, not add decorative screens.

## 5. Business Scope

PartnerOS covers the following operating loop:

Market signal -> customer discovery -> company/contact management -> product fit -> partner/product selection -> interval quote -> PDF quote delivery -> customer order -> production and logistics tracking -> customer portal status -> feedback -> commercial memory -> next quote and repeat business.

## 6. Core Domains

### 6.1 Customer Development

The system must support:

- companies and contacts;
- lead intake and enrichment;
- customer segmentation;
- manual outreach support;
- follow-up tasks;
- customer lifecycle history.

Success criterion: an operator can understand who the customer is, what they are interested in, what has already happened, and what the next manual action should be.

### 6.2 Product And Partner Catalog

The long-term product model is:

Partner -> Product family -> Product model -> Configuration options -> Quote intervals -> Order line item.

HOSUN, JOOBOO, and future partners must remain peer partners.

HOSUN currently requires detailed support for:

- lifting systems;
- desk frames;
- desk legs;
- lifting columns;
- heavy-duty supply;
- hand control panels;
- color swatch sample set;
- standardized SKU rules;
- product images;
- weight, factory cost, shipping assumptions, and target margin.

JOOBOO currently requires support for:

- education furniture;
- school desks and chairs;
- project furniture;
- brochure/catalog resources;
- product attributes suitable for project procurement.

Future partners must be added through the same partner/product structure rather than hard-coded UI branches.

### 6.3 Quote System

The quote system is a priority module.

Quotes must be interval-based. A quote does not ask the customer to commit to a final quantity at quote creation time. Instead, each selected product appears with its full customer-visible quantity interval table.

Required quote capabilities:

- automatic quote number sequence;
- quote draft persistence and archive;
- customer/company/contact selection from database;
- ability to create a new customer/contact while quoting;
- selected products only, no duplicate product lines in one quote;
- product interval pricing table;
- FOB and DDP prices only for current workflow;
- editable quote terms and instructions;
- professional PDF export;
- PDF deletion or storage cleanup workflow;
- internal cost and margin visibility only for administrators;
- no automatic email sending in the current stage.

### 6.4 Quote Pricing Model

The pricing model must reflect the current business logic:

1. Each product has a fixed RMB factory cost.
2. Each product has a unit weight.
3. Ocean freight is maintained as a global assumption, currently RMB 22/kg unless updated.
4. Real-time USD/CNY exchange rate must come from an online or refreshable rate source, not from an old spreadsheet snapshot.
5. FOB cost in USD is based on factory RMB cost divided by exchange rate.
6. DDP cost in USD is based on factory RMB cost plus shipping cost, divided by exchange rate.
7. Target margin is product-specific.
8. Interval pricing applies descending margin or discount logic as quantity increases.
9. Customer-visible quote output must show only Quantity, FOB Unit Price, and DDP Unit Price.
10. Internal cost, pricing breakdown, and margin remain hidden from customers.

The current profit strategy should be stored as structured assumptions, not raw spreadsheet text. It may be optimized later based on market evidence, but changes must be explicit and testable.

### 6.5 Customer Portal

The customer-facing portal is separate from the internal admin system. It should provide:

- public/home pages;
- product browsing;
- sample inventory;
- resource center;
- customer login;
- customer order placement;
- order dashboard;
- order detail and tracking;
- production and shipment status summary;
- feedback submission.

The customer portal must not expose:

- internal cost;
- profit or margin;
- supplier private notes;
- backend file paths;
- raw database IDs if unsafe;
- internal readiness flags;
- internal commercial intelligence.

**RC note (2026-07-25):** The imported legacy customer-site compat API (`CUSTOMER_SITE_COMPAT_ENABLED`, default off) exposes `POST /api/site/customer/orders` as a **non-persistent demo intake** (`draft_intake_not_persisted`) until quote-acceptance workflow is wired. JOOBOO education catalog SKUs/PDF may be `pending` or local-only; do not treat as production-ready catalog data.

### 6.6 Orders, Production, And Logistics

Orders should preferably be created by customers from the customer portal. Internal admin-created orders may remain available for exceptions, but should not be the primary customer workflow.

The order system must support:

- quote reference when a valid quote exists;
- customer order lines and total calculation;
- production milestones;
- shipment plan;
- shipment status summary;
- customer-visible tracking;
- internal-only coordination notes.

Production tracking should use understandable stage names rather than raw status codes. Suggested simplified production stages:

- material preparation;
- cutting and welding;
- polishing;
- coating;
- assembly and testing;
- packing;
- factory release.

### 6.7 Samples And Inventory

The system must support local sample inventory by partner/brand. Customers should be able to see available samples where appropriate, while internal operators maintain actual stock, reservations, and sample workflow.

### 6.8 Resource Center

The resource center must be organized by partner and resource type. It should support:

- official catalogs;
- product brochures;
- color references;
- sample kit references;
- downloadable PDFs and images;
- customer-safe documents only.

Reference resources must be cleanly named and presented. Raw technical labels or internal storage language should not appear in the customer UI.

### 6.9 Feedback

Feedback creates internal review work. It must not:

- auto-reply to customers;
- promise resolution time;
- notify suppliers automatically;
- change order/shipment status automatically.

Feedback should flow back into:

- order review;
- product-market fit;
- quote playbook;
- repeat business recommendations;
- partner performance context.

### 6.10 Commercial Intelligence

Commercial intelligence is a near-term product goal. It should help management answer:

- Which customers are most worth following?
- Which products are worth selling?
- Which quote experiences should be reused?

Secondary questions:

- Which partners are most reliable?
- Where may future revenue come from?

Required commercial intelligence capabilities:

- Win/Loss capture for quotes or opportunities;
- customer decision factors;
- product factors;
- partner factors;
- quote playbook recommendations;
- repeat business recommendations;
- product/partner commercial playbooks;
- account-level commercial memory.

All recommendations must be internal, explainable, and manually confirmed. The system must not invent customer feedback or external evidence.

## 7. Admin Frontend Requirements

The admin frontend should prioritize operational clarity over decorative complexity.

Required admin areas:

- dashboard / workbench;
- customer development;
- companies and contacts;
- growth operations;
- products and partners;
- quote catalog;
- quote creation and detail;
- orders and order detail;
- production and logistics;
- feedback tickets;
- market/commercial intelligence;
- resource management;
- system health and deployment readiness.

UI requirements:

- Chinese operating language by default;
- English allowed for quote PDF customer-facing output and product names;
- no raw enum/status labels visible to operators;
- no duplicate navigation patterns;
- no internal attributes dumped directly into UI;
- no excessive demo/test records in normal views.

## 8. Customer Frontend Requirements

The customer frontend should be a clean portal, not an admin dashboard.

Required characteristics:

- professional landing page that introduces intelliOffice as a connector between U.S. market needs and high-quality manufacturers;
- partner-neutral positioning;
- product/category browsing;
- supplier/manufacturer context where useful;
- sample and resource access;
- order dashboard after login;
- order detail and tracking;
- feedback entry.

The customer frontend should not use admin terminology or expose internal workflows.

## 9. Deployment Requirements

The current deployment target is local-server Docker deployment.

Required deployment expectations:

- backend service container;
- frontend/customer portal container;
- PostgreSQL container or managed local database;
- stable ports and reverse proxy plan;
- persistent volumes for database and approved storage;
- clear `.env.example`;
- no raw tokens or real credentials committed;
- health checks for backend, frontend, database, and static assets.

Windows desktop packaging may remain a future option, but it is not the current priority.

## 10. Safety And Compliance Boundaries

The system must not:

- automatically send email, SMS, LinkedIn messages, or customer notifications;
- automatically notify suppliers or partners;
- automatically change quote/order/opportunity status based on background logic;
- expose cost, margin, supplier private notes, internal scoring, backend paths, storage keys, tokens, or unsafe raw database IDs to customers;
- record raw tokens in Git, docs, logs, screenshots, or chat;
- claim staging validation without real staging credentials and smoke evidence;
- fabricate customer feedback, partner feedback, sign-off, credentials, or external evidence.

## 11. Success Metrics

Near-term success is measured by:

- internal operator can create a quote from selected products and export a professional PDF;
- customer can browse products/resources and create an order through the portal;
- valid quote pricing can be referenced during order creation;
- operator can track order production and shipment status;
- customer can see customer-safe order tracking;
- feedback enters internal review and commercial intelligence;
- product and partner data are governed and not polluted by demo records;
- local Docker deployment can run predictably.

## 12. Near-Term Roadmap

### P0 - Must Stabilize

- Quote interval pricing model.
- Quote PDF quality and storage management.
- Product catalog governance for HOSUN and JOOBOO.
- Customer portal order creation and order tracking.
- Admin/customer frontend separation.
- Local-server Docker deployment path.
- Customer-safe field isolation.

### P1 - Next Product Value

- Quote-to-order price reference.
- Customer/company/contact reuse during quote creation.
- Sample inventory workflow.
- Resource center governance.
- Commercial intelligence: customer value, win/loss, quote playbook, repeat business.

### P2 - Operating Intelligence

- Product/partner commercial playbooks.
- Partner performance context.
- Delivery risk feedback loop.
- Production/logistics dashboard refinement.
- Better import tools for real product/customer/order data.

### P3 - Platform Expansion

- More partner onboarding workflows.
- External integrations after safety design.
- Role-based access control.
- Email delivery automation with explicit human approval.
- Advanced analytics and forecasting.

## 13. Open Questions

1. When should customer order totals strictly require a valid quote?
2. How should expired quote pricing be handled during customer ordering?
3. Which customer portal resources require login?
4. Which PartnerOS data should be shared with partners in a future partner portal, if any?
5. What is the retention policy for generated quote PDFs and uploaded customer files?
6. How should real-time exchange rates be cached and audited?
7. What is the final local-server backup strategy?

