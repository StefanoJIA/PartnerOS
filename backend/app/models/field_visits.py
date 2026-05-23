from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class FieldVisitPlan(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "field_visit_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    salesperson: Mapped[str | None] = mapped_column(String(255), nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_items: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_company_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="draft", nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_visit_brief: Mapped[str | None] = mapped_column(Text, nullable=True)

    targets: Mapped[list["FieldVisitTarget"]] = relationship(
        "FieldVisitTarget", back_populates="plan", cascade="all, delete-orphan"
    )


class FieldVisitTarget(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "field_visit_targets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("field_visit_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pre_contact_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_products: Mapped[str | None] = mapped_column(Text, nullable=True)
    talking_points: Mapped[str | None] = mapped_column(Text, nullable=True)
    visit_result: Mapped[str | None] = mapped_column(String(128), nullable=True)
    interest_level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    next_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    plan: Mapped["FieldVisitPlan"] = relationship("FieldVisitPlan", back_populates="targets")
