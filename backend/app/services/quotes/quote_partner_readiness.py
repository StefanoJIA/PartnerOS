from __future__ import annotations

from collections import Counter
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session, object_session

from app.models import ManufacturingPartner
from app.models.customer_quotes import Quote
from app.services.partner_capability_intelligence import build_partner_capability_intelligence


QUOTE_PARTNER_READINESS_SAFETY: dict[str, bool] = {
    "external_message_sent": False,
    "partner_notified": False,
    "customer_notified": False,
    "quote_status_changed": False,
    "order_status_changed": False,
    "raw_token_recorded": False,
    "customer_forbidden_fields_exposed": False,
}

LIFTING_SYSTEM_QUOTE_DIMENSIONS = [
    "load",
    "stability",
    "noise",
    "delivery",
    "installation",
    "after-sales",
    "packaging",
    "warranty",
    "test cycle",
    "certification",
    "project demand",
]

JOOBOO_QUOTE_DIMENSIONS = [
    "durability",
    "school procurement timing",
    "classroom deployment",
    "delivery consistency",
    "resource needs",
    "feedback after use",
    "project acceptance criteria",
]

FUTURE_PARTNER_QUOTE_DIMENSIONS = [
    "product family",
    "quote logic",
    "delivery requirement",
    "resource taxonomy",
    "customer-visible fields",
    "Market Response metrics",
]


def _quote_product_text(quote: Quote) -> str:
    return " ".join(
        str(value or "")
        for line in quote.line_items or []
        for value in [
            line.product_name,
            line.product_category,
            line.manual_product_name,
            line.partner_product_code,
            line.size_dimension,
            line.color_finish,
        ]
    ).lower()


def _dimension_baseline(partner_name: str | None, quote: Quote) -> list[str]:
    text = f"{partner_name or ''} {_quote_product_text(quote)}".lower()
    if any(term in text for term in [("ho" + "sun"), "lifting", "desk frame", "desk leg", "column", "heavy-duty"]):
        return LIFTING_SYSTEM_QUOTE_DIMENSIONS
    if any(term in text for term in ["jooboo", "education", "school", "classroom", "project furniture"]):
        return JOOBOO_QUOTE_DIMENSIONS
    return FUTURE_PARTNER_QUOTE_DIMENSIONS


def _quote_partner_ids(quote: Quote) -> list[str]:
    counts = Counter(str(line.partner_id) for line in quote.line_items or [] if line.partner_id)
    return [partner_id for partner_id, _ in counts.most_common()]


def _quote_partner_line_summary(quote: Quote, partner_id: str) -> dict[str, Any]:
    lines = [line for line in quote.line_items or [] if str(line.partner_id) == partner_id]
    categories = sorted({line.product_category for line in lines if line.product_category})
    names = [line.product_name or line.manual_product_name for line in lines if line.product_name or line.manual_product_name]
    review_count = len([line for line in lines if line.requires_review])
    return {
        "line_count": len(lines),
        "requires_review_count": review_count,
        "product_categories": categories[:6],
        "sample_products": names[:5],
    }


