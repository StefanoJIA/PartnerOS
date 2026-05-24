from __future__ import annotations

import uuid

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
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class ManufacturingPartner(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "manufacturing_partners"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    legal_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    brand_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    partner_type: Mapped[str] = mapped_column(String(128), nullable=False)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    contact_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    province: Mapped[str | None] = mapped_column(String(128), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    factory_locations: Mapped[str | None] = mapped_column(Text, nullable=True)
    main_product_categories: Mapped[str | None] = mapped_column(Text, nullable=True)
    manufacturing_capabilities: Mapped[str | None] = mapped_column(Text, nullable=True)
    oem_odm_capability: Mapped[str | None] = mapped_column(Text, nullable=True)
    customization_capability: Mapped[str | None] = mapped_column(Text, nullable=True)
    moq_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
    lead_time: Mapped[str | None] = mapped_column(String(255), nullable=True)
    export_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    us_market_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    certifications: Mapped[str | None] = mapped_column(Text, nullable=True)
    testing_capability: Mapped[str | None] = mapped_column(Text, nullable=True)
    english_materials_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    price_level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quality_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    communication_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    delivery_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    project_fit_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    preferred_product_categories: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_partner_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_risk_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    partner_code: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True, index=True)
    default_incoterm: Mapped[str | None] = mapped_column(String(16), nullable=True)
    default_currency: Mapped[str | None] = mapped_column(String(3), nullable=True, default="USD")
    catalog_status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    contacts: Mapped[list["PartnerContact"]] = relationship(
        "PartnerContact", back_populates="partner", cascade="all, delete-orphan"
    )
    capabilities: Mapped[list["PartnerCapability"]] = relationship(
        "PartnerCapability", back_populates="partner", cascade="all, delete-orphan"
    )


class PartnerContact(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "partner_contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    partner: Mapped["ManufacturingPartner"] = relationship("ManufacturingPartner", back_populates="contacts")


class PartnerCapability(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "partner_capabilities"
    __table_args__ = (UniqueConstraint("partner_id", "capability_key", name="uq_partner_capability"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="CASCADE"), nullable=False
    )
    capability_key: Mapped[str] = mapped_column(String(128), nullable=False)
    level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    partner: Mapped["ManufacturingPartner"] = relationship("ManufacturingPartner", back_populates="capabilities")
