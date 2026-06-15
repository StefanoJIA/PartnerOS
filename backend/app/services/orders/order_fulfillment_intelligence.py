from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import CustomerOrder, FeedbackTicket, Quote
from app.services.quotes.quote_learning import build_quote_commercial_intelligence
from app.services.quotes.quote_partner_readiness import build_quote_partner_readiness


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


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _build_partner_execution_readiness(
    order: CustomerOrder,
    quote_partner_readiness: dict[str, Any],
    feedback: dict[str, Any],
) -> dict[str, Any]:
    quote_partners = list(quote_partner_readiness.get("partners") or [])
    split_by_partner = {str(split.partner_id): split for split in order.partner_splits}
    delayed_partner_ids = {
        str(row.partner_id)
        for row in order.production_milestones
        if row.status in {"delayed", "blocked"}
    }

    partners: list[dict[str, Any]] = []
    missing_inputs: list[str] = []
    risk_signals: list[str] = []
    readiness_impact: list[str] = []

    for partner in quote_partners:
        partner_id = str(partner.get("partner_id") or "")
        split = split_by_partner.get(partner_id)
        split_created = split is not None
        supplier_confirmations = [row for row in (split.supplier_confirmations if split else []) if row.status == "active"]
        confirmed_supplier_records = [
            row for row in supplier_confirmations if row.confirmation_status in {"confirmed", "accepted"}
        ]
        partner_milestones = [row for row in order.production_milestones if str(row.partner_id) == partner_id]
        active_partner_shipments = [
            row
            for row in order.shipment_plans
            if split and str(row.partner_split_id) == str(split.id) and row.status != "cancelled"
        ]

        partner_missing = list(partner.get("missing_inputs") or [])
        if not split_created:
            partner_missing.append("partner split")
        if split_created and not confirmed_supplier_records:
            partner_missing.append("supplier confirmation")
        if split_created and not partner_milestones:
            partner_missing.append("production milestones")
        if split_created and not active_partner_shipments:
            partner_missing.append("shipment plan")

        partner_risks = list(partner.get("risk_signals") or [])
        if partner_id in delayed_partner_ids:
            partner_risks.append("production delayed or blocked")
        if feedback["open"]:
            partner_risks.append("linked feedback needs delivery review")

        if not split_created:
            handoff_stage = "quote_to_order"
            next_action = "先把报价中的 Partner 承接判断落到订单 partner split，明确谁负责生产/交付。"
        elif not confirmed_supplier_records:
            handoff_stage = "supplier_confirmation"
            next_action = "补齐供应商确认，确认产能、交期、认证和生产起始信息。"
        elif not partner_milestones:
            handoff_stage = "production_planning"
            next_action = "生成或维护生产里程碑，让订单交付风险可跟踪。"
        elif not active_partner_shipments:
            handoff_stage = "shipment_planning"
            next_action = "维护人工物流计划，确认 ETD/ETA 是否可 customer-safe 展示。"
        elif partner_risks:
            handoff_stage = "risk_review"
            next_action = "复核生产/物流/反馈风险，并判断是否回流 Market Response。"
        else:
            handoff_stage = "delivery_follow_up"
            next_action = "继续跟踪生产、物流和客户反馈，保留人工确认边界。"

        partner_impact = list(partner.get("readiness_impact") or [])
        if partner_missing:
            partner_impact.append("order execution readiness")
        if partner_risks:
            partner_impact.append("delivery risk review")
        if not active_partner_shipments:
            partner_impact.append("customer-visible shipment readiness")

        partner_item = {
            "partner_id": partner_id,
            "partner_name": partner.get("partner_name") or "未命名 Partner",
            "quote_readiness_health": partner.get("health"),
            "handoff_stage": handoff_stage,
            "readiness_score": partner.get("readiness_score", 0),
            "split_created": split_created,
            "split_id": str(split.id) if split else None,
            "split_status": split.split_status if split else None,
            "supplier_confirmation_count": len(confirmed_supplier_records),
            "production_milestone_count": len(partner_milestones),
            "shipment_plan_count": len(active_partner_shipments),
            "missing_execution_inputs": _unique(partner_missing),
            "risk_signals": _unique(partner_risks),
            "readiness_impact": _unique(partner_impact),
            "next_best_action": next_action,
            "customer_safe_boundary": partner.get("customer_safe_boundary")
            or "Partner 执行判断仅供内部使用；客户可见字段必须继续走白名单和人工确认。",
        }
        partners.append(partner_item)
        missing_inputs.extend([f"{partner_item['partner_name']}: {item}" for item in partner_item["missing_execution_inputs"]])
        risk_signals.extend([f"{partner_item['partner_name']}: {item}" for item in partner_item["risk_signals"]])
        readiness_impact.extend(partner_item["readiness_impact"])

    if not partners and order.partner_splits:
        for split in order.partner_splits:
            active_shipments = [plan for plan in split.shipment_plans if plan.status != "cancelled"]
            partner_missing = []
            if not [row for row in split.supplier_confirmations if row.status == "active" and row.confirmation_status in {"confirmed", "accepted"}]:
                partner_missing.append("supplier confirmation")
            if not split.production_milestones:
                partner_missing.append("production milestones")
            if not active_shipments:
                partner_missing.append("shipment plan")
            partners.append(
                {
                    "partner_id": str(split.partner_id),
                    "partner_name": getattr(split, "partner_name", None) or split.partner_reference_number or str(split.partner_id),
                    "quote_readiness_health": None,
                    "handoff_stage": "order_execution",
                    "readiness_score": 0,
                    "split_created": True,
                    "split_id": str(split.id),
                    "split_status": split.split_status,
                    "supplier_confirmation_count": len(split.supplier_confirmations),
                    "production_milestone_count": len(split.production_milestones),
                    "shipment_plan_count": len(active_shipments),
                    "missing_execution_inputs": partner_missing,
                    "risk_signals": [],
                    "readiness_impact": ["order execution readiness"] if partner_missing else [],
                    "next_best_action": "订单已有 partner split；补齐供应商确认、生产里程碑和物流计划后再对客户展示交付摘要。",
                    "customer_safe_boundary": "Partner 执行判断仅供内部使用；客户可见字段必须继续走白名单和人工确认。",
                }
            )
            missing_inputs.extend([f"{str(split.partner_id)}: {item}" for item in partner_missing])

    if risk_signals:
        health = "partner_execution_risk"
        priority = "P1"
        next_best_action = "优先处理 Partner 执行风险，再更新订单交付或客户可见摘要。"
    elif missing_inputs:
        health = "partner_execution_gap"
        priority = "P1"
        next_best_action = "补齐 Partner split、供应商确认、生产或物流计划，让报价承接进入可执行订单交付。"
    elif partners:
        health = "partner_execution_ready"
        priority = "P2"
        next_best_action = "继续跟踪 Partner 生产、物流和反馈，沉淀复购与 Market Response 信号。"
    else:
        health = "partner_execution_unknown"
        priority = "P2"
        next_best_action = "订单缺少可判断的 Partner 承接信息；先确认源报价或订单 partner split。"

    return {
        "health": health,
        "priority": priority,
        "partners": partners,
        "missing_inputs": _unique(missing_inputs),
        "risk_signals": _unique(risk_signals),
        "readiness_impact": _unique(readiness_impact),
        "next_best_action": next_best_action,
        "customer_safe_boundary": "订单 Partner 执行判断只读派生，不通知客户/供应商，不创建物流，不改变订单状态；客户可见内容必须走 Portal 白名单。",
        "safety": dict(FULFILLMENT_INTELLIGENCE_SAFETY),
    }


def build_order_fulfillment_intelligence(db: Session, order: CustomerOrder) -> dict[str, Any]:
    quote = db.query(Quote).filter(Quote.id == order.source_quote_id).first()
    quote_intelligence = build_quote_commercial_intelligence(quote) if quote else {}
    quote_partner_readiness = build_quote_partner_readiness(quote, db) if quote else {}
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
    partner_execution_readiness = _build_partner_execution_readiness(order, quote_partner_readiness, feedback)
    if partner_execution_readiness["missing_inputs"]:
        missing_operating_inputs.extend(
            [f"partner execution: {item}" for item in partner_execution_readiness["missing_inputs"][:4]]
        )

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
    if partner_execution_readiness["health"] in {"partner_execution_gap", "partner_execution_risk"}:
        readiness_impact.append("partner execution readiness")
    readiness_impact.extend(partner_execution_readiness["readiness_impact"][:4])

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
        "quote_partner_readiness_health": quote_partner_readiness.get("health"),
        "quote_dimension_gaps": quote_dimension_gaps,
        "quote_missing_inputs": quote_missing_inputs,
        "missing_operating_inputs": missing_operating_inputs,
        "partner_execution_readiness": partner_execution_readiness,
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
