"""Commercial pilot operations API schemas."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SupplierDevelopmentTaskOut(BaseModel):
    id: UUID
    supplier_discovery_id: UUID
    task_type: str
    title: str
    owner_user_id: UUID | None
    due_date: date | None
    priority: str
    status: str
    depends_on_task_ids: list | None
    result_summary: str | None
    email_draft_json: dict | None
    checklist_json: list | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SupplierDevelopmentTaskCreate(BaseModel):
    task_type: str
    title: str | None = None
    owner_user_id: UUID | None = None
    priority: str = "P2"
    due_days: int = 7
    depends_on_task_ids: list[str] | None = None


class SupplierDevelopmentTaskUpdate(BaseModel):
    status: str | None = None
    result_summary: str | None = None
    notes: str | None = None
    owner_user_id: UUID | None = None


class CategoryCoverageOut(BaseModel):
    id: UUID
    industry_vertical: str
    assessment_label: str
    customer_needs_json: dict
    coverage_json: dict
    gaps_json: dict | None
    risk_json: dict | None
    suggested_actions_json: list | None
    linked_evidence_json: dict | None
    generated_at: datetime

    model_config = {"from_attributes": True}


class CommercialPilotRunOut(BaseModel):
    id: UUID
    pilot_code: str
    pilot_name: str
    industry_vertical: str
    status: str
    synthetic_customer_json: dict
    requirements_json: dict
    candidate_summary_json: dict | None
    selection_json: dict | None
    gap_tasks_json: list | None
    project_request_id: UUID | None
    quote_id: UUID | None
    market_response_review_id: UUID | None
    scenario_pricing_blocked: bool
    result_summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CommercialMetricsOut(BaseModel):
    candidate_suppliers: int
    qualification_conversion_pct: float
    open_development_tasks: int
    commercial_pilot_runs: int
    projects_with_2_plus_candidates: int
    frozen_selection_snapshots: int
    pilots_with_quotes: int
    info_completeness_note: str
    sample_cycle_days: str
    quote_readiness_blocked_scenario: bool


class EmailDraftOut(BaseModel):
    subject: str
    body: str
    approval_required: str = "true"
    auto_send_blocked: str = "true"
