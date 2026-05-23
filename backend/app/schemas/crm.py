from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.constants.status_enums import LEAD_STAGES, PRIORITY_LEVELS, TASK_STATUSES
from app.models.enums import (
    CompanyType,
    LeadSource,
    LeadType,
)


class CompanyCreate(BaseModel):
    company_name: str
    website: str | None = None
    linkedin_url: str | None = None
    company_type: str
    industry: str | None = None
    size: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = "United States"
    address: str | None = None
    business_description: str | None = None
    customer_segment: str | None = None
    strategic_level: str | None = None
    product_interest_tags: str | None = None
    source: str | None = None
    status: str | None = None
    priority: str | None = None
    linkedin_status: str | None = None
    notes: str | None = None

    @field_validator("company_type")
    @classmethod
    def _company_type(cls, v: str) -> str:
        allowed = {e.value for e in CompanyType}
        if v not in allowed:
            raise ValueError(f"Invalid company_type; must be one of: {sorted(allowed)}")
        return v


class CompanyUpdate(BaseModel):
    company_name: str | None = None
    website: str | None = None
    linkedin_url: str | None = None
    company_type: str | None = None
    industry: str | None = None
    size: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    address: str | None = None
    business_description: str | None = None
    customer_segment: str | None = None
    strategic_level: str | None = None
    product_interest_tags: str | None = None
    source: str | None = None
    status: str | None = None
    priority: str | None = None
    linkedin_status: str | None = None
    ai_profile_summary: str | None = None
    ai_recommended_strategy: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class CompanyOut(BaseModel):
    id: UUID
    company_name: str
    company_type: str
    country: str | None
    city: str | None
    state: str | None
    linkedin_status: str | None
    status: str | None
    strategic_level: str | None
    website: str | None = None
    linkedin_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyDetailOut(BaseModel):
    """Full company row for workspace / detail views."""

    id: UUID
    company_name: str
    website: str | None
    linkedin_url: str | None
    company_type: str
    industry: str | None
    size: str | None
    city: str | None
    state: str | None
    country: str | None
    address: str | None
    business_description: str | None
    customer_segment: str | None
    strategic_level: str | None
    product_interest_tags: str | None
    source: str | None
    status: str | None
    priority: str | None
    linkedin_status: str | None
    ai_profile_summary: str | None
    ai_recommended_strategy: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    company_id: UUID
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    location: str | None = None
    contact_type: str | None = None
    decision_maker_level: str | None = None
    communication_preference: str | None = None
    status: str | None = None
    notes: str | None = None


class ContactUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    location: str | None = None
    contact_type: str | None = None
    decision_maker_level: str | None = None
    communication_preference: str | None = None
    last_contacted_at: datetime | None = None
    next_follow_up_at: datetime | None = None
    status: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class ContactOut(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    company_id: UUID
    email: str | None
    title: str | None
    phone: str | None = None
    linkedin_url: str | None = None

    model_config = {"from_attributes": True}


class ContactDetailOut(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    company_id: UUID
    title: str | None
    email: str | None
    phone: str | None
    linkedin_url: str | None
    location: str | None
    contact_type: str | None
    decision_maker_level: str | None
    communication_preference: str | None
    last_contacted_at: datetime | None
    next_follow_up_at: datetime | None
    status: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContactListItemOut(ContactDetailOut):
    company_name: str | None = None


class LeadCreate(BaseModel):
    lead_name: str
    company_id: UUID
    primary_contact_id: UUID | None = None
    source: str
    lead_type: str
    product_interest: str | None = None
    current_stage: str
    priority: str | None = None
    estimated_value: Decimal | None = None
    expected_timeline: str | None = None
    next_action: str | None = None
    next_action_due_date: date | None = None
    owner_user_id: UUID | None = None
    notes: str | None = None

    @field_validator("source")
    @classmethod
    def _source(cls, v: str) -> str:
        allowed = {e.value for e in LeadSource}
        if v not in allowed:
            raise ValueError(f"Invalid source; must be one of: {sorted(allowed)}")
        return v

    @field_validator("lead_type")
    @classmethod
    def _lead_type(cls, v: str) -> str:
        allowed = {e.value for e in LeadType}
        if v not in allowed:
            raise ValueError(f"Invalid lead_type; must be one of: {sorted(allowed)}")
        return v

    @field_validator("current_stage")
    @classmethod
    def _stage(cls, v: str) -> str:
        if v not in LEAD_STAGES:
            raise ValueError(f"Invalid current_stage; must be one of: {sorted(LEAD_STAGES)}")
        return v

    @field_validator("priority")
    @classmethod
    def _prio(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in PRIORITY_LEVELS:
            raise ValueError(f"Invalid priority; must be one of: {sorted(PRIORITY_LEVELS)}")
        return v


class LeadUpdate(BaseModel):
    lead_name: str | None = None
    primary_contact_id: UUID | None = None
    source: str | None = None
    lead_type: str | None = None
    product_interest: str | None = None
    current_stage: str | None = None
    priority: str | None = None
    estimated_value: Decimal | None = None
    expected_timeline: str | None = None
    next_action: str | None = None
    next_action_due_date: date | None = None
    owner_user_id: UUID | None = None
    ai_lead_summary: str | None = None
    ai_next_step_suggestion: str | None = None
    notes: str | None = None
    is_active: bool | None = None

    @field_validator("source")
    @classmethod
    def _source_u(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {e.value for e in LeadSource}
        if v not in allowed:
            raise ValueError(f"Invalid source; must be one of: {sorted(allowed)}")
        return v

    @field_validator("lead_type")
    @classmethod
    def _lt_u(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {e.value for e in LeadType}
        if v not in allowed:
            raise ValueError(f"Invalid lead_type; must be one of: {sorted(allowed)}")
        return v

    @field_validator("current_stage")
    @classmethod
    def _st_u(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in LEAD_STAGES:
            raise ValueError(f"Invalid current_stage; must be one of: {sorted(LEAD_STAGES)}")
        return v

    @field_validator("priority")
    @classmethod
    def _pr_u(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in PRIORITY_LEVELS:
            raise ValueError(f"Invalid priority; must be one of: {sorted(PRIORITY_LEVELS)}")
        return v


class LeadOut(BaseModel):
    id: UUID
    lead_name: str
    company_id: UUID
    current_stage: str
    lead_type: str
    source: str
    next_action_due_date: date | None
    owner_user_id: UUID | None
    product_interest: str | None = None
    notes: str | None = None
    next_action: str | None = None
    priority: str | None = None
    estimated_value: Decimal | None = None

    model_config = {"from_attributes": True}


class LeadStageBody(BaseModel):
    current_stage: str

    @field_validator("current_stage")
    @classmethod
    def _st(cls, v: str) -> str:
        if v not in LEAD_STAGES:
            raise ValueError(f"Invalid current_stage; must be one of: {sorted(LEAD_STAGES)}")
        return v


class InteractionCreate(BaseModel):
    related_object_type: str
    related_object_id: UUID
    interaction_type: str
    channel: str
    subject: str | None = None
    content: str | None = None
    summary: str | None = None
    direction: str | None = None
    interaction_date: datetime | None = None
    next_action: str | None = None
    next_action_due_date: date | None = None


class InteractionOut(BaseModel):
    id: UUID
    related_object_type: str
    related_object_id: UUID
    interaction_type: str
    channel: str
    interaction_date: datetime

    model_config = {"from_attributes": True}


class InteractionSpawnTaskBody(BaseModel):
    title: str | None = None
    assignee_user_id: UUID | None = None
    due_at: datetime | None = None


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    related_object_type: str | None = None
    related_object_id: UUID | None = None
    assignee_user_id: UUID | None = None
    due_at: datetime | None = None
    status: str = "open"
    priority: str | None = None

    @field_validator("status")
    @classmethod
    def _ts(cls, v: str) -> str:
        if v not in TASK_STATUSES:
            raise ValueError(f"Invalid task status; must be one of: {sorted(TASK_STATUSES)}")
        return v

    @field_validator("priority")
    @classmethod
    def _tp(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in PRIORITY_LEVELS:
            raise ValueError(f"Invalid priority; must be one of: {sorted(PRIORITY_LEVELS)}")
        return v


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_user_id: UUID | None = None
    due_at: datetime | None = None
    status: str | None = None
    priority: str | None = None
    is_active: bool | None = None

    @field_validator("status")
    @classmethod
    def _ts_u(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in TASK_STATUSES:
            raise ValueError(f"Invalid task status; must be one of: {sorted(TASK_STATUSES)}")
        return v

    @field_validator("priority")
    @classmethod
    def _tp_u(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in PRIORITY_LEVELS:
            raise ValueError(f"Invalid priority; must be one of: {sorted(PRIORITY_LEVELS)}")
        return v


class TaskOut(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    status: str
    priority: str | None = None
    due_at: datetime | None
    completed_at: datetime | None
    assignee_user_id: UUID | None
    assignee_email: str | None = None
    related_object_type: str | None = None
    related_object_id: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
