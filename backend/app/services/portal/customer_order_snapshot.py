"""Customer-visible order snapshot for Portal consumption and operations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import FeedbackTicket, OrderResource
from app.models.customer_orders import CustomerOrder, OrderProductionMilestone, ShipmentPlan
from app.services.portal.customer_field_filter import (
    assert_no_forbidden_internal_fields,
    strip_forbidden_internal_fields,
)
from app.services.portal.customer_portal_bridge import (
    build_customer_order_detail,
    build_customer_production_view,
    build_customer_shipment_view,
)
from app.services.portal.order_resource_service import list_customer_order_resources


def _safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = strip_forbidden_internal_fields(payload)
    assert_no_forbidden_internal_fields(cleaned)
    return cleaned


def _status_counts(rows: list[Any], attr: str = "status") -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(getattr(row, attr, None) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _customer_stage(order_status: str, production_rows: list[OrderProductionMilestone], shipment_rows: list[ShipmentPlan]) -> str:
    active_shipments = [row for row in shipment_rows if row.status != "cancelled"]
    if any(row.status == "delivered" for row in active_shipments) or order_status == "delivered":
        return "delivered"
    if any(row.status == "shipped" for row in active_shipments) or order_status == "shipped":
        return "shipped"
    if order_status == "ready_to_ship" or any(row.status == "completed" and row.milestone_type == "ready_to_ship" for row in production_rows):
        return "ready_to_ship"
    if any(row.status in {"in_progress", "completed", "delayed", "blocked"} for row in production_rows):
        return "in_production"
    if order_status in {"confirmed", "supplier_confirmed", "production_pending"}:
        return "confirmed"
    if order_status == "cancelled":
        return "cancelled"
    return "pending_confirmation"


def _customer_status_label(stage: str) -> str:
    labels = {
        "pending_confirmation": "Waiting for order confirmation",
        "confirmed": "Order confirmed",
        "in_production": "Production in progress",
        "ready_to_ship": "Ready to ship",
        "shipped": "Shipment in transit",
        "delivered": "Delivered",
        "cancelled": "Cancelled",
    }
    return labels.get(stage, "Order in review")


def build_customer_order_snapshot(db: Session, order_id: UUID) -> dict[str, Any]:
    detail = build_customer_order_detail(db, order_id)
    production = build_customer_production_view(db, order_id)
    shipment = build_customer_shipment_view(db, order_id)
    resources = list_customer_order_resources(db, order_id)

    order = db.query(CustomerOrder).filter(CustomerOrder.id == order_id).first()
    production_rows = (
        db.query(OrderProductionMilestone)
        .filter(OrderProductionMilestone.order_id == order_id)
        .order_by(OrderProductionMilestone.sequence.asc())
        .all()
    )
    shipment_rows = (
        db.query(ShipmentPlan)
        .filter(ShipmentPlan.order_id == order_id)
        .order_by(ShipmentPlan.created_at.desc())
        .all()
    )
    feedback_count = db.query(FeedbackTicket).filter(FeedbackTicket.order_id == order_id).count()
    open_feedback_count = (
        db.query(FeedbackTicket)
        .filter(FeedbackTicket.order_id == order_id, FeedbackTicket.status.in_(("new", "in_review", "responded")))
        .count()
    )
    visible_resource_count = (
        db.query(OrderResource)
        .filter(
            OrderResource.order_id == order_id,
            OrderResource.status == "published",
            OrderResource.customer_visible.is_(True),
        )
        .count()
    )

    order_status = getattr(order, "status", detail.get("status") or "unknown")
    stage = _customer_stage(order_status, production_rows, shipment_rows)
    production_statuses = _status_counts(production_rows)
    shipment_statuses = _status_counts(shipment_rows)

    payload = {
        "order": detail,
        "customer_status": {
            "stage": stage,
            "label": _customer_status_label(stage),
            "order_confirmed": order_status
            in {"confirmed", "supplier_confirmation_pending", "supplier_confirmed", "production_pending", "in_production", "ready_to_ship", "shipped", "delivered"},
            "production_started": bool(production_rows),
            "production_completed": bool(production_rows) and all(row.status in {"completed", "skipped", "cancelled"} for row in production_rows),
            "ready_to_ship": stage in {"ready_to_ship", "shipped", "delivered"},
            "shipped": stage in {"shipped", "delivered"},
            "delivered": stage == "delivered",
            "planned_dates_are_guarantees": False,
        },
        "production": {
            **production,
            "status_counts": production_statuses,
            "blocked_count": production_statuses.get("blocked", 0),
            "delayed_count": production_statuses.get("delayed", 0),
        },
        "shipment": {
            **shipment,
            "status_counts": shipment_statuses,
            "active_count": sum(1 for row in shipment_rows if row.status != "cancelled"),
        },
        "resources": {
            **resources,
            "visible_count": visible_resource_count,
        },
        "feedback": {
            "submit_endpoint": "/api/v1/portal/customer/feedback",
            "total_count": feedback_count,
            "open_count": open_feedback_count,
            "customer_notified": False,
            "automatic_reply_sent": False,
        },
        "safety": {
            "customer_visible_only": True,
            "forbidden_field_filter_enabled": True,
            "cost_fields_exposed": False,
            "private_supplier_fields_exposed": False,
            "server_file_path_exposed": False,
            "customer_notified": False,
        },
    }
    return _safe_payload(payload)
