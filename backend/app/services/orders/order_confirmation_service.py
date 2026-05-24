"""Customer order confirmation service (D7.3)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import NOT_FOUND, VALIDATION_ERROR, ApiError
from app.models import User
from app.models.customer_orders import (
    CONFIRMATION_STATUSES,
    CUSTOMER_CONFIRMATION_TYPES,
    CustomerOrder,
    OrderConfirmation,
    STRENGTH_BY_TYPE,
)
from app.services.activity import log_activity
from app.services.orders.order_service import ORDER_SAFETY, get_order

FORBIDDEN_PHRASES = (
    "supplier notified",
    "production started",
    "shipment created",
    "inventory confirmed",
    "certification confirmed",
    "lead time confirmed",
    "payment received",
    "delivery guaranteed",
)


def confirmation_safety(*, order_confirmed: bool = False) -> dict[str, bool]:
    return {
        **ORDER_SAFETY,
        "order_confirmed": order_confirmed,
        "customer_confirmation_recorded": order_confirmed,
        "payment_received": False,
    }


def infer_strength(confirmation_type: str) -> str:
    return STRENGTH_BY_TYPE.get(confirmation_type, "weak")


def _parse_confirmed_at(value: datetime | str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def confirmation_to_dict(row: OrderConfirmation) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "order_id": str(row.order_id),
        "confirmation_type": row.confirmation_type,
        "confirmation_strength": row.confirmation_strength,
        "confirmed_by_name": row.confirmed_by_name,
        "confirmed_by_email": row.confirmed_by_email,
        "confirmed_by_company": row.confirmed_by_company,
        "confirmed_at": row.confirmed_at.isoformat() if row.confirmed_at else None,
        "source_channel": row.source_channel,
        "evidence_reference": row.evidence_reference,
        "evidence_filename": row.evidence_filename,
        "status": row.status,
        "note": row.note,
        "voided_at": row.voided_at.isoformat() if row.voided_at else None,
        "voided_reason": row.voided_reason,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _build_warnings(confirmation_type: str, evidence_reference: str | None) -> list[str]:
    warnings: list[str] = []
    if confirmation_type == "verbal":
        warnings.append("verbal confirmation should be reviewed")
    if confirmation_type == "internal_note":
        warnings.append("internal note confirmation should be reviewed")
    if not (evidence_reference or "").strip():
        warnings.append("no evidence reference provided")
    warnings.append("confirmed order still requires supplier confirmation before production")
    return warnings


def _sync_order_summary(order: CustomerOrder, confirmation: OrderConfirmation) -> None:
    order.customer_confirmed_at = confirmation.confirmed_at
    order.customer_confirmation_method = confirmation.confirmation_type
    order.customer_confirmation_note = confirmation.note


def _apply_confirmed_status(order: CustomerOrder) -> bool:
    changed = order.status == "pending_customer_confirmation"
    if changed:
        order.status = "confirmed"
        for li in order.line_items:
            if li.status == "pending":
                li.status = "confirmed"
    return changed


def list_customer_confirmations(db: Session, order_id: UUID) -> list[OrderConfirmation]:
    get_order(db, order_id)
    return (
        db.query(OrderConfirmation)
        .filter(OrderConfirmation.order_id == order_id)
        .order_by(OrderConfirmation.confirmed_at.desc())
        .all()
    )


def active_confirmation_count(db: Session, order_id: UUID) -> int:
    return (
        db.query(OrderConfirmation)
        .filter(OrderConfirmation.order_id == order_id, OrderConfirmation.status == "active")
        .count()
    )


def latest_active_confirmation(db: Session, order_id: UUID) -> OrderConfirmation | None:
    return (
        db.query(OrderConfirmation)
        .filter(OrderConfirmation.order_id == order_id, OrderConfirmation.status == "active")
        .order_by(OrderConfirmation.confirmed_at.desc())
        .first()
    )


def confirmation_summary(db: Session, order: CustomerOrder) -> dict[str, Any]:
    active_count = active_confirmation_count(db, order.id)
    latest = latest_active_confirmation(db, order.id)
    warnings: list[str] = []
    if order.status == "confirmed" and active_count == 0:
        warnings.append("confirmed order has no active confirmation")
    return {
        "active_count": active_count,
        "latest": confirmation_to_dict(latest) if latest else None,
        "warnings": warnings,
    }


def add_customer_confirmation(
    db: Session,
    user: User,
    order_id: UUID,
    *,
    confirmation_type: str,
    confirmed_at: datetime | str | None = None,
    confirmed_by_name: str | None = None,
    confirmed_by_email: str | None = None,
    confirmed_by_company: str | None = None,
    source_channel: str | None = None,
    evidence_reference: str | None = None,
    evidence_filename: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    order = get_order(db, order_id)
    if order.status == "cancelled":
        raise ApiError(VALIDATION_ERROR, "Cancelled order cannot receive confirmations", status_code=400)
    if confirmation_type not in CUSTOMER_CONFIRMATION_TYPES:
        raise ApiError(VALIDATION_ERROR, f"Invalid confirmation type: {confirmation_type}", status_code=400)

    when = _parse_confirmed_at(confirmed_at)
    strength = infer_strength(confirmation_type)
    status_changed = _apply_confirmed_status(order)

    row = OrderConfirmation(
        order_id=order.id,
        confirmation_type=confirmation_type,
        confirmation_strength=strength,
        confirmed_by_name=confirmed_by_name,
        confirmed_by_email=confirmed_by_email,
        confirmed_by_company=confirmed_by_company,
        confirmed_at=when,
        source_channel=source_channel or confirmation_type,
        evidence_reference=evidence_reference,
        evidence_filename=evidence_filename,
        note=note,
        status="active",
        created_by_id=user.id,
    )
    db.add(row)
    db.flush()
    _sync_order_summary(order, row)

    log_activity(
        db,
        object_type="customer_order",
        object_id=order.id,
        action="customer_confirmation_added",
        actor_id=user.id,
        diff={"confirmation_id": str(row.id), "confirmation_type": confirmation_type},
    )

    db.commit()
    db.refresh(order)
    db.refresh(row)

    warnings = _build_warnings(confirmation_type, evidence_reference)
    has_active = active_confirmation_count(db, order.id) > 0
    return {
        "order": order,
        "confirmation": row,
        "status_changed": status_changed,
        "warnings": warnings,
        "safety": confirmation_safety(order_confirmed=has_active or order.status == "confirmed"),
    }


def void_customer_confirmation(
    db: Session,
    user: User,
    order_id: UUID,
    confirmation_id: UUID,
    *,
    reason: str | None = None,
) -> dict[str, Any]:
    order = get_order(db, order_id)
    row = (
        db.query(OrderConfirmation)
        .filter(OrderConfirmation.id == confirmation_id, OrderConfirmation.order_id == order_id)
        .first()
    )
    if not row:
        raise ApiError(NOT_FOUND, "Confirmation not found", status_code=404)
    if row.status == "voided":
        raise ApiError(VALIDATION_ERROR, "Confirmation is already voided", status_code=400)

    row.status = "voided"
    row.voided_at = datetime.now(timezone.utc)
    row.voided_reason = reason
    db.flush()

    warnings: list[str] = []
    latest = latest_active_confirmation(db, order.id)
    if latest:
        _sync_order_summary(order, latest)
    elif order.status == "confirmed":
        warnings.append("confirmed order has no active confirmation")

    log_activity(
        db,
        object_type="customer_order",
        object_id=order.id,
        action="customer_confirmation_voided",
        actor_id=user.id,
        diff={"confirmation_id": str(row.id), "reason": reason},
    )

    db.commit()
    db.refresh(order)
    db.refresh(row)

    has_active = active_confirmation_count(db, order.id) > 0
    return {
        "order": order,
        "confirmation": row,
        "warnings": warnings,
        "safety": confirmation_safety(order_confirmed=has_active and order.status == "confirmed"),
    }
