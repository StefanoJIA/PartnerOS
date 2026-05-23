from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class FactoryAudit(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "factory_audits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manufacturing_partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    audit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    auditor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audit_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    production_capacity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quality_system_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    certification_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    communication_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    export_readiness_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)
    files_meta: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    ai_audit_summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class QualityDocument(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "quality_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manufacturing_partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="CASCADE"), nullable=True, index=True
    )
    file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id", ondelete="SET NULL"), nullable=True
    )
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
