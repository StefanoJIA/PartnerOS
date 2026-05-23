from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.crm import CompanyDetailOut, ContactOut, LeadOut


class LeadIntelligenceWorkflowOut(BaseModel):
    """A-domain workbench payload: company → contact → intel → score → actions."""

    lead: LeadOut
    company: CompanyDetailOut
    primary_contact: ContactOut | None
    intelligence_score: int = Field(ge=0, le=100)
    score_breakdown: dict[str, int]
    suggested_next_actions: list[str]
    market_intelligence_count: int
    market_intelligence_preview_ids: list[UUID]
    market_fit_segments: list[str] = Field(
        default_factory=list,
        description=(
            "Explainable tags: lift_system_signal, general_office_furniture_only (D5.1 weak industry fit), "
            "oem_odm_fit, medical_vertical, education_vertical, heavy_duty_fit, project_based_furniture"
        ),
    )


class TouchpointCreate(BaseModel):
    """Log interaction on lead and refresh sales next step (D5 closed loop)."""

    interaction_type: str = Field(..., min_length=1, max_length=64)
    channel: str = Field(..., min_length=1, max_length=64)
    subject: str | None = Field(None, max_length=512)
    content: str | None = None
    summary: str | None = None
    direction: str | None = Field(None, max_length=32)
    next_action: str | None = None
    next_action_due_date: date | None = None
    interaction_next_action: str | None = None
    interaction_next_action_due_date: date | None = None
