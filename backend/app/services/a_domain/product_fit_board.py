"""Build product fit rows from DB (D5.12 / D5.13 read-only)."""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Company, Contact, Lead, MarketIntelligenceItem
from app.services.a_domain.follow_up_queue import compute_due_status
from app.services.a_domain.follow_up_rhythm import NO_NEXT_ACTION
from app.services.a_domain.intelligence_score import IntelligenceScoreInput, compute_intelligence_score
from app.services.a_domain.lead_completeness import LeadCompletenessInput, compute_lead_completeness
from app.services.a_domain.lead_completeness_board import _enrichment_label, _touch_count
from app.services.a_domain.product_fit import ProductFitInput, compute_product_fit

PRODUCT_OPPORTUNITY_SAFETY: dict[str, bool] = {
    "automatic_quote_creation": False,
    "automatic_sending_enabled": False,
    "price_promises_enabled": False,
    "inventory_promises_enabled": False,
}


def build_product_fit_for_lead(db: Session, lead_id: UUID) -> dict[str, Any] | None:
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.is_active.is_(True)).first()
    if not lead:
        return None
    company = db.query(Company).filter(Company.id == lead.company_id).first()
    if not company:
        return None

    contact = None
    if lead.primary_contact_id:
        contact = db.query(Contact).filter(Contact.id == lead.primary_contact_id).first()

    mi_count = (
        db.query(MarketIntelligenceItem)
        .filter(MarketIntelligenceItem.related_company_id == company.id)
        .count()
    )
    intel = compute_intelligence_score(
        IntelligenceScoreInput(
            has_primary_contact=contact is not None,
            market_intel_count=mi_count,
            product_interest_tags=company.product_interest_tags,
            business_description=company.business_description,
            lead_product_interest=lead.product_interest,
            lead_priority=lead.priority,
            company_strategic_level=company.strategic_level,
        )
    )

    contact_name = None
    if contact:
        contact_name = f"{contact.first_name} {contact.last_name}".strip()

    na = (lead.next_action or "").strip() or NO_NEXT_ACTION
    enrich = _enrichment_label(db, company.id)
    touches = _touch_count(db, lead.id)

    comp_inp = LeadCompletenessInput(
        company_name=company.company_name,
        company_type=company.company_type,
        industry=company.industry,
        notes=company.notes,
        business_description=company.business_description,
        website=company.website,
        contact_name=contact_name,
        contact_title=contact.title if contact else None,
        contact_email=contact.email if contact else None,
        contact_linkedin_url=contact.linkedin_url if contact else None,
        company_linkedin_url=company.linkedin_url,
        contact_phone=contact.phone if contact else None,
        segments=intel.market_fit_segments,
        intelligence_score=intel.score,
        suggested_next_actions=intel.suggestions,
        next_action=na,
        enrichment_status=enrich,
        touch_count=touches,
    )
    comp = compute_lead_completeness(comp_inp)

    fit_inp = ProductFitInput(
        lead_id=str(lead.id),
        company_name=company.company_name,
        company_type=company.company_type,
        industry=company.industry,
        notes=company.notes,
        business_description=company.business_description,
        product_interest_tags=company.product_interest_tags,
        lead_product_interest=lead.product_interest,
        lead_notes=lead.notes,
        expected_timeline=lead.expected_timeline,
        estimated_value=str(lead.estimated_value) if lead.estimated_value is not None else None,
        contact_name=contact_name,
        contact_title=contact.title if contact else None,
        contact_email=contact.email if contact else None,
        contact_linkedin_url=contact.linkedin_url if contact else None,
        company_linkedin_url=company.linkedin_url,
        contact_phone=contact.phone if contact else None,
        segments=intel.market_fit_segments,
        next_action=na if na != NO_NEXT_ACTION else None,
        follow_up_date_set=lead.next_action_due_date is not None,
        completeness_score=comp["score"],
        enrichment_status=enrich,
        touch_count=touches,
    )
    return compute_product_fit(fit_inp)


def build_product_fit_rows(db: Session) -> list[dict[str, Any]]:
    return build_product_opportunity_board_rows(db)


def _lead_operational_fields(lead: Lead, today: date | None = None) -> dict[str, Any]:
    due_status, _ = compute_due_status(lead.next_action_due_date, today)
    na = (lead.next_action or "").strip()
    if na == NO_NEXT_ACTION:
        na = ""
    return {
        "next_action": na or None,
        "follow_up_date": lead.next_action_due_date.isoformat() if lead.next_action_due_date else None,
        "due_status": due_status,
    }


def build_product_opportunity_board_rows(db: Session, today: date | None = None) -> list[dict[str, Any]]:
    ref = today or date.today()
    leads = db.query(Lead).filter(Lead.is_active.is_(True)).order_by(Lead.created_at.desc()).all()
    rows: list[dict[str, Any]] = []
    for lead in leads:
        fit = build_product_fit_for_lead(db, lead.id)
        if not fit:
            continue
        ops = _lead_operational_fields(lead, ref)
        rows.append(
            {
                **fit,
                "opportunity_score": fit["project_opportunity_score"],
                **ops,
            }
        )
    return rows


def summarize_missing_info(rows: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        for key in row.get("missing_quote_info") or []:
            counter[key] += 1
    return dict(counter.most_common())


def summarize_product_opportunity_board(rows: list[dict[str, Any]]) -> dict[str, int]:
    almost = sum(1 for r in rows if r.get("quote_readiness") == "almost_ready")
    return {
        "total": len(rows),
        "high_opportunity": sum(1 for r in rows if r.get("opportunity_level") == "high_opportunity"),
        "promising": sum(1 for r in rows if r.get("opportunity_level") == "promising"),
        "quote_ready": sum(1 for r in rows if r.get("quote_readiness") == "ready"),
        "almost_ready": almost,
        "almost_quote_ready": almost,
        "sample_ready": sum(1 for r in rows if r.get("sample_readiness") == "ready"),
        "needs_specs": sum(1 for r in rows if r.get("sample_readiness") == "needs_specs"),
        "lifting_system_fit": sum(
            1 for r in rows if "hosun_lifting_systems" in r.get("recommended_product_focus", [])
        ),
        "project_supply_fit": sum(
            1 for r in rows if "project_supply" in r.get("recommended_product_focus", [])
        ),
        "education_fit": sum(
            1 for r in rows if "jooboo_education_furniture" in r.get("recommended_product_focus", [])
        ),
        "medical_fit": sum(
            1 for r in rows if "medical_workspace" in r.get("recommended_product_focus", [])
        ),
        "oem_odm_fit": sum(
            1 for r in rows if "oem_odm_components" in r.get("recommended_product_focus", [])
        ),
        "oem_odm_potential": sum(
            1 for r in rows if "oem_odm_components" in r.get("recommended_product_focus", [])
        ),
    }


def build_product_opportunity_board(db: Session) -> dict[str, Any]:
    rows = build_product_opportunity_board_rows(db)
    return {
        "summary": summarize_product_opportunity_board(rows),
        "missing_info_summary": summarize_missing_info(rows),
        "rows": rows,
        "safety": dict(PRODUCT_OPPORTUNITY_SAFETY),
        "warnings": [],
        "degraded": False,
    }


def build_product_opportunity_board_degraded(warning: str) -> dict[str, Any]:
    empty_summary = summarize_product_opportunity_board([])
    return {
        "summary": empty_summary,
        "missing_info_summary": {},
        "rows": [],
        "safety": dict(PRODUCT_OPPORTUNITY_SAFETY),
        "warnings": [warning],
        "degraded": True,
    }
