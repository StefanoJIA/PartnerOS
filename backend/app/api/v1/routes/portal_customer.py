"""D7.7 customer portal bridge API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import SERVICE_UNAVAILABLE, VALIDATION_ERROR, ApiError
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.services.portal.customer_portal_bridge import (
    build_customer_order_detail,
    build_customer_order_list,
    build_customer_product_list,
    build_customer_production_view,
    build_customer_resource_view,
    build_customer_shipment_view,
    create_feedback_ticket,
)
from app.services.portal.order_resource_service import download_customer_resource, list_customer_order_resources

router = APIRouter(prefix="/portal/customer", tags=["v1-portal-customer"])


class PortalFeedbackIn(BaseModel):
    order_id: UUID | None = None
    company_id: UUID | None = None
    feedback_type: str = "general"
    subject: str
    message: str
    priority: str = "normal"
    customer_name: str | None = None
    customer_email: str | None = None


def require_portal_customer_access(
    authorization: str | None = Header(default=None),
    x_portal_customer_token: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.PORTAL_CUSTOMER_API_ENABLED:
        raise ApiError(
            SERVICE_UNAVAILABLE,
            "Customer portal bridge API is disabled",
            status_code=503,
        )
    if not settings.PORTAL_CUSTOMER_API_REQUIRE_TOKEN:
        return
    expected = settings.PORTAL_CUSTOMER_API_TOKEN.strip()
    if not expected:
        raise ApiError(
            SERVICE_UNAVAILABLE,
            "Customer portal bridge token is not configured",
            status_code=503,
        )
    supplied = (x_portal_customer_token or "").strip()
    if not supplied and authorization and authorization.lower().startswith("bearer "):
        supplied = authorization.split(" ", 1)[1].strip()
    if not supplied:
        raise ApiError(VALIDATION_ERROR, "Customer portal token required", status_code=401)
    if supplied != expected:
        raise ApiError(VALIDATION_ERROR, "Invalid customer portal token", status_code=403)


@router.get("/products", dependencies=[Depends(require_portal_customer_access)])
def portal_customer_products(
    request: Request,
    category: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    data = build_customer_product_list(db, category=category, search=search, page=page, limit=limit)
    return success_envelope(data, request_id=get_request_id(request))


@router.get("/readiness")
def portal_customer_readiness(
    request: Request,
    settings: Settings = Depends(get_settings),
    _: User = Depends(get_current_user),
):
    data = {
        "enabled": settings.PORTAL_CUSTOMER_API_ENABLED,
        "require_token": settings.PORTAL_CUSTOMER_API_REQUIRE_TOKEN,
        "token_configured": bool(settings.PORTAL_CUSTOMER_API_TOKEN.strip()),
        "allowed_origins_configured": bool(settings.PORTAL_CUSTOMER_ALLOWED_ORIGINS.strip()),
        "cors_origins": settings.cors_origins_list,
        "safety": {
            "token_exposed": False,
            "automatic_customer_notification": False,
            "forbidden_field_filter_enabled": True,
        },
    }
    return success_envelope(data, request_id=get_request_id(request))


@router.get("/orders", dependencies=[Depends(require_portal_customer_access)])
def portal_customer_orders(
    request: Request,
    company_id: UUID | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    data = build_customer_order_list(db, company_id=company_id, status=status, page=page, limit=limit)
    return success_envelope(data, request_id=get_request_id(request))


@router.get("/orders/{order_id}", dependencies=[Depends(require_portal_customer_access)])
def portal_customer_order_detail(order_id: UUID, request: Request, db: Session = Depends(get_db)):
    return success_envelope(build_customer_order_detail(db, order_id), request_id=get_request_id(request))


@router.get("/orders/{order_id}/production", dependencies=[Depends(require_portal_customer_access)])
def portal_customer_order_production(order_id: UUID, request: Request, db: Session = Depends(get_db)):
    return success_envelope(build_customer_production_view(db, order_id), request_id=get_request_id(request))


@router.get("/orders/{order_id}/shipment", dependencies=[Depends(require_portal_customer_access)])
def portal_customer_order_shipment(order_id: UUID, request: Request, db: Session = Depends(get_db)):
    return success_envelope(build_customer_shipment_view(db, order_id), request_id=get_request_id(request))


@router.get("/orders/{order_id}/resources", dependencies=[Depends(require_portal_customer_access)])
def portal_customer_order_resources(order_id: UUID, request: Request, db: Session = Depends(get_db)):
    return success_envelope(list_customer_order_resources(db, order_id), request_id=get_request_id(request))


@router.get("/resources/{resource_id}/download")
def portal_customer_resource_download(
    resource_id: UUID,
    expires_at: int,
    token: str,
    db: Session = Depends(get_db),
):
    return download_customer_resource(db, resource_id, expires_at=expires_at, token=token)


@router.post("/feedback", dependencies=[Depends(require_portal_customer_access)])
def portal_customer_feedback(body: PortalFeedbackIn, request: Request, db: Session = Depends(get_db)):
    data = create_feedback_ticket(
        db,
        order_id=body.order_id,
        company_id=body.company_id,
        feedback_type=body.feedback_type,
        subject=body.subject,
        message=body.message,
        priority=body.priority,
        customer_name=body.customer_name,
        customer_email=body.customer_email,
    )
    return success_envelope(data, request_id=get_request_id(request), status_code=201)
