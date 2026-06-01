"""Internal Portal operations console payload builder."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database_lifecycle import check_database, get_migration_revisions
from app.models import FeedbackTicket, OrderResource, ProductCatalog
from app.models.customer_orders import CustomerOrder, OrderLineItem, OrderProductionMilestone, ShipmentPlan
from app.services.portal.customer_field_filter import (
    FORBIDDEN_FIELD_NAMES,
    FORBIDDEN_TEXT_MARKERS,
)
from app.services.portal.customer_order_snapshot import build_customer_order_snapshot
from app.services.portal.customer_portal_bridge import build_customer_order_list
from app.services.portal.feedback_ticket_service import OPEN_FEEDBACK_STATUSES, feedback_operation_flags


SAFE_OPERATION_METADATA_KEYS = {
    "token_required",
    "token_configured",
    "token_value_exposed",
    "credential_value_exposed",
}


def _strip_operations_payload(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            lowered = key.lower()
            if lowered in FORBIDDEN_FIELD_NAMES and lowered not in SAFE_OPERATION_METADATA_KEYS:
                continue
            if any(marker in lowered for marker in ("secret", "password")):
                continue
            if lowered in {"token", "api_token", "portal_customer_api_token"}:
                continue
            cleaned[key] = _strip_operations_payload(item)
        return cleaned
    if isinstance(value, list):
        return [_strip_operations_payload(item) for item in value]
    return value


def _safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = _strip_operations_payload(payload)
    text = str(cleaned).lower()
    for marker in FORBIDDEN_TEXT_MARKERS:
        if marker == "portal_customer_api_token":
            continue
        if marker in text:
            raise ValueError(f"Forbidden portal operations field leaked: {marker}")
    return cleaned


def _audit_forbidden_fields(value: Any) -> dict[str, Any]:
    hits: set[str] = set()

    def walk(item: Any, path: str = "$") -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                lowered = key.lower()
                child_path = f"{path}.{key}"
                if lowered in FORBIDDEN_FIELD_NAMES and lowered not in SAFE_OPERATION_METADATA_KEYS:
                    hits.add(f"{child_path}:forbidden_key")
                if any(marker in lowered for marker in ("secret", "password")):
                    hits.add(f"{child_path}:forbidden_key")
                if lowered in {"token", "api_token", "portal_customer_api_token"}:
                    hits.add(f"{child_path}:forbidden_key")
                walk(child, child_path)
            return
        if isinstance(item, list):
            for index, child in enumerate(item):
                walk(child, f"{path}[{index}]")
            return
        if isinstance(item, str):
            lowered = item.lower()
            for marker in FORBIDDEN_TEXT_MARKERS:
                if marker == "portal_customer_api_token":
                    continue
                if marker in lowered:
                    hits.add(f"{path}:{marker}")

    walk(value)
    return {
        "checked": True,
        "checked_payloads": [
            "recent_customer_visible_orders",
            "customer_snapshots",
            "portal_contract",
        ],
        "hits": sorted(hits),
        "credential_value_exposed": any("token" in hit or "secret" in hit or "password" in hit for hit in hits),
        "server_file_path_exposed": any("backend/storage" in hit or "local_data" in hit or "storage_key" in hit for hit in hits),
        "cost_fields_exposed": any("cost" in hit or "margin" in hit or "pricing_breakdown" in hit for hit in hits),
    }


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


def _build_feedback_operations(ticket_rows: list[FeedbackTicket]) -> dict[str, Any]:
    open_rows = [row for row in ticket_rows if row.status in OPEN_FEEDBACK_STATUSES]
    high_priority_rows = [row for row in ticket_rows if row.priority in {"high", "urgent"}]
    flags = [feedback_operation_flags(row) for row in ticket_rows]
    return {
        "total_count": len(ticket_rows),
        "open_count": len(open_rows),
        "high_priority_count": len(high_priority_rows),
        "needs_internal_review_count": sum(1 for item in flags if item["needs_internal_review"]),
        "response_summary_missing_count": sum(1 for item in flags if item["response_summary_missing"]),
        "ready_to_close_count": sum(1 for row in ticket_rows if row.status == "resolved"),
        "oldest_open_age_days": max(
            (
                int(item["age_days"])
                for row, item in zip(ticket_rows, flags, strict=False)
                if row.status in OPEN_FEEDBACK_STATUSES and item["age_days"] is not None
            ),
            default=None,
        ),
        "safety": {
            "internal_queue_only": True,
            "customer_notified": False,
            "automatic_reply_sent": False,
            "sla_promised": False,
        },
    }


def _build_customer_snapshot_readiness(snapshot_items: list[dict[str, Any]]) -> dict[str, Any]:
    stage_counts: dict[str, int] = {}
    missing_progress_count = 0
    production_visible_count = 0
    ready_to_ship_count = 0
    shipped_count = 0
    delivered_count = 0
    active_shipment_count = 0
    open_feedback_count = 0

    for snapshot in snapshot_items:
        customer_status = snapshot.get("customer_status", {})
        stage = str(customer_status.get("stage") or "unknown")
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
        progress_steps = customer_status.get("progress_steps") or []
        if not progress_steps:
            missing_progress_count += 1
        if customer_status.get("production_started") or customer_status.get("production_completed"):
            production_visible_count += 1
        if customer_status.get("ready_to_ship"):
            ready_to_ship_count += 1
        if customer_status.get("shipped"):
            shipped_count += 1
        if customer_status.get("delivered"):
            delivered_count += 1
        active_shipment_count += int(snapshot.get("shipment", {}).get("active_count") or 0)
        open_feedback_count += int(snapshot.get("feedback", {}).get("open_count") or 0)

    return {
        "snapshot_count": len(snapshot_items),
        "stage_counts": stage_counts,
        "missing_progress_count": missing_progress_count,
        "production_visible_count": production_visible_count,
        "ready_to_ship_count": ready_to_ship_count,
        "shipped_count": shipped_count,
        "delivered_count": delivered_count,
        "active_shipment_count": active_shipment_count,
        "open_feedback_count": open_feedback_count,
        "portal_ready": bool(snapshot_items) and missing_progress_count == 0,
        "safety": {
            "customer_visible_only": True,
            "forbidden_field_filter_enabled": True,
            "planned_dates_are_guarantees": False,
            "customer_notified": False,
            "order_status_mutated": False,
        },
    }


def _build_resource_readiness(resource_rows: list[OrderResource]) -> dict[str, Any]:
    status_counts = _count_by_status(resource_rows)
    category_counts = _count_by_status(resource_rows, "category")
    customer_visible_count = sum(1 for row in resource_rows if row.customer_visible)
    portal_visible_count = sum(1 for row in resource_rows if row.status == "published" and row.customer_visible)
    blocked_visibility_count = sum(1 for row in resource_rows if row.customer_visible and row.status != "published")
    hidden_published_count = sum(1 for row in resource_rows if row.status == "published" and not row.customer_visible)
    return {
        "total_count": len(resource_rows),
        "portal_visible_count": portal_visible_count,
        "customer_visible_count": customer_visible_count,
        "blocked_visibility_count": blocked_visibility_count,
        "hidden_published_count": hidden_published_count,
        "status_counts": status_counts,
        "category_counts": category_counts,
        "ready": portal_visible_count > 0,
        "safety": {
            "metadata_only": True,
            "download_links_signed": True,
            "file_location_exposed": False,
            "filesystem_path_exposed": False,
            "customer_notified": False,
            "automatic_email_sent": False,
        },
    }


def _build_portal_launch_readiness(
    *,
    status: dict[str, Any],
    runtime_health: dict[str, Any],
    endpoints: dict[str, bool],
    forbidden_field_audit: dict[str, Any],
    customer_snapshot_readiness: dict[str, Any],
    resource_readiness: dict[str, Any],
    feedback_operations: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    if not status["enabled"]:
        blockers.append("portal api disabled")
    if status["token_required"] and not status["token_configured"]:
        blockers.append("portal customer token missing")
    if not status["public_base_url_configured"]:
        blockers.append("public base url missing")
    if status["missing_config"]:
        blockers.extend(f"missing config: {item}" for item in status["missing_config"])
    if not runtime_health["database_ready"]:
        blockers.append("database not ready")
    if runtime_health["migration_pending"]:
        blockers.append("alembic migration pending")
    for name, ready in endpoints.items():
        if not ready:
            blockers.append(f"endpoint not ready: {name}")
    if forbidden_field_audit["hits"]:
        blockers.append("forbidden customer-visible field audit hit")
    if not customer_snapshot_readiness["portal_ready"]:
        warnings.append("customer order snapshots need representative progress data")
    if resource_readiness["blocked_visibility_count"]:
        warnings.append("customer-visible resources need publishing")
    if not resource_readiness["ready"]:
        warnings.append("no portal-visible resources available")
    if feedback_operations["needs_internal_review_count"]:
        warnings.append("feedback tickets need internal review")

    return {
        "ready_for_real_staging": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "checks": {
            "portal_api_enabled": status["enabled"],
            "token_configured": status["token_configured"],
            "public_base_url_configured": status["public_base_url_configured"],
            "runtime_ok": runtime_health["ok"],
            "all_endpoints_ready": all(endpoints.values()),
            "forbidden_field_audit_clear": not forbidden_field_audit["hits"],
            "customer_snapshots_ready": customer_snapshot_readiness["portal_ready"],
            "resources_ready": resource_readiness["ready"],
            "feedback_queue_clear": feedback_operations["needs_internal_review_count"] == 0,
        },
        "safety": {
            "read_only": True,
            "staging_validated": False,
            "customer_notified": False,
            "supplier_notified": False,
            "automatic_reply_sent": False,
            "carrier_api_called": False,
            "token_value_exposed": False,
        },
    }


def _build_portal_contract(settings: Settings, endpoints: dict[str, bool], missing_config: list[str]) -> dict[str, Any]:
    return {
        "base_url": settings.PUBLIC_BASE_URL.strip() or None,
        "server_to_server_auth": {
            "required": settings.PORTAL_CUSTOMER_API_REQUIRE_TOKEN,
            "header_name": "X-Portal-Customer-Token",
            "bearer_authorization_supported": True,
            "token_configured": bool(settings.PORTAL_CUSTOMER_API_TOKEN.strip()),
            "token_value_exposed": False,
        },
        "allowed_origins": settings.cors_origins_list,
        "missing_config": missing_config,
        "endpoints": [
            {"name": "manifest", "method": "GET", "path": "/api/v1/portal/customer/manifest", "ready": True},
            {"name": "products", "method": "GET", "path": "/api/v1/portal/customer/products", "ready": endpoints["products"]},
            {"name": "orders", "method": "GET", "path": "/api/v1/portal/customer/orders", "ready": endpoints["orders"]},
            {
                "name": "order_snapshot",
                "method": "GET",
                "path": "/api/v1/portal/customer/orders/{order_id}/snapshot",
                "ready": endpoints["orders"] and endpoints["production"] and endpoints["shipment"] and endpoints["resources"],
            },
            {
                "name": "production",
                "method": "GET",
                "path": "/api/v1/portal/customer/orders/{order_id}/production",
                "ready": endpoints["production"],
            },
            {
                "name": "shipment",
                "method": "GET",
                "path": "/api/v1/portal/customer/orders/{order_id}/shipment",
                "ready": endpoints["shipment"],
            },
            {
                "name": "resources",
                "method": "GET",
                "path": "/api/v1/portal/customer/orders/{order_id}/resources",
                "ready": endpoints["resources"],
            },
            {"name": "feedback", "method": "POST", "path": "/api/v1/portal/customer/feedback", "ready": endpoints["feedback"]},
        ],
        "safety": {
            "customer_visible_fields_only": True,
            "forbidden_field_filter_enabled": True,
            "token_value_exposed": False,
            "automatic_customer_notification": False,
            "carrier_api_called": False,
        },
    }


def _build_runtime_health(settings: Settings, missing_config: list[str]) -> dict[str, Any]:
    db_status, db_errors = check_database(settings)
    current_rev = None
    head_rev = None
    migration_pending = False
    warnings: list[str] = []
    if db_status == "ready":
        try:
            current_rev, head_rev, _ = get_migration_revisions(settings)
            migration_pending = current_rev != head_rev
            if migration_pending:
                warnings.append("alembic migration pending")
        except Exception:  # noqa: BLE001
            migration_pending = True
            warnings.append("alembic revision inspection failed")
    else:
        warnings.extend(db_errors[:3] if db_errors else [f"database_status={db_status}"])
    if missing_config:
        warnings.append("portal customer api config incomplete")
    return {
        "ok": db_status == "ready" and not migration_pending and not missing_config,
        "database_status": db_status,
        "database_ready": db_status == "ready",
        "migration_pending": migration_pending,
        "alembic_current_revision": current_rev,
        "alembic_head_revision": head_rev,
        "portal_customer_api_ready": not missing_config,
        "warnings": warnings,
        "safety": {
            "read_only": True,
            "secret_values_exposed": False,
            "database_url_exposed": False,
            "storage_path_exposed": False,
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
    resource_rows = db.query(OrderResource).order_by(OrderResource.created_at.desc()).limit(500).all()
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
    portal_contract = _build_portal_contract(settings, endpoints, missing_config)
    runtime_health = _build_runtime_health(settings, missing_config)
    forbidden_field_audit = _audit_forbidden_fields(
        {
            "recent_customer_visible_orders": recent_orders,
            "customer_snapshots": snapshot_items,
            "portal_contract": portal_contract,
        }
    )
    feedback_operations = _build_feedback_operations(ticket_rows)
    customer_snapshot_readiness = _build_customer_snapshot_readiness(snapshot_items)
    resource_readiness = _build_resource_readiness(resource_rows)
    status = {
        "ready": settings.PORTAL_CUSTOMER_API_ENABLED and not missing_config,
        "enabled": settings.PORTAL_CUSTOMER_API_ENABLED,
        "token_required": settings.PORTAL_CUSTOMER_API_REQUIRE_TOKEN,
        "token_configured": bool(settings.PORTAL_CUSTOMER_API_TOKEN.strip()),
        "public_base_url_configured": bool(settings.PUBLIC_BASE_URL.strip()),
        "public_base_url": settings.PUBLIC_BASE_URL.strip() or None,
        "allowed_origins": settings.cors_origins_list,
        "missing_config": missing_config,
    }
    portal_launch_readiness = _build_portal_launch_readiness(
        status=status,
        runtime_health=runtime_health,
        endpoints=endpoints,
        forbidden_field_audit=forbidden_field_audit,
        customer_snapshot_readiness=customer_snapshot_readiness,
        resource_readiness=resource_readiness,
        feedback_operations=feedback_operations,
    )

    payload = {
        "status": status,
        "portal_launch_readiness": portal_launch_readiness,
        "portal_contract": portal_contract,
        "runtime_health": runtime_health,
        "endpoint_readiness": endpoints,
        "recent_customer_visible_orders": recent_orders,
        "customer_snapshots": snapshot_items,
        "customer_snapshot_readiness": customer_snapshot_readiness,
        "resource_readiness": resource_readiness,
        "shipment_status_counts": _count_by_status(shipment_rows),
        "feedback_status_counts": _count_by_status(ticket_rows),
        "feedback_priority_counts": _count_by_status(ticket_rows, "priority"),
        "feedback_operations": feedback_operations,
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
                "internal_owner": row.internal_owner,
                "operation": feedback_operation_flags(row),
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in ticket_rows[:recent_limit]
        ],
        "forbidden_field_audit": forbidden_field_audit,
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
