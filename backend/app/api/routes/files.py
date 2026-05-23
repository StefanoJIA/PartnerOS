import hashlib
import os
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.object_type_http import parse_object_type_path
from app.models import File as FileModel
from app.models import FileAttachment, User
from app.schemas.objects import FileAttachBody, FileAttachmentOut, FileOut
from app.schemas.pagination import PaginatedResponse
from app.services.activity import log_activity

router = APIRouter(prefix="/files", tags=["files"])
objects_files_router = APIRouter(prefix="/objects", tags=["objects"])


def _ensure_upload_dir() -> str:
    settings = get_settings()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    return settings.UPLOAD_DIR


@router.post("/upload", response_model=FileOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FileOut:
    base = _ensure_upload_dir()
    raw = await upload.read()
    h = hashlib.sha256(raw).hexdigest()
    ext = os.path.splitext(upload.filename or "")[1][:16]
    storage_key = f"{user.id}/{h}{ext}"
    abs_path = os.path.join(base, storage_key)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(raw)
    row = FileModel(
        storage_key=storage_key,
        original_filename=upload.filename or "upload",
        mime=upload.content_type,
        size=len(raw),
        sha256=h,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="file", object_id=row.id, action="file_uploaded", actor_id=user.id)
    db.commit()
    return FileOut.model_validate(row)


@router.get("/{file_id}", response_model=FileOut)
def get_file_meta(
    file_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FileOut:
    row = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    return FileOut.model_validate(row)


@router.get("/{file_id}/download")
def download_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FileResponse:
    row = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    base = _ensure_upload_dir()
    path = os.path.join(base, row.storage_key)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File missing on disk")
    media_type = row.mime or "application/octet-stream"
    return FileResponse(path, filename=row.original_filename, media_type=media_type)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    base = _ensure_upload_dir()
    path = os.path.join(base, row.storage_key)
    if os.path.isfile(path):
        os.remove(path)
    db.query(FileAttachment).filter(FileAttachment.file_id == file_id).delete()
    db.delete(row)
    db.commit()
    log_activity(db, object_type="file", object_id=file_id, action="file_deleted", actor_id=user.id)
    db.commit()


@router.post("/{file_id}/attach", status_code=status.HTTP_204_NO_CONTENT)
def attach_file(
    file_id: UUID,
    body: FileAttachBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    ot = parse_object_type_path(body.object_type)
    att = FileAttachment(
        file_id=file_id,
        object_type=ot,
        object_id=body.object_id,
        purpose=body.purpose,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(att)
    db.commit()
    log_activity(
        db,
        object_type=ot,
        object_id=body.object_id,
        action="file_attached",
        actor_id=user.id,
        diff={"file_id": str(file_id)},
    )
    db.commit()


@objects_files_router.get("/{object_type}/{object_id}/files", response_model=PaginatedResponse[FileAttachmentOut])
def list_object_files(
    object_type: str,
    object_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[FileAttachmentOut]:
    ot = parse_object_type_path(object_type)
    q = (
        db.query(FileAttachment, FileModel)
        .join(FileModel, FileModel.id == FileAttachment.file_id)
        .filter(FileAttachment.object_type == ot, FileAttachment.object_id == object_id)
    )
    total = q.count()
    rows = (
        q.order_by(FileAttachment.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    items = [
        FileAttachmentOut(
            id=att.id,
            file_id=att.file_id,
            purpose=att.purpose,
            file=FileOut.model_validate(f),
        )
        for att, f in rows
    ]
    return PaginatedResponse(items=items, total=total, page=page, limit=limit)
