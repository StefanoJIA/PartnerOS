from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import FieldVisitPlan, FieldVisitTarget, User
from app.schemas.ai import GenericAIRequest
from app.schemas.field_visits_domain import (
    FieldVisitPlanCreate,
    FieldVisitPlanOut,
    FieldVisitPlanUpdate,
    FieldVisitTargetCreate,
    FieldVisitTargetOut,
    FieldVisitTargetUpdate,
)
from app.schemas.pagination import PaginatedResponse
from app.services.ai import client as ai_client
from app.services.ai import prompts as prompt_lib

router = APIRouter(prefix="/field-visits", tags=["field-visits"])


@router.get("", response_model=PaginatedResponse[FieldVisitPlanOut])
def list_plans(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[FieldVisitPlanOut]:
    q = db.query(FieldVisitPlan)
    total = q.count()
    rows = q.order_by(FieldVisitPlan.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(
        items=[FieldVisitPlanOut.model_validate(r) for r in rows], total=total, page=page, limit=limit
    )


@router.post("", response_model=FieldVisitPlanOut, status_code=status.HTTP_201_CREATED)
def create_plan(
    body: FieldVisitPlanCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FieldVisitPlanOut:
    row = FieldVisitPlan(**body.model_dump(), created_by_id=user.id, updated_by_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return FieldVisitPlanOut.model_validate(row)


@router.get("/{plan_id}", response_model=FieldVisitPlanOut)
def get_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FieldVisitPlanOut:
    row = db.query(FieldVisitPlan).filter(FieldVisitPlan.id == plan_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")
    return FieldVisitPlanOut.model_validate(row)


@router.put("/{plan_id}", response_model=FieldVisitPlanOut)
def update_plan(
    plan_id: UUID,
    body: FieldVisitPlanUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FieldVisitPlanOut:
    row = db.query(FieldVisitPlan).filter(FieldVisitPlan.id == plan_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    return FieldVisitPlanOut.model_validate(row)


@router.post("/{plan_id}/ai-brief")
def ai_brief(
    plan_id: UUID,
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    row = db.query(FieldVisitPlan).filter(FieldVisitPlan.id == plan_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")
    targets = db.query(FieldVisitTarget).filter(FieldVisitTarget.visit_plan_id == plan_id).all()
    ctx = {
        "city": row.city or "",
        "purpose": row.purpose or "",
        "sample_items": row.sample_items or "",
        "targets": str(len(targets)),
        **body.context,
    }
    msgs = prompt_lib.field_visit_brief_prompt(ctx)
    text = ai_client.chat_completion(msgs)
    row.ai_visit_brief = text
    row.updated_by_id = user.id
    db.commit()
    return {"brief": text}


@router.post("/{plan_id}/targets", response_model=FieldVisitTargetOut, status_code=status.HTTP_201_CREATED)
def add_target(
    plan_id: UUID,
    body: FieldVisitTargetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FieldVisitTargetOut:
    plan = db.query(FieldVisitPlan).filter(FieldVisitPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    row = FieldVisitTarget(visit_plan_id=plan_id, **body.model_dump(), created_by_id=user.id, updated_by_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return FieldVisitTargetOut.model_validate(row)


@router.put("/{plan_id}/targets/{target_id}", response_model=FieldVisitTargetOut)
def update_target(
    plan_id: UUID,
    target_id: UUID,
    body: FieldVisitTargetUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FieldVisitTargetOut:
    row = (
        db.query(FieldVisitTarget)
        .filter(FieldVisitTarget.id == target_id, FieldVisitTarget.visit_plan_id == plan_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Target not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    return FieldVisitTargetOut.model_validate(row)
