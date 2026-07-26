"""Supplier discovery and qualification workbench records."""

from __future__ import annotations

import uuid

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class SupplierDiscoveryRecord(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "supplier_discovery_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    brand_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    categories: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    capabilities: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    certifications: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    moq_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
    lead_time_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    export_markets: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    doc_completeness_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contact_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    data_source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    factory_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    contacts_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    pricing_doc_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data_rights_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_review_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    usage_restrictions: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    dedup_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="discovered", index=True)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="SET NULL"), nullable=True, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    qualification_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
