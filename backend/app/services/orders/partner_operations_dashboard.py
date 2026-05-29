"""Read-only multi-partner operations dashboard aggregation (D8.4)."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ManufacturingPartner
from app.models.customer_orders import OrderPartnerSplit, OrderProductionMilestone, ShipmentPlan

DASHBOARD_SAFETY = {
    "read_only": True,
    "supplier_notified": False,
    "customer_notified": False,
    "shipment_created": False,
    "order_status_changed": False,
    "automatic_sending_enabled": False,
}


def dashboard_safety() -> dict[str, bool]:
    return dict(DASHBOARD_SAFETY)


def _partner_label(row: ManufacturingPartner | None, partner_id: UUID) -> tuple[str, str | None]:
    if row is None:
        return str(partner_id)[:8], None
    return row.partner_name or row.brand_name or str(partner_id)[:8], row.partner_type


def _date_min(values: list[date | None]) -> str | None:
    valid = sorted(v for v in values if v is not None)
    return str(valid[0]) if valid else None


def _currency_totals(splits: list[OrderPartnerSplit]) -> dict[str, str]:
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for split in splits:
        totals[split.currency or "USD"] += Decimal(split.subtotal or 0)
    return {currency: str(total) for currency, total in sorted(totals.items())}


def _risk_flags(
    splits: list[OrderPartnerSplit],
    milestones: list[OrderProductionMilestone],
    shipments: list[ShipmentPlan],
) -> list[str]:
    flags: list[str] = []
    if any(s.supplier_confirmation_status in {"pending", "not_requested", "needs_clarification"} for s in splits):
        flags.append("supplier_confirmation_open")
    if any(m.status == "delayed" for m in milestones):
        flags.append("production_delayed")
    if any(m.status == "blocked" for m in milestones):
        flags.append("production_blocked")
    if not shipments and any(m.milestone_type == "ready_to_ship" and m.status == "completed" for m in milestones):
        flags.append("ready_to_ship_without_shipment")
    return flags


def _status_counts(rows: list[Any], attr: str) -> dict[str, int]:
    counts = Counter(str(getattr(row, attr) or "unknown") for row in rows)
    return dict(sorted(counts.items()))


def build_partner_operations_dashboard(db: Session) -> dict[str, Any]:
    splits = db.query(OrderPartnerSplit).all()
    partner_ids = {split.partner_id for split in splits}
    split_ids = {split.id for split in splits}

    partners = {}
    if partner_ids:
        rows = db.query(ManufacturingPartner).filter(ManufacturingPartner.id.in_(partner_ids)).all()
        partners = {row.id: row for row in rows}

    milestones: list[OrderProductionMilestone] = []
    shipments: list[ShipmentPlan] = []
    if partner_ids:
        milestones = (
            db.query(OrderProductionMilestone)
            .filter(OrderProductionMilestone.partner_id.in_(partner_ids))
            .all()
        )
    if split_ids:
        shipments = db.query(ShipmentPlan).filter(ShipmentPlan.partner_split_id.in_(split_ids)).all()

    splits_by_partner: dict[UUID, list[OrderPartnerSplit]] = defaultdict(list)
    milestones_by_partner: dict[UUID, list[OrderProductionMilestone]] = defaultdict(list)
    shipments_by_partner: dict[UUID, list[ShipmentPlan]] = defaultdict(list)
    for split in splits:
        splits_by_partner[split.partner_id].append(split)
    for milestone in milestones:
        milestones_by_partner[milestone.partner_id].append(milestone)
    split_partner = {split.id: split.partner_id for split in splits}
    for shipment in shipments:
        partner_id = split_partner.get(shipment.partner_split_id)
        if partner_id is not None:
            shipments_by_partner[partner_id].append(shipment)

    partner_rows: list[dict[str, Any]] = []
    for partner_id in sorted(partner_ids, key=lambda item: str(item)):
        partner_splits = splits_by_partner[partner_id]
        partner_milestones = milestones_by_partner[partner_id]
        partner_shipments = shipments_by_partner[partner_id]
        name, partner_type = _partner_label(partners.get(partner_id), partner_id)
        delayed = sum(1 for m in partner_milestones if m.status == "delayed")
        blocked = sum(1 for m in partner_milestones if m.status == "blocked")
        ready_to_ship = sum(
            1 for m in partner_milestones if m.milestone_type == "ready_to_ship" and m.status == "completed"
        )
        partner_rows.append(
            {
                "partner_id": str(partner_id),
                "partner_name": name,
                "partner_type": partner_type,
                "split_count": len(partner_splits),
                "order_count": len({split.order_id for split in partner_splits}),
                "line_item_count": sum(split.line_item_count or 0 for split in partner_splits),
                "subtotal_by_currency": _currency_totals(partner_splits),
                "supplier_confirmation_status_counts": _status_counts(partner_splits, "supplier_confirmation_status"),
                "split_status_counts": _status_counts(partner_splits, "split_status"),
                "milestone_status_counts": _status_counts(partner_milestones, "status"),
                "delayed_milestone_count": delayed,
                "blocked_milestone_count": blocked,
                "ready_to_ship_completed_count": ready_to_ship,
                "shipment_status_counts": _status_counts(partner_shipments, "status"),
                "active_shipment_count": sum(1 for s in partner_shipments if s.status != "cancelled"),
                "next_expected_ready_date": _date_min([split.expected_ready_date for split in partner_splits]),
                "risk_flags": _risk_flags(partner_splits, partner_milestones, partner_shipments),
            }
        )

    summary = {
        "partner_count": len(partner_rows),
        "split_count": len(splits),
        "order_count": len({split.order_id for split in splits}),
        "supplier_confirmed_split_count": sum(1 for split in splits if split.supplier_confirmation_status == "confirmed"),
        "supplier_open_split_count": sum(
            1
            for split in splits
            if split.supplier_confirmation_status in {"pending", "not_requested", "needs_clarification"}
        ),
        "delayed_milestone_count": sum(1 for milestone in milestones if milestone.status == "delayed"),
        "blocked_milestone_count": sum(1 for milestone in milestones if milestone.status == "blocked"),
        "active_shipment_count": sum(1 for shipment in shipments if shipment.status != "cancelled"),
        "shipped_or_delivered_count": sum(1 for shipment in shipments if shipment.status in {"shipped", "delivered"}),
    }

    return {
        "summary": summary,
        "items": partner_rows,
        "total": len(partner_rows),
        "safety": dashboard_safety(),
    }
