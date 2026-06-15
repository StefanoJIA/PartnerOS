from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    CustomerOrder,
    FeedbackTicket,
    ManufacturingPartner,
    OrderPartnerSplit,
    OrderProductionMilestone,
    ProductCatalog,
    ProductPartnerLink,
    ProductPriceTier,
    ShipmentPlan,
)


PARTNER_CAPABILITY_SAFETY: dict[str, bool] = {
    "external_message_sent": False,
    "partner_notified": False,
    "customer_notified": False,
    "quote_status_changed": False,
    "order_status_changed": False,
    "raw_token_recorded": False,
    "customer_forbidden_fields_exposed": False,
}


def _split_terms(*values: str | None) -> list[str]:
    terms: list[str] = []
    for value in values:
        for raw in (value or "").replace("\n", ",").replace(";", ",").split(","):
            item = raw.strip()
            if item:
                terms.append(item)
    seen: set[str] = set()
    unique: list[str] = []
    for item in terms:
        key = item.lower()
        if key not in seen:
            unique.append(item)
            seen.add(key)
    return unique


def _rating_average(partner: ManufacturingPartner) -> int | None:
    ratings = [
        value
        for value in [
            partner.quality_rating,
            partner.communication_rating,
            partner.delivery_rating,
            partner.project_fit_rating,
        ]
        if value is not None
    ]
    if not ratings:
        return None
    return round(sum(ratings) / len(ratings))


def _partner_counts(db: Session, partner: ManufacturingPartner) -> dict[str, int]:
    product_count = (
        db.query(func.count(ProductCatalog.id))
        .filter(ProductCatalog.partner_id == partner.id)
        .scalar()
        or 0
    )
    product_link_count = (
        db.query(func.count(ProductPartnerLink.id))
        .filter(ProductPartnerLink.manufacturing_partner_id == partner.id)
        .scalar()
        or 0
    )
    price_tier_count = (
        db.query(func.count(ProductPriceTier.id))
        .join(ProductCatalog, ProductCatalog.id == ProductPriceTier.product_id)
        .filter(ProductCatalog.partner_id == partner.id)
        .scalar()
        or 0
    )
    split_count = (
        db.query(func.count(OrderPartnerSplit.id))
        .filter(OrderPartnerSplit.partner_id == partner.id)
        .scalar()
        or 0
    )
    order_count = (
        db.query(func.count(func.distinct(CustomerOrder.id)))
        .join(OrderPartnerSplit, OrderPartnerSplit.order_id == CustomerOrder.id)
        .filter(OrderPartnerSplit.partner_id == partner.id)
        .scalar()
        or 0
    )
    milestone_count = (
        db.query(func.count(OrderProductionMilestone.id))
        .filter(OrderProductionMilestone.partner_id == partner.id)
        .scalar()
        or 0
    )
    delayed_milestone_count = (
        db.query(func.count(OrderProductionMilestone.id))
        .filter(
            OrderProductionMilestone.partner_id == partner.id,
            OrderProductionMilestone.status.in_(["delayed", "blocked"]),
        )
        .scalar()
        or 0
    )
    shipment_count = (
        db.query(func.count(ShipmentPlan.id))
        .join(OrderPartnerSplit, OrderPartnerSplit.id == ShipmentPlan.partner_split_id)
        .filter(OrderPartnerSplit.partner_id == partner.id)
        .scalar()
        or 0
    )
    feedback_count = (
        db.query(func.count(FeedbackTicket.id))
        .join(CustomerOrder, CustomerOrder.id == FeedbackTicket.order_id)
        .join(OrderPartnerSplit, OrderPartnerSplit.order_id == CustomerOrder.id)
        .filter(OrderPartnerSplit.partner_id == partner.id)
        .scalar()
        or 0
    )
    return {
        "product_count": int(product_count),
        "product_link_count": int(product_link_count),
        "price_tier_count": int(price_tier_count),
        "split_count": int(split_count),
        "order_count": int(order_count),
        "milestone_count": int(milestone_count),
        "delayed_milestone_count": int(delayed_milestone_count),
        "shipment_count": int(shipment_count),
        "feedback_count": int(feedback_count),
    }


