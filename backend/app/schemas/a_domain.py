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
