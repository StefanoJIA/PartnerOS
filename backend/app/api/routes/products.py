from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import AIOutput, Product, User
from app.schemas.ai import GenericAIRequest
from app.schemas.object_workspaces import ProductWorkspaceOut
from app.schemas.pagination import PaginatedResponse
from app.schemas.products import (
    ProductCreate,
    ProductDetailOut,
    ProductOut,
    ProductPartnerLinkBody,
    ProductPartnerLinkUpdate,
    ProductUpdate,
)
from app.services.activity import log_activity
from app.services.ai import client as ai_client
from app.services.ai import prompts as prompt_lib
from app.services.product_partner_links import (
    delete_product_partner_link,
    ensure_product_partner_exist,
    update_product_partner_link,
    upsert_product_partner_link,
)
from app.services.workspaces import build_product_workspace

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=PaginatedResponse[ProductOut])
def list_products(
    q: str | None = None,
    category: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[ProductOut]:
    query = db.query(Product).filter(Product.is_active.is_(True))
    if q:
        query = query.filter(or_(Product.product_name.ilike(f"%{q}%"), Product.description.ilike(f"%{q}%")))
    if category:
        query = query.filter(Product.product_category == category)
    total = query.count()
    rows = query.order_by(Product.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(items=[ProductOut.model_validate(r) for r in rows], total=total, page=page, limit=limit)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductOut:
    row = Product(**body.model_dump(), created_by_id=user.id, updated_by_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="product", object_id=row.id, action="product_created", actor_id=user.id)
    db.commit()
    return ProductOut.model_validate(row)


@router.get("/{product_id}/workspace", response_model=ProductWorkspaceOut)
def get_product_workspace(
    product_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ProductWorkspaceOut:
    ws = build_product_workspace(db, product_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Product not found")
    return ws


@router.get("/{product_id}", response_model=ProductDetailOut)
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ProductDetailOut:
    row = db.query(Product).filter(Product.id == product_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductDetailOut.model_validate(row)


@router.put("/{product_id}", response_model=ProductDetailOut)
def update_product(
    product_id: UUID,
    body: ProductUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductDetailOut:
    row = db.query(Product).filter(Product.id == product_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="product", object_id=row.id, action="product_updated", actor_id=user.id, diff=data)
    db.commit()
    return ProductDetailOut.model_validate(row)


@router.post("/{product_id}/partners", response_model=ProductDetailOut, status_code=status.HTTP_201_CREATED)
def link_product_partner(
    product_id: UUID,
    body: ProductPartnerLinkBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductDetailOut:
    ensure_product_partner_exist(db, product_id, body.manufacturing_partner_id)
    upsert_product_partner_link(db, product_id=product_id, body=body, user_id=user.id)
    row = db.query(Product).filter(Product.id == product_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductDetailOut.model_validate(row)


@router.put("/{product_id}/partners/{partner_id}", response_model=ProductDetailOut)
def update_product_partner_link_route(
    product_id: UUID,
    partner_id: UUID,
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
    row = db.query(Product).filter(Product.id == product_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductDetailOut.model_validate(row)


@router.delete("/{product_id}/partners/{partner_id}", response_model=ProductDetailOut)
def unlink_product_partner(
    product_id: UUID,
    partner_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductDetailOut:
    ensure_product_partner_exist(db, product_id, partner_id)
    if not delete_product_partner_link(db, product_id=product_id, partner_id=partner_id, user_id=user.id):
        raise HTTPException(status_code=404, detail="Link not found")
    row = db.query(Product).filter(Product.id == product_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductDetailOut.model_validate(row)


@router.post("/{product_id}/ai-sales-description", response_model=ProductOut)
def ai_sales_description(
    product_id: UUID,
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductOut:
    row = db.query(Product).filter(Product.id == product_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    ctx = {
        "product_name": row.product_name,
        "category": row.product_category or "",
        "description": row.description or "",
        **body.context,
    }
    msgs = prompt_lib.product_sales_description_prompt(ctx)
    text = ai_client.chat_completion(msgs)
    row.ai_sales_description = text
    row.updated_by_id = user.id
    db.commit()
    ao = AIOutput(
        task_type="product_sales_description",
        input_object_type="product",
        input_object_id=row.id,
        prompt=str(msgs)[:50000],
        output_text=text,
        status="draft",
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(ao)
    db.commit()
    db.refresh(row)
    return ProductOut.model_validate(row)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = db.query(Product).filter(Product.id == product_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    row.is_active = False
    row.updated_by_id = user.id
    db.commit()
    log_activity(db, object_type="product", object_id=row.id, action="soft_deleted", actor_id=user.id)
    db.commit()
