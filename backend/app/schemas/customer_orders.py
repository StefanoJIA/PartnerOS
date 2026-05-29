"""Pydantic schemas for D7.2 Customer Orders."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.models.customer_orders import CUSTOMER_CONFIRMATION_TYPES, SHIPMENT_PLAN_STATUSES, SUPPLIER_CONFIRMATION_STATUSES


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


class SupplierConfirmationIn(BaseModel):
    confirmation_status: str
    confirmed_at: datetime | str | None = None
    confirmed_by_name: str | None = None
    confirmed_by_email: str | None = None
    confirmation_channel: str | None = None
    inventory_confirmed: bool = False
    certification_confirmed: bool = False
    lead_time_confirmed: bool = False
    production_capacity_confirmed: bool = False
    expected_production_start: date | str | None = None
    expected_ready_date: date | str | None = None
    supplier_reference: str | None = None
    note: str | None = None

    @field_validator("confirmation_status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in SUPPLIER_CONFIRMATION_STATUSES:
            raise ValueError(f"confirmation_status must be one of {SUPPLIER_CONFIRMATION_STATUSES}")
        return v


class VoidSupplierConfirmationIn(BaseModel):
    reason: str | None = None


class ProductionMilestoneUpdateIn(BaseModel):
    status: str | None = None
    planned_date: date | str | None = None
    actual_date: date | str | None = None
    responsible_party: str | None = None
    notes: str | None = None


class ShipmentPlanCreateIn(BaseModel):
    partner_split_id: UUID | None = None
    shipment_method: str | None = None
    incoterm: str | None = None
    origin: str | None = None
    destination: str | None = None
    estimated_ship_date: date | str | None = None
    estimated_arrival_date: date | str | None = None
    tracking_number: str | None = None
    status: str = "draft"
    notes: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in SHIPMENT_PLAN_STATUSES:
            raise ValueError(f"status must be one of {SHIPMENT_PLAN_STATUSES}")
        return v


class ShipmentPlanUpdateIn(BaseModel):
    partner_split_id: UUID | None = None
    shipment_method: str | None = None
    incoterm: str | None = None
    origin: str | None = None
    destination: str | None = None
    estimated_ship_date: date | str | None = None
    estimated_arrival_date: date | str | None = None
    tracking_number: str | None = None
    status: str | None = None
    notes: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in SHIPMENT_PLAN_STATUSES:
            raise ValueError(f"status must be one of {SHIPMENT_PLAN_STATUSES}")
        return v


class OrderResourceCreateIn(BaseModel):
    file_id: UUID
    title: str | None = None
    category: str = "general"
    description: str | None = None
    customer_visible: bool = False


class OrderResourceUpdateIn(BaseModel):
    title: str | None = None
    category: str | None = None
    description: str | None = None
    status: str | None = None
    customer_visible: bool | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        allowed = ("draft", "published", "archived")
        if v is not None and v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class ShipmentSafety(BaseModel):
    shipment_created: bool = False
    supplier_notified: bool = False
    customer_notified: bool = False


class PortalShipmentSummary(BaseModel):
    """D7.7-ready customer-visible shipment summary DTO; no portal route in D7.6."""

    status: str
    shipment_method: str | None = None
    estimated_ship_date: date | None = None
    estimated_arrival_date: date | None = None
    tracking_number: str | None = None
