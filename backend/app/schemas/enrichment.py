"""Pydantic schemas for company public enrichment (D5.2)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CompanyEnrichmentSourceOut(BaseModel):
    id: UUID
    url: str
    page_title: str | None
    page_type: str
    fetch_status: str
    http_status: int | None
    fetched_at: datetime | None
    content_excerpt: str | None
    content_hash: str | None

    model_config = {"from_attributes": True}


class CompanyEnrichmentSuggestionOut(BaseModel):
    id: UUID
    enrichment_run_id: UUID
    suggestion_type: str
    suggested_value: str | None
    confidence: str | None
    reason: str | None
    evidence_source_id: UUID | None
    evidence_snippet: str | None
    matched_phrase: str | None
    review_status: str
    reviewed_at: datetime | None
    reviewed_by_id: UUID | None

    model_config = {"from_attributes": True}


class CompanyEnrichmentRunSummaryOut(BaseModel):
    id: UUID
    company_id: UUID
    status: str
    source_scope: str
    max_pages: int
    pages_fetched: int
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    pending_suggestion_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyEnrichmentRunDetailOut(BaseModel):
    run: CompanyEnrichmentRunSummaryOut
    sources: list[CompanyEnrichmentSourceOut]
    suggestions: list[CompanyEnrichmentSuggestionOut]


class EnrichmentReviewBody(BaseModel):
    review_status: Literal["pending", "accepted", "rejected", "partial"]
    edited_value: str | None = Field(None, description="Optional override text when accepting summary/tag")


class EnrichmentBatchReviewBody(BaseModel):
    suggestion_ids: list[UUID]
    review_status: Literal["accepted", "rejected"]
