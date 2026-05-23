"""V1 system routes (readiness, doctor)."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.services.system.platform import build_doctor_payload, build_readiness_payload

router = APIRouter(prefix="/system", tags=["v1-system"])


@router.get("/readiness")
def get_system_readiness(request: Request):
    settings = get_settings()
    data = build_readiness_payload(settings)
    rid = get_request_id(request)
    return success_envelope(data, request_id=rid)


@router.get("/doctor")
def get_system_doctor(request: Request):
    settings = get_settings()
    started_at = getattr(request.app.state, "started_at", None)
    data = build_doctor_payload(settings, started_at=started_at)
    rid = get_request_id(request)
    return success_envelope(data, request_id=rid)
