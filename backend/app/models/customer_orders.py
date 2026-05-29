"""D7.2 — Customer Order records (distinct from legacy Phase 1 orders table)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixins import TimestampMixin

ORDER_STATUSES_MVP = (
    "pending_customer_confirmation",
    "confirmed",
    "cancelled",
)

ORDER_STATUSES_FUTURE = (
    "internal_review",
    "supplier_confirmation_pending",
    "supplier_confirmed",
    "production_pending",
    "in_production",
    "ready_to_ship",
    "shipped",
    "delivered",
    "on_hold",
)

ORDER_LINE_STATUSES = ("pending", "confirmed", "cancelled")

CUSTOMER_CONFIRMATION_TYPES = (
    "email",
    "purchase_order",
    "signed_quote",
    "verbal",
    "internal_note",
    "other",
)

CONFIRMATION_STRENGTHS = ("strong", "medium", "weak")

CONFIRMATION_STATUSES = ("active", "voided")

STRENGTH_BY_TYPE = {
    "purchase_order": "strong",
    "signed_quote": "strong",
    "email": "medium",
    "verbal": "weak",
    "internal_note": "weak",
    "other": "weak",
}

SPLIT_STATUSES = (
    "pending_supplier_confirmation",
    "supplier_confirmed",
    "production_pending",
    "on_hold",
    "cancelled",
)

SUPPLIER_SPLIT_CONFIRMATION_STATUSES = (
    "not_requested",
    "pending",
    "partially_confirmed",
    "confirmed",
    "rejected",
    "needs_clarification",
)

SUPPLIER_CONFIRMATION_STATUSES = (
    "confirmed",
    "rejected",
    "needs_clarification",
    "partially_confirmed",
)

SUPPLIER_RECORD_STATUSES = ("active", "voided")

MILESTONE_TYPES = (
    "order_received",
    "supplier_confirmed",
    "materials_prepared",
    "cutting",
    "welding",
    "painting",
    "assembly",
    "quality_check",
    "packing",
    "ready_to_ship",
    "production_started",
    "production_pending",
    "custom",
)

MILESTONE_STATUSES = (
    "planned",
    "in_progress",
    "completed",
    "delayed",
    "blocked",
    "skipped",
    "cancelled",
)

MILESTONE_SOURCES = ("template", "manual", "imported", "system")

SHIPMENT_PLAN_STATUSES = (
    "draft",
    "planned",
    "shipped",
    "delivered",
    "cancelled",
)


class CustomerOrder(Base, TimestampMixin):
    __tablename__ = "customer_orders"
    __table_args__ = (UniqueConstraint("order_number", name="uq_customer_orders_order_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_quote_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_quote_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quote_versions.id", ondelete="SET NULL"), nullable=True
    )
    source_pdf_export_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quote_pdf_exports.id", ondelete="SET NULL"), nullable=True
    )
    source_delivery_log_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quote_delivery_logs.id", ondelete="SET NULL"), nullable=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(48), nullable=False, default="pending_customer_confirmation", index=True)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    customer_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    customer_confirmation_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    customer_confirmation_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    bill_to_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    bill_to_company: Mapped[str | None] = mapped_column(String(256), nullable=True)
    bill_to_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    ship_to_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ship_to_company: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ship_to_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    adjustment_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    payment_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    shipping_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_input_contract_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    readiness_snapshot_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    line_items: Mapped[list["OrderLineItem"]] = relationship(
        "OrderLineItem", back_populates="order", cascade="all, delete-orphan"
    )
    confirmations: Mapped[list["OrderConfirmation"]] = relationship(
        "OrderConfirmation", back_populates="order", cascade="all, delete-orphan"
    )
    partner_splits: Mapped[list["OrderPartnerSplit"]] = relationship(
        "OrderPartnerSplit", back_populates="order", cascade="all, delete-orphan"
    )
    supplier_confirmations: Mapped[list["SupplierConfirmation"]] = relationship(
        "SupplierConfirmation", back_populates="order", cascade="all, delete-orphan"
    )
    production_milestones: Mapped[list["OrderProductionMilestone"]] = relationship(
        "OrderProductionMilestone", back_populates="order", cascade="all, delete-orphan"
    )
    shipment_plans: Mapped[list["ShipmentPlan"]] = relationship(
        "ShipmentPlan", back_populates="order", cascade="all, delete-orphan"
    )


class OrderConfirmation(Base, TimestampMixin):
    __tablename__ = "order_confirmations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    confirmation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    confirmation_strength: Mapped[str] = mapped_column(String(16), nullable=False)
    confirmed_by_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    confirmed_by_email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    confirmed_by_company: Mapped[str | None] = mapped_column(String(256), nullable=True)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_channel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    evidence_storage_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active", index=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    order: Mapped["CustomerOrder"] = relationship("CustomerOrder", back_populates="confirmations")


class OrderLineItem(Base, TimestampMixin):
    __tablename__ = "order_line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_quote_line_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quote_line_items.id", ondelete="RESTRICT"), nullable=False
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_catalog_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_catalog.id", ondelete="SET NULL"), nullable=True
    )
    internal_sku: Mapped[str | None] = mapped_column(String(64), nullable=True)
    partner_product_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    product_name: Mapped[str] = mapped_column(String(512), nullable=False)
    product_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description_customer: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_internal: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    uom: Mapped[str] = mapped_column(String(16), nullable=False, default="EA")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    incoterm: Mapped[str | None] = mapped_column(String(16), nullable=True)
    color_finish: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_dimension: Mapped[str | None] = mapped_column(String(128), nullable=True)
    attributes_snapshot_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    customer_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    supplier_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    order: Mapped["CustomerOrder"] = relationship("CustomerOrder", back_populates="line_items")


class OrderPartnerSplit(Base, TimestampMixin):
    __tablename__ = "order_partner_splits"
    __table_args__ = (UniqueConstraint("order_id", "partner_id", name="uq_order_partner_splits_order_partner"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    split_number: Mapped[str] = mapped_column(String(32), nullable=False)
    split_status: Mapped[str] = mapped_column(String(48), nullable=False, default="pending_supplier_confirmation")
    partner_reference_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    supplier_confirmation_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    supplier_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_production_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_ready_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    line_item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    order: Mapped["CustomerOrder"] = relationship("CustomerOrder", back_populates="partner_splits")
    supplier_confirmations: Mapped[list["SupplierConfirmation"]] = relationship(
        "SupplierConfirmation", back_populates="partner_split", cascade="all, delete-orphan"
    )
    production_milestones: Mapped[list["OrderProductionMilestone"]] = relationship(
        "OrderProductionMilestone", back_populates="partner_split", cascade="all, delete-orphan"
    )
    shipment_plans: Mapped[list["ShipmentPlan"]] = relationship(
        "ShipmentPlan", back_populates="partner_split"
    )


class SupplierConfirmation(Base, TimestampMixin):
    __tablename__ = "supplier_confirmations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    partner_split_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("order_partner_splits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    confirmation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_by_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    confirmed_by_email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    confirmation_channel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    inventory_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    certification_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    lead_time_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    production_capacity_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expected_production_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_ready_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    supplier_reference: Mapped[str | None] = mapped_column(String(256), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active", index=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    order: Mapped["CustomerOrder"] = relationship("CustomerOrder", back_populates="supplier_confirmations")
    partner_split: Mapped["OrderPartnerSplit"] = relationship("OrderPartnerSplit", back_populates="supplier_confirmations")


class OrderProductionMilestone(Base, TimestampMixin):
    __tablename__ = "order_production_milestones"
    __table_args__ = (
        UniqueConstraint("partner_split_id", "milestone_type", name="uq_order_prod_milestones_split_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    partner_split_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("order_partner_splits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    milestone_type: Mapped[str] = mapped_column(String(64), nullable=False)
    milestone_label: Mapped[str] = mapped_column(String(128), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned", index=True)
    planned_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    responsible_party: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="template")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    order: Mapped["CustomerOrder"] = relationship("CustomerOrder", back_populates="production_milestones")
    partner_split: Mapped["OrderPartnerSplit"] = relationship("OrderPartnerSplit", back_populates="production_milestones")


class ShipmentPlan(Base, TimestampMixin):
    __tablename__ = "shipment_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    partner_split_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("order_partner_splits.id", ondelete="SET NULL"), nullable=True, index=True
    )
    shipment_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    incoterm: Mapped[str | None] = mapped_column(String(16), nullable=True)
    origin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    destination: Mapped[str | None] = mapped_column(String(255), nullable=True)
    estimated_ship_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_arrival_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    order: Mapped["CustomerOrder"] = relationship("CustomerOrder", back_populates="shipment_plans")
    partner_split: Mapped["OrderPartnerSplit | None"] = relationship("OrderPartnerSplit", back_populates="shipment_plans")
    tracking_events: Mapped[list["ShipmentTrackingEvent"]] = relationship(
        "ShipmentTrackingEvent", back_populates="shipment_plan", cascade="all, delete-orphan"
    )


class ShipmentTrackingEvent(Base, TimestampMixin):
    __tablename__ = "shipment_tracking_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shipment_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    shipment_plan: Mapped["ShipmentPlan"] = relationship("ShipmentPlan", back_populates="tracking_events")
