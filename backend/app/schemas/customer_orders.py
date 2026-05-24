"""Pydantic schemas for D7.2 Customer Orders."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.customer_orders import CUSTOMER_CONFIRMATION_TYPES


class AddressIn(BaseModel):
    name: str | None = None
    company: str | None = None
    address: str | None = None


class CustomerConfirmationIn(BaseModel):
    type: str
    confirmed_at: datetime | str | None = None
    note: str | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in CUSTOMER_CONFIRMATION_TYPES:
            raise ValueError(f"type must be one of {CUSTOMER_CONFIRMATION_TYPES}")
        return v


class OrderFromQuoteIn(BaseModel):
    quote_id: UUID
    quote_version_id: UUID | None = None
    pdf_export_id: UUID | None = None
    delivery_log_id: UUID | None = None
    customer_confirmation: CustomerConfirmationIn | None = None
    selected_line_item_ids: list[UUID] | None = None
    bill_to: AddressIn | None = None
    ship_to: AddressIn | None = None
    internal_notes: str | None = None
    customer_notes: str | None = None


class OrderUpdateIn(BaseModel):
    bill_to_name: str | None = None
    bill_to_company: str | None = None
    bill_to_address: str | None = None
    ship_to_name: str | None = None
    ship_to_company: str | None = None
    ship_to_address: str | None = None
    internal_notes: str | None = None
    customer_notes: str | None = None
    payment_terms: str | None = None
    shipping_terms: str | None = None


class ConfirmCustomerIn(BaseModel):
    confirmation_type: str = Field(..., alias="confirmation_type")
    confirmed_at: datetime | str | None = None
    note: str | None = None

    @field_validator("confirmation_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in CUSTOMER_CONFIRMATION_TYPES:
            raise ValueError(f"confirmation_type must be one of {CUSTOMER_CONFIRMATION_TYPES}")
        return v

    model_config = {"populate_by_name": True}


class CancelOrderIn(BaseModel):
    reason: str | None = None
