"""V1 Quote delivery log and timeline routes (D6.5)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.services.quotes.quote_delivery_service import list_delivery_due, list_delivery_logs
from app.services.quotes.quote_timeline import build_quote_timeline

router = APIRouter(prefix="/quotes", tags=["v1-quote-delivery"])


@router.get("/delivery-due")
def delivery_due_route(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items = list_delivery_due(db)
    rid = get_request_id(request)
    return success_envelope({"items": items, "total": len(items)}, request_id=rid)


@router.get("/{quote_id}/delivery-logs")
def list_delivery_logs_route(
    quote_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items = list_delivery_logs(db, quote_id)
    rid = get_request_id(request)
    return success_envelope({"items": items, "total": len(items)}, request_id=rid)


@router.get("/{quote_id}/timeline")
def quote_timeline_route(
    quote_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    data = build_quote_timeline(db, quote_id)
    rid = get_request_id(request)
    return success_envelope(data, request_id=rid)
