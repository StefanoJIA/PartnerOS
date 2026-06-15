from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class BusinessExecutionSummary(BaseModel):
    lifecycle_accounts: int = 0
    active_opportunities: int = 0
    quote_learning_items: int = 0
    delivery_risks: int = 0
    product_validation_items: int = 0
    partner_investment_items: int = 0
    executive_decisions: int = 0
    status: str = "READY_FOR_STAGING_HANDOFF"
    external_staging_state: str = "WAITING_FOR_REAL_STAGING_EVIDENCE"


class CustomerLifecycleItem(BaseModel):
    id: str
    source_type: str = "unknown"
    source_id: str | None = None
    customer_name: str
    lifecycle_stage: str
    stage_order: int = 0
    priority: str = "P2"
    owner: str | None = None
    partner_focus: str | None = None
    product_focus: list[str] = Field(default_factory=list)
    current_signal: str
    next_action: str
    blocker: str | None = None
    readiness_impact: list[str] = Field(default_factory=list)
    path: str


class CustomerAccountExecutionItem(BaseModel):
    account_key: str
    customer_name: str
    current_stage: str
    stage_order: int = 0
    priority: str = "P2"
    owner: str | None = None
    partner_focus: str | None = None
    product_focus: list[str] = Field(default_factory=list)
    source_counts: dict[str, int] = Field(default_factory=dict)
    active_paths: list[str] = Field(default_factory=list)
    open_blockers: list[str] = Field(default_factory=list)
    next_action: str
    decision_reason: str
    readiness_impact: list[str] = Field(default_factory=list)
    commercial_health: dict[str, Any] = Field(default_factory=dict)


class CompanyExecutionContext(BaseModel):
    account: CustomerAccountExecutionItem | None = None
    lifecycle: list[CustomerLifecycleItem] = Field(default_factory=list)
    safety: dict[str, bool] = Field(default_factory=dict)


class OpportunityPipelineItem(BaseModel):
    id: str
    opportunity_name: str
    customer_or_segment: str | None = None
    partner_focus: str | None = None
    product_focus: list[str] = Field(default_factory=list)
    project_size: str
    decision_stage: str
    competitive_signal: str
    probability: int = Field(ge=0, le=100)
    risk: str
    next_action: str
    path: str
    stage_gate: dict[str, Any] = Field(default_factory=dict)


class QuotationIntelligenceItem(BaseModel):
    quote_id: str
    quote_number: str
    customer_name: str | None = None
    status: str
    version_count: int = 0
    manual_sent: bool = False
    follow_up_date: date | None = None
    product_focus: list[str] = Field(default_factory=list)
    outcome_signal: str
    learning_signal: str
    next_action: str
    path: str
    commercial_intelligence: dict[str, Any] = Field(default_factory=dict)


class ProductIntelligenceItem(BaseModel):
    partner_focus: str
    product_focus: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    validation_signal: str
    risk: str
    next_action: str
    source_path: str


class PartnerIntelligenceItem(BaseModel):
    partner_id: str
    partner_name: str
    product_coverage: list[str] = Field(default_factory=list)
    readiness_level: str
    delivery_ability: str
    risk_assessment: str
    next_action: str
    path: str
    capability_intelligence: dict[str, Any] = Field(default_factory=dict)


class DeliveryVisibilityItem(BaseModel):
    order_id: str
    order_number: str
    customer_name: str | None = None
    lifecycle_stage: str
    risk_level: str
    production_signal: str
    shipment_signal: str
    feedback_signal: str
    repeat_business_risk: str
    next_action: str
    path: str
    fulfillment_intelligence: dict[str, Any] = Field(default_factory=dict)


class ExecutiveDecisionItem(BaseModel):
    decision_id: str
    question: str
    answer: str
    priority: str
    owner: str
    next_action: str
    path: str


class BusinessExecutionOut(BaseModel):
    summary: BusinessExecutionSummary
    account_lifecycle: list[CustomerAccountExecutionItem]
    lifecycle: list[CustomerLifecycleItem]
    opportunities: list[OpportunityPipelineItem]
    quotations: list[QuotationIntelligenceItem]
    products: list[ProductIntelligenceItem]
    partners: list[PartnerIntelligenceItem]
    delivery: list[DeliveryVisibilityItem]
    executive_decisions: list[ExecutiveDecisionItem]
    safety: dict[str, bool]
