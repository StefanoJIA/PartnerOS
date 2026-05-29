"""D8.5 market response intelligence routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import PERM_MARKET_READ, require_permission
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.services.market_response_intelligence import build_market_response_intelligence

router = APIRouter(prefix="/market", tags=["v1-market-response"])


@router.get("/response-intelligence")
def get_market_response_intelligence(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = build_market_response_intelligence(db)
    return success_envelope(data, request_id=get_request_id(request))