def build_partner_capability_intelligence(db: Session, partner: ManufacturingPartner) -> dict[str, Any]:
    counts = _partner_counts(db, partner)
    coverage_terms = _split_terms(
        partner.main_product_categories,
        partner.preferred_product_categories,
        partner.manufacturing_capabilities,
    )
    capability_keys = [cap.capability_key for cap in partner.capabilities[:8]]
    rating_average = _rating_average(partner)

    missing_inputs: list[str] = []
    if not coverage_terms and not counts["product_count"] and not capability_keys:
        missing_inputs.append("product coverage")
    if not counts["price_tier_count"] and not partner.price_level and not partner.moq_policy:
        missing_inputs.append("pricing basis")
    if not partner.lead_time and partner.delivery_rating is None:
        missing_inputs.append("delivery ability")
    if not partner.certifications and not partner.testing_capability:
        missing_inputs.append("certification/testing evidence")
    if not partner.ai_partner_summary:
        missing_inputs.append("partner operating summary")
    if counts["order_count"] == 0:
        missing_inputs.append("historical order evidence")

    risk_signals: list[str] = []
    if partner.risk_level in {"high", "blocked"}:
        risk_signals.append(f"profile risk={partner.risk_level}")
    if counts["delayed_milestone_count"]:
        risk_signals.append(f"{counts['delayed_milestone_count']} delayed/blocked production milestone(s)")
    if counts["order_count"] and not counts["shipment_count"]:
        risk_signals.append("orders exist without shipment evidence")
    if counts["feedback_count"]:
        risk_signals.append(f"{counts['feedback_count']} linked feedback ticket(s)")

    score = 40
    score += min((len(coverage_terms) + counts["product_count"] + counts["product_link_count"]) * 3, 18)
    score += 10 if counts["price_tier_count"] or partner.price_level or partner.moq_policy else 0
    score += 10 if partner.lead_time or partner.delivery_rating is not None else 0
    score += 10 if partner.certifications or partner.testing_capability else 0
    score += min(counts["order_count"] * 5 + counts["shipment_count"] * 3, 16)
    score += max(rating_average or 0, 0)
    score -= min(len(missing_inputs) * 5, 20)
    score -= 12 if counts["delayed_milestone_count"] else 0
    score -= 8 if partner.risk_level in {"high", "blocked"} else 0
    score = max(0, min(100, score))

    if risk_signals and counts["order_count"]:
        health = "delivery_risk_review"
        investment_priority = "P1"
        business_focus = "交付可靠性"
    elif missing_inputs:
        health = "capability_gap"
        investment_priority = "P1" if {"product coverage", "pricing basis", "delivery ability"} & set(missing_inputs) else "P2"
        business_focus = "能力补齐"
    elif counts["order_count"] or counts["shipment_count"]:
        health = "active_partner_investment"
        investment_priority = "P1"
        business_focus = "订单承接"
    else:
        health = "pilot_candidate"
        investment_priority = "P2"
        business_focus = "试点准备"

    if health == "delivery_risk_review":
        next_action = "复核该 partner 的生产、物流和反馈记录，决定是否调整项目分配或客户可见交付表述。"
    elif health == "capability_gap":
        next_action = "补齐产品覆盖、报价基础、交付能力和认证/测试证据，再判断是否进入报价或 pilot。"
    elif health == "active_partner_investment":
        next_action = "沉淀历史订单与交付表现，判断是否扩大项目投入或复购机会。"
    else:
        next_action = "准备 partner profile、产品族、报价逻辑、资源分类和 Market Response 指标。"

    return {
        "health": health,
        "score": score,
        "investment_priority": investment_priority,
        "business_focus": business_focus,
        "product_coverage": coverage_terms[:8] or capability_keys[:8],
        "capability_keys": capability_keys,
        "delivery_reliability": partner.lead_time or f"delivery rating {partner.delivery_rating or 'unknown'}",
        "rating_average": rating_average,
        "historical_cooperation": counts,
        "missing_inputs": missing_inputs,
        "risk_signals": risk_signals,
        "readiness_impact": [
            impact
            for impact, enabled in [
                ("quote readiness", "pricing basis" in missing_inputs),
                ("customer-visible resources", "product coverage" in missing_inputs),
                ("delivery visibility", bool(risk_signals)),
                ("pilot partner selection", health in {"delivery_risk_review", "active_partner_investment"}),
                ("Market Response metrics", "partner operating summary" in missing_inputs),
            ]
            if enabled
        ],
        "next_best_action": next_action,
        "customer_safe_boundary": "内部 partner 投入判断；不得向客户暴露供应商私密备注、内部评分或未确认交付风险。",
        "safety": dict(PARTNER_CAPABILITY_SAFETY),
    }
