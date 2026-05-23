from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.crm import CompanyDetailOut, ContactOut, LeadOut


class LeadIntelligenceWorkflowOut(BaseModel):
    """A-domain workbench payload: company → contact → intel → score → actions."""

    lead: LeadOut
    company: CompanyDetailOut
    primary_contact: ContactOut | None
    intelligence_score: int = Field(ge=0, le=100)
    score_breakdown: dict[str, int]
    suggested_next_actions: list[str]
    market_intelligence_count: int
    market_intelligence_preview_ids: list[UUID]
    market_fit_segments: list[str] = Field(
        default_factory=list,
        description=(
            "Explainable tags: lift_system_signal, general_office_furniture_only (D5.1 weak industry fit), "
            "oem_odm_fit, medical_vertical, education_vertical, heavy_duty_fit, project_based_furniture"
        ),
    )


class TouchpointCreate(BaseModel):
    """Log interaction on lead and refresh sales next step (D5 closed loop)."""

    interaction_type: str = Field(..., min_length=1, max_length=64)
    channel: str = Field(..., min_length=1, max_length=64)
    subject: str | None = Field(None, max_length=512)
    content: str | None = None
    summary: str | None = None
    direction: str | None = Field(None, max_length=32)
    next_action: str | None = None
    next_action_due_date: date | None = None
    interaction_next_action: str | None = None
    interaction_next_action_due_date: date | None = None


class OutreachDraftOut(BaseModel):
    """Human-reviewed outreach draft (D5.2.4 — display/copy only, not sent)."""

    channel: str
    language: str
    tone: str
    product_focus: str
    company_name: str
    segments: list[str]
    linkedin_connect_note: str | None = None
    email_subject: str | None = None
    email_body: str | None = None
    suggested_next_action: str
    suggested_touchpoint_type: str


class LeadIntakePreviewRequest(BaseModel):
    csv_text: str = Field(..., min_length=1)


class LeadIntakePreviewRowOut(BaseModel):
    row_number: int
    company_name: str
    contact_name: str
    website: str
    company_type: str
    source: str
    likely_segments: list[str]
    priority_hint: str
    missing_fields: list[str]
    duplicate_status: str
    recommended_next_action: str
    status: str
    warnings: list[str] = Field(default_factory=list)


class LeadIntakePreviewSummaryOut(BaseModel):
    total: int
    ok: int
    warnings: int
    errors: int
    duplicates: int
    ready_to_import: int


class LeadIntakePreviewResponse(BaseModel):
    rows: list[LeadIntakePreviewRowOut]
    summary: LeadIntakePreviewSummaryOut
    header_warnings: list[str] = Field(default_factory=list)


class LeadIntakeApplyRequest(BaseModel):
    csv_text: str = Field(..., min_length=1)
    confirm: bool = False


class LeadIntakeApplyResponse(BaseModel):
    created_companies: int
    skipped_duplicates: int
    created_contacts: int
    linked_leads: int
    warnings: list[str] = Field(default_factory=list)


class LeadCompletenessRowOut(BaseModel):
    lead_id: str
    company_name: str
    lead_name: str
    score: int
    status: str
    status_label: str
    missing_fields: list[str]
    recommended_research_action: str
    segment: str | None = None
    segments: list[str] = Field(default_factory=list)
    next_action: str | None = None
    last_touchpoint: str | None = None


class LeadCompletenessSummaryOut(BaseModel):
    total: int
    complete: int
    ready_for_outreach: int
    needs_contact_research: int
    incomplete: int
    missing_website: int
    missing_contact_method: int


class LeadCompletenessResponse(BaseModel):
    rows: list[LeadCompletenessRowOut]
    summary: LeadCompletenessSummaryOut


class ContactResearchCompanyIn(BaseModel):
    website: str | None = None
    company_type: str | None = None
    notes: str | None = None


class ContactResearchContactIn(BaseModel):
    name: str | None = None
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None


class ContactResearchLeadIn(BaseModel):
    next_action: str | None = None


