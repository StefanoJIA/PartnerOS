"""V1 Customer Order CRUD routes (D7.2)."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.models.customer_orders import CustomerOrder
from app.schemas.customer_orders import (
    CancelOrderIn,
    ConfirmCustomerIn,
    OrderFromQuoteIn,
    OrderUpdateIn,
)
from app.services.orders.order_service import (
    ORDER_SAFETY_RESPONSE,
    cancel_order,
    confirm_customer,
    create_order_from_quote,
    get_order,
    order_detail_payload,
    order_list_item,
    order_to_dict,
    update_order,
)
from app.services.orders.order_timeline import build_order_timeline

router = APIRouter(prefix="/orders", tags=["v1-orders"])


@router.post("/from-quote")
def create_order_from_quote_route(
    body: OrderFromQuoteIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = create_order_from_quote(
        db,
        user,
        quote_id=body.quote_id,
        quote_version_id=body.quote_version_id,
        pdf_export_id=body.pdf_export_id,
        delivery_log_id=body.delivery_log_id,
        customer_confirmation=body.customer_confirmation.model_dump() if body.customer_confirmation else None,
        selected_line_item_ids=body.selected_line_item_ids,
        bill_to=body.bill_to.model_dump() if body.bill_to else None,
        ship_to=body.ship_to.model_dump() if body.ship_to else None,
        internal_notes=body.internal_notes,
        customer_notes=body.customer_notes,
    )
    rid = get_request_id(request)
    payload = {
        "order": order_to_dict(order),
        "line_items": order_to_dict(order)["line_items"],
        "source_quote": order_detail_payload(db, order)["source_quote"],
        "safety": ORDER_SAFETY_RESPONSE,
    }
    return success_envelope(payload, request_id=rid, status_code=201)


@router.get("")
def list_orders(
    request: Request,
    status: str | None = None,
    company_id: UUID | None = None,
    quote_id: UUID | None = None,
    search: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(CustomerOrder)
    if status:
        q = q.filter(CustomerOrder.status == status)
    if company_id:
        q = q.filter(CustomerOrder.company_id == company_id)
    if quote_id:
        q = q.filter(CustomerOrder.source_quote_id == quote_id)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(CustomerOrder.order_number.ilike(like) | CustomerOrder.bill_to_company.ilike(like))
    if date_from:
        q = q.filter(CustomerOrder.order_date >= date_from)
    if date_to:
        q = q.filter(CustomerOrder.order_date <= date_to)
    total = q.count()
    rows = q.order_by(CustomerOrder.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    items = [order_list_item(r) for r in rows]
    rid = get_request_id(request)
    return success_envelope(
        {"items": items, "total": total, "page": page, "limit": limit},
        request_id=rid,
        pagination={"page": page, "limit": limit, "total": total},
    )


@router.get("/{order_id}")
def get_order_route(
    order_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    order = get_order(db, order_id)
    rid = get_request_id(request)
    payload = order_detail_payload(db, order)
    payload["timeline"] = build_order_timeline(db, order_id)["items"]
    return success_envelope(payload, request_id=rid)


@router.patch("/{order_id}")
def patch_order_route(
    order_id: UUID,
    body: OrderUpdateIn,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    data = body.model_dump(exclude_unset=True)
    order = update_order(db, order_id, **data)
    rid = get_request_id(request)
    return success_envelope(order_detail_payload(db, order), request_id=rid)


@router.post("/{order_id}/confirm-customer")
def confirm_customer_route(
    order_id: UUID,
    body: ConfirmCustomerIn,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    confirmed_at = None
    if body.confirmed_at:
        if isinstance(body.confirmed_at, str):
            from datetime import datetime

            confirmed_at = datetime.fromisoformat(body.confirmed_at.replace("Z", "+00:00"))
        else:
            confirmed_at = body.confirmed_at
    order = confirm_customer(
        db,
        order_id,
        confirmation_type=body.confirmation_type,
        confirmed_at=confirmed_at,
        note=body.note,
    )
    rid = get_request_id(request)
    return success_envelope(order_detail_payload(db, order), request_id=rid)


@router.post("/{order_id}/cancel")
def cancel_order_route(
    order_id: UUID,
    body: CancelOrderIn,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    order = cancel_order(db, order_id, reason=body.reason)
    rid = get_request_id(request)
    return success_envelope(order_detail_payload(db, order), request_id=rid)


@router.get("/{order_id}/timeline")
def order_timeline_route(
    order_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rid = get_request_id(request)
    return success_envelope(build_order_timeline(db, order_id), request_id=rid)
