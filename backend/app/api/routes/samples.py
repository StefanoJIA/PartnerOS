from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import (
    Company,
    Contact,
    Lead,
    ManufacturingPartner,
    Order,
    OrderItem,
    ProductionMilestone,
    Product,
    RFQ,
    Sample,
    User,
)
from app.models.enums import SampleStatus
from app.schemas.ai import GenericAIRequest
from app.schemas.orders_domain import DEFAULT_MILESTONE_NAMES, OrderOut, next_order_number
from app.schemas.pagination import PaginatedResponse
from app.schemas.samples_domain import (
    SampleConvertToOrderBody,
    SampleCreate,
    SampleDetailOut,
    SampleFeedbackBody,
    SampleListItemOut,
    SampleOut,
    SampleShippingBody,
    SampleStatusBody,
    SampleUpdate,
    SampleWorkspaceOut,
    next_sample_number,
)
from app.services.activity import log_activity
from app.services.ai import client as ai_client
from app.services.ai import prompts as prompt_lib
from app.services.sample_workspace import build_sample_workspace

router = APIRouter(prefix="/samples", tags=["samples"])


@router.get("", response_model=PaginatedResponse[SampleListItemOut])
def list_samples(
    sample_status: str | None = Query(None),
    company_id: UUID | None = None,
    product_id: UUID | None = None,
    manufacturing_partner_id: UUID | None = None,
    delivered_no_feedback: bool | None = None,
    follow_up_due: bool | None = None,
    converted_to_order: bool | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[SampleListItemOut]:
    today = date.today()
    q = (
        db.query(
            Sample,
            Company.company_name,
            Contact.first_name,
            Contact.last_name,
            Lead.lead_name,
            RFQ.rfq_number,
            Product.product_name,
            ManufacturingPartner.partner_name,
        )
        .outerjoin(Company, Sample.company_id == Company.id)
        .outerjoin(Contact, Sample.contact_id == Contact.id)
        .outerjoin(Lead, Sample.lead_id == Lead.id)
        .outerjoin(RFQ, Sample.rfq_id == RFQ.id)
        .outerjoin(Product, Sample.product_id == Product.id)
        .outerjoin(ManufacturingPartner, Sample.manufacturing_partner_id == ManufacturingPartner.id)
    )
    if sample_status:
        q = q.filter(Sample.sample_status == sample_status)
    if company_id:
        q = q.filter(Sample.company_id == company_id)
    if product_id:
        q = q.filter(Sample.product_id == product_id)
    if manufacturing_partner_id:
        q = q.filter(Sample.manufacturing_partner_id == manufacturing_partner_id)
    if delivered_no_feedback:
        q = q.filter(
            Sample.delivered_date.isnot(None),
            or_(Sample.customer_feedback.is_(None), Sample.customer_feedback == ""),
            Sample.sample_status != SampleStatus.feedback_received.value,
        )
    if follow_up_due:
        q = q.filter(Sample.follow_up_due_date.isnot(None), Sample.follow_up_due_date <= today)
    if converted_to_order is True:
        q = q.filter(Sample.converted_to_order.is_(True))
    if converted_to_order is False:
        q = q.filter(Sample.converted_to_order.is_(False))

    total = q.count()
    rows = q.order_by(Sample.updated_at.desc()).offset((page - 1) * limit).limit(limit).all()
    items: list[SampleListItemOut] = []
    for s, cn, fn, ln, lname, rnum, pname, ptn in rows:
        cl = None
        if fn or ln:
            cl = f"{fn or ''} {ln or ''}".strip() or None
        items.append(
            SampleListItemOut(
                id=s.id,
                sample_request_number=s.sample_request_number,
                sample_status=s.sample_status,
                company_id=s.company_id,
                company_name=cn,
                contact_id=s.contact_id,
                contact_label=cl,
                lead_id=s.lead_id,
                lead_name=lname,
                rfq_id=s.rfq_id,
                rfq_number=rnum,
                product_id=s.product_id,
                product_name=pname,
                manufacturing_partner_id=s.manufacturing_partner_id,
                partner_name=ptn,
                courier=s.courier,
                tracking_number=s.tracking_number,
                shipped_date=s.shipped_date,
                delivered_date=s.delivered_date,
                follow_up_due_date=s.follow_up_due_date,
                converted_to_order=s.converted_to_order,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
        )
    return PaginatedResponse(items=items, total=total, page=page, limit=limit)


@router.post("", response_model=SampleOut, status_code=status.HTTP_201_CREATED)
def create_sample(
    body: SampleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SampleOut:
    row = Sample(
        sample_request_number=next_sample_number(),
        **body.model_dump(),
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="sample", object_id=row.id, action="sample_created", actor_id=user.id)
    if row.lead_id:
        log_activity(
            db,
            object_type="lead",
            object_id=row.lead_id,
            action="sample_created_from_lead",
            actor_id=user.id,
            diff={"sample_id": str(row.id), "sample_request_number": row.sample_request_number},
        )
    db.commit()
    return SampleOut.model_validate(row)


@router.get("/{sample_id}/workspace", response_model=SampleWorkspaceOut)
def get_sample_workspace_route(
    sample_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SampleWorkspaceOut:
    ws = build_sample_workspace(db, sample_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Sample not found")
    return ws


@router.post("/{sample_id}/status", response_model=SampleDetailOut)
def set_sample_status(
    sample_id: UUID,
    body: SampleStatusBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SampleDetailOut:
    row = db.query(Sample).filter(Sample.id == sample_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Sample not found")
    prev = row.sample_status
    row.sample_status = body.status
    row.updated_by_id = user.id
    if body.notes:
        row.notes = (row.notes or "") + ("\n" if row.notes else "") + body.notes
    db.commit()
    db.refresh(row)
    log_activity(
        db,
        object_type="sample",
        object_id=row.id,
        action="sample_status_changed",
        actor_id=user.id,
        diff={"from": prev, "to": body.status},
    )
    db.commit()
    return SampleDetailOut.model_validate(row)


@router.put("/{sample_id}/shipping", response_model=SampleDetailOut)
def update_sample_shipping(
    sample_id: UUID,
    body: SampleShippingBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SampleDetailOut:
    row = db.query(Sample).filter(Sample.id == sample_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Sample not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="sample", object_id=row.id, action="sample_shipping_updated", actor_id=user.id, diff=data)
    db.commit()
    return SampleDetailOut.model_validate(row)


@router.post("/{sample_id}/feedback", response_model=SampleDetailOut)
def record_sample_feedback(
    sample_id: UUID,
    body: SampleFeedbackBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SampleDetailOut:
    row = db.query(Sample).filter(Sample.id == sample_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Sample not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    log_activity(
        db,
        object_type="sample",
        object_id=row.id,
        action="sample_feedback_recorded",
        actor_id=user.id,
        diff={k: str(v) for k, v in data.items()},
    )
    db.commit()
    return SampleDetailOut.model_validate(row)


@router.post("/{sample_id}/convert-to-order", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def convert_sample_to_order(
    sample_id: UUID,
    body: SampleConvertToOrderBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderOut:
    s = db.query(Sample).filter(Sample.id == sample_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Sample not found")
    partner_id = body.manufacturing_partner_id or s.manufacturing_partner_id
    if not partner_id:
        raise HTTPException(status_code=400, detail="manufacturing_partner_id required (set on sample or in body)")
    if s.converted_to_order:
        raise HTTPException(status_code=400, detail="Sample already converted to order")
    order = Order(
        order_number=next_order_number(),
        company_id=s.company_id,
        contact_id=s.contact_id,
        lead_id=s.lead_id,
        rfq_id=s.rfq_id,
        sample_id=s.id,
        manufacturing_partner_id=partner_id,
        total_amount=s.sample_cost,
        currency="USD",
        production_status="Draft",
        notes=body.notes,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    if s.product_id:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=s.product_id,
                quantity=1,
                unit_price=s.sample_cost,
                created_by_id=user.id,
                updated_by_id=user.id,
            )
        )
    s.converted_to_order = True
    s.sample_status = SampleStatus.converted.value
    s.updated_by_id = user.id
    db.commit()
    db.refresh(order)
    log_activity(
        db,
        object_type="sample",
        object_id=s.id,
        action="sample_converted_to_order",
        actor_id=user.id,
        diff={"order_id": str(order.id)},
    )
    log_activity(
        db,
        object_type="order",
        object_id=order.id,
        action="order_created_from_sample",
        actor_id=user.id,
        diff={"sample_id": str(sample_id)},
    )
    db.commit()
    if body.generate_milestones:
        for name in DEFAULT_MILESTONE_NAMES:
            m = ProductionMilestone(
                order_id=order.id,
                milestone_name=name,
                status="pending",
                created_by_id=user.id,
                updated_by_id=user.id,
            )
            db.add(m)
        db.commit()
    return OrderOut.model_validate(order)


@router.get("/{sample_id}", response_model=SampleDetailOut)
def get_sample(
    sample_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SampleDetailOut:
    row = db.query(Sample).filter(Sample.id == sample_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Sample not found")
    return SampleDetailOut.model_validate(row)


@router.put("/{sample_id}", response_model=SampleDetailOut)
def update_sample(
    sample_id: UUID,
    body: SampleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SampleDetailOut:
    row = db.query(Sample).filter(Sample.id == sample_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Sample not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    return SampleDetailOut.model_validate(row)


@router.post("/{sample_id}/follow-up-email")
def sample_followup_email(
    sample_id: UUID,
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    row = db.query(Sample).filter(Sample.id == sample_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Sample not found")
    ctx = {
        "sample_status": row.sample_status,
        "customer_feedback": row.customer_feedback or "",
        **body.context,
    }
    msgs = prompt_lib.follow_up_prompt(ctx)
    text = ai_client.chat_completion(msgs)
    from app.models import AIOutput

    ao = AIOutput(
        task_type="email_generation",
        input_object_type="sample",
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
