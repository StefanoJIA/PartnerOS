"""Pydantic schemas for D6.2 product catalog & pricing."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductCatalogCreate(BaseModel):
    partner_id: UUID
    internal_sku: str
    partner_product_code: str | None = None
    product_name: str
    product_category: str
    product_family: str | None = None
    description_customer: str | None = None
    description_internal: str | None = None
    status: str = "active"
    default_uom: str = "EA"
    base_currency: str = "USD"
    default_incoterm: str | None = "FOB"
    image_url: str | None = None
    attributes_json: dict | None = None
    notes: str | None = None


class ProductCatalogUpdate(BaseModel):
    partner_product_code: str | None = None
    product_name: str | None = None
    product_category: str | None = None
    product_family: str | None = None
    description_customer: str | None = None
    description_internal: str | None = None
    status: str | None = None
    default_uom: str | None = None
    base_currency: str | None = None
    default_incoterm: str | None = None
    image_url: str | None = None
    attributes_json: dict | None = None
    notes: str | None = None


class ProductCatalogOut(BaseModel):
    id: UUID
    partner_id: UUID
    internal_sku: str
    partner_product_code: str | None
    product_name: str
    product_category: str
    product_family: str | None
    description_customer: str | None
    description_internal: str | None
    status: str
    default_uom: str
    base_currency: str
    default_incoterm: str | None
    image_url: str | None
    attributes_json: dict | None
    notes: str | None
    partner_code: str | None = None
    partner_name: str | None = None
    quote_interval_count: int = 0
    has_interval_pricing: bool = False
    configuration_summary: dict | None = None
    pricing_model_summary: dict | None = None

    model_config = {"from_attributes": True}


class FxRateCreate(BaseModel):
    base_currency: str = "USD"
    quote_currency: str = "CNY"
    rate: Decimal
    rate_date: date
    source: str = "manual"
    is_manual_override: bool = True


class FxRateOut(BaseModel):
    id: UUID
    base_currency: str
    quote_currency: str
    rate: Decimal
    rate_date: date
    source: str | None
    is_manual_override: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PricingAssumptionOut(BaseModel):
    assumption_key: str
    numeric_value: Decimal
    unit: str | None
    source: str | None
    effective_from: date | None
    fallback_used: bool = False
    internal_only: bool = True


class PricingAssumptionUpdate(BaseModel):
    ocean_freight_unit_price: Decimal = Field(gt=0)
    effective_from: date | None = None
    source: str = "manual_provider_quote"
    notes: str | None = None


class PricingAssumptionSnapshotOut(BaseModel):
    ocean_freight: PricingAssumptionOut
    safety: dict


class PricingDiscountIn(BaseModel):
    type: str = Field(description="percentage or amount")
    value: Decimal


class PricingPreviewRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0)
    incoterm: str = "FOB"
    pricing_strategy: str = "volume"
    discount: PricingDiscountIn | None = None
    fx_rate_date: date | None = None
    manual_unit_price: Decimal | None = None


class PricingSafetyOut(BaseModel):
    quote_created: bool = False
    automatic_sending_enabled: bool = False
    inventory_promised: bool = False
    certification_promised: bool = False
    lead_time_promised: bool = False
