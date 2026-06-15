from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


CAMPAIGN_STATUS_LABELS = {
    "planned": "已规划",
    "active": "推进中",
    "paused": "已暂停",
    "completed": "已完成",
    "archived": "已归档",
}

CAMPAIGN_TASK_STATUS_LABELS = {
    "planned": "待人工执行",
    "manual_sent": "已人工发送",
    "replied": "客户已回复",
    "interested": "有兴趣",
    "quote_requested": "已请求报价",
    "closed": "已关闭",
}

ALLOWED_CAMPAIGN_STATUSES = set(CAMPAIGN_STATUS_LABELS)
ALLOWED_TASK_STATUSES = set(CAMPAIGN_TASK_STATUS_LABELS)
OPPORTUNITY_STAGE_LABELS = {
    "discovery": "需求发现",
    "qualified": "已确认机会",
    "solution_fit": "方案匹配",
    "quotation": "报价推进",
    "negotiation": "商务谈判",
    "won": "已成交",
    "lost": "已丢单",
    "on_hold": "暂停",
}
OPPORTUNITY_STATUS_LABELS = {
    "open": "推进中",
    "won": "已成交",
    "lost": "已丢单",
    "on_hold": "暂停",
    "archived": "归档",
}
ALLOWED_OPPORTUNITY_STAGES = set(OPPORTUNITY_STAGE_LABELS)
ALLOWED_OPPORTUNITY_STATUSES = set(OPPORTUNITY_STATUS_LABELS)


def _clean_product_focus(value: list[str] | None) -> list[str]:
    return [item.strip() for item in value or [] if item and item.strip()]


class GrowthCampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    partner_focus: str = Field(min_length=1, max_length=128)
    product_focus: list[str] = Field(default_factory=list)
    target_segment: str | None = Field(default=None, max_length=255)
    goal: str | None = None
    status: str = "planned"
    owner: str | None = Field(default=None, max_length=255)
    next_action: str | None = None
    notes: str | None = None

    @field_validator("product_focus")
    @classmethod
    def normalize_product_focus(cls, value: list[str]) -> list[str]:
        return _clean_product_focus(value)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in ALLOWED_CAMPAIGN_STATUSES:
            raise ValueError("unsupported campaign status")
        return value


class GrowthCampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    partner_focus: str | None = Field(default=None, min_length=1, max_length=128)
    product_focus: list[str] | None = None
    target_segment: str | None = Field(default=None, max_length=255)
    goal: str | None = None
    status: str | None = None
    owner: str | None = Field(default=None, max_length=255)
    next_action: str | None = None
    notes: str | None = None

    @field_validator("product_focus")
    @classmethod
    def normalize_product_focus(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return _clean_product_focus(value)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_CAMPAIGN_STATUSES:
            raise ValueError("unsupported campaign status")
        return value


class GrowthCampaignTaskCreate(BaseModel):
    company_id: UUID | None = None
    contact_id: UUID | None = None
    task_type: str = Field(default="manual_outreach", max_length=64)
    language: str = Field(default="zh", max_length=16)
    draft_subject: str | None = Field(default=None, max_length=512)
    draft_body: str | None = None
    status: str = "planned"
    due_date: date | None = None
    notes: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in ALLOWED_TASK_STATUSES:
            raise ValueError("unsupported campaign task status")
        return value


class GrowthCampaignTaskUpdate(BaseModel):
    company_id: UUID | None = None
    contact_id: UUID | None = None
    task_type: str | None = Field(default=None, max_length=64)
    language: str | None = Field(default=None, max_length=16)
    draft_subject: str | None = Field(default=None, max_length=512)
    draft_body: str | None = None
    status: str | None = None
    due_date: date | None = None
    notes: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_TASK_STATUSES:
            raise ValueError("unsupported campaign task status")
        return value


class GrowthCampaignRead(BaseModel):
    id: UUID
    name: str
    partner_focus: str
    product_focus: list[str]
    target_segment: str | None
    goal: str | None
    status: str
    status_label: str
    owner: str | None
    next_action: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class GrowthCampaignTaskRead(BaseModel):
    id: UUID
    campaign_id: UUID
    company_id: UUID | None
    contact_id: UUID | None
    company_name: str | None
    contact_name: str | None
    task_type: str
    task_type_label: str
    language: str
    draft_subject: str | None
    draft_body: str | None
    status: str
    status_label: str
    due_date: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class SalesOpportunityCreate(BaseModel):
    opportunity_name: str = Field(min_length=1, max_length=255)
    company_id: UUID | None = None
    lead_id: UUID | None = None
    campaign_id: UUID | None = None
    quote_id: UUID | None = None
    order_id: UUID | None = None
    partner_focus: str | None = Field(default=None, max_length=128)
    product_focus: list[str] = Field(default_factory=list)
    customer_segment: str | None = Field(default=None, max_length=255)
    project_size: str | None = Field(default=None, max_length=64)
    estimated_value: Decimal | None = None
    decision_stage: str = "discovery"
    competition: str | None = None
    risk: str | None = None
    probability: int = Field(default=20, ge=0, le=100)
    priority: str = Field(default="P2", max_length=16)
    owner: str | None = Field(default=None, max_length=255)
    next_action: str | None = None
    blocker: str | None = None
    status: str = "open"
    expected_close_date: date | None = None
    won_reason: str | None = None
    lost_reason: str | None = None
    notes: str | None = None

    @field_validator("product_focus")
    @classmethod
    def normalize_product_focus(cls, value: list[str]) -> list[str]:
        return _clean_product_focus(value)

    @field_validator("decision_stage")
    @classmethod
    def validate_stage(cls, value: str) -> str:
        if value not in ALLOWED_OPPORTUNITY_STAGES:
            raise ValueError("unsupported opportunity decision stage")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in ALLOWED_OPPORTUNITY_STATUSES:
            raise ValueError("unsupported opportunity status")
        return value


class SalesOpportunityUpdate(BaseModel):
    opportunity_name: str | None = Field(default=None, min_length=1, max_length=255)
    company_id: UUID | None = None
    lead_id: UUID | None = None
    campaign_id: UUID | None = None
    quote_id: UUID | None = None
    order_id: UUID | None = None
    partner_focus: str | None = Field(default=None, max_length=128)
    product_focus: list[str] | None = None
    customer_segment: str | None = Field(default=None, max_length=255)
    project_size: str | None = Field(default=None, max_length=64)
    estimated_value: Decimal | None = None
    decision_stage: str | None = None
    competition: str | None = None
    risk: str | None = None
    probability: int | None = Field(default=None, ge=0, le=100)
    priority: str | None = Field(default=None, max_length=16)
    owner: str | None = Field(default=None, max_length=255)
    next_action: str | None = None
    blocker: str | None = None
    status: str | None = None
    expected_close_date: date | None = None
    won_reason: str | None = None
    lost_reason: str | None = None
    notes: str | None = None

    @field_validator("product_focus")
    @classmethod
    def normalize_product_focus(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return _clean_product_focus(value)

    @field_validator("decision_stage")
    @classmethod
    def validate_stage(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_OPPORTUNITY_STAGES:
            raise ValueError("unsupported opportunity decision stage")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_OPPORTUNITY_STATUSES:
            raise ValueError("unsupported opportunity status")
        return value


class OpportunityRecommendationRead(BaseModel):
    id: str
    source_type: str
    source_id: str
    priority: str
    suggested_probability: int
    suggested_decision_stage: str
    risk_signal: str
    recommended_next_action: str
    reason: str
    path: str
    manual_apply_required: bool
    partner_fit: dict[str, Any] = Field(default_factory=dict)
    safety: dict[str, bool]


class SalesOpportunityRead(BaseModel):
    id: UUID
    opportunity_name: str
    company_id: UUID | None
    company_name: str | None = None
    lead_id: UUID | None
    campaign_id: UUID | None
    quote_id: UUID | None
    order_id: UUID | None
    partner_focus: str | None
    product_focus: list[str]
    customer_segment: str | None
    project_size: str | None
    estimated_value: Decimal | None
    decision_stage: str
    decision_stage_label: str
    competition: str | None
    risk: str | None
    probability: int
    priority: str
    owner: str | None
    next_action: str | None
    blocker: str | None
    status: str
    status_label: str
    expected_close_date: date | None
    won_reason: str | None
    lost_reason: str | None
    notes: str | None
    path: str
    recommendations: list[OpportunityRecommendationRead] = Field(default_factory=list)
    partner_fit: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
