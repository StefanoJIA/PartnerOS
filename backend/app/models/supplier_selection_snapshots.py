"""Frozen supplier selection snapshots for project requests."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class SupplierSelectionSnapshot(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "supplier_selection_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_project_requests.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    selected_candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_request_supplier_candidates.id", ondelete="SET NULL"), nullable=True
    )
    snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    selected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    selected_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
