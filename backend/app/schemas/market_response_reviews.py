from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


REVIEW_STATUS_LABELS = {
    "watching": "观察中",
    "needs review": "待人工审查",
    "reviewed": "已人工审查",
    "blocked": "阻塞",
    "deferred": "暂缓",
}
ALLOWED_REVIEW_STATUSES = set(REVIEW_STATUS_LABELS)

VISIBILITY_CLASS_LABELS = {
    "customer-safe candidate": "客户可见候选",
    "needs validation": "需要验证",
    "internal-only": "内部专用",
    "pilot blocker": "Pilot 阻塞项",
}
ALLOWED_VISIBILITY_CLASSES = set(VISIBILITY_CLASS_LABELS)

PRIORITY_LABELS = {
    "P0": "P0 staging/pilot 前必须处理",
    "P1": "P1 rehearsal 后优先处理",
    "P2": "P2 pilot 期间增强",
    "P3": "P3 长期平台能力",
}
ALLOWED_PRIORITIES = set(PRIORITY_LABELS)

SOURCE_TYPE_LABELS = {
    "market signal": "市场信号",
    "feedback": "客户反馈",
    "order": "订单",
    "shipment": "物流",
    "operator review": "运营审查",
    "partner onboarding": "Partner 接入",
}
ALLOWED_SOURCE_TYPES = set(SOURCE_TYPE_LABELS)

REVIEW_DIMENSION_LABELS = {
    "load": "承重",
    "stability": "稳定性",
    "noise": "噪音",
    "delivery": "交付",
    "installation": "安装",
    "after-sales": "售后",
    "packaging": "包装",
    "warranty": "质保",
    "test cycle": "测试周期",
    "certification": "认证",
    "project demand": "项目制需求",
    "school procurement timing": "学校采购周期",
    "delivery consistency": "交付一致性",
    "resource needs": "资料需求",
    "feedback after use": "使用后反馈",
    "project acceptance criteria": "项目验收标准",
    "product family": "产品族",
    "quote logic": "报价逻辑",
    "delivery requirement": "交付要求",
    "customer-visible fields": "客户可见字段",
    "market response metrics": "市场响应指标",
}
ALLOWED_REVIEW_DIMENSIONS = set(REVIEW_DIMENSION_LABELS)

TOKEN_LIKE_MARKERS = (
    "bearer ",
    "authorization:",
    "api_key",
    "api-key",
    "token=",
    "sk-",
    "ghp_",
    "xoxb-",
    "actual-secret",
)


def _clean_list(value: list[str] | None) -> list[str]:
    return [item.strip() for item in value or [] if item and item.strip()]


def _contains_token_like(value: str | None) -> bool:
    lower = (value or "").lower()
    return any(marker in lower for marker in TOKEN_LIKE_MARKERS)


class MarketResponseReviewBase(BaseModel):
    partner_focus: str = Field(min_length=1, max_length=128)
    focus_category: str = Field(min_length=1, max_length=96)
    product_focus: list[str] = Field(default_factory=list)
    review_dimension: str
    visibility_class: str = "needs validation"
    priority: str = "P2"
    status: str = "needs review"
    source_type: str = "operator review"
    source_summary: str = Field(min_length=1)
    evidence_summary: str | None = None
    customer_safe_summary: str | None = None
    internal_notes: str | None = None
    next_action: str | None = None
    owner: str | None = Field(default=None, max_length=255)
    due_date: date | None = None

    @field_validator("product_focus")
    @classmethod
    def normalize_product_focus(cls, value: list[str]) -> list[str]:
        return _clean_list(value)

    @field_validator("review_dimension")
    @classmethod
    def validate_review_dimension(cls, value: str) -> str:
        if value not in ALLOWED_REVIEW_DIMENSIONS:
            raise ValueError("unsupported market response review dimension")
        return value

    @field_validator("visibility_class")
    @classmethod
    def validate_visibility_class(cls, value: str) -> str:
        if value not in ALLOWED_VISIBILITY_CLASSES:
            raise ValueError("unsupported market response visibility class")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        if value not in ALLOWED_PRIORITIES:
            raise ValueError("unsupported market response priority")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in ALLOWED_REVIEW_STATUSES:
            raise ValueError("unsupported market response review status")
        return value

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        if value not in ALLOWED_SOURCE_TYPES:
            raise ValueError("unsupported market response source type")
        return value

    @model_validator(mode="after")
    def validate_safety_boundaries(self) -> "MarketResponseReviewBase":
        text_fields = (
            self.source_summary,
            self.evidence_summary,
            self.customer_safe_summary,
            self.internal_notes,
            self.next_action,
        )
        if any(_contains_token_like(value) for value in text_fields):
            raise ValueError("raw token or credential-like value is not allowed")
        if self.status == "reviewed" and self.visibility_class == "customer-safe candidate":
            if not (self.customer_safe_summary or "").strip():
                raise ValueError("customer_safe_summary is required before reviewing a customer-safe candidate")
        return self


class MarketResponseReviewCreate(MarketResponseReviewBase):
    pass


class MarketResponseReviewUpdate(BaseModel):
    partner_focus: str | None = Field(default=None, min_length=1, max_length=128)
    focus_category: str | None = Field(default=None, min_length=1, max_length=96)
    product_focus: list[str] | None = None
    review_dimension: str | None = None
    visibility_class: str | None = None
    priority: str | None = None
    status: str | None = None
    source_type: str | None = None
    source_summary: str | None = Field(default=None, min_length=1)
    evidence_summary: str | None = None
    customer_safe_summary: str | None = None
    internal_notes: str | None = None
    next_action: str | None = None
    owner: str | None = Field(default=None, max_length=255)
    due_date: date | None = None

    @field_validator("product_focus")
    @classmethod
    def normalize_product_focus(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return _clean_list(value)

    @field_validator("review_dimension")
    @classmethod
    def validate_review_dimension(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_REVIEW_DIMENSIONS:
            raise ValueError("unsupported market response review dimension")
        return value

    @field_validator("visibility_class")
    @classmethod
    def validate_visibility_class(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_VISIBILITY_CLASSES:
            raise ValueError("unsupported market response visibility class")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_PRIORITIES:
            raise ValueError("unsupported market response priority")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_REVIEW_STATUSES:
            raise ValueError("unsupported market response review status")
        return value

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_SOURCE_TYPES:
            raise ValueError("unsupported market response source type")
        return value

    @model_validator(mode="after")
    def validate_secret_boundaries(self) -> "MarketResponseReviewUpdate":
        text_fields = (
            self.source_summary,
            self.evidence_summary,
            self.customer_safe_summary,
            self.internal_notes,
            self.next_action,
        )
        if any(_contains_token_like(value) for value in text_fields):
            raise ValueError("raw token or credential-like value is not allowed")
        return self


class MarketResponseReviewRead(BaseModel):
    id: UUID
    partner_focus: str
    focus_category: str
    product_focus: list[str]
    review_dimension: str
    review_dimension_label: str
    visibility_class: str
    visibility_class_label: str
    priority: str
    priority_label: str
    status: str
    status_label: str
    source_type: str
    source_type_label: str
    source_summary: str
    evidence_summary: str | None
    customer_safe_summary: str | None
    internal_notes: str | None
    next_action: str | None
    owner: str | None
    due_date: date | None
    created_at: datetime
    updated_at: datetime
