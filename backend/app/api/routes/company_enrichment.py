"""Company public-source enrichment API (D5.2)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Company, User
from app.models.enrichment import (
    ENRICHMENT_STATUS_PENDING,
    REVIEW_ACCEPTED,
    REVIEW_PENDING,
    REVIEW_REJECTED,
    CompanyEnrichmentRun,
    CompanyEnrichmentSource,
    CompanyEnrichmentSuggestion,
)
from app.schemas.enrichment import (
    CompanyEnrichmentRunDetailOut,
    CompanyEnrichmentRunSummaryOut,
    CompanyEnrichmentSourceOut,
    CompanyEnrichmentSuggestionOut,
    EnrichmentBatchReviewBody,
    EnrichmentReviewBody,
)
from app.schemas.pagination import PaginatedResponse
from app.services.activity import log_activity
from app.services.enrichment.apply_suggestion import apply_enrichment_suggestion
from app.services.enrichment.runner import execute_enrichment_run

router = APIRouter(tags=["company-enrichment"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _pending_count(db: Session, run_id: UUID) -> int:
    return (
        db.query(CompanyEnrichmentSuggestion)
        .filter(
            CompanyEnrichmentSuggestion.enrichment_run_id == run_id,
            CompanyEnrichmentSuggestion.review_status == REVIEW_PENDING,
        )
        .count()
    )


def _run_summary(db: Session, run: CompanyEnrichmentRun) -> CompanyEnrichmentRunSummaryOut:
    base = CompanyEnrichmentRunSummaryOut.model_validate(run)
    return base.model_copy(update={"pending_suggestion_count": _pending_count(db, run.id)})


@router.post(
    "/companies/{company_id}/enrichment/runs",
    response_model=CompanyEnrichmentRunSummaryOut,
    status_code=status.HTTP_201_CREATED,
)
def create_enrichment_run(
    company_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CompanyEnrichmentRunSummaryOut:
    settings = get_settings()
    if not settings.PUBLIC_ENRICHMENT_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="public enrichment disabled")

    company = db.query(Company).filter(Company.id == company_id, Company.is_active.is_(True)).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if not company.website or not str(company.website).strip():
        raise HTTPException(status_code=400, detail="Company has no website to enrich")

    run = CompanyEnrichmentRun(
        company_id=company_id,
        status=ENRICHMENT_STATUS_PENDING,
        source_scope="website_mvp_v1",
        max_pages=settings.ENRICHMENT_MAX_PAGES,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    log_activity(
        db,
        object_type="company",
        object_id=company_id,
        action="enrichment_run_started",
        actor_id=user.id,
        diff={"run_id": str(run.id)},
    )
    db.commit()

    background_tasks.add_task(execute_enrichment_run, run.id)
    return _run_summary(db, run)


@router.get("/companies/{company_id}/enrichment/runs", response_model=PaginatedResponse[CompanyEnrichmentRunSummaryOut])
def list_enrichment_runs(
    company_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[CompanyEnrichmentRunSummaryOut]:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    q = db.query(CompanyEnrichmentRun).filter(CompanyEnrichmentRun.company_id == company_id)
    total = q.count()
    rows = q.order_by(CompanyEnrichmentRun.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    items = [_run_summary(db, r) for r in rows]
    return PaginatedResponse(items=items, total=total, page=page, limit=limit)


@router.get("/companies/enrichment/runs/{run_id}", response_model=CompanyEnrichmentRunDetailOut)
def get_enrichment_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CompanyEnrichmentRunDetailOut:
    run = db.get(CompanyEnrichmentRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    sources = (
        db.query(CompanyEnrichmentSource)
        .filter(CompanyEnrichmentSource.enrichment_run_id == run_id)
        .order_by(CompanyEnrichmentSource.created_at.asc())
        .all()
    )
    suggestions = (
        db.query(CompanyEnrichmentSuggestion)
        .filter(CompanyEnrichmentSuggestion.enrichment_run_id == run_id)
        .order_by(CompanyEnrichmentSuggestion.created_at.asc())
        .all()
    )
    summary = _run_summary(db, run)
    return CompanyEnrichmentRunDetailOut(
        run=summary,
        sources=[CompanyEnrichmentSourceOut.model_validate(s) for s in sources],
        suggestions=[CompanyEnrichmentSuggestionOut.model_validate(s) for s in suggestions],
    )


@router.post("/companies/enrichment/suggestions/{suggestion_id}/review", response_model=CompanyEnrichmentSuggestionOut)
def review_suggestion(
    suggestion_id: UUID,
    body: EnrichmentReviewBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CompanyEnrichmentSuggestionOut:
    sug = db.get(CompanyEnrichmentSuggestion, suggestion_id)
    if not sug:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    if body.review_status in (REVIEW_ACCEPTED, "partial") and body.edited_value is not None:
        if sug.suggestion_type in ("business_summary", "tag"):
            sug.suggested_value = body.edited_value.strip()

    if body.review_status == "partial":
        sug.review_status = REVIEW_ACCEPTED
    else:
        sug.review_status = body.review_status

    sug.reviewed_by_id = user.id
    sug.reviewed_at = _utcnow()
    db.add(sug)

    run = db.get(CompanyEnrichmentRun, sug.enrichment_run_id)
    if run:
        log_activity(
            db,
            object_type="company",
            object_id=run.company_id,
            action="enrichment_suggestion_reviewed",
            actor_id=user.id,
            diff={"suggestion_id": str(sug.id), "status": sug.review_status},
        )
    db.commit()
    db.refresh(sug)
    return CompanyEnrichmentSuggestionOut.model_validate(sug)


@router.post("/companies/enrichment/runs/{run_id}/suggestions/batch-review")
def batch_review_suggestions(
    run_id: UUID,
    body: EnrichmentBatchReviewBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    run = db.get(CompanyEnrichmentRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    status_val = body.review_status
    if status_val not in (REVIEW_ACCEPTED, REVIEW_REJECTED):
        raise HTTPException(status_code=400, detail="batch only supports accepted/rejected")

    now = _utcnow()
    for sid in body.suggestion_ids:
        sug = (
            db.query(CompanyEnrichmentSuggestion)
            .filter(
                CompanyEnrichmentSuggestion.id == sid,
                CompanyEnrichmentSuggestion.enrichment_run_id == run_id,
            )
            .first()
        )
        if sug:
            sug.review_status = status_val
            sug.reviewed_by_id = user.id
            sug.reviewed_at = now
    log_activity(
        db,
        object_type="company",
        object_id=run.company_id,
        action="enrichment_suggestion_batch_reviewed",
        actor_id=user.id,
        diff={"run_id": str(run_id), "count": len(body.suggestion_ids), "status": status_val},
    )
    db.commit()
    return {"ok": True}


@router.post(
    "/companies/{company_id}/enrichment/suggestions/{suggestion_id}/apply",
    response_model=CompanyEnrichmentSuggestionOut,
)
def apply_suggestion_route(
    company_id: UUID,
    suggestion_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CompanyEnrichmentSuggestionOut:
    try:
        sug = apply_enrichment_suggestion(db, company_id, suggestion_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    db.commit()
    db.refresh(sug)
    return CompanyEnrichmentSuggestionOut.model_validate(sug)