class ContactResearchRequest(BaseModel):
    company: ContactResearchCompanyIn | None = None
    contact: ContactResearchContactIn | None = None
    lead: ContactResearchLeadIn | None = None
    touchpoint_note: str | None = None


class ContactResearchResponse(BaseModel):
    lead_id: str
    interaction_id: str
    completeness: LeadCompletenessRowOut


class LeadTimelineItemOut(BaseModel):
    id: str
    timestamp: str | None
    type: str
    channel: str
    title: str
    summary: str | None = None
    is_manual_send: bool = False
    is_contact_research: bool = False


class LeadTimelineStatsOut(BaseModel):
    total_touchpoints: int
    manual_sent_count: int
    contact_research_count: int
    last_channel: str | None = None


class LeadTimelineOut(BaseModel):
    lead_id: str
    company_name: str
    next_action: str | None = None
    next_follow_up_date: str | None = None
    due_status: str | None = None
    days_until_due: int | None = None
    last_touchpoint_at: str | None = None
    follow_up_hint: str
    items: list[LeadTimelineItemOut]
    stats: LeadTimelineStatsOut


class FollowUpScheduleRequest(BaseModel):
    next_follow_up_date: date | None = None
    next_action: str | None = None
    status_note: str | None = None
    clear_date: bool = False


class FollowUpScheduleResponse(BaseModel):
    lead_id: str
    company_name: str
    next_action: str | None = None
    next_follow_up_date: str | None = None
    due_status: str
    days_until_due: int | None = None
    interaction_id: str


class FollowUpQueueRowOut(BaseModel):
    lead_id: str
    company_name: str
    lead_score: int
    segments: list[str] = Field(default_factory=list)
    next_action: str | None = None
    next_follow_up_date: str | None = None
    due_status: str
    days_until_due: int | None = None
    last_touchpoint_at: str | None = None
    waiting_reply: bool = False
    recommended_action: str


class FollowUpQueueSummaryOut(BaseModel):
    total: int
    overdue: int
    due_today: int
    due_soon: int
    no_follow_up_date: int
    waiting_reply: int


class FollowUpQueueResponse(BaseModel):
    summary: FollowUpQueueSummaryOut
    rows: list[FollowUpQueueRowOut]


class DailyOpsSummaryCountsOut(BaseModel):
    total_leads: int = 0
    overdue: int = 0
    due_today: int = 0
    due_soon: int = 0
    high_priority: int = 0
    needs_contact_research: int = 0
    ready_for_outreach: int = 0
    waiting_reply: int = 0
    needs_enrichment: int = 0


class DailyOpsFocusItemOut(BaseModel):
    lead_id: str
    company_name: str
    reason: str
    segments: list[str] = Field(default_factory=list)
    due_status: str
    next_action: str | None = None
    priority: str = "normal"
    lead_score: int = 0


class DailyOpsQuickActionOut(BaseModel):
    label: str
    path: str


class DailyOpsSafetyOut(BaseModel):
    automatic_sending_enabled: bool = False
    linkedin_automation_enabled: bool = False
    outlook_integration_enabled: bool = False


class DailyOpsRecentOutreachOut(BaseModel):
    lead_id: str
    company_name: str
    interaction_type: str | None = None
    channel: str
    timestamp: str | None = None
    next_action: str | None = None
    type: str | None = None
    summary: str | None = None
    badge: str | None = None
    is_manual_send: bool = False
    is_contact_research: bool = False


class DailyOpsRecentActivityOut(BaseModel):
    lead_id: str
    company_name: str
    type: str
    channel: str
    summary: str | None = None
    timestamp: str | None = None
    badge: str
    is_manual_send: bool = False
    is_contact_research: bool = False
    next_action: str | None = None


