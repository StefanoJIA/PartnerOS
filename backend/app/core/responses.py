"""Unified JSON envelope for /api/v1 responses only."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi.responses import JSONResponse


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def meta_dict(
    *,
    request_id: str | None = None,
    pagination: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    m: dict[str, Any] = {
        "request_id": request_id,
        "timestamp": _utc_now_iso(),
        "pagination": pagination,
    }
    if extra:
        m.update(extra)
    return m


def success_envelope(
    data: Any,
    *,
    request_id: str | None = None,
    pagination: dict[str, Any] | None = None,
    status_code: int = 200,
) -> JSONResponse:
    body = {
        "ok": True,
        "data": data,
        "meta": meta_dict(request_id=request_id, pagination=pagination),
    }
    return JSONResponse(status_code=status_code, content=body)


def error_envelope(
    *,
    code: str,
    message: str,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
    status_code: int = 400,
) -> JSONResponse:
    body = {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "request_id": request_id,
        },
        "meta": meta_dict(request_id=request_id),
    }
    return JSONResponse(status_code=status_code, content=body)
