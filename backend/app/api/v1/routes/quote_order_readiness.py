"""V1 Quote-to-order readiness routes (D6.6)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.services.quotes.order_readiness import build_order_readiness_board, build_quote_order_readiness

router = APIRouter(prefix="/quotes", tags=["v1-quote-order-readiness"])


@router.get("/order-readiness-board")
def order_readiness_board_route(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items = build_order_readiness_board(db, limit=limit)
    rid = get_request_id(request)
    return success_envelope({"items": items, "total": len(items)}, request_id=rid)


@router.get("/{quote_id}/order-readiness")
def quote_order_readiness_route(
    quote_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    data = build_quote_order_readiness(db, quote_id)
    rid = get_request_id(request)
    return success_envelope(data, request_id=rid)
