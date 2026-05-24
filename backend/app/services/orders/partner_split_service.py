"""Partner split service (D7.4)."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import NOT_FOUND, VALIDATION_ERROR, ApiError
from app.models import ManufacturingPartner
from app.models.customer_orders import CustomerOrder, OrderLineItem, OrderPartnerSplit, SupplierConfirmation
from app.services.activity import log_activity
from app.services.orders.order_service import ORDER_SAFETY, get_order, _serialize_line

SPLIT_SAFETY: dict[str, bool] = {
    **ORDER_SAFETY,
    "supplier_notified": False,
    "production_started": False,
    "shipment_created": False,
    "automatic_sending_enabled": False,
    "payment_received": False,
}


def split_safety() -> dict[str, bool]:
    return dict(SPLIT_SAFETY)


def _partner_name(db: Session, partner_id: UUID) -> str:
    row = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == partner_id).first()
    if not row:
        return str(partner_id)[:8]
    return row.partner_name or row.brand_name or str(partner_id)[:8]


def split_to_dict(db: Session, split: OrderPartnerSplit, *, include_production: bool = False) -> dict[str, Any]:
    payload = {
        "id": str(split.id),
        "order_id": str(split.order_id),
        "partner_id": str(split.partner_id),
        "partner_name": _partner_name(db, split.partner_id),
        "split_number": split.split_number,
        "split_status": split.split_status,
        "partner_reference_number": split.partner_reference_number,
        "supplier_confirmation_status": split.supplier_confirmation_status,
        "supplier_confirmed_at": split.supplier_confirmed_at.isoformat() if split.supplier_confirmed_at else None,
        "expected_production_start": str(split.expected_production_start) if split.expected_production_start else None,
        "expected_ready_date": str(split.expected_ready_date) if split.expected_ready_date else None,
        "line_item_count": split.line_item_count,
        "subtotal": str(split.subtotal),
        "currency": split.currency,
        "notes": split.notes,
        "created_at": split.created_at.isoformat() if split.created_at else None,
        "updated_at": split.updated_at.isoformat() if split.updated_at else None,
    }
    if include_production:
        from app.services.orders.production_milestone_service import split_milestone_summary

        payload.update(split_milestone_summary(db, split))
    return payload


def _next_split_number(existing_count: int) -> str:
    return f"SPLIT-{existing_count + 1}"


def _group_lines_by_partner(lines: list[OrderLineItem]) -> dict[UUID, list[OrderLineItem]]:
    groups: dict[UUID, list[OrderLineItem]] = defaultdict(list)
    for line in lines:
        if line.status != "cancelled":
            groups[line.partner_id].append(line)
    return groups


def get_partner_splits(db: Session, order_id: UUID) -> list[OrderPartnerSplit]:
    get_order(db, order_id)
    return (
        db.query(OrderPartnerSplit)
        .filter(OrderPartnerSplit.order_id == order_id)
        .order_by(OrderPartnerSplit.split_number.asc())
        .all()
    )


def get_partner_split(db: Session, order_id: UUID, split_id: UUID) -> OrderPartnerSplit:
    split = (
        db.query(OrderPartnerSplit)
        .filter(OrderPartnerSplit.id == split_id, OrderPartnerSplit.order_id == order_id)
        .first()
    )
    if not split:
        raise ApiError(NOT_FOUND, "Partner split not found", status_code=404)
    return split


def get_partner_split_detail(db: Session, order_id: UUID, split_id: UUID) -> dict[str, Any]:
    from app.services.orders.supplier_confirmation_service import confirmation_to_dict, list_supplier_confirmations

    order = get_order(db, order_id)
    split = get_partner_split(db, order_id, split_id)
    lines = [li for li in order.line_items if li.partner_id == split.partner_id and li.status != "cancelled"]
    confirmations = list_supplier_confirmations(db, order_id, split_id=split_id)
    payload = split_to_dict(db, split, include_production=True)
    payload["line_items"] = [_serialize_line(li) for li in sorted(lines, key=lambda x: x.created_at)]
    payload["supplier_confirmations"] = [confirmation_to_dict(c) for c in confirmations]
    payload["safety"] = split_safety()
    return payload


def partner_splits_summary(db: Session, order: CustomerOrder) -> dict[str, Any]:
    splits = get_partner_splits(db, order.id)
    confirmed = sum(1 for s in splits if s.supplier_confirmation_status == "confirmed")
    pending = sum(
        1
        for s in splits
        if s.supplier_confirmation_status in ("not_requested", "pending", "partially_confirmed")
    )
    needs_clarification = sum(1 for s in splits if s.supplier_confirmation_status == "needs_clarification")
    return {
        "total_splits": len(splits),
        "confirmed_splits": confirmed,
        "pending_splits": pending,
        "needs_clarification_splits": needs_clarification,
    }


def ensure_partner_splits(db: Session, user_id: UUID | None, order_id: UUID) -> dict[str, Any]:
    order = get_order(db, order_id)
    if order.status == "cancelled":
        raise ApiError(VALIDATION_ERROR, "Cancelled order cannot create partner splits", status_code=400)

    groups = _group_lines_by_partner(list(order.line_items))
    if not groups:
        raise ApiError(VALIDATION_ERROR, "Order has no line items to split", status_code=400)

    existing = {s.partner_id: s for s in get_partner_splits(db, order_id)}
    created = 0
    updated = 0
    next_num = len(existing)

    warnings: list[str] = []
    if order.status == "pending_customer_confirmation":
        warnings.append("Customer confirmation is not recorded; supplier actions should be reviewed.")

    for partner_id, lines in groups.items():
        subtotal = sum((li.total_price for li in lines), Decimal("0"))
        count = len(lines)
        split = existing.get(partner_id)
        if split:
            changed = split.line_item_count != count or split.subtotal != subtotal
            split.line_item_count = count
            split.subtotal = subtotal
            split.currency = order.currency
            if changed:
                updated += 1
                log_activity(
                    db,
                    object_type="customer_order",
                    object_id=order.id,
                    action="partner_split_updated",
                    actor_id=user_id,
                    diff={"split_id": str(split.id), "partner_id": str(partner_id)},
                )
        else:
            next_num += 1
            split = OrderPartnerSplit(
                order_id=order.id,
                partner_id=partner_id,
                split_number=f"SPLIT-{next_num}",
                split_status="pending_supplier_confirmation",
                supplier_confirmation_status="pending",
                line_item_count=count,
                subtotal=subtotal,
                currency=order.currency,
            )
            db.add(split)
            db.flush()
            created += 1
            log_activity(
                db,
                object_type="customer_order",
                object_id=order.id,
                action="partner_split_created",
                actor_id=user_id,
                diff={"split_id": str(split.id), "partner_id": str(partner_id)},
            )

    db.commit()
    splits = get_partner_splits(db, order_id)
    return {
        "order_id": str(order_id),
        "splits": [split_to_dict(db, s) for s in splits],
        "created": created,
        "updated": updated,
        "warnings": warnings,
        "safety": split_safety(),
    }
