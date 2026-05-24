"""V1 Customer Order CRUD routes (D7.2+)."""

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
    SupplierConfirmationIn,
    VoidConfirmationIn,
    VoidSupplierConfirmationIn,
)
from app.services.orders.partner_split_service import (
    ensure_partner_splits,
    get_partner_split_detail,
    get_partner_splits,
    split_to_dict,
)
from app.services.orders.supplier_confirmation_service import (
    add_supplier_confirmation,
    confirmation_to_dict as supplier_confirmation_to_dict,
    list_supplier_confirmations,
    void_supplier_confirmation,
)
from app.services.orders.order_confirmation_service import (
    add_customer_confirmation,
    confirmation_to_dict,
    list_customer_confirmations,
    void_customer_confirmation,
)
from app.services.orders.order_service import (
    ORDER_SAFETY_RESPONSE,
    cancel_order,
    create_order_from_quote,
    get_order,
    order_detail_payload,
    order_list_item,
    order_to_dict,
    update_order,
)
from app.services.orders.order_timeline import build_order_timeline

router = APIRouter(prefix="/orders", tags=["v1-orders"])


def _confirmation_response(db: Session, result: dict) -> dict:
    order = result["order"]
    payload = order_detail_payload(db, order)
    payload["confirmation"] = confirmation_to_dict(result["confirmation"])
    payload["status_changed"] = result.get("status_changed", False)
    payload["warnings"] = result.get("warnings") or []
    payload["safety"] = result.get("safety") or payload.get("safety")
    return payload


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
    payload = order_detail_payload(db, order)
    payload["line_items"] = order_to_dict(order)["line_items"]
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
    user: User = Depends(get_current_user),
):
    result = add_customer_confirmation(
        db,
        user,
        order_id,
        confirmation_type=body.confirmation_type,
        confirmed_at=body.confirmed_at,
        confirmed_by_name=body.confirmed_by_name,
        confirmed_by_email=body.confirmed_by_email,
        confirmed_by_company=body.confirmed_by_company,
        source_channel=body.source_channel,
        evidence_reference=body.evidence_reference,
        evidence_filename=body.evidence_filename,
        note=body.note,
    )
    rid = get_request_id(request)
    return success_envelope(_confirmation_response(db, result), request_id=rid)


@router.get("/{order_id}/confirmations")
def list_confirmations_route(
    order_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = list_customer_confirmations(db, order_id)
    rid = get_request_id(request)
    return success_envelope(
        {"items": [confirmation_to_dict(r) for r in rows], "total": len(rows)},
        request_id=rid,
    )


@router.post("/{order_id}/confirmations/{confirmation_id}/void")
def void_confirmation_route(
    order_id: UUID,
    confirmation_id: UUID,
    body: VoidConfirmationIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = void_customer_confirmation(
        db, user, order_id, confirmation_id, reason=body.reason
    )
    rid = get_request_id(request)
    payload = order_detail_payload(db, result["order"])
    payload["confirmation"] = confirmation_to_dict(result["confirmation"])
    payload["warnings"] = result.get("warnings") or []
    payload["safety"] = result.get("safety")
    return success_envelope(payload, request_id=rid)


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


@router.post("/{order_id}/partner-splits/ensure")
def ensure_partner_splits_route(
    order_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = ensure_partner_splits(db, user.id, order_id)
    rid = get_request_id(request)
    payload = order_detail_payload(db, get_order(db, order_id))
    payload.update(result)
    return success_envelope(payload, request_id=rid)


@router.get("/{order_id}/partner-splits")
def list_partner_splits_route(
    order_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = get_partner_splits(db, order_id)
    rid = get_request_id(request)
    return success_envelope(
        {"items": [split_to_dict(db, r) for r in rows], "total": len(rows)},
        request_id=rid,
    )


@router.get("/{order_id}/partner-splits/{split_id}")
def get_partner_split_route(
    order_id: UUID,
    split_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rid = get_request_id(request)
    return success_envelope(get_partner_split_detail(db, order_id, split_id), request_id=rid)


@router.post("/{order_id}/partner-splits/{split_id}/supplier-confirmations")
def add_supplier_confirmation_route(
    order_id: UUID,
    split_id: UUID,
    body: SupplierConfirmationIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = add_supplier_confirmation(
        db,
        user,
        order_id,
        split_id,
        confirmation_status=body.confirmation_status,
        confirmed_at=body.confirmed_at,
        confirmed_by_name=body.confirmed_by_name,
        confirmed_by_email=body.confirmed_by_email,
        confirmation_channel=body.confirmation_channel,
        inventory_confirmed=body.inventory_confirmed,
        certification_confirmed=body.certification_confirmed,
        lead_time_confirmed=body.lead_time_confirmed,
        production_capacity_confirmed=body.production_capacity_confirmed,
        expected_production_start=body.expected_production_start,
        expected_ready_date=body.expected_ready_date,
        supplier_reference=body.supplier_reference,
        note=body.note,
    )
    rid = get_request_id(request)
    payload = get_partner_split_detail(db, order_id, split_id)
    payload["confirmation"] = supplier_confirmation_to_dict(result["confirmation"])
    payload["warnings"] = result.get("warnings") or []
    payload["safety"] = result.get("safety")
    return success_envelope(payload, request_id=rid, status_code=201)


@router.get("/{order_id}/supplier-confirmations")
def list_supplier_confirmations_route(
    order_id: UUID,
    request: Request,
    split_id: UUID | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = list_supplier_confirmations(db, order_id, split_id=split_id)
    rid = get_request_id(request)
    return success_envelope(
        {"items": [supplier_confirmation_to_dict(r) for r in rows], "total": len(rows)},
        request_id=rid,
    )


@router.post("/{order_id}/supplier-confirmations/{confirmation_id}/void")
def void_supplier_confirmation_route(
    order_id: UUID,
    confirmation_id: UUID,
    body: VoidSupplierConfirmationIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = void_supplier_confirmation(
        db, user, order_id, confirmation_id, reason=body.reason
    )
    rid = get_request_id(request)
    payload = get_partner_split_detail(db, order_id, result["split"].id)
    payload["confirmation"] = supplier_confirmation_to_dict(result["confirmation"])
    payload["warnings"] = result.get("warnings") or []
    payload["safety"] = result.get("safety")
    return success_envelope(payload, request_id=rid)
