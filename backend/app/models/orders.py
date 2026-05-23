from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class Order(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True
    )
    rfq_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="SET NULL"), nullable=True
    )
    quotation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quotations.id", ondelete="SET NULL"), nullable=True
    )
    sample_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("samples.id", ondelete="SET NULL"), nullable=True, index=True
    )
    manufacturing_partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="SET NULL"), nullable=True
    )
    product_items: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    order_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    target_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    incoterm: Mapped[str | None] = mapped_column(String(32), nullable=True)
    production_status: Mapped[str | None] = mapped_column(String(128), nullable=True)
    shipping_status: Mapped[str | None] = mapped_column(String(128), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    order_items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    milestones: Mapped[list["ProductionMilestone"]] = relationship(
        "ProductionMilestone", back_populates="order", cascade="all, delete-orphan"
    )
    shipping_records: Mapped[list["ShippingRecord"]] = relationship(
        "ShippingRecord", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="order_items")


class ProductionMilestone(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "production_milestones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    milestone_name: Mapped[str] = mapped_column(String(128), nullable=False)
    planned_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    delay_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    responsible_party: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="milestones")


class ShippingRecord(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "shipping_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    origin_factory: Mapped[str | None] = mapped_column(String(255), nullable=True)
    origin_port: Mapped[str | None] = mapped_column(String(255), nullable=True)
    destination_port: Mapped[str | None] = mapped_column(String(255), nullable=True)
    destination_warehouse: Mapped[str | None] = mapped_column(String(255), nullable=True)
    incoterm: Mapped[str | None] = mapped_column(String(32), nullable=True)
    container_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    carton_dimensions: Mapped[str | None] = mapped_column(String(255), nullable=True)
    carton_weight: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cartons_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pallet_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cbm: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    freight_forwarder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    booking_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    etd: Mapped[date | None] = mapped_column(Date, nullable=True)
    eta: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_arrival_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    customs_status: Mapped[str | None] = mapped_column(String(128), nullable=True)
    delivery_status: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="shipping_records")
