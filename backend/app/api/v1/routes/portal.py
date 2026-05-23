"""V1 portal integration routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.services.system.platform import build_manifest_payload
from app.services.system.portal_integration import (
    build_a_domain_status_payload,
    build_portal_summary_payload,
)

router = APIRouter(prefix="/portal", tags=["v1-portal"])


@router.get("/manifest")
def get_portal_manifest(request: Request):
    settings = get_settings()
    data = build_manifest_payload(settings)
    rid = get_request_id(request)
    return success_envelope(data, request_id=rid)


@router.get("/summary")
def get_portal_summary(request: Request, db: Session = Depends(get_db)):
    """Read-only daily outreach / lead intelligence summary for external Portal."""
    settings = get_settings()
    data = build_portal_summary_payload(settings, db)
    rid = get_request_id(request)
    return success_envelope(data, request_id=rid)


@router.get("/a-domain/status")
def get_portal_a_domain_status(request: Request):
    """Read-only A-domain readiness flags for external Portal."""
    data = build_a_domain_status_payload()
    rid = get_request_id(request)
    return success_envelope(data, request_id=rid)
