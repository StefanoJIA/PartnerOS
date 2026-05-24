"""Supplier confirmation service (D7.4)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import NOT_FOUND, VALIDATION_ERROR, ApiError
from app.models import User
from app.models.customer_orders import (
    SUPPLIER_CONFIRMATION_STATUSES,
    OrderPartnerSplit,
    SupplierConfirmation,
)
from app.services.activity import log_activity
from app.services.orders.order_service import ORDER_SAFETY, get_order
from app.services.orders.partner_split_service import _partner_name, get_partner_split

FORBIDDEN_PHRASES = (
    "supplier notified automatically",
    "production started",
    "shipment created",
    "inventory guaranteed",
    "certification guaranteed",
    "lead time guaranteed",
    "delivery guaranteed",
    "payment received",
)


def supplier_confirmation_safety(
    *,
    recorded: bool = False,
    inventory_confirmed: bool = False,
    certification_confirmed: bool = False,
    lead_time_confirmed: bool = False,
) -> dict[str, bool]:
    return {
        **ORDER_SAFETY,
        "supplier_confirmation_recorded": recorded,
        "supplier_notified": False,
        "production_started": False,
        "shipment_created": False,
        "automatic_sending_enabled": False,
        "payment_received": False,
        "inventory_promised": inventory_confirmed,
        "certification_promised": certification_confirmed,
        "lead_time_promised": lead_time_confirmed,
    }


def _parse_confirmed_at(value: datetime | str | None) -> datetime | None:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _parse_date(value: date | str | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def confirmation_to_dict(row: SupplierConfirmation) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "order_id": str(row.order_id),
        "partner_split_id": str(row.partner_split_id),
        "partner_id": str(row.partner_id),
        "confirmation_status": row.confirmation_status,
        "confirmed_at": row.confirmed_at.isoformat() if row.confirmed_at else None,
        "confirmed_by_name": row.confirmed_by_name,
        "confirmed_by_email": row.confirmed_by_email,
        "confirmation_channel": row.confirmation_channel,
        "inventory_confirmed": row.inventory_confirmed,
        "certification_confirmed": row.certification_confirmed,
        "lead_time_confirmed": row.lead_time_confirmed,
        "production_capacity_confirmed": row.production_capacity_confirmed,
        "expected_production_start": str(row.expected_production_start) if row.expected_production_start else None,
        "expected_ready_date": str(row.expected_ready_date) if row.expected_ready_date else None,
        "supplier_reference": row.supplier_reference,
        "note": row.note,
        "status": row.status,
        "voided_at": row.voided_at.isoformat() if row.voided_at else None,
        "voided_reason": row.voided_reason,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _build_warnings(row: SupplierConfirmation) -> list[str]:
    warnings: list[str] = []
    if not row.inventory_confirmed:
        warnings.append("inventory not confirmed")
    if not row.certification_confirmed:
        warnings.append("certification not confirmed")
    if not row.lead_time_confirmed:
        warnings.append("lead time not confirmed")
    if not row.production_capacity_confirmed:
        warnings.append("production capacity not confirmed")
    warnings.append("supplier confirmation does not start production")
    warnings.append("supplier confirmation does not create shipment")
    return warnings


def _apply_split_from_confirmation(db: Session, split: OrderPartnerSplit, row: SupplierConfirmation) -> None:
    split.supplier_confirmation_status = row.confirmation_status
    if row.confirmation_status == "confirmed":
        split.supplier_confirmed_at = row.confirmed_at
        split.split_status = "supplier_confirmed"
        if row.expected_production_start:
            split.expected_production_start = row.expected_production_start
        if row.expected_ready_date:
            split.expected_ready_date = row.expected_ready_date
    elif row.confirmation_status == "needs_clarification":
        split.split_status = "pending_supplier_confirmation"
    elif row.confirmation_status == "rejected":
        split.split_status = "on_hold"
    elif row.confirmation_status == "partially_confirmed":
        split.split_status = "pending_supplier_confirmation"


def supplier_confirmation_summary(db: Session, order_id: UUID) -> dict[str, Any]:
    rows = (
        db.query(SupplierConfirmation)
        .filter(SupplierConfirmation.order_id == order_id, SupplierConfirmation.status == "active")
        .all()
    )
    return {
        "active_confirmations": len(rows),
        "confirmed_count": sum(1 for r in rows if r.confirmation_status == "confirmed"),
        "needs_clarification_count": sum(1 for r in rows if r.confirmation_status == "needs_clarification"),
        "rejected_count": sum(1 for r in rows if r.confirmation_status == "rejected"),
    }


def list_supplier_confirmations(
    db: Session, order_id: UUID, *, split_id: UUID | None = None
) -> list[SupplierConfirmation]:
    get_order(db, order_id)
    q = db.query(SupplierConfirmation).filter(SupplierConfirmation.order_id == order_id)
    if split_id is not None:
        q = q.filter(SupplierConfirmation.partner_split_id == split_id)
    return q.order_by(SupplierConfirmation.created_at.desc()).all()


def add_supplier_confirmation(
    db: Session,
    user: User,
    order_id: UUID,
    split_id: UUID,
    *,
    confirmation_status: str,
    confirmed_at: datetime | str | None = None,
    confirmed_by_name: str | None = None,
    confirmed_by_email: str | None = None,
    confirmation_channel: str | None = None,
    inventory_confirmed: bool = False,
    certification_confirmed: bool = False,
    lead_time_confirmed: bool = False,
    production_capacity_confirmed: bool = False,
    expected_production_start: date | str | None = None,
    expected_ready_date: date | str | None = None,
    supplier_reference: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    order = get_order(db, order_id)
    if order.status == "cancelled":
        raise ApiError(VALIDATION_ERROR, "Cancelled order cannot receive supplier confirmations", status_code=400)
    if order.status != "confirmed":
        raise ApiError(
            VALIDATION_ERROR,
            "Supplier confirmation requires customer-confirmed order",
            status_code=400,
        )
    if confirmation_status not in SUPPLIER_CONFIRMATION_STATUSES:
        raise ApiError(VALIDATION_ERROR, f"Invalid confirmation status: {confirmation_status}", status_code=400)

    split = get_partner_split(db, order_id, split_id)
    when = _parse_confirmed_at(confirmed_at)

    row = SupplierConfirmation(
        order_id=order.id,
        partner_split_id=split.id,
        partner_id=split.partner_id,
        confirmation_status=confirmation_status,
        confirmed_at=when,
        confirmed_by_name=confirmed_by_name,
        confirmed_by_email=confirmed_by_email,
        confirmation_channel=confirmation_channel,
        inventory_confirmed=bool(inventory_confirmed),
        certification_confirmed=bool(certification_confirmed),
        lead_time_confirmed=bool(lead_time_confirmed),
        production_capacity_confirmed=bool(production_capacity_confirmed),
        expected_production_start=_parse_date(expected_production_start),
        expected_ready_date=_parse_date(expected_ready_date),
        supplier_reference=supplier_reference,
        note=note,
        status="active",
        created_by_id=user.id,
    )
    db.add(row)
    db.flush()
    _apply_split_from_confirmation(db, split, row)

    log_activity(
        db,
        object_type="customer_order",
        object_id=order.id,
        action="supplier_confirmation_added",
        actor_id=user.id,
        diff={
            "confirmation_id": str(row.id),
            "split_id": str(split.id),
            "partner_id": str(split.partner_id),
            "confirmation_status": confirmation_status,
        },
    )

    db.commit()
    db.refresh(split)
    db.refresh(row)

    partner = _partner_name(db, split.partner_id)
    warnings = _build_warnings(row)
    return {
        "split": split,
        "confirmation": row,
        "partner_name": partner,
        "warnings": warnings,
        "safety": supplier_confirmation_safety(
            recorded=True,
            inventory_confirmed=row.inventory_confirmed,
            certification_confirmed=row.certification_confirmed,
            lead_time_confirmed=row.lead_time_confirmed,
        ),
    }


def void_supplier_confirmation(
    db: Session,
    user: User,
    order_id: UUID,
    confirmation_id: UUID,
    *,
    reason: str | None = None,
) -> dict[str, Any]:
    order = get_order(db, order_id)
    row = (
        db.query(SupplierConfirmation)
        .filter(SupplierConfirmation.id == confirmation_id, SupplierConfirmation.order_id == order_id)
        .first()
    )
    if not row:
        raise ApiError(NOT_FOUND, "Supplier confirmation not found", status_code=404)
    if row.status == "voided":
        raise ApiError(VALIDATION_ERROR, "Supplier confirmation is already voided", status_code=400)

    row.status = "voided"
    row.voided_at = datetime.now(timezone.utc)
    row.voided_reason = reason
    db.flush()

    split = get_partner_split(db, order_id, row.partner_split_id)
    active = (
        db.query(SupplierConfirmation)
        .filter(
            SupplierConfirmation.partner_split_id == split.id,
            SupplierConfirmation.status == "active",
        )
        .order_by(SupplierConfirmation.confirmed_at.desc().nullslast())
        .first()
    )
    warnings: list[str] = []
    if active:
        _apply_split_from_confirmation(db, split, active)
    else:
        split.supplier_confirmation_status = "pending"
        split.split_status = "pending_supplier_confirmation"
        split.supplier_confirmed_at = None
        warnings.append("partner split has no active supplier confirmation")

    log_activity(
        db,
        object_type="customer_order",
        object_id=order.id,
        action="supplier_confirmation_voided",
        actor_id=user.id,
        diff={"confirmation_id": str(row.id), "reason": reason},
    )

    db.commit()
    db.refresh(split)
    db.refresh(row)

    return {
        "split": split,
        "confirmation": row,
        "warnings": warnings,
        "safety": supplier_confirmation_safety(recorded=active is not None),
    }
