"""Build sample workspace aggregate."""

from __future__ import annotations

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
    Product,
    RFQ,
    Sample,
    Task,
    User,
)
from app.schemas.lead_workspace import (
    AIOutputWorkspaceBrief,
    InteractionWorkspaceBrief,
    OrderWorkspaceBrief,
    RFQWorkspaceBrief,
    TaskWorkspaceBrief,
)
from app.schemas.rfq_domain import (
    ActivitySummaryOut,
    CompanySummaryMini,
    ContactSummaryMini,
    LeadSummaryMini,
    PartnerBrief,
    ProductBrief,
    RfqFileBrief,
)
from app.schemas.samples_domain import SampleDetailOut, SampleWorkspaceOut


def _assignee_email(db: Session, uid: UUID | None) -> str | None:
    if not uid:
        return None
    u = db.query(User).filter(User.id == uid).first()
    return u.email if u else None


def _activity_summary_sample(db: Session, sample_id: UUID) -> ActivitySummaryOut:
    rows = (
        db.query(ActivityLog.action, func.count())
        .filter(ActivityLog.object_type == "sample", ActivityLog.object_id == sample_id)
        .group_by(ActivityLog.action)
        .all()
    )
    return ActivitySummaryOut(by_action={str(a): int(c) for a, c in rows})


def build_sample_workspace(db: Session, sample_id: UUID) -> SampleWorkspaceOut | None:
    row = db.query(Sample).filter(Sample.id == sample_id).first()
    if not row:
        return None

    company = db.query(Company).filter(Company.id == row.company_id).first() if row.company_id else None
    contact = db.query(Contact).filter(Contact.id == row.contact_id).first() if row.contact_id else None
    lead_row = db.query(Lead).filter(Lead.id == row.lead_id).first() if row.lead_id else None
    rfq_row = db.query(RFQ).filter(RFQ.id == row.rfq_id).first() if row.rfq_id else None
    product = db.query(Product).filter(Product.id == row.product_id).first() if row.product_id else None
    partner = (
        db.query(ManufacturingPartner).filter(ManufacturingPartner.id == row.manufacturing_partner_id).first()
        if row.manufacturing_partner_id
        else None
    )

    related_order = db.query(Order).filter(Order.sample_id == sample_id).order_by(Order.created_at.desc()).first()

    recent_ix = (
        db.query(Interaction)
        .filter(Interaction.related_object_type == "sample", Interaction.related_object_id == sample_id)
        .order_by(Interaction.interaction_date.desc())
        .limit(25)
        .all()
    )
    open_tasks_q = (
        db.query(Task)
        .filter(
            Task.is_active.is_(True),
            Task.status != "done",
            Task.related_object_type == "sample",
            Task.related_object_id == sample_id,
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
        .filter(AIOutput.input_object_type == "sample", AIOutput.input_object_id == sample_id)
        .order_by(AIOutput.created_at.desc())
        .limit(20)
        .all()
    )

    fa_rows = (
        db.query(FileAttachment, File)
        .join(File, FileAttachment.file_id == File.id)
        .filter(FileAttachment.object_type == "sample", FileAttachment.object_id == sample_id)
        .order_by(FileAttachment.created_at.desc())
        .limit(100)
        .all()
    )
    files = [
        RfqFileBrief(id=att.id, file_id=att.file_id, original_filename=f.original_filename, purpose=att.purpose)
        for att, f in fa_rows
    ]

    rfq_brief = RFQWorkspaceBrief.model_validate(rfq_row) if rfq_row else None

    return SampleWorkspaceOut(
        sample=SampleDetailOut.model_validate(row),
        company=CompanySummaryMini.model_validate(company) if company else None,
        contact=ContactSummaryMini.model_validate(contact) if contact else None,
        lead=LeadSummaryMini.model_validate(lead_row) if lead_row else None,
        rfq=rfq_brief,
        product=ProductBrief.model_validate(product) if product else None,
        manufacturing_partner=PartnerBrief.model_validate(partner) if partner else None,
        related_order=OrderWorkspaceBrief.model_validate(related_order) if related_order else None,
        recent_interactions=[InteractionWorkspaceBrief.model_validate(i) for i in recent_ix],
        open_tasks=open_tasks,
        recent_ai_outputs=[AIOutputWorkspaceBrief.model_validate(a) for a in recent_ai],
        files=files,
        activity_summary=_activity_summary_sample(db, sample_id),
    )
