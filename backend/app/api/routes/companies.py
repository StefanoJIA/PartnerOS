from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Company, User
from app.schemas.crm import CompanyCreate, CompanyOut, CompanyUpdate
from app.schemas.object_workspaces import CompanyWorkspaceOut
from app.schemas.pagination import PaginatedResponse
from app.services.activity import log_activity
from app.services.workspaces import build_company_workspace

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=PaginatedResponse[CompanyOut])
def list_companies(
    q: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[CompanyOut]:
    query = db.query(Company).filter(Company.is_active.is_(True))
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(Company.company_name.ilike(like), Company.industry.ilike(like), Company.city.ilike(like))
        )
    total = query.count()
    items = query.order_by(Company.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(
        items=[CompanyOut.model_validate(x) for x in items], total=total, page=page, limit=limit
    )


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(
    body: CompanyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CompanyOut:
    row = Company(**body.model_dump(), created_by_id=user.id, updated_by_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="company", object_id=row.id, action="company_created", actor_id=user.id)
    db.commit()
    return CompanyOut.model_validate(row)


@router.get("/{company_id}/workspace", response_model=CompanyWorkspaceOut)
def get_company_workspace(
    company_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CompanyWorkspaceOut:
    ws = build_company_workspace(db, company_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Company not found")
    return ws


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CompanyOut:
    row = db.query(Company).filter(Company.id == company_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyOut.model_validate(row)


@router.put("/{company_id}", response_model=CompanyOut)
def update_company(
    company_id: UUID,
    body: CompanyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CompanyOut:
    row = db.query(Company).filter(Company.id == company_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="company", object_id=row.id, action="company_updated", actor_id=user.id, diff=data)
    db.commit()
    return CompanyOut.model_validate(row)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = db.query(Company).filter(Company.id == company_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
    row.is_active = False
    row.updated_by_id = user.id
    db.commit()
    log_activity(db, object_type="company", object_id=row.id, action="soft_deleted", actor_id=user.id)
    db.commit()
