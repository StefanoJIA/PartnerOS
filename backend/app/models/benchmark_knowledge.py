"""Industry benchmark knowledge — isolated from manufacturing partners."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class BenchmarkBrand(Base, TimestampMixin, UserAuditMixin):
    """Public/industry reference brand — NOT a partner or authorized supplier."""

    __tablename__ = "benchmark_brands"
    __table_args__ = (UniqueConstraint("brand_code", name="uq_benchmark_brand_code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry_vertical: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    relationship_disclaimer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Industry reference only — not a PartnerOS partner, supplier, or authorized dealer.",
    )
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    capabilities: Mapped[list["BenchmarkProductCapability"]] = relationship(
        "BenchmarkProductCapability", back_populates="brand", cascade="all, delete-orphan"
    )
    source_references: Mapped[list["BenchmarkSourceReference"]] = relationship(
        "BenchmarkSourceReference", back_populates="brand", cascade="all, delete-orphan"
    )
    data_rights: Mapped["BenchmarkDataRights | None"] = relationship(
        "BenchmarkDataRights", back_populates="brand", uselist=False, cascade="all, delete-orphan"
    )


class BenchmarkProductCapability(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "benchmark_product_capabilities"
    __table_args__ = (UniqueConstraint("brand_id", "capability_key", name="uq_benchmark_capability"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("benchmark_brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_line: Mapped[str | None] = mapped_column(String(255), nullable=True)
    capability_key: Mapped[str] = mapped_column(String(128), nullable=False)
    capability_label: Mapped[str] = mapped_column(String(255), nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_verification")
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, default="PUBLIC_REFERENCE")
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    retrieved_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    brand: Mapped["BenchmarkBrand"] = relationship("BenchmarkBrand", back_populates="capabilities")


class BenchmarkSourceReference(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "benchmark_source_references"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("benchmark_brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    retrieved_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    excerpt_facts: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    brand: Mapped["BenchmarkBrand"] = relationship("BenchmarkBrand", back_populates="source_references")


class BenchmarkDataRights(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "benchmark_data_rights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("benchmark_brands.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    allowed_use: Mapped[str] = mapped_column(Text, nullable=False)
    prohibited_use: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="No unauthorized catalog copy, logos, images, or price reproduction.",
    )
    logo_copy_allowed: Mapped[bool] = mapped_column(default=False, nullable=False)
    catalog_copy_allowed: Mapped[bool] = mapped_column(default=False, nullable=False)
    price_copy_allowed: Mapped[bool] = mapped_column(default=False, nullable=False)
    last_reviewed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    brand: Mapped["BenchmarkBrand"] = relationship("BenchmarkBrand", back_populates="data_rights")
