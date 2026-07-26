from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import SupplierSampleEvaluation, User
from app.schemas.multibrand_export import (
    SupplierSampleEvaluationCreate,
    SupplierSampleEvaluationOut,
    SupplierSampleEvaluationUpdate,
)
from app.schemas.pagination import PaginatedResponse
from app.services.supplier_network_service import create_sample_evaluation

router = APIRouter(prefix="/supplier-sample-evaluations", tags=["supplier-sample-evaluations"])


@router.get("", response_model=PaginatedResponse[SupplierSampleEvaluationOut])
def list_sample_evaluations(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    supplier_discovery_id: UUID | None = None,
    project_request_id: UUID | None = None,
) -> PaginatedResponse[SupplierSampleEvaluationOut]:
    query = db.query(SupplierSampleEvaluation)
    if supplier_discovery_id:
        query = query.filter(SupplierSampleEvaluation.supplier_discovery_id == supplier_discovery_id)
    if project_request_id:
        query = query.filter(SupplierSampleEvaluation.project_request_id == project_request_id)
    total = query.count()
    rows = query.order_by(SupplierSampleEvaluation.updated_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(
        items=[SupplierSampleEvaluationOut.model_validate(r) for r in rows], total=total, page=page, limit=limit
    )


@router.post("", response_model=SupplierSampleEvaluationOut, status_code=status.HTTP_201_CREATED)
def create_sample_evaluation_route(
    body: SupplierSampleEvaluationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SupplierSampleEvaluationOut:
    row = create_sample_evaluation(
        db,
        template_key=body.template_key,
        supplier_discovery_id=body.supplier_discovery_id,
        partner_id=body.partner_id,
        project_request_id=body.project_request_id,
        product_catalog_id=body.product_catalog_id,
        request_date=body.request_date,
        actor_id=user.id,
    )
    db.commit()
    db.refresh(row)
    return SupplierSampleEvaluationOut.model_validate(row)


@router.patch("/{evaluation_id}", response_model=SupplierSampleEvaluationOut)
def update_sample_evaluation(
    evaluation_id: UUID,
    body: SupplierSampleEvaluationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SupplierSampleEvaluationOut:
    row = db.query(SupplierSampleEvaluation).filter(SupplierSampleEvaluation.id == evaluation_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Sample evaluation not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    if body.overall_result:
        row.reviewer_user_id = user.id
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    return SupplierSampleEvaluationOut.model_validate(row)
