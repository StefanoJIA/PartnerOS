"""D8.4 multi-partner operations dashboard routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import PERM_ORDERS_READ, require_permission
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.services.orders.partner_operations_dashboard import build_partner_operations_dashboard

router = APIRouter(prefix="/operations", tags=["v1-operations"])


@router.get("/partner-dashboard")
def get_partner_operations_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERM_ORDERS_READ)),
):
    data = build_partner_operations_dashboard(db)
    return success_envelope(data, request_id=get_request_id(request))
