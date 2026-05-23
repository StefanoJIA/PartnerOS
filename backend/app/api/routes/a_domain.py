"""A domain API — Lead Intelligence workbench (D5)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Company, Contact, Interaction, Lead, MarketIntelligenceItem, User
from app.schemas.a_domain import (
    LeadIntakeApplyRequest,
    LeadIntakeApplyResponse,
    LeadIntakePreviewRequest,
    LeadIntakePreviewResponse,
    LeadIntakePreviewRowOut,
    LeadIntakePreviewSummaryOut,
    LeadCompletenessResponse,
    LeadCompletenessRowOut,
    LeadCompletenessSummaryOut,
    ContactResearchRequest,
    ContactResearchResponse,
    LeadTimelineOut,
    LeadTimelineItemOut,
    LeadTimelineStatsOut,
    LeadIntelligenceWorkflowOut,
    OutreachDraftOut,
    TouchpointCreate,
)
from app.schemas.crm import CompanyDetailOut, ContactOut, LeadOut
from app.services.activity import log_activity
from app.services.a_domain.intelligence_score import IntelligenceScoreInput, compute_intelligence_score
from app.services.a_domain.outreach_templates import generate_outreach_draft
from app.services.a_domain.lead_import_service import (
    apply_lead_csv_text,
    get_template_csv,
    preview_lead_csv_text,
)
from app.services.a_domain.lead_completeness_board import (
    build_lead_completeness_rows,
    summarize_completeness,
)
from app.services.a_domain.contact_research_service import apply_contact_research
from app.services.a_domain.lead_timeline import build_lead_timeline

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


def _preview_to_response(result) -> LeadIntakePreviewResponse:
    return LeadIntakePreviewResponse(
        rows=[
            LeadIntakePreviewRowOut(
                row_number=r.row_number,
                company_name=r.company_name,
                contact_name=r.contact_name,
                website=r.website,
                company_type=r.company_type,
                source=r.source,
                likely_segments=r.likely_segments,
                priority_hint=r.priority_hint,
                missing_fields=r.missing_fields,
                duplicate_status=r.duplicate_status,
                recommended_next_action=r.recommended_next_action,
                status=r.status,
                warnings=r.warnings,
            )
            for r in result.rows
        ],
        summary=LeadIntakePreviewSummaryOut(
            total=result.summary.total,
            ok=result.summary.ok,
            warnings=result.summary.warnings,
            errors=result.summary.errors,
            duplicates=result.summary.duplicates,
            ready_to_import=result.summary.ready_to_import,
        ),
        header_warnings=result.header_warnings,
    )


@router.get("/lead-intake/template", response_class=PlainTextResponse)
def get_lead_intake_template(_: User = Depends(get_current_user)) -> PlainTextResponse:
    """Download CSV template (fictional examples only)."""
    return PlainTextResponse(
        content=get_template_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="lead_import_template.csv"'},
    )


@router.post("/lead-intake/preview", response_model=LeadIntakePreviewResponse)
def post_lead_intake_preview(
    body: LeadIntakePreviewRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> LeadIntakePreviewResponse:
    """Preview CSV rows — read-only, no DB writes (D5.3)."""
    try:
        result = preview_lead_csv_text(db, body.csv_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _preview_to_response(result)


@router.post("/lead-intake/apply", response_model=LeadIntakeApplyResponse)
def post_lead_intake_apply(
    body: LeadIntakeApplyRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LeadIntakeApplyResponse:
    """Confirm import — human-reviewed only, no automatic outreach (D5.3)."""
    if not body.confirm:
        raise HTTPException(status_code=400, detail="confirm must be true to import leads")
    try:
        result = apply_lead_csv_text(db, user, body.csv_text, confirm=body.confirm)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return LeadIntakeApplyResponse(
        created_companies=result.created_companies,
        skipped_duplicates=result.skipped_duplicates,
        created_contacts=result.created_contacts,
        linked_leads=result.linked_leads,
        warnings=result.warnings,
    )


@router.get("/lead-completeness", response_model=LeadCompletenessResponse)
def get_lead_completeness(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> LeadCompletenessResponse:
    """Read-only completeness board for all active leads (D5.4)."""
    raw_rows = build_lead_completeness_rows(db)
    summary = summarize_completeness(raw_rows)
    rows = [_completeness_row_out(r) for r in raw_rows]
    return LeadCompletenessResponse(
        rows=rows,
        summary=LeadCompletenessSummaryOut(**summary),
    )


def _completeness_row_out(row: dict) -> LeadCompletenessRowOut:
    return LeadCompletenessRowOut(
        lead_id=row["lead_id"],
        company_name=row["company_name"],
        lead_name=row["lead_name"],
        score=row["score"],
        status=row["status"],
        status_label=row["status_label"],
        missing_fields=row["missing_fields"],
        recommended_research_action=row["recommended_research_action"],
        segment=row.get("segment"),
        segments=row.get("segments") or [],
        next_action=row.get("next_action"),
        last_touchpoint=row.get("last_touchpoint"),
    )


@router.post("/leads/{lead_id}/contact-research", response_model=ContactResearchResponse)
def post_lead_contact_research(
    lead_id: UUID,
    body: ContactResearchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContactResearchResponse:
    """Manual contact research update — no auto search or send (D5.5)."""
    try:
        result = apply_contact_research(
            db,
            user,
            lead_id,
            company_data=body.company.model_dump() if body.company else None,
            contact_data=body.contact.model_dump() if body.contact else None,
            lead_data=body.lead.model_dump() if body.lead else None,
            touchpoint_note=body.touchpoint_note,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    comp = result["completeness"]
    if not comp:
        raise HTTPException(status_code=404, detail="Lead completeness row not found")
    return ContactResearchResponse(
        lead_id=result["lead_id"],
        interaction_id=result["interaction_id"],
        completeness=_completeness_row_out(comp),
    )


@router.get("/leads/{lead_id}/timeline", response_model=LeadTimelineOut)
def get_lead_timeline(
    lead_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> LeadTimelineOut:
    """Read-only outreach history timeline (D5.6 — manual actions only)."""
    try:
        raw = build_lead_timeline(db, lead_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return LeadTimelineOut(
        lead_id=raw["lead_id"],
        company_name=raw["company_name"],
        next_action=raw.get("next_action"),
        last_touchpoint_at=raw.get("last_touchpoint_at"),
        follow_up_hint=raw["follow_up_hint"],
        items=[LeadTimelineItemOut(**i) for i in raw["items"]],
        stats=LeadTimelineStatsOut(**raw["stats"]),
    )
