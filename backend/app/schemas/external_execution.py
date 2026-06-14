from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


EXTERNAL_ACTION_STATUS_LABELS = {
    "draft": "草稿",
    "ready to send": "待人工发送",
    "sent manually": "已人工发送",
    "response received": "已收到真实回复",
    "blocked": "阻塞",
    "complete": "完成",
}

ALLOWED_EXTERNAL_ACTION_STATUSES = set(EXTERNAL_ACTION_STATUS_LABELS)

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


class ExternalExecutionActionBase(BaseModel):
    action_type: str = Field(min_length=1, max_length=96)
    target_partner_system: str = Field(min_length=1, max_length=255)
    partner_focus: str | None = Field(default=None, max_length=128)
    product_focus: list[str] = Field(default_factory=list)
    owner: str | None = Field(default=None, max_length=255)
    due_date: date | None = None
    dependency: str | None = None
    next_step: str | None = None
    status: str = "draft"
    response_summary: str | None = None
    risk_notes: str | None = None
    blocker_notes: str | None = None
    redacted_credential_status: str | None = Field(default=None, max_length=96)
    staging_readiness_key: str | None = Field(default=None, max_length=96)
    pilot_readiness_key: str | None = Field(default=None, max_length=96)
    notes: str | None = None

    @field_validator("product_focus")
    @classmethod
    def normalize_product_focus(cls, value: list[str]) -> list[str]:
        return _clean_list(value)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in ALLOWED_EXTERNAL_ACTION_STATUSES:
            raise ValueError("unsupported external execution status")
        return value

    @model_validator(mode="after")
    def validate_response_and_secret_boundaries(self) -> "ExternalExecutionActionBase":
        text_fields = (
            self.response_summary,
            self.risk_notes,
            self.blocker_notes,
            self.redacted_credential_status,
            self.notes,
        )
        if any(_contains_token_like(value) for value in text_fields):
            raise ValueError("raw token or credential-like value is not allowed")
        if self.status == "response received" and not (self.response_summary or "").strip():
            raise ValueError("response_summary is required before marking response received")
        return self


class ExternalExecutionActionCreate(ExternalExecutionActionBase):
    pass


class ExternalExecutionActionUpdate(BaseModel):
    action_type: str | None = Field(default=None, min_length=1, max_length=96)
    target_partner_system: str | None = Field(default=None, min_length=1, max_length=255)
    partner_focus: str | None = Field(default=None, max_length=128)
    product_focus: list[str] | None = None
    owner: str | None = Field(default=None, max_length=255)
    due_date: date | None = None
    dependency: str | None = None
    next_step: str | None = None
    status: str | None = None
    response_summary: str | None = None
    risk_notes: str | None = None
    blocker_notes: str | None = None
    redacted_credential_status: str | None = Field(default=None, max_length=96)
    staging_readiness_key: str | None = Field(default=None, max_length=96)
    pilot_readiness_key: str | None = Field(default=None, max_length=96)
    notes: str | None = None

    @field_validator("product_focus")
    @classmethod
    def normalize_product_focus(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return _clean_list(value)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_EXTERNAL_ACTION_STATUSES:
            raise ValueError("unsupported external execution status")
        return value

    @model_validator(mode="after")
    def validate_secret_boundaries(self) -> "ExternalExecutionActionUpdate":
        text_fields = (
            self.response_summary,
            self.risk_notes,
            self.blocker_notes,
            self.redacted_credential_status,
            self.notes,
        )
        if any(_contains_token_like(value) for value in text_fields):
            raise ValueError("raw token or credential-like value is not allowed")
        return self


class ExternalExecutionActionRead(BaseModel):
    id: UUID
    action_type: str
    target_partner_system: str
    partner_focus: str | None
    product_focus: list[str]
    owner: str | None
    due_date: date | None
    dependency: str | None
    next_step: str | None
    status: str
    status_label: str
    response_summary: str | None
    risk_notes: str | None
    blocker_notes: str | None
    redacted_credential_status: str | None
    staging_readiness_key: str | None
    pilot_readiness_key: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
