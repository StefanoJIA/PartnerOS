from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import ManufacturingPartner, Product, ProductPartnerLink
from app.schemas.products import ProductPartnerLinkBody, ProductPartnerLinkUpdate
from app.services.activity import log_activity


def upsert_product_partner_link(
    db: Session,
    *,
    product_id: UUID,
    body: ProductPartnerLinkBody,
    user_id: UUID,
) -> ProductPartnerLink:
    link = (
        db.query(ProductPartnerLink)
        .filter(
            ProductPartnerLink.product_id == product_id,
            ProductPartnerLink.manufacturing_partner_id == body.manufacturing_partner_id,
        )
        .first()
    )
    payload = body.model_dump(exclude={"manufacturing_partner_id"})
    if link:
        is_new = False
        for k, v in payload.items():
            setattr(link, k, v)
        link.updated_by_id = user_id
    else:
        is_new = True
        link = ProductPartnerLink(
            product_id=product_id,
            manufacturing_partner_id=body.manufacturing_partner_id,
            **payload,
            created_by_id=user_id,
            updated_by_id=user_id,
        )
        db.add(link)
    db.commit()
    db.refresh(link)
    pid = body.manufacturing_partner_id
    if is_new:
        log_activity(
            db,
            object_type="product",
            object_id=product_id,
            action="partner_linked",
            actor_id=user_id,
            diff={"partner_id": str(pid)},
        )
        log_activity(
            db,
            object_type="manufacturing_partner",
            object_id=pid,
            action="product_linked",
            actor_id=user_id,
            diff={"product_id": str(product_id)},
        )
    else:
        log_activity(
            db,
            object_type="product",
            object_id=product_id,
            action="partner_link_updated",
            actor_id=user_id,
            diff={"partner_id": str(pid)},
        )
        log_activity(
            db,
            object_type="manufacturing_partner",
            object_id=pid,
            action="product_link_updated",
            actor_id=user_id,
            diff={"product_id": str(product_id)},
        )
    db.commit()
    return link


def update_product_partner_link(
    db: Session,
    *,
    product_id: UUID,
    partner_id: UUID,
    body: ProductPartnerLinkUpdate,
    user_id: UUID,
) -> ProductPartnerLink | None:
    link = (
        db.query(ProductPartnerLink)
        .filter(
            ProductPartnerLink.product_id == product_id,
            ProductPartnerLink.manufacturing_partner_id == partner_id,
        )
        .first()
    )
    if not link:
        return None
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(link, k, v)
    link.updated_by_id = user_id
    db.commit()
    db.refresh(link)
    log_activity(
        db,
        object_type="product",
        object_id=product_id,
        action="partner_link_updated",
        actor_id=user_id,
        diff={"partner_id": str(partner_id)},
    )
    log_activity(
        db,
        object_type="manufacturing_partner",
        object_id=partner_id,
        action="product_link_updated",
        actor_id=user_id,
        diff={"product_id": str(product_id)},
    )
    db.commit()
    return link


def delete_product_partner_link(db: Session, *, product_id: UUID, partner_id: UUID, user_id: UUID) -> bool:
    link = (
        db.query(ProductPartnerLink)
        .filter(
            ProductPartnerLink.product_id == product_id,
            ProductPartnerLink.manufacturing_partner_id == partner_id,
        )
        .first()
    )
    if not link:
        return False
    db.delete(link)
    db.commit()
    log_activity(
        db,
        object_type="product",
        object_id=product_id,
        action="partner_unlinked",
        actor_id=user_id,
        diff={"partner_id": str(partner_id)},
    )
    log_activity(
        db,
        object_type="manufacturing_partner",
        object_id=partner_id,
        action="product_unlinked",
        actor_id=user_id,
        diff={"product_id": str(product_id)},
    )
    db.commit()
    return True


def ensure_product_partner_exist(db: Session, product_id: UUID, partner_id: UUID) -> None:
    p = db.query(Product).filter(Product.id == product_id).first()
    m = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == partner_id).first()
    if not p or not m:
        raise HTTPException(status_code=404, detail="Product or partner not found")
