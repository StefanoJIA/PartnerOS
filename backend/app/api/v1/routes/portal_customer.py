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
from app.core.permissions import PERM_PORTAL_READINESS, require_permission
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
from app.services.portal.customer_order_snapshot import build_customer_order_snapshot
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


def _portal_customer_endpoints() -> dict[str, str]:
    return {
        "manifest": "/api/v1/portal/customer/manifest",
        "products": "/api/v1/portal/customer/products",
        "orders": "/api/v1/portal/customer/orders",
        "order_detail": "/api/v1/portal/customer/orders/{order_id}",
        "order_snapshot": "/api/v1/portal/customer/orders/{order_id}/snapshot",
        "production": "/api/v1/portal/customer/orders/{order_id}/production",
        "shipment": "/api/v1/portal/customer/orders/{order_id}/shipment",
        "resources": "/api/v1/portal/customer/orders/{order_id}/resources",
        "feedback": "/api/v1/portal/customer/feedback",
    }


def _portal_customer_field_contract() -> dict[str, object]:
    return {
        "envelope": ["ok", "data", "error", "request_id"],
        "pagination": ["items", "total", "page", "limit"],
        "products": [
            "id",
            "internal_sku",
            "product_name",
            "product_category",
            "product_family",
            "description",
            "status",
            "uom",
            "currency",
            "default_incoterm",
            "image_url",
            "attributes",
        ],
        "order_summary": [
            "id",
            "order_number",
            "status",
            "order_date",
            "company_id",
            "company_name",
            "currency",
            "grand_total",
            "customer_confirmed_at",
            "ship_to_company",
            "ship_to_address",
        ],
        "order_detail": [
            "bill_to_company",
            "ship_to_name",
            "payment_terms",
            "shipping_terms",
            "customer_notes",
            "line_items",
        ],
        "line_item": [
            "id",
            "product_name",
            "product_category",
            "description",
            "quantity",
            "uom",
            "unit_price",
            "total_price",
            "currency",
            "incoterm",
            "status",
        ],
        "snapshot": [
            "order",
            "customer_status",
            "production",
            "shipment",
            "resources",
            "feedback",
            "safety",
        ],
        "customer_status": [
            "stage",
            "label",
            "order_confirmed",
            "production_started",
            "production_completed",
            "ready_to_ship",
            "shipped",
            "delivered",
            "current_step_index",
            "progress_steps",
            "planned_dates_are_guarantees",
        ],
        "customer_status_stages": [
            "pending_confirmation",
            "confirmed",
            "in_production",
            "ready_to_ship",
            "shipped",
            "delivered",
            "cancelled",
        ],
        "progress_step_states": ["complete", "current", "pending"],
        "production_item": ["milestone_type", "milestone_label", "sequence", "status", "planned_date", "actual_date"],
        "shipment_item": [
            "id",
            "status",
            "shipment_method",
            "carrier_name",
            "tracking_number",
            "tracking_url",
            "estimated_ship_date",
            "actual_ship_date",
            "estimated_arrival_date",
            "actual_arrival_date",
        ],
        "resource_item": ["id", "title", "category", "status", "filename", "mime", "size", "download_url", "created_at"],
        "feedback_create": [
            "order_id",
            "company_id",
            "feedback_type",
            "subject",
            "message",
            "priority",
            "customer_name",
            "customer_email",
        ],
        "feedback_create_response": [
            "ticket_number",
            "status",
            "feedback_received",
            "customer_notified",
            "automatic_reply_sent",
            "resolution_time_promised",
        ],
        "date_policy": {
            "planned_dates_are_guarantees": False,
            "planned_dates_label": "planned",
            "actual_dates_label": "actual",
        },
    }


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


@router.get("/manifest", dependencies=[Depends(require_portal_customer_access)])
def portal_customer_manifest(request: Request, settings: Settings = Depends(get_settings)):
    data = {
        "contract_version": "D8.1",
        "source_of_truth": "PartnerOS",
        "consumer": "service.intelli-opus.com",
        "public_base_url": settings.PUBLIC_BASE_URL.strip() or None,
        "auth": {
            "required": settings.PORTAL_CUSTOMER_API_REQUIRE_TOKEN,
            "header_name": "X-Portal-Customer-Token",
            "bearer_authorization_supported": True,
            "token_configured": bool(settings.PORTAL_CUSTOMER_API_TOKEN.strip()),
            "token_value_exposed": False,
        },
        "endpoints": _portal_customer_endpoints(),
        "field_contract": _portal_customer_field_contract(),
        "customer_visible_surfaces": ["products", "orders", "order_snapshot", "production", "shipment", "resources", "feedback"],
        "field_policy": {
            "allow_customer_visible_fields_only": True,
            "planned_dates_are_guarantees": False,
            "hidden_field_categories": [
                "internal pricing details",
                "supplier-private notes",
                "backend file locations",
                "credential values",
            ],
        },
        "safety": {
            "token_exposed": False,
            "automatic_customer_notification": False,
            "supplier_notified": False,
            "carrier_api_called": False,
            "order_status_mutated": False,
            "feedback_auto_reply_sent": False,
        },
    }
    return success_envelope(data, request_id=get_request_id(request))


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
    _: User = Depends(require_permission(PERM_PORTAL_READINESS)),
):
    data = {
        "enabled": settings.PORTAL_CUSTOMER_API_ENABLED,
        "require_token": settings.PORTAL_CUSTOMER_API_REQUIRE_TOKEN,
        "token_configured": bool(settings.PORTAL_CUSTOMER_API_TOKEN.strip()),
        "allowed_origins_configured": bool(settings.PORTAL_CUSTOMER_ALLOWED_ORIGINS.strip()),
        "public_base_url_configured": bool(settings.PUBLIC_BASE_URL.strip()),
        "public_base_url": settings.PUBLIC_BASE_URL.strip() or None,
        "cors_origins": settings.cors_origins_list,
        "endpoints": _portal_customer_endpoints(),
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


@router.get("/orders/{order_id}/snapshot", dependencies=[Depends(require_portal_customer_access)])
def portal_customer_order_snapshot(order_id: UUID, request: Request, db: Session = Depends(get_db)):
    return success_envelope(build_customer_order_snapshot(db, order_id), request_id=get_request_id(request))


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
