"""D6.2 — product catalog and pricing foundation (Phase 2, not Customer Quote)."""

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


class ProductCatalog(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "product_catalog"
    __table_args__ = (
        UniqueConstraint("internal_sku", name="uq_product_catalog_internal_sku"),
        UniqueConstraint("partner_id", "partner_product_code", name="uq_product_catalog_partner_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    internal_sku: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    partner_product_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    product_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    product_category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    product_family: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description_customer: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_internal: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    default_uom: Mapped[str] = mapped_column(String(16), nullable=False, default="EA")
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    default_incoterm: Mapped[str | None] = mapped_column(String(16), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    attributes_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    cost_models: Mapped[list["ProductCostModel"]] = relationship(
        "ProductCostModel", back_populates="product", cascade="all, delete-orphan"
    )
    price_tiers: Mapped[list["ProductPriceTier"]] = relationship(
        "ProductPriceTier", back_populates="product", cascade="all, delete-orphan"
    )


class ProductCostModel(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "product_cost_models"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_catalog.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cost_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    unit_material_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    unit_weight: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    ocean_freight_unit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    domestic_transport_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    domestic_profit_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    fob_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    ddp_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["ProductCatalog"] = relationship("ProductCatalog", back_populates="cost_models")


class ProductPriceTier(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "product_price_tiers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_catalog.id", ondelete="CASCADE"), nullable=False, index=True
    )
    min_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    max_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    incoterm: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    base_unit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    adjustment_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    final_unit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    pricing_strategy: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["ProductCatalog"] = relationship("ProductCatalog", back_populates="price_tiers")


class MarginStrategyTier(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "margin_strategy_tiers"
    __table_args__ = (
        UniqueConstraint("strategy_code", "min_qty", "max_qty", name="uq_margin_strategy_tier"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    strategy_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    min_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    max_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    multiplier: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class FxRate(Base):
    __tablename__ = "fx_rates"
    __table_args__ = (
        UniqueConstraint("base_currency", "quote_currency", "rate_date", name="uq_fx_rate_pair_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    quote_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    rate_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_manual_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