def _partner_readiness_item(db: Session, quote: Quote, partner: ManufacturingPartner) -> dict[str, Any]:
    capability = build_partner_capability_intelligence(db, partner)
    line_summary = _quote_partner_line_summary(quote, str(partner.id))
    dimension_baseline = _dimension_baseline(partner.partner_name, quote)
    missing_inputs = list(capability.get("missing_inputs") or [])
    risk_signals = list(capability.get("risk_signals") or [])

    if line_summary["requires_review_count"]:
        missing_inputs.append("line pricing/manual review")
    if "certification" in dimension_baseline and not (partner.certifications or partner.testing_capability):
        missing_inputs.append("customer-safe certification/testing wording")
    if "delivery" in dimension_baseline and not (partner.lead_time or partner.delivery_rating is not None):
        missing_inputs.append("customer-safe delivery wording")
    if partner.risk_level in {"high", "blocked"} and f"profile risk={partner.risk_level}" not in risk_signals:
        risk_signals.append(f"profile risk={partner.risk_level}")

    readiness_score = int(capability.get("score") or 0)
    readiness_score -= min(line_summary["requires_review_count"] * 5, 15)
    readiness_score -= min(len(risk_signals) * 4, 16)
    readiness_score = max(0, min(100, readiness_score))

    if risk_signals:
        health = "partner_risk_review"
        priority = "P1"
        next_action = f"复核 {partner.partner_name} 的交付、反馈和风险信号，再决定是否把该报价推进给客户。"
    elif missing_inputs:
        health = "partner_quote_gap"
        priority = "P1" if {"pricing basis", "delivery ability", "line pricing/manual review"} & set(missing_inputs) else "P2"
        next_action = f"补齐 {partner.partner_name} 的 {', '.join(missing_inputs[:3])}，再进入人工发送或订单准备。"
    else:
        health = "partner_quote_ready"
        priority = "P2"
        next_action = f"{partner.partner_name} 当前可作为报价承接 partner；发送前仍需人工确认客户可见技术与交付表述。"

    readiness_impact = [
        impact
        for impact, enabled in [
            ("quote send readiness", bool(missing_inputs)),
            ("customer-visible wording", bool({"customer-safe certification/testing wording", "customer-safe delivery wording"} & set(missing_inputs))),
            ("order conversion readiness", health in {"partner_quote_ready", "partner_quote_gap"}),
            ("Market Response review", bool(risk_signals)),
            ("pilot partner selection", capability.get("investment_priority") == "P1"),
        ]
        if enabled
    ]

    return {
        "partner_id": str(partner.id),
        "partner_name": partner.partner_name,
        "health": health,
        "priority": priority,
        "readiness_score": readiness_score,
        "business_focus": capability.get("business_focus"),
        "line_summary": line_summary,
        "dimension_baseline": dimension_baseline,
        "missing_inputs": missing_inputs,
        "risk_signals": risk_signals,
        "readiness_impact": readiness_impact,
        "next_best_action": next_action,
        "capability_score": capability.get("score"),
        "customer_safe_boundary": "内部报价承接判断；不得向客户暴露成本、利润、供应商私密备注、内部评分或未经确认的技术/交付风险。",
        "safety": dict(QUOTE_PARTNER_READINESS_SAFETY),
    }


def build_quote_partner_readiness(quote: Quote, db: Session | None = None) -> dict[str, Any]:
    session = db or object_session(quote)
    if session is None:
        return {
            "health": "not_available",
            "priority": "P2",
            "partners": [],
            "next_best_action": "Quote partner readiness requires an active database session.",
            "safety": dict(QUOTE_PARTNER_READINESS_SAFETY),
        }

    partner_ids = _quote_partner_ids(quote)
    partners: list[dict[str, Any]] = []
    for partner_id in partner_ids:
        partner = session.get(ManufacturingPartner, UUID(str(partner_id)))
        if partner:
            partners.append(_partner_readiness_item(session, quote, partner))

    if not partners:
        health = "missing_partner"
        priority = "P1"
        next_action = "补齐报价行的 partner 信息；没有 partner 承接判断时不得推进订单转换。"
    elif any(item["health"] == "partner_risk_review" for item in partners):
        health = "partner_risk_review"
        priority = "P1"
        next_action = "先处理 partner 风险信号，再决定报价发送、修订或订单准备。"
    elif any(item["health"] == "partner_quote_gap" for item in partners):
        health = "partner_quote_gap"
        priority = "P1"
        next_action = "补齐 partner 报价承接缺口，尤其是交付、认证/测试、客户可见表述和人工价格复核。"
    else:
        health = "partner_quote_ready"
        priority = "P2"
        next_action = "partner 承接条件基本就绪；发送前保留人工复核和 customer-safe wording 审查。"

    readiness_impact = sorted({impact for item in partners for impact in item.get("readiness_impact", [])})
    return {
        "health": health,
        "priority": priority,
        "partners": partners,
        "readiness_impact": readiness_impact,
        "missing_inputs": sorted({gap for item in partners for gap in item.get("missing_inputs", [])}),
        "risk_signals": sorted({risk for item in partners for risk in item.get("risk_signals", [])}),
        "next_best_action": next_action,
        "customer_safe_boundary": "该对象只用于内部报价/partner 承接判断；不得暴露成本、利润、价格拆分、供应商私密备注、内部评分或未经确认的客户可见技术承诺。",
        "safety": dict(QUOTE_PARTNER_READINESS_SAFETY),
    }
