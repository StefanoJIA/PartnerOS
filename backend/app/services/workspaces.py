from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import (
    AIOutput,
    ActivityLog,
    Company,
    Contact,
    FieldVisitPlan,
    FieldVisitTarget,
    File,
    Interaction,
    Lead,
    ManufacturingPartner,
    Order,
    OrderItem,
    Product,
    ProductDocument,
    ProductPartnerLink,
    QualityDocument,
    Quotation,
    RFQ,
    RFQItem,
    RFQPartnerCandidate,
    Sample,
    Task,
    User,
)
from app.schemas.crm import CompanyDetailOut, ContactDetailOut, LeadOut
from app.schemas.lead_workspace import (
    AIOutputWorkspaceBrief,
    FieldVisitWorkspaceBrief,
    InteractionWorkspaceBrief,
    OrderWorkspaceBrief,
    RFQWorkspaceBrief,
    SampleWorkspaceBrief,
    TaskWorkspaceBrief,
)
from app.schemas.object_workspaces import (
    ActivitySummaryOut,
    CompanySummaryCard,
    CompanyWorkspaceOut,
    ContactWorkspaceOut,
    LinkedPartnerRow,
    PartnerComparisonHints,
    PartnerWorkspaceOut,
    ProductInterestSummaryOut,
    ProductWorkspaceFileBrief,
    ProductWorkspaceOut,
    QualityDocumentBrief,
    QuotationWorkspaceBrief,
)
from app.schemas.partners import PartnerDetailOut
from app.schemas.products import ProductDetailOut, ProductPartnerLinkDetailOut


def _assignee_email(db: Session, uid: UUID | None) -> str | None:
    if not uid:
        return None
    u = db.query(User).filter(User.id == uid).first()
    return u.email if u else None


def _activity_summary_for(db: Session, object_type: str, object_id: UUID) -> ActivitySummaryOut:
    rows = (
        db.query(ActivityLog.action, func.count())
        .filter(ActivityLog.object_type == object_type, ActivityLog.object_id == object_id)
        .group_by(ActivityLog.action)
        .all()
    )
    return ActivitySummaryOut(by_action={str(a): int(c) for a, c in rows})


