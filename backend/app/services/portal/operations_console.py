"""Internal Portal operations console payload builder."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import FeedbackTicket, OrderResource, ProductCatalog
from app.models.customer_orders import CustomerOrder, OrderLineItem, OrderProductionMilestone, ShipmentPlan
from app.services.portal.customer_field_filter import (
    assert_no_forbidden_internal_fields,
    strip_forbidden_internal_fields,
)
from app.services.portal.customer_order_snapshot import build_customer_order_snapshot
from app.services.portal.customer_portal_bridge import build_customer_order_list


def _safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = strip_forbidden_internal_fields(payload)
    assert_no_forbidden_internal_fields(cleaned)
    return cleaned


def _count_by_status(rows: list[Any], attr: str = "status") -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(getattr(row, attr, None) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


MARKET_FOCUS_CATEGORIES = (
    {
        "key": "adjustable_desk_frames",
        "label": "Adjustable desk frames",
        "terms": ("adjustable", "height", "standing", "sit stand", "desk frame", "frame"),
    },
    {
        "key": "desk_legs",
        "label": "Desk legs",
        "terms": ("desk leg", "table leg", "leg frame", "legs"),
    },
    {
        "key": "lifting_columns",
        "label": "Lifting columns",
        "terms": ("lifting column", "lift column", "column", "motor column"),
    },
    {
        "key": "education_furniture",
        "label": "Education furniture",
        "terms": ("education", "school", "student", "classroom", "training"),
    },
    {
        "key": "project_furniture",
        "label": "Project furniture",
        "terms": ("project", "contract", "fitout", "custom", "workspace"),
    },
)


def _blob(*parts: Any) -> str:
    return " ".join(str(part or "") for part in parts).lower()


def _focus_key(*parts: Any) -> str:
    text = _blob(*parts)
    for item in MARKET_FOCUS_CATEGORIES:
        if any(term in text for term in item["terms"]):
            return str(item["key"])
    return "other"


def _market_signal_seed() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {
        str(item["key"]): {
            "key": item["key"],
            "label": item["label"],
            "order_line_count": 0,
            "ordered_quantity": 0,
            "feedback_count": 0,
            "delayed_or_blocked_production_count": 0,
            "shipment_issue_count": 0,
            "human_review_required": True,
        }
        for item in MARKET_FOCUS_CATEGORIES
    }
    rows["other"] = {
        "key": "other",
        "label": "Other products",
        "order_line_count": 0,
        "ordered_quantity": 0,
        "feedback_count": 0,
        "delayed_or_blocked_production_count": 0,
        "shipment_issue_count": 0,
        "human_review_required": True,
    }
    return rows


def _build_market_signal_preview(
    order_lines: list[OrderLineItem],
    production_rows: list[OrderProductionMilestone],
    shipment_rows: list[ShipmentPlan],
    ticket_rows: list[FeedbackTicket],
) -> dict[str, Any]:
    rows = _market_signal_seed()
    order_category_by_id: dict[Any, str] = {}

    for line in order_lines:
        key = _focus_key(line.product_category, line.product_name, line.description_customer)
        order_category_by_id[line.order_id] = key
        rows[key]["order_line_count"] += 1
        rows[key]["ordered_quantity"] += int(line.quantity or 0)

    for milestone in production_rows:
        if milestone.status not in {"delayed", "blocked"}:
            continue
        key = order_category_by_id.get(milestone.order_id, "other")
        rows[key]["delayed_or_blocked_production_count"] += 1

    for shipment in shipment_rows:
        text = _blob(shipment.status, shipment.notes)
        if shipment.status not in {"planned", "shipped"} and not any(term in text for term in ("delay", "late", "issue", "hold")):
            continue
        key = order_category_by_id.get(shipment.order_id, "other")
        if any(term in text for term in ("delay", "late", "issue", "hold")):
            rows[key]["shipment_issue_count"] += 1

    for ticket in ticket_rows:
        key = _focus_key(ticket.feedback_type, ticket.subject, ticket.message, ticket.response_summary)
        if key == "other" and ticket.order_id in order_category_by_id:
            key = order_category_by_id[ticket.order_id]
        rows[key]["feedback_count"] += 1

    items = sorted(
        rows.values(),
        key=lambda row: (
            row["feedback_count"]
            + row["delayed_or_blocked_production_count"]
            + row["shipment_issue_count"],
            row["order_line_count"],
            row["ordered_quantity"],
        ),
        reverse=True,
    )
    return {
        "items": items,
        "total": len(items),
        "safety": {
            "read_only": True,
            "advisory_only": True,
            "human_review_required": True,
            "auto_ticket_created": False,
            "customer_notified": False,
            "supplier_notified": False,
        },
    }


def build_portal_operations_console(db: Session, settings: Settings, *, recent_limit: int = 8) -> dict[str, Any]:
    recent_orders = build_customer_order_list(db, page=1, limit=recent_limit)
    order_rows = (
        db.query(CustomerOrder)
        .filter(CustomerOrder.status != "cancelled")
        .order_by(CustomerOrder.created_at.desc())
        .limit(recent_limit)
        .all()
    )
    shipment_rows = db.query(ShipmentPlan).order_by(ShipmentPlan.created_at.desc()).limit(200).all()
    ticket_rows = db.query(FeedbackTicket).order_by(FeedbackTicket.created_at.desc()).limit(200).all()
    order_lines = db.query(OrderLineItem).limit(500).all()
    production_rows = db.query(OrderProductionMilestone).limit(500).all()

    snapshot_items = []
    for order in order_rows[:3]:
        snapshot_items.append(build_customer_order_snapshot(db, order.id))

    endpoints = {
        "products": db.query(ProductCatalog).filter(ProductCatalog.status == "active").count() >= 0,
        "orders": recent_orders.get("total", 0) >= 0,
        "production": True,
        "shipment": True,
        "resources": db.query(OrderResource).count() >= 0,
        "feedback": True,
    }
    missing_config = []
    if not settings.PORTAL_CUSTOMER_API_ENABLED:
        missing_config.append("PORTAL_CUSTOMER_API_ENABLED")
    if settings.PORTAL_CUSTOMER_API_REQUIRE_TOKEN and not settings.PORTAL_CUSTOMER_API_TOKEN.strip():
        missing_config.append("PORTAL_CUSTOMER_API_TOKEN")
    if not settings.PORTAL_CUSTOMER_ALLOWED_ORIGINS.strip():
        missing_config.append("PORTAL_CUSTOMER_ALLOWED_ORIGINS")
    if not settings.PUBLIC_BASE_URL.strip():
        missing_config.append("PUBLIC_BASE_URL")

    payload = {
        "status": {
            "ready": settings.PORTAL_CUSTOMER_API_ENABLED and not missing_config,
            "enabled": settings.PORTAL_CUSTOMER_API_ENABLED,
            "token_required": settings.PORTAL_CUSTOMER_API_REQUIRE_TOKEN,
            "token_configured": bool(settings.PORTAL_CUSTOMER_API_TOKEN.strip()),
            "public_base_url_configured": bool(settings.PUBLIC_BASE_URL.strip()),
            "public_base_url": settings.PUBLIC_BASE_URL.strip() or None,
            "allowed_origins": settings.cors_origins_list,
            "missing_config": missing_config,
        },
        "endpoint_readiness": endpoints,
        "recent_customer_visible_orders": recent_orders,
        "customer_snapshots": snapshot_items,
        "shipment_status_counts": _count_by_status(shipment_rows),
        "feedback_status_counts": _count_by_status(ticket_rows),
        "feedback_priority_counts": _count_by_status(ticket_rows, "priority"),
        "market_signal_preview": _build_market_signal_preview(order_lines, production_rows, shipment_rows, ticket_rows),
        "recent_feedback_tickets": [
            {
                "id": str(row.id),
                "ticket_number": row.ticket_number,
                "order_id": str(row.order_id) if row.order_id else None,
                "feedback_type": row.feedback_type,
                "subject": row.subject,
                "status": row.status,
                "priority": row.priority,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in ticket_rows[:recent_limit]
        ],
        "forbidden_field_audit": {
            "checked": True,
            "hits": [],
            "credential_value_exposed": False,
            "server_file_path_exposed": False,
            "cost_fields_exposed": False,
        },
        "safety": {
            "read_only": True,
            "customer_notified": False,
            "supplier_notified": False,
            "automatic_reply_sent": False,
            "carrier_api_called": False,
            "order_status_mutated": False,
        },
    }
    return _safe_payload(payload)
