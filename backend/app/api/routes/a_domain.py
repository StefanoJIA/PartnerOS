"""A domain API — Lead Intelligence workbench (D5)."""

from __future__ import annotations

from datetime import date
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
    FollowUpScheduleRequest,
    FollowUpScheduleResponse,
    FollowUpQueueResponse,
    FollowUpQueueRowOut,
    FollowUpQueueSummaryOut,
    DailyOpsSummaryResponse,
    DailyOpsSummaryCountsOut,
    DailyOpsFocusItemOut,
    DailyOpsQuickActionOut,
    DailyOpsSafetyOut,
    DailyOpsRecentOutreachOut,
    DailyOpsRecentActivityOut,
    DailyWorkSummaryResponse,
    DailyWorkSummaryCountsOut,
    DailyWorkHighlightOut,
    DailyWorkTomorrowFocusOut,
    ProductFitOut,
    ProductOpportunityBoardResponse,
    ProductOpportunityBoardRowOut,
    ProductOpportunityBoardSummaryOut,
    ProductOpportunitySafetyOut,
    PreQuoteBriefOut,
    PreQuoteBoardResponse,
    PreQuoteBoardRowOut,
    PreQuoteBoardSummaryOut,
    PreQuoteSafetyOut,
    ProductAwareDraftRequest,
    ProductAwareDraftResponse,
    ProductAwareDraftSourceContextOut,
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
from app.services.a_domain.follow_up_queue import (
    apply_follow_up_schedule,
    build_follow_up_queue_rows,
    summarize_follow_up_queue,
)
from app.services.a_domain.daily_ops_summary import (
    build_daily_ops_summary,
    build_daily_ops_summary_degraded,
)
from app.services.a_domain.daily_work_summary import (
    build_daily_work_summary,
    build_daily_work_summary_degraded,
)
from app.services.a_domain.pre_quote_board import (
    build_pre_quote_board_degraded,
    build_pre_quote_board_rows,
    build_pre_quote_brief_for_lead,
    summarize_pre_quote_board,
)
from app.services.a_domain.product_aware_draft_board import build_product_aware_draft_for_lead
from app.services.a_domain.pre_quote_prep import PRE_QUOTE_SAFETY
from app.services.a_domain.product_fit_board import (
    build_product_fit_for_lead,
    build_product_opportunity_board,
    build_product_opportunity_board_degraded,
)

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
        next_follow_up_date=raw.get("next_follow_up_date"),
        due_status=raw.get("due_status"),
        days_until_due=raw.get("days_until_due"),
        last_touchpoint_at=raw.get("last_touchpoint_at"),
        follow_up_hint=raw["follow_up_hint"],
        items=[LeadTimelineItemOut(**i) for i in raw["items"]],
        stats=LeadTimelineStatsOut(**raw["stats"]),
    )


