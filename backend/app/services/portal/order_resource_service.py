"""D7.9 customer-safe order resource center service."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import NOT_FOUND, VALIDATION_ERROR, ApiError
from app.models import File, FileAttachment, OrderResource, User
from app.models.customer_orders import CustomerOrder
from app.services.activity import log_activity
from app.services.portal.customer_field_filter import (
    assert_no_forbidden_internal_fields,
    strip_forbidden_internal_fields,
)

RESOURCE_STATUSES = ("draft", "published", "archived")
RESOURCE_CATEGORIES = ("general", "quote_pdf", "packing_list", "spec_sheet", "certificate", "shipment", "other")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_payload(payload: dict) -> dict:
    cleaned = strip_forbidden_internal_fields(payload)
    assert_no_forbidden_internal_fields(cleaned)
    return cleaned


def _get_order(db: Session, order_id: UUID) -> CustomerOrder:
    row = db.query(CustomerOrder).filter(CustomerOrder.id == order_id).first()
    if not row:
        raise ApiError(NOT_FOUND, "Order not found", status_code=404)
    return row


def _get_file(db: Session, file_id: UUID) -> File:
    row = db.query(File).filter(File.id == file_id).first()
    if not row:
        raise ApiError(NOT_FOUND, "File not found", status_code=404)
    return row


def _get_resource(db: Session, order_id: UUID, resource_id: UUID) -> OrderResource:
    row = (
        db.query(OrderResource)
        .filter(OrderResource.id == resource_id, OrderResource.order_id == order_id)
        .first()
    )
    if not row:
        raise ApiError(NOT_FOUND, "Order resource not found", status_code=404)
    return row


def _signed_payload(resource_id: UUID, expires_at: int) -> str:
    return f"{resource_id}:{expires_at}"


def sign_resource_download(
    resource_id: UUID,
    *,
    settings: Settings | None = None,
    expires_in_minutes: int = 60,
) -> dict[str, str | int]:
    settings = settings or get_settings()
    expires_at = int((_now() + timedelta(minutes=expires_in_minutes)).timestamp())
    payload = _signed_payload(resource_id, expires_at)
    digest = hmac.new(settings.SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return {"expires_at": expires_at, "token": token}


def verify_resource_signature(resource_id: UUID, *, expires_at: int, token: str, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    if expires_at < int(_now().timestamp()):
        raise ApiError(VALIDATION_ERROR, "Resource download link expired", status_code=403)
    expected = sign_resource_download(
        resource_id,
        settings=settings,
        expires_in_minutes=max(1, int((expires_at - int(_now().timestamp())) / 60)),
    )["token"]
    # Recompute with exact expires_at to avoid minute-rounding differences.
    payload = _signed_payload(resource_id, expires_at)
    digest = hmac.new(settings.SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    expected = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    if not hmac.compare_digest(token, expected):
        raise ApiError(VALIDATION_ERROR, "Invalid resource download signature", status_code=403)


def resource_safety() -> dict[str, bool]:
    return {
        "customer_visible": False,
        "download_link_signed": True,
        "file_location_exposed": False,
        "filesystem_path_exposed": False,
        "customer_notified": False,
        "automatic_email_sent": False,
    }


def resource_to_dict(row: OrderResource, file: File, *, include_signed_url: bool = False) -> dict:
    safety = resource_safety()
    safety["customer_visible"] = bool(row.customer_visible and row.status == "published")
    payload = {
        "id": str(row.id),
        "order_id": str(row.order_id),
        "file_id": str(row.file_id),
        "title": row.title,
        "category": row.category,
        "description": row.description,
        "status": row.status,
        "customer_visible": row.customer_visible,
        "published_at": row.published_at.isoformat() if row.published_at else None,
        "filename": file.original_filename,
        "mime": file.mime,
        "size": file.size,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "safety": safety,
    }
    if include_signed_url and safety["customer_visible"]:
        signed = sign_resource_download(row.id)
        payload["download_url"] = (
            f"/api/v1/portal/customer/resources/{row.id}/download"
            f"?expires_at={signed['expires_at']}&token={signed['token']}"
        )
        payload["download_expires_at"] = signed["expires_at"]
    return _safe_payload(payload)


def list_order_resources(db: Session, order_id: UUID, *, include_archived: bool = False) -> dict:
    _get_order(db, order_id)
    q = (
        db.query(OrderResource, File)
        .join(File, File.id == OrderResource.file_id)
        .filter(OrderResource.order_id == order_id)
    )
    if not include_archived:
        q = q.filter(OrderResource.status != "archived")
    rows = q.order_by(OrderResource.created_at.desc()).all()
    return {
        "items": [resource_to_dict(row, file) for row, file in rows],
        "total": len(rows),
        "safety": {
            "customer_notified": False,
            "automatic_email_sent": False,
        },
    }


def list_customer_order_resources(db: Session, order_id: UUID) -> dict:
    _get_order(db, order_id)
    rows = (
        db.query(OrderResource, File)
        .join(File, File.id == OrderResource.file_id)
        .filter(
            OrderResource.order_id == order_id,
            OrderResource.status == "published",
            OrderResource.customer_visible.is_(True),
        )
        .order_by(OrderResource.published_at.desc().nullslast(), OrderResource.created_at.desc())
        .all()
    )
    return _safe_payload(
        {
            "order_id": str(order_id),
            "items": [resource_to_dict(row, file, include_signed_url=True) for row, file in rows],
            "total": len(rows),
        }
    )


def create_order_resource(
    db: Session,
    user: User,
    order_id: UUID,
    *,
    file_id: UUID,
    title: str | None = None,
    category: str = "general",
    description: str | None = None,
    customer_visible: bool = False,
) -> OrderResource:
    _get_order(db, order_id)
    file = _get_file(db, file_id)
    if category not in RESOURCE_CATEGORIES:
        raise ApiError(VALIDATION_ERROR, "Invalid resource category", status_code=400)
    att = FileAttachment(
        file_id=file_id,
        object_type="order",
        object_id=order_id,
        purpose=category,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(att)
    db.flush()
    row = OrderResource(
        order_id=order_id,
        file_id=file_id,
        file_attachment_id=att.id,
        title=(title or file.original_filename).strip()[:255],
        category=category,
        description=description.strip() if description else None,
        status="published" if customer_visible else "draft",
        customer_visible=customer_visible,
        published_at=_now() if customer_visible else None,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(
        db,
        object_type="order",
        object_id=order_id,
        action="order_resource_created",
        actor_id=user.id,
        diff={"resource_id": str(row.id), "file_id": str(file_id), "customer_visible": customer_visible},
    )
    db.commit()
    return row


def update_order_resource(
    db: Session,
    user: User,
    order_id: UUID,
    resource_id: UUID,
    *,
    title: str | None = None,
    category: str | None = None,
    description: str | None = None,
    status: str | None = None,
    customer_visible: bool | None = None,
) -> OrderResource:
    row = _get_resource(db, order_id, resource_id)
    previous = {"status": row.status, "customer_visible": row.customer_visible}
    if title is not None:
        cleaned = title.strip()
        if not cleaned:
            raise ApiError(VALIDATION_ERROR, "title is required", status_code=400)
        row.title = cleaned[:255]
    if category is not None:
        if category not in RESOURCE_CATEGORIES:
            raise ApiError(VALIDATION_ERROR, "Invalid resource category", status_code=400)
        row.category = category
    if description is not None:
        row.description = description.strip() or None
    if status is not None:
        if status not in RESOURCE_STATUSES:
            raise ApiError(VALIDATION_ERROR, "Invalid resource status", status_code=400)
        row.status = status
    if customer_visible is not None:
        row.customer_visible = customer_visible
    if row.status == "published" and row.customer_visible and not row.published_at:
        row.published_at = _now()
    if row.status != "published" or not row.customer_visible:
        row.published_at = None
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    log_activity(
        db,
        object_type="order",
        object_id=order_id,
        action="order_resource_updated",
        actor_id=user.id,
        diff={
            "resource_id": str(row.id),
            "previous": previous,
            "status": row.status,
            "customer_visible": row.customer_visible,
        },
    )
    db.commit()
    return row


def download_customer_resource(db: Session, resource_id: UUID, *, expires_at: int, token: str) -> FileResponse:
    verify_resource_signature(resource_id, expires_at=expires_at, token=token)
    row = (
        db.query(OrderResource, File)
        .join(File, File.id == OrderResource.file_id)
        .filter(
            OrderResource.id == resource_id,
            OrderResource.status == "published",
            OrderResource.customer_visible.is_(True),
        )
        .first()
    )
    if not row:
        raise ApiError(NOT_FOUND, "Resource not found", status_code=404)
    resource, file = row
    base = get_settings().UPLOAD_DIR
    path = os.path.join(base, file.storage_key)
    if not os.path.isfile(path):
        raise ApiError(NOT_FOUND, "Resource file missing", status_code=404)
    return FileResponse(path, filename=file.original_filename, media_type=file.mime or "application/octet-stream")
