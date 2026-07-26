"""Supplier sample and engineering review records."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class SupplierSampleEvaluation(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "supplier_sample_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_discovery_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supplier_discovery_records.id", ondelete="SET NULL"), nullable=True, index=True
    )
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="SET NULL"), nullable=True
    )
    project_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_project_requests.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_catalog_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_catalog.id", ondelete="SET NULL"), nullable=True
    )
    template_key: Mapped[str] = mapped_column(String(64), nullable=False, default="generic")
    request_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    shipment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    receipt_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    test_items_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    results_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    file_refs_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    issues: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_result: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reviewer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
