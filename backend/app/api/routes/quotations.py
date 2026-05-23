from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Quotation, User
from app.schemas.pagination import PaginatedResponse
from app.schemas.quotation_domain import QuotationCreate, QuotationOut, QuotationUpdate
from app.services.activity import log_activity

router = APIRouter(prefix="/quotations", tags=["quotations"])


@router.get("", response_model=PaginatedResponse[QuotationOut])
def list_quotations(
    rfq_id: UUID | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[QuotationOut]:
    q = db.query(Quotation)
    if rfq_id:
        q = q.filter(Quotation.rfq_id == rfq_id)
    total = q.count()
    rows = q.order_by(Quotation.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(items=[QuotationOut.model_validate(r) for r in rows], total=total, page=page, limit=limit)


@router.post("", response_model=QuotationOut, status_code=status.HTTP_201_CREATED)
def create_quotation(
    body: QuotationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QuotationOut:
    row = Quotation(**body.model_dump(), created_by_id=user.id, updated_by_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    if row.rfq_id:
        log_activity(
            db,
            object_type="rfq",
            object_id=row.rfq_id,
            action="quotation_added",
            actor_id=user.id,
            diff={"quotation_id": str(row.id)},
        )
        db.commit()
    return QuotationOut.model_validate(row)


@router.get("/{quotation_id}", response_model=QuotationOut)
def get_quotation(
    quotation_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> QuotationOut:
    row = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return QuotationOut.model_validate(row)


@router.put("/{quotation_id}", response_model=QuotationOut)
def update_quotation(
    quotation_id: UUID,
    body: QuotationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QuotationOut:
    row = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    if row.rfq_id:
        log_activity(
            db,
            object_type="rfq",
            object_id=row.rfq_id,
            action="quotation_updated",
            actor_id=user.id,
            diff={"quotation_id": str(row.id)},
        )
        db.commit()
    return QuotationOut.model_validate(row)


@router.delete("/{quotation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quotation(
    quotation_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    rfq_id = row.rfq_id
    db.delete(row)
    db.commit()
    if rfq_id:
        log_activity(
            db,
            object_type="rfq",
            object_id=rfq_id,
            action="quotation_deleted",
            actor_id=user.id,
            diff={"quotation_id": str(quotation_id)},
        )
        db.commit()
