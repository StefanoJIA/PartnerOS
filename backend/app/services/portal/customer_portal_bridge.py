"""D7.7 customer portal bridge data builders."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import NOT_FOUND, VALIDATION_ERROR, ApiError
from app.models import Company, FeedbackTicket, File, FileAttachment, ProductCatalog
from app.models.customer_orders import CustomerOrder, OrderLineItem, OrderProductionMilestone
from app.services.orders.shipment_plan_service import list_shipment_plans, shipment_plan_to_dict
from app.services.portal.customer_contract import CUSTOMER_FEEDBACK_PRIORITIES, CUSTOMER_FEEDBACK_TYPES
from app.services.portal.customer_field_filter import (
    assert_no_forbidden_internal_fields,
    strip_forbidden_internal_fields,
)


def _date_str(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _money(value: Decimal | None) -> str | None:
    return str(value) if value is not None else None


def _company_name(db: Session, company_id: UUID | None) -> str | None:
    if not company_id:
        return None
    row = db.query(Company).filter(Company.id == company_id).first()
    return row.company_name if row else None


def _safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = strip_forbidden_internal_fields(payload)
    assert_no_forbidden_internal_fields(cleaned)
    return cleaned


def _product_to_customer_dict(row: ProductCatalog) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "internal_sku": row.internal_sku,
        "product_name": row.product_name,
        "product_category": row.product_category,
        "product_family": row.product_family,
        "description": row.description_customer,
        "status": row.status,
        "uom": row.default_uom,
        "currency": row.base_currency,
        "default_incoterm": row.default_incoterm,
        "image_url": row.image_url,
        "attributes": row.attributes_json or {},
    }


def build_customer_product_list(
    db: Session,
    *,
    category: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 50,
) -> dict[str, Any]:
    q = db.query(ProductCatalog).filter(ProductCatalog.status == "active")
    if category:
        q = q.filter(ProductCatalog.product_category == category)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(ProductCatalog.product_name.ilike(like) | ProductCatalog.internal_sku.ilike(like))
    total = q.count()
    rows = q.order_by(ProductCatalog.product_name.asc()).offset((page - 1) * limit).limit(limit).all()
    return _safe_payload({"items": [_product_to_customer_dict(r) for r in rows], "total": total, "page": page, "limit": limit})


def _line_to_customer_dict(line: OrderLineItem) -> dict[str, Any]:
    return {
        "id": str(line.id),
        "product_name": line.product_name,
        "product_category": line.product_category,
        "description": line.description_customer,
        "quantity": line.quantity,
        "uom": line.uom,
        "unit_price": _money(line.unit_price),
        "total_price": _money(line.total_price),
        "currency": line.currency,
        "incoterm": line.incoterm,
        "status": line.status,
    }


def _order_summary(db: Session, order: CustomerOrder) -> dict[str, Any]:
    return {
        "id": str(order.id),
        "order_number": order.order_number,
        "status": order.status,
        "order_date": _date_str(order.order_date),
        "company_id": str(order.company_id) if order.company_id else None,
        "company_name": _company_name(db, order.company_id),
        "currency": order.currency,
        "grand_total": _money(order.grand_total),
        "customer_confirmed_at": order.customer_confirmed_at.isoformat() if order.customer_confirmed_at else None,
        "ship_to_company": order.ship_to_company,
        "ship_to_address": order.ship_to_address,
    }


def build_customer_order_list(
    db: Session,
    *,
    company_id: UUID | None = None,
    status: str | None = None,
    page: int = 1,
    limit: int = 50,
) -> dict[str, Any]:
    q = db.query(CustomerOrder).filter(CustomerOrder.status != "cancelled")
    if company_id:
        q = q.filter(CustomerOrder.company_id == company_id)
    if status:
        q = q.filter(CustomerOrder.status == status)
    total = q.count()
    rows = q.order_by(CustomerOrder.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return _safe_payload({"items": [_order_summary(db, r) for r in rows], "total": total, "page": page, "limit": limit})


def _get_customer_order(db: Session, order_id: UUID) -> CustomerOrder:
    row = db.query(CustomerOrder).filter(CustomerOrder.id == order_id).first()
    if not row:
        raise ApiError(NOT_FOUND, "Order not found", status_code=404)
    return row


def build_customer_order_detail(db: Session, order_id: UUID) -> dict[str, Any]:
    order = _get_customer_order(db, order_id)
    payload = _order_summary(db, order)
    payload.update(
        {
            "bill_to_company": order.bill_to_company,
            "ship_to_name": order.ship_to_name,
            "payment_terms": order.payment_terms,
            "shipping_terms": order.shipping_terms,
            "customer_notes": order.customer_notes,
            "line_items": [_line_to_customer_dict(li) for li in order.line_items if li.customer_visible and li.status != "cancelled"],
        }
    )
    return _safe_payload(payload)


def build_customer_production_view(db: Session, order_id: UUID) -> dict[str, Any]:
    _get_customer_order(db, order_id)
    rows = (
        db.query(OrderProductionMilestone)
        .filter(OrderProductionMilestone.order_id == order_id)
        .order_by(OrderProductionMilestone.sequence.asc())
        .all()
    )
    items = [
        {
            "milestone_type": row.milestone_type,
            "milestone_label": row.milestone_label,
            "sequence": row.sequence,
            "status": row.status,
            "planned_date": _date_str(row.planned_date),
            "actual_date": _date_str(row.actual_date),
        }
        for row in rows
    ]
    return _safe_payload(
        {
            "order_id": str(order_id),
            "items": items,
            "total": len(items),
            "completed_count": sum(1 for i in items if i["status"] == "completed"),
        }
    )


def build_customer_shipment_view(db: Session, order_id: UUID) -> dict[str, Any]:
    _get_customer_order(db, order_id)
    rows = list_shipment_plans(db, order_id)
    items = [shipment_plan_to_dict(row).get("portal_visible_fields", {}) for row in rows if row.status != "cancelled"]
    return _safe_payload({"order_id": str(order_id), "items": items, "total": len(items)})


def build_customer_resource_view(db: Session, order_id: UUID) -> dict[str, Any]:
    _get_customer_order(db, order_id)
    rows = (
        db.query(FileAttachment, File)
        .join(File, File.id == FileAttachment.file_id)
        .filter(FileAttachment.object_type == "customer_order", FileAttachment.object_id == order_id)
        .order_by(FileAttachment.created_at.desc())
        .all()
    )
    items = [
        {
            "id": str(att.id),
            "file_id": str(file.id),
            "filename": file.original_filename,
            "mime": file.mime,
            "size": file.size,
            "purpose": att.purpose,
            "created_at": att.created_at.isoformat() if att.created_at else None,
        }
        for att, file in rows
    ]
    return _safe_payload({"order_id": str(order_id), "items": items, "total": len(items)})


def _next_ticket_number(db: Session) -> str:
    year = date.today().year
    prefix = f"FB-{year}-"
    last = (
        db.query(FeedbackTicket)
        .filter(FeedbackTicket.ticket_number.like(f"{prefix}%"))
        .order_by(FeedbackTicket.ticket_number.desc())
        .with_for_update()
        .first()
    )
    seq = 1
    if last:
        try:
            seq = int(last.ticket_number.rsplit("-", 1)[-1]) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:04d}"


def create_feedback_ticket(
    db: Session,
    *,
    source: str = "customer_portal",
    order_id: UUID | None = None,
    company_id: UUID | None = None,
    feedback_type: str = "general",
    subject: str,
    message: str,
    priority: str = "normal",
    customer_name: str | None = None,
    customer_email: str | None = None,
) -> dict[str, Any]:
    if order_id:
        order = _get_customer_order(db, order_id)
        if not company_id:
            company_id = order.company_id
    if not subject.strip() or not message.strip():
        raise ApiError(VALIDATION_ERROR, "subject and message are required", status_code=400)
    normalized_feedback_type = (feedback_type or "general").strip().lower()
    normalized_priority = (priority or "normal").strip().lower()
    if normalized_feedback_type not in CUSTOMER_FEEDBACK_TYPES:
        raise ApiError(VALIDATION_ERROR, "Invalid feedback type", status_code=400)
    if normalized_priority not in CUSTOMER_FEEDBACK_PRIORITIES:
        raise ApiError(VALIDATION_ERROR, "Invalid feedback priority", status_code=400)
    row = FeedbackTicket(
        ticket_number=_next_ticket_number(db),
        source=source or "customer_portal",
        order_id=order_id,
        company_id=company_id,
        feedback_type=normalized_feedback_type,
        subject=subject.strip()[:255],
        message=message.strip(),
        status="new",
        priority=normalized_priority,
        customer_name=customer_name,
        customer_email=customer_email,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    next_links: dict[str, str | None] = {
        "orders": "/api/v1/portal/customer/orders",
        "order_snapshot": None,
        "production": None,
        "shipment": None,
        "resources": None,
        "feedback_submit": "/api/v1/portal/customer/feedback",
    }
    if order_id:
        order_id_text = str(order_id)
        next_links.update(
            {
                "order_snapshot": f"/api/v1/portal/customer/orders/{order_id_text}/snapshot",
                "production": f"/api/v1/portal/customer/orders/{order_id_text}/production",
                "shipment": f"/api/v1/portal/customer/orders/{order_id_text}/shipment",
                "resources": f"/api/v1/portal/customer/orders/{order_id_text}/resources",
            }
        )
    return _safe_payload(
        {
            "ticket_number": row.ticket_number,
            "status": row.status,
            "feedback_received": True,
            "next_links": next_links,
            "customer_notified": False,
            "automatic_reply_sent": False,
            "resolution_time_promised": False,
        }
    )
