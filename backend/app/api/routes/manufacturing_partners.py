from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import ManufacturingPartner, Product, User
from app.schemas.object_workspaces import PartnerWorkspaceOut
from app.schemas.pagination import PaginatedResponse
from app.schemas.partners import PartnerCreate, PartnerDetailOut, PartnerOut, PartnerScoreBody, PartnerUpdate
from app.schemas.products import PartnerProductLinkBody, ProductDetailOut, ProductPartnerLinkBody, ProductPartnerLinkUpdate
from app.services.activity import log_activity
from app.services.product_partner_links import (
    delete_product_partner_link,
    ensure_product_partner_exist,
    update_product_partner_link,
    upsert_product_partner_link,
)
from app.services.workspaces import build_partner_workspace

router = APIRouter(prefix="/manufacturing-partners", tags=["manufacturing-partners"])


@router.get("", response_model=PaginatedResponse[PartnerOut])
def list_partners(
    q: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[PartnerOut]:
    query = db.query(ManufacturingPartner).filter(ManufacturingPartner.is_active.is_(True))
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(ManufacturingPartner.partner_name.ilike(like), ManufacturingPartner.brand_name.ilike(like))
        )
    total = query.count()
    rows = query.order_by(ManufacturingPartner.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(items=[PartnerOut.model_validate(r) for r in rows], total=total, page=page, limit=limit)


@router.post("", response_model=PartnerOut, status_code=status.HTTP_201_CREATED)
def create_partner(
    body: PartnerCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PartnerOut:
    row = ManufacturingPartner(**body.model_dump(), created_by_id=user.id, updated_by_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="manufacturing_partner", object_id=row.id, action="partner_created", actor_id=user.id)
    db.commit()
    return PartnerOut.model_validate(row)


@router.get("/{partner_id}/workspace", response_model=PartnerWorkspaceOut)
def get_partner_workspace(
    partner_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PartnerWorkspaceOut:
    ws = build_partner_workspace(db, partner_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Partner not found")
    return ws


@router.get("/{partner_id}", response_model=PartnerDetailOut)
def get_partner(
    partner_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PartnerDetailOut:
    row = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == partner_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Partner not found")
    return PartnerDetailOut.model_validate(row)


@router.put("/{partner_id}", response_model=PartnerDetailOut)
def update_partner(
    partner_id: UUID,
    body: PartnerUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PartnerDetailOut:
    row = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == partner_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Partner not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    log_activity(
        db,
        object_type="manufacturing_partner",
        object_id=row.id,
        action="partner_updated",
        actor_id=user.id,
        diff=data,
    )
    db.commit()
    return PartnerDetailOut.model_validate(row)


@router.post("/{partner_id}/score", response_model=PartnerDetailOut)
def score_partner(
    partner_id: UUID,
    body: PartnerScoreBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PartnerDetailOut:
    row = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == partner_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Partner not found")
    data = body.model_dump(exclude_unset=True)
    extra_patch = {}
    for key in ("product_fit_rating", "certification_readiness"):
        if key in data:
            v = data.pop(key)
            if v is not None:
                extra_patch[key] = v
    for k, v in data.items():
        setattr(row, k, v)
    if extra_patch:
        merged = dict(row.extra_scores or {})
        merged.update(extra_patch)
        row.extra_scores = merged
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    return PartnerDetailOut.model_validate(row)


@router.post("/{partner_id}/products", response_model=ProductDetailOut, status_code=status.HTTP_201_CREATED)
def partner_link_product(
    partner_id: UUID,
    body: PartnerProductLinkBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductDetailOut:
    ensure_product_partner_exist(db, body.product_id, partner_id)
    payload = body.model_dump(exclude={"product_id"})
    upsert_product_partner_link(
        db,
        product_id=body.product_id,
        body=ProductPartnerLinkBody(manufacturing_partner_id=partner_id, **payload),
        user_id=user.id,
    )
    prod = db.query(Product).filter(Product.id == body.product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductDetailOut.model_validate(prod)


@router.put("/{partner_id}/products/{product_id}", response_model=ProductDetailOut)
def partner_update_product_link(
    partner_id: UUID,
    product_id: UUID,
    body: ProductPartnerLinkUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductDetailOut:
    ensure_product_partner_exist(db, product_id, partner_id)
    link = update_product_partner_link(
        db, product_id=product_id, partner_id=partner_id, body=body, user_id=user.id
    )
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductDetailOut.model_validate(prod)


@router.delete("/{partner_id}/products/{product_id}", response_model=ProductDetailOut)
def partner_unlink_product(
    partner_id: UUID,
    product_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductDetailOut:
    ensure_product_partner_exist(db, product_id, partner_id)
    if not delete_product_partner_link(db, product_id=product_id, partner_id=partner_id, user_id=user.id):
        raise HTTPException(status_code=404, detail="Link not found")
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductDetailOut.model_validate(prod)


@router.post("/{partner_id}/ai-risk-summary", response_model=PartnerOut)
def partner_ai_risk_stub(
    partner_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PartnerOut:
    """Use POST /api/ai/supplier-risk-summary to generate and persist text."""
    row = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == partner_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Partner not found")
    return PartnerOut.model_validate(row)


@router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_partner(
    partner_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == partner_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Partner not found")
    row.is_active = False
    row.updated_by_id = user.id
    db.commit()
    log_activity(db, object_type="manufacturing_partner", object_id=row.id, action="soft_deleted", actor_id=user.id)
    db.commit()
