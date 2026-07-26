from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import BenchmarkBrand, BenchmarkProductCapability, User
from app.schemas.multibrand_export import BenchmarkBrandDetailOut, BenchmarkBrandOut, BenchmarkCapabilityOut
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/benchmark-brands", tags=["benchmark-brands"])


@router.get("", response_model=PaginatedResponse[BenchmarkBrandOut])
def list_benchmark_brands(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    vertical: str | None = None,
) -> PaginatedResponse[BenchmarkBrandOut]:
    query = db.query(BenchmarkBrand).filter(BenchmarkBrand.is_active.is_(True))
    if vertical:
        query = query.filter(BenchmarkBrand.industry_vertical == vertical)
    total = query.count()
    rows = query.order_by(BenchmarkBrand.display_name).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(
        items=[BenchmarkBrandOut.model_validate(r) for r in rows], total=total, page=page, limit=limit
    )


@router.get("/{brand_id}", response_model=BenchmarkBrandDetailOut)
def get_benchmark_brand(
    brand_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> BenchmarkBrandDetailOut:
    row = db.query(BenchmarkBrand).filter(BenchmarkBrand.id == brand_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Benchmark brand not found")
    caps = (
        db.query(BenchmarkProductCapability)
        .filter(BenchmarkProductCapability.brand_id == brand_id)
        .order_by(BenchmarkProductCapability.capability_key)
        .all()
    )
    payload = BenchmarkBrandOut.model_validate(row).model_dump()
    payload["capabilities"] = [BenchmarkCapabilityOut.model_validate(c) for c in caps]
    return BenchmarkBrandDetailOut.model_validate(payload)
