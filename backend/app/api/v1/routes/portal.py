"""V1 portal integration routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.services.system.platform import build_manifest_payload

router = APIRouter(prefix="/portal", tags=["v1-portal"])


@router.get("/manifest")
def get_portal_manifest(request: Request):
    settings = get_settings()
    data = build_manifest_payload(settings)
    rid = get_request_id(request)
    return success_envelope(data, request_id=rid)
