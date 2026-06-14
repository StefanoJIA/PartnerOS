from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class MarketResponseReview(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "market_response_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_focus: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    focus_category: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    product_focus: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    review_dimension: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    visibility_class: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="P2", index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="needs review", index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_safe_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
