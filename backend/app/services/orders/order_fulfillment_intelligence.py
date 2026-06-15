from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import CustomerOrder, FeedbackTicket, Quote
from app.services.quotes.quote_learning import build_quote_commercial_intelligence


FULFILLMENT_INTELLIGENCE_SAFETY: dict[str, bool] = {
    "external_message_sent": False,
    "customer_notified": False,
    "supplier_notified": False,
    "quote_status_changed": False,
    "order_status_changed": False,
    "shipment_created": False,
    "raw_token_recorded": False,
    "customer_forbidden_fields_exposed": False,
}


def _feedback_summary(db: Session, order: CustomerOrder) -> dict[str, Any]:
    rows = db.query(FeedbackTicket).filter(FeedbackTicket.order_id == order.id).all()
    open_rows = [row for row in rows if row.status not in {"closed", "resolved", "archived"}]
    high_priority = [row for row in rows if row.priority in {"high", "urgent", "P0", "P1"}]
    return {
        "total": len(rows),
        "open": len(open_rows),
        "high_priority": len(high_priority),
        "latest_status": rows[0].status if rows else None,
    }


def build_order_fulfillment_intelligence(db: Session, order: CustomerOrder) -> dict[str, Any]:
    quote = db.query(Quote).filter(Quote.id == order.source_quote_id).first()
    quote_intelligence = build_quote_commercial_intelligence(quote) if quote else {}
    delayed = [row for row in order.production_milestones if row.status in {"delayed", "blocked"}]
    completed = [row for row in order.production_milestones if row.status == "completed"]
    shipments = order.shipment_plans or []
    shipped = [row for row in shipments if row.status in {"shipped", "in_transit", "delivered"}]
    delivered = [row for row in shipments if row.status == "delivered"]
    feedback = _feedback_summary(db, order)
    linked_feedback_count = db.query(func.count(FeedbackTicket.id)).filter(FeedbackTicket.order_id == order.id).scalar() or 0

    quote_dimension_gaps = list(quote_intelligence.get("dimension_review_needs") or [])
    quote_missing_inputs = list(quote_intelligence.get("missing_inputs") or [])
    missing_operating_inputs: list[str] = []
    if not order.production_milestones:
        missing_operating_inputs.append("production milestones")
    if not shipments:
        missing_operating_inputs.append("shipment plan")
    if order.status in {"delivered", "completed"} and not linked_feedback_count:
        missing_operating_inputs.append("after-sales feedback")
    if quote_missing_inputs:
        missing_operating_inputs.extend([f"quote learning: {item}" for item in quote_missing_inputs[:3]])

    if delayed:
        health = "delivery_blocked"
        risk_level = "high"
        business_focus = "生产异常"
    elif feedback["open"] or feedback["high_priority"]:
        health = "after_sales_attention"
        risk_level = "medium"
        business_focus = "售后反馈"
    elif not shipments:
        health = "shipment_gap"
        risk_level = "high" if order.status in {"confirmed", "in_production", "ready_to_ship"} else "medium"
        business_focus = "物流计划"
    elif shipments and not shipped and completed:
        health = "ready_to_ship_gap"
        risk_level = "medium"
        business_focus = "待发运"
    elif delivered:
        health = "repeat_business_review"
        risk_level = "normal" if feedback["open"] == 0 else "medium"
        business_focus = "复购维护"
    else:
        health = "on_track"
        risk_level = "normal"
        business_focus = "交付跟进"

    if health == "delivery_blocked":
        next_action = "先处理 delayed/blocked 生产里程碑，再更新客户可见交付摘要。"
    elif health == "shipment_gap":
        next_action = "补齐人工物流计划，确认 ETD/ETA 是否能以 planned wording 对客户可见。"
    elif health == "after_sales_attention":
        next_action = "处理未关闭反馈，判断是否回流到 Market Response 或复购风险。"
    elif health == "ready_to_ship_gap":
        next_action = "确认发运安排、物流状态和客户可见 tracking 摘要。"
    elif health == "repeat_business_review":
        next_action = "收集交付后反馈，评估复购或同类项目推进机会。"
    elif quote_dimension_gaps:
        next_action = "把报价阶段未验证的产品维度纳入交付复盘，避免客户可见材料过度承诺。"
    else:
        next_action = "持续跟踪生产、物流和反馈，保留人工确认边界。"

    readiness_impact: list[str] = []
    if delayed or not shipments:
        readiness_impact.append("delivery visibility risk")
    if feedback["open"]:
        readiness_impact.append("repeat business risk")
    if quote_dimension_gaps or quote_missing_inputs:
        readiness_impact.append("commercial learning loop")
    if quote_intelligence.get("market_response_review_needed") or feedback["open"]:
        readiness_impact.append("Market Response review")

    return {
        "health": health,
        "risk_level": risk_level,
        "business_focus": business_focus,
        "source_quote": {
            "quote_id": str(quote.id),
            "quote_number": quote.quote_number,
            "status": quote.status,
        }
        if quote
        else {"quote_id": str(order.source_quote_id)},
        "quote_commercial_health": quote_intelligence.get("health"),
        "quote_business_focus": quote_intelligence.get("business_focus"),
        "quote_dimension_gaps": quote_dimension_gaps,
        "quote_missing_inputs": quote_missing_inputs,
        "missing_operating_inputs": missing_operating_inputs,
        "production": {
            "total_milestones": len(order.production_milestones),
            "completed_milestones": len(completed),
            "delayed_or_blocked": len(delayed),
        },
        "shipment": {
            "total_plans": len(shipments),
            "shipped_or_delivered": len(shipped),
            "delivered": len(delivered),
        },
        "feedback": feedback,
        "readiness_impact": readiness_impact,
        "next_best_action": next_action,
        "customer_safe_boundary": "内部履约判断；客户可见 production/shipment/feedback 文案必须继续走白名单和人工确认。",
        "safety": dict(FULFILLMENT_INTELLIGENCE_SAFETY),
    }
