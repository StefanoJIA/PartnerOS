from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import CustomerProjectRequestPriority, CustomerProjectRequestStatus


class ProjectRequirementFields(BaseModel):
    load_capacity_kg: float | None = None
    load_capacity_lb: float | None = None
    noise_db_target: float | None = None
    stability_requirement: str | None = None
    width_mm: float | None = None
    stroke_range_mm: str | None = None
    leg_count: int | None = None
    desk_configuration: str | None = None
    medical_industrial: bool | None = None
    mounting_holes: str | None = None
    controller_type: str | None = None
    anti_collision: bool | None = None
    color_finish: str | None = None
    powder_coat: str | None = None
    certifications: list[str] | None = None
    sample_required: bool | None = None
    warranty_requirement: str | None = None
    lead_time_days_max: int | None = None
    duty_cycle: str | None = None
    speed_mm_s: float | None = None
    custom_notes: str | None = None


class SiteProjectRequestIn(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    delivery_method: str | None = None
    payment_method: str | None = None
    shipping_address: str | None = None
    shipping_name: str | None = None
    billing_address: str | None = None
    billing_name: str | None = None
    notes: str | None = None
    customer_email: EmailStr | None = None
    customer_name: str | None = None
    company_name: str | None = None
    project_scenario: str | None = None
    requirements: ProjectRequirementFields | None = None


class SiteProjectRequestOut(BaseModel):
    message: str
    order_created: bool = False
    status: str
    request_reference: str
    request_id: UUID
    intake_type: str = "project_request"


class CustomerProjectRequestCreate(BaseModel):
    customer_name: str | None = None
    customer_email: EmailStr | None = None
    company_name_text: str | None = None
    company_id: UUID | None = None
    contact_id: UUID | None = None
    partner_id: UUID | None = None
    product_catalog_id: UUID | None = None
    sku: str | None = None
    product_interest: str | None = None
    quantity_min: int | None = None
    quantity_max: int | None = None
    target_price: Decimal | None = None
    delivery_region: str | None = None
    expected_date: date | None = None
    project_scenario: str | None = None
    requirements: ProjectRequirementFields | None = None
    attachment_refs: list[str] | None = None
    source: str = "admin_manual"
    priority: CustomerProjectRequestPriority = CustomerProjectRequestPriority.normal


class CustomerProjectRequestUpdate(BaseModel):
    status: CustomerProjectRequestStatus | None = None
    priority: CustomerProjectRequestPriority | None = None
    owner_user_id: UUID | None = None
    partner_id: UUID | None = None
    product_catalog_id: UUID | None = None
    sku: str | None = None
    operator_notes: str | None = None
    lead_id: UUID | None = None
    rfq_id: UUID | None = None
    quote_id: UUID | None = None


class CapabilityMatchOut(BaseModel):
    dimension: str
    label: str
    match_status: str
    evidence_source: str
    gap_notes: str | None = None
    engineering_review_required: bool = False
    suggested_validation: str | None = None
    confidence: str = "medium"


class FitSummaryOut(BaseModel):
    overall_status: str
    partner_code: str | None = None
    partner_pending: bool = False
    product_sku: str | None = None
    coverage_pct: float = 0
    missing_fields: list[str] = Field(default_factory=list)
    matches: list[CapabilityMatchOut] = Field(default_factory=list)
    disclaimer: str = "Internal recommendation only — not a customer-facing claim."


class CustomerProjectRequestOut(BaseModel):
    id: UUID
    request_reference: str
    status: str
    priority: str
    source: str
    customer_name: str | None = None
    customer_email: str | None = None
    company_name_text: str | None = None
    company_id: UUID | None = None
    contact_id: UUID | None = None
    partner_id: UUID | None = None
    product_catalog_id: UUID | None = None
    sku: str | None = None
    product_interest: str | None = None
    quantity_min: int | None = None
    quantity_max: int | None = None
    target_price: Decimal | None = None
    delivery_region: str | None = None
    expected_date: date | None = None
    project_scenario: str | None = None
    requirements_json: dict[str, Any] | None = None
    attachment_refs: list[Any] | None = None
    fit_summary_json: dict[str, Any] | None = None
    completeness_json: dict[str, Any] | None = None
    owner_user_id: UUID | None = None
    lead_id: UUID | None = None
    rfq_id: UUID | None = None
    quote_id: UUID | None = None
    submitted_at: datetime | None = None
    triaged_at: datetime | None = None
    quote_ready_at: datetime | None = None
    resolved_at: datetime | None = None
    operator_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerProjectRequestListItemOut(CustomerProjectRequestOut):
    company_name: str | None = None
    partner_code: str | None = None
    owner_email: str | None = None
    completeness_pct: float | None = None


class CustomerProjectRequestDetailOut(CustomerProjectRequestOut):
    fit_summary: FitSummaryOut | None = None
    quote_input_contract: dict[str, Any] | None = None
    market_signal_draft: dict[str, Any] | None = None


class QuoteInputContractGenerateOut(BaseModel):
    request_id: UUID
    quote_input_contract: dict[str, Any]
    summary_text: str


class MarketSignalDraftOut(BaseModel):
    request_id: UUID
    draft: dict[str, Any]
    requires_operator_approval: bool = True
