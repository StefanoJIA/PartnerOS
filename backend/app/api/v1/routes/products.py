"""V1 product catalog routes (D6.2)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import ApiError, NOT_FOUND
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import ProductCatalog, User
from app.schemas.quote_catalog import ProductCatalogCreate, ProductCatalogOut, ProductCatalogUpdate

router = APIRouter(prefix="/products", tags=["v1-products"])


@router.get("")
def list_products(
    request: Request,
    partner_id: UUID | None = None,
    category: str | None = None,
    status: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(ProductCatalog)
    if partner_id:
        q = q.filter(ProductCatalog.partner_id == partner_id)
    if category:
        q = q.filter(ProductCatalog.product_category == category)
    if status:
        q = q.filter(ProductCatalog.status == status)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(
            ProductCatalog.product_name.ilike(like)
            | ProductCatalog.internal_sku.ilike(like)
            | ProductCatalog.partner_product_code.ilike(like)
        )
    total = q.count()
    rows = q.order_by(ProductCatalog.product_name.asc()).offset((page - 1) * limit).limit(limit).all()
    items = [ProductCatalogOut.model_validate(r) for r in rows]
    rid = get_request_id(request)
    return success_envelope(
        {"items": [i.model_dump(mode="json") for i in items], "total": total, "page": page, "limit": limit},
        request_id=rid,
        pagination={"page": page, "limit": limit, "total": total},
    )


@router.get("/{product_id}")
def get_product(
    product_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    row = db.query(ProductCatalog).filter(ProductCatalog.id == product_id).first()
    if not row:
        raise ApiError(NOT_FOUND, "product not found", status_code=404)
    rid = get_request_id(request)
    return success_envelope(ProductCatalogOut.model_validate(row).model_dump(mode="json"), request_id=rid)


@router.post("")
def create_product(
    body: ProductCatalogCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = ProductCatalog(**body.model_dump(), created_by_id=user.id, updated_by_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    rid = get_request_id(request)
    return success_envelope(
        ProductCatalogOut.model_validate(row).model_dump(mode="json"),
        request_id=rid,
        status_code=201,
    )


@router.patch("/{product_id}")
def update_product(
    product_id: UUID,
    body: ProductCatalogUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.query(ProductCatalog).filter(ProductCatalog.id == product_id).first()
    if not row:
        raise ApiError(NOT_FOUND, "product not found", status_code=404)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    rid = get_request_id(request)
    return success_envelope(ProductCatalogOut.model_validate(row).model_dump(mode="json"), request_id=rid)
