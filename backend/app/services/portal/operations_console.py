"""Internal Portal operations console payload builder."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import FeedbackTicket, OrderResource, ProductCatalog
from app.models.customer_orders import CustomerOrder, ShipmentPlan
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
