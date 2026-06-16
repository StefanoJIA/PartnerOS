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


QUOTE_LEARNING_OUTCOMES = {
    "open",
    "customer_reviewing",
    "revision_requested",
    "won",
    "lost",
    "no_response",
    "deferred",
    "still_active",
    "no_decision",
    "on_hold",
}

WIN_LOSS_REASON_CATEGORIES = {
    "price",
    "delivery",
    "certification",
    "product_fit",
    "partner_capacity",
    "customer_budget",
    "competitor",
    "timing",
    "relationship",
    "unknown",
}


def _normalize_labels(value: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in value or []:
        label = item.strip()
        key = label.lower()
        if label and key not in seen:
            seen.add(key)
            result.append(label)
    return result[:20]


class QuoteLearningRecordIn(BaseModel):
    quote_version_id: UUID | None = None
    outcome_status: str = "open"
    customer_feedback: str | None = None
    customer_objection: str | None = None
    competitor_signal: str | None = None
    reason_category: str | None = None
    customer_decision_factors: list[str] = Field(default_factory=list)
    won_reason: str | None = None
    lost_reason: str | None = None
    price_feedback: str | None = None
    delivery_feedback: str | None = None
    product_feedback: dict[str, Any] | None = None
    product_dimensions: list[str] = Field(default_factory=list)
    product_factors: list[str] = Field(default_factory=list)
    partner_factors: list[str] = Field(default_factory=list)
    outcome_source_type: str = "quote"
    outcome_source_id: UUID | None = None
    next_action: str | None = None
    owner: str | None = None
    follow_up_date: date | None = None
    affects_product_intelligence: bool = False
    affects_market_response: bool = False
    affects_opportunity: bool = True
    internal_only: bool = True

    @field_validator("outcome_status")
    @classmethod
    def valid_outcome_status(cls, value: str) -> str:
        if value not in QUOTE_LEARNING_OUTCOMES:
            raise ValueError(f"outcome_status must be one of {sorted(QUOTE_LEARNING_OUTCOMES)}")
        return value

    @field_validator("reason_category")
    @classmethod
    def valid_reason_category(cls, value: str | None) -> str | None:
        if value is not None and value not in WIN_LOSS_REASON_CATEGORIES:
            raise ValueError(f"reason_category must be one of {sorted(WIN_LOSS_REASON_CATEGORIES)}")
        return value

    @field_validator("product_dimensions", "customer_decision_factors", "product_factors", "partner_factors")
    @classmethod
    def normalize_dimensions(cls, value: list[str]) -> list[str]:
        return _normalize_labels(value)


class QuoteLearningRecordUpdate(BaseModel):
    quote_version_id: UUID | None = None
    outcome_status: str | None = None
    customer_feedback: str | None = None
    customer_objection: str | None = None
    competitor_signal: str | None = None
    reason_category: str | None = None
    customer_decision_factors: list[str] | None = None
    won_reason: str | None = None
    lost_reason: str | None = None
    price_feedback: str | None = None
    delivery_feedback: str | None = None
    product_feedback: dict[str, Any] | None = None
    product_dimensions: list[str] | None = None
    product_factors: list[str] | None = None
    partner_factors: list[str] | None = None
    outcome_source_type: str | None = None
    outcome_source_id: UUID | None = None
    next_action: str | None = None
    owner: str | None = None
    follow_up_date: date | None = None
    affects_product_intelligence: bool | None = None
    affects_market_response: bool | None = None
    affects_opportunity: bool | None = None
    internal_only: bool | None = None

    @field_validator("outcome_status")
    @classmethod
    def valid_update_outcome_status(cls, value: str | None) -> str | None:
        if value is not None and value not in QUOTE_LEARNING_OUTCOMES:
            raise ValueError(f"outcome_status must be one of {sorted(QUOTE_LEARNING_OUTCOMES)}")
        return value

    @field_validator("reason_category")
    @classmethod
    def valid_update_reason_category(cls, value: str | None) -> str | None:
        if value is not None and value not in WIN_LOSS_REASON_CATEGORIES:
            raise ValueError(f"reason_category must be one of {sorted(WIN_LOSS_REASON_CATEGORIES)}")
        return value

    @field_validator("product_dimensions", "customer_decision_factors", "product_factors", "partner_factors")
    @classmethod
    def normalize_update_dimensions(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return _normalize_labels(value)
