"""Internal external execution collaboration routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import PERM_MARKET_READ, require_permission
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.schemas.external_execution import ExternalExecutionActionCreate, ExternalExecutionActionUpdate
from app.services.external_execution import (
    build_external_execution_console,
    create_external_execution_action,
    update_external_execution_action,
)

router = APIRouter(prefix="/external-execution", tags=["v1-external-execution"])


@router.get("/console")
def get_external_execution_console(
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = build_external_execution_console(db, actor)
    return success_envelope(data, request_id=get_request_id(request))


@router.post("/actions", status_code=status.HTTP_201_CREATED)
def post_external_execution_action(
    payload: ExternalExecutionActionCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = create_external_execution_action(db, payload, actor)
    return success_envelope(data, request_id=get_request_id(request))


@router.patch("/actions/{action_id}")
def patch_external_execution_action(
    action_id: UUID,
    payload: ExternalExecutionActionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERM_MARKET_READ)),
):
    try:
        data = update_external_execution_action(db, action_id, payload, actor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if data is None:
        raise HTTPException(status_code=404, detail="external execution action not found")
    return success_envelope(data, request_id=get_request_id(request))
