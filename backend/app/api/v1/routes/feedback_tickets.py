"""D7.8 internal feedback ticket operations routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.request_id import get_request_id
from app.core.permissions import PERM_FEEDBACK_READ, PERM_FEEDBACK_WRITE, require_permission
from app.core.responses import success_envelope
from app.models import User
from app.schemas.feedback_tickets import FeedbackTicketUpdateIn
from app.services.portal.feedback_ticket_service import (
    get_feedback_ticket,
    list_feedback_tickets,
    ticket_to_dict,
    update_feedback_ticket,
)

router = APIRouter(prefix="/feedback-tickets", tags=["v1-feedback-tickets"])


@router.get("")
def list_feedback_ticket_route(
    request: Request,
    status: str | None = None,
    priority: str | None = None,
    feedback_type: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERM_FEEDBACK_READ)),
):
    data = list_feedback_tickets(
        db,
        status=status,
        priority=priority,
        feedback_type=feedback_type,
        search=search,
        page=page,
        limit=limit,
    )
    return success_envelope(data, request_id=get_request_id(request))


@router.get("/{ticket_id}")
def get_feedback_ticket_route(
    ticket_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERM_FEEDBACK_READ)),
):
    return success_envelope(ticket_to_dict(get_feedback_ticket(db, ticket_id)), request_id=get_request_id(request))


@router.patch("/{ticket_id}")
def patch_feedback_ticket_route(
    ticket_id: UUID,
    body: FeedbackTicketUpdateIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERM_FEEDBACK_WRITE)),
):
    row = update_feedback_ticket(
        db,
        ticket_id,
        status=body.status,
        priority=body.priority,
        internal_owner=body.internal_owner,
        response_summary=body.response_summary,
        actor_id=user.id,
    )
    return success_envelope(ticket_to_dict(row), request_id=get_request_id(request))


@router.post("/{ticket_id}/resolve")
def resolve_feedback_ticket_route(
    ticket_id: UUID,
    body: FeedbackTicketUpdateIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERM_FEEDBACK_WRITE)),
):
    row = update_feedback_ticket(
        db,
        ticket_id,
        status="resolved",
        priority=body.priority,
        internal_owner=body.internal_owner,
        response_summary=body.response_summary,
        actor_id=user.id,
    )
    return success_envelope(ticket_to_dict(row), request_id=get_request_id(request))


@router.post("/{ticket_id}/close")
def close_feedback_ticket_route(
    ticket_id: UUID,
    body: FeedbackTicketUpdateIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PERM_FEEDBACK_WRITE)),
):
    row = update_feedback_ticket(
        db,
        ticket_id,
        status="closed",
        priority=body.priority,
        internal_owner=body.internal_owner,
        response_summary=body.response_summary,
        actor_id=user.id,
    )
    return success_envelope(ticket_to_dict(row), request_id=get_request_id(request))
