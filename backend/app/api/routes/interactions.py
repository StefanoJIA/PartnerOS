from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.object_type_http import parse_object_type_path
from app.models import Interaction, Task, User
from app.schemas.crm import InteractionCreate, InteractionOut, InteractionSpawnTaskBody, TaskOut
from app.schemas.pagination import PaginatedResponse
from app.services.activity import log_activity

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.get("", response_model=PaginatedResponse[InteractionOut])
def list_interactions(
    object_type: str | None = None,
    object_id: UUID | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[InteractionOut]:
    q = db.query(Interaction)
    if object_type:
        q = q.filter(Interaction.related_object_type == object_type)
    if object_id:
        q = q.filter(Interaction.related_object_id == object_id)
    total = q.count()
    rows = q.order_by(Interaction.interaction_date.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(items=[InteractionOut.model_validate(r) for r in rows], total=total, page=page, limit=limit)


@router.post("", response_model=InteractionOut, status_code=status.HTTP_201_CREATED)
def create_interaction(
    body: InteractionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InteractionOut:
    payload = body.model_dump()
    payload["related_object_type"] = parse_object_type_path(payload["related_object_type"])
    if payload.get("interaction_date") is None:
        payload.pop("interaction_date", None)
    row = Interaction(**payload, created_by_id=user.id, updated_by_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(
        db,
        object_type=row.related_object_type,
        object_id=row.related_object_id,
        action="interaction_created",
        actor_id=user.id,
        diff={"interaction_id": str(row.id)},
    )
    db.commit()
    return InteractionOut.model_validate(row)


@router.post("/{interaction_id}/spawn-task", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def spawn_task_from_interaction(
    interaction_id: UUID,
    body: InteractionSpawnTaskBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskOut:
    intr = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not intr:
        raise HTTPException(status_code=404, detail="Interaction not found")
    title = body.title or (intr.subject or f"Follow up: {intr.interaction_type}")
    desc = f"From interaction {intr.id}"
    if intr.summary:
        desc += "\n\n" + intr.summary
    elif intr.content:
        desc += "\n\n" + intr.content[:4000]
    row = Task(
        title=title[:512],
        description=desc[:8000],
        related_object_type=intr.related_object_type,
        related_object_id=intr.related_object_id,
        assignee_user_id=body.assignee_user_id,
        due_at=body.due_at,
        status="open",
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(
        db,
        object_type="task",
        object_id=row.id,
        action="task_created",
        actor_id=user.id,
        diff={"from_interaction_id": str(intr.id)},
    )
    log_activity(
        db,
        object_type=intr.related_object_type,
        object_id=intr.related_object_id,
        action="interaction_spawned_task",
        actor_id=user.id,
        diff={"task_id": str(row.id), "interaction_id": str(intr.id)},
    )
    db.commit()
    return TaskOut.model_validate(row)
