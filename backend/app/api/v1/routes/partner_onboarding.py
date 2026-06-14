"""D8.9 multi-brand partner onboarding routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.services.partner_onboarding import build_partner_onboarding, create_partner_market_response_reviews

router = APIRouter(prefix="/partner-onboarding", tags=["v1-partner-onboarding"])


@router.get("")
def get_partner_onboarding(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    data = build_partner_onboarding(db)
    return success_envelope(data.model_dump(mode="json"), request_id=get_request_id(request))


@router.post("/{partner_id}/market-response-reviews")
def post_partner_market_response_reviews(
    partner_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    data = create_partner_market_response_reviews(db, partner_id, actor)
    if not data.get("found"):
        raise HTTPException(status_code=404, detail="partner onboarding record not found")
    return success_envelope(data, request_id=get_request_id(request))
