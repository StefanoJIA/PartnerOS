from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import (
    Company,
    Contact,
    Lead,
    ManufacturingPartner,
    Order,
    ProductionMilestone,
    RFQ,
    ShippingRecord,
    User,
)
from app.schemas.ai import GenericAIRequest
from app.schemas.orders_domain import (
    DEFAULT_MILESTONE_NAMES,
    MilestoneUpdate,
    OrderCreate,
    OrderDetailOut,
    OrderListItemOut,
    OrderOut,
    OrderProductionStatusBody,
    OrderShippingStatusBody,
    OrderUpdate,
    OrderWorkspaceOut,
    ProductionMilestoneOut,
    ShippingRecordCreate,
    ShippingRecordOut,
    ShippingRecordUpdate,
    next_order_number,
)
from app.schemas.pagination import PaginatedResponse
from app.services.activity import log_activity
from app.services.ai import client as ai_client
from app.services.ai import prompts as prompt_lib
from app.services.order_workspace import build_order_workspace

router = APIRouter(prefix="/orders", tags=["orders"])


def _milestone_done_status(st: str | None) -> bool:
    return (st or "").lower() in ("completed", "done", "complete")


def _sync_milestone_delay(m: ProductionMilestone, today: date) -> None:
    if m.planned_date and m.actual_date:
        m.delay_days = (m.actual_date - m.planned_date).days
    elif m.planned_date and not m.actual_date and not _milestone_done_status(m.status):
        if m.planned_date < today:
            m.delay_days = (today - m.planned_date).days


