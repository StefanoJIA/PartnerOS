import uuid
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import (
    AIOutput,
    Company,
    Contact,
    Lead,
    ManufacturingPartner,
    Order,
    OrderItem,
    Product,
    ProductionMilestone,
    Quotation,
    RFQ,
    RFQItem,
    RFQPartnerCandidate,
    Sample,
    User,
)
from app.models.enums import RFQPartnerCandidateStatus, RFQStatus
from app.schemas.orders_domain import DEFAULT_MILESTONE_NAMES, OrderOut, next_order_number
from app.schemas.pagination import PaginatedResponse
from app.schemas.quotation_domain import QuotationCreate, QuotationOut
from app.schemas.rfq_domain import (
    RFQConvertToOrderBody,
    RFQConvertToSampleBody,
    RFQCreate,
    RFQDetailOut,
    RFQItemCreate,
    RFQItemOut,
    RFQItemUpdate,
    RFQListItemOut,
    RFQOut,
    RFQPartnerBody,
    RFQPartnerCandidateCreate,
    RFQPartnerCandidateOut,
    RFQPartnerCandidateUpdate,
    RFQPartnerCandidateWithPartnerOut,
    RFQStatusBody,
    RFQUpdate,
    RFQWorkspaceOut,
    PartnerBrief,
    ProductBrief,
)
from app.schemas.samples_domain import SampleOut, next_sample_number
from app.services.activity import log_activity
from app.services.ai import client as ai_client
from app.services.ai import prompts as prompt_lib
from app.services.quotation_comparison import QuotationComparisonOut, build_quotation_comparison
from app.services.rfq_workspace import build_rfq_workspace, candidate_sort_key

router = APIRouter(prefix="/rfqs", tags=["rfqs"])


def _next_rfq_number() -> str:
    return f"RFQ-{uuid.uuid4().hex[:8].upper()}"


def _quotation_row_out(row: Quotation) -> QuotationOut:
    return QuotationOut.model_validate(row)


def _item_out(db: Session, item: RFQItem) -> RFQItemOut:
    pb = None
    if item.product_id:
        p = db.query(Product).filter(Product.id == item.product_id).first()
        if p:
            pb = ProductBrief.model_validate(p)
    base = RFQItemOut.model_validate(item)
    return base.model_copy(update={"product": pb})


