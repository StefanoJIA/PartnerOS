from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class DailyQueueHandlingRecord(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "daily_queue_handling_records"
    __table_args__ = (UniqueConstraint("queue_item_id", name="uq_daily_queue_handling_queue_item_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    queue_item_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    source_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    partner_focus: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    product_focus: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    customer_or_account: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    handling_status: Mapped[str] = mapped_column(String(32), nullable=False, default="new", index=True)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    handling_events: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