def _open_tasks(db: Session, object_type: str, object_id: UUID) -> list[TaskWorkspaceBrief]:
    open_tasks_q = (
        db.query(Task)
        .filter(
            Task.is_active.is_(True),
            Task.status != "done",
            Task.related_object_type == object_type,
            Task.related_object_id == object_id,
        )
        .order_by(Task.due_at.asc().nullslast())
        .limit(30)
        .all()
    )
    return [
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


def _recent_interactions(db: Session, object_type: str, object_id: UUID, limit: int = 25):
    rows = (
        db.query(Interaction)
        .filter(Interaction.related_object_type == object_type, Interaction.related_object_id == object_id)
        .order_by(Interaction.interaction_date.desc())
        .limit(limit)
        .all()
    )
    return [InteractionWorkspaceBrief.model_validate(i) for i in rows]


def _recent_ai(db: Session, object_type: str, object_id: UUID, limit: int = 20):
    rows = (
        db.query(AIOutput)
        .filter(AIOutput.input_object_type == object_type, AIOutput.input_object_id == object_id)
        .order_by(AIOutput.created_at.desc())
        .limit(limit)
        .all()
    )
    return [AIOutputWorkspaceBrief.model_validate(a) for a in rows]


def _product_interest_company(db: Session, company_id: UUID) -> ProductInterestSummaryOut:
    co = db.query(Company).filter(Company.id == company_id).first()
    tags: list[str] = []
    if co and co.product_interest_tags:
        tags = [t.strip() for t in co.product_interest_tags.replace(";", ",").split(",") if t.strip()]
    leads = db.query(Lead).filter(Lead.company_id == company_id, Lead.is_active.is_(True)).all()
    snippets = [x.product_interest for x in leads if x.product_interest]
    return ProductInterestSummaryOut(
        tags_from_company=tags,
        lead_interest_snippets=snippets[:50],
        active_lead_count=len(leads),
    )


def build_company_workspace(db: Session, company_id: UUID) -> CompanyWorkspaceOut | None:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return None
    contacts = (
        db.query(Contact)
        .filter(Contact.company_id == company_id, Contact.is_active.is_(True))
        .order_by(Contact.last_name, Contact.first_name)
        .limit(200)
        .all()
    )
    leads = (
        db.query(Lead)
        .filter(Lead.company_id == company_id, Lead.is_active.is_(True))
        .order_by(Lead.created_at.desc())
        .limit(100)
        .all()
    )
    lead_ids = [l.id for l in leads]
    conds = [RFQ.company_id == company_id]
    if lead_ids:
        conds.append(RFQ.lead_id.in_(lead_ids))
    related_rfqs = db.query(RFQ).filter(or_(*conds)).order_by(RFQ.created_at.desc()).limit(50).all()
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
        .filter(Sample.company_id == company_id)
        .order_by(Sample.created_at.desc())
        .limit(50)
        .all()
    )
    fv_rows = (
        db.query(FieldVisitTarget, FieldVisitPlan)
        .join(FieldVisitPlan, FieldVisitTarget.visit_plan_id == FieldVisitPlan.id)
        .filter(FieldVisitTarget.company_id == company_id)
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

    return CompanyWorkspaceOut(
        company=CompanyDetailOut.model_validate(company),
        contacts=[ContactDetailOut.model_validate(c) for c in contacts],
        leads=[LeadOut.model_validate(l) for l in leads],
        related_rfqs=[RFQWorkspaceBrief.model_validate(r) for r in related_rfqs],
        related_samples=[SampleWorkspaceBrief.model_validate(s) for s in related_samples],
        related_orders=[OrderWorkspaceBrief.model_validate(o) for o in related_orders],
        related_field_visits=related_field,
        recent_interactions=_recent_interactions(db, "company", company_id),
        open_tasks=_open_tasks(db, "company", company_id),
        recent_ai_outputs=_recent_ai(db, "company", company_id),
        product_interest_summary=_product_interest_company(db, company_id),
        activity_summary=_activity_summary_for(db, "company", company_id),
    )


def build_contact_workspace(db: Session, contact_id: UUID) -> ContactWorkspaceOut | None:
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        return None
    company = db.query(Company).filter(Company.id == contact.company_id).first()
    if not company:
        return None
    leads_rows = (
        db.query(Lead)
        .filter(
            Lead.is_active.is_(True),
            or_(Lead.primary_contact_id == contact_id, Lead.company_id == contact.company_id),
        )
        .order_by(Lead.created_at.desc())
        .limit(80)
        .all()
    )
    seen: dict[UUID, Lead] = {}
    for l in leads_rows:
        seen[l.id] = l
    leads = list(seen.values())

    conds = [RFQ.contact_id == contact_id]
    if contact.company_id:
        conds.append(RFQ.company_id == contact.company_id)
    lead_ids_same_co = [l.id for l in db.query(Lead.id).filter(Lead.company_id == contact.company_id).all()]
    if lead_ids_same_co:
        conds.append(RFQ.lead_id.in_(lead_ids_same_co))
    rfqs = db.query(RFQ).filter(or_(*conds)).order_by(RFQ.created_at.desc()).limit(40).all()
    rfq_ids = [r.id for r in rfqs]

    samples = (
        db.query(Sample)
        .filter(or_(Sample.contact_id == contact_id, Sample.company_id == contact.company_id))
        .order_by(Sample.created_at.desc())
        .limit(40)
        .all()
    )

    orders_cond = [Order.contact_id == contact_id, Order.company_id == contact.company_id]
    if rfq_ids:
        orders_cond.append(Order.rfq_id.in_(rfq_ids))
    orders = db.query(Order).filter(or_(*orders_cond)).order_by(Order.created_at.desc()).limit(40).all()

    return ContactWorkspaceOut(
        contact=ContactDetailOut.model_validate(contact),
        company=CompanySummaryCard.model_validate(company),
        related_leads=[LeadOut.model_validate(l) for l in leads],
        related_rfqs=[RFQWorkspaceBrief.model_validate(r) for r in rfqs],
        related_samples=[SampleWorkspaceBrief.model_validate(s) for s in samples],
        related_orders=[OrderWorkspaceBrief.model_validate(o) for o in orders],
        recent_interactions=_recent_interactions(db, "contact", contact_id),
        open_tasks=_open_tasks(db, "contact", contact_id),
        recent_ai_outputs=_recent_ai(db, "contact", contact_id),
        activity_summary=_activity_summary_for(db, "contact", contact_id),
    )


def _partner_comparison_from_links(links: list[ProductPartnerLink]) -> PartnerComparisonHints:
    def pick_min_moq(row: ProductPartnerLink) -> int:
        v = row.partner_moq
        if v is not None:
            return v
        return 10**9

    def cap_score(val: str | None) -> int:
        if not val:
            return 0
        v = val.lower()
        if any(x in v for x in ("complete", "ready", "yes", "passed", "available")):
            return 3
        if any(x in v for x in ("pending", "partial", "progress")):
            return 2
        return 1

    def customization_score(val: str | None) -> int:
        if not val:
            return 0
        v = val.lower()
        order = ["oem", "odm", "tier-1", "tier 1", "tier1", "strong", "high", "medium"]
        for i, key in enumerate(order):
            if key in v:
                return len(order) - i
        return 1

    if not links:
        return PartnerComparisonHints(
            best_for_sample_partner_id=None,
            best_for_low_moq_partner_id=None,
            best_for_customization_partner_id=None,
            best_for_certification_partner_id=None,
        )

    sample_pool = [ln for ln in links if ln.sample_available is True]
    sample_pick = None
    if sample_pool:
        sample_pick = sorted(sample_pool, key=lambda x: (x.lead_time_days or 9999, pick_min_moq(x)))[0]
    low_moq = sorted(links, key=pick_min_moq)[0]
    cust_pick = sorted(links, key=lambda x: customization_score(x.capability_level), reverse=True)[0]
    cert_pick = sorted(links, key=lambda x: cap_score(x.certification_status), reverse=True)[0]

    return PartnerComparisonHints(
        best_for_sample_partner_id=sample_pick.manufacturing_partner_id if sample_pick else None,
        best_for_low_moq_partner_id=low_moq.manufacturing_partner_id,
        best_for_customization_partner_id=cust_pick.manufacturing_partner_id,
        best_for_certification_partner_id=cert_pick.manufacturing_partner_id,
    )


def build_product_workspace(db: Session, product_id: UUID) -> ProductWorkspaceOut | None:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    links = (
        db.query(ProductPartnerLink)
        .filter(ProductPartnerLink.product_id == product_id)
        .order_by(ProductPartnerLink.is_preferred.desc(), ProductPartnerLink.updated_at.desc())
        .all()
    )
    partner_ids = [ln.manufacturing_partner_id for ln in links]
    partners: list[ManufacturingPartner] = []
    if partner_ids:
        partners = db.query(ManufacturingPartner).filter(ManufacturingPartner.id.in_(partner_ids)).all()
    pmap = {p.id: p for p in partners}
    partner_rows = [
        LinkedPartnerRow(
            link=ProductPartnerLinkDetailOut.model_validate(ln),
            partner=PartnerDetailOut.model_validate(pmap[ln.manufacturing_partner_id]),
        )
        for ln in links
        if ln.manufacturing_partner_id in pmap
    ]
    link_details = [ProductPartnerLinkDetailOut.model_validate(ln) for ln in links]

    sub_rfq = db.query(RFQItem.rfq_id).filter(RFQItem.product_id == product_id).distinct()
    rfq_ids_sub = [r[0] for r in sub_rfq.all()]
    related_rfqs = (
        db.query(RFQ).filter(RFQ.id.in_(rfq_ids_sub)).order_by(RFQ.created_at.desc()).limit(50).all()
        if rfq_ids_sub
        else []
    )

    related_samples = (
        db.query(Sample)
        .filter(Sample.product_id == product_id)
        .order_by(Sample.created_at.desc())
        .limit(50)
        .all()
    )

    oids = [o[0] for o in db.query(OrderItem.order_id).filter(OrderItem.product_id == product_id).distinct().all()]
    related_orders = (
        db.query(Order).filter(Order.id.in_(oids)).order_by(Order.created_at.desc()).limit(50).all() if oids else []
    )

    doc_rows = (
        db.query(ProductDocument, File)
        .join(File, ProductDocument.file_id == File.id)
        .filter(ProductDocument.product_id == product_id)
        .order_by(ProductDocument.created_at.desc())
        .limit(100)
        .all()
    )
    files = [
        ProductWorkspaceFileBrief(
            id=pd.id,
            file_id=pd.file_id,
            doc_type=pd.doc_type,
            original_filename=f.original_filename,
        )
        for pd, f in doc_rows
    ]

    return ProductWorkspaceOut(
        product=ProductDetailOut.model_validate(product),
        linked_manufacturing_partners=[PartnerDetailOut.model_validate(p) for p in partners],
        product_partner_link_details=link_details,
        partner_rows=partner_rows,
        related_rfqs=[RFQWorkspaceBrief.model_validate(r) for r in related_rfqs],
        related_samples=[SampleWorkspaceBrief.model_validate(s) for s in related_samples],
        related_orders=[OrderWorkspaceBrief.model_validate(o) for o in related_orders],
        files=files,
        open_tasks=_open_tasks(db, "product", product_id),
        recent_ai_outputs=_recent_ai(db, "product", product_id),
        partner_comparison=_partner_comparison_from_links(links),
        activity_summary=_activity_summary_for(db, "product", product_id),
    )


def build_partner_workspace(db: Session, partner_id: UUID) -> PartnerWorkspaceOut | None:
    partner = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == partner_id).first()
    if not partner:
        return None
    links = (
        db.query(ProductPartnerLink)
        .filter(ProductPartnerLink.manufacturing_partner_id == partner_id)
        .order_by(ProductPartnerLink.is_preferred.desc(), ProductPartnerLink.updated_at.desc())
        .all()
    )
    product_ids = [ln.product_id for ln in links]
    products: list[Product] = []
    if product_ids:
        products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    prmap = {p.id: p for p in products}
    link_details = [ProductPartnerLinkDetailOut.model_validate(ln) for ln in links]

    cand_rfq_ids = [
        r[0]
        for r in db.query(RFQPartnerCandidate.rfq_id)
        .filter(RFQPartnerCandidate.partner_id == partner_id)
        .distinct()
        .all()
    ]
    related_rfqs = (
        db.query(RFQ).filter(RFQ.id.in_(cand_rfq_ids)).order_by(RFQ.created_at.desc()).limit(50).all()
        if cand_rfq_ids
        else []
    )

    quotations = (
        db.query(Quotation)
        .filter(Quotation.manufacturing_partner_id == partner_id)
        .order_by(Quotation.created_at.desc())
        .limit(80)
        .all()
    )

    related_samples = (
        db.query(Sample)
        .filter(Sample.manufacturing_partner_id == partner_id)
        .order_by(Sample.created_at.desc())
        .limit(50)
        .all()
    )

    related_orders = (
        db.query(Order)
        .filter(Order.manufacturing_partner_id == partner_id)
        .order_by(Order.created_at.desc())
        .limit(50)
        .all()
    )

    qdocs = (
        db.query(QualityDocument)
        .filter(QualityDocument.manufacturing_partner_id == partner_id)
        .order_by(QualityDocument.created_at.desc())
        .limit(100)
        .all()
    )

    return PartnerWorkspaceOut(
        partner=PartnerDetailOut.model_validate(partner),
        linked_products=[ProductDetailOut.model_validate(prmap[ln.product_id]) for ln in links if ln.product_id in prmap],
        product_partner_link_details=link_details,
        related_rfqs=[RFQWorkspaceBrief.model_validate(r) for r in related_rfqs],
        related_quotations=[QuotationWorkspaceBrief.model_validate(q) for q in quotations],
        related_samples=[SampleWorkspaceBrief.model_validate(s) for s in related_samples],
        related_orders=[OrderWorkspaceBrief.model_validate(o) for o in related_orders],
        quality_documents=[QualityDocumentBrief.model_validate(d) for d in qdocs],
        recent_interactions=_recent_interactions(db, "manufacturing_partner", partner_id),
        open_tasks=_open_tasks(db, "manufacturing_partner", partner_id),
        recent_ai_outputs=_recent_ai(db, "manufacturing_partner", partner_id),
        activity_summary=_activity_summary_for(db, "manufacturing_partner", partner_id),
    )
