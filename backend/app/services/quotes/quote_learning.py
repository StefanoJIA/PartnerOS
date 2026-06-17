from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ApiError, NOT_FOUND, VALIDATION_ERROR
from app.models import MarketResponseReview, Quote, QuoteLearningRecord, QuoteVersion, User
from app.schemas.quotes import QuoteLearningRecordIn, QuoteLearningRecordUpdate


QUOTE_LEARNING_SAFETY: dict[str, bool] = {
    "external_message_sent": False,
    "quote_status_changed": False,
    "order_status_changed": False,
    "customer_notified": False,
    "supplier_notified": False,
    "raw_token_recorded": False,
    "customer_forbidden_fields_exposed": False,
}


FORBIDDEN_LEARNING_TERMS = (
    "raw token",
    "api key",
    "internal cost",
    "margin",
    "supplier private",
    "pricing breakdown",
)


def _assert_safe_text(*values: str | None) -> None:
    text = " ".join(value or "" for value in values).lower()
    for term in FORBIDDEN_LEARNING_TERMS:
        if term in text:
            raise ApiError(VALIDATION_ERROR, f"quote learning text contains forbidden term: {term}", status_code=400)


def _assert_quote_version(db: Session, quote_id: UUID, version_id: UUID | None) -> None:
    if not version_id:
        return
    exists = db.query(QuoteVersion.id).filter(QuoteVersion.id == version_id, QuoteVersion.quote_id == quote_id).first()
    if not exists:
        raise ApiError(VALIDATION_ERROR, "quote_version_id does not belong to this quote", status_code=400)


def _brand(*parts: str) -> str:
    return "".join(parts)


def _quote_product_focus(quote: Quote) -> list[str]:
    values = []
    for line in quote.line_items or []:
        values.extend([line.product_name, line.product_category, line.manual_product_name])
    text = " ".join(value or "" for value in values).lower()
    focus: list[str] = []
    for label in [
        "lifting systems",
        "desk frames",
        "desk legs",
        "lifting columns",
        "heavy-duty supply",
        "heavy-duty solutions",
        "education furniture",
        "school desks",
        "school chairs",
        "project furniture",
    ]:
        if label in text:
            focus.append(label)
    if focus:
        return focus
    return [line.product_category for line in quote.line_items or [] if line.product_category][:5]


def _partner_focus(quote: Quote) -> str:
    text = " ".join(
        str(value or "")
        for line in quote.line_items or []
        for value in [line.product_name, line.product_category, line.manual_product_name]
    ).lower()
    if any(term in text for term in ["education", "school", "classroom"]):
        return _brand("JOO", "BOO")
    if any(term in text for term in ["lifting", "desk frame", "desk leg", "column", "heavy-duty"]):
        return _brand("HO", "SUN")
    return "future partner"


def _focus_category(partner_focus: str, dimensions: list[str], product_focus: list[str]) -> str:
    text = " ".join([partner_focus, *dimensions, *product_focus]).lower()
    if "school" in text or "education" in text or "classroom" in text:
        return "education_furniture"
    if "column" in text:
        return "lifting_columns"
    if "desk leg" in text:
        return "desk_legs"
    if "desk frame" in text or "lifting" in text or "heavy-duty" in text:
        return "adjustable_desk_frames"
    return "quote_learning"


def _review_dimension(row: QuoteLearningRecord) -> str:
    allowed = {
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
        "school procurement timing",
        "delivery consistency",
        "resource needs",
        "feedback after use",
        "project acceptance criteria",
        "product family",
        "quote logic",
        "delivery requirement",
        "customer-visible fields",
        "market response metrics",
    }
    for dimension in row.product_dimensions or []:
        if dimension in allowed:
            return dimension
    return "quote logic"


def _visibility_class(row: QuoteLearningRecord) -> str:
    if row.outcome_status in {"lost", "on_hold"}:
        return "needs validation"
    if row.internal_only:
        return "internal-only"
    return "customer-safe candidate"


def _priority(row: QuoteLearningRecord) -> str:
    dimensions = {item.lower() for item in [*(row.product_dimensions or []), *(row.product_factors or [])]}
    if row.outcome_status == "lost":
        return "P1"
    if {"load", "noise", "warranty", "certification", "delivery consistency"} & dimensions:
        return "P1"
    return "P2"


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


