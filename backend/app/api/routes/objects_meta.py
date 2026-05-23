from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.object_type_http import parse_object_type_path
from app.models import ActivityLog, Note, ObjectTag, Tag, User
from app.schemas.objects import (
    ActivityOut,
    NoteCreate,
    NoteOut,
    NoteUpdate,
    ObjectTagBody,
    ObjectTagOut,
    TagCreate,
    TagOut,
)
from app.schemas.pagination import PaginatedResponse
from app.services.activity import log_activity

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=PaginatedResponse[TagOut])
def list_tags(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[TagOut]:
    q = db.query(Tag)
    total = q.count()
    rows = q.order_by(Tag.name).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(items=[TagOut.model_validate(r) for r in rows], total=total, page=page, limit=limit)


@router.post("", response_model=TagOut, status_code=status.HTTP_201_CREATED)
def create_tag(
    body: TagCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TagOut:
    row = Tag(**body.model_dump(), created_by_id=user.id, updated_by_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return TagOut.model_validate(row)


notes_router = APIRouter(prefix="/objects", tags=["objects"])
tags_attach_router = APIRouter(prefix="/objects", tags=["objects"])
activity_router = APIRouter(prefix="/objects", tags=["objects"])


@notes_router.get("/{object_type}/{object_id}/notes", response_model=PaginatedResponse[NoteOut])
def list_notes(
    object_type: str,
    object_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[NoteOut]:
    ot = parse_object_type_path(object_type)
    q = db.query(Note).filter(Note.object_type == ot, Note.object_id == object_id)
    total = q.count()
    rows = q.order_by(Note.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(items=[NoteOut.model_validate(r) for r in rows], total=total, page=page, limit=limit)


@notes_router.post("/{object_type}/{object_id}/notes", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(
    object_type: str,
    object_id: UUID,
    body: NoteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NoteOut:
    ot = parse_object_type_path(object_type)
    row = Note(
        object_type=ot,
        object_id=object_id,
        body=body.body,
        author_id=user.id,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(
        db,
        object_type=ot,
        object_id=object_id,
        action="note_created",
        actor_id=user.id,
        diff={"note_id": str(row.id)},
    )
    db.commit()
    return NoteOut.model_validate(row)


@notes_router.put("/{object_type}/{object_id}/notes/{note_id}", response_model=NoteOut)
def update_note(
    object_type: str,
    object_id: UUID,
    note_id: UUID,
    body: NoteUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NoteOut:
    ot = parse_object_type_path(object_type)
    row = (
        db.query(Note)
        .filter(Note.id == note_id, Note.object_type == ot, Note.object_id == object_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Note not found")
    row.body = body.body
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    log_activity(
        db,
        object_type=ot,
        object_id=object_id,
        action="note_updated",
        actor_id=user.id,
        diff={"note_id": str(row.id)},
    )
    db.commit()
    return NoteOut.model_validate(row)


@notes_router.delete("/{object_type}/{object_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    object_type: str,
    object_id: UUID,
    note_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    ot = parse_object_type_path(object_type)
    row = (
        db.query(Note)
        .filter(Note.id == note_id, Note.object_type == ot, Note.object_id == object_id)
        .first()
    )
    if row:
        log_activity(
            db,
            object_type=ot,
            object_id=object_id,
            action="note_deleted",
            actor_id=user.id,
            diff={"note_id": str(note_id)},
        )
        db.delete(row)
        db.commit()


@tags_attach_router.get("/{object_type}/{object_id}/tags", response_model=PaginatedResponse[ObjectTagOut])
def list_object_tags(
    object_type: str,
    object_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[ObjectTagOut]:
    ot = parse_object_type_path(object_type)
    q = (
        db.query(ObjectTag)
        .options(joinedload(ObjectTag.tag))
        .filter(ObjectTag.object_type == ot, ObjectTag.object_id == object_id)
    )
    total = q.count()
    rows = q.order_by(ObjectTag.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    items = [
        ObjectTagOut(object_tag_id=r.id, tag=TagOut.model_validate(r.tag)) for r in rows
    ]
    return PaginatedResponse(items=items, total=total, page=page, limit=limit)


@tags_attach_router.post("/{object_type}/{object_id}/tags", status_code=status.HTTP_204_NO_CONTENT)
def attach_tag(
    object_type: str,
    object_id: UUID,
    body: ObjectTagBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    ot = parse_object_type_path(object_type)
    exists = (
        db.query(ObjectTag)
        .filter(
            ObjectTag.object_type == ot,
            ObjectTag.object_id == object_id,
            ObjectTag.tag_id == body.tag_id,
        )
        .first()
    )
    if exists:
        return None
    row = ObjectTag(
        object_type=ot,
        object_id=object_id,
        tag_id=body.tag_id,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(row)
    db.commit()
    log_activity(
        db,
        object_type=ot,
        object_id=object_id,
        action="tag_attached",
        actor_id=user.id,
        diff={"tag_id": str(body.tag_id)},
    )
    db.commit()


@tags_attach_router.delete("/{object_type}/{object_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def detach_tag(
    object_type: str,
    object_id: UUID,
    tag_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    ot = parse_object_type_path(object_type)
    row = (
        db.query(ObjectTag)
        .filter(
            ObjectTag.object_type == ot,
            ObjectTag.object_id == object_id,
            ObjectTag.tag_id == tag_id,
        )
        .first()
    )
    if row:
        log_activity(
            db,
            object_type=ot,
            object_id=object_id,
            action="tag_detached",
            actor_id=user.id,
            diff={"tag_id": str(tag_id)},
        )
        db.delete(row)
        db.commit()


@activity_router.get("/{object_type}/{object_id}/activity", response_model=PaginatedResponse[ActivityOut])
def list_activity(
    object_type: str,
    object_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[ActivityOut]:
    ot = parse_object_type_path(object_type)
    q = db.query(ActivityLog).filter(ActivityLog.object_type == ot, ActivityLog.object_id == object_id)
    total = q.count()
    rows = q.order_by(ActivityLog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(items=[ActivityOut.model_validate(r) for r in rows], total=total, page=page, limit=limit)
