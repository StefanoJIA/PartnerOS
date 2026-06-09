"""D8.9 multi-brand partner onboarding routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.services.partner_onboarding import build_partner_onboarding

router = APIRouter(prefix="/partner-onboarding", tags=["v1-partner-onboarding"])


@router.get("")
def get_partner_onboarding(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    data = build_partner_onboarding(db)
    return success_envelope(data.model_dump(mode="json"), request_id=get_request_id(request))
