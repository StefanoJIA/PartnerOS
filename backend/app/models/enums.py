from enum import Enum


class RoleName(str, Enum):
    admin = "Admin"
    sales = "Sales"
    supplier_manager = "Supplier Manager"
    operations = "Operations"
    viewer = "Viewer"


class CompanyType(str, Enum):
    office_furniture_dealer = "Office Furniture Dealer"
    furniture_distributor = "Furniture Distributor"
    education_furniture_company = "Education Furniture Company"
    interior_design_firm = "Interior Design Firm"
    workplace_solution_provider = "Workplace Solution Provider"
    school_college = "School / College"
    facility_management = "Facility Management"
    corporate_buyer = "Corporate Buyer"
    ergonomic_product_company = "Ergonomic Product Company"
    healthcare_furniture_company = "Healthcare Furniture Company"
    manufacturer = "Manufacturer"
    manufacturing_partner = "Manufacturing Partner"
    other = "Other"


class LinkedInStatus(str, Enum):
    not_contacted = "Not Contacted"
    note_sent = "Note Sent"
    connected = "Connected"
    replied = "Replied"
    interested = "Interested"
    follow_up_needed = "Follow-up Needed"
    meeting_requested = "Meeting Requested"
    sample_discussed = "Sample Discussed"
    dormant = "Dormant"


class ContactType(str, Enum):
    buyer = "Buyer"
    owner = "Owner"
    sales_manager = "Sales Manager"
    procurement_manager = "Procurement Manager"
    facility_manager = "Facility Manager"
    designer = "Designer"
    project_manager = "Project Manager"
    supplier_representative = "Supplier Representative"
    other = "Other"


class LeadSource(str, Enum):
    linkedin = "LinkedIn"
    email = "Email"
    constant_contact = "Constant Contact"
    field_visit = "Field Visit"
    trade_show = "Trade Show"
    website = "Website"
    referral = "Referral"
    existing_customer = "Existing Customer"
    manual_research = "Manual Research"
    other = "Other"


class LeadType(str, Enum):
    strategic_partner = "Strategic Partner"
    project_buyer = "Project Buyer"
    product_fit_lead = "Product Fit Lead"
    channel_lead = "Channel Lead"
    sample_opportunity = "Sample Opportunity"
    rfq_opportunity = "RFQ Opportunity"
    manufacturing_partner_candidate = "Manufacturing Partner Candidate"


class LeadStage(str, Enum):
    new = "New"
    researched = "Researched"
    contacted = "Contacted"
    connected = "Connected"
    replied = "Replied"
    interested = "Interested"
    meeting_scheduled = "Meeting Scheduled"
    sample_requested = "Sample Requested"
    rfq_created = "RFQ Created"
    quotation_sent = "Quotation Sent"
    negotiating = "Negotiating"
    won = "Won"
    lost = "Lost"
    dormant = "Dormant"


class InteractionType(str, Enum):
    linkedin_note = "LinkedIn Note"
    linkedin_message = "LinkedIn Message"
    email = "Email"
    phone_call = "Phone Call"
    meeting = "Meeting"
    field_visit = "Field Visit"
    sample_discussion = "Sample Discussion"
    quotation_discussion = "Quotation Discussion"
    supplier_discussion = "Supplier Discussion"
    internal_note = "Internal Note"


class InteractionChannel(str, Enum):
    linkedin = "LinkedIn"
    email = "Email"
    phone = "Phone"
    in_person = "In Person"
    constant_contact = "Constant Contact"
    trade_show = "Trade Show"
    website = "Website"
    internal = "Internal"


class TaskStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    done = "done"
    cancelled = "cancelled"


class PartnerType(str, Enum):
    lifting_system_manufacturer = "Lifting System Manufacturer"
    education_furniture_manufacturer = "Education Furniture Manufacturer"
    office_furniture_manufacturer = "Office Furniture Manufacturer"
    tabletop_manufacturer = "Tabletop Manufacturer"
    seating_manufacturer = "Seating Manufacturer"
    storage_manufacturer = "Storage Manufacturer"
    medical_furniture_manufacturer = "Medical Furniture Manufacturer"
    custom_furniture_manufacturer = "Custom Furniture Manufacturer"
    hardware_component_supplier = "Hardware / Component Supplier"
    packaging_supplier = "Packaging Supplier"
    other = "Other"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RFQStatus(str, Enum):
    draft = "Draft"
    waiting_internal_review = "Waiting for Internal Review"
    waiting_partner_quote = "Waiting for Partner Quote"
    partner_quoted = "Partner Quoted"
    internal_costing = "Internal Costing"
    quotation_prepared = "Quotation Prepared"
    sent_to_customer = "Sent to Customer"
    customer_reviewing = "Customer Reviewing"
    negotiating = "Negotiating"
    accepted = "Accepted"
    rejected = "Rejected"
    closed = "Closed"


class SampleStatus(str, Enum):
    requested = "Requested"
    internal_review = "Internal Review"
    waiting_for_partner = "Waiting for Partner"
    ready = "Ready"
    shipped = "Shipped"
    delivered = "Delivered"
    feedback_received = "Feedback Received"
    converted = "Converted"
    closed = "Closed"


class RFQPartnerCandidateStatus(str, Enum):
    candidate = "Candidate"
    quote_requested = "Quote Requested"
    quote_received = "Quote Received"
    under_review = "Under Review"
    preferred = "Preferred"
    not_suitable = "Not Suitable"
    rejected = "Rejected"


class OrderProductionStatus(str, Enum):
    draft = "Draft"
    order_confirmed = "Order Confirmed"
    material_preparation = "Material Preparation"
    production = "Production"
    assembly = "Assembly"
    testing = "Testing"
    packaging = "Packaging"
    ready_to_ship = "Ready to Ship"
    shipped = "Shipped"
    delivered = "Delivered"
    closed = "Closed"


