import uuid
from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixins import TimestampMixin, UserAuditMixin


class ExternalExecutionAction(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = "external_execution_actions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_type: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    target_partner_system: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_focus: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    product_focus: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    dependency: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_step: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    response_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocker_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    redacted_credential_status: Mapped[str | None] = mapped_column(String(96), nullable=True)
    staging_readiness_key: Mapped[str | None] = mapped_column(String(96), nullable=True)
    pilot_readiness_key: Mapped[str | None] = mapped_column(String(96), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
