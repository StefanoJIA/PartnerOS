from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import (
    AIOutput,
    Company,
    Contact,
    FieldVisitPlan,
    FieldVisitTarget,
    Interaction,
    Lead,
    Order,
    RFQ,
    Sample,
    Task,
    User,
)
from app.schemas.crm import LeadCreate, LeadOut, LeadStageBody, LeadUpdate
from app.schemas.lead_workspace import (
    AIOutputWorkspaceBrief,
    CompanyWorkspaceCard,
    ContactWorkspaceCard,
    FieldVisitWorkspaceBrief,
    InteractionWorkspaceBrief,
    LeadWorkspaceOut,
    OrderWorkspaceBrief,
    RFQWorkspaceBrief,
    SampleWorkspaceBrief,
    TaskWorkspaceBrief,
)
from app.schemas.pagination import PaginatedResponse
from app.services.activity import log_activity

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=PaginatedResponse[LeadOut])
def list_leads(
    stage: str | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[LeadOut]:
    query = db.query(Lead).filter(Lead.is_active.is_(True))
    if stage:
        query = query.filter(Lead.current_stage == stage)
    if q:
        like = f"%{q}%"
        query = query.filter(Lead.lead_name.ilike(like))
    total = query.count()
    rows = query.order_by(Lead.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(items=[LeadOut.model_validate(r) for r in rows], total=total, page=page, limit=limit)


@router.post("", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
def create_lead(
    body: LeadCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LeadOut:
    row = Lead(**body.model_dump(), created_by_id=user.id, updated_by_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="lead", object_id=row.id, action="lead_created", actor_id=user.id)
    log_activity(
        db,
        object_type="company",
        object_id=body.company_id,
        action="lead_created_from_company",
        actor_id=user.id,
        diff={"lead_id": str(row.id)},
    )
    if body.primary_contact_id:
        log_activity(
            db,
            object_type="contact",
            object_id=body.primary_contact_id,
            action="lead_created_from_contact",
            actor_id=user.id,
            diff={"lead_id": str(row.id)},
        )
    db.commit()
    return LeadOut.model_validate(row)


def _assignee_email(db: Session, uid: UUID | None) -> str | None:
    if not uid:
        return None
    u = db.query(User).filter(User.id == uid).first()
    return u.email if u else None


@router.get("/{lead_id}/workspace", response_model=LeadWorkspaceOut)
def get_lead_workspace(
    lead_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> LeadWorkspaceOut:
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.is_active.is_(True)).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    company = db.query(Company).filter(Company.id == lead.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found for lead")
    contact = (
        db.query(Contact).filter(Contact.id == lead.primary_contact_id).first()
        if lead.primary_contact_id
        else None
    )
    owner_display = None
    if lead.owner_user_id:
        ou = db.query(User).filter(User.id == lead.owner_user_id).first()
        if ou:
            owner_display = f"{ou.full_name} <{ou.email}>"

    related_rfqs = (
        db.query(RFQ).filter(RFQ.lead_id == lead_id).order_by(RFQ.created_at.desc()).limit(50).all()
    )
    rfq_ids = [r.id for r in related_rfqs]
    related_orders: list[Order] = []
    if rfq_ids:
        related_orders = (
            db.query(Order)
            .filter(Order.rfq_id.in_(rfq_ids))
            .order_by(Order.created_at.desc())
            .limit(50)
            .all()
        )

    related_samples = (
        db.query(Sample)
        .filter(Sample.lead_id == lead_id)
        .order_by(Sample.created_at.desc())
        .limit(50)
        .all()
    )

    fv_rows = (
        db.query(FieldVisitTarget, FieldVisitPlan)
        .join(FieldVisitPlan, FieldVisitTarget.visit_plan_id == FieldVisitPlan.id)
        .filter(FieldVisitTarget.company_id == lead.company_id)
        .order_by(FieldVisitTarget.scheduled_time.desc().nullslast())
        .limit(30)
        .all()
    )
    related_field = [
        FieldVisitWorkspaceBrief(
            target_id=tgt.id,
            plan_id=plan.id,
            plan_name=plan.plan_name,
            company_id=tgt.company_id,
            scheduled_time=tgt.scheduled_time,
            visit_result=tgt.visit_result,
            status=plan.status,
        )
        for tgt, plan in fv_rows
    ]

    recent_ix = (
        db.query(Interaction)
        .filter(Interaction.related_object_type == "lead", Interaction.related_object_id == lead_id)
        .order_by(Interaction.interaction_date.desc())
        .limit(25)
        .all()
    )
    open_tasks_q = (
        db.query(Task)
        .filter(
            Task.is_active.is_(True),
            Task.status != "done",
            Task.related_object_type == "lead",
            Task.related_object_id == lead_id,
        )
        .order_by(Task.due_at.asc().nullslast())
        .limit(30)
        .all()
    )
    open_tasks = [
        TaskWorkspaceBrief(
            id=t.id,
            title=t.title,
            status=t.status,
            priority=t.priority,
            due_at=t.due_at,
            completed_at=t.completed_at,
            assignee_user_id=t.assignee_user_id,
            assignee_email=_assignee_email(db, t.assignee_user_id),
        )
        for t in open_tasks_q
    ]
    recent_ai = (
        db.query(AIOutput)
        .filter(AIOutput.input_object_type == "lead", AIOutput.input_object_id == lead_id)
        .order_by(AIOutput.created_at.desc())
        .limit(20)
        .all()
    )

    return LeadWorkspaceOut(
        lead=LeadOut.model_validate(lead),
        company=CompanyWorkspaceCard.model_validate(company),
        contact=ContactWorkspaceCard.model_validate(contact) if contact else None,
        owner_display=owner_display,
        related_rfqs=[RFQWorkspaceBrief.model_validate(r) for r in related_rfqs],
        related_samples=[SampleWorkspaceBrief.model_validate(s) for s in related_samples],
        related_orders=[OrderWorkspaceBrief.model_validate(o) for o in related_orders],
        related_field_visits=related_field,
        recent_interactions=[InteractionWorkspaceBrief.model_validate(i) for i in recent_ix],
        open_tasks=open_tasks,
        recent_ai_outputs=[AIOutputWorkspaceBrief.model_validate(a) for a in recent_ai],
    )


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(
    lead_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> LeadOut:
    row = db.query(Lead).filter(Lead.id == lead_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadOut.model_validate(row)


@router.put("/{lead_id}", response_model=LeadOut)
def update_lead(
    lead_id: UUID,
    body: LeadUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LeadOut:
    row = db.query(Lead).filter(Lead.id == lead_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="lead", object_id=row.id, action="lead_updated", actor_id=user.id, diff=data)
    db.commit()
    return LeadOut.model_validate(row)


@router.post("/{lead_id}/stage", response_model=LeadOut)
def set_lead_stage(
    lead_id: UUID,
    body: LeadStageBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LeadOut:
    row = db.query(Lead).filter(Lead.id == lead_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    row.current_stage = body.current_stage
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    log_activity(
        db,
        object_type="lead",
        object_id=row.id,
        action="lead_stage_changed",
        actor_id=user.id,
        diff={"current_stage": body.current_stage},
    )
    db.commit()
    return LeadOut.model_validate(row)


@router.post("/{lead_id}/ai-summary", response_model=LeadOut)
def lead_ai_summary_placeholder(
    lead_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LeadOut:
    """Placeholder: AI summary stored via /api/ai/* then PATCH lead."""
    row = db.query(Lead).filter(Lead.id == lead_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadOut.model_validate(row)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
    lead_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = db.query(Lead).filter(Lead.id == lead_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    row.is_active = False
    row.updated_by_id = user.id
    db.commit()
    log_activity(db, object_type="lead", object_id=row.id, action="soft_deleted", actor_id=user.id)
    db.commit()
