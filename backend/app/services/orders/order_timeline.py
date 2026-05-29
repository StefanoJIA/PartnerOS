"""Customer Order timeline builder (D7.2+)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ActivityLog, User
from app.models.customer_orders import (
    OrderConfirmation,
    OrderPartnerSplit,
    OrderProductionMilestone,
    ShipmentPlan,
    SupplierConfirmation,
)
from app.services.orders.order_service import get_order
from app.services.orders.partner_split_service import _partner_name


def _actor_name(user: User | None) -> str:
    if not user:
        return ""
    return user.email or str(user.id)


def build_order_timeline(db: Session, order_id: UUID) -> dict[str, Any]:
    order = get_order(db, order_id)
    items: list[dict[str, Any]] = []

    creator = None
    if order.created_by_id:
        creator = db.query(User).filter(User.id == order.created_by_id).first()

    if order.created_at:
        items.append(
            {
                "type": "order_created",
                "title": "Order created from quote",
                "timestamp": order.created_at.isoformat(),
                "actor": _actor_name(creator),
                "meta": {
                    "order_number": order.order_number,
                    "source_quote_id": str(order.source_quote_id),
                },
            }
        )

    confirmations = (
        db.query(OrderConfirmation)
        .filter(OrderConfirmation.order_id == order_id)
        .order_by(OrderConfirmation.confirmed_at.asc())
        .all()
    )
    for conf in confirmations:
        if conf.status == "active":
            items.append(
                {
                    "type": "customer_confirmation_added",
                    "title": "Customer confirmation recorded",
                    "timestamp": conf.confirmed_at.isoformat() if conf.confirmed_at else None,
                    "actor": "",
                    "meta": {
                        "confirmation_type": conf.confirmation_type,
                        "confirmation_strength": conf.confirmation_strength,
                        "confirmed_by_name": conf.confirmed_by_name,
                        "confirmation_id": str(conf.id),
                    },
                }
            )
        elif conf.status == "voided" and conf.voided_at:
            items.append(
                {
                    "type": "customer_confirmation_voided",
                    "title": "Customer confirmation voided",
                    "timestamp": conf.voided_at.isoformat(),
                    "actor": "",
                    "meta": {
                        "confirmation_id": str(conf.id),
                        "reason": conf.voided_reason,
                    },
                }
            )

    splits = (
        db.query(OrderPartnerSplit)
        .filter(OrderPartnerSplit.order_id == order_id)
        .order_by(OrderPartnerSplit.created_at.asc())
        .all()
    )
    for split in splits:
        partner = _partner_name(db, split.partner_id)
        items.append(
            {
                "type": "partner_split_created",
                "title": "Partner split created",
                "timestamp": split.created_at.isoformat() if split.created_at else None,
                "actor": "",
                "meta": {
                    "split_id": str(split.id),
                    "split_number": split.split_number,
                    "partner": partner,
                    "partner_id": str(split.partner_id),
                },
            }
        )
        if split.updated_at and split.created_at and split.updated_at > split.created_at:
            items.append(
                {
                    "type": "partner_split_updated",
                    "title": "Partner split updated",
                    "timestamp": split.updated_at.isoformat(),
                    "actor": "",
                    "meta": {
                        "split_id": str(split.id),
                        "split_number": split.split_number,
                        "partner": partner,
                    },
                }
            )

    supplier_rows = (
        db.query(SupplierConfirmation)
        .filter(SupplierConfirmation.order_id == order_id)
        .order_by(SupplierConfirmation.created_at.asc())
        .all()
    )
    for sc in supplier_rows:
        partner = _partner_name(db, sc.partner_id)
        if sc.status == "active":
            items.append(
                {
                    "type": "supplier_confirmation_added",
                    "title": "Supplier confirmation recorded",
                    "timestamp": sc.confirmed_at.isoformat() if sc.confirmed_at else (sc.created_at.isoformat() if sc.created_at else None),
                    "actor": "",
                    "meta": {
                        "partner": partner,
                        "confirmation_status": sc.confirmation_status,
                        "inventory_confirmed": sc.inventory_confirmed,
                        "lead_time_confirmed": sc.lead_time_confirmed,
                        "confirmation_id": str(sc.id),
                    },
                }
            )
        elif sc.status == "voided" and sc.voided_at:
            items.append(
                {
                    "type": "supplier_confirmation_voided",
                    "title": "Supplier confirmation voided",
                    "timestamp": sc.voided_at.isoformat(),
                    "actor": "",
                    "meta": {
                        "confirmation_id": str(sc.id),
                        "partner": partner,
                        "reason": sc.voided_reason,
                    },
                }
            )

    prod_milestones = (
        db.query(OrderProductionMilestone)
        .filter(OrderProductionMilestone.order_id == order_id)
        .order_by(OrderProductionMilestone.sequence.asc())
        .all()
    )
    splits_created: set[UUID] = set()
    for pm in prod_milestones:
        partner = _partner_name(db, pm.partner_id)
        if pm.partner_split_id not in splits_created:
            splits_created.add(pm.partner_split_id)
            items.append(
                {
                    "type": "production_milestones_created",
                    "title": "Production milestones created",
                    "timestamp": pm.created_at.isoformat() if pm.created_at else None,
                    "actor": "",
                    "meta": {
                        "partner": partner,
                        "partner_split_id": str(pm.partner_split_id),
                        "milestone_type": pm.milestone_type,
                    },
                }
            )
        if pm.updated_at and pm.created_at and pm.updated_at > pm.created_at:
            if pm.milestone_type == "ready_to_ship" and pm.status == "completed":
                event_type = "ready_to_ship_marked"
                title = "Ready to ship milestone completed"
            elif pm.status == "completed":
                event_type = "production_milestone_completed"
                title = "Production milestone completed"
            else:
                event_type = "production_milestone_updated"
                title = "Production milestone updated"
            items.append(
                {
                    "type": event_type,
                    "title": title,
                    "timestamp": pm.updated_at.isoformat(),
                    "actor": "",
                    "meta": {
                        "partner": partner,
                        "milestone_type": pm.milestone_type,
                        "status": pm.status,
                        "milestone_id": str(pm.id),
                    },
                }
            )

    shipment_logs = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.object_type == "customer_order",
            ActivityLog.object_id == order_id,
            ActivityLog.action.in_(("shipment_plan_created", "shipment_plan_updated", "shipment_status_changed")),
        )
        .order_by(ActivityLog.created_at.asc())
        .all()
    )
    for log in shipment_logs:
        diff = log.diff or {}
        title = {
            "shipment_plan_created": "Shipment plan created",
            "shipment_plan_updated": "Shipment plan updated",
            "shipment_status_changed": "Shipment status changed",
        }.get(log.action, "Shipment plan updated")
        items.append(
            {
                "type": log.action,
                "title": title,
                "timestamp": log.created_at.isoformat() if log.created_at else None,
                "actor": "",
                "meta": {
                    "shipment_plan_id": diff.get("shipment_plan_id"),
                    "previous_status": diff.get("previous_status"),
                    "status": diff.get("status"),
                },
            }
        )

    if not shipment_logs:
        shipment_plans = (
            db.query(ShipmentPlan)
            .filter(ShipmentPlan.order_id == order_id)
            .order_by(ShipmentPlan.created_at.asc())
            .all()
        )
        for plan in shipment_plans:
            items.append(
                {
                    "type": "shipment_plan_created",
                    "title": "Shipment plan created",
                    "timestamp": plan.created_at.isoformat() if plan.created_at else None,
                    "actor": "",
                    "meta": {
                        "shipment_plan_id": str(plan.id),
                        "status": plan.status,
                        "tracking_number": plan.tracking_number,
                    },
                }
            )

    if order.cancelled_at and order.status == "cancelled":
        items.append(
            {
                "type": "order_cancelled",
                "title": "Order cancelled",
                "timestamp": order.cancelled_at.isoformat(),
                "actor": "",
                "meta": {"reason": order.cancelled_reason},
            }
        )

    items.sort(key=lambda x: x.get("timestamp") or "")
    return {"items": items, "total": len(items)}
