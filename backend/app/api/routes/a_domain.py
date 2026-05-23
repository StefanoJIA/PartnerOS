"""A domain API — Lead Intelligence workbench (D5)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Company, Contact, Interaction, Lead, MarketIntelligenceItem, User
from app.schemas.a_domain import LeadIntelligenceWorkflowOut, OutreachDraftOut, TouchpointCreate
from app.schemas.crm import CompanyDetailOut, ContactOut, LeadOut
from app.services.activity import log_activity
from app.services.a_domain.intelligence_score import IntelligenceScoreInput, compute_intelligence_score
from app.services.a_domain.outreach_templates import generate_outreach_draft

router = APIRouter(prefix="/a-domain", tags=["a-domain-intelligence"])


@router.get("/leads/{lead_id}/workflow", response_model=LeadIntelligenceWorkflowOut)
def get_lead_intelligence_workflow(
    lead_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> LeadIntelligenceWorkflowOut:
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.is_active.is_(True)).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    company = db.query(Company).filter(Company.id == lead.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    contact = None
    if lead.primary_contact_id:
        contact = db.query(Contact).filter(Contact.id == lead.primary_contact_id).first()

    mi_q = db.query(MarketIntelligenceItem).filter(MarketIntelligenceItem.related_company_id == company.id)
    mi_count = mi_q.count()
    preview_rows = mi_q.order_by(MarketIntelligenceItem.created_at.desc()).limit(5).all()
    preview_ids = [r.id for r in preview_rows]

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

    return LeadIntelligenceWorkflowOut(
        lead=LeadOut.model_validate(lead),
        company=CompanyDetailOut.model_validate(company),
        primary_contact=ContactOut.model_validate(contact) if contact else None,
        intelligence_score=intel.score,
        score_breakdown=intel.breakdown,
        suggested_next_actions=intel.suggestions,
        market_intelligence_count=mi_count,
        market_intelligence_preview_ids=preview_ids,
        market_fit_segments=intel.market_fit_segments,
    )


@router.post("/leads/{lead_id}/touchpoint", status_code=status.HTTP_201_CREATED)
def post_lead_touchpoint(
    lead_id: UUID,
    body: TouchpointCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.is_active.is_(True)).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    intr = Interaction(
        related_object_type="lead",
        related_object_id=lead.id,
        interaction_type=body.interaction_type,
        channel=body.channel,
        subject=body.subject,
        content=body.content,
        summary=body.summary,
        direction=body.direction,
        next_action=body.interaction_next_action,
        next_action_due_date=body.interaction_next_action_due_date,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(intr)
    if body.next_action is not None:
        lead.next_action = body.next_action
    if body.next_action_due_date is not None:
        lead.next_action_due_date = body.next_action_due_date
    lead.updated_by_id = user.id

    db.commit()
    db.refresh(intr)
    db.refresh(lead)

    log_activity(
        db,
        object_type="lead",
        object_id=lead.id,
        action="intelligence_touchpoint_logged",
        actor_id=user.id,
        diff={"interaction_id": str(intr.id)},
    )
    db.commit()

    return {
        "interaction_id": str(intr.id),
        "lead_id": str(lead.id),
        "next_action": lead.next_action,
        "next_action_due_date": lead.next_action_due_date.isoformat() if lead.next_action_due_date else None,
    }


@router.get("/outreach-draft", response_model=OutreachDraftOut)
def get_outreach_draft(
    company_id: UUID = Query(...),
    channel: str = Query("linkedin_connect"),
    language: str = Query("en"),
    tone: str = Query("concise"),
    product_focus: str = Query("general"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> OutreachDraftOut:
    """Generate copy-only outreach draft from company + live workflow segments (D5.2.4)."""
    company = db.query(Company).filter(Company.id == company_id, Company.is_active.is_(True)).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    contact = None
    lead = (
        db.query(Lead)
        .filter(Lead.company_id == company_id, Lead.is_active.is_(True))
        .order_by(Lead.created_at.desc())
        .first()
    )
    segments: list[str] = []
    if lead:
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
                lead_product_interest=lead.product_interest if lead else None,
                lead_priority=lead.priority if lead else None,
                company_strategic_level=company.strategic_level,
            )
        )
        segments = intel.market_fit_segments

    contact_name = None
    if contact:
        contact_name = f"{contact.first_name} {contact.last_name}".strip()

    try:
        draft = generate_outreach_draft(
            company_name=company.company_name,
            segments=segments,
            contact_name=contact_name,
            channel=channel,
            language=language,
            tone=tone,
            product_focus=product_focus,
            notes=company.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return OutreachDraftOut(
        channel=draft.channel,
        language=draft.language,
        tone=draft.tone,
        product_focus=draft.product_focus,
        company_name=draft.company_name,
        segments=draft.segments,
        linkedin_connect_note=draft.linkedin_connect_note,
        email_subject=draft.email_subject,
        email_body=draft.email_body,
        suggested_next_action=draft.suggested_next_action,
        suggested_touchpoint_type=draft.suggested_touchpoint_type,
    )