class DailyOpsSummaryResponse(BaseModel):
    summary: DailyOpsSummaryCountsOut
    today_focus: list[DailyOpsFocusItemOut]
    recent_activity: list[DailyOpsRecentActivityOut] = Field(default_factory=list)
    recent_manual_outreach: list[DailyOpsRecentActivityOut] = Field(default_factory=list)
    recent_contact_research: list[DailyOpsRecentActivityOut] = Field(default_factory=list)
    recent_outreach: list[DailyOpsRecentOutreachOut] = Field(default_factory=list)
    quick_actions: list[DailyOpsQuickActionOut]
    safety: DailyOpsSafetyOut
    warnings: list[str] = Field(default_factory=list)
    degraded: bool = False


class DailyWorkSummaryCountsOut(BaseModel):
    manual_outreach_sent: int = 0
    contact_research_updates: int = 0
    follow_ups_scheduled: int = 0
    drafts_generated: int | None = None
    leads_touched: int = 0
    overdue_remaining: int = 0
    due_today_remaining: int = 0
    due_soon: int = 0
    needs_contact_research: int = 0
    high_priority_remaining: int = 0


class DailyWorkHighlightOut(BaseModel):
    lead_id: str
    company_name: str
    action: str
    next_action: str | None = None


class DailyWorkTomorrowFocusOut(BaseModel):
    lead_id: str
    company_name: str
    reason: str
    next_action: str | None = None


class DailyWorkSummaryResponse(BaseModel):
    date: str
    summary: DailyWorkSummaryCountsOut
    highlights: list[DailyWorkHighlightOut] = Field(default_factory=list)
    tomorrow_focus: list[DailyWorkTomorrowFocusOut] = Field(default_factory=list)
    copyable_summary: str
    warnings: list[str] = Field(default_factory=list)
    degraded: bool = False


class ProductFitOut(BaseModel):
    """D5.12 — derived product fit and project opportunity (read-only, no quotes)."""

    lead_id: str
    company_name: str
    recommended_product_focus: list[str] = Field(default_factory=list)
    project_opportunity_score: int = Field(ge=0, le=100)
    opportunity_level: str
    project_type: str
    quote_readiness: str
    sample_readiness: str
    missing_quote_info: list[str] = Field(default_factory=list)
    recommended_discovery_questions: list[str] = Field(default_factory=list)
    recommended_next_product_action: str
    sales_angle: str
    warnings: list[str] = Field(default_factory=list)


class ProductOpportunityBoardRowOut(BaseModel):
    lead_id: str
    company_name: str
    project_opportunity_score: int
    opportunity_score: int | None = None
    opportunity_level: str
    project_type: str
    quote_readiness: str
    sample_readiness: str
    recommended_product_focus: list[str] = Field(default_factory=list)
    missing_quote_info: list[str] = Field(default_factory=list)
    recommended_next_product_action: str | None = None
    sales_angle: str | None = None
    next_action: str | None = None
    follow_up_date: str | None = None
    due_status: str | None = None


class ProductOpportunityBoardSummaryOut(BaseModel):
    total: int = 0
    high_opportunity: int = 0
    promising: int = 0
    quote_ready: int = 0
    almost_ready: int = 0
    almost_quote_ready: int = 0
    sample_ready: int = 0
    needs_specs: int = 0
    lifting_system_fit: int = 0
    project_supply_fit: int = 0
    education_fit: int = 0
    medical_fit: int = 0
    oem_odm_fit: int = 0
    oem_odm_potential: int = 0


class ProductOpportunitySafetyOut(BaseModel):
    automatic_quote_creation: bool = False
    automatic_sending_enabled: bool = False
    price_promises_enabled: bool = False
    inventory_promises_enabled: bool = False


class ProductOpportunityBoardResponse(BaseModel):
    summary: ProductOpportunityBoardSummaryOut
    missing_info_summary: dict[str, int] = Field(default_factory=dict)
    rows: list[ProductOpportunityBoardRowOut]
    safety: ProductOpportunitySafetyOut = Field(default_factory=ProductOpportunitySafetyOut)
    warnings: list[str] = Field(default_factory=list)
    degraded: bool = False


