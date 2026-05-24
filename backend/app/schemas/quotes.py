"""Pydantic schemas for D6.3 Customer Quotes."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AddressIn(BaseModel):
    name: str | None = None
    company: str | None = None
    address: str | None = None


class QuoteLineItemIn(BaseModel):
    product_id: UUID | None = None
    product_catalog_id: UUID | None = None
    partner_id: UUID | None = None
    manual_product_name: str | None = None
    quantity: int = Field(..., gt=0)
    incoterm: str = "FOB"
    pricing_strategy: str = "volume"
    discount: dict[str, Any] | None = None
    manual_unit_price: Decimal | None = None
    unit_price: Decimal | None = None
    color_finish: str | None = None
    size_dimension: str | None = None


class QuoteCreateIn(BaseModel):
    lead_id: UUID | None = None
    company_id: UUID | None = None
    contact_id: UUID | None = None
    bill_to: AddressIn | None = None
    ship_to: AddressIn | None = None
    payment_terms: str | None = None
    shipping_terms: str | None = None
    internal_notes: str | None = None
    customer_notes: str | None = None
    default_incoterm: str | None = "FOB"
    line_items: list[QuoteLineItemIn] = Field(..., min_length=1)


class QuoteFromContractIn(BaseModel):
    lead_id: UUID
    selected_product_ids: list[UUID] | None = None
    line_items: list[QuoteLineItemIn] = Field(..., min_length=1)
    bill_to: AddressIn | None = None
    ship_to: AddressIn | None = None
    payment_terms: str | None = None
    shipping_terms: str | None = None
    internal_notes: str | None = None


class QuoteUpdateIn(BaseModel):
    bill_to_name: str | None = None
    bill_to_company: str | None = None
    bill_to_address: str | None = None
    ship_to_name: str | None = None
    ship_to_company: str | None = None
    ship_to_address: str | None = None
    payment_terms: str | None = None
    shipping_terms: str | None = None
    customer_notes: str | None = None
    internal_notes: str | None = None
    valid_until: date | None = None


class QuoteAdjustmentIn(BaseModel):
    type: str
    label: str
    amount: Decimal = Decimal("0")
    percentage: Decimal | None = None
    taxable: bool = False
    customer_visible: bool = True
    notes: str | None = None

    @field_validator("type")
    @classmethod
    def valid_type(cls, v: str) -> str:
        allowed = {"discount", "shipping", "sample_fee", "tax", "other_fee"}
        if v not in allowed:
            raise ValueError(f"type must be one of {allowed}")
        return v


class QuoteAdjustmentUpdateIn(BaseModel):
    label: str | None = None
    amount: Decimal | None = None
    percentage: Decimal | None = None
    taxable: bool | None = None
    customer_visible: bool | None = None
    notes: str | None = None


class QuoteVersionCreateIn(BaseModel):
    version_type: str = "revised"
    version_label: str | None = None
    notes: str | None = None


class MarkSentIn(BaseModel):
    quote_version_id: UUID | None = None
    pdf_export_id: UUID | None = None
    sent_channel: str | None = None
    send_channel: str | None = None
    sent_to_name: str | None = None
    sent_to_email: str | None = None
    sent_to_company: str | None = None
    sent_at: datetime | None = None
    follow_up_date: date | None = None
    note: str | None = None


class ExportPdfIn(BaseModel):
    quote_version_id: UUID | None = None
    export_type: str = "customer_pdf"
