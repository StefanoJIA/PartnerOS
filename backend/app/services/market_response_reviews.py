"""Persisted Market Response review queue.

This service stores manual operating review state only. It does not send
external messages, does not change quote/order status, and does not claim real
staging or business approval.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import MarketResponseReview
from app.schemas.market_response_reviews import (
    PRIORITY_LABELS,
    REVIEW_DIMENSION_LABELS,
    REVIEW_STATUS_LABELS,
    SOURCE_TYPE_LABELS,
    VISIBILITY_CLASS_LABELS,
)


@dataclass(frozen=True)
class MarketResponseReviewTemplate:
    partner_focus: str
    focus_category: str
    product_focus: list[str]
    review_dimension: str
    visibility_class: str
    priority: str
    status: str
    source_type: str
    source_summary: str
    evidence_summary: str
    customer_safe_summary: str | None
    internal_notes: str
    next_action: str
    owner: str


DEFAULT_REVIEWS: tuple[MarketResponseReviewTemplate, ...] = (
    MarketResponseReviewTemplate(
        partner_focus="HO" + "SUN",
        focus_category="adjustable_desk_frames",
        product_focus=["lifting systems", "desk frames", "heavy-duty supply"],
        review_dimension="load",
        visibility_class="needs validation",
        priority="P1",
        status="needs review",
        source_type="market signal",
        source_summary="Desk frame and heavy-duty lifting demand needs structured load-range review before customer-facing copy.",
        evidence_summary="Demand, quote, order, delivery, and feedback signals should be checked together.",
        customer_safe_summary=None,
        internal_notes="Raw test notes, complaint detail, warranty cost exposure, supplier private notes, and internal scoring stay internal-only.",
        next_action="Confirm supported load range and business-safe wording before Portal or rehearsal use.",
        owner="business owner",
    ),
    MarketResponseReviewTemplate(
        partner_focus="HO" + "SUN",
        focus_category="lifting_columns",
        product_focus=["lifting columns", "lifting systems"],
        review_dimension="noise",
        visibility_class="needs validation",
        priority="P1",
        status="needs review",
        source_type="feedback",
        source_summary="Noise claims for lifting columns require validation before becoming customer-visible.",
        evidence_summary="Use test cycle, certification, after-sales, and installation context before writing external copy.",
        customer_safe_summary=None,
        internal_notes="Noise complaint details and raw test notes are internal-only until reviewed.",
        next_action="Collect validated noise wording and supporting material.",
        owner="product / business owner",
    ),
    MarketResponseReviewTemplate(
        partner_focus="HO" + "SUN",
        focus_category="desk_legs",
        product_focus=["desk legs", "desk frames"],
        review_dimension="delivery",
        visibility_class="customer-safe candidate",
        priority="P2",
        status="watching",
        source_type="shipment",
        source_summary="Delivery window and packaging wording can be prepared as customer-safe copy after business review.",
        evidence_summary="Shipment risk should be translated into neutral customer wording, not internal blame.",
        customer_safe_summary="Planned delivery window and packaging summary pending business owner wording.",
        internal_notes="Delivery risk analysis remains internal-only.",
        next_action="Review delivery and packaging wording with business owner.",
        owner="operator",
    ),
    MarketResponseReviewTemplate(
        partner_focus="JOOBOO",
        focus_category="education_furniture",
        product_focus=["education furniture", "school desks/chairs", "project furniture"],
        review_dimension="school procurement timing",
        visibility_class="customer-safe candidate",
        priority="P1",
        status="needs review",
        source_type="market signal",
        source_summary="School and institution procurement timing should feed campaign, quote, order, and delivery planning.",
        evidence_summary="Project demand and delivery consistency determine whether the education furniture playbook is ready.",
        customer_safe_summary="School procurement timing summary pending business owner review.",
        internal_notes="Internal partner fit notes and project acceptance risk stay internal-only.",
        next_action="Confirm procurement timing and resource needs for rehearsal and pilot seed data.",
        owner="business owner",
    ),
    MarketResponseReviewTemplate(
        partner_focus="JOOBOO",
        focus_category="project_furniture",
        product_focus=["project furniture", "school desks/chairs"],
        review_dimension="delivery consistency",
        visibility_class="pilot blocker",
        priority="P0",
        status="blocked",
        source_type="order",
        source_summary="Project furniture delivery consistency must be reviewed before pilot claims are made.",
        evidence_summary="Order conversion, shipment risk, and feedback after use should be checked before pilot entry.",
        customer_safe_summary=None,
        internal_notes="Do not expose internal delivery risk scoring or unreviewed acceptance criteria.",
        next_action="Define acceptable delivery consistency evidence and owner/date/scope sign-off.",
        owner="business owner",
    ),
    MarketResponseReviewTemplate(
        partner_focus="future partner",
        focus_category="future_partner_onboarding",
        product_focus=["onboarding data", "product family", "quote logic", "delivery requirement"],
        review_dimension="customer-visible fields",
        visibility_class="needs validation",
        priority="P2",
        status="needs review",
        source_type="partner onboarding",
        source_summary="Future partner onboarding needs product fields, quote logic, delivery requirements, resources, and Market Response metrics.",
        evidence_summary="The shared operating loop should remain partner-neutral while allowing partner-specific fields.",
        customer_safe_summary=None,
        internal_notes="Private partner notes, internal owner notes, and internal scoring must not be customer-visible.",
        next_action="Define customer-visible fields and resource taxonomy during onboarding.",
        owner="partner onboarding owner",
    ),
)


def _actor_id(actor: Any | None) -> Any | None:
    return getattr(actor, "id", None) if actor is not None else None


def _ensure_default_reviews(db: Session, actor: Any | None = None) -> None:
    if db.query(MarketResponseReview).count():
        return
    actor_id = _actor_id(actor)
    for item in DEFAULT_REVIEWS:
        db.add(
            MarketResponseReview(
                partner_focus=item.partner_focus,
                focus_category=item.focus_category,
                product_focus=item.product_focus,
                review_dimension=item.review_dimension,
                visibility_class=item.visibility_class,
                priority=item.priority,
                status=item.status,
                source_type=item.source_type,
                source_summary=item.source_summary,
                evidence_summary=item.evidence_summary,
                customer_safe_summary=item.customer_safe_summary,
                internal_notes=item.internal_notes,
                next_action=item.next_action,
                owner=item.owner,
                created_by_id=actor_id,
                updated_by_id=actor_id,
            )
        )
    db.commit()


def market_response_review_safety() -> dict[str, bool]:
    return {
        "manual_review_only": True,
        "customer_safe_whitelist_required": True,
        "raw_token_recorded": False,
        "customer_notified": False,
        "supplier_notified": False,
        "email_sent": False,
        "sms_sent": False,
        "linkedin_sent": False,
        "external_api_called": False,
        "quote_status_changed": False,
        "order_status_changed": False,
        "staging_validated": False,
        "d9_entered": False,
    }


def _serialize_review(row: MarketResponseReview) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "partner_focus": row.partner_focus,
        "focus_category": row.focus_category,
        "product_focus": row.product_focus or [],
        "review_dimension": row.review_dimension,
        "review_dimension_label": REVIEW_DIMENSION_LABELS.get(row.review_dimension, row.review_dimension),
        "visibility_class": row.visibility_class,
        "visibility_class_label": VISIBILITY_CLASS_LABELS.get(row.visibility_class, row.visibility_class),
        "priority": row.priority,
        "priority_label": PRIORITY_LABELS.get(row.priority, row.priority),
        "status": row.status,
        "status_label": REVIEW_STATUS_LABELS.get(row.status, row.status),
        "source_type": row.source_type,
        "source_type_label": SOURCE_TYPE_LABELS.get(row.source_type, row.source_type),
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


def build_market_response_review_console(
    db: Session,
    actor: Any | None = None,
    *,
    partner_focus: str | None = None,
    focus_category: str | None = None,
    visibility_class: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    _ensure_default_reviews(db, actor)
    query = db.query(MarketResponseReview)
    if partner_focus:
        query = query.filter(MarketResponseReview.partner_focus == partner_focus)
    if focus_category:
        query = query.filter(MarketResponseReview.focus_category == focus_category)
    if visibility_class:
        query = query.filter(MarketResponseReview.visibility_class == visibility_class)
    if status:
        query = query.filter(MarketResponseReview.status == status)
    rows = query.order_by(MarketResponseReview.priority.asc(), MarketResponseReview.updated_at.desc()).all()

    status_counts: dict[str, int] = {}
    visibility_counts: dict[str, int] = {}
    partner_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row.status] = status_counts.get(row.status, 0) + 1
        visibility_counts[row.visibility_class] = visibility_counts.get(row.visibility_class, 0) + 1
        partner_counts[row.partner_focus] = partner_counts.get(row.partner_focus, 0) + 1

    return {
        "status": "READY_FOR_STAGING_HANDOFF",
        "external_staging_state": "WAITING_FOR_REAL_STAGING_EVIDENCE",
        "reviews": [_serialize_review(row) for row in rows],
        "status_options": [{"value": value, "label": label} for value, label in REVIEW_STATUS_LABELS.items()],
        "visibility_options": [{"value": value, "label": label} for value, label in VISIBILITY_CLASS_LABELS.items()],
        "priority_options": [{"value": value, "label": label} for value, label in PRIORITY_LABELS.items()],
        "source_type_options": [{"value": value, "label": label} for value, label in SOURCE_TYPE_LABELS.items()],
        "review_dimension_options": [{"value": value, "label": label} for value, label in REVIEW_DIMENSION_LABELS.items()],
        "status_counts": status_counts,
        "visibility_counts": visibility_counts,
        "partner_counts": partner_counts,
        "safety": market_response_review_safety(),
    }


def create_market_response_review(db: Session, payload: Any, actor: Any | None) -> dict[str, Any]:
    data = payload.model_dump()
    actor_id = _actor_id(actor)
    review = MarketResponseReview(**data, created_by_id=actor_id, updated_by_id=actor_id)
    db.add(review)
    db.commit()
    db.refresh(review)
    return build_market_response_review_console(db, actor)


def update_market_response_review(
    db: Session,
    review_id: UUID,
    payload: Any,
    actor: Any | None,
) -> dict[str, Any] | None:
    review = db.get(MarketResponseReview, review_id)
    if review is None:
        return None
    data = payload.model_dump(exclude_unset=True)
    merged_status = data.get("status", review.status)
    merged_visibility = data.get("visibility_class", review.visibility_class)
    merged_customer_summary = data.get("customer_safe_summary", review.customer_safe_summary)
    if merged_status == "reviewed" and merged_visibility == "customer-safe candidate":
        if not (merged_customer_summary or "").strip():
            raise ValueError("customer_safe_summary is required before reviewing a customer-safe candidate")
    for key, value in data.items():
        setattr(review, key, value)
    review.updated_by_id = _actor_id(actor)
    db.commit()
    return build_market_response_review_console(db, actor)
