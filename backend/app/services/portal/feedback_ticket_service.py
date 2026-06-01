"""Internal operations service for D7.8 feedback tickets."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.errors import NOT_FOUND, VALIDATION_ERROR, ApiError
from app.models import FeedbackTicket
from app.services.activity import log_activity

FEEDBACK_STATUSES = ("new", "in_review", "responded", "resolved", "closed")
FEEDBACK_PRIORITIES = ("low", "normal", "high", "urgent")


def feedback_safety() -> dict[str, bool]:
    return {
        "customer_notified": False,
        "automatic_reply_sent": False,
        "email_sent": False,
        "sla_promised": False,
    }


def ticket_to_dict(row: FeedbackTicket) -> dict:
    return {
        "id": str(row.id),
        "ticket_number": row.ticket_number,
        "source": row.source,
        "order_id": str(row.order_id) if row.order_id else None,
        "company_id": str(row.company_id) if row.company_id else None,
        "feedback_type": row.feedback_type,
        "subject": row.subject,
        "message": row.message,
        "status": row.status,
        "priority": row.priority,
        "internal_owner": row.internal_owner,
        "customer_name": row.customer_name,
        "customer_email": row.customer_email,
        "response_summary": row.response_summary,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "operation": {
            "internal_handling_only": True,
            "activity_logging_enabled": True,
            "customer_visible_response": False,
        },
        "safety": feedback_safety(),
    }


def list_feedback_tickets(
    db: Session,
    *,
    status: str | None = None,
    priority: str | None = None,
    feedback_type: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 50,
) -> dict:
    q = db.query(FeedbackTicket)
    if status:
        q = q.filter(FeedbackTicket.status == status)
    if priority:
        q = q.filter(FeedbackTicket.priority == priority)
    if feedback_type:
        q = q.filter(FeedbackTicket.feedback_type == feedback_type)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(
            or_(
                FeedbackTicket.ticket_number.ilike(like),
                FeedbackTicket.subject.ilike(like),
                FeedbackTicket.message.ilike(like),
                FeedbackTicket.customer_email.ilike(like),
            )
        )
    total = q.count()
    rows = q.order_by(FeedbackTicket.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"items": [ticket_to_dict(r) for r in rows], "total": total, "page": page, "limit": limit}


def get_feedback_ticket(db: Session, ticket_id: UUID) -> FeedbackTicket:
    row = db.query(FeedbackTicket).filter(FeedbackTicket.id == ticket_id).first()
    if not row:
        raise ApiError(NOT_FOUND, "Feedback ticket not found", status_code=404)
    return row


def update_feedback_ticket(
    db: Session,
    ticket_id: UUID,
    *,
    status: str | None = None,
    priority: str | None = None,
    internal_owner: str | None = None,
    response_summary: str | None = None,
    actor_id: UUID | None = None,
) -> FeedbackTicket:
    row = get_feedback_ticket(db, ticket_id)
    previous = {
        "status": row.status,
        "priority": row.priority,
        "internal_owner": row.internal_owner,
        "has_response_summary": bool(row.response_summary),
    }
    if status is not None:
        if status not in FEEDBACK_STATUSES:
            raise ApiError(VALIDATION_ERROR, "Invalid feedback status", status_code=400)
        row.status = status
    if priority is not None:
        if priority not in FEEDBACK_PRIORITIES:
            raise ApiError(VALIDATION_ERROR, "Invalid feedback priority", status_code=400)
        row.priority = priority
    if internal_owner is not None:
        row.internal_owner = internal_owner.strip() or None
    if response_summary is not None:
        row.response_summary = response_summary.strip() or None
    changes = {
        "status": row.status,
        "priority": row.priority,
        "internal_owner": row.internal_owner,
        "has_response_summary": bool(row.response_summary),
        "customer_notified": False,
        "automatic_reply_sent": False,
        "sla_promised": False,
    }
    action = "feedback_ticket_updated"
    if previous["status"] != row.status:
        action = "feedback_status_changed"
    if row.status == "resolved":
        action = "feedback_ticket_resolved"
    if row.status == "closed":
        action = "feedback_ticket_closed"
    log_activity(
        db,
        object_type="feedback_ticket",
        object_id=row.id,
        action=action,
        actor_id=actor_id,
        diff={"previous": previous, "current": changes},
    )
    db.commit()
    db.refresh(row)
    return row
