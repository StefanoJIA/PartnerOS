from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class CustomerProjectRequest(Base, TimestampMixin, UserAuditMixin):
    """Partner-neutral customer project requirement / RFQ intake (not a formal order)."""

    __tablename__ = "customer_project_requests"
    __table_args__ = (
        UniqueConstraint("request_reference", name="uq_customer_project_request_reference"),
        UniqueConstraint("idempotency_key", name="uq_customer_project_request_idempotency"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_reference: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True, default="submitted")
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="normal", index=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="customer_site", index=True)

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_name_text: Mapped[str | None] = mapped_column(String(255), nullable=True)

    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturing_partners.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_catalog_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_catalog.id", ondelete="SET NULL"), nullable=True, index=True
    )
    sku: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    product_interest: Mapped[str | None] = mapped_column(String(512), nullable=True)

    quantity_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantity_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    delivery_region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expected_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    project_scenario: Mapped[str | None] = mapped_column(Text, nullable=True)

    requirements_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    attachment_refs: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    fit_summary_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    completeness_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True
    )
    rfq_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    quote_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="SET NULL"), nullable=True, index=True
    )

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    triaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    quote_ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    operator_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
