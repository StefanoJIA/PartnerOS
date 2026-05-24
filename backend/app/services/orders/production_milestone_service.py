"""Production milestone service for customer orders (D7.5)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import NOT_FOUND, VALIDATION_ERROR, ApiError
from app.models import ManufacturingPartner, User
from app.models.customer_orders import (
    MILESTONE_STATUSES,
    CustomerOrder,
    OrderLineItem,
    OrderPartnerSplit,
    OrderProductionMilestone,
)
from app.services.activity import log_activity
from app.services.orders.order_service import get_order
from app.services.orders.partner_split_service import _partner_name, get_partner_split
from app.services.orders.production_templates import get_default_milestone_template

MILESTONE_SAFETY: dict[str, bool] = {
    "production_started": False,
    "shipment_created": False,
    "supplier_notified": False,
    "customer_notified": False,
    "automatic_sending_enabled": False,
    "lead_time_promised": False,
    "payment_received": False,
    "milestone_updated": False,
}


def milestone_safety(*, updated: bool = False) -> dict[str, bool]:
    return {**MILESTONE_SAFETY, "milestone_updated": updated}


def _parse_date(value: date | str | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def milestone_to_dict(row: OrderProductionMilestone) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "order_id": str(row.order_id),
        "partner_split_id": str(row.partner_split_id),
        "partner_id": str(row.partner_id),
        "milestone_type": row.milestone_type,
        "milestone_label": row.milestone_label,
        "sequence": row.sequence,
        "status": row.status,
        "planned_date": str(row.planned_date) if row.planned_date else None,
        "actual_date": str(row.actual_date) if row.actual_date else None,
        "responsible_party": row.responsible_party,
        "source": row.source,
        "notes": row.notes,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _primary_category(lines: list[OrderLineItem]) -> str | None:
    for line in lines:
        if line.product_category:
            return line.product_category
    return None


def _partner_code(db: Session, partner_id: UUID) -> tuple[str | None, str | None]:
    row = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == partner_id).first()
    if not row:
        return None, None
    return row.brand_name or row.partner_name, row.partner_type


def list_production_milestones(
    db: Session,
    order_id: UUID,
    *,
    partner_split_id: UUID | None = None,
    status: str | None = None,
    milestone_type: str | None = None,
) -> list[OrderProductionMilestone]:
    get_order(db, order_id)
    q = db.query(OrderProductionMilestone).filter(OrderProductionMilestone.order_id == order_id)
    if partner_split_id is not None:
        q = q.filter(OrderProductionMilestone.partner_split_id == partner_split_id)
    if status:
        q = q.filter(OrderProductionMilestone.status == status)
    if milestone_type:
        q = q.filter(OrderProductionMilestone.milestone_type == milestone_type)
    return q.order_by(OrderProductionMilestone.sequence.asc()).all()


def _split_progress(milestones: list[OrderProductionMilestone]) -> dict[str, Any]:
    completed = [m for m in milestones if m.status == "completed"]
    in_progress = [m for m in milestones if m.status == "in_progress"]
    current = in_progress[0] if in_progress else None
    next_m = None
    for m in milestones:
        if m.status in ("planned", "delayed", "blocked"):
            next_m = m
            break
    return {
        "production_milestone_count": len(milestones),
        "production_completed_count": len(completed),
        "current_milestone": milestone_to_dict(current) if current else None,
        "next_milestone": milestone_to_dict(next_m) if next_m else None,
    }


def production_summary(db: Session, order_id: UUID) -> dict[str, Any]:
    rows = list_production_milestones(db, order_id)
    ready_completed = any(
        m.milestone_type == "ready_to_ship" and m.status == "completed" for m in rows
    )
    return {
        "total_milestones": len(rows),
        "completed_milestones": sum(1 for m in rows if m.status == "completed"),
        "in_progress_milestones": sum(1 for m in rows if m.status == "in_progress"),
        "delayed_milestones": sum(1 for m in rows if m.status == "delayed"),
        "blocked_milestones": sum(1 for m in rows if m.status == "blocked"),
        "ready_to_ship_completed": ready_completed,
        "shipment_created": False,
    }


def split_milestone_summary(db: Session, split: OrderPartnerSplit) -> dict[str, Any]:
    rows = list_production_milestones(db, split.order_id, partner_split_id=split.id)
    return _split_progress(rows)


def ensure_production_milestones(
    db: Session,
    user: User,
    order_id: UUID,
    partner_split_id: UUID,
) -> dict[str, Any]:
    order = get_order(db, order_id)
    if order.status == "cancelled":
        raise ApiError(VALIDATION_ERROR, "Cancelled order cannot create production milestones", status_code=400)
    if order.status == "pending_customer_confirmation":
        raise ApiError(
            VALIDATION_ERROR,
            "Production milestones require customer-confirmed order",
            status_code=400,
        )

    split = get_partner_split(db, order_id, partner_split_id)
    if split.split_status == "cancelled":
        raise ApiError(VALIDATION_ERROR, "Cancelled partner split cannot create milestones", status_code=400)

    warnings: list[str] = []
    if split.supplier_confirmation_status != "confirmed":
        warnings.append(
            "supplier not fully confirmed; milestones are planning placeholders"
        )

    lines = [li for li in order.line_items if li.partner_id == split.partner_id and li.status != "cancelled"]
    category = _primary_category(lines)
    partner_code, partner_type = _partner_code(db, split.partner_id)
    template = get_default_milestone_template(partner_code, category, partner_type=partner_type)

    existing = {
        m.milestone_type: m
        for m in list_production_milestones(db, order_id, partner_split_id=partner_split_id)
    }
    created = 0
    for item in template:
        mtype = item["milestone_type"]
        if mtype in existing:
            continue
        row = OrderProductionMilestone(
            order_id=order.id,
            partner_split_id=split.id,
            partner_id=split.partner_id,
            milestone_type=mtype,
            milestone_label=item["milestone_label"],
            sequence=item["sequence"],
            status="planned",
            source="template",
            created_by_id=user.id,
        )
        db.add(row)
        created += 1

    if created:
        log_activity(
            db,
            object_type="customer_order",
            object_id=order.id,
            action="production_milestones_created",
            actor_id=user.id,
            diff={"split_id": str(split.id), "created": created},
        )

    db.commit()
    milestones = list_production_milestones(db, order_id, partner_split_id=partner_split_id)
    return {
        "order_id": str(order_id),
        "partner_split_id": str(partner_split_id),
        "milestones": [milestone_to_dict(m) for m in milestones],
        "created": created,
        "updated": 0,
        "warnings": warnings,
        "safety": milestone_safety(),
    }


def update_production_milestone(
    db: Session,
    user: User,
    order_id: UUID,
    milestone_id: UUID,
    *,
    status: str | None = None,
    planned_date: date | str | None = None,
    actual_date: date | str | None = None,
    responsible_party: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    order = get_order(db, order_id)
    if order.status == "cancelled":
        raise ApiError(VALIDATION_ERROR, "Cancelled order cannot update milestones", status_code=400)

    row = (
        db.query(OrderProductionMilestone)
        .filter(OrderProductionMilestone.id == milestone_id, OrderProductionMilestone.order_id == order_id)
        .first()
    )
    if not row:
        raise ApiError(NOT_FOUND, "Production milestone not found", status_code=404)

    warnings: list[str] = []
    if status is not None:
        if status not in MILESTONE_STATUSES:
            raise ApiError(VALIDATION_ERROR, f"Invalid milestone status: {status}", status_code=400)
        row.status = status

    if planned_date is not None:
        row.planned_date = _parse_date(planned_date)

    if actual_date is not None:
        row.actual_date = _parse_date(actual_date)

    if responsible_party is not None:
        row.responsible_party = responsible_party

    if notes is not None:
        row.notes = notes

    if row.status == "completed" and not row.actual_date:
        row.actual_date = date.today()
        warnings.append("actual_date auto-set to today for completed milestone")

    if row.planned_date and order.order_date and row.planned_date < order.order_date:
        warnings.append("planned_date is before order_date; subject to confirmation")

    if row.milestone_type == "ready_to_ship" and row.status == "completed":
        warnings.append("shipment still needs to be created in D7.6")

    log_activity(
        db,
        object_type="customer_order",
        object_id=order.id,
        action="production_milestone_completed" if row.status == "completed" else "production_milestone_updated",
        actor_id=user.id,
        diff={
            "milestone_id": str(row.id),
            "milestone_type": row.milestone_type,
            "status": row.status,
        },
    )

    db.commit()
    db.refresh(row)

    partner = _partner_name(db, row.partner_id)
    return {
        "milestone": row,
        "partner_name": partner,
        "warnings": warnings,
        "safety": milestone_safety(updated=True),
    }
