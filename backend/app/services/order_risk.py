"""Rule-based order risk panel (no partner-name bias)."""

from __future__ import annotations

from datetime import date

from app.models import Order, ProductionMilestone, ShippingRecord
from app.models.enums import RiskLevel
from app.schemas.orders_domain import OrderRiskItemOut, OrderRiskPanelOut


def _severity(levels: list[str]) -> str:
    if any(x == "high" for x in levels):
        return "high"
    if any(x == "medium" for x in levels):
        return "medium"
    return "low"


def build_order_risk_panel(
    order: Order,
    milestones: list[ProductionMilestone],
    shipping_records: list[ShippingRecord],
    today: date,
) -> OrderRiskPanelOut:
    items: list[OrderRiskItemOut] = []

    if order.risk_level and order.risk_level.lower() in (RiskLevel.high.value, RiskLevel.critical.value):
        items.append(
            OrderRiskItemOut(
                risk_level="high",
                risk_reason="Order risk_level is marked high or critical.",
                recommended_action="Review commitments, milestones, and shipping plan; prepare factual customer update.",
            )
        )

    for m in milestones:
        st = (m.status or "").lower()
        done = st in ("completed", "done", "complete")
        if m.planned_date and not m.actual_date and not done and m.planned_date < today:
            items.append(
                OrderRiskItemOut(
                    risk_level="medium",
                    risk_reason=f"Milestone '{m.milestone_name}' is past planned_date without completion.",
                    recommended_action="Update milestone dates or mark complete; communicate timeline slip if customer-facing.",
                )
            )

    if order.target_delivery_date and order.target_delivery_date <= today:
        has_delivered = any(
            (r.delivery_status or "").lower() in ("delivered", "final delivered", "customer received")
            for r in shipping_records
        )
        if not has_delivered:
            items.append(
                OrderRiskItemOut(
                    risk_level="high",
                    risk_reason="Target delivery date has passed but shipping records do not show final delivery.",
                    recommended_action="Confirm forwarder/warehouse status and send a concise customer status update.",
                )
            )

    near_days = 14
    if order.target_delivery_date and today <= order.target_delivery_date <= date.fromordinal(
        today.toordinal() + near_days
    ):
        if not shipping_records:
            items.append(
                OrderRiskItemOut(
                    risk_level="medium",
                    risk_reason="Target delivery date is within two weeks and no shipping record exists.",
                    recommended_action="Create or update a shipping record with booking/ETD/ETA.",
                )
            )

    missing_eta = False
    for r in shipping_records:
        if r.eta and r.eta < today and (r.delivery_status or "").lower() not in ("delivered", "final delivered"):
            items.append(
                OrderRiskItemOut(
                    risk_level="medium",
                    risk_reason="Shipping ETA is in the past but delivery is not marked complete.",
                    recommended_action="Verify with freight forwarder; update customer on revised ETA.",
                )
            )
        if not r.eta and not r.etd and order.target_delivery_date:
            missing_eta = True
    if missing_eta:
        items.append(
            OrderRiskItemOut(
                risk_level="low",
                risk_reason="At least one shipping record lacks ETD/ETA while order has target_delivery_date.",
                recommended_action="Add ETD/ETA to improve downstream tracking.",
            )
        )

    if not items:
        items.append(
            OrderRiskItemOut(
                risk_level="low",
                risk_reason="No automatic risk flags from current structured fields.",
                recommended_action="Continue monitoring milestones and shipping milestones.",
            )
        )

    sev = _severity([i.risk_level for i in items])
    return OrderRiskPanelOut(items=items, overall_severity=sev)
