"""Build lead completeness rows from DB (D5.4 read-only)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Company, Contact, Interaction, Lead, MarketIntelligenceItem
from app.models.enrichment import CompanyEnrichmentRun
from app.services.a_domain.intelligence_score import IntelligenceScoreInput, compute_intelligence_score
from app.services.a_domain.lead_completeness import LeadCompletenessInput, compute_lead_completeness
from app.services.a_domain.follow_up_rhythm import NO_NEXT_ACTION


def _enrichment_label(db: Session, company_id: UUID) -> str:
    run = (
        db.query(CompanyEnrichmentRun)
        .filter(CompanyEnrichmentRun.company_id == company_id)
        .order_by(CompanyEnrichmentRun.created_at.desc())
        .first()
    )
    if not run:
        return "No runs"
    return run.status or "—"


def _touch_count(db: Session, lead_id: UUID) -> int:
    return (
        db.query(Interaction)
        .filter(
            Interaction.related_object_type == "lead",
            Interaction.related_object_id == lead_id,
        )
        .count()
    )


def _last_touch_summary(db: Session, lead_id: UUID) -> str:
    row = (
        db.query(Interaction)
        .filter(
            Interaction.related_object_type == "lead",
            Interaction.related_object_id == lead_id,
        )
        .order_by(Interaction.interaction_date.desc())
        .first()
    )
    if not row:
        return "—"
    return row.summary or row.subject or row.interaction_type or "—"


def build_lead_completeness_rows(db: Session) -> list[dict[str, Any]]:
    leads = db.query(Lead).filter(Lead.is_active.is_(True)).order_by(Lead.created_at.desc()).all()
    rows: list[dict[str, Any]] = []

    for lead in leads:
        company = db.query(Company).filter(Company.id == lead.company_id).first()
        if not company:
            continue
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

        inp = LeadCompletenessInput(
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
        comp = compute_lead_completeness(inp)
        rows.append(
            {
                "lead_id": str(lead.id),
                "company_name": company.company_name,
                "lead_name": lead.lead_name,
                "segment": intel.market_fit_segments[0] if intel.market_fit_segments else None,
                "segments": intel.market_fit_segments,
                "next_action": na if na != NO_NEXT_ACTION else None,
                "last_touchpoint": _last_touch_summary(db, lead.id),
                **comp,
            }
        )

    return rows


def summarize_completeness(rows: list[dict[str, Any]]) -> dict[str, int]:
    total = len(rows)
    complete = sum(1 for r in rows if r.get("status") == "complete")
    ready = sum(1 for r in rows if r.get("status") == "ready_for_outreach")
    research = sum(1 for r in rows if r.get("status") == "needs_contact_research")
    incomplete = sum(1 for r in rows if r.get("status") == "incomplete")
    missing_website = sum(1 for r in rows if "website" in r.get("missing_fields", []))
    missing_contact = sum(
        1 for r in rows if "contact_email_or_linkedin" in r.get("missing_fields", [])
    )
    return {
        "total": total,
        "complete": complete,
        "ready_for_outreach": ready,
        "needs_contact_research": research,
        "incomplete": incomplete,
        "missing_website": missing_website,
        "missing_contact_method": missing_contact,
    }
