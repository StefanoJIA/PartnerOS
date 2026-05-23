"""Build quote handoff brief from DB (D5.18 read-only)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Company, Contact, Interaction, Lead, MarketIntelligenceItem
from app.services.a_domain.follow_up_queue import compute_due_status
from app.services.a_domain.follow_up_rhythm import NO_NEXT_ACTION
from app.services.a_domain.intelligence_score import IntelligenceScoreInput, compute_intelligence_score
from app.services.a_domain.pre_quote_board import build_pre_quote_brief_for_lead
from app.services.a_domain.product_fit_board import build_product_fit_for_lead
from app.services.a_domain.quote_handoff import QuoteHandoffInput, build_quote_handoff_brief


def _touchpoint_summary(db: Session, lead_id: UUID) -> str | None:
    latest = (
        db.query(Interaction)
        .filter(
            Interaction.related_object_type == "lead",
            Interaction.related_object_id == lead_id,
        )
        .order_by(Interaction.interaction_date.desc())
        .first()
    )
    if not latest:
        return None
    subject = (latest.subject or latest.interaction_type or "Touchpoint").strip()
    return f"Latest touchpoint: {subject}."


def build_quote_handoff_for_lead(db: Session, lead_id: UUID) -> dict[str, Any] | None:
    fit = build_product_fit_for_lead(db, lead_id)
    if not fit:
        return None
    brief = build_pre_quote_brief_for_lead(db, lead_id)
    if not brief:
        return None

    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.is_active.is_(True)).first()
    company = db.query(Company).filter(Company.id == lead.company_id).first() if lead else None
    contact = None
    if lead and lead.primary_contact_id:
        contact = db.query(Contact).filter(Contact.id == lead.primary_contact_id).first()

    has_contact = bool(
        contact
        and (
            (contact.email and contact.email.strip())
            or (contact.linkedin_url and contact.linkedin_url.strip())
            or (company and company.linkedin_url and company.linkedin_url.strip())
        )
    )

    na = (lead.next_action or "").strip() if lead else ""
    if na == NO_NEXT_ACTION:
        na = ""
    due_status, _ = compute_due_status(lead.next_action_due_date if lead else None)

    notes_parts = [
        company.notes if company else None,
        company.business_description if company else None,
        lead.notes if lead else None,
        lead.product_interest if lead else None,
    ]
    notes_blob = " ".join(p for p in notes_parts if p).lower()

    mi_count = 0
    if company:
        mi_count = (
            db.query(MarketIntelligenceItem)
            .filter(MarketIntelligenceItem.related_company_id == company.id)
            .count()
        )
    intel = compute_intelligence_score(
        IntelligenceScoreInput(
            has_primary_contact=contact is not None,
            market_intel_count=mi_count,
            product_interest_tags=company.product_interest_tags if company else None,
            business_description=company.business_description if company else None,
            lead_product_interest=lead.product_interest if lead else None,
            lead_priority=lead.priority if lead else None,
            company_strategic_level=company.strategic_level if company else None,
            company_notes=company.notes if company else None,
            lead_notes=lead.notes if lead else None,
            company_type=company.company_type if company else None,
            industry=company.industry if company else None,
        )
    )

    inp = QuoteHandoffInput(
        lead_id=str(lead_id),
        company_name=fit.get("company_name", ""),
        company_type=company.company_type if company else None,
        industry=company.industry if company else None,
        business_description=company.business_description if company else None,
        segments=intel.market_fit_segments,
        quote_readiness=fit.get("quote_readiness", "not_ready"),
        sample_readiness=fit.get("sample_readiness", "not_ready"),
        opportunity_score=fit.get("project_opportunity_score", 0),
        opportunity_level=fit.get("opportunity_level", "low_incomplete"),
        project_type=fit.get("project_type", "unknown"),
        recommended_product_focus=fit.get("recommended_product_focus") or [],
        missing_quote_info=fit.get("missing_quote_info") or [],
        recommended_discovery_questions=fit.get("recommended_discovery_questions") or [],
        recommended_next_action=brief.get("recommended_next_action")
        or fit.get("recommended_next_product_action", ""),
        next_action=na or None,
        follow_up_date=lead.next_action_due_date.isoformat() if lead and lead.next_action_due_date else None,
        due_status=due_status,
        has_contact_method=has_contact,
        touchpoint_summary=_touchpoint_summary(db, lead_id),
        notes_blob=notes_blob,
    )
    return build_quote_handoff_brief(inp)


def build_quote_handoff_board_rows(db: Session) -> list[dict[str, Any]]:
    leads = db.query(Lead).filter(Lead.is_active.is_(True)).order_by(Lead.created_at.desc()).all()
    rows: list[dict[str, Any]] = []
    for lead in leads:
        handoff = build_quote_handoff_for_lead(db, lead.id)
        if not handoff:
            continue
        rows.append(
            {
                "lead_id": handoff["lead_id"],
                "company_name": handoff["company_name"],
                "handoff_status": handoff["handoff_status"],
                "handoff_priority": handoff["handoff_priority"],
                "quote_readiness": handoff["quote_readiness"],
                "sample_readiness": handoff["sample_readiness"],
                "recommended_partner_route": handoff.get("recommended_partner_route") or [],
                "missing_customer_info_count": len(handoff.get("missing_customer_info") or []),
                "opportunity_score": handoff.get("opportunity_score", 0),
            }
        )
    return rows


def summarize_quote_handoff_board(rows: list[dict[str, Any]]) -> dict[str, int]:
    def _has_route(row: dict[str, Any], route: str) -> bool:
        return route in (row.get("recommended_partner_route") or [])

    return {
        "total": len(rows),
        "ready_for_manual_quote_prep": sum(
            1 for r in rows if r.get("handoff_status") == "ready_for_manual_quote_prep"
        ),
        "needs_customer_clarification": sum(
            1 for r in rows if r.get("handoff_status") == "needs_customer_clarification"
        ),
        "not_ready": sum(1 for r in rows if r.get("handoff_status") == "not_ready"),
        "high_priority": sum(1 for r in rows if r.get("handoff_priority") == "high"),
        "lifting_system_route": sum(1 for r in rows if _has_route(r, "hosun_lifting_systems")),
        "jooboo_route": sum(1 for r in rows if _has_route(r, "jooboo_education_furniture")),
        "project_supply_route": sum(1 for r in rows if _has_route(r, "project_supply")),
        "oem_odm_route": sum(1 for r in rows if _has_route(r, "oem_odm_components")),
    }


def build_quote_handoff_board(db: Session) -> dict[str, Any]:
    rows = build_quote_handoff_board_rows(db)
    return {
        "summary": summarize_quote_handoff_board(rows),
        "rows": rows,
        "warnings": [],
        "degraded": False,
    }
