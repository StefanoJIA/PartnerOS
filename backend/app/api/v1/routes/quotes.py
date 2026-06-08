"""V1 Customer Quote CRUD routes (D6.3)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import ApiError, NOT_FOUND, VALIDATION_ERROR
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.models.customer_quotes import Quote, QuoteAdjustment, QuoteLineItem, QuoteVersion
from app.schemas.quotes import (
    MarkSentIn,
    QuoteAdjustmentIn,
    QuoteAdjustmentUpdateIn,
    QuoteCreateIn,
    QuoteFromContractIn,
    QuoteLineItemIn,
    QuoteUpdateIn,
    QuoteVersionCreateIn,
)
from app.services.quotes.quote_delivery_service import mark_sent_with_delivery
from app.services.quotes.quote_service import (
    add_line_item,
    create_quote,
    create_quote_from_contract,
    create_version_snapshot,
    get_quote,
    mark_expired,
    mark_ready,
    quote_list_item,
    quote_to_dict,
    recalculate_quote,
)
from app.services.quotes.quote_totals import apply_totals_to_quote

router = APIRouter(prefix="/quotes", tags=["v1-quotes"])

ARCHIVABLE_QUOTE_STATUSES = ("internal_review", "ready_to_send", "revised", "expired")


@router.get("")
def list_quotes(
    request: Request,
    status: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Quote).filter(Quote.is_archived.is_(False))
    if status:
        q = q.filter(Quote.status == status)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(Quote.quote_number.ilike(like) | Quote.bill_to_company.ilike(like))
    total = q.count()
    rows = q.order_by(Quote.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    items = [quote_list_item(r) for r in rows]
    rid = get_request_id(request)
    return success_envelope(
        {"items": items, "total": total, "page": page, "limit": limit},
        request_id=rid,
        pagination={"page": page, "limit": limit, "total": total},
    )


@router.post("")
def create_quote_route(
    body: QuoteCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    quote = create_quote(
        db,
        user=user,
        line_items_in=[li.model_dump(mode="json") for li in body.line_items],
        lead_id=body.lead_id,
        company_id=body.company_id,
        contact_id=body.contact_id,
        bill_to=body.bill_to.model_dump() if body.bill_to else None,
        ship_to=body.ship_to.model_dump() if body.ship_to else None,
        payment_terms=body.payment_terms,
        shipping_terms=body.shipping_terms,
        internal_notes=body.internal_notes,
        customer_notes=body.customer_notes,
        default_incoterm=body.default_incoterm,
    )
    rid = get_request_id(request)
    return success_envelope(quote_to_dict(quote), request_id=rid, status_code=201)


@router.post("/from-contract")
def create_from_contract(
    body: QuoteFromContractIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    quote = create_quote_from_contract(
        db,
        user=user,
        lead_id=body.lead_id,
        line_items_in=[li.model_dump(mode="json") for li in body.line_items],
        bill_to=body.bill_to.model_dump() if body.bill_to else None,
        ship_to=body.ship_to.model_dump() if body.ship_to else None,
        payment_terms=body.payment_terms,
        shipping_terms=body.shipping_terms,
        internal_notes=body.internal_notes,
    )
    rid = get_request_id(request)
    return success_envelope(quote_to_dict(quote), request_id=rid, status_code=201)


@router.get("/{quote_id}")
def get_quote_route(
    quote_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    quote = get_quote(db, quote_id)
    rid = get_request_id(request)
    return success_envelope(quote_to_dict(quote), request_id=rid)


@router.patch("/{quote_id}")
def update_quote(
    quote_id: UUID,
    body: QuoteUpdateIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    quote = get_quote(db, quote_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(quote, k, v)
    quote.updated_by_id = user.id
    db.commit()
    db.refresh(quote)
    rid = get_request_id(request)
    return success_envelope(quote_to_dict(quote), request_id=rid)


@router.delete("/{quote_id}")
def archive_quote(
    quote_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    quote = get_quote(db, quote_id)
    if quote.status not in ARCHIVABLE_QUOTE_STATUSES:
        raise ApiError(
            VALIDATION_ERROR,
            "only unsent, revised, or expired quotes can be archived",
            status_code=400,
        )
    quote.is_archived = True
    quote.updated_by_id = user.id
    db.commit()
    rid = get_request_id(request)
    return success_envelope({"archived": True, "id": str(quote_id)}, request_id=rid)


@router.post("/{quote_id}/line-items")
def add_line_item_route(
    quote_id: UUID,
    body: QuoteLineItemIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    quote = add_line_item(db, quote_id, user=user, item=body.model_dump(mode="json"))
    rid = get_request_id(request)
    return success_envelope(quote_to_dict(quote), request_id=rid, status_code=201)


@router.delete("/{quote_id}/line-items/{line_id}")
def delete_line_item(
    quote_id: UUID,
    line_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    quote = get_quote(db, quote_id)
    line = db.query(QuoteLineItem).filter(QuoteLineItem.id == line_id, QuoteLineItem.quote_id == quote_id).first()
    if not line:
        raise ApiError(NOT_FOUND, "line item not found", status_code=404)
    db.delete(line)
    apply_totals_to_quote(quote)
    quote.updated_by_id = user.id
    db.commit()
    db.refresh(quote)
    rid = get_request_id(request)
    return success_envelope(quote_to_dict(quote), request_id=rid)


@router.post("/{quote_id}/adjustments")
def add_adjustment(
    quote_id: UUID,
    body: QuoteAdjustmentIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    quote = get_quote(db, quote_id)
    adj = QuoteAdjustment(
        quote_id=quote.id,
        type=body.type,
        label=body.label,
        amount=body.amount,
        percentage=body.percentage,
        taxable=body.taxable,
        customer_visible=body.customer_visible,
        notes=body.notes,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(adj)
    apply_totals_to_quote(quote)
    quote.updated_by_id = user.id
    db.commit()
    db.refresh(quote)
    rid = get_request_id(request)
    return success_envelope(quote_to_dict(quote), request_id=rid, status_code=201)


@router.patch("/{quote_id}/adjustments/{adjustment_id}")
def update_adjustment(
    quote_id: UUID,
    adjustment_id: UUID,
    body: QuoteAdjustmentUpdateIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    quote = get_quote(db, quote_id)
    adj = db.query(QuoteAdjustment).filter(QuoteAdjustment.id == adjustment_id, QuoteAdjustment.quote_id == quote_id).first()
    if not adj:
        raise ApiError(NOT_FOUND, "adjustment not found", status_code=404)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(adj, k, v)
    adj.updated_by_id = user.id
    apply_totals_to_quote(quote)
    db.commit()
    db.refresh(quote)
    rid = get_request_id(request)
    return success_envelope(quote_to_dict(quote), request_id=rid)


@router.delete("/{quote_id}/adjustments/{adjustment_id}")
def delete_adjustment(
    quote_id: UUID,
    adjustment_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    quote = get_quote(db, quote_id)
    adj = db.query(QuoteAdjustment).filter(QuoteAdjustment.id == adjustment_id, QuoteAdjustment.quote_id == quote_id).first()
    if not adj:
        raise ApiError(NOT_FOUND, "adjustment not found", status_code=404)
    db.delete(adj)
    apply_totals_to_quote(quote)
    db.commit()
    db.refresh(quote)
    rid = get_request_id(request)
    return success_envelope(quote_to_dict(quote), request_id=rid)


@router.get("/{quote_id}/versions")
def list_versions(
    quote_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = (
        db.query(QuoteVersion)
        .filter(QuoteVersion.quote_id == quote_id)
        .order_by(QuoteVersion.version_number.asc())
        .all()
    )
    items = [
        {
            "id": str(v.id),
            "version_number": v.version_number,
            "version_label": v.version_label,
            "version_type": v.version_type,
            "status": v.status,
            "created_at": v.created_at.isoformat(),
            "notes": v.notes,
        }
        for v in rows
    ]
    rid = get_request_id(request)
    return success_envelope({"items": items}, request_id=rid)


@router.post("/{quote_id}/versions")
def create_version(
    quote_id: UUID,
    body: QuoteVersionCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    quote = get_quote(db, quote_id)
    version = create_version_snapshot(
        db,
        quote,
        user=user,
        version_type=body.version_type,
        version_label=body.version_label,
        notes=body.notes,
    )
    if quote.status == "sent":
        quote.status = "revised"
    db.commit()
    rid = get_request_id(request)
    return success_envelope(
        {"id": str(version.id), "version_number": version.version_number, "version_label": version.version_label},
        request_id=rid,
        status_code=201,
    )


@router.post("/{quote_id}/mark-ready")
def mark_ready_route(
    quote_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    quote = mark_ready(db, quote_id, user=user)
    rid = get_request_id(request)
    return success_envelope(quote_to_dict(quote), request_id=rid)


@router.post("/{quote_id}/mark-sent")
def mark_sent_route(
    quote_id: UUID,
    body: MarkSentIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = mark_sent_with_delivery(
        db,
        quote_id,
        user=user,
        sent_channel=body.sent_channel,
        send_channel=body.send_channel,
        quote_version_id=body.quote_version_id,
        pdf_export_id=body.pdf_export_id,
        sent_to_name=body.sent_to_name,
        sent_to_email=body.sent_to_email,
        sent_to_company=body.sent_to_company,
        sent_at=body.sent_at,
        follow_up_date=body.follow_up_date,
        note=body.note,
    )
    rid = get_request_id(request)
    return success_envelope(result, request_id=rid)


@router.post("/{quote_id}/mark-expired")
def mark_expired_route(
    quote_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    quote = mark_expired(db, quote_id, user=user)
    rid = get_request_id(request)
    return success_envelope(quote_to_dict(quote), request_id=rid)
