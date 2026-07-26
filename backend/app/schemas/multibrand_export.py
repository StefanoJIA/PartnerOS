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
    source_url: str | None = None
    factory_address: str | None = None
    contacts_json: list | None = None
    pricing_doc_status: str | None = None
    data_rights_status: str | None = None
    source_review_status: str | None = None
    retrieved_at: datetime | None = None
    usage_restrictions: str | None = None
    domain_key: str | None = None
    doc_completeness_pct: int | None
    contact_status: str | None
    owner_user_id: UUID | None
    partner_id: UUID | None
    notes: str | None
    qualification_json: dict | None = None
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
    source_url: str | None = None
    factory_address: str | None = None
    contacts_json: list[dict] | None = None
    pricing_doc_status: str | None = "unknown"
    data_rights_status: str | None = "pending_review"
    source_review_status: str | None = "pending"
    usage_restrictions: str | None = None
    notes: str | None = None


class SupplierDiscoveryUpdate(BaseModel):
    status: str | None = None
    contact_status: str | None = None
    risk_level: str | None = None
    doc_completeness_pct: int | None = None
    notes: str | None = None
    owner_user_id: UUID | None = None
    factory_address: str | None = None
    contacts_json: list[dict] | None = None
    pricing_doc_status: str | None = None
    data_rights_status: str | None = None
    source_review_status: str | None = None
    usage_restrictions: str | None = None


class SupplierDiscoveryImportResult(BaseModel):
    created_count: int
    skipped_count: int
    created: list[SupplierDiscoveryOut]
    skipped: list[dict[str, str]]


class QualificationDimensionUpdate(BaseModel):
    dimension_key: str
    status: str
    evidence: str | None = None
    notes: str | None = None


class SupplierSampleEvaluationOut(BaseModel):
    id: UUID
    template_key: str
    supplier_discovery_id: UUID | None
    partner_id: UUID | None
    project_request_id: UUID | None
    product_catalog_id: UUID | None
    request_date: date | None
    shipment_date: date | None
    receipt_date: date | None
    test_items_json: list | None
    results_json: dict | None
    file_refs_json: list | None
    issues: str | None
    corrective_action: str | None
    overall_result: str | None
    reviewer_user_id: UUID | None
    reviewer_notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SupplierSampleEvaluationCreate(BaseModel):
    template_key: str = "generic"
    supplier_discovery_id: UUID | None = None
    partner_id: UUID | None = None
    project_request_id: UUID | None = None
    product_catalog_id: UUID | None = None
    request_date: date | None = None


class SupplierSampleEvaluationUpdate(BaseModel):
    shipment_date: date | None = None
    receipt_date: date | None = None
    results_json: dict | None = None
    file_refs_json: list | None = None
    issues: str | None = None
    corrective_action: str | None = None
    overall_result: str | None = None
    reviewer_notes: str | None = None


class SupplierSelectionSnapshotOut(BaseModel):
    id: UUID
    project_request_id: UUID
    selected_candidate_id: UUID | None
    snapshot_json: dict
    selected_at: datetime

    model_config = {"from_attributes": True}


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
    competitor_capability: str | None = None
    partneros_existing: str | None = None
    gap_description: str | None = None
    target_user: str | None = None
    business_value: str | None = None
    implementation_cost: str | None = None
    build_action: str | None = None

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
    qualified_project_count: int | None = None
    cycle_days_avg: int | None = None
    supplier_coverage_pct: float | None = None
    lost_reasons_json: dict | None = None

    model_config = {"from_attributes": True}
