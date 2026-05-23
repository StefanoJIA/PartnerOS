"""Build product-aware draft for lead (D5.15 read-only)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Contact, Lead
from app.services.a_domain.pre_quote_board import build_pre_quote_brief_for_lead
from app.services.a_domain.product_aware_outreach import build_product_aware_draft_from_brief


def build_product_aware_draft_for_lead(
    db: Session,
    lead_id: UUID,
    *,
    channel: str,
    draft_purpose: str,
    tone: str = "concise",
    language: str = "en",
    include_questions: bool = True,
    include_product_brief: bool = True,
) -> dict[str, Any] | None:
    brief = build_pre_quote_brief_for_lead(db, lead_id)
    if not brief:
        return None
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.is_active.is_(True)).first()
    contact_name = None
    if lead and lead.primary_contact_id:
        contact = db.query(Contact).filter(Contact.id == lead.primary_contact_id).first()
        if contact:
            contact_name = f"{contact.first_name} {contact.last_name}".strip()
    return build_product_aware_draft_from_brief(
        brief,
        contact_name=contact_name,
        channel=channel,
        draft_purpose=draft_purpose,
        tone=tone,
        language=language,
        include_questions=include_questions,
        include_product_brief=include_product_brief,
    )
