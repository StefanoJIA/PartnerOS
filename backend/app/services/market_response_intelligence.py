"""D8.5 read-only market response intelligence aggregation."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import FeedbackTicket, MarketIntelligenceItem, Product
from app.models.customer_orders import CustomerOrder, OrderLineItem
from app.models.customer_quotes import Quote, QuoteLineItem

ADJUSTABLE_FRAME_TERMS = ("adjustable", "frame", "desk", "height", "sit stand", "standing")
FOCUS_CATEGORY_TERMS = {
    "adjustable_desk_frames": ("adjustable frame", "height adjustable", "sit stand", "standing desk", "desk frame"),
    "desk_legs": ("desk leg", "table leg", "legs", "leg set"),
    "lifting_columns": ("lifting column", "telescopic column", "column lift", "linear column"),
    "education_furniture": ("education", "school", "classroom", "student", "training table"),
    "project_furniture": ("project furniture", "project-based", "project based", "custom furniture", "contract furniture"),
}
NEGATIVE_TERMS = ("delay", "delayed", "late", "issue", "problem", "missing", "broken", "wrong", "noise", "unstable")
POSITIVE_TERMS = ("good", "accepted", "works", "solid", "fit", "stable", "approved", "satisfied")
GAP_FIELDS = (
    ("dimensions", "Missing dimensions"),
    ("load_capacity", "Missing load capacity"),
    ("lifting_speed", "Missing lifting speed"),
    ("noise_level", "Missing noise level"),
    ("available_certifications", "Missing certifications"),
    ("moq", "Missing MOQ"),
    ("sample_available", "Missing sample availability"),
    ("target_us_price_range", "Missing target US price range"),
)


def market_response_safety() -> dict[str, bool]:
    return {
        "read_only": True,
        "ai_suggestions_advisory": True,
        "human_review_required": True,
        "ai_executed": False,
        "customer_notified": False,
        "supplier_notified": False,
        "email_sent": False,
        "webhook_sent": False,
        "partner_selection_changed": False,
        "quote_status_changed": False,
        "order_status_changed": False,
    }


def _safe_rows(db: Session, model: Any) -> list[Any]:
    return list(db.query(model).all())


def _text(*parts: Any) -> str:
    return " ".join(str(p or "") for p in parts).strip()


def _norm(value: Any, fallback: str = "Uncategorized") -> str:
    text = str(value or "").strip()
    return text or fallback


def _inc(counter: dict[str, int], key: str, amount: int = 1) -> None:
    counter[key] = counter.get(key, 0) + amount


def _money(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _tags_for_feedback(row: FeedbackTicket) -> list[str]:
    body = _text(row.feedback_type, row.subject, row.message, row.response_summary).lower()
    tags: set[str] = {_norm(row.feedback_type, "general").lower().replace(" ", "_")}
    if any(term in body for term in NEGATIVE_TERMS):
        tags.add("risk_or_issue")
    if any(term in body for term in POSITIVE_TERMS):
        tags.add("positive_signal")
    if "track" in body or "ship" in body or "carrier" in body:
        tags.add("logistics")
    if "price" in body or "cost" in body or "quote" in body:
        tags.add("pricing")
    if "spec" in body or "dimension" in body or "capacity" in body or "cert" in body:
        tags.add("product_gap")
    if "test" in body:
        tags.add("test")
    return sorted(tags)


def _summary(value: str | None, limit: int = 180) -> str:
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _is_adjustable_frame_signal(*parts: Any) -> bool:
    blob = _text(*parts).lower()
    return any(term in blob for term in ADJUSTABLE_FRAME_TERMS)


def _focus_category(*parts: Any) -> str | None:
    blob = _text(*parts).lower()
    for category, terms in FOCUS_CATEGORY_TERMS.items():
        if any(term in blob for term in terms):
            return category
    return None


def _date_key(value: Any) -> str | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _build_feedback_section(rows: list[FeedbackTicket]) -> dict[str, Any]:
    status_counts: Counter[str] = Counter()
    priority_counts: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    tag_counts: Counter[str] = Counter()
    extracted: list[dict[str, Any]] = []

    for row in rows:
        tags = _tags_for_feedback(row)
        status_counts[_norm(row.status, "new")] += 1
        priority_counts[_norm(row.priority, "normal")] += 1
        type_counts[_norm(row.feedback_type, "general")] += 1
        tag_counts.update(tags)
        extracted.append(
            {
                "ticket_id": str(row.id),
                "ticket_number": row.ticket_number,
                "feedback_type": row.feedback_type,
                "status": row.status,
                "priority": row.priority,
                "subject": row.subject,
                "summary": _summary(row.response_summary or row.message),
                "tags": tags,
                "linked_order_id": str(row.order_id) if row.order_id else None,
                "human_review_required": True,
                "created_at": _date_key(getattr(row, "created_at", None)),
            }
        )

    extracted.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return {
        "total": len(rows),
        "status_counts": dict(status_counts),
        "priority_counts": dict(priority_counts),
        "type_counts": dict(type_counts),
        "tag_counts": dict(tag_counts),
        "items": extracted[:20],
    }


def _build_win_loss_section(
    quotes: list[Quote],
    quote_lines: list[QuoteLineItem],
    orders: list[CustomerOrder],
    order_lines: list[OrderLineItem],
) -> dict[str, Any]:
    quote_status_counts: Counter[str] = Counter(_norm(q.status, "unknown") for q in quotes)
    order_status_counts: Counter[str] = Counter(_norm(o.status, "unknown") for o in orders)
    quote_by_id = {q.id: q for q in quotes}
    order_by_quote = {o.source_quote_id for o in orders if getattr(o, "source_quote_id", None)}
    won_quote_ids = {q.id for q in quotes if _norm(q.status, "unknown") == "converted_to_order"} | order_by_quote
    open_statuses = {"internal_review", "ready_to_send", "sent", "revised"}
    lost_statuses = {"expired"}

    categories: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "category": "",
            "quote_count": 0,
            "quoted_quantity": 0,
            "quoted_value": "0.00",
            "order_count": 0,
            "ordered_quantity": 0,
            "ordered_value": "0.00",
            "win_count": 0,
            "loss_count": 0,
            "open_count": 0,
        }
    )

    quoted_value: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    ordered_value: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    seen_quote_categories: set[tuple[Any, str]] = set()
    seen_order_categories: set[tuple[Any, str]] = set()

    for line in quote_lines:
        category = _norm(getattr(line, "product_category", None))
        bucket = categories[category]
        bucket["category"] = category
        quote = quote_by_id.get(getattr(line, "quote_id", None))
        quote_status = _norm(getattr(quote, "status", None), "unknown")
        key = (getattr(line, "quote_id", None), category)
        if key not in seen_quote_categories:
            bucket["quote_count"] += 1
            seen_quote_categories.add(key)
            if getattr(line, "quote_id", None) in won_quote_ids:
                bucket["win_count"] += 1
            elif quote_status in lost_statuses:
                bucket["loss_count"] += 1
            elif quote_status in open_statuses:
                bucket["open_count"] += 1
        bucket["quoted_quantity"] += int(getattr(line, "quantity", 0) or 0)
        quoted_value[category] += _money(getattr(line, "total_price", None))

    for line in order_lines:
        category = _norm(getattr(line, "product_category", None))
        bucket = categories[category]
        bucket["category"] = category
        key = (getattr(line, "order_id", None), category)
        if key not in seen_order_categories:
            bucket["order_count"] += 1
            seen_order_categories.add(key)
        bucket["ordered_quantity"] += int(getattr(line, "quantity", 0) or 0)
        ordered_value[category] += _money(getattr(line, "total_price", None))

    for category, bucket in categories.items():
        bucket["quoted_value"] = f"{quoted_value[category]:.2f}"
        bucket["ordered_value"] = f"{ordered_value[category]:.2f}"
        denom = bucket["win_count"] + bucket["loss_count"]
        bucket["win_rate"] = round(bucket["win_count"] / denom, 3) if denom else None

    return {
        "quote_status_counts": dict(quote_status_counts),
        "order_status_counts": dict(order_status_counts),
        "won_quote_count": len(won_quote_ids),
        "lost_quote_count": quote_status_counts.get("expired", 0),
        "open_quote_count": sum(quote_status_counts.get(status, 0) for status in open_statuses),
        "category_rows": sorted(categories.values(), key=lambda r: (r["order_count"], r["quote_count"]), reverse=True),
    }


def _build_demand_section(
    market_items: list[MarketIntelligenceItem],
    feedback_rows: list[FeedbackTicket],
    quote_lines: list[QuoteLineItem],
    order_lines: list[OrderLineItem],
) -> dict[str, Any]:
    focus_counts: Counter[str] = Counter()
    demand: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "category": "",
            "market_signal_count": 0,
            "feedback_signal_count": 0,
            "quote_line_count": 0,
            "order_line_count": 0,
            "quoted_quantity": 0,
            "ordered_quantity": 0,
            "importance_counts": {},
            "segments": {},
            "adjustable_frame_focus": False,
            "focus_category": None,
        }
    )

    for item in market_items:
        category = _norm(getattr(item, "related_product_category", None))
        bucket = demand[category]
        bucket["category"] = category
        bucket["market_signal_count"] += 1
        bucket["adjustable_frame_focus"] = bucket["adjustable_frame_focus"] or _is_adjustable_frame_signal(
            category, getattr(item, "title", None), getattr(item, "content", None), getattr(item, "tags", None)
        )
        focus = _focus_category(category, getattr(item, "title", None), getattr(item, "content", None), getattr(item, "tags", None))
        if focus:
            bucket["focus_category"] = bucket["focus_category"] or focus
            focus_counts[focus] += 1
        _inc(bucket["importance_counts"], _norm(getattr(item, "importance", None), "normal"))
        segment = _norm(getattr(item, "market_segment", None), "Unsegmented")
        _inc(bucket["segments"], segment)

    for ticket in feedback_rows:
        category = "Logistics / Service" if "tracking" in _text(ticket.feedback_type, ticket.subject).lower() else "Customer Feedback"
        if _is_adjustable_frame_signal(ticket.subject, ticket.message):
            category = "Adjustable Frames"
        bucket = demand[category]
        bucket["category"] = category
        bucket["feedback_signal_count"] += 1
        bucket["adjustable_frame_focus"] = bucket["adjustable_frame_focus"] or _is_adjustable_frame_signal(ticket.subject, ticket.message)
        focus = _focus_category(ticket.feedback_type, ticket.subject, ticket.message, ticket.response_summary)
        if focus:
            bucket["focus_category"] = bucket["focus_category"] or focus
            focus_counts[focus] += 1

    for line in quote_lines:
        category = _norm(getattr(line, "product_category", None))
        bucket = demand[category]
        bucket["category"] = category
        bucket["quote_line_count"] += 1
        bucket["quoted_quantity"] += int(getattr(line, "quantity", 0) or 0)
        bucket["adjustable_frame_focus"] = bucket["adjustable_frame_focus"] or _is_adjustable_frame_signal(
            category, getattr(line, "product_name", None), getattr(line, "description_customer", None)
        )
        focus = _focus_category(category, getattr(line, "product_name", None), getattr(line, "description_customer", None))
        if focus:
            bucket["focus_category"] = bucket["focus_category"] or focus
            focus_counts[focus] += 1

    for line in order_lines:
        category = _norm(getattr(line, "product_category", None))
        bucket = demand[category]
        bucket["category"] = category
        bucket["order_line_count"] += 1
        bucket["ordered_quantity"] += int(getattr(line, "quantity", 0) or 0)
        bucket["adjustable_frame_focus"] = bucket["adjustable_frame_focus"] or _is_adjustable_frame_signal(
            category, getattr(line, "product_name", None), getattr(line, "description_customer", None)
        )
        focus = _focus_category(category, getattr(line, "product_name", None), getattr(line, "description_customer", None))
        if focus:
            bucket["focus_category"] = bucket["focus_category"] or focus
            focus_counts[focus] += 1

    rows = sorted(
        demand.values(),
        key=lambda r: (
            bool(r["focus_category"]),
            bool(r["adjustable_frame_focus"]),
            r["order_line_count"] + r["quote_line_count"],
            r["market_signal_count"] + r["feedback_signal_count"],
        ),
        reverse=True,
    )
    return {"items": rows, "total": len(rows), "focus_category_counts": dict(focus_counts)}


def _build_gap_section(products: list[Product], demand_rows: list[dict[str, Any]]) -> dict[str, Any]:
    demand_by_category = {row["category"]: row for row in demand_rows}
    rows: list[dict[str, Any]] = []
    missing_counts: Counter[str] = Counter()

    for product in products:
        category = _norm(getattr(product, "product_category", None))
        missing = [label for field, label in GAP_FIELDS if not getattr(product, field, None)]
        if not missing:
            continue
        missing_counts.update(missing)
        demand = demand_by_category.get(category, {})
        rows.append(
            {
                "product_id": str(product.id),
                "product_name": product.product_name,
                "category": category,
                "missing_fields": missing,
                "demand_signal_count": int(demand.get("market_signal_count", 0))
                + int(demand.get("feedback_signal_count", 0))
                + int(demand.get("quote_line_count", 0))
                + int(demand.get("order_line_count", 0)),
                "recommended_review": "Complete product parameters before quote prep or partner comparison.",
                "human_review_required": True,
            }
        )

    rows.sort(key=lambda r: (r["demand_signal_count"], len(r["missing_fields"])), reverse=True)
    return {"items": rows[:25], "total": len(rows), "missing_field_counts": dict(missing_counts)}


def _build_recommendations(feedback: dict[str, Any], win_loss: dict[str, Any], gaps: dict[str, Any]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    if feedback["tag_counts"].get("risk_or_issue", 0):
        recommendations.append(
            {
                "area": "feedback",
                "priority": "high",
                "recommendation": "Review risk-tagged feedback before the next quote or customer status update.",
                "evidence": f"{feedback['tag_counts']['risk_or_issue']} risk-tagged feedback ticket(s)",
                "human_review_required": True,
                "auto_execute": False,
            }
        )
    if win_loss.get("lost_quote_count", 0):
        recommendations.append(
            {
                "area": "quote_strategy",
                "priority": "medium",
                "recommendation": "Compare expired quotes against converted orders to identify product, timing, or pricing objections.",
                "evidence": f"{win_loss['lost_quote_count']} expired quote(s)",
                "human_review_required": True,
                "auto_execute": False,
            }
        )
    if gaps.get("total", 0):
        recommendations.append(
            {
                "area": "product_fit",
                "priority": "medium",
                "recommendation": "Fill missing product parameters for high-demand categories before partner selection.",
                "evidence": f"{gaps['total']} product(s) with parameter gaps",
                "human_review_required": True,
                "auto_execute": False,
            }
        )
    if not recommendations:
        recommendations.append(
            {
                "area": "monitoring",
                "priority": "low",
                "recommendation": "Continue collecting feedback, quote outcomes, and market notes before changing operating playbooks.",
                "evidence": "No high-risk market response pattern detected",
                "human_review_required": True,
                "auto_execute": False,
            }
        )
    return recommendations


def build_market_response_intelligence(db: Session, *, related_company_id: UUID | None = None) -> dict[str, Any]:
    feedback_rows = _safe_rows(db, FeedbackTicket)
    quotes = _safe_rows(db, Quote)
    orders = _safe_rows(db, CustomerOrder)
    market_items = _safe_rows(db, MarketIntelligenceItem)
    if related_company_id:
        feedback_rows = [row for row in feedback_rows if getattr(row, "company_id", None) == related_company_id]
        quotes = [row for row in quotes if getattr(row, "company_id", None) == related_company_id]
        orders = [row for row in orders if getattr(row, "company_id", None) == related_company_id]
        market_items = [row for row in market_items if getattr(row, "related_company_id", None) == related_company_id]
    quote_ids = {row.id for row in quotes}
    order_ids = {row.id for row in orders}
    quote_lines = [row for row in _safe_rows(db, QuoteLineItem) if not related_company_id or getattr(row, "quote_id", None) in quote_ids]
    order_lines = [row for row in _safe_rows(db, OrderLineItem) if not related_company_id or getattr(row, "order_id", None) in order_ids]
    products = _safe_rows(db, Product)

    feedback = _build_feedback_section(feedback_rows)
    win_loss = _build_win_loss_section(quotes, quote_lines, orders, order_lines)
    demand = _build_demand_section(market_items, feedback_rows, quote_lines, order_lines)
    gaps = _build_gap_section(products, demand["items"])
    recommendations = _build_recommendations(feedback, win_loss, gaps)

    return {
        "summary": {
            "feedback_ticket_count": len(feedback_rows),
            "market_signal_count": len(market_items),
            "quote_count": len(quotes),
            "order_count": len(orders),
            "product_gap_count": gaps["total"],
            "recommendation_count": len(recommendations),
            "filtered_by_company": bool(related_company_id),
            "focus_category_counts": demand["focus_category_counts"],
        },
        "feedback": feedback,
        "win_loss": win_loss,
        "demand": demand,
        "product_gaps": gaps,
        "recommendations": recommendations,
        "safety": market_response_safety(),
    }
