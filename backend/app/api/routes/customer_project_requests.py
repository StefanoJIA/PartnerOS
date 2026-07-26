from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Company, CustomerProjectRequest, ManufacturingPartner, User
from app.models.enums import CustomerProjectRequestStatus
from app.schemas.customer_project_request_domain import (
    CustomerProjectRequestCreate,
    CustomerProjectRequestDetailOut,
    CustomerProjectRequestListItemOut,
    CustomerProjectRequestUpdate,
    MarketSignalDraftOut,
    QuoteInputContractGenerateOut,
)
from app.schemas.pagination import PaginatedResponse
from app.services.customer_project_requests.market_signal_service import (
    build_market_signal_draft,
    promote_market_signal_to_review,
)
from app.schemas.multibrand_export import CandidateDecisionBody, ProjectRequestCandidateOut
from app.models.project_request_candidates import ProjectRequestSupplierCandidate
from app.services.customer_project_requests.workspace_service import (
    assign_partner_and_sku,
    build_detail_payload,
    build_quote_input_contract_for_request,
    create_admin_request,
    update_request_status,
)
from app.services.customer_project_requests.multi_supplier_fit_service import (
    record_candidate_decision,
    refresh_supplier_candidates,
)

router = APIRouter(prefix="/project-requests", tags=["project-requests"])