@router.get("", response_model=PaginatedResponse[RFQListItemOut])
def list_rfqs(
    status: str | None = Query(None),
    company_id: UUID | None = None,
    target_delivery_from: date | None = Query(None),
    target_delivery_to: date | None = Query(None),
    has_quotation: bool | None = None,
    waiting_partner_quote: bool | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[RFQListItemOut]:
    q = (
        db.query(RFQ, Company.company_name, Contact.first_name, Contact.last_name, Lead.lead_name)
        .outerjoin(Company, RFQ.company_id == Company.id)
        .outerjoin(Contact, RFQ.contact_id == Contact.id)
        .outerjoin(Lead, RFQ.lead_id == Lead.id)
    )

    if status:
        q = q.filter(RFQ.status == status)
    if company_id:
        q = q.filter(RFQ.company_id == company_id)
    if target_delivery_from:
        q = q.filter(RFQ.target_delivery_date.isnot(None), RFQ.target_delivery_date >= target_delivery_from)
    if target_delivery_to:
        q = q.filter(RFQ.target_delivery_date.isnot(None), RFQ.target_delivery_date <= target_delivery_to)
    if has_quotation is True:
        q = q.filter(RFQ.id.in_(db.query(Quotation.rfq_id).filter(Quotation.rfq_id.isnot(None))))
    if has_quotation is False:
        q = q.filter(~RFQ.id.in_(db.query(Quotation.rfq_id).filter(Quotation.rfq_id.isnot(None))))
    if waiting_partner_quote:
        cand_ids = [
            x[0]
            for x in db.query(RFQPartnerCandidate.rfq_id)
            .filter(
                RFQPartnerCandidate.partner_status == RFQPartnerCandidateStatus.quote_requested.value,
                RFQPartnerCandidate.quote_received_at.is_(None),
            )
            .distinct()
            .all()
        ]
        cond = RFQ.status == RFQStatus.waiting_partner_quote.value
        if cand_ids:
            cond = or_(cond, RFQ.id.in_(cand_ids))
        q = q.filter(cond)

    total = q.count()
    rows = q.order_by(RFQ.updated_at.desc()).offset((page - 1) * limit).limit(limit).all()
    rfq_ids = [r[0].id for r in rows]
    qset: set[uuid.UUID] = set()
    if rfq_ids:
        qset = {
            x[0]
            for x in db.query(Quotation.rfq_id).filter(Quotation.rfq_id.in_(rfq_ids)).distinct().all()
            if x[0]
        }

    items: list[RFQListItemOut] = []
    for r, cn, fn, ln, lname in rows:
        c_label = None
        if fn or ln:
            c_label = f"{fn or ''} {ln or ''}".strip() or None
        items.append(
            RFQListItemOut(
                id=r.id,
                rfq_number=r.rfq_number,
                status=r.status,
                company_id=r.company_id,
                company_name=cn,
                contact_id=r.contact_id,
                contact_label=c_label,
                lead_id=r.lead_id,
                lead_name=lname,
                target_delivery_date=r.target_delivery_date,
                required_certifications=r.required_certifications,
                created_at=r.created_at,
                updated_at=r.updated_at,
                has_quotation=r.id in qset,
            )
        )
    return PaginatedResponse(items=items, total=total, page=page, limit=limit)


@router.post("", response_model=RFQOut, status_code=status.HTTP_201_CREATED)
def create_rfq(
    body: RFQCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RFQOut:
    row = RFQ(
        rfq_number=_next_rfq_number(),
        **body.model_dump(),
        owner_user_id=user.id,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="rfq", object_id=row.id, action="rfq_created", actor_id=user.id)
    if row.lead_id:
        log_activity(
            db,
            object_type="lead",
            object_id=row.lead_id,
            action="rfq_created_from_lead",
            actor_id=user.id,
            diff={"rfq_id": str(row.id), "rfq_number": row.rfq_number},
        )
    db.commit()
    return RFQOut.model_validate(row)


@router.get("/{rfq_id}/workspace", response_model=RFQWorkspaceOut)
def get_rfq_workspace_route(
    rfq_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> RFQWorkspaceOut:
    ws = build_rfq_workspace(db, rfq_id)
    if not ws:
        raise HTTPException(status_code=404, detail="RFQ not found")
    return ws


@router.get("/{rfq_id}/quotation-comparison", response_model=QuotationComparisonOut)
def get_quotation_comparison_route(
    rfq_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> QuotationComparisonOut:
    quotations = db.query(Quotation).filter(Quotation.rfq_id == rfq_id).all()
    pmap: dict[UUID, ManufacturingPartner] = {}
    pids = {q.manufacturing_partner_id for q in quotations if q.manufacturing_partner_id}
    if pids:
        for p in db.query(ManufacturingPartner).filter(ManufacturingPartner.id.in_(pids)).all():
            pmap[p.id] = p
    return build_quotation_comparison(quotations, pmap)


# --- RFQ Items (declare before /{rfq_id} GET) ---


@router.get("/{rfq_id}/items", response_model=list[RFQItemOut])
def list_rfq_items(
    rfq_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[RFQItemOut]:
    if not db.query(RFQ).filter(RFQ.id == rfq_id).first():
        raise HTTPException(status_code=404, detail="RFQ not found")
    items = db.query(RFQItem).filter(RFQItem.rfq_id == rfq_id).order_by(RFQItem.created_at.asc()).all()
    return [_item_out(db, it) for it in items]


@router.post("/{rfq_id}/items", response_model=RFQItemOut, status_code=status.HTTP_201_CREATED)
def add_rfq_item(
    rfq_id: UUID,
    body: RFQItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RFQItemOut:
    row = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="RFQ not found")
    item = RFQItem(rfq_id=rfq_id, **body.model_dump(), created_by_id=user.id, updated_by_id=user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    log_activity(
        db, object_type="rfq", object_id=rfq_id, action="rfq_item_added", actor_id=user.id, diff={"item_id": str(item.id)}
    )
    db.commit()
    return _item_out(db, item)


@router.put("/{rfq_id}/items/{item_id}", response_model=RFQItemOut)
def update_rfq_item(
    rfq_id: UUID,
    item_id: UUID,
    body: RFQItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RFQItemOut:
    item = db.query(RFQItem).filter(RFQItem.id == item_id, RFQItem.rfq_id == rfq_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(item, k, v)
    item.updated_by_id = user.id
    db.commit()
    db.refresh(item)
    log_activity(
        db, object_type="rfq", object_id=rfq_id, action="rfq_item_updated", actor_id=user.id, diff={"item_id": str(item.id)}
    )
    db.commit()
    return _item_out(db, item)


@router.delete("/{rfq_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rfq_item(
    rfq_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    item = db.query(RFQItem).filter(RFQItem.id == item_id, RFQItem.rfq_id == rfq_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    log_activity(
        db, object_type="rfq", object_id=rfq_id, action="rfq_item_removed", actor_id=user.id, diff={"item_id": str(item_id)}
    )
    db.commit()


# --- Partner candidates ---


@router.get("/{rfq_id}/partner-candidates", response_model=list[RFQPartnerCandidateWithPartnerOut])
def list_partner_candidates(
    rfq_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[RFQPartnerCandidateWithPartnerOut]:
    if not db.query(RFQ).filter(RFQ.id == rfq_id).first():
        raise HTTPException(status_code=404, detail="RFQ not found")
    cands = db.query(RFQPartnerCandidate).filter(RFQPartnerCandidate.rfq_id == rfq_id).all()
    cands_sorted = sorted(cands, key=candidate_sort_key)
    out: list[RFQPartnerCandidateWithPartnerOut] = []
    for c in cands_sorted:
        p = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == c.partner_id).first()
        if not p:
            continue
        out.append(
            RFQPartnerCandidateWithPartnerOut(
                **RFQPartnerCandidateOut.model_validate(c).model_dump(),
                partner=PartnerBrief.model_validate(p),
            )
        )
    return out


@router.post("/{rfq_id}/partner-candidates", response_model=RFQPartnerCandidateOut, status_code=status.HTTP_201_CREATED)
def add_partner_candidate(
    rfq_id: UUID,
    body: RFQPartnerCandidateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RFQPartnerCandidateOut:
    row = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="RFQ not found")
    exists_c = (
        db.query(RFQPartnerCandidate)
        .filter(RFQPartnerCandidate.rfq_id == rfq_id, RFQPartnerCandidate.partner_id == body.partner_id)
        .first()
    )
    if exists_c:
        raise HTTPException(status_code=400, detail="Partner already a candidate for this RFQ")
    cand = RFQPartnerCandidate(rfq_id=rfq_id, **body.model_dump(), created_by_id=user.id, updated_by_id=user.id)
    db.add(cand)
    db.commit()
    db.refresh(cand)
    log_activity(
        db,
        object_type="rfq",
        object_id=rfq_id,
        action="rfq_partner_candidate_added",
        actor_id=user.id,
        diff={"candidate_id": str(cand.id), "partner_id": str(body.partner_id)},
    )
    db.commit()
    return RFQPartnerCandidateOut.model_validate(cand)


@router.post("/{rfq_id}/partners", response_model=RFQPartnerCandidateOut, status_code=status.HTTP_201_CREATED)
def add_rfq_partner_legacy(
    rfq_id: UUID,
    body: RFQPartnerBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RFQPartnerCandidateOut:
    """Back-compat alias for older clients; same as POST /partner-candidates."""
    return add_partner_candidate(rfq_id, body, db, user)


@router.put("/{rfq_id}/partner-candidates/{candidate_id}", response_model=RFQPartnerCandidateOut)
def update_partner_candidate(
    rfq_id: UUID,
    candidate_id: UUID,
    body: RFQPartnerCandidateUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RFQPartnerCandidateOut:
    cand = db.query(RFQPartnerCandidate).filter(RFQPartnerCandidate.id == candidate_id, RFQPartnerCandidate.rfq_id == rfq_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    prev_req = cand.quote_requested_at
    prev_recv = cand.quote_received_at
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(cand, k, v)
    cand.updated_by_id = user.id
    db.commit()
    db.refresh(cand)
    log_activity(
        db,
        object_type="rfq",
        object_id=rfq_id,
        action="rfq_partner_candidate_updated",
        actor_id=user.id,
        diff={"candidate_id": str(candidate_id)},
    )
    if body.quote_requested_at is not None and prev_req is None:
        log_activity(
            db,
            object_type="rfq",
            object_id=rfq_id,
            action="rfq_partner_quote_requested",
            actor_id=user.id,
            diff={"candidate_id": str(candidate_id)},
        )
    if body.quote_received_at is not None and prev_recv is None:
        log_activity(
            db,
            object_type="rfq",
            object_id=rfq_id,
            action="rfq_partner_quote_received",
            actor_id=user.id,
            diff={"candidate_id": str(candidate_id)},
        )
    db.commit()
    return RFQPartnerCandidateOut.model_validate(cand)


@router.post("/{rfq_id}/partner-candidates/{candidate_id}/quote-requested", response_model=RFQPartnerCandidateOut)
def mark_quote_requested(
    rfq_id: UUID,
    candidate_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RFQPartnerCandidateOut:
    cand = db.query(RFQPartnerCandidate).filter(RFQPartnerCandidate.id == candidate_id, RFQPartnerCandidate.rfq_id == rfq_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    now = datetime.now(timezone.utc)
    cand.partner_status = RFQPartnerCandidateStatus.quote_requested.value
    cand.quote_requested_at = now
    cand.updated_by_id = user.id
    db.commit()
    db.refresh(cand)
    log_activity(
        db, object_type="rfq", object_id=rfq_id, action="rfq_partner_quote_requested", actor_id=user.id, diff={"candidate_id": str(candidate_id)}
    )
    db.commit()
    return RFQPartnerCandidateOut.model_validate(cand)


@router.post("/{rfq_id}/partner-candidates/{candidate_id}/quote-received", response_model=RFQPartnerCandidateOut)
def mark_quote_received(
    rfq_id: UUID,
    candidate_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RFQPartnerCandidateOut:
    cand = db.query(RFQPartnerCandidate).filter(RFQPartnerCandidate.id == candidate_id, RFQPartnerCandidate.rfq_id == rfq_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    now = datetime.now(timezone.utc)
    cand.partner_status = RFQPartnerCandidateStatus.quote_received.value
    cand.quote_received_at = now
    cand.updated_by_id = user.id
    db.commit()
    db.refresh(cand)
    log_activity(
        db, object_type="rfq", object_id=rfq_id, action="rfq_partner_quote_received", actor_id=user.id, diff={"candidate_id": str(candidate_id)}
    )
    db.commit()
    return RFQPartnerCandidateOut.model_validate(cand)


@router.delete("/{rfq_id}/partner-candidates/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_partner_candidate(
    rfq_id: UUID,
    candidate_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    cand = db.query(RFQPartnerCandidate).filter(RFQPartnerCandidate.id == candidate_id, RFQPartnerCandidate.rfq_id == rfq_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    db.delete(cand)
    db.commit()
    log_activity(
        db,
        object_type="rfq",
        object_id=rfq_id,
        action="rfq_partner_candidate_removed",
        actor_id=user.id,
        diff={"candidate_id": str(candidate_id)},
    )
    db.commit()


# --- Quotations ---


@router.get("/{rfq_id}/quotations", response_model=PaginatedResponse[QuotationOut])
def list_rfq_quotations(
    rfq_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[QuotationOut]:
    if not db.query(RFQ).filter(RFQ.id == rfq_id).first():
        raise HTTPException(status_code=404, detail="RFQ not found")
    qry = db.query(Quotation).filter(Quotation.rfq_id == rfq_id)
    total = qry.count()
    rows = qry.order_by(Quotation.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(items=[_quotation_row_out(r) for r in rows], total=total, page=page, limit=limit)


@router.post("/{rfq_id}/quotations", response_model=QuotationOut, status_code=status.HTTP_201_CREATED)
def create_rfq_quotation(
    rfq_id: UUID,
    body: QuotationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QuotationOut:
    if not db.query(RFQ).filter(RFQ.id == rfq_id).first():
        raise HTTPException(status_code=404, detail="RFQ not found")
    payload = body.model_dump()
    payload["rfq_id"] = rfq_id
    row = Quotation(**payload, created_by_id=user.id, updated_by_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="rfq", object_id=rfq_id, action="quotation_added", actor_id=user.id, diff={"quotation_id": str(row.id)})
    db.commit()
    return _quotation_row_out(row)


# --- Convert ---


@router.post("/{rfq_id}/convert-to-sample", response_model=SampleOut, status_code=status.HTTP_201_CREATED)
def convert_rfq_to_sample(
    rfq_id: UUID,
    body: RFQConvertToSampleBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SampleOut:
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    item = db.query(RFQItem).filter(RFQItem.id == body.rfq_item_id, RFQItem.rfq_id == rfq_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="RFQ item not found")
    row = Sample(
        sample_request_number=next_sample_number(),
        company_id=rfq.company_id,
        contact_id=rfq.contact_id,
        lead_id=rfq.lead_id,
        rfq_id=rfq_id,
        product_id=item.product_id,
        manufacturing_partner_id=body.manufacturing_partner_id,
        sample_status="Requested",
        notes=body.notes,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="rfq", object_id=rfq_id, action="rfq_converted_to_sample", actor_id=user.id, diff={"sample_id": str(row.id)})
    log_activity(db, object_type="sample", object_id=row.id, action="sample_created_from_rfq", actor_id=user.id, diff={"rfq_id": str(rfq_id)})
    db.commit()
    return SampleOut.model_validate(row)


@router.post("/{rfq_id}/convert-to-order", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def convert_rfq_to_order(
    rfq_id: UUID,
    body: RFQConvertToOrderBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderOut:
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    q_row: Quotation | None = None
    if body.quotation_id:
        q_row = db.query(Quotation).filter(Quotation.id == body.quotation_id, Quotation.rfq_id == rfq_id).first()
        if not q_row:
            raise HTTPException(status_code=404, detail="Quotation not found for this RFQ")
        if q_row.manufacturing_partner_id and q_row.manufacturing_partner_id != body.manufacturing_partner_id:
            raise HTTPException(status_code=400, detail="manufacturing_partner_id must match quotation")

    product_id = None
    qty = None
    unit_price = None
    total_amount = None
    quotation_id = body.quotation_id
    if q_row:
        product_id = q_row.product_id
        qty = q_row.quantity
        unit_price = q_row.unit_price
        if qty is not None and unit_price is not None:
            total_amount = unit_price * qty
    else:
        item = None
        if body.rfq_item_id:
            item = db.query(RFQItem).filter(RFQItem.id == body.rfq_item_id, RFQItem.rfq_id == rfq_id).first()
        if not item:
            raise HTTPException(status_code=400, detail="Provide quotation_id or valid rfq_item_id")
        product_id = item.product_id
        qty = item.quantity

    order = Order(
        order_number=next_order_number(),
        company_id=rfq.company_id,
        contact_id=rfq.contact_id,
        lead_id=rfq.lead_id,
        rfq_id=rfq_id,
        quotation_id=quotation_id,
        manufacturing_partner_id=body.manufacturing_partner_id,
        total_amount=total_amount,
        currency=q_row.currency if q_row else "USD",
        incoterm=q_row.incoterm if q_row else None,
        production_status="Draft",
        notes=body.notes,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    if product_id:
        oi = OrderItem(
            order_id=order.id,
            product_id=product_id,
            quantity=qty,
            unit_price=unit_price,
            created_by_id=user.id,
            updated_by_id=user.id,
        )
        db.add(oi)
    db.commit()
    db.refresh(order)
    log_activity(db, object_type="rfq", object_id=rfq_id, action="rfq_converted_to_order", actor_id=user.id, diff={"order_id": str(order.id)})
    log_activity(db, object_type="order", object_id=order.id, action="order_created_from_rfq", actor_id=user.id, diff={"rfq_id": str(rfq_id)})
    db.commit()
    if body.generate_milestones:
        for name in DEFAULT_MILESTONE_NAMES:
            m = ProductionMilestone(
                order_id=order.id,
                milestone_name=name,
                status="pending",
                created_by_id=user.id,
                updated_by_id=user.id,
            )
            db.add(m)
        db.commit()
    return OrderOut.model_validate(order)


@router.get("/{rfq_id}", response_model=RFQDetailOut)
def get_rfq(
    rfq_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> RFQDetailOut:
    row = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="RFQ not found")
    return RFQDetailOut.model_validate(row)


@router.put("/{rfq_id}", response_model=RFQDetailOut)
def update_rfq(
    rfq_id: UUID,
    body: RFQUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RFQDetailOut:
    row = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="RFQ not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="rfq", object_id=row.id, action="rfq_updated", actor_id=user.id, diff=data)
    db.commit()
    return RFQDetailOut.model_validate(row)


@router.post("/{rfq_id}/status", response_model=RFQDetailOut)
def set_rfq_status(
    rfq_id: UUID,
    body: RFQStatusBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RFQDetailOut:
    row = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="RFQ not found")
    prev = row.status
    row.status = body.status
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    log_activity(
        db,
        object_type="rfq",
        object_id=row.id,
        action="rfq_status_changed",
        actor_id=user.id,
        diff={"from": prev, "to": body.status},
    )
    db.commit()
    return RFQDetailOut.model_validate(row)


@router.post("/{rfq_id}/recommend-partners")
def recommend_partners(
    rfq_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    row = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="RFQ not found")
    partners = (
        db.query(ManufacturingPartner)
        .filter(ManufacturingPartner.is_active.is_(True))
        .order_by(ManufacturingPartner.partner_name.asc())
        .limit(20)
        .all()
    )
    lines = [
        f"- {p.partner_name}: type={p.partner_type}, ratings q/c/d/p={p.quality_rating}/{p.communication_rating}/"
        f"{p.delivery_rating}/{p.project_fit_rating}, risk={p.risk_level}"
        for p in partners
    ]
    ctx = {
        "customer_requirement": row.customer_requirement or "",
        "required_certifications": row.required_certifications or "",
        "partners": "\n".join(lines),
    }
    msgs = prompt_lib.partner_recommendation_prompt(ctx)
    text = ai_client.chat_completion(msgs)
    row.ai_recommended_partners = text
    row.updated_by_id = user.id
    db.commit()
    ao = AIOutput(
        task_type="partner_recommendation",
        input_object_type="rfq",
        input_object_id=row.id,
        prompt=str(msgs)[:50000],
        output_text=text,
        status="draft",
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(ao)
    db.commit()
    return {"rfq_id": str(row.id), "recommended_text": text, "ai_output_id": str(ao.id)}


@router.post("/{rfq_id}/generate-quotation")
def generate_quotation_stub(
    rfq_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    if not db.query(RFQ).filter(RFQ.id == rfq_id).first():
        raise HTTPException(status_code=404, detail="RFQ not found")
    return {"message": "Create quotations via POST /api/rfqs/{id}/quotations or POST /api/quotations.", "rfq_id": str(rfq_id)}
