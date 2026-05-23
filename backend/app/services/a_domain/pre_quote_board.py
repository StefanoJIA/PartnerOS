"""Build pre-quote brief rows from DB (D5.14 read-only)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Company, Contact, Lead
from app.services.a_domain.follow_up_rhythm import NO_NEXT_ACTION
from app.services.a_domain.pre_quote_prep import PRE_QUOTE_SAFETY, build_pre_quote_brief_from_product_fit
from app.services.a_domain.product_fit_board import build_product_fit_for_lead


def build_pre_quote_brief_for_lead(db: Session, lead_id: UUID) -> dict[str, Any] | None:
    fit = build_product_fit_for_lead(db, lead_id)
    if not fit:
        return None
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.is_active.is_(True)).first()
    company = db.query(Company).filter(Company.id == lead.company_id).first() if lead else None
    contact = None
    if lead and lead.primary_contact_id:
        contact = db.query(Contact).filter(Contact.id == lead.primary_contact_id).first()
    contact_name = None
    if contact:
        contact_name = f"{contact.first_name} {contact.last_name}".strip()
    na = (lead.next_action or "").strip() if lead else ""
    if na == NO_NEXT_ACTION:
        na = ""
    return build_pre_quote_brief_from_product_fit(
        fit,
        company_type=company.company_type if company else None,
        business_description=company.business_description if company else None,
        contact_name=contact_name,
        contact_email=contact.email if contact else None,
        next_action=na or None,
        follow_up_date=lead.next_action_due_date.isoformat() if lead and lead.next_action_due_date else None,
    )


def build_pre_quote_board_rows(db: Session) -> list[dict[str, Any]]:
    leads = db.query(Lead).filter(Lead.is_active.is_(True)).order_by(Lead.created_at.desc()).all()
    rows: list[dict[str, Any]] = []
    for lead in leads:
        brief = build_pre_quote_brief_for_lead(db, lead.id)
        if not brief:
            continue
        rows.append(
            {
                "lead_id": brief["lead_id"],
                "company_name": brief["company_name"],
                "quote_readiness": brief["quote_readiness"],
                "sample_readiness": brief["sample_readiness"],
                "missing_quote_info_count": len(brief.get("missing_quote_info") or []),
                "recommended_next_action": brief.get("recommended_next_action"),
                "recommended_product_focus": brief.get("recommended_product_focus") or [],
                "opportunity_score": brief.get("opportunity_score", 0),
            }
        )
    return rows


def summarize_pre_quote_board(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total": len(rows),
        "quote_prep_ready": sum(1 for r in rows if r.get("quote_readiness") == "ready"),
        "sample_discussion_ready": sum(1 for r in rows if r.get("sample_readiness") == "ready"),
        "needs_specs_before_quote": sum(
            1
            for r in rows
            if r.get("quote_readiness") in ("almost_ready", "not_ready")
            and r.get("sample_readiness") == "needs_specs"
        ),
        "almost_ready": sum(1 for r in rows if r.get("quote_readiness") == "almost_ready"),
    }


def build_pre_quote_board_degraded(warning: str) -> dict[str, Any]:
    return {
        "summary": summarize_pre_quote_board([]),
        "rows": [],
        "safety": dict(PRE_QUOTE_SAFETY),
        "warnings": [warning],
        "degraded": True,
    }
