"""V1 product catalog routes (D6.2)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import ApiError, NOT_FOUND
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import ManufacturingPartner, ProductCatalog, ProductPriceTier, User
from app.schemas.quote_catalog import ProductCatalogCreate, ProductCatalogOut, ProductCatalogUpdate

router = APIRouter(prefix="/products", tags=["v1-products"])


def _configuration_summary(attrs: dict | None) -> dict | None:
    if not attrs:
        return None
    specs = attrs.get("product_specs") or {}
    model = attrs.get("configuration_model") or {}
    colors = attrs.get("color_options_summary") or {}
    inventory = attrs.get("inventory_snapshot") or []
    return {
        "source_system": attrs.get("source_system") or attrs.get("pricing_model_source"),
        "customer_quote_name": attrs.get("customer_quote_name"),
        "base_type": model.get("base_type"),
        "stage": model.get("stage") or specs.get("stages"),
        "column_type": model.get("column_type"),
        "dimensions": model.get("dimensions") or specs.get("specification"),
        "load_capacity": specs.get("load_capacity"),
        "lifting_range": specs.get("lifting_range"),
        "lifting_speed": specs.get("lifting_speed"),
        "package_size": specs.get("package_size"),
        "total_available_colors": colors.get("total_available_colors"),
        "inventory_reference_count": len(inventory) if isinstance(inventory, list) else 0,
        "inventory_not_promised": True,
    }


def _product_payload(
    row: ProductCatalog,
    *,
    partner: ManufacturingPartner | None,
    quote_interval_count: int,
) -> dict:
    payload = ProductCatalogOut.model_validate(row).model_dump(mode="json")
    payload["partner_code"] = partner.partner_code if partner else None
    payload["partner_name"] = partner.partner_name if partner else None
    payload["quote_interval_count"] = quote_interval_count
    payload["has_interval_pricing"] = quote_interval_count > 0
    payload["configuration_summary"] = _configuration_summary(row.attributes_json)
    return payload


@router.get("")
def list_products(
    request: Request,
    partner_id: UUID | None = None,
    partner_code: str | None = None,
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
    if partner_code:
        partner = (
            db.query(ManufacturingPartner)
            .filter(ManufacturingPartner.partner_code.ilike(partner_code.strip()))
            .first()
        )
        if not partner:
            q = q.filter(False)
        else:
            q = q.filter(ProductCatalog.partner_id == partner.id)
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
    rows = (
        q.order_by(ProductCatalog.image_url.is_(None).asc(), ProductCatalog.product_name.asc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    partner_ids = {r.partner_id for r in rows}
    product_ids = [r.id for r in rows]
    partners = {
        p.id: p
        for p in db.query(ManufacturingPartner).filter(ManufacturingPartner.id.in_(partner_ids)).all()
    } if partner_ids else {}
    tier_counts = {
        product_id: count
        for product_id, count in (
            db.query(ProductPriceTier.product_id, func.count(ProductPriceTier.id))
            .filter(ProductPriceTier.product_id.in_(product_ids))
            .group_by(ProductPriceTier.product_id)
            .all()
            if product_ids
            else []
        )
    }
    items = [
        _product_payload(r, partner=partners.get(r.partner_id), quote_interval_count=int(tier_counts.get(r.id, 0)))
        for r in rows
    ]
    rid = get_request_id(request)
    return success_envelope(
        {"items": items, "total": total, "page": page, "limit": limit},
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
    partner = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == row.partner_id).first()
    quote_interval_count = (
        db.query(func.count(ProductPriceTier.id)).filter(ProductPriceTier.product_id == row.id).scalar() or 0
    )
    rid = get_request_id(request)
    return success_envelope(
        _product_payload(row, partner=partner, quote_interval_count=int(quote_interval_count)),
        request_id=rid,
    )


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
