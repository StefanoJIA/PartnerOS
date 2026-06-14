"""D8.5 market response intelligence routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import PERM_MARKET_READ, require_permission
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.schemas.market_response_reviews import MarketResponseReviewCreate, MarketResponseReviewUpdate
from app.services.market_response_intelligence import build_market_response_intelligence
from app.services.market_response_reviews import (
    build_market_response_review_console,
    create_market_response_review,
    update_market_response_review,
)

router = APIRouter(prefix="/market", tags=["v1-market-response"])


@router.get("/response-intelligence")
def get_market_response_intelligence(
    request: Request,
    related_company_id: UUID | None = None,
    focus_category: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = build_market_response_intelligence(db, related_company_id=related_company_id, focus_category=focus_category)
    return success_envelope(data, request_id=get_request_id(request))


@router.get("/response-reviews")
def get_market_response_reviews(
    request: Request,
    partner_focus: str | None = None,
    focus_category: str | None = None,
    visibility_class: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = build_market_response_review_console(
        db,
        actor,
        partner_focus=partner_focus,
        focus_category=focus_category,
        visibility_class=visibility_class,
        status=status,
    )
    return success_envelope(data, request_id=get_request_id(request))


@router.post("/response-reviews", status_code=status.HTTP_201_CREATED)
def post_market_response_review(
    payload: MarketResponseReviewCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = create_market_response_review(db, payload, actor)
    return success_envelope(data, request_id=get_request_id(request))


@router.patch("/response-reviews/{review_id}")
def patch_market_response_review(
    review_id: UUID,
    payload: MarketResponseReviewUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERM_MARKET_READ)),
):
    try:
        data = update_market_response_review(db, review_id, payload, actor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if data is None:
        raise HTTPException(status_code=404, detail="market response review not found")
    return success_envelope(data, request_id=get_request_id(request))