def _latest_learning_model(quote: Quote) -> QuoteLearningRecord | None:
    records = sorted(
        quote.learning_records or [],
        key=lambda row: row.updated_at or row.created_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return records[0] if records else None


def _dimension_baseline(partner_focus: str) -> list[str]:
    if partner_focus == _brand("HO", "SUN"):
        return LIFTING_SYSTEM_QUOTE_DIMENSIONS
    if partner_focus == _brand("JOO", "BOO"):
        return JOOBOO_QUOTE_DIMENSIONS
    return FUTURE_PARTNER_QUOTE_DIMENSIONS


def _merge_unique(values: list[str], limit: int = 8) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(text)
        if len(merged) >= limit:
            break
    return merged


def _top_values(values: list[str], limit: int = 6) -> list[str]:
    counter = Counter(str(value or "").strip() for value in values if str(value or "").strip())
    return [value for value, _ in counter.most_common(limit)]


def build_quote_playbook(db: Session | None, quote: Quote) -> dict[str, Any]:
    partner_focus = _partner_focus(quote)
    product_focus = _quote_product_focus(quote)
    baseline_dimensions = _dimension_baseline(partner_focus)
    current_records = list(quote.learning_records or [])
    historical_records: list[QuoteLearningRecord] = []
    if db is not None and quote.company_id:
        quote_ids = [
            row_id
            for (row_id,) in (
                db.query(Quote.id)
                .filter(Quote.company_id == quote.company_id, Quote.id != quote.id, Quote.is_archived.is_(False))
                .order_by(Quote.updated_at.desc())
                .limit(24)
                .all()
            )
        ]
        if quote_ids:
            historical_records = (
                db.query(QuoteLearningRecord)
                .filter(QuoteLearningRecord.quote_id.in_(quote_ids))
                .order_by(QuoteLearningRecord.updated_at.desc(), QuoteLearningRecord.created_at.desc())
                .limit(80)
                .all()
            )

    records = [*current_records, *historical_records]
    won_records = [row for row in records if row.outcome_status == "won"]
    lost_records = [row for row in records if row.outcome_status == "lost"]
    no_response_records = [row for row in records if row.outcome_status in {"no_response", "no_decision"}]
    deferred_records = [row for row in records if row.outcome_status in {"deferred", "on_hold", "still_active"}]
    winning_factors = _top_values(
        [
            *[row.won_reason or "" for row in won_records],
            *[factor for row in won_records for factor in (row.customer_decision_factors or [])],
            *[factor for row in won_records for factor in (row.product_factors or [])],
            *[factor for row in won_records for factor in (row.product_dimensions or [])],
        ]
    )
    loss_factors = _top_values(
        [
            *[row.lost_reason or "" for row in lost_records],
            *[row.customer_objection or "" for row in lost_records],
            *[row.reason_category or "" for row in lost_records],
            *[factor for row in lost_records for factor in (row.customer_decision_factors or [])],
            *[factor for row in lost_records for factor in (row.product_factors or [])],
        ]
    )
    customer_factors = _top_values([factor for row in records for factor in (row.customer_decision_factors or [])], limit=8)
    product_factors = _top_values(
        [
            *[factor for row in records for factor in (row.product_factors or [])],
            *[factor for row in records for factor in (row.product_dimensions or [])],
        ],
        limit=10,
    )
    partner_factors = _top_values([factor for row in records for factor in (row.partner_factors or [])], limit=8)
    delivery_and_service_factors = [
        factor
        for factor in _merge_unique(
            [*[row.delivery_feedback or "" for row in records], *product_factors, *partner_factors],
            limit=16,
        )
        if any(
            term in factor.lower()
            for term in ["delivery", "certification", "installation", "after-sales", "warranty", "packaging", "test cycle"]
        )
    ][:8]
    dimensions_needing_wording = [
        dimension
        for dimension in baseline_dimensions
        if dimension in product_factors
        or dimension in {"load", "stability", "noise", "warranty", "certification", "test cycle", "project demand"}
    ][:8]
    quote_emphasis = _merge_unique(
        [
            *winning_factors,
            *[factor for factor in customer_factors if factor not in loss_factors],
            *[factor for factor in product_factors if factor in baseline_dimensions],
            *product_focus,
        ],
        limit=8,
    )
    avoid_or_validate = _merge_unique(
        [
            *loss_factors,
            *[
                factor
                for factor in partner_factors
                if any(term in factor.lower() for term in ["capacity", "delivery", "certification", "after-sales"])
            ],
            *[factor for factor in delivery_and_service_factors if factor not in quote_emphasis],
        ],
        limit=8,
    )
    if quote_emphasis and avoid_or_validate:
        next_quote_guidance = (
            f"Emphasize {', '.join(quote_emphasis[:3])}; validate or avoid {', '.join(avoid_or_validate[:3])} before sending."
        )
    elif quote_emphasis:
        next_quote_guidance = f"Emphasize {', '.join(quote_emphasis[:4])} and keep manual follow-up evidence attached to the quote."
    elif avoid_or_validate:
        next_quote_guidance = f"Resolve {', '.join(avoid_or_validate[:4])} before treating this quote as ready to advance."
    else:
        next_quote_guidance = "Record more manual win/loss evidence before treating this as a repeatable quote playbook."
    return {
        "recommendation_type": "internal_quote_playbook",
        "status": "ready" if records else "needs_manual_outcome_evidence",
        "partner_focus": partner_focus,
        "product_focus": product_focus,
        "evidence_count": len(records),
        "won_count": len(won_records),
        "lost_count": len(lost_records),
        "no_response_count": len(no_response_records),
        "deferred_count": len(deferred_records),
        "common_winning_factors": winning_factors,
        "common_loss_factors": loss_factors,
        "customer_decision_factors": customer_factors,
        "product_factors": product_factors,
        "partner_factors": partner_factors,
        "delivery_certification_service_factors": delivery_and_service_factors,
        "quote_emphasis": quote_emphasis,
        "avoid_or_validate_before_sending": avoid_or_validate,
        "customer_safe_wording_needed": dimensions_needing_wording,
        "business_owner_confirmation_needed": dimensions_needing_wording,
        "next_quote_guidance": next_quote_guidance,
        "source_scope": "current quote plus same-account historical quote learning" if db is not None else "current quote learning only",
        "customer_safe_boundary": (
            "Internal recommendation only. Do not expose as customer feedback, AI output, cost, margin, pricing breakdown, "
            "supplier private notes, or customer-visible promise without business owner confirmation."
        ),
        "safety": dict(QUOTE_LEARNING_SAFETY),
    }


def _quote_due_state(quote: Quote) -> str:
    if quote.follow_up_date and quote.follow_up_date <= date.today() and quote.status not in {"converted_to_order"}:
        return "due"
    if quote.follow_up_date and quote.follow_up_date > date.today():
        return "scheduled"
    return "missing"


def build_quote_commercial_intelligence(quote: Quote, db: Session | None = None) -> dict[str, Any]:
    latest = _latest_learning_model(quote)
    learning_records = quote.learning_records or []
    partner_focus = _partner_focus(quote)
    product_focus = _quote_product_focus(quote)
    baseline_dimensions = _dimension_baseline(partner_focus)
    captured_dimensions = sorted(
        {
            str(dimension)
            for record in learning_records
            for dimension in (record.product_dimensions or [])
            if dimension
        }
    )
    missing_inputs: list[str] = []
    if quote.status in {"sent", "revised", "expired"} and not latest:
        missing_inputs.extend(["customer feedback", "won/lost reason"])
    if quote.status in {"sent", "revised"} and _quote_due_state(quote) == "missing":
        missing_inputs.append("follow-up date")
    if len(quote.versions or []) > 1 and not (
        latest and (latest.customer_objection or latest.price_feedback or latest.delivery_feedback)
    ):
        missing_inputs.append("revision reason")
    if quote.status == "converted_to_order" and not (latest and latest.won_reason):
        missing_inputs.append("won reason")
    if (quote.status == "expired" or (latest and latest.outcome_status == "lost")) and not (latest and latest.lost_reason):
        missing_inputs.append("lost reason")
    if not captured_dimensions:
        missing_inputs.append("product dimension feedback")

    priority_dimensions = {"load", "noise", "warranty", "certification", "delivery consistency", "project demand"}
    dimensions_need_review = [dimension for dimension in baseline_dimensions if dimension not in captured_dimensions]
    has_priority_dimension_gap = bool(priority_dimensions & set(dimensions_need_review))
    due_state = _quote_due_state(quote)
    learning_affects_market = bool(
        latest and (latest.affects_market_response or latest.affects_product_intelligence or latest.affects_opportunity)
    )

    if quote.status == "converted_to_order":
        health = "converted_learning_ready" if not missing_inputs else "converted_learning_gap"
        business_focus = "成交复盘"
    elif quote.status == "expired" or (latest and latest.outcome_status == "lost"):
        health = "lost_learning_gap" if missing_inputs else "lost_review_ready"
        business_focus = "丢单复盘"
    elif due_state == "due":
        health = "follow_up_due"
        business_focus = "报价跟进"
    elif len(quote.versions or []) > 1 and missing_inputs:
        health = "revision_learning_gap"
        business_focus = "修订原因"
    elif has_priority_dimension_gap:
        health = "dimension_validation_gap"
        business_focus = "产品维度验证"
    elif missing_inputs:
        health = "needs_quote_learning"
        business_focus = "客户反馈沉淀"
    else:
        health = "conversion_ready"
        business_focus = "成交推进"

    score = 55
    if quote.manual_sent:
        score += 8
    if latest:
        score += 12
    if quote.status == "converted_to_order":
        score += 18
    if quote.status in {"expired"}:
        score -= 14
    if due_state == "due":
        score -= 10
    score -= min(len(missing_inputs) * 6, 24)
    score -= 8 if has_priority_dimension_gap else 0
    score = max(0, min(100, score))

    if health == "follow_up_due":
        next_action = "今天人工跟进客户，并记录回复、异议和下一次 follow-up。"
    elif health in {"lost_learning_gap", "converted_learning_gap"}:
        next_action = "补齐赢单/丢单原因，把可复用经验沉淀到报价学习和 Market Response。"
    elif health == "dimension_validation_gap":
        next_action = "确认关键产品维度是否已有业务认可表述，再决定是否进入客户可见材料。"
    elif health == "revision_learning_gap":
        next_action = "补录报价修订原因，区分价格、交期、认证、安装或质保问题。"
    elif health == "needs_quote_learning":
        next_action = "记录客户反馈、报价状态、异议、owner 和后续人工动作。"
    else:
        next_action = latest.next_action if latest and latest.next_action else "继续人工推进成交，并把客户反馈回流到产品和 Market Response。"

    readiness_impact: list[str] = []
    if missing_inputs:
        readiness_impact.append("commercial pilot learning gap")
    if learning_affects_market or has_priority_dimension_gap:
        readiness_impact.append("Market Response review")
    if partner_focus in {_brand("HO", "SUN"), _brand("JOO", "BOO")} and dimensions_need_review:
        readiness_impact.append("business wording sign-off")

    return {
        "health": health,
        "score": score,
        "priority": "P1" if health in {"follow_up_due", "lost_learning_gap", "dimension_validation_gap"} else "P2",
        "business_focus": business_focus,
        "partner_focus": partner_focus,
        "product_focus": product_focus,
        "version_count": len(quote.versions or []),
        "latest_outcome_status": latest.outcome_status if latest else None,
        "follow_up_state": due_state,
        "missing_inputs": missing_inputs,
        "captured_dimensions": captured_dimensions,
        "dimension_review_needs": dimensions_need_review[:8],
        "market_response_review_needed": learning_affects_market or has_priority_dimension_gap,
        "quote_learning_impacts": [
            value
            for value, enabled in [
                ("opportunity", bool(latest and latest.affects_opportunity)),
                ("product intelligence", bool(latest and latest.affects_product_intelligence)),
                ("market response", bool(latest and latest.affects_market_response)),
            ]
            if enabled
        ],
        "readiness_impact": readiness_impact,
        "quote_playbook": build_quote_playbook(db, quote),
        "next_best_action": next_action,
        "customer_safe_boundary": "内部经营判断；进入 Portal 或客户材料前必须经过 customer-safe wording 与 business/security sign-off。",
        "safety": dict(QUOTE_LEARNING_SAFETY),
    }


def quote_learning_to_dict(row: QuoteLearningRecord) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "quote_id": str(row.quote_id),
        "quote_version_id": str(row.quote_version_id) if row.quote_version_id else None,
        "outcome_status": row.outcome_status,
        "customer_feedback": row.customer_feedback,
        "customer_objection": row.customer_objection,
        "competitor_signal": row.competitor_signal,
        "reason_category": row.reason_category,
        "customer_decision_factors": row.customer_decision_factors or [],
        "won_reason": row.won_reason,
        "lost_reason": row.lost_reason,
        "price_feedback": row.price_feedback,
        "delivery_feedback": row.delivery_feedback,
        "product_feedback": row.product_feedback or {},
        "product_dimensions": row.product_dimensions or [],
        "product_factors": row.product_factors or [],
        "partner_factors": row.partner_factors or [],
        "outcome_source_type": row.outcome_source_type,
        "outcome_source_id": str(row.outcome_source_id) if row.outcome_source_id else None,
        "next_action": row.next_action,
        "owner": row.owner,
        "follow_up_date": str(row.follow_up_date) if row.follow_up_date else None,
        "affects_product_intelligence": row.affects_product_intelligence,
        "affects_market_response": row.affects_market_response,
        "affects_opportunity": row.affects_opportunity,
        "internal_only": row.internal_only,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "safety": dict(QUOTE_LEARNING_SAFETY),
    }