@router.get("", response_model=PaginatedResponse[OrderListItemOut])
def list_orders(
    production_status: str | None = Query(None),
    shipping_status: str | None = Query(None),
    risk_level: str | None = Query(None),
    delayed_only: bool | None = None,
    company_id: UUID | None = None,
    manufacturing_partner_id: UUID | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[OrderListItemOut]:
    today = date.today()
    delay_subq = (
        db.query(ProductionMilestone.order_id, func.count(ProductionMilestone.id).label("dc"))
        .filter(
            ProductionMilestone.planned_date.isnot(None),
            ProductionMilestone.planned_date < today,
            ProductionMilestone.actual_date.is_(None),
        )
        .group_by(ProductionMilestone.order_id)
        .subquery()
    )

    q = (
        db.query(
            Order,
            Company.company_name,
            Contact.first_name,
            Contact.last_name,
            Lead.lead_name,
            RFQ.rfq_number,
            ManufacturingPartner.partner_name,
            func.coalesce(delay_subq.c.dc, 0).label("delayed_cnt"),
        )
        .outerjoin(Company, Order.company_id == Company.id)
        .outerjoin(Contact, Order.contact_id == Contact.id)
        .outerjoin(Lead, Order.lead_id == Lead.id)
        .outerjoin(RFQ, Order.rfq_id == RFQ.id)
        .outerjoin(ManufacturingPartner, Order.manufacturing_partner_id == ManufacturingPartner.id)
        .outerjoin(delay_subq, delay_subq.c.order_id == Order.id)
    )
    if production_status:
        q = q.filter(Order.production_status == production_status)
    if shipping_status:
        q = q.filter(Order.shipping_status == shipping_status)
    if risk_level:
        q = q.filter(Order.risk_level == risk_level)
    if company_id:
        q = q.filter(Order.company_id == company_id)
    if manufacturing_partner_id:
        q = q.filter(Order.manufacturing_partner_id == manufacturing_partner_id)
    if delayed_only:
        q = q.filter(func.coalesce(delay_subq.c.dc, 0) > 0)

    total = q.count()
    rows = q.order_by(Order.updated_at.desc()).offset((page - 1) * limit).limit(limit).all()
    items: list[OrderListItemOut] = []
    for o, cn, fn, ln, lname, rnum, ptn, dcnt in rows:
        cl = None
        if fn or ln:
            cl = f"{fn or ''} {ln or ''}".strip() or None
        items.append(
            OrderListItemOut(
                id=o.id,
                order_number=o.order_number,
                company_id=o.company_id,
                company_name=cn,
                contact_id=o.contact_id,
                contact_label=cl,
                lead_id=o.lead_id,
                lead_name=lname,
                rfq_id=o.rfq_id,
                rfq_number=rnum,
                manufacturing_partner_id=o.manufacturing_partner_id,
                partner_name=ptn,
                order_date=o.order_date,
                target_delivery_date=o.target_delivery_date,
                production_status=o.production_status,
                shipping_status=o.shipping_status,
                risk_level=o.risk_level,
                delayed_milestones_count=int(dcnt or 0),
                total_amount=o.total_amount,
                created_at=o.created_at,
                updated_at=o.updated_at,
            )
        )
    return PaginatedResponse(items=items, total=total, page=page, limit=limit)


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    body: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderOut:
    row = Order(
        order_number=next_order_number(),
        **body.model_dump(),
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="order", object_id=row.id, action="order_created", actor_id=user.id)
    db.commit()
    return OrderOut.model_validate(row)


@router.get("/{order_id}/workspace", response_model=OrderWorkspaceOut)
def get_order_workspace_route(
    order_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> OrderWorkspaceOut:
    ws = build_order_workspace(db, order_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Order not found")
    return ws


@router.get("/{order_id}/shipping-records", response_model=list[ShippingRecordOut])
def list_shipping_records(
    order_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ShippingRecordOut]:
    if not db.query(Order).filter(Order.id == order_id).first():
        raise HTTPException(status_code=404, detail="Order not found")
    rows = db.query(ShippingRecord).filter(ShippingRecord.order_id == order_id).order_by(ShippingRecord.created_at).all()
    return [ShippingRecordOut.model_validate(r) for r in rows]


@router.post("/{order_id}/shipping-records", response_model=ShippingRecordOut, status_code=status.HTTP_201_CREATED)
def create_shipping_record(
    order_id: UUID,
    body: ShippingRecordCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ShippingRecordOut:
    if not db.query(Order).filter(Order.id == order_id).first():
        raise HTTPException(status_code=404, detail="Order not found")
    rec = ShippingRecord(order_id=order_id, **body.model_dump(), created_by_id=user.id, updated_by_id=user.id)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    log_activity(db, object_type="order", object_id=order_id, action="shipping_record_added", actor_id=user.id, diff={"id": str(rec.id)})
    db.commit()
    return ShippingRecordOut.model_validate(rec)


@router.put("/{order_id}/shipping-records/{record_id}", response_model=ShippingRecordOut)
def update_shipping_record(
    order_id: UUID,
    record_id: UUID,
    body: ShippingRecordUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ShippingRecordOut:
    rec = db.query(ShippingRecord).filter(ShippingRecord.id == record_id, ShippingRecord.order_id == order_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Shipping record not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(rec, k, v)
    rec.updated_by_id = user.id
    db.commit()
    db.refresh(rec)
    log_activity(db, object_type="order", object_id=order_id, action="shipping_record_updated", actor_id=user.id, diff={"id": str(record_id)})
    db.commit()
    return ShippingRecordOut.model_validate(rec)


@router.delete("/{order_id}/shipping-records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shipping_record(
    order_id: UUID,
    record_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    rec = db.query(ShippingRecord).filter(ShippingRecord.id == record_id, ShippingRecord.order_id == order_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Shipping record not found")
    db.delete(rec)
    db.commit()
    log_activity(db, object_type="order", object_id=order_id, action="shipping_record_deleted", actor_id=user.id, diff={"id": str(record_id)})
    db.commit()


@router.post("/{order_id}/shipping-records/{record_id}/customs-cleared", response_model=ShippingRecordOut)
def mark_customs_cleared(
    order_id: UUID,
    record_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ShippingRecordOut:
    rec = db.query(ShippingRecord).filter(ShippingRecord.id == record_id, ShippingRecord.order_id == order_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Shipping record not found")
    rec.customs_status = "Cleared"
    rec.updated_by_id = user.id
    db.commit()
    db.refresh(rec)
    log_activity(db, object_type="order", object_id=order_id, action="shipping_customs_cleared", actor_id=user.id, diff={"id": str(record_id)})
    db.commit()
    return ShippingRecordOut.model_validate(rec)


@router.post("/{order_id}/shipping-records/{record_id}/warehouse-inbound", response_model=ShippingRecordOut)
def mark_warehouse_inbound(
    order_id: UUID,
    record_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ShippingRecordOut:
    rec = db.query(ShippingRecord).filter(ShippingRecord.id == record_id, ShippingRecord.order_id == order_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Shipping record not found")
    rec.delivery_status = "Warehouse Inbound"
    rec.updated_by_id = user.id
    db.commit()
    db.refresh(rec)
    log_activity(
        db, object_type="order", object_id=order_id, action="shipping_warehouse_inbound", actor_id=user.id, diff={"id": str(record_id)}
    )
    db.commit()
    return ShippingRecordOut.model_validate(rec)


@router.post("/{order_id}/shipping-records/{record_id}/final-delivered", response_model=ShippingRecordOut)
def mark_final_delivered(
    order_id: UUID,
    record_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ShippingRecordOut:
    rec = db.query(ShippingRecord).filter(ShippingRecord.id == record_id, ShippingRecord.order_id == order_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Shipping record not found")
    rec.delivery_status = "Delivered"
    rec.updated_by_id = user.id
    db.commit()
    db.refresh(rec)
    log_activity(
        db, object_type="order", object_id=order_id, action="shipping_final_delivered", actor_id=user.id, diff={"id": str(record_id)}
    )
    db.commit()
    return ShippingRecordOut.model_validate(rec)


@router.get("/{order_id}", response_model=OrderDetailOut)
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> OrderDetailOut:
    row = db.query(Order).filter(Order.id == order_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderDetailOut.model_validate(row)


@router.put("/{order_id}", response_model=OrderDetailOut)
def update_order(
    order_id: UUID,
    body: OrderUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderDetailOut:
    row = db.query(Order).filter(Order.id == order_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    return OrderDetailOut.model_validate(row)


@router.post("/{order_id}/production-status", response_model=OrderDetailOut)
def set_production_status(
    order_id: UUID,
    body: OrderProductionStatusBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderDetailOut:
    row = db.query(Order).filter(Order.id == order_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    prev = row.production_status
    row.production_status = body.production_status
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    log_activity(
        db,
        object_type="order",
        object_id=order_id,
        action="order_production_status_changed",
        actor_id=user.id,
        diff={"from": prev, "to": body.production_status, "notes": body.notes},
    )
    db.commit()
    return OrderDetailOut.model_validate(row)


@router.post("/{order_id}/shipping-status", response_model=OrderDetailOut)
def set_shipping_status(
    order_id: UUID,
    body: OrderShippingStatusBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderDetailOut:
    row = db.query(Order).filter(Order.id == order_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    prev = row.shipping_status
    row.shipping_status = body.shipping_status
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    log_activity(
        db,
        object_type="order",
        object_id=order_id,
        action="order_shipping_status_changed",
        actor_id=user.id,
        diff={"from": prev, "to": body.shipping_status, "notes": body.notes},
    )
    db.commit()
    return OrderDetailOut.model_validate(row)


@router.post("/{order_id}/generate-milestones")
def generate_milestones(
    order_id: UUID,
    force: bool = Query(False),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    row = db.query(Order).filter(Order.id == order_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    existing = db.query(ProductionMilestone).filter(ProductionMilestone.order_id == order_id).count()
    if existing and not force:
        return {"message": "Milestones already exist", "order_id": str(order_id)}
    if force and existing:
        for m in db.query(ProductionMilestone).filter(ProductionMilestone.order_id == order_id).all():
            db.delete(m)
        db.commit()
    n = 0
    for name in DEFAULT_MILESTONE_NAMES:
        m = ProductionMilestone(
            order_id=order_id,
            milestone_name=name,
            status="pending",
            created_by_id=user.id,
            updated_by_id=user.id,
        )
        db.add(m)
        n += 1
    db.commit()
    log_activity(
        db,
        object_type="order",
        object_id=order_id,
        action="order_milestones_generated",
        actor_id=user.id,
        diff={"count": n},
    )
    db.commit()
    return {"created": n}


@router.put("/{order_id}/milestones/{milestone_id}", response_model=ProductionMilestoneOut)
def update_milestone(
    order_id: UUID,
    milestone_id: UUID,
    body: MilestoneUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductionMilestoneOut:
    m = (
        db.query(ProductionMilestone)
        .filter(ProductionMilestone.id == milestone_id, ProductionMilestone.order_id == order_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Milestone not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    _sync_milestone_delay(m, date.today())
    m.updated_by_id = user.id
    db.commit()
    db.refresh(m)
    log_activity(
        db,
        object_type="order",
        object_id=order_id,
        action="order_milestone_updated",
        actor_id=user.id,
        diff={"milestone_id": str(milestone_id)},
    )
    db.commit()
    return ProductionMilestoneOut.model_validate(m)


@router.post("/{order_id}/milestones/{milestone_id}/complete", response_model=ProductionMilestoneOut)
def complete_milestone(
    order_id: UUID,
    milestone_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductionMilestoneOut:
    m = (
        db.query(ProductionMilestone)
        .filter(ProductionMilestone.id == milestone_id, ProductionMilestone.order_id == order_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Milestone not found")
    m.status = "completed"
    m.actual_date = date.today()
    _sync_milestone_delay(m, date.today())
    m.updated_by_id = user.id
    db.commit()
    db.refresh(m)
    log_activity(
        db,
        object_type="order",
        object_id=order_id,
        action="order_milestone_completed",
        actor_id=user.id,
        diff={"milestone_id": str(milestone_id)},
    )
    if m.planned_date and m.actual_date and m.actual_date > m.planned_date:
        log_activity(
            db,
            object_type="order",
            object_id=order_id,
            action="order_milestone_delayed",
            actor_id=user.id,
            diff={"milestone_id": str(milestone_id), "delay_days": (m.actual_date - m.planned_date).days},
        )
    db.commit()
    return ProductionMilestoneOut.model_validate(m)


@router.post("/{order_id}/milestones/{milestone_id}/delayed", response_model=ProductionMilestoneOut)
def mark_milestone_delayed(
    order_id: UUID,
    milestone_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductionMilestoneOut:
    m = (
        db.query(ProductionMilestone)
        .filter(ProductionMilestone.id == milestone_id, ProductionMilestone.order_id == order_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Milestone not found")
    today = date.today()
    m.status = "delayed"
    if m.planned_date:
        m.delay_days = (today - m.planned_date).days
    m.updated_by_id = user.id
    db.commit()
    db.refresh(m)
    log_activity(
        db,
        object_type="order",
        object_id=order_id,
        action="order_milestone_delayed",
        actor_id=user.id,
        diff={"milestone_id": str(milestone_id), "delay_days": m.delay_days},
    )
    db.commit()
    return ProductionMilestoneOut.model_validate(m)


@router.post("/{order_id}/customer-update-email")
def customer_update_email(
    order_id: UUID,
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    row = db.query(Order).filter(Order.id == order_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    milestones = db.query(ProductionMilestone).filter(ProductionMilestone.order_id == order_id).all()
    done = [x.milestone_name for x in milestones if x.actual_date]
    pending = [x.milestone_name for x in milestones if not x.actual_date]
    ctx = {
        "order_number": row.order_number,
        "production_status": row.production_status or "",
        "shipping_status": row.shipping_status or "",
        "completed_milestones": ", ".join(done),
        "pending_milestones": ", ".join(pending),
        **body.context,
    }
    msgs = prompt_lib.order_update_email_prompt(ctx)
    text = ai_client.chat_completion(msgs)
    from app.models import AIOutput

    ao = AIOutput(
        task_type="order_update_email",
        input_object_type="order",
        input_object_id=row.id,
        prompt=str(msgs)[:50000],
        output_text=text,
        status="draft",
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(ao)
    db.commit()
    db.refresh(ao)
    return {"ai_output_id": str(ao.id), "text": text}
