from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.crm import LeadOut


class CompanyWorkspaceCard(BaseModel):
    id: UUID
    company_name: str
    company_type: str
    website: str | None
    linkedin_url: str | None
    city: str | None
    state: str | None
    strategic_level: str | None

    model_config = {"from_attributes": True}


class ContactWorkspaceCard(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    title: str | None
    email: str | None
    phone: str | None
    linkedin_url: str | None

    model_config = {"from_attributes": True}


class RFQWorkspaceBrief(BaseModel):
    id: UUID
    rfq_number: str
    status: str
    lead_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SampleWorkspaceBrief(BaseModel):
    id: UUID
    sample_request_number: str
    sample_status: str
    lead_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderWorkspaceBrief(BaseModel):
    id: UUID
    order_number: str
    rfq_id: UUID | None
    sample_id: UUID | None = None
    production_status: str | None
    risk_level: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FieldVisitWorkspaceBrief(BaseModel):
    target_id: UUID
    plan_id: UUID
    plan_name: str
    company_id: UUID | None
    scheduled_time: datetime | None
    visit_result: str | None
    status: str | None


class InteractionWorkspaceBrief(BaseModel):
    id: UUID
    related_object_type: str
    related_object_id: UUID
    interaction_type: str
    channel: str
    subject: str | None
    interaction_date: datetime

    model_config = {"from_attributes": True}


class TaskWorkspaceBrief(BaseModel):
    id: UUID
    title: str
    status: str
    priority: str | None
    due_at: datetime | None
    completed_at: datetime | None
    assignee_user_id: UUID | None
    assignee_email: str | None = None

    model_config = {"from_attributes": True}


class AIOutputWorkspaceBrief(BaseModel):
    id: UUID
    task_type: str
    status: str
    output_text: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LeadWorkspaceOut(BaseModel):
    lead: LeadOut
    company: CompanyWorkspaceCard
    contact: ContactWorkspaceCard | None
    owner_display: str | None = None
    related_rfqs: list[RFQWorkspaceBrief]
    related_samples: list[SampleWorkspaceBrief]
    related_orders: list[OrderWorkspaceBrief]
    related_field_visits: list[FieldVisitWorkspaceBrief]
    recent_interactions: list[InteractionWorkspaceBrief]
    open_tasks: list[TaskWorkspaceBrief]
    recent_ai_outputs: list[AIOutputWorkspaceBrief]