@router.get("", response_model=PaginatedResponse[CustomerProjectRequestListItemOut])
def list_project_requests(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    priority: str | None = None,
    partner_id: UUID | None = None,
    owner_user_id: UUID | None = None,
    q: str | None = None,
) -> PaginatedResponse[CustomerProjectRequestListItemOut]:
    query = db.query(CustomerProjectRequest)
    if status:
        query = query.filter(CustomerProjectRequest.status == status)
    if priority:
        query = query.filter(CustomerProjectRequest.priority == priority)
    if partner_id:
        query = query.filter(CustomerProjectRequest.partner_id == partner_id)
    if owner_user_id:
        query = query.filter(CustomerProjectRequest.owner_user_id == owner_user_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                CustomerProjectRequest.request_reference.ilike(like),
                CustomerProjectRequest.customer_name.ilike(like),
                CustomerProjectRequest.company_name_text.ilike(like),
                CustomerProjectRequest.sku.ilike(like),
                CustomerProjectRequest.product_interest.ilike(like),
            )
        )
    total = query.count()
    rows = (
        query.order_by(CustomerProjectRequest.submitted_at.desc().nullslast(), CustomerProjectRequest.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    items: list[CustomerProjectRequestListItemOut] = []
    for row in rows:
        payload = build_detail_payload(db, row)
        items.append(CustomerProjectRequestListItemOut.model_validate(payload))
    return PaginatedResponse(items=items, total=total, page=page, limit=limit)


@router.post("", response_model=CustomerProjectRequestDetailOut, status_code=status.HTTP_201_CREATED)
def create_project_request(
    body: CustomerProjectRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CustomerProjectRequestDetailOut:
    row = create_admin_request(db, body, actor_id=user.id)
    return CustomerProjectRequestDetailOut.model_validate(build_detail_payload(db, row))


@router.get("/{request_id}", response_model=CustomerProjectRequestDetailOut)
def get_project_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CustomerProjectRequestDetailOut:
    row = db.query(CustomerProjectRequest).filter(CustomerProjectRequest.id == request_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Project request not found")
    return CustomerProjectRequestDetailOut.model_validate(build_detail_payload(db, row))


@router.patch("/{request_id}", response_model=CustomerProjectRequestDetailOut)
def patch_project_request(
    request_id: UUID,
    body: CustomerProjectRequestUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CustomerProjectRequestDetailOut:
    row = db.query(CustomerProjectRequest).filter(CustomerProjectRequest.id == request_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Project request not found")
    if body.status is not None:
        row = update_request_status(db, row, status=body.status, actor_id=user.id, operator_notes=body.operator_notes)
    else:
        if body.priority is not None:
            row.priority = body.priority.value
        if body.owner_user_id is not None:
            row.owner_user_id = body.owner_user_id
        if body.operator_notes is not None:
            row.operator_notes = body.operator_notes
        if body.lead_id is not None:
            row.lead_id = body.lead_id
        if body.rfq_id is not None:
            row.rfq_id = body.rfq_id
        if body.quote_id is not None:
            row.quote_id = body.quote_id
        row.updated_by_id = user.id
        db.commit()
        db.refresh(row)
    if body.partner_id is not None or body.product_catalog_id is not None or body.sku is not None:
        row = assign_partner_and_sku(
            db,
            row,
            partner_id=body.partner_id if body.partner_id is not None else row.partner_id,
            product_catalog_id=body.product_catalog_id if body.product_catalog_id is not None else row.product_catalog_id,
            sku=body.sku if body.sku is not None else row.sku,
            actor_id=user.id,
        )
    return CustomerProjectRequestDetailOut.model_validate(build_detail_payload(db, row))


@router.post("/{request_id}/quote-input-contract", response_model=QuoteInputContractGenerateOut)
def generate_quote_input_contract(
    request_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QuoteInputContractGenerateOut:
    row = db.query(CustomerProjectRequest).filter(CustomerProjectRequest.id == request_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Project request not found")
    contract = build_quote_input_contract_for_request(db, row)
    return QuoteInputContractGenerateOut(
        request_id=row.id,
        quote_input_contract=contract,
        summary_text=contract.get("summary_text", ""),
    )


@router.get("/{request_id}/market-signal-draft", response_model=MarketSignalDraftOut)
def get_market_signal_draft(
    request_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MarketSignalDraftOut:
    row = db.query(CustomerProjectRequest).filter(CustomerProjectRequest.id == request_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Project request not found")
    draft = build_market_signal_draft(db, row)
    return MarketSignalDraftOut(request_id=row.id, draft=draft, requires_operator_approval=True)


@router.post("/{request_id}/promote-market-signal")
def promote_market_signal(
    request_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    row = db.query(CustomerProjectRequest).filter(CustomerProjectRequest.id == request_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Project request not found")
    review = promote_market_signal_to_review(db, row, actor_id=user.id)
    return {"review_id": str(review.id), "status": review.status, "message": "Market signal queued for operator review."}


@router.post("/{request_id}/refresh-candidates", response_model=list[ProjectRequestCandidateOut])
def refresh_candidates(
    request_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ProjectRequestCandidateOut]:
    row = db.query(CustomerProjectRequest).filter(CustomerProjectRequest.id == request_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Project request not found")
    candidates = refresh_supplier_candidates(db, row, actor_id=user.id)
    db.commit()
    return [ProjectRequestCandidateOut.model_validate(c) for c in candidates]


@router.get("/{request_id}/candidates", response_model=list[ProjectRequestCandidateOut])
def list_candidates(
    request_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ProjectRequestCandidateOut]:
    rows = (
        db.query(ProjectRequestSupplierCandidate)
        .filter(ProjectRequestSupplierCandidate.project_request_id == request_id)
        .order_by(ProjectRequestSupplierCandidate.is_auto_recommended.desc())
        .all()
    )
    return [ProjectRequestCandidateOut.model_validate(r) for r in rows]


@router.post("/{request_id}/candidates/{candidate_id}/decision", response_model=ProjectRequestCandidateOut)
def decide_candidate(
    request_id: UUID,
    candidate_id: UUID,
    body: CandidateDecisionBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectRequestCandidateOut:
    cand = (
        db.query(ProjectRequestSupplierCandidate)
        .filter(
            ProjectRequestSupplierCandidate.id == candidate_id,
            ProjectRequestSupplierCandidate.project_request_id == request_id,
        )
        .first()
    )
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if body.decision == "selected" and not cand.eligible_for_formal_quote:
        raise HTTPException(status_code=400, detail="Candidate not eligible for formal quote")
    updated = record_candidate_decision(db, cand, decision=body.decision, reason=body.reason, actor_id=user.id)
    return ProjectRequestCandidateOut.model_validate(updated)
