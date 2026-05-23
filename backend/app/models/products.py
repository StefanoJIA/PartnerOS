from typing import Optional

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class ProductCategory(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "product_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True
    )
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    children: Mapped[list["ProductCategory"]] = relationship(
        "ProductCategory", back_populates="parent"
    )
    parent: Mapped[Optional["ProductCategory"]] = relationship(
        "ProductCategory", remote_side=[id], back_populates="children"
    )


class Product(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    product_category: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    product_subcategory: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_features: Mapped[str | None] = mapped_column(Text, nullable=True)
    application_scenarios: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_customer_types: Mapped[str | None] = mapped_column(Text, nullable=True)
    dimensions: Mapped[str | None] = mapped_column(String(255), nullable=True)
    weight: Mapped[str | None] = mapped_column(String(128), nullable=True)
    load_capacity: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lifting_speed: Mapped[str | None] = mapped_column(String(128), nullable=True)
    noise_level: Mapped[str | None] = mapped_column(String(128), nullable=True)
    material: Mapped[str | None] = mapped_column(String(255), nullable=True)
    finish: Mapped[str | None] = mapped_column(String(255), nullable=True)
    color_options: Mapped[str | None] = mapped_column(Text, nullable=True)
    certification_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    available_certifications: Mapped[str | None] = mapped_column(Text, nullable=True)
    moq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sample_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    sample_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    fob_price_range: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_us_price_range: Mapped[str | None] = mapped_column(String(255), nullable=True)
    packaging_dimensions: Mapped[str | None] = mapped_column(String(255), nullable=True)
    carton_weight: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pallet_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    container_loading_20gp: Mapped[str | None] = mapped_column(String(128), nullable=True)
    container_loading_40gp: Mapped[str | None] = mapped_column(String(128), nullable=True)
    container_loading_40hq: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ai_product_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_sales_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    partner_links: Mapped[list["ProductPartnerLink"]] = relationship(
        "ProductPartnerLink", back_populates="product", cascade="all, delete-orphan"
    )
    documents: Mapped[list["ProductDocument"]] = relationship(
        "ProductDocument", back_populates="product", cascade="all, delete-orphan"
    )


class ProductPartnerLink(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "product_partner_links"
    __table_args__ = (UniqueConstraint("product_id", "manufacturing_partner_id", name="uq_product_partner"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    manufacturing_partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_preferred: Mapped[bool] = mapped_column(default=False, nullable=False)
    capability_level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    partner_moq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lead_time_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    partner_price_range: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sample_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    certification_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship("Product", back_populates="partner_links")


class ProductDocument(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "product_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False
    )
    doc_type: Mapped[str | None] = mapped_column(String(64), nullable=True)

    product: Mapped["Product"] = relationship("Product", back_populates="documents")
