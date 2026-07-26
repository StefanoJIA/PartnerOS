"""V1 Quote PDF export routes (D6.4)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import ApiError, NOT_FOUND
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.models.customer_quotes import QuotePdfExport
from app.schemas.quotes import ExportPdfIn
from app.services.quotes.pdf_generator import export_record_to_dict, generate_quote_pdf
from app.services.quotes.quote_service import get_quote

router = APIRouter(prefix="/quotes", tags=["v1-quote-pdf"])


@router.post("/{quote_id}/export-pdf")
def export_quote_pdf_route(
    quote_id: UUID,
    body: ExportPdfIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_quote(db, quote_id)
    result = generate_quote_pdf(
        db,
        quote_id,
        version_id=body.quote_version_id,
        export_type=body.export_type,
        user=user,
    )
    rid = get_request_id(request)
    payload = {
        "export_id": result["export_id"],
        "file_name": result["file_name"],
        "content_type": result["content_type"],
        "file_size_bytes": result["file_size_bytes"],
        "download_url": f"/api/v1/quotes/{quote_id}/pdf-exports/{result['export_id']}/download",
        "safety": result["safety"],
    }
    return success_envelope(payload, request_id=rid, status_code=201)


@router.get("/{quote_id}/pdf-exports")
def list_quote_pdf_exports_route(
    quote_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    get_quote(db, quote_id)
    rows = (
        db.query(QuotePdfExport)
        .filter(QuotePdfExport.quote_id == quote_id, QuotePdfExport.status != "deleted")
        .order_by(QuotePdfExport.exported_at.desc().nullslast(), QuotePdfExport.created_at.desc())
        .all()
    )
    items = [export_record_to_dict(r, quote_id=quote_id) for r in rows]
    rid = get_request_id(request)
    return success_envelope({"items": items, "total": len(items)}, request_id=rid)


@router.get("/{quote_id}/pdf-exports/{export_id}/download")
def download_quote_pdf_route(
    quote_id: UUID,
    export_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    record = (
        db.query(QuotePdfExport)
        .filter(QuotePdfExport.id == export_id, QuotePdfExport.quote_id == quote_id)
        .first()
    )
    if not record or record.status != "generated":
        raise ApiError(NOT_FOUND, "pdf export not found", status_code=404)
    if not record.file_path or not Path(record.file_path).is_file():
        raise ApiError(NOT_FOUND, "pdf file not found", status_code=404)
    return FileResponse(
        path=record.file_path,
        media_type=record.content_type or "application/pdf",
        filename=record.file_name,
    )


@router.delete("/{quote_id}/pdf-exports/{export_id}")
def delete_quote_pdf_export_route(
    quote_id: UUID,
    export_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    get_quote(db, quote_id)
    record = (
        db.query(QuotePdfExport)
        .filter(QuotePdfExport.id == export_id, QuotePdfExport.quote_id == quote_id)
        .first()
    )
    if not record or record.status == "deleted":
        raise ApiError(NOT_FOUND, "pdf export not found", status_code=404)

    removed_file = False
    file_path = Path(record.file_path) if record.file_path else None
    if file_path and file_path.is_file():
        file_path.unlink()
        removed_file = True

    record.status = "deleted"
    record.file_path = None
    record.file_size_bytes = 0
    stamp = datetime.now(timezone.utc).isoformat()
    record.notes = f"{record.notes or ''}\nDeleted by operator at {stamp}; file_removed={removed_file}".strip()
    db.commit()

    rid = get_request_id(request)
    return success_envelope(
        {
            "deleted": True,
            "export_id": str(export_id),
            "file_removed": removed_file,
            "safety": {
                "automatic_sending_enabled": False,
                "quote_status_changed": False,
                "order_created": False,
                "customer_notified": False,
            },
        },
        request_id=rid,
        status_code=status.HTTP_200_OK,
    )