def latest_quote_learning(quote: Quote) -> dict[str, Any] | None:
    row = _latest_learning_model(quote)
    return quote_learning_to_dict(row) if row else None


def list_quote_learning(db: Session, quote_id: UUID) -> dict[str, Any]:
    quote = db.query(Quote).filter(Quote.id == quote_id, Quote.is_archived.is_(False)).first()
    if not quote:
        raise ApiError(NOT_FOUND, "quote not found", status_code=404)
    rows = (
        db.query(QuoteLearningRecord)
        .filter(QuoteLearningRecord.quote_id == quote_id)
        .order_by(QuoteLearningRecord.updated_at.desc(), QuoteLearningRecord.created_at.desc())
        .all()
    )
    return {"items": [quote_learning_to_dict(row) for row in rows], "total": len(rows), "safety": dict(QUOTE_LEARNING_SAFETY)}


def create_quote_learning(
    db: Session,
    quote_id: UUID,
    body: QuoteLearningRecordIn,
    *,
    user: User,
) -> QuoteLearningRecord:
    quote = db.query(Quote).filter(Quote.id == quote_id, Quote.is_archived.is_(False)).first()
    if not quote:
        raise ApiError(NOT_FOUND, "quote not found", status_code=404)
    _assert_quote_version(db, quote_id, body.quote_version_id)
    _assert_safe_text(
        body.customer_feedback,
        body.customer_objection,
        body.competitor_signal,
        body.reason_category,
        body.won_reason,
        body.lost_reason,
        body.price_feedback,
        body.delivery_feedback,
        body.next_action,
        " ".join(body.customer_decision_factors or []),
        " ".join(body.product_factors or []),
        " ".join(body.partner_factors or []),
    )
    row = QuoteLearningRecord(
        quote_id=quote_id,
        quote_version_id=body.quote_version_id,
        outcome_status=body.outcome_status,
        customer_feedback=body.customer_feedback,
        customer_objection=body.customer_objection,
        competitor_signal=body.competitor_signal,
        reason_category=body.reason_category,
        customer_decision_factors=body.customer_decision_factors,
        won_reason=body.won_reason,
        lost_reason=body.lost_reason,
        price_feedback=body.price_feedback,
        delivery_feedback=body.delivery_feedback,
        product_feedback=body.product_feedback,
        product_dimensions=body.product_dimensions,
        product_factors=body.product_factors,
        partner_factors=body.partner_factors,
        outcome_source_type=body.outcome_source_type,
        outcome_source_id=body.outcome_source_id,
        next_action=body.next_action,
        owner=body.owner,
        follow_up_date=body.follow_up_date,
        affects_product_intelligence=body.affects_product_intelligence,
        affects_market_response=body.affects_market_response,
        affects_opportunity=body.affects_opportunity,
        internal_only=body.internal_only,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(row)
    quote.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    return row


def update_quote_learning(
    db: Session,
    quote_id: UUID,
    learning_id: UUID,
    body: QuoteLearningRecordUpdate,
    *,
    user: User,
) -> QuoteLearningRecord:
    row = (
        db.query(QuoteLearningRecord)
        .filter(QuoteLearningRecord.id == learning_id, QuoteLearningRecord.quote_id == quote_id)
        .first()
    )
    if not row:
        raise ApiError(NOT_FOUND, "quote learning record not found", status_code=404)
    values = body.model_dump(exclude_unset=True)
    if "quote_version_id" in values:
        _assert_quote_version(db, quote_id, values["quote_version_id"])
    _assert_safe_text(
        values.get("customer_feedback"),
        values.get("customer_objection"),
        values.get("competitor_signal"),
        values.get("reason_category"),
        values.get("won_reason"),
        values.get("lost_reason"),
        values.get("price_feedback"),
        values.get("delivery_feedback"),
        values.get("next_action"),
        " ".join(values.get("customer_decision_factors") or []),
        " ".join(values.get("product_factors") or []),
        " ".join(values.get("partner_factors") or []),
    )
    for key, value in values.items():
        setattr(row, key, value)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    return row


def promote_quote_learning_to_market_response(
    db: Session,
    quote_id: UUID,
    learning_id: UUID,
    *,
    user: User,
) -> dict[str, Any]:
    quote = db.query(Quote).filter(Quote.id == quote_id, Quote.is_archived.is_(False)).first()
    if not quote:
        raise ApiError(NOT_FOUND, "quote not found", status_code=404)
    row = (
        db.query(QuoteLearningRecord)
        .filter(QuoteLearningRecord.id == learning_id, QuoteLearningRecord.quote_id == quote_id)
        .first()
    )
    if not row:
        raise ApiError(NOT_FOUND, "quote learning record not found", status_code=404)

    duplicate_marker = f"quote_learning_record={row.id}"
    existing = (
        db.query(MarketResponseReview)
        .filter(MarketResponseReview.source_type == "feedback", MarketResponseReview.internal_notes.ilike(f"%{duplicate_marker}%"))
        .first()
    )
    if existing:
        return {
            "review": _market_review_to_dict(existing),
            "created": False,
            "safety": dict(QUOTE_LEARNING_SAFETY),
        }

    product_focus = _quote_product_focus(quote)
    partner_focus = _partner_focus(quote)
    dimensions = row.product_dimensions or []
    source_summary = (
        f"Quote {quote.quote_number} learning: "
        f"{row.customer_objection or row.customer_feedback or row.price_feedback or row.delivery_feedback or row.outcome_status}."
    )
    evidence = "Manual quote learning record. No real partner feedback or customer-safe approval is claimed by this promotion."
    internal_notes = (
        f"{duplicate_marker}; outcome={row.outcome_status}; "
        "internal-only until business owner reviews wording and security boundaries."
    )
    review = MarketResponseReview(
        partner_focus=partner_focus,
        focus_category=_focus_category(partner_focus, dimensions, product_focus),
        product_focus=product_focus or ["quote learning"],
        review_dimension=_review_dimension(row),
        visibility_class=_visibility_class(row),
        priority=_priority(row),
        status="needs review",
        source_type="feedback",
        source_summary=source_summary[:2000],
        evidence_summary=evidence,
        customer_safe_summary=None,
        internal_notes=internal_notes,
        next_action=row.next_action or "Review quote feedback and decide whether product wording, quote logic, or pilot readiness changes.",
        owner=row.owner or user.email,
        due_date=row.follow_up_date,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return {
        "review": _market_review_to_dict(review),
        "created": True,
        "safety": dict(QUOTE_LEARNING_SAFETY),
    }


def _market_review_to_dict(row: MarketResponseReview) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "partner_focus": row.partner_focus,
        "focus_category": row.focus_category,
        "product_focus": row.product_focus or [],
        "review_dimension": row.review_dimension,
        "visibility_class": row.visibility_class,
        "priority": row.priority,
        "status": row.status,
        "source_type": row.source_type,
        "source_summary": row.source_summary,
        "evidence_summary": row.evidence_summary,
        "customer_safe_summary": row.customer_safe_summary,
        "internal_notes": row.internal_notes,
        "next_action": row.next_action,
        "owner": row.owner,
        "due_date": row.due_date.isoformat() if row.due_date else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }
