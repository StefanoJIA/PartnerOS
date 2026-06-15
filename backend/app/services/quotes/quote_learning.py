from __future__ import annotations

from datetime import datetime, timezone
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
    dimensions = {item.lower() for item in row.product_dimensions or []}
    if row.outcome_status == "lost":
        return "P1"
    if {"load", "noise", "warranty", "certification", "delivery consistency"} & dimensions:
        return "P1"
    return "P2"


def quote_learning_to_dict(row: QuoteLearningRecord) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "quote_id": str(row.quote_id),
        "quote_version_id": str(row.quote_version_id) if row.quote_version_id else None,
        "outcome_status": row.outcome_status,
        "customer_feedback": row.customer_feedback,
        "customer_objection": row.customer_objection,
        "competitor_signal": row.competitor_signal,
        "won_reason": row.won_reason,
        "lost_reason": row.lost_reason,
        "price_feedback": row.price_feedback,
        "delivery_feedback": row.delivery_feedback,
        "product_feedback": row.product_feedback or {},
        "product_dimensions": row.product_dimensions or [],
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
    records = sorted(
        quote.learning_records or [],
        key=lambda row: row.updated_at or row.created_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return quote_learning_to_dict(records[0]) if records else None


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
        body.won_reason,
        body.lost_reason,
        body.price_feedback,
        body.delivery_feedback,
        body.next_action,
    )
    row = QuoteLearningRecord(
        quote_id=quote_id,
        quote_version_id=body.quote_version_id,
        outcome_status=body.outcome_status,
        customer_feedback=body.customer_feedback,
        customer_objection=body.customer_objection,
        competitor_signal=body.competitor_signal,
        won_reason=body.won_reason,
        lost_reason=body.lost_reason,
        price_feedback=body.price_feedback,
        delivery_feedback=body.delivery_feedback,
        product_feedback=body.product_feedback,
        product_dimensions=body.product_dimensions,
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
        values.get("won_reason"),
        values.get("lost_reason"),
        values.get("price_feedback"),
        values.get("delivery_feedback"),
        values.get("next_action"),
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
