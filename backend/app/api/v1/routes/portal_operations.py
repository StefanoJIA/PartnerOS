"""D8 internal Portal operations console routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.permissions import PERM_PORTAL_READINESS, require_permission
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.services.portal.operations_console import build_portal_operations_console

router = APIRouter(prefix="/portal/operations", tags=["v1-portal-operations"])


@router.get("/console")
def portal_operations_console(
    request: Request,
    recent_limit: int = Query(8, ge=1, le=25),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: User = Depends(require_permission(PERM_PORTAL_READINESS)),
):
    data = build_portal_operations_console(db, settings, recent_limit=recent_limit)
    return success_envelope(data, request_id=get_request_id(request))
