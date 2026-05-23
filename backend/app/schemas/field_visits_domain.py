from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class FieldVisitPlanCreate(BaseModel):
    plan_name: str
    city: str | None = None
    state: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    salesperson: str | None = None
    purpose: str | None = None
    sample_items: str | None = None


class FieldVisitPlanUpdate(BaseModel):
    city: str | None = None
    state: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    salesperson: str | None = None
    purpose: str | None = None
    sample_items: str | None = None
    status: str | None = None
    summary: str | None = None
    ai_visit_brief: str | None = None


class FieldVisitPlanOut(BaseModel):
    id: UUID
    plan_name: str
    status: str
    city: str | None

    model_config = {"from_attributes": True}


class FieldVisitTargetCreate(BaseModel):
    company_id: UUID | None = None
    contact_id: UUID | None = None
    address: str | None = None
    scheduled_time: datetime | None = None
    priority: str | None = None
    pre_contact_status: str | None = None


class FieldVisitTargetUpdate(BaseModel):
    visit_result: str | None = None
    interest_level: str | None = None
    next_action: str | None = None
    follow_up_due_date: date | None = None
    notes: str | None = None
    recommended_products: str | None = None
    talking_points: str | None = None


class FieldVisitTargetOut(BaseModel):
    id: UUID
    company_id: UUID | None
    visit_result: str | None

    model_config = {"from_attributes": True}
