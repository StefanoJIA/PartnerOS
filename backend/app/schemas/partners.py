from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PartnerCreate(BaseModel):
    partner_name: str
    legal_name: str | None = None
    brand_name: str | None = None
    partner_type: str
    website: str | None = None
    contact_person: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    country: str | None = "China"
    province: str | None = None
    city: str | None = None
    address: str | None = None
    notes: str | None = None


class PartnerUpdate(BaseModel):
    partner_name: str | None = None
    legal_name: str | None = None
    brand_name: str | None = None
    partner_type: str | None = None
    website: str | None = None
    contact_person: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    country: str | None = None
    province: str | None = None
    city: str | None = None
    address: str | None = None
    factory_locations: str | None = None
    main_product_categories: str | None = None
    manufacturing_capabilities: str | None = None
    oem_odm_capability: str | None = None
    customization_capability: str | None = None
    moq_policy: str | None = None
    sample_policy: str | None = None
    lead_time: str | None = None
    export_experience: str | None = None
    us_market_experience: str | None = None
    certifications: str | None = None
    testing_capability: str | None = None
    english_materials_available: bool | None = None
    price_level: str | None = None
    quality_rating: int | None = None
    communication_rating: int | None = None
    delivery_rating: int | None = None
    project_fit_rating: int | None = None
    risk_level: str | None = None
    preferred_product_categories: str | None = None
    ai_partner_summary: str | None = None
    ai_risk_summary: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class PartnerOut(BaseModel):
    id: UUID
    partner_name: str
    partner_type: str
    country: str | None
    risk_level: str | None

    model_config = {"from_attributes": True}


class PartnerDetailOut(BaseModel):
    id: UUID
    partner_name: str
    legal_name: str | None
    brand_name: str | None
    partner_type: str
    website: str | None
    contact_person: str | None
    contact_email: str | None
    phone: str | None
    country: str | None
    province: str | None
    city: str | None
    address: str | None
    factory_locations: str | None
    main_product_categories: str | None
    manufacturing_capabilities: str | None
    oem_odm_capability: str | None
    customization_capability: str | None
    moq_policy: str | None
    sample_policy: str | None
    lead_time: str | None
    export_experience: str | None
    us_market_experience: str | None
    certifications: str | None
    testing_capability: str | None
    english_materials_available: bool | None
    price_level: str | None
    quality_rating: int | None
    communication_rating: int | None
    delivery_rating: int | None
    project_fit_rating: int | None
    risk_level: str | None
    preferred_product_categories: str | None
    notes: str | None
    ai_partner_summary: str | None
    ai_risk_summary: str | None
    extra_scores: dict | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PartnerScoreBody(BaseModel):
    quality_rating: int | None = None
    communication_rating: int | None = None
    delivery_rating: int | None = None
    project_fit_rating: int | None = None
    risk_level: str | None = None
    product_fit_rating: int | None = None
    certification_readiness: int | None = None
