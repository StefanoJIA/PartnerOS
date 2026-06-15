from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.business_execution import CompanyExecutionContext
from app.schemas.crm import CompanyDetailOut, ContactDetailOut, LeadOut
from app.schemas.lead_workspace import (
    AIOutputWorkspaceBrief,
    FieldVisitWorkspaceBrief,
    InteractionWorkspaceBrief,
    OrderWorkspaceBrief,
    RFQWorkspaceBrief,
    SampleWorkspaceBrief,
    TaskWorkspaceBrief,
)
from app.schemas.partners import PartnerDetailOut
from app.schemas.products import ProductDetailOut, ProductPartnerLinkDetailOut


class ActivitySummaryOut(BaseModel):
    """Counts of activity log rows on the primary object, grouped by action."""

    by_action: dict[str, int]


class ProductInterestSummaryOut(BaseModel):
    tags_from_company: list[str]
    lead_interest_snippets: list[str]
    active_lead_count: int


class CompanyWorkspaceOut(BaseModel):
    company: CompanyDetailOut
    contacts: list[ContactDetailOut]
    leads: list[LeadOut]
    related_rfqs: list[RFQWorkspaceBrief]
    related_samples: list[SampleWorkspaceBrief]
    related_orders: list[OrderWorkspaceBrief]
    related_field_visits: list[FieldVisitWorkspaceBrief]
    recent_interactions: list[InteractionWorkspaceBrief]
    open_tasks: list[TaskWorkspaceBrief]
    recent_ai_outputs: list[AIOutputWorkspaceBrief]
    product_interest_summary: ProductInterestSummaryOut
    activity_summary: ActivitySummaryOut
    business_execution: CompanyExecutionContext | None = None


class CompanySummaryCard(BaseModel):
    id: UUID
    company_name: str
    company_type: str
    website: str | None
    city: str | None
    state: str | None
    country: str | None

    model_config = {"from_attributes": True}


class ContactWorkspaceOut(BaseModel):
    contact: ContactDetailOut
    company: CompanySummaryCard
    related_leads: list[LeadOut]
    related_rfqs: list[RFQWorkspaceBrief]
    related_samples: list[SampleWorkspaceBrief]
    related_orders: list[OrderWorkspaceBrief]
    recent_interactions: list[InteractionWorkspaceBrief]
    open_tasks: list[TaskWorkspaceBrief]
    recent_ai_outputs: list[AIOutputWorkspaceBrief]
    activity_summary: ActivitySummaryOut


class QuotationWorkspaceBrief(BaseModel):
    id: UUID
    rfq_id: UUID | None
    manufacturing_partner_id: UUID | None
    product_id: UUID | None
    unit_price: Decimal | None
    currency: str | None
    moq: int | None
    lead_time: str | None
    valid_until: date | None
    created_at: datetime

    model_config = {"from_attributes": True}


class QualityDocumentBrief(BaseModel):
    id: UUID
    document_type: str
    expiry_date: date | None
    notes: str | None
    file_id: UUID | None

    model_config = {"from_attributes": True}


class PartnerWorkspaceOut(BaseModel):
    partner: PartnerDetailOut
    linked_products: list[ProductDetailOut]
    product_partner_link_details: list[ProductPartnerLinkDetailOut]
    related_rfqs: list[RFQWorkspaceBrief]
    related_quotations: list[QuotationWorkspaceBrief]
    related_samples: list[SampleWorkspaceBrief]
    related_orders: list[OrderWorkspaceBrief]
    quality_documents: list[QualityDocumentBrief]
    recent_interactions: list[InteractionWorkspaceBrief]
    open_tasks: list[TaskWorkspaceBrief]
    recent_ai_outputs: list[AIOutputWorkspaceBrief]
    activity_summary: ActivitySummaryOut


class ProductWorkspaceFileBrief(BaseModel):
    id: UUID
    file_id: UUID
    doc_type: str | None
    original_filename: str | None

    model_config = {"from_attributes": True}


class LinkedPartnerRow(BaseModel):
    link: ProductPartnerLinkDetailOut
    partner: PartnerDetailOut


class PartnerComparisonHints(BaseModel):
    """Rule-based hints; no LLM; order of partner ids is not brand-driven."""

    best_for_sample_partner_id: UUID | None
    best_for_low_moq_partner_id: UUID | None
    best_for_customization_partner_id: UUID | None
    best_for_certification_partner_id: UUID | None


class ProductWorkspaceOut(BaseModel):
    product: ProductDetailOut
    linked_manufacturing_partners: list[PartnerDetailOut]
    product_partner_link_details: list[ProductPartnerLinkDetailOut]
    partner_rows: list[LinkedPartnerRow]
    related_rfqs: list[RFQWorkspaceBrief]
    related_samples: list[SampleWorkspaceBrief]
    related_orders: list[OrderWorkspaceBrief]
    files: list[ProductWorkspaceFileBrief]
    open_tasks: list[TaskWorkspaceBrief]
    recent_ai_outputs: list[AIOutputWorkspaceBrief]
    partner_comparison: PartnerComparisonHints
    activity_summary: ActivitySummaryOut
