from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.constants.status_enums import RFQ_CANDIDATE_STATUSES, RFQ_STATUSES
from app.schemas.lead_workspace import (
    AIOutputWorkspaceBrief,
    InteractionWorkspaceBrief,
    OrderWorkspaceBrief,
    SampleWorkspaceBrief,
    TaskWorkspaceBrief,
)
from app.services.quotation_comparison import QuotationComparisonOut


class RFQCreate(BaseModel):
    lead_id: UUID | None = None
    company_id: UUID | None = None
    contact_id: UUID | None = None
    customer_requirement: str | None = None
    quantity: int | None = None
    target_price: Decimal | None = None
    target_delivery_date: date | None = None
    required_certifications: str | None = None
    packaging_requirement: str | None = None
    shipping_requirement: str | None = None
    status: str = "Draft"
    notes: str | None = None

    @field_validator("status")
    @classmethod
    def _st(cls, v: str) -> str:
        if v not in RFQ_STATUSES:
            raise ValueError(f"Invalid RFQ status; must be one of: {sorted(RFQ_STATUSES)}")
        return v


class RFQUpdate(BaseModel):
    customer_requirement: str | None = None
    quantity: int | None = None
    target_price: Decimal | None = None
    target_delivery_date: date | None = None
    required_certifications: str | None = None
    packaging_requirement: str | None = None
    shipping_requirement: str | None = None
    status: str | None = None
    ai_requirement_summary: str | None = None
    ai_recommended_partners: str | None = None
    notes: str | None = None

    @field_validator("status")
    @classmethod
    def _st_u(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in RFQ_STATUSES:
            raise ValueError(f"Invalid RFQ status; must be one of: {sorted(RFQ_STATUSES)}")
        return v


class RFQStatusBody(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _st(cls, v: str) -> str:
        if v not in RFQ_STATUSES:
            raise ValueError(f"Invalid RFQ status; must be one of: {sorted(RFQ_STATUSES)}")
        return v


class RFQOut(BaseModel):
    id: UUID
    rfq_number: str
    status: str
    company_id: UUID | None
    lead_id: UUID | None

    model_config = {"from_attributes": True}


class RFQDetailOut(BaseModel):
    id: UUID
    rfq_number: str
    lead_id: UUID | None
    company_id: UUID | None
    contact_id: UUID | None
    customer_requirement: str | None
    quantity: int | None
    target_price: Decimal | None
    target_delivery_date: date | None
    required_certifications: str | None
    packaging_requirement: str | None
    shipping_requirement: str | None
    status: str
    owner_user_id: UUID | None
    ai_requirement_summary: str | None
    ai_recommended_partners: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RFQListItemOut(BaseModel):
    id: UUID
    rfq_number: str
    status: str
    company_id: UUID | None
    company_name: str | None = None
    contact_id: UUID | None
    contact_label: str | None = None
    lead_id: UUID | None
    lead_name: str | None = None
    target_delivery_date: date | None
    required_certifications: str | None
    created_at: datetime
    updated_at: datetime
    has_quotation: bool = False


class RFQItemCreate(BaseModel):
    product_id: UUID | None = None
    quantity: int | None = None
    spec_notes: str | None = None
    target_price: Decimal | None = None
    required_certifications: str | None = None
    packaging_requirement: str | None = None
    shipping_requirement: str | None = None


class RFQItemUpdate(BaseModel):
    product_id: UUID | None = None
    quantity: int | None = None
    spec_notes: str | None = None
    target_price: Decimal | None = None
    required_certifications: str | None = None
    packaging_requirement: str | None = None
    shipping_requirement: str | None = None


class ProductBrief(BaseModel):
    id: UUID
    product_name: str
    product_category: str | None

    model_config = {"from_attributes": True}


class RFQItemOut(BaseModel):
    id: UUID
    rfq_id: UUID
    product_id: UUID | None
    product: ProductBrief | None = None
    quantity: int | None
    spec_notes: str | None
    target_price: Decimal | None
    required_certifications: str | None
    packaging_requirement: str | None
    shipping_requirement: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PartnerBrief(BaseModel):
    id: UUID
    partner_name: str
    partner_type: str

    model_config = {"from_attributes": True}


class RFQPartnerCandidateCreate(BaseModel):
    partner_id: UUID
    rank: int | None = None
    partner_status: str | None = "Candidate"
    is_preferred: bool = False
    capability_level: str | None = None
    partner_moq: int | None = None
    lead_time_days: int | None = None
    partner_price_range: str | None = None
    sample_available: bool | None = None
    certification_status: str | None = None
    product_fit: str | None = None
    notes: str | None = None

    @field_validator("partner_status")
    @classmethod
    def _ps(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in RFQ_CANDIDATE_STATUSES:
            raise ValueError(f"Invalid partner_status; must be one of: {sorted(RFQ_CANDIDATE_STATUSES)}")
        return v


class RFQPartnerCandidateUpdate(BaseModel):
    rank: int | None = None
    partner_status: str | None = None
    is_preferred: bool | None = None
    capability_level: str | None = None
    partner_moq: int | None = None
    lead_time_days: int | None = None
    partner_price_range: str | None = None
    sample_available: bool | None = None
    certification_status: str | None = None
    product_fit: str | None = None
    quote_requested_at: datetime | None = None
    quote_received_at: datetime | None = None
    notes: str | None = None

    @field_validator("partner_status")
    @classmethod
    def _ps_u(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in RFQ_CANDIDATE_STATUSES:
            raise ValueError(f"Invalid partner_status; must be one of: {sorted(RFQ_CANDIDATE_STATUSES)}")
        return v


class RFQPartnerCandidateOut(BaseModel):
    id: UUID
    rfq_id: UUID
    partner_id: UUID
    rank: int | None
    partner_status: str | None
    is_preferred: bool
    capability_level: str | None
    partner_moq: int | None
    lead_time_days: int | None
    partner_price_range: str | None
    sample_available: bool | None
    certification_status: str | None
    product_fit: str | None
    quote_requested_at: datetime | None
    quote_received_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RFQPartnerCandidateWithPartnerOut(RFQPartnerCandidateOut):
    partner: PartnerBrief


class QuotationItemOut(BaseModel):
    id: UUID
    quotation_id: UUID
    product_id: UUID | None
    quantity: int | None
    unit_price: Decimal | None
    created_at: datetime

    model_config = {"from_attributes": True}


class QuotationDetailOut(BaseModel):
    id: UUID
    rfq_id: UUID | None
    manufacturing_partner_id: UUID | None
    product_id: UUID | None
    quantity: int | None
    unit_price: Decimal | None
    currency: str | None
    incoterm: str | None
    moq: int | None
    lead_time: str | None
    sample_cost: Decimal | None
    tooling_cost: Decimal | None
    packaging_cost: Decimal | None
    estimated_shipping_cost: Decimal | None
    landed_cost: Decimal | None
    target_margin: Decimal | None
    notes: str | None
    valid_until: date | None
    created_at: datetime
    updated_at: datetime
    partner: PartnerBrief | None = None
    product: ProductBrief | None = None
    lines: list[QuotationItemOut] = []

    model_config = {"from_attributes": True}


class RfqFileBrief(BaseModel):
    id: UUID
    file_id: UUID
    original_filename: str
    purpose: str | None


class ActivitySummaryOut(BaseModel):
    by_action: dict[str, int]


class CompanySummaryMini(BaseModel):
    id: UUID
    company_name: str

    model_config = {"from_attributes": True}


class ContactSummaryMini(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str | None

    model_config = {"from_attributes": True}


class LeadSummaryMini(BaseModel):
    id: UUID
    lead_name: str

    model_config = {"from_attributes": True}


class RFQWorkspaceOut(BaseModel):
    rfq: RFQDetailOut
    company: CompanySummaryMini | None
    contact: ContactSummaryMini | None
    lead: LeadSummaryMini | None
    owner_display: str | None = None
    rfq_items: list[RFQItemOut]
    candidate_manufacturing_partners: list[PartnerBrief]
    partner_candidates_with_partner_detail: list[RFQPartnerCandidateWithPartnerOut]
    quotations: list[QuotationDetailOut]
    quotation_items: list[QuotationItemOut]
    quotation_comparison: QuotationComparisonOut
    related_samples: list[SampleWorkspaceBrief]
    related_orders: list[OrderWorkspaceBrief]
    recent_interactions: list[InteractionWorkspaceBrief]
    open_tasks: list[TaskWorkspaceBrief]
    recent_ai_outputs: list[AIOutputWorkspaceBrief]
    files: list[RfqFileBrief]
    activity_summary: ActivitySummaryOut


class RFQConvertToSampleBody(BaseModel):
    rfq_item_id: UUID
    manufacturing_partner_id: UUID
    notes: str | None = None


class RFQConvertToOrderBody(BaseModel):
    quotation_id: UUID | None = None
    manufacturing_partner_id: UUID
    rfq_item_id: UUID | None = None
    generate_milestones: bool = False
    notes: str | None = None


# Legacy alias for backwards compatibility
class RFQItemBody(RFQItemCreate):
    pass


class RFQPartnerBody(RFQPartnerCandidateCreate):
    pass