class OrderShippingStatus(str, Enum):
    not_started = "Not Started"
    booking = "Booking"
    trucking_to_port = "Trucking to Port"
    customs_declaration = "Customs Declaration"
    vessel_departed = "Vessel Departed"
    vessel_arrived = "Vessel Arrived"
    us_customs = "U.S. Customs"
    warehouse_inbound = "Warehouse Inbound"
    final_delivery = "Final Delivery"
    delivered = "Delivered"


class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class FieldVisitStatus(str, Enum):
    draft = "draft"
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class VisitResult(str, Enum):
    not_visited = "Not Visited"
    visited = "Visited"
    no_decision_maker = "No Decision Maker"
    interested = "Interested"
    requested_brochure = "Requested Brochure"
    requested_sample = "Requested Sample"
    requested_quotation = "Requested Quotation"
    meeting_scheduled = "Meeting Scheduled"
    not_interested = "Not Interested"
    follow_up_needed = "Follow-up Needed"


class AITaskType(str, Enum):
    linkedin_note = "linkedin_note"
    linkedin_follow_up = "linkedin_follow_up"
    email_generation = "email_generation"
    customer_profile = "customer_profile"
    product_recommendation = "product_recommendation"
    partner_recommendation = "partner_recommendation"
    supplier_risk_summary = "supplier_risk_summary"
    rfq_summary = "rfq_summary"
    quotation_analysis = "quotation_analysis"
    field_visit_brief = "field_visit_brief"
    order_update_email = "order_update_email"
    market_trend_summary = "market_trend_summary"
    product_sales_description = "product_sales_description"


class CustomerProjectRequestStatus(str, Enum):
    submitted = "submitted"
    triage = "triage"
    needs_information = "needs_information"
    quote_ready = "quote_ready"
    converted = "converted"
    declined = "declined"


class CustomerProjectRequestPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class PartnerLifecycle(str, Enum):
    candidate = "candidate"
    onboarding = "onboarding"
    active = "active"
    paused = "paused"
    legacy = "legacy"
    archived = "archived"


class BenchmarkSourceType(str, Enum):
    public_reference = "PUBLIC_REFERENCE"
    partner_provided = "PARTNER_PROVIDED"
    authorized_catalog = "AUTHORIZED_CATALOG"
    internal_fixture = "INTERNAL_FIXTURE"


class FieldVerificationStatus(str, Enum):
    fact = "fact"
    inferred = "inferred"
    pending_verification = "pending_verification"


class SupplierDiscoveryStatus(str, Enum):
    discovered = "discovered"
    contacted = "contacted"
    information_requested = "information_requested"
    evaluating = "evaluating"
    sample_requested = "sample_requested"
    sample_received = "sample_received"
    qualified = "qualified"
    active = "active"
    rejected = "rejected"
    paused = "paused"


class QualificationDimensionStatus(str, Enum):
    pass_ = "PASS"
    partial = "PARTIAL"
    unknown = "UNKNOWN"
    fail = "FAIL"


class SampleEvaluationResult(str, Enum):
    pass_ = "pass"
    conditional = "conditional"
    fail = "fail"


class BuildAction(str, Enum):
    build = "build"
    integrate = "integrate"
    do_not_build = "do-not-build"


class FitDimensionStatus(str, Enum):
    match = "MATCH"
    partial = "PARTIAL"
    unknown = "UNKNOWN"
    not_supported = "NOT_SUPPORTED"


class CandidateRole(str, Enum):
    primary = "primary"
    alternate = "alternate"
    engineering_review = "engineering_review"


class CandidateSourceType(str, Enum):
    partner = "partner"
    supplier_discovery = "supplier_discovery"
    benchmark = "benchmark"


class SupplierRelationshipType(str, Enum):
    public_candidate = "PUBLIC_CANDIDATE"
    internal_research = "INTERNAL_RESEARCH"
    qualified_supplier = "QUALIFIED_SUPPLIER"


class SupplierEvidenceStatus(str, Enum):
    verified_public = "verified_public"
    partial_public = "partial_public"
    pending_review = "pending_review"
    unknown = "UNKNOWN"


class SupplierDevelopmentTaskType(str, Enum):
    initial_research = "initial_research"
    contact_prep = "contact_prep"
    information_request = "information_request"
    catalog_requested = "catalog_requested"
    price_list_requested = "price_list_requested"
    certification_requested = "certification_requested"
    sample_requested = "sample_requested"
    sample_follow_up = "sample_follow_up"
    qualification_review = "qualification_review"


class CommercialPilotIndustry(str, Enum):
    lifting_systems = "lifting_systems"
    education_furniture = "education_furniture"
    contract_office = "contract_office"


class CommercialPilotStatus(str, Enum):
    draft = "draft"
    running = "running"
    quote_blocked = "quote_blocked"
    mr_pending = "mr_pending"
    completed = "completed"


class ChannelLeadSource(str, Enum):
    direct = "direct"
    referral = "referral"
    trade_show = "trade_show"
    website = "website"
    dealer = "dealer"
    alibaba = "Alibaba"
    made_in_china = "Made-in-China"
    thomasnet = "Thomasnet"
    manual = "manual"
    other = "other"


class PlatformBuildPriority(str, Enum):
    p0 = "P0"
    p1 = "P1"
    p2 = "P2"


class ObjectType(str, Enum):
    company = "company"
    contact = "contact"
    lead = "lead"
    manufacturing_partner = "manufacturing_partner"
    product = "product"
    rfq = "rfq"
    sample = "sample"
    order = "order"
    field_visit = "field_visit"
    user = "user"
    customer_project_request = "customer_project_request"
