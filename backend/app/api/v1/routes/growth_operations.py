"""D8.13 growth operations routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import PERM_MARKET_READ, require_permission
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.services.growth_operations import build_growth_operations_console

router = APIRouter(prefix="/growth", tags=["v1-growth-operations"])


@router.get("/operations-console")
def get_growth_operations_console(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = build_growth_operations_console(db)
    return success_envelope(data, request_id=get_request_id(request))
