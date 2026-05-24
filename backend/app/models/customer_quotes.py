"""D6.3 — Customer Quote records (distinct from RFQ Partner Quotation)."""

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
from app.models.base_mixins import TimestampMixin, UserAuditMixin

QUOTE_STATUSES = (
    "internal_review",
    "ready_to_send",
    "sent",
    "revised",
    "expired",
    "converted_to_order",
)


class Quote(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "quotes"
    __table_args__ = (UniqueConstraint("quote_number", name="uq_quotes_quote_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    sales_owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    quote_date: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="internal_review", index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    default_incoterm: Mapped[str | None] = mapped_column(String(16), nullable=True)
    payment_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    shipping_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    bill_to_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    bill_to_company: Mapped[str | None] = mapped_column(String(256), nullable=True)
    bill_to_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    ship_to_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ship_to_company: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ship_to_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_quote_input_contract_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    adjustment_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    manual_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    send_channel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    line_items: Mapped[list["QuoteLineItem"]] = relationship("QuoteLineItem", back_populates="quote", cascade="all, delete-orphan")
    adjustments: Mapped[list["QuoteAdjustment"]] = relationship("QuoteAdjustment", back_populates="quote", cascade="all, delete-orphan")
    versions: Mapped[list["QuoteVersion"]] = relationship("QuoteVersion", back_populates="quote", cascade="all, delete-orphan")
    terms: Mapped["QuoteTerms | None"] = relationship("QuoteTerms", back_populates="quote", uselist=False, cascade="all, delete-orphan")


class QuoteVersion(Base):
    __tablename__ = "quote_versions"
    __table_args__ = (UniqueConstraint("quote_id", "version_number", name="uq_quote_version_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    version_type: Mapped[str] = mapped_column(String(32), nullable=False, default="revised")
    created_from_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("quote_versions.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    quote: Mapped["Quote"] = relationship("Quote", back_populates="versions")


class QuoteLineItem(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "quote_line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    quote_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("quote_versions.id", ondelete="SET NULL"), nullable=True)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    partner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_catalog_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("product_catalog.id", ondelete="SET NULL"), nullable=True)
    internal_sku: Mapped[str | None] = mapped_column(String(64), nullable=True)
    partner_product_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    manual_product_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    product_name: Mapped[str] = mapped_column(String(512), nullable=False)
    product_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description_customer: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_internal: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    uom: Mapped[str] = mapped_column(String(16), nullable=False, default="EA")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    final_unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    incoterm: Mapped[str | None] = mapped_column(String(16), nullable=True)
    pricing_source: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    pricing_strategy: Mapped[str | None] = mapped_column(String(32), nullable=True)
    discount_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    discount_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    color_finish: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_dimension: Mapped[str | None] = mapped_column(String(128), nullable=True)
    attributes_snapshot_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cost_snapshot_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pricing_breakdown_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    customer_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    internal_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    estimated_margin: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    quote: Mapped["Quote"] = relationship("Quote", back_populates="line_items")


class QuoteAdjustment(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "quote_adjustments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    percentage: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    taxable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    customer_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    quote: Mapped["Quote"] = relationship("Quote", back_populates="adjustments")


class QuoteTerms(Base, TimestampMixin):
    __tablename__ = "quote_terms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, unique=True)
    payment_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    shipping_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    validity_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    warranty_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    quote: Mapped["Quote"] = relationship("Quote", back_populates="terms")
