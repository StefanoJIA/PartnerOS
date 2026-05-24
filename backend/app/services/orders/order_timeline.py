"""Customer Order timeline builder (D7.2+)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import User
from app.models.customer_orders import OrderConfirmation, OrderPartnerSplit, SupplierConfirmation
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
