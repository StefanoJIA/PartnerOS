from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class ProductCreate(BaseModel):
    product_name: str
    product_category: str | None = None
    description: str | None = None


class ProductUpdate(BaseModel):
    product_name: str | None = None
    product_category: str | None = None
    product_subcategory: str | None = None
    description: str | None = None
    key_features: str | None = None
    application_scenarios: str | None = None
    target_customer_types: str | None = None
    load_capacity: str | None = None
    moq: int | None = None
    fob_price_range: str | None = None
    container_loading_40hq: str | None = None
    ai_product_summary: str | None = None
    ai_sales_description: str | None = None
    is_active: bool | None = None


class ProductOut(BaseModel):
    id: UUID
    product_name: str
    product_category: str | None
    ai_sales_description: str | None = None

    model_config = {"from_attributes": True}


class ProductDetailOut(BaseModel):
    id: UUID
    product_name: str
    product_category: str | None
    product_subcategory: str | None
    category_id: UUID | None
    description: str | None
    key_features: str | None
    application_scenarios: str | None
    target_customer_types: str | None
    dimensions: str | None
    weight: str | None
    load_capacity: str | None
    lifting_speed: str | None
    noise_level: str | None
    material: str | None
    finish: str | None
    color_options: str | None
    certification_requirements: str | None
    available_certifications: str | None
    moq: int | None
    sample_available: bool | None
    sample_cost: Decimal | None
    fob_price_range: str | None
    target_us_price_range: str | None
    packaging_dimensions: str | None
    carton_weight: str | None
    pallet_info: str | None
    container_loading_20gp: str | None
    container_loading_40gp: str | None
    container_loading_40hq: str | None
    ai_product_summary: str | None
    ai_sales_description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductPartnerLinkDetailOut(BaseModel):
    id: UUID
    product_id: UUID
    manufacturing_partner_id: UUID
    is_preferred: bool
    capability_level: str | None
    partner_moq: int | None
    lead_time_days: int | None
    partner_price_range: str | None
    sample_available: bool | None
    certification_status: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductPartnerLinkBody(BaseModel):
    manufacturing_partner_id: UUID
    is_preferred: bool = False
    capability_level: str | None = None
    partner_moq: int | None = None
    lead_time_days: int | None = None
    partner_price_range: str | None = None
    sample_available: bool | None = None
    certification_status: str | None = None
    notes: str | None = None


class ProductPartnerLinkUpdate(BaseModel):
    is_preferred: bool | None = None
    capability_level: str | None = None
    partner_moq: int | None = None
    lead_time_days: int | None = None
    partner_price_range: str | None = None
    sample_available: bool | None = None
    certification_status: str | None = None
    notes: str | None = None


class PartnerProductLinkBody(BaseModel):
    """Same link fields as ProductPartnerLinkBody but product_id (for POST .../partners/{id}/products)."""

    product_id: UUID
    is_preferred: bool = False
    capability_level: str | None = None
    partner_moq: int | None = None
    lead_time_days: int | None = None
    partner_price_range: str | None = None
    sample_available: bool | None = None
    certification_status: str | None = None
    notes: str | None = None
