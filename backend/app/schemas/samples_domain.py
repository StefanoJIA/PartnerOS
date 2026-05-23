import uuid
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.constants.status_enums import SAMPLE_STATUSES
from app.schemas.lead_workspace import (
    AIOutputWorkspaceBrief,
    InteractionWorkspaceBrief,
    OrderWorkspaceBrief,
    RFQWorkspaceBrief,
    TaskWorkspaceBrief,
)
from app.schemas.rfq_domain import (
    ActivitySummaryOut,
    CompanySummaryMini,
    ContactSummaryMini,
    LeadSummaryMini,
    PartnerBrief,
    ProductBrief,
    RfqFileBrief,
)


class SampleCreate(BaseModel):
    company_id: UUID | None = None
    contact_id: UUID | None = None
    lead_id: UUID | None = None
    rfq_id: UUID | None = None
    product_id: UUID | None = None
    manufacturing_partner_id: UUID | None = None
    sample_status: str = "Requested"
    sample_cost: Decimal | None = None
    notes: str | None = None

    @field_validator("sample_status")
    @classmethod
    def _ss(cls, v: str) -> str:
        if v not in SAMPLE_STATUSES:
            raise ValueError(f"Invalid sample_status; must be one of: {sorted(SAMPLE_STATUSES)}")
        return v


class SampleUpdate(BaseModel):
    sample_status: str | None = None
    sample_cost: Decimal | None = None
    shipping_cost: Decimal | None = None
    courier: str | None = None
    tracking_number: str | None = None
    shipped_date: date | None = None
    delivered_date: date | None = None
    customer_feedback: str | None = None
    follow_up_due_date: date | None = None
    shipping_destination: str | None = None
    feedback_date: date | None = None
    interest_level: str | None = None
    next_action: str | None = None
    converted_to_rfq: bool | None = None
    converted_to_order: bool | None = None
    notes: str | None = None

    @field_validator("sample_status")
    @classmethod
    def _ss_u(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in SAMPLE_STATUSES:
            raise ValueError(f"Invalid sample_status; must be one of: {sorted(SAMPLE_STATUSES)}")
        return v


class SampleDetailOut(BaseModel):
    id: UUID
    sample_request_number: str
    company_id: UUID | None
    contact_id: UUID | None
    lead_id: UUID | None
    rfq_id: UUID | None
    product_id: UUID | None
    manufacturing_partner_id: UUID | None
    sample_status: str
    sample_cost: Decimal | None
    shipping_cost: Decimal | None
    courier: str | None
    tracking_number: str | None
    shipped_date: date | None
    delivered_date: date | None
    customer_feedback: str | None
    follow_up_due_date: date | None
    shipping_destination: str | None
    feedback_date: date | None
    interest_level: str | None
    next_action: str | None
    converted_to_rfq: bool
    converted_to_order: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SampleOut(BaseModel):
    id: UUID
    sample_request_number: str
    sample_status: str
    company_id: UUID | None
    rfq_id: UUID | None = None

    model_config = {"from_attributes": True}


class SampleListItemOut(BaseModel):
    id: UUID
    sample_request_number: str
    sample_status: str
    company_id: UUID | None
    company_name: str | None = None
    contact_id: UUID | None
    contact_label: str | None = None
    lead_id: UUID | None
    lead_name: str | None = None
    rfq_id: UUID | None
    rfq_number: str | None = None
    product_id: UUID | None
    product_name: str | None = None
    manufacturing_partner_id: UUID | None
    partner_name: str | None = None
    courier: str | None
    tracking_number: str | None
    shipped_date: date | None
    delivered_date: date | None
    follow_up_due_date: date | None
    converted_to_order: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SampleWorkspaceOut(BaseModel):
    sample: SampleDetailOut
    company: CompanySummaryMini | None
    contact: ContactSummaryMini | None
    lead: LeadSummaryMini | None
    rfq: RFQWorkspaceBrief | None
    product: ProductBrief | None
    manufacturing_partner: PartnerBrief | None
    related_order: OrderWorkspaceBrief | None
    recent_interactions: list[InteractionWorkspaceBrief]
    open_tasks: list[TaskWorkspaceBrief]
    recent_ai_outputs: list[AIOutputWorkspaceBrief]
    files: list[RfqFileBrief]
    activity_summary: ActivitySummaryOut


class SampleStatusBody(BaseModel):
    status: str
    notes: str | None = None

    @field_validator("status")
    @classmethod
    def _ss(cls, v: str) -> str:
        if v not in SAMPLE_STATUSES:
            raise ValueError(f"Invalid sample status; must be one of: {sorted(SAMPLE_STATUSES)}")
        return v


class SampleShippingBody(BaseModel):
    courier: str | None = None
    tracking_number: str | None = None
    shipping_cost: Decimal | None = None
    shipped_date: date | None = None
    delivered_date: date | None = None
    shipping_destination: str | None = None
    notes: str | None = None


class SampleFeedbackBody(BaseModel):
    customer_feedback: str | None = None
    feedback_date: date | None = None
    interest_level: str | None = None
    next_action: str | None = None
    follow_up_due_date: date | None = None


class SampleConvertToOrderBody(BaseModel):
    manufacturing_partner_id: UUID | None = None
    generate_milestones: bool = False
    notes: str | None = None


def next_sample_number() -> str:
    return f"SMP-{uuid.uuid4().hex[:8].upper()}"
