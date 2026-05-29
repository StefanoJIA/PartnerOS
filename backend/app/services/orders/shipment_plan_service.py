"""Shipment plan service for customer orders (D7.6)."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import NOT_FOUND, VALIDATION_ERROR, ApiError
from app.models import User
from app.models.customer_orders import SHIPMENT_PLAN_STATUSES, OrderPartnerSplit, ShipmentPlan
from app.services.activity import log_activity
from app.services.orders.order_service import get_order

SHIPMENT_SAFETY: dict[str, bool] = {
    "shipment_created": False,
    "supplier_notified": False,
    "customer_notified": False,
}

SHIPMENT_ALLOWED_ORDER_STATUSES = (
    "confirmed",
    "internal_review",
    "supplier_confirmation_pending",
    "supplier_confirmed",
    "production_pending",
    "in_production",
    "ready_to_ship",
    "shipped",
    "delivered",
    "on_hold",
)


def shipment_safety() -> dict[str, bool]:
    return dict(SHIPMENT_SAFETY)


def _parse_date(value: date | str | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _assert_order_can_create_shipment(status: str) -> None:
    if status == "cancelled":
        raise ApiError(VALIDATION_ERROR, "Cancelled order cannot create shipment plans", status_code=400)
    if status not in SHIPMENT_ALLOWED_ORDER_STATUSES:
        raise ApiError(
            VALIDATION_ERROR,
            "Shipment plan requires customer-confirmed order",
            status_code=400,
        )


def _assert_split_belongs_to_order(db: Session, order_id: UUID, split_id: UUID | None) -> None:
    if split_id is None:
        return
    found = (
        db.query(OrderPartnerSplit)
        .filter(OrderPartnerSplit.id == split_id, OrderPartnerSplit.order_id == order_id)
        .first()
    )
    if not found:
        raise ApiError(VALIDATION_ERROR, "partner_split_id does not belong to this order", status_code=400)


def shipment_plan_to_dict(row: ShipmentPlan) -> dict[str, Any]:
    portal_visible_fields = {
        "status": row.status,
        "shipment_method": row.shipment_method,
        "estimated_ship_date": str(row.estimated_ship_date) if row.estimated_ship_date else None,
        "estimated_arrival_date": str(row.estimated_arrival_date) if row.estimated_arrival_date else None,
        "tracking_number": row.tracking_number,
    }
    return {
        "id": str(row.id),
        "order_id": str(row.order_id),
        "partner_split_id": str(row.partner_split_id) if row.partner_split_id else None,
        "shipment_method": row.shipment_method,
        "incoterm": row.incoterm,
        "origin": row.origin,
        "destination": row.destination,
        "estimated_ship_date": str(row.estimated_ship_date) if row.estimated_ship_date else None,
        "estimated_arrival_date": str(row.estimated_arrival_date) if row.estimated_arrival_date else None,
        "tracking_number": row.tracking_number,
        "status": row.status,
        "notes": row.notes,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "portal_visible_fields": portal_visible_fields,
        "safety": shipment_safety(),
    }


def shipment_summary(db: Session, order_id: UUID) -> dict[str, Any]:
    rows = list_shipment_plans(db, order_id)
    active = [r for r in rows if r.status != "cancelled"]
    return {
        "total_plans": len(rows),
        "active_plans": len(active),
        "shipped_plans": sum(1 for r in rows if r.status == "shipped"),
        "delivered_plans": sum(1 for r in rows if r.status == "delivered"),
        "shipment_created": False,
    }


def list_shipment_plans(
    db: Session,
    order_id: UUID,
    *,
    partner_split_id: UUID | None = None,
    status: str | None = None,
) -> list[ShipmentPlan]:
    get_order(db, order_id)
    q = db.query(ShipmentPlan).filter(ShipmentPlan.order_id == order_id)
    if partner_split_id is not None:
        q = q.filter(ShipmentPlan.partner_split_id == partner_split_id)
    if status:
        q = q.filter(ShipmentPlan.status == status)
    return q.order_by(ShipmentPlan.created_at.desc()).all()


def create_shipment_plan(
    db: Session,
    user: User,
    order_id: UUID,
    *,
    partner_split_id: UUID | None = None,
    shipment_method: str | None = None,
    incoterm: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
    estimated_ship_date: date | str | None = None,
    estimated_arrival_date: date | str | None = None,
    tracking_number: str | None = None,
    status: str = "draft",
    notes: str | None = None,
) -> ShipmentPlan:
    order = get_order(db, order_id)
    _assert_order_can_create_shipment(order.status)
    _assert_split_belongs_to_order(db, order.id, partner_split_id)
    if status not in SHIPMENT_PLAN_STATUSES:
        raise ApiError(VALIDATION_ERROR, f"Invalid shipment status: {status}", status_code=400)

    row = ShipmentPlan(
        order_id=order.id,
        partner_split_id=partner_split_id,
        shipment_method=shipment_method,
        incoterm=incoterm,
        origin=origin,
        destination=destination,
        estimated_ship_date=_parse_date(estimated_ship_date),
        estimated_arrival_date=_parse_date(estimated_arrival_date),
        tracking_number=tracking_number,
        status=status,
        notes=notes,
        created_by_id=user.id,
    )
    db.add(row)
    db.flush()
    log_activity(
        db,
        object_type="customer_order",
        object_id=order.id,
        action="shipment_plan_created",
        actor_id=user.id,
        diff={"shipment_plan_id": str(row.id), "status": row.status},
    )
    db.commit()
    db.refresh(row)
    return row


def update_shipment_plan(
    db: Session,
    user: User,
    order_id: UUID,
    plan_id: UUID,
    **fields: Any,
) -> ShipmentPlan:
    order = get_order(db, order_id)
    if order.status == "cancelled":
        raise ApiError(VALIDATION_ERROR, "Cancelled order cannot update shipment plans", status_code=400)

    row = (
        db.query(ShipmentPlan)
        .filter(ShipmentPlan.id == plan_id, ShipmentPlan.order_id == order_id)
        .first()
    )
    if not row:
        raise ApiError(NOT_FOUND, "Shipment plan not found", status_code=404)

    previous_status = row.status
    if "partner_split_id" in fields:
        _assert_split_belongs_to_order(db, order.id, fields["partner_split_id"])

    date_fields = {"estimated_ship_date", "estimated_arrival_date"}
    for key, value in fields.items():
        if key == "status" and value is not None and value not in SHIPMENT_PLAN_STATUSES:
            raise ApiError(VALIDATION_ERROR, f"Invalid shipment status: {value}", status_code=400)
        if key in date_fields:
            setattr(row, key, _parse_date(value))
        else:
            setattr(row, key, value)

    event = "shipment_status_changed" if row.status != previous_status else "shipment_plan_updated"
    log_activity(
        db,
        object_type="customer_order",
        object_id=order.id,
        action=event,
        actor_id=user.id,
        diff={
            "shipment_plan_id": str(row.id),
            "previous_status": previous_status,
            "status": row.status,
        },
    )
    db.commit()
    db.refresh(row)
    return row


def cancel_shipment_plan(db: Session, user: User, order_id: UUID, plan_id: UUID) -> ShipmentPlan:
    return update_shipment_plan(db, user, order_id, plan_id, status="cancelled")
