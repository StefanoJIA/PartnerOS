"""Commercial pilot operations API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import CommercialPilotRun, SupplierDevelopmentTask, User
from app.models.enums import CommercialPilotIndustry
from app.schemas.commercial_pilot import (
    CategoryCoverageOut,
    CommercialMetricsOut,
    CommercialPilotRunOut,
    EmailDraftOut,
    SupplierDevelopmentTaskCreate,
    SupplierDevelopmentTaskOut,
    SupplierDevelopmentTaskUpdate,
)
from app.schemas.pagination import PaginatedResponse
from app.services.commercial_pilot_service import (
    build_category_coverage,
    build_commercial_metrics,
    build_email_draft,
    create_development_task,
    get_latest_category_coverage,
    get_pilot_by_code,
    seed_standard_development_tasks,
    update_pilot_status,
)

router = APIRouter(prefix="/commercial-pilot", tags=["commercial-pilot"])


@router.get("/metrics", response_model=CommercialMetricsOut)
def commercial_metrics(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> CommercialMetricsOut:
    return CommercialMetricsOut(**build_commercial_metrics(db))


@router.get("/category-coverage", response_model=list[CategoryCoverageOut])
def list_category_coverage(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    industry: str | None = None,
) -> list[CategoryCoverageOut]:
    industries = [industry] if industry else [i.value for i in CommercialPilotIndustry]
    rows: list[CategoryCoverageOut] = []
    for ind in industries:
        row = get_latest_category_coverage(db, ind)
        if row:
            rows.append(CategoryCoverageOut.model_validate(row))
    return rows


@router.post("/category-coverage/{industry_vertical}/refresh", response_model=CategoryCoverageOut)
def refresh_category_coverage(
    industry_vertical: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CategoryCoverageOut:
    if industry_vertical not in {i.value for i in CommercialPilotIndustry}:
        raise HTTPException(status_code=400, detail="Unsupported industry vertical")
    row = build_category_coverage(db, industry_vertical=industry_vertical, actor_id=user.id)
    db.commit()
    db.refresh(row)
    return CategoryCoverageOut.model_validate(row)


@router.get("/pilots", response_model=list[CommercialPilotRunOut])
def list_pilots(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[CommercialPilotRunOut]:
    rows = db.query(CommercialPilotRun).order_by(CommercialPilotRun.created_at.desc()).all()
    return [CommercialPilotRunOut.model_validate(r) for r in rows]


@router.get("/pilots/{pilot_code}", response_model=CommercialPilotRunOut)
def get_pilot(pilot_code: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> CommercialPilotRunOut:
    row = get_pilot_by_code(db, pilot_code)
    if not row:
        raise HTTPException(status_code=404, detail="Pilot not found")
    return CommercialPilotRunOut.model_validate(row)


@router.get(
    "/supplier-discovery/{discovery_id}/tasks",
    response_model=PaginatedResponse[SupplierDevelopmentTaskOut],
)
def list_development_tasks(
    discovery_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[SupplierDevelopmentTaskOut]:
    query = db.query(SupplierDevelopmentTask).filter(SupplierDevelopmentTask.supplier_discovery_id == discovery_id)
    total = query.count()
    rows = query.order_by(SupplierDevelopmentTask.created_at.asc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(
        items=[SupplierDevelopmentTaskOut.model_validate(r) for r in rows],
        total=total,
        page=page,
        limit=limit,
    )


@router.post(
    "/supplier-discovery/{discovery_id}/tasks",
    response_model=SupplierDevelopmentTaskOut,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    discovery_id: UUID,
    body: SupplierDevelopmentTaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SupplierDevelopmentTaskOut:
    row = create_development_task(
        db,
        supplier_discovery_id=discovery_id,
        task_type=body.task_type,
        title=body.title,
        owner_user_id=body.owner_user_id or user.id,
        actor_id=user.id,
        priority=body.priority,
        due_days=body.due_days,
        depends_on_task_ids=body.depends_on_task_ids,
    )
    db.commit()
    db.refresh(row)
    return SupplierDevelopmentTaskOut.model_validate(row)


@router.post(
    "/supplier-discovery/{discovery_id}/tasks/seed-standard",
    response_model=list[SupplierDevelopmentTaskOut],
)
def seed_tasks(
    discovery_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[SupplierDevelopmentTaskOut]:
    rows = seed_standard_development_tasks(
        db, supplier_discovery_id=discovery_id, owner_user_id=user.id, actor_id=user.id
    )
    db.commit()
    return [SupplierDevelopmentTaskOut.model_validate(r) for r in rows]


@router.patch("/tasks/{task_id}", response_model=SupplierDevelopmentTaskOut)
def update_task(
    task_id: UUID,
    body: SupplierDevelopmentTaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SupplierDevelopmentTaskOut:
    row = db.query(SupplierDevelopmentTask).filter(SupplierDevelopmentTask.id == task_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    if body.status is not None:
        row.status = body.status
    if body.result_summary is not None:
        row.result_summary = body.result_summary
    if body.notes is not None:
        row.notes = body.notes
    if body.owner_user_id is not None:
        row.owner_user_id = body.owner_user_id
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    return SupplierDevelopmentTaskOut.model_validate(row)


@router.get("/tasks/{task_id}/email-draft", response_model=EmailDraftOut)
def get_task_email_draft(
    task_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> EmailDraftOut:
    row = db.query(SupplierDevelopmentTask).filter(SupplierDevelopmentTask.id == task_id).first()
    if not row or not row.email_draft_json:
        raise HTTPException(status_code=404, detail="Email draft not found")
    return EmailDraftOut(**row.email_draft_json)
