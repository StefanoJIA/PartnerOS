from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TaskActionBrief(BaseModel):
    id: UUID
    title: str
    status: str
    priority: str | None
    due_at: datetime | None = None
    completed_at: datetime | None = None
    assignee_email: str | None = None
    related_object_type: str | None = None
    related_object_id: UUID | None = None
    created_at: datetime


class LeadActionBrief(BaseModel):
    id: UUID
    lead_name: str
    current_stage: str
    priority: str | None
    source: str
    next_action_due_date: date | None
    company_id: UUID


class OrderActionBrief(BaseModel):
    id: UUID
    order_number: str
    risk_level: str | None
    production_status: str | None
    rfq_id: UUID | None
    target_delivery_date: date | None = None
    updated_at: datetime


class RFQActionBrief(BaseModel):
    id: UUID
    rfq_number: str
    status: str
    lead_id: UUID | None
    company_id: UUID | None
    updated_at: datetime


class SampleActionBrief(BaseModel):
    id: UUID
    sample_request_number: str
    sample_status: str
    lead_id: UUID | None = None
    delivered_date: date | None = None
    follow_up_due_date: date | None = None


class OrderMilestoneRisk(BaseModel):
    order_id: UUID
    order_number: str
    rfq_id: UUID | None
    milestone_id: UUID
    milestone_name: str
    planned_date: date | None
    delay_days: int | None
    risk_level: str | None


class AIOutputBrief(BaseModel):
    id: UUID
    task_type: str
    status: str
    input_object_type: str | None
    input_object_id: UUID | None
    created_at: datetime


class RecommendedAction(BaseModel):
    id: str
    title: str
    message: str
    severity: str = "medium"
    object_type: str
    object_id: UUID
    path: str = Field(description="Frontend path e.g. /tasks, /leads/{id}")


class DashboardActionsOut(BaseModel):
    due_today_tasks: list[TaskActionBrief]
    overdue_tasks: list[TaskActionBrief]
    this_week_tasks: list[TaskActionBrief]
    leads_follow_up_due_today: list[LeadActionBrief]
    hot_leads: list[LeadActionBrief]
    leads_needing_follow_up: list[LeadActionBrief]
    leads_recent_activity: list[LeadActionBrief]
    leads_waiting_next_step: list[LeadActionBrief]
    rfqs_waiting_partner_quote: list[RFQActionBrief]
    rfqs_customer_reviewing: list[RFQActionBrief]
    rfqs_negotiating: list[RFQActionBrief]
    samples_requested: list[SampleActionBrief]
    samples_shipped: list[SampleActionBrief]
    samples_delivered_no_feedback: list[SampleActionBrief]
    samples_follow_up_due: list[SampleActionBrief]
    orders_delayed_milestones: list[OrderMilestoneRisk]
    high_risk_orders: list[OrderActionBrief]
    orders_eta_missing: list[OrderActionBrief]
    orders_eta_passed_not_delivered: list[OrderActionBrief]
    recent_ai_outputs: list[AIOutputBrief]
    recommended_actions: list[RecommendedAction]


class DailyDecisionQueueItem(BaseModel):
    id: str
    title: str
    category: str
    priority: str
    severity: str
    owner: str | None = None
    due_date: date | None = None
    partner_focus: str | None = None
    product_focus: list[str] = Field(default_factory=list)
    customer_or_account: str | None = None
    readiness_impact: list[str] = Field(default_factory=list)
    risk: str
    reason: str
    next_action: str
    source_type: str
    source_id: str | None = None
    source_path: str
    depends_on_external_input: bool = False
    needs_business_signoff: bool = False
    needs_security_signoff: bool = False
    needs_partner_feedback: bool = False
    needs_staging_credentials: bool = False
    affects_d9: bool = False
    affects_pilot: bool = False
    customer_safe_boundary: str | None = None
    handling: "DailyQueueHandlingRecordOut | None" = None


class DailyDecisionQueueSummary(BaseModel):
    total: int
    p0: int
    p1: int
    staging_or_d9: int
    pilot: int
    external_input_required: int
    business_signoff_required: int
    security_signoff_required: int
    partner_feedback_required: int
    order_or_feedback_risk: int
    acknowledged: int = 0
    in_progress: int = 0
    blocked: int = 0
    deferred: int = 0
    waiting_external: int = 0
    overdue_followups: int = 0
    my_items: int = 0
    status: str
    external_staging_state: str


class DailyDecisionQueueRollup(BaseModel):
    key: str
    label: str
    total: int
    p0: int
    p1: int
    affects_d9: int
    affects_pilot: int
    external_input_required: int
    top_priority: str
    top_next_action: str
    source_paths: list[str] = Field(default_factory=list)


class DailyDecisionQueueOut(BaseModel):
    summary: DailyDecisionQueueSummary
    items: list[DailyDecisionQueueItem]
    decision_brief: list[str] = Field(default_factory=list)
    partner_rollup: list[DailyDecisionQueueRollup] = Field(default_factory=list)
    product_rollup: list[DailyDecisionQueueRollup] = Field(default_factory=list)
    category_rollup: list[DailyDecisionQueueRollup] = Field(default_factory=list)
    safety: dict[str, bool]


class DailyQueueHandlingRecordOut(BaseModel):
    id: UUID
    queue_item_id: str
    source_type: str
    source_id: str | None
    source_path: str
    title: str
    category: str
    priority: str
    partner_focus: str | None = None
    product_focus: list[str] = Field(default_factory=list)
    customer_or_account: str | None = None
    owner: str | None = None
    handling_status: str
    follow_up_date: date | None = None
    blocked_reason: str | None = None
    internal_note: str | None = None
    decision_summary: str | None = None
    last_action: str | None = None
    action_count: int
    handling_events: list[dict] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DailyQueueHandlingUpdate(BaseModel):
    queue_item_id: str
    source_type: str
    source_id: str | None = None
    source_path: str
    title: str
    category: str
    priority: str
    partner_focus: str | None = None
    product_focus: list[str] = Field(default_factory=list)
    customer_or_account: str | None = None
    action: str
    owner: str | None = None
    handling_status: str | None = None
    follow_up_date: date | None = None
    blocked_reason: str | None = None
    internal_note: str | None = None
    decision_summary: str | None = None
