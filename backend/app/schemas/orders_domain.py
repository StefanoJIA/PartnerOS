from datetime import date, datetime
from decimal import Decimal
import uuid
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.constants.status_enums import (
    MILESTONE_ROW_STATUSES,
    ORDER_PRODUCTION_STATUSES,
    ORDER_SHIPPING_STATUSES,
    RISK_LEVELS,
)
from app.schemas.lead_workspace import (
    AIOutputWorkspaceBrief,
    InteractionWorkspaceBrief,
    RFQWorkspaceBrief,
    SampleWorkspaceBrief,
    TaskWorkspaceBrief,
)
from app.schemas.rfq_domain import (
    ActivitySummaryOut,
    CompanySummaryMini,
    ContactSummaryMini,
    LeadSummaryMini,
    PartnerBrief,
    RfqFileBrief,
)

class OrderCreate(BaseModel):
    company_id: UUID | None = None
    contact_id: UUID | None = None
    lead_id: UUID | None = None
    rfq_id: UUID | None = None
    quotation_id: UUID | None = None
    sample_id: UUID | None = None
    manufacturing_partner_id: UUID | None = None
    order_date: date | None = None
    target_delivery_date: date | None = None
    total_amount: Decimal | None = None
    currency: str | None = "USD"
    incoterm: str | None = None
    production_status: str | None = "Draft"

    @field_validator("production_status")
    @classmethod
    def _ps(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in ORDER_PRODUCTION_STATUSES:
            raise ValueError(f"Invalid production_status; must be one of: {sorted(ORDER_PRODUCTION_STATUSES)}")
        return v


class OrderUpdate(BaseModel):
    target_delivery_date: date | None = None
    total_amount: Decimal | None = None
    production_status: str | None = None
    shipping_status: str | None = None
    risk_level: str | None = None
    notes: str | None = None

    @field_validator("production_status")
    @classmethod
    def _ps_u(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in ORDER_PRODUCTION_STATUSES:
            raise ValueError(f"Invalid production_status; must be one of: {sorted(ORDER_PRODUCTION_STATUSES)}")
        return v

    @field_validator("shipping_status")
    @classmethod
    def _ss_u(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in ORDER_SHIPPING_STATUSES:
            raise ValueError(f"Invalid shipping_status; must be one of: {sorted(ORDER_SHIPPING_STATUSES)}")
        return v

    @field_validator("risk_level")
    @classmethod
    def _rl_u(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in RISK_LEVELS:
            raise ValueError(f"Invalid risk_level; must be one of: {sorted(RISK_LEVELS)}")
        return v


class OrderOut(BaseModel):
    id: UUID
    order_number: str
    production_status: str | None
    shipping_status: str | None
    rfq_id: UUID | None = None
    lead_id: UUID | None = None
    sample_id: UUID | None = None

    model_config = {"from_attributes": True}


class OrderDetailOut(BaseModel):
    id: UUID
    order_number: str
    company_id: UUID | None
    contact_id: UUID | None
    lead_id: UUID | None
    rfq_id: UUID | None
    quotation_id: UUID | None
    sample_id: UUID | None
    manufacturing_partner_id: UUID | None
    order_date: date | None
    target_delivery_date: date | None
    total_amount: Decimal | None
    currency: str | None
    incoterm: str | None
    production_status: str | None
    shipping_status: str | None
    risk_level: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderListItemOut(BaseModel):
    id: UUID
    order_number: str
    company_id: UUID | None
    company_name: str | None = None
    contact_id: UUID | None
    contact_label: str | None = None
    lead_id: UUID | None
    lead_name: str | None = None
    rfq_id: UUID | None
    rfq_number: str | None = None
    manufacturing_partner_id: UUID | None
    partner_name: str | None = None
    order_date: date | None
    target_delivery_date: date | None
    production_status: str | None
    shipping_status: str | None
    risk_level: str | None
    delayed_milestones_count: int = 0
    total_amount: Decimal | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderItemOut(BaseModel):
    id: UUID
    order_id: UUID
    product_id: UUID | None
    quantity: int | None
    unit_price: Decimal | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductionMilestoneOut(BaseModel):
    id: UUID
    order_id: UUID
    milestone_name: str
    planned_date: date | None
    actual_date: date | None
    delay_days: int | None
    status: str | None
    responsible_party: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShippingRecordOut(BaseModel):
    id: UUID
    order_id: UUID
    origin_factory: str | None
    origin_port: str | None
    destination_port: str | None
    destination_warehouse: str | None
    incoterm: str | None
    container_type: str | None
    carton_dimensions: str | None
    carton_weight: str | None
    cartons_count: int | None
    pallet_count: int | None
    estimated_cbm: Decimal | None
    freight_forwarder: str | None
    booking_date: date | None
    etd: date | None
    eta: date | None
    actual_arrival_date: date | None
    customs_status: str | None
    delivery_status: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShippingRecordCreate(BaseModel):
    origin_factory: str | None = None
    origin_port: str | None = None
    destination_port: str | None = None
    destination_warehouse: str | None = None
    incoterm: str | None = None
    container_type: str | None = None
    carton_dimensions: str | None = None
    carton_weight: str | None = None
    cartons_count: int | None = None
    pallet_count: int | None = None
    estimated_cbm: Decimal | None = None
    freight_forwarder: str | None = None
    booking_date: date | None = None
    etd: date | None = None
    eta: date | None = None
    actual_arrival_date: date | None = None
    customs_status: str | None = None
    delivery_status: str | None = None
    notes: str | None = None


class ShippingRecordUpdate(ShippingRecordCreate):
    pass


class QuotationBriefOut(BaseModel):
    id: UUID
    rfq_id: UUID | None
    manufacturing_partner_id: UUID | None
    product_id: UUID | None
    quantity: int | None
    unit_price: Decimal | None
    currency: str | None
    lead_time: str | None

    model_config = {"from_attributes": True}


class OrderRiskItemOut(BaseModel):
    risk_level: str
    risk_reason: str
    recommended_action: str


class OrderRiskPanelOut(BaseModel):
    items: list[OrderRiskItemOut]
    overall_severity: str


class OrderWorkspaceOut(BaseModel):
    order: OrderDetailOut
    company: CompanySummaryMini | None
    contact: ContactSummaryMini | None
    lead: LeadSummaryMini | None
    rfq: RFQWorkspaceBrief | None
    quotation: QuotationBriefOut | None
    sample: SampleWorkspaceBrief | None
    manufacturing_partner: PartnerBrief | None
    order_items: list[OrderItemOut]
    production_milestones: list[ProductionMilestoneOut]
    shipping_records: list[ShippingRecordOut]
    risk_panel: OrderRiskPanelOut
    recent_interactions: list[InteractionWorkspaceBrief]
    open_tasks: list[TaskWorkspaceBrief]
    recent_ai_outputs: list[AIOutputWorkspaceBrief]
    files: list[RfqFileBrief]
    activity_summary: ActivitySummaryOut


class OrderProductionStatusBody(BaseModel):
    production_status: str
    notes: str | None = None

    @field_validator("production_status")
    @classmethod
    def _ps(cls, v: str) -> str:
        if v not in ORDER_PRODUCTION_STATUSES:
            raise ValueError(f"Invalid production_status; must be one of: {sorted(ORDER_PRODUCTION_STATUSES)}")
        return v


class OrderShippingStatusBody(BaseModel):
    shipping_status: str
    notes: str | None = None

    @field_validator("shipping_status")
    @classmethod
    def _ss(cls, v: str) -> str:
        if v not in ORDER_SHIPPING_STATUSES:
            raise ValueError(f"Invalid shipping_status; must be one of: {sorted(ORDER_SHIPPING_STATUSES)}")
        return v


class MilestoneUpdate(BaseModel):
    planned_date: date | None = None
    actual_date: date | None = None
    status: str | None = None
    responsible_party: str | None = None
    notes: str | None = None

    @field_validator("status")
    @classmethod
    def _ms(cls, v: str | None) -> str | None:
        if v is None:
            return v
        low = v.strip().lower()
        if low not in MILESTONE_ROW_STATUSES:
            raise ValueError(f"Invalid milestone status; must be one of: {sorted(MILESTONE_ROW_STATUSES)}")
        return low


def next_order_number() -> str:
    return f"ORD-{uuid.uuid4().hex[:8].upper()}"


DEFAULT_MILESTONE_NAMES = [
    "Order Confirmed",
    "Material Preparation",
    "Cutting",
    "Sheet Metal Processing",
    "Welding",
    "Polishing",
    "Powder Coating",
    "Assembly",
    "Testing",
    "Packaging",
    "Palletizing",
    "Booking",
    "Trucking to Port",
    "Customs Declaration",
    "Vessel Departure",
    "Vessel Arrival",
    "U.S. Customs",
    "Warehouse Inbound",
    "Final Delivery",
    "Customer Received",
]