class PreQuoteSafetyOut(BaseModel):
    quote_created: bool = False
    pricing_generated: bool = False
    inventory_promised: bool = False
    certification_promised: bool = False
    lead_time_promised: bool = False
    automatic_sending_enabled: bool = False


class PreQuoteBriefOut(BaseModel):
    """D5.14 — pre-quote and sample prep brief (read-only, no quote creation)."""

    lead_id: str
    company_name: str
    quote_readiness: str
    sample_readiness: str
    recommended_product_focus: list[str] = Field(default_factory=list)
    project_type: str
    opportunity_score: int = Field(ge=0, le=100)
    missing_quote_info: list[str] = Field(default_factory=list)
    quote_preparation_checklist: list[str] = Field(default_factory=list)
    sample_preparation_checklist: list[str] = Field(default_factory=list)
    recommended_customer_questions: list[str] = Field(default_factory=list)
    recommended_internal_next_steps: list[str] = Field(default_factory=list)
    recommended_next_action: str
    pre_quote_brief_text: str
    sample_discussion_brief_text: str
    warnings: list[str] = Field(default_factory=list)
    safety: PreQuoteSafetyOut = Field(default_factory=PreQuoteSafetyOut)


class PreQuoteBoardRowOut(BaseModel):
    lead_id: str
    company_name: str
    quote_readiness: str
    sample_readiness: str
    missing_quote_info_count: int = 0
    recommended_next_action: str | None = None
    recommended_product_focus: list[str] = Field(default_factory=list)
    opportunity_score: int = 0


class PreQuoteBoardSummaryOut(BaseModel):
    total: int = 0
    quote_prep_ready: int = 0
    sample_discussion_ready: int = 0
    needs_specs_before_quote: int = 0
    almost_ready: int = 0


class PreQuoteBoardResponse(BaseModel):
    summary: PreQuoteBoardSummaryOut
    rows: list[PreQuoteBoardRowOut]
    safety: PreQuoteSafetyOut = Field(default_factory=PreQuoteSafetyOut)
    warnings: list[str] = Field(default_factory=list)
    degraded: bool = False


class ProductAwareDraftRequest(BaseModel):
    channel: str = "email_intro"
    draft_purpose: str = "product_discovery"
    tone: str = "concise"
    language: str = "en"
    include_questions: bool = True
    include_product_brief: bool = True


class ProductAwareDraftSourceContextOut(BaseModel):
    product_focus: list[str] = Field(default_factory=list)
    quote_readiness: str
    sample_readiness: str
    missing_quote_info: list[str] = Field(default_factory=list)


class ProductAwareDraftResponse(BaseModel):
    lead_id: str
    company_name: str
    channel: str
    draft_purpose: str
    tone: str
    language: str
    subject: str | None = None
    body: str | None = None
    linkedin_note: str | None = None
    questions: list[str] = Field(default_factory=list)
    recommended_next_action: str
    suggested_follow_up_days: int = 5
    source_context: ProductAwareDraftSourceContextOut
    safety: PreQuoteSafetyOut = Field(default_factory=PreQuoteSafetyOut)
    warnings: list[str] = Field(default_factory=list)


class QuoteHandoffBriefOut(BaseModel):
    """D5.18 — soft quote handoff brief (read-only, no quote creation)."""

    lead_id: str
    company_name: str
    handoff_status: str
    handoff_priority: str
    quote_readiness: str
    sample_readiness: str
    opportunity_score: int = Field(default=0, ge=0, le=100)
    recommended_partner_route: list[str] = Field(default_factory=list)
    recommended_product_scope: list[str] = Field(default_factory=list)
    known_context: list[str] = Field(default_factory=list)
    missing_customer_info: list[str] = Field(default_factory=list)
    supplier_preparation_notes: list[str] = Field(default_factory=list)
    customer_clarification_questions: list[str] = Field(default_factory=list)
    recommended_next_step: str
    quote_handoff_brief_text: str
    supplier_notes_text: str
    customer_questions_text: str
    safety: PreQuoteSafetyOut = Field(default_factory=PreQuoteSafetyOut)
    warnings: list[str] = Field(default_factory=list)


