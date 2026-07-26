"""Multi-supplier candidate matching for project requests."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class ProjectRequestSupplierCandidate(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "project_request_supplier_candidates"
    __table_args__ = (
        UniqueConstraint(
            "project_request_id",
            "candidate_source_type",
            "candidate_ref_id",
            name="uq_project_request_candidate_ref",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_project_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    candidate_ref_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="SET NULL"), nullable=True
    )
    product_catalog_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_catalog.id", ondelete="SET NULL"), nullable=True
    )
    benchmark_brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("benchmark_brands.id", ondelete="SET NULL"), nullable=True
    )
    supplier_discovery_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supplier_discovery_records.id", ondelete="SET NULL"), nullable=True
    )
    candidate_role: Mapped[str] = mapped_column(String(32), nullable=False, default="alternate")
    display_name: Mapped[str] = mapped_column(String(512), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fit_dimensions_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    evidence_quality: Mapped[str | None] = mapped_column(String(32), nullable=True)
    overall_fit_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    eligible_for_formal_quote: Mapped[bool] = mapped_column(default=False, nullable=False)
    operator_decision: Mapped[str | None] = mapped_column(String(32), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_auto_recommended: Mapped[bool] = mapped_column(default=False, nullable=False)
