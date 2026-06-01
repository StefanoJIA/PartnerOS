"""Customer-visible order snapshot for Portal consumption and operations."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import FeedbackTicket, OrderResource
from app.models.customer_orders import CustomerOrder, OrderProductionMilestone, ShipmentPlan
from app.services.portal.customer_field_filter import (
    assert_no_forbidden_internal_fields,
    strip_forbidden_internal_fields,
)
from app.services.portal.customer_contract import portal_customer_feedback_form_contract
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


def _customer_next_action(stage: str) -> dict[str, str]:
    actions = {
        "pending_confirmation": {
            "label": "Waiting for confirmation",
            "detail": "PartnerOS is waiting for the order confirmation before production tracking starts.",
        },
        "confirmed": {
            "label": "Preparing production",
            "detail": "The order is confirmed and the team is preparing supplier and production updates.",
        },
        "in_production": {
            "label": "Production update pending",
            "detail": "Production is in progress. Planned dates are progress guidance, not a guaranteed lead time.",
        },
        "ready_to_ship": {
            "label": "Shipment planning",
            "detail": "The order is ready to ship and logistics details will appear when an operator adds a shipment plan.",
        },
        "shipped": {
            "label": "Track shipment",
            "detail": "Shipment information is available from PartnerOS tracking records.",
        },
        "delivered": {
            "label": "Order delivered",
            "detail": "The order is marked delivered in PartnerOS tracking records.",
        },
        "cancelled": {
            "label": "Order cancelled",
            "detail": "The order is cancelled and no further customer tracking steps are planned.",
        },
    }
    return actions.get(
        stage,
        {
            "label": "Review order",
            "detail": "PartnerOS is reviewing the order status before the next customer-visible update.",
        },
    )


PROGRESS_STEPS = (
    ("confirmed", "Order confirmed"),
    ("in_production", "Production in progress"),
    ("ready_to_ship", "Ready to ship"),
    ("shipped", "Shipment in transit"),
    ("delivered", "Delivered"),
)

def _date_value(value: Any) -> str | None:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return None


def _milestone_date(
    production_rows: list[OrderProductionMilestone],
    *,
    milestone_type: str | None = None,
    status: str | None = None,
    field: str = "actual_date",
) -> str | None:
    for row in production_rows:
        if milestone_type and row.milestone_type != milestone_type:
            continue
        if status and row.status != status:
            continue
        value = getattr(row, field, None)
        if value:
            return _date_value(value)
    return None


def _shipment_date(shipment_rows: list[ShipmentPlan], *, status: str, field: str) -> str | None:
    for row in shipment_rows:
        if row.status == status:
            value = getattr(row, field, None)
            if value:
                return _date_value(value)
    return None


def _customer_progress_steps(
    stage: str,
    order: CustomerOrder | None,
    production_rows: list[OrderProductionMilestone],
    shipment_rows: list[ShipmentPlan],
) -> list[dict[str, Any]]:
    if stage == "cancelled":
        return [
            {
                "key": "cancelled",
                "label": "Order cancelled",
                "state": "current",
                "date": None,
                "planned_dates_are_guarantees": False,
            }
        ]
    stage_order = [item[0] for item in PROGRESS_STEPS]
    current_index = max(0, stage_order.index(stage) if stage in stage_order else 0)
    dates = {
        "confirmed": _date_value(getattr(order, "customer_confirmed_at", None)),
        "in_production": _milestone_date(production_rows, status="in_progress", field="actual_date")
        or _milestone_date(production_rows, status="completed", field="actual_date")
        or _milestone_date(production_rows, field="planned_date"),
        "ready_to_ship": _milestone_date(production_rows, milestone_type="ready_to_ship", status="completed", field="actual_date")
        or _milestone_date(production_rows, milestone_type="ready_to_ship", field="planned_date"),
        "shipped": _shipment_date(shipment_rows, status="shipped", field="actual_ship_date")
        or _shipment_date(shipment_rows, status="planned", field="estimated_ship_date"),
        "delivered": _shipment_date(shipment_rows, status="delivered", field="actual_arrival_date")
        or _shipment_date(shipment_rows, status="shipped", field="estimated_arrival_date")
        or _shipment_date(shipment_rows, status="planned", field="estimated_arrival_date"),
    }
    steps = []
    for index, (key, label) in enumerate(PROGRESS_STEPS):
        if index < current_index:
            state = "complete"
        elif index == current_index:
            state = "current"
        else:
            state = "pending"
        steps.append(
            {
                "key": key,
                "label": label,
                "state": state,
                "date": dates.get(key),
                "planned_dates_are_guarantees": False,
            }
        )
    return steps


def _portal_display(
    *,
    order_number: str | None,
    stage: str,
    status_label: str,
    next_action: dict[str, str],
    progress_steps: list[dict[str, Any]],
    tracking_summary: dict[str, Any],
    feedback_submit_path: str,
) -> dict[str, Any]:
    completed_steps = sum(1 for step in progress_steps if step.get("state") == "complete")
    current_step = next((step for step in progress_steps if step.get("state") == "current"), None)
    total_steps = len(progress_steps)
    progress_percent = int(((completed_steps + (1 if current_step else 0)) / total_steps) * 100) if total_steps else 0
    return {
        "headline": f"{order_number or 'Order'}: {status_label}",
        "stage": stage,
        "stage_label": status_label,
        "current_step_label": current_step.get("label") if current_step else status_label,
        "next_action_label": next_action["label"],
        "next_action_detail": next_action["detail"],
        "progress_percent": progress_percent,
        "signal_cards": [
            {
                "key": "production",
                "label": "Production",
                "active": bool(tracking_summary["has_production_updates"]),
                "count": int(tracking_summary["production_item_count"]),
            },
            {
                "key": "shipment",
                "label": "Shipment",
                "active": bool(tracking_summary["has_active_shipment"]),
                "count": int(tracking_summary["shipment_item_count"]),
            },
            {
                "key": "resources",
                "label": "Resources",
                "active": bool(tracking_summary["has_visible_resources"]),
                "count": int(tracking_summary["resource_visible_count"]),
            },
            {
                "key": "feedback",
                "label": "Feedback",
                "active": bool(tracking_summary["has_open_feedback"]),
                "count": int(tracking_summary["feedback_open_count"]),
            },
        ],
        "feedback_cta": {
            "label": "Send feedback",
            "path": feedback_submit_path,
            "customer_notified": False,
            "automatic_reply_sent": False,
            "resolution_time_promised": False,
        },
        "planned_dates_are_guarantees": False,
    }


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
    progress_steps = _customer_progress_steps(stage, order, production_rows, shipment_rows)
    next_action = _customer_next_action(stage)
    status_label = _customer_status_label(stage)
    production_statuses = _status_counts(production_rows)
    shipment_statuses = _status_counts(shipment_rows)
    order_id_text = str(order_id)
    links = {
        "order_detail": f"/api/v1/portal/customer/orders/{order_id_text}",
        "order_snapshot": f"/api/v1/portal/customer/orders/{order_id_text}/snapshot",
        "production": f"/api/v1/portal/customer/orders/{order_id_text}/production",
        "shipment": f"/api/v1/portal/customer/orders/{order_id_text}/shipment",
        "resources": f"/api/v1/portal/customer/orders/{order_id_text}/resources",
        "feedback_submit": "/api/v1/portal/customer/feedback",
    }
    tracking_summary = {
        "stage": stage,
        "production_item_count": len(production_rows),
        "shipment_item_count": sum(1 for row in shipment_rows if row.status != "cancelled"),
        "resource_visible_count": visible_resource_count,
        "feedback_open_count": open_feedback_count,
        "has_production_updates": bool(production_rows),
        "has_active_shipment": any(row.status != "cancelled" for row in shipment_rows),
        "has_visible_resources": visible_resource_count > 0,
        "has_open_feedback": open_feedback_count > 0,
        "planned_dates_are_guarantees": False,
    }

    payload = {
        "order": detail,
        "customer_status": {
            "stage": stage,
            "label": status_label,
            "next_action_label": next_action["label"],
            "next_action_detail": next_action["detail"],
            "order_confirmed": order_status
            in {"confirmed", "supplier_confirmation_pending", "supplier_confirmed", "production_pending", "in_production", "ready_to_ship", "shipped", "delivered"},
            "production_started": bool(production_rows),
            "production_completed": bool(production_rows) and all(row.status in {"completed", "skipped", "cancelled"} for row in production_rows),
            "ready_to_ship": stage in {"ready_to_ship", "shipped", "delivered"},
            "shipped": stage in {"shipped", "delivered"},
            "delivered": stage == "delivered",
            "current_step_index": next((idx for idx, step in enumerate(progress_steps) if step["state"] == "current"), 0),
            "progress_steps": progress_steps,
            "planned_dates_are_guarantees": False,
        },
        "tracking_summary": tracking_summary,
        "portal_display": _portal_display(
            order_number=detail.get("order_number"),
            stage=stage,
            status_label=status_label,
            next_action=next_action,
            progress_steps=progress_steps,
            tracking_summary=tracking_summary,
            feedback_submit_path=links["feedback_submit"],
        ),
        "links": links,
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
            **portal_customer_feedback_form_contract(),
            "total_count": feedback_count,
            "open_count": open_feedback_count,
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
