"""Platform benchmark and channel intelligence records."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class PlatformBenchmarkRecord(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "platform_benchmark_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    capability_area: Mapped[str] = mapped_column(String(128), nullable=False)
    capability_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    partneros_has: Mapped[bool] = mapped_column(default=False, nullable=False)
    partneros_gap_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    build_recommended: Mapped[bool] = mapped_column(default=False, nullable=False)
    build_priority: Mapped[str] = mapped_column(String(8), nullable=False, default="P2")
    evidence_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ChannelIntelligenceMetric(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "channel_intelligence_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel_source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    period_label: Mapped[str] = mapped_column(String(32), nullable=False)
    lead_count: Mapped[int | None] = mapped_column(nullable=True)
    quote_count: Mapped[int | None] = mapped_column(nullable=True)
    win_count: Mapped[int | None] = mapped_column(nullable=True)
    lead_quality_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    quote_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    win_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    data_source: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
