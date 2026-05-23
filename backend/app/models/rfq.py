from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class RFQ(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "rfqs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    customer_requirement: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    target_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    required_certifications: Mapped[str | None] = mapped_column(Text, nullable=True)
    packaging_requirement: Mapped[str | None] = mapped_column(Text, nullable=True)
    shipping_requirement: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    ai_requirement_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_recommended_partners: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    items: Mapped[list["RFQItem"]] = relationship(
        "RFQItem", back_populates="rfq", cascade="all, delete-orphan"
    )
    partner_candidates: Mapped[list["RFQPartnerCandidate"]] = relationship(
        "RFQPartnerCandidate", back_populates="rfq", cascade="all, delete-orphan"
    )
    quotations: Mapped[list["Quotation"]] = relationship(
        "Quotation", back_populates="rfq", cascade="all, delete-orphan"
    )


class RFQItem(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "rfq_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spec_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    required_certifications: Mapped[str | None] = mapped_column(Text, nullable=True)
    packaging_requirement: Mapped[str | None] = mapped_column(Text, nullable=True)
    shipping_requirement: Mapped[str | None] = mapped_column(Text, nullable=True)

    rfq: Mapped["RFQ"] = relationship("RFQ", back_populates="items")


class RFQPartnerCandidate(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "rfq_partner_candidates"
    __table_args__ = (UniqueConstraint("rfq_id", "partner_id", name="uq_rfq_partner_candidate"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    partner_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quote_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    quote_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_preferred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    capability_level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    partner_moq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lead_time_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    partner_price_range: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sample_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    certification_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_fit: Mapped[str | None] = mapped_column(String(64), nullable=True)

    rfq: Mapped["RFQ"] = relationship("RFQ", back_populates="partner_candidates")


class Quotation(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "quotations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    manufacturing_partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    incoterm: Mapped[str | None] = mapped_column(String(32), nullable=True)
    moq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lead_time: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sample_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    tooling_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    packaging_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    estimated_shipping_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    landed_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    target_margin: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    rfq: Mapped["RFQ | None"] = relationship("RFQ", back_populates="quotations")
    lines: Mapped[list["QuotationItem"]] = relationship(
        "QuotationItem", back_populates="quotation", cascade="all, delete-orphan"
    )


class QuotationItem(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "quotation_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)

    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="lines")
