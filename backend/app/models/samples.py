from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class Sample(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "samples"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sample_request_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True
    )
    rfq_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    manufacturing_partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="SET NULL"), nullable=True
    )
    sample_status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sample_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    shipping_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    courier: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shipped_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    delivered_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    customer_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    shipping_destination: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    interest_level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    next_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    converted_to_rfq: Mapped[bool] = mapped_column(default=False, nullable=False)
    converted_to_order: Mapped[bool] = mapped_column(default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    shipments: Mapped[list["SampleShipment"]] = relationship(
        "SampleShipment", back_populates="sample", cascade="all, delete-orphan"
    )


class SampleShipment(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "sample_shipments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("samples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    carrier: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    sample: Mapped["Sample"] = relationship("Sample", back_populates="shipments")
