"""D5.2 — Public-source enrichment (company website evidence, human-reviewed suggestions)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin

# Run lifecycle
ENRICHMENT_STATUS_PENDING = "pending"
ENRICHMENT_STATUS_RUNNING = "running"
ENRICHMENT_STATUS_COMPLETED = "completed"
ENRICHMENT_STATUS_FAILED = "failed"

# Source row fetch outcome
FETCH_OK = "ok"
FETCH_TIMEOUT = "timeout"
FETCH_HTTP_ERROR = "http_error"
FETCH_BLOCKED = "blocked"
FETCH_DUPLICATE = "duplicate"
FETCH_INVALID_URL = "invalid_url"

# Suggestion types
SUGGESTION_BUSINESS_SUMMARY = "business_summary"
SUGGESTION_TAG = "tag"
SUGGESTION_MARKET_SEGMENT = "market_segment"
SUGGESTION_SCORE_HINT = "score_hint"

# Review
REVIEW_PENDING = "pending"
REVIEW_ACCEPTED = "accepted"
REVIEW_REJECTED = "rejected"
REVIEW_PARTIAL = "partial"


class CompanyEnrichmentRun(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "company_enrichment_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ENRICHMENT_STATUS_PENDING, index=True)
    source_scope: Mapped[str] = mapped_column(String(64), nullable=False, default="website_mvp_v1")
    max_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    pages_fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    sources: Mapped[list["CompanyEnrichmentSource"]] = relationship(
        "CompanyEnrichmentSource",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="CompanyEnrichmentSource.created_at",
    )
    suggestions: Mapped[list["CompanyEnrichmentSuggestion"]] = relationship(
        "CompanyEnrichmentSuggestion",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="CompanyEnrichmentSuggestion.created_at",
    )


class CompanyEnrichmentSource(Base, TimestampMixin):
    __tablename__ = "company_enrichment_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrichment_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("company_enrichment_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    page_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    page_type: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fetch_status: Mapped[str] = mapped_column(String(32), nullable=False, default=FETCH_OK)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_excerpt: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    run: Mapped["CompanyEnrichmentRun"] = relationship("CompanyEnrichmentRun", back_populates="sources")


class CompanyEnrichmentSuggestion(Base, TimestampMixin):
    __tablename__ = "company_enrichment_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrichment_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("company_enrichment_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    suggestion_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    suggested_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("company_enrichment_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    evidence_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    matched_phrase: Mapped[str | None] = mapped_column(String(512), nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=REVIEW_PENDING, index=True
    )
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    run: Mapped["CompanyEnrichmentRun"] = relationship("CompanyEnrichmentRun", back_populates="suggestions")
