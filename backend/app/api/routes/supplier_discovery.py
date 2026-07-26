from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import SupplierDiscoveryRecord, User
from app.models.enums import SupplierDiscoveryStatus
from app.schemas.multibrand_export import SupplierDiscoveryCreate, SupplierDiscoveryOut, SupplierDiscoveryUpdate
from app.schemas.pagination import PaginatedResponse
from app.services.activity import log_activity

router = APIRouter(prefix="/supplier-discovery", tags=["supplier-discovery"])

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    SupplierDiscoveryStatus.discovered.value: {
        SupplierDiscoveryStatus.contacted.value,
        SupplierDiscoveryStatus.rejected.value,
        SupplierDiscoveryStatus.paused.value,
    },
    SupplierDiscoveryStatus.contacted.value: {
        SupplierDiscoveryStatus.evaluating.value,
        SupplierDiscoveryStatus.rejected.value,
        SupplierDiscoveryStatus.paused.value,
    },
    SupplierDiscoveryStatus.evaluating.value: {
        SupplierDiscoveryStatus.sample_requested.value,
        SupplierDiscoveryStatus.qualified.value,
        SupplierDiscoveryStatus.rejected.value,
        SupplierDiscoveryStatus.paused.value,
    },
    SupplierDiscoveryStatus.sample_requested.value: {
        SupplierDiscoveryStatus.qualified.value,
        SupplierDiscoveryStatus.rejected.value,
        SupplierDiscoveryStatus.paused.value,
    },
    SupplierDiscoveryStatus.qualified.value: {
        SupplierDiscoveryStatus.active.value,
        SupplierDiscoveryStatus.rejected.value,
        SupplierDiscoveryStatus.paused.value,
    },
    SupplierDiscoveryStatus.active.value: {SupplierDiscoveryStatus.paused.value},
    SupplierDiscoveryStatus.rejected.value: set(),
    SupplierDiscoveryStatus.paused.value: {SupplierDiscoveryStatus.evaluating.value},
}


@router.get("", response_model=PaginatedResponse[SupplierDiscoveryOut])
def list_supplier_discovery(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    q: str | None = None,
) -> PaginatedResponse[SupplierDiscoveryOut]:
    query = db.query(SupplierDiscoveryRecord)
    if status:
        query = query.filter(SupplierDiscoveryRecord.status == status)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(SupplierDiscoveryRecord.company_name.ilike(like), SupplierDiscoveryRecord.brand_name.ilike(like))
        )
    total = query.count()
    rows = query.order_by(SupplierDiscoveryRecord.updated_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(
        items=[SupplierDiscoveryOut.model_validate(r) for r in rows], total=total, page=page, limit=limit
    )


@router.post("", response_model=SupplierDiscoveryOut, status_code=status.HTTP_201_CREATED)
def create_supplier_discovery(
    body: SupplierDiscoveryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SupplierDiscoveryOut:
    row = SupplierDiscoveryRecord(
        **body.model_dump(),
        status=SupplierDiscoveryStatus.discovered.value,
        owner_user_id=user.id,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="supplier_discovery", object_id=row.id, action="created", actor_id=user.id)
    db.commit()
    return SupplierDiscoveryOut.model_validate(row)


@router.patch("/{record_id}", response_model=SupplierDiscoveryOut)
def update_supplier_discovery(
    record_id: UUID,
    body: SupplierDiscoveryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SupplierDiscoveryOut:
    row = db.query(SupplierDiscoveryRecord).filter(SupplierDiscoveryRecord.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Supplier discovery record not found")
    data = body.model_dump(exclude_unset=True)
    if "status" in data and data["status"] != row.status:
        allowed = ALLOWED_TRANSITIONS.get(row.status, set())
        if data["status"] not in allowed:
            raise HTTPException(status_code=400, detail=f"Illegal status transition from {row.status} to {data['status']}")
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    return SupplierDiscoveryOut.model_validate(row)
