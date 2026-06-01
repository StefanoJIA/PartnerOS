"""Schemas for D7.8 feedback ticket operations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FeedbackTicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_number: str
    source: str
    order_id: UUID | None = None
    company_id: UUID | None = None
    feedback_type: str
    subject: str
    message: str
    status: str
    priority: str
    internal_owner: str | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    response_summary: str | None = None
    created_at: datetime
    updated_at: datetime
    operation: dict[str, bool]
    safety: dict[str, bool]


class FeedbackTicketUpdateIn(BaseModel):
    status: str | None = None
    priority: str | None = None
    internal_owner: str | None = None
    response_summary: str | None = None
