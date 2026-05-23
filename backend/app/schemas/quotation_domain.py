from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class QuotationCreate(BaseModel):
    rfq_id: UUID | None = None
    manufacturing_partner_id: UUID | None = None
    product_id: UUID | None = None
    quantity: int | None = None
    unit_price: Decimal | None = None
    currency: str | None = "USD"
    incoterm: str | None = None
    moq: int | None = None
    lead_time: str | None = None
    sample_cost: Decimal | None = None
    tooling_cost: Decimal | None = None
    packaging_cost: Decimal | None = None
    estimated_shipping_cost: Decimal | None = None
    landed_cost: Decimal | None = None
    target_margin: Decimal | None = None
    notes: str | None = None
    valid_until: date | None = None


class QuotationUpdate(BaseModel):
    manufacturing_partner_id: UUID | None = None
    product_id: UUID | None = None
    quantity: int | None = None
    unit_price: Decimal | None = None
    currency: str | None = None
    incoterm: str | None = None
    moq: int | None = None
    lead_time: str | None = None
    sample_cost: Decimal | None = None
    tooling_cost: Decimal | None = None
    packaging_cost: Decimal | None = None
    estimated_shipping_cost: Decimal | None = None
    landed_cost: Decimal | None = None
    target_margin: Decimal | None = None
    notes: str | None = None
    valid_until: date | None = None


class QuotationOut(BaseModel):
    id: UUID
    rfq_id: UUID | None
    manufacturing_partner_id: UUID | None

    model_config = {"from_attributes": True}
