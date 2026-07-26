"""Commercial pilot operations models."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class SupplierDevelopmentTask(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "supplier_development_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_discovery_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supplier_discovery_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority: Mapped[str] = mapped_column(String(8), nullable=False, default="P2")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    depends_on_task_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_draft_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    checklist_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class CategoryCoverageAssessment(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "category_coverage_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    industry_vertical: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    assessment_label: Mapped[str] = mapped_column(String(128), nullable=False)
    customer_needs_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    coverage_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    gaps_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    risk_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    suggested_actions_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    linked_evidence_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CommercialPilotRun(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "commercial_pilot_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pilot_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    pilot_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry_vertical: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    synthetic_customer_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    requirements_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    candidate_summary_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    selection_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    gap_tasks_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    project_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_project_requests.id", ondelete="SET NULL"), nullable=True
    )
    quote_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="SET NULL"), nullable=True
    )
    market_response_review_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("market_response_reviews.id", ondelete="SET NULL"), nullable=True
    )
    scenario_pricing_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
