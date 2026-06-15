import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_mixins import TimestampMixin, UserAuditMixin
from app.core.database import Base


class GrowthCampaign(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "growth_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_focus: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    product_focus: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    target_segment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned", index=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    next_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    tasks: Mapped[list["GrowthCampaignTask"]] = relationship(
        "GrowthCampaignTask",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="GrowthCampaignTask.created_at.desc()",
    )


class GrowthCampaignTask(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "growth_campaign_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("growth_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    task_type: Mapped[str] = mapped_column(String(64), nullable=False, default="manual_outreach")
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="zh")
    draft_subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    draft_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned", index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    campaign: Mapped[GrowthCampaign] = relationship("GrowthCampaign", back_populates="tasks")
    company: Mapped[Any] = relationship("Company")
    contact: Mapped[Any] = relationship("Contact")


class SalesOpportunity(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "sales_opportunities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("growth_campaigns.id", ondelete="SET NULL"), nullable=True, index=True
    )
    quote_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    partner_focus: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    product_focus: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    customer_segment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    project_size: Mapped[str | None] = mapped_column(String(64), nullable=True)
    estimated_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    decision_stage: Mapped[str] = mapped_column(String(64), nullable=False, default="discovery", index=True)
    competition: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk: Mapped[str | None] = mapped_column(Text, nullable=True)
    probability: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="P2", index=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    next_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocker: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open", index=True)
    expected_close_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    won_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    lost_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    company: Mapped[Any] = relationship("Company")
    lead: Mapped[Any] = relationship("Lead")
    campaign: Mapped[Any] = relationship("GrowthCampaign")
    quote: Mapped[Any] = relationship("Quote")
    order: Mapped[Any] = relationship("CustomerOrder")
