"""Pydantic schemas for D7.2 Customer Orders."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, field_validator

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
    confirmation_type: str
    confirmed_at: datetime | str | None = None
    confirmed_by_name: str | None = None
    confirmed_by_email: str | None = None
    confirmed_by_company: str | None = None
    source_channel: str | None = None
    evidence_reference: str | None = None
    evidence_filename: str | None = None
    note: str | None = None

    @field_validator("confirmation_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in CUSTOMER_CONFIRMATION_TYPES:
            raise ValueError(f"confirmation_type must be one of {CUSTOMER_CONFIRMATION_TYPES}")
        return v


class VoidConfirmationIn(BaseModel):
    reason: str | None = None


class CancelOrderIn(BaseModel):
    reason: str | None = None