@router.patch("/leads/{lead_id}/follow-up", response_model=FollowUpScheduleResponse)
def patch_lead_follow_up(
    lead_id: UUID,
    body: FollowUpScheduleRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FollowUpScheduleResponse:
    """Schedule manual follow-up date — no auto send or calendar (D5.7)."""
    try:
        result = apply_follow_up_schedule(
            db,
            user,
            lead_id,
            next_follow_up_date=body.next_follow_up_date,
            next_action=body.next_action,
            status_note=body.status_note,
            clear_date=body.clear_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return FollowUpScheduleResponse(**result)


@router.get("/follow-up-queue", response_model=FollowUpQueueResponse)
def get_follow_up_queue(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FollowUpQueueResponse:
    """Read-only due queue for daily follow-up (D5.7)."""
    raw_rows = build_follow_up_queue_rows(db)
    summary = summarize_follow_up_queue(raw_rows)
    rows = [FollowUpQueueRowOut(**r) for r in raw_rows]
    return FollowUpQueueResponse(
        summary=FollowUpQueueSummaryOut(**summary),
        rows=rows,
    )


@router.get("/daily-ops-summary", response_model=DailyOpsSummaryResponse)
def get_daily_ops_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DailyOpsSummaryResponse:
    """Read-only daily operations command center aggregation (D5.8)."""
    try:
        raw = build_daily_ops_summary(db)
    except Exception:
        raw = build_daily_ops_summary_degraded(
            "Daily operations unavailable. Check backend and database status."
        )
    return DailyOpsSummaryResponse(**raw)


@router.get("/leads/{lead_id}/product-fit", response_model=ProductFitOut)
def get_lead_product_fit(
    lead_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ProductFitOut:
    """Read-only product fit and project opportunity planner (D5.12)."""
    raw = build_product_fit_for_lead(db, lead_id)
    if not raw:
        raise HTTPException(status_code=404, detail="Lead not found")
    return ProductFitOut(**raw)


@router.post("/leads/{lead_id}/product-aware-draft", response_model=ProductAwareDraftResponse)
def post_lead_product_aware_draft(
    lead_id: UUID,
    body: ProductAwareDraftRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ProductAwareDraftResponse:
    """Generate product-aware discovery draft from fit + pre-quote context (D5.15)."""
    try:
        raw = build_product_aware_draft_for_lead(
            db,
            lead_id,
            channel=body.channel,
            draft_purpose=body.draft_purpose,
            tone=body.tone,
            language=body.language,
            include_questions=body.include_questions,
            include_product_brief=body.include_product_brief,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not raw:
        raise HTTPException(status_code=404, detail="Lead not found")
    ctx = raw.get("source_context") or {}
    return ProductAwareDraftResponse(
        lead_id=raw["lead_id"],
        company_name=raw["company_name"],
        channel=raw["channel"],
        draft_purpose=raw["draft_purpose"],
        tone=raw["tone"],
        language=raw["language"],
        subject=raw.get("subject"),
        body=raw.get("body"),
        linkedin_note=raw.get("linkedin_note"),
        questions=raw.get("questions") or [],
        recommended_next_action=raw["recommended_next_action"],
        suggested_follow_up_days=raw.get("suggested_follow_up_days", 5),
        source_context=ProductAwareDraftSourceContextOut(**ctx),
        safety=PreQuoteSafetyOut(**raw.get("safety", {})),
        warnings=raw.get("warnings") or [],
    )


@router.get("/leads/{lead_id}/pre-quote-brief", response_model=PreQuoteBriefOut)
def get_lead_pre_quote_brief(
    lead_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PreQuoteBriefOut:
    """Read-only pre-quote and sample prep brief (D5.14 — no quote creation)."""
    raw = build_pre_quote_brief_for_lead(db, lead_id)
    if not raw:
        raise HTTPException(status_code=404, detail="Lead not found")
    return PreQuoteBriefOut(**raw)


@router.get("/pre-quote-board", response_model=PreQuoteBoardResponse)
def get_pre_quote_board(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PreQuoteBoardResponse:
    """Read-only pre-quote board summary for all active leads (D5.14)."""
    try:
        rows_raw = build_pre_quote_board_rows(db)
        summary = summarize_pre_quote_board(rows_raw)
        return PreQuoteBoardResponse(
            summary=PreQuoteBoardSummaryOut(**summary),
            rows=[PreQuoteBoardRowOut(**r) for r in rows_raw],
            safety=PreQuoteSafetyOut(**PRE_QUOTE_SAFETY),
            warnings=[],
            degraded=False,
        )
    except Exception:
        raw = build_pre_quote_board_degraded(
            "Pre-quote board unavailable. Check backend and database status."
        )
        return PreQuoteBoardResponse(
            summary=PreQuoteBoardSummaryOut(**raw["summary"]),
            rows=[],
            safety=PreQuoteSafetyOut(**raw["safety"]),
            warnings=raw.get("warnings") or [],
            degraded=True,
        )


@router.get("/product-opportunity-board", response_model=ProductOpportunityBoardResponse)
def get_product_opportunity_board(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ProductOpportunityBoardResponse:
    """Read-only product opportunity board for all active leads (D5.12 / D5.13)."""
    try:
        raw = build_product_opportunity_board(db)
    except Exception:
        raw = build_product_opportunity_board_degraded(
            "Product opportunity board unavailable. Check backend and database status."
        )
    rows = [
        ProductOpportunityBoardRowOut(
            lead_id=r["lead_id"],
            company_name=r["company_name"],
            project_opportunity_score=r["project_opportunity_score"],
            opportunity_score=r.get("opportunity_score", r["project_opportunity_score"]),
            opportunity_level=r["opportunity_level"],
            project_type=r["project_type"],
            quote_readiness=r["quote_readiness"],
            sample_readiness=r["sample_readiness"],
            recommended_product_focus=r.get("recommended_product_focus") or [],
            missing_quote_info=r.get("missing_quote_info") or [],
            recommended_next_product_action=r.get("recommended_next_product_action"),
            sales_angle=r.get("sales_angle"),
            next_action=r.get("next_action"),
            follow_up_date=r.get("follow_up_date"),
            due_status=r.get("due_status"),
        )
        for r in raw["rows"]
    ]
    return ProductOpportunityBoardResponse(
        summary=ProductOpportunityBoardSummaryOut(**raw["summary"]),
        missing_info_summary=raw.get("missing_info_summary") or {},
        rows=rows,
        safety=ProductOpportunitySafetyOut(**raw.get("safety", {})),
        warnings=raw.get("warnings") or [],
        degraded=bool(raw.get("degraded")),
    )


@router.get("/daily-work-summary", response_model=DailyWorkSummaryResponse)
def get_daily_work_summary(
    work_date: date | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DailyWorkSummaryResponse:
    """Read-only end-of-day work summary (D5.10)."""
    target = work_date or date.today()
    try:
        raw = build_daily_work_summary(db, target_date=target)
    except Exception:
        raw = build_daily_work_summary_degraded(
            target,
            "Daily work summary unavailable. Check backend and database status.",
        )
    return DailyWorkSummaryResponse(**raw)