class QuoteHandoffBoardRowOut(BaseModel):
    lead_id: str
    company_name: str
    handoff_status: str
    handoff_priority: str
    quote_readiness: str
    sample_readiness: str
    recommended_partner_route: list[str] = Field(default_factory=list)
    missing_customer_info_count: int = 0
    opportunity_score: int = 0


class QuoteHandoffBoardSummaryOut(BaseModel):
    total: int = 0
    ready_for_manual_quote_prep: int = 0
    needs_customer_clarification: int = 0
    not_ready: int = 0
    high_priority: int = 0
    lifting_system_route: int = 0
    jooboo_route: int = 0
    project_supply_route: int = 0
    oem_odm_route: int = 0


class QuoteHandoffBoardResponse(BaseModel):
    summary: QuoteHandoffBoardSummaryOut
    rows: list[QuoteHandoffBoardRowOut]
    safety: PreQuoteSafetyOut = Field(default_factory=PreQuoteSafetyOut)
    warnings: list[str] = Field(default_factory=list)
    degraded: bool = False


class QuoteInputCustomerOut(BaseModel):
    company_name: str
    contact_name: str | None = None
    contact_method_available: bool = False


class QuoteInputProductIntentOut(BaseModel):
    product_focus: list[str] = Field(default_factory=list)
    project_type: str = "unknown"
    sample_readiness: str = "not_ready"
    quote_readiness: str = "not_ready"


class QuoteInputKnownRequirementsOut(BaseModel):
    quantity_or_volume: str | None = None
    product_type: str | None = None
    frame_size_or_desktop_size: str | None = None
    load_capacity_requirement: str | None = None
    color_or_finish: str | None = None
    delivery_location: str | None = None
    project_timeline: str | None = None
    certification_requirement: str | None = None
    sample_quantity: str | None = None
    oem_customization_requirement: str | None = None
    component_category: str | None = None


class QuoteInputFieldsOut(BaseModel):
    customer: QuoteInputCustomerOut
    product_intent: QuoteInputProductIntentOut
    known_requirements: QuoteInputKnownRequirementsOut
    missing_requirements: list[str] = Field(default_factory=list)
    recommended_questions: list[str] = Field(default_factory=list)
    supplier_preparation_notes: list[str] = Field(default_factory=list)


class QuoteInputContractOut(BaseModel):
    """D5.19 — quote input contract for Phase 2 handoff (read-only, no quote creation)."""

    lead_id: str
    company_name: str
    handoff_status: str
    quote_module_readiness: str
    recommended_partner_route: list[str] = Field(default_factory=list)
    recommended_product_scope: list[str] = Field(default_factory=list)
    quote_input_fields: QuoteInputFieldsOut
    copyable_json: str
    copyable_handoff_summary: str
    safety: PreQuoteSafetyOut = Field(default_factory=PreQuoteSafetyOut)
    warnings: list[str] = Field(default_factory=list)


class QuoteInputContractBoardRowOut(BaseModel):
    lead_id: str
    company_name: str
    handoff_status: str
    quote_module_readiness: str
    recommended_partner_route: list[str] = Field(default_factory=list)
    missing_requirements_count: int = 0


class QuoteInputContractBoardSummaryOut(BaseModel):
    total: int = 0
    ready_for_phase2_quote_draft: int = 0
    needs_more_customer_info: int = 0
    not_quote_ready: int = 0
    lifting_system_route: int = 0
    jooboo_route: int = 0
    project_supply_route: int = 0
    oem_odm_route: int = 0


class QuoteInputContractBoardResponse(BaseModel):
    summary: QuoteInputContractBoardSummaryOut
    rows: list[QuoteInputContractBoardRowOut]
    warnings: list[str] = Field(default_factory=list)
    degraded: bool = False
