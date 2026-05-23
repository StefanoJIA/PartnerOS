"""Build order workspace aggregate."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    AIOutput,
    ActivityLog,
    Company,
    Contact,
    File,
    FileAttachment,
    Interaction,
    Lead,
    ManufacturingPartner,
    Order,
    OrderItem,
    ProductionMilestone,
    Quotation,
    RFQ,
    Sample,
    ShippingRecord,
    Task,
    User,
)
from app.schemas.lead_workspace import (
    AIOutputWorkspaceBrief,
    InteractionWorkspaceBrief,
    RFQWorkspaceBrief,
    SampleWorkspaceBrief,
    TaskWorkspaceBrief,
)
from app.schemas.orders_domain import (
    OrderDetailOut,
    OrderItemOut,
    OrderWorkspaceOut,
    ProductionMilestoneOut,
    QuotationBriefOut,
    ShippingRecordOut,
)
from app.schemas.rfq_domain import (
    ActivitySummaryOut,
    CompanySummaryMini,
    ContactSummaryMini,
    LeadSummaryMini,
    PartnerBrief,
    RfqFileBrief,
)
from app.services.order_risk import build_order_risk_panel


def _assignee_email(db: Session, uid: UUID | None) -> str | None:
    if not uid:
        return None
    u = db.query(User).filter(User.id == uid).first()
    return u.email if u else None


def _activity_order(db: Session, order_id: UUID) -> ActivitySummaryOut:
    rows = (
        db.query(ActivityLog.action, func.count())
        .filter(ActivityLog.object_type == "order", ActivityLog.object_id == order_id)
        .group_by(ActivityLog.action)
        .all()
    )
    return ActivitySummaryOut(by_action={str(a): int(c) for a, c in rows})


def build_order_workspace(db: Session, order_id: UUID) -> OrderWorkspaceOut | None:
    row = db.query(Order).filter(Order.id == order_id).first()
    if not row:
        return None

    company = db.query(Company).filter(Company.id == row.company_id).first() if row.company_id else None
    contact = db.query(Contact).filter(Contact.id == row.contact_id).first() if row.contact_id else None
    lead_row = db.query(Lead).filter(Lead.id == row.lead_id).first() if row.lead_id else None
    rfq_row = db.query(RFQ).filter(RFQ.id == row.rfq_id).first() if row.rfq_id else None
    q_row = db.query(Quotation).filter(Quotation.id == row.quotation_id).first() if row.quotation_id else None
    sample_row = db.query(Sample).filter(Sample.id == row.sample_id).first() if row.sample_id else None
    partner = (
        db.query(ManufacturingPartner).filter(ManufacturingPartner.id == row.manufacturing_partner_id).first()
        if row.manufacturing_partner_id
        else None
    )

    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).order_by(OrderItem.created_at).all()
    milestones = (
        db.query(ProductionMilestone).filter(ProductionMilestone.order_id == order_id).order_by(
            ProductionMilestone.created_at
        ).all()
    )
    shipping = (
        db.query(ShippingRecord).filter(ShippingRecord.order_id == order_id).order_by(ShippingRecord.created_at).all()
    )

    today = date.today()
    risk = build_order_risk_panel(row, milestones, shipping, today)

    recent_ix = (
        db.query(Interaction)
        .filter(Interaction.related_object_type == "order", Interaction.related_object_id == order_id)
        .order_by(Interaction.interaction_date.desc())
        .limit(25)
        .all()
    )
    open_tasks_q = (
        db.query(Task)
        .filter(
            Task.is_active.is_(True),
            Task.status != "done",
            Task.related_object_type == "order",
            Task.related_object_id == order_id,
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
        .filter(AIOutput.input_object_type == "order", AIOutput.input_object_id == order_id)
        .order_by(AIOutput.created_at.desc())
        .limit(20)
        .all()
    )

    fa_rows = (
        db.query(FileAttachment, File)
        .join(File, FileAttachment.file_id == File.id)
        .filter(FileAttachment.object_type == "order", FileAttachment.object_id == order_id)
        .order_by(FileAttachment.created_at.desc())
        .limit(100)
        .all()
    )
    files = [
        RfqFileBrief(id=att.id, file_id=att.file_id, original_filename=f.original_filename, purpose=att.purpose)
        for att, f in fa_rows
    ]

    rfq_brief = RFQWorkspaceBrief.model_validate(rfq_row) if rfq_row else None
    quot_brief = QuotationBriefOut.model_validate(q_row) if q_row else None
    sample_brief = SampleWorkspaceBrief.model_validate(sample_row) if sample_row else None

    return OrderWorkspaceOut(
        order=OrderDetailOut.model_validate(row),
        company=CompanySummaryMini.model_validate(company) if company else None,
        contact=ContactSummaryMini.model_validate(contact) if contact else None,
        lead=LeadSummaryMini.model_validate(lead_row) if lead_row else None,
        rfq=rfq_brief,
        quotation=quot_brief,
        sample=sample_brief,
        manufacturing_partner=PartnerBrief.model_validate(partner) if partner else None,
        order_items=[OrderItemOut.model_validate(x) for x in items],
        production_milestones=[ProductionMilestoneOut.model_validate(m) for m in milestones],
        shipping_records=[ShippingRecordOut.model_validate(s) for s in shipping],
        risk_panel=risk,
        recent_interactions=[InteractionWorkspaceBrief.model_validate(i) for i in recent_ix],
        open_tasks=open_tasks,
        recent_ai_outputs=[AIOutputWorkspaceBrief.model_validate(a) for a in recent_ai],
        files=files,
        activity_summary=_activity_order(db, order_id),
    )
