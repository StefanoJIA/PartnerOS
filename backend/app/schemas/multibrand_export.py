from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BenchmarkBrandOut(BaseModel):
    id: UUID
    brand_code: str
    display_name: str
    industry_vertical: str
    country: str | None
    website_url: str | None
    relationship_disclaimer: str
    review_status: str
    verified_at: datetime | None
    is_active: bool

    model_config = {"from_attributes": True}


class BenchmarkCapabilityOut(BaseModel):
    id: UUID
    capability_key: str
    capability_label: str
    value_text: str | None
    verification_status: str
    source_type: str
    source_url: str | None
    retrieved_at: date | None

    model_config = {"from_attributes": True}


class BenchmarkBrandDetailOut(BenchmarkBrandOut):
    capabilities: list[BenchmarkCapabilityOut] = Field(default_factory=list)


class SupplierDiscoveryOut(BaseModel):
    id: UUID
    company_name: str
    brand_name: str | None
    country: str | None
    categories: list | None
    capabilities: list | None
    certifications: list | None
    status: str
    risk_level: str | None
    data_source: str | None
    doc_completeness_pct: int | None
    contact_status: str | None
    owner_user_id: UUID | None
    partner_id: UUID | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SupplierDiscoveryCreate(BaseModel):
    company_name: str
    brand_name: str | None = None
    country: str | None = None
    categories: list[str] | None = None
    capabilities: list[str] | None = None
    certifications: list[str] | None = None
    moq_notes: str | None = None
    sample_policy: str | None = None
    lead_time_notes: str | None = None
    export_markets: list[str] | None = None
    doc_completeness_pct: int | None = None
    contact_status: str | None = None
    risk_level: str | None = None
    data_source: str | None = "manual"
    notes: str | None = None


class SupplierDiscoveryUpdate(BaseModel):
    status: str | None = None
    contact_status: str | None = None
    risk_level: str | None = None
    doc_completeness_pct: int | None = None
    notes: str | None = None
    owner_user_id: UUID | None = None


class ProjectRequestCandidateOut(BaseModel):
    id: UUID
    candidate_source_type: str
    candidate_role: str
    display_name: str
    sku: str | None
    fit_dimensions_json: dict | None
    evidence_quality: str | None
    overall_fit_status: str | None
    eligible_for_formal_quote: bool
    operator_decision: str | None
    decision_reason: str | None
    is_auto_recommended: bool
    partner_id: UUID | None
    benchmark_brand_id: UUID | None

    model_config = {"from_attributes": True}


class CandidateDecisionBody(BaseModel):
    decision: str
    reason: str | None = None


class PlatformBenchmarkOut(BaseModel):
    id: UUID
    platform_name: str
    capability_area: str
    capability_description: str | None
    partneros_has: bool
    partneros_gap_notes: str | None
    build_recommended: bool
    build_priority: str
    evidence_source: str | None

    model_config = {"from_attributes": True}


class ChannelMetricOut(BaseModel):
    id: UUID
    channel_source: str
    period_label: str
    lead_count: int | None
    quote_count: int | None
    win_count: int | None
    lead_quality_score: float | None
    quote_rate: float | None
    win_rate: float | None
    data_source: str

    model_config = {"from_attributes": True}
