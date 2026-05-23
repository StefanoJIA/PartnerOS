"""Request ID propagation for v1 API meta and error envelopes."""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"


def generate_request_id() -> str:
    return str(uuid.uuid4())


def get_request_id(request: Request) -> str:
    rid = getattr(request.state, "request_id", None)
    if rid:
        return str(rid)
    incoming = request.headers.get(REQUEST_ID_HEADER)
    if incoming and incoming.strip():
        return incoming.strip()
    return generate_request_id()


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request.state.request_id = (
            incoming.strip() if incoming and incoming.strip() else generate_request_id()
        )
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request.state.request_id
        return response
