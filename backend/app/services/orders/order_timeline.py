"""Customer Order timeline builder (D7.2)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import User
from app.services.orders.order_service import get_order


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
                    "initial_status": order.status if order.status == "pending_customer_confirmation" else "pending_customer_confirmation",
                },
            }
        )

    if order.customer_confirmed_at and order.status == "confirmed":
        items.append(
            {
                "type": "customer_confirmed",
                "title": "Customer confirmation recorded",
                "timestamp": order.customer_confirmed_at.isoformat(),
                "actor": "",
                "meta": {
                    "confirmation_type": order.customer_confirmation_method,
                    "note": order.customer_confirmation_note,
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
