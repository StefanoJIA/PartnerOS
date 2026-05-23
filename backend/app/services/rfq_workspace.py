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
    Quotation,
    QuotationItem,
    RFQ,
    RFQItem,
    RFQPartnerCandidate,
    Sample,
    Task,
    User,
)
from app.schemas.lead_workspace import (
    AIOutputWorkspaceBrief,
    InteractionWorkspaceBrief,
    OrderWorkspaceBrief,
    SampleWorkspaceBrief,
    TaskWorkspaceBrief,
)
from app.schemas.rfq_domain import (
    ActivitySummaryOut,
    CompanySummaryMini,
    ContactSummaryMini,
    LeadSummaryMini,
    PartnerBrief,
    ProductBrief,
    QuotationDetailOut,
    QuotationItemOut,
    RFQDetailOut,
    RFQItemOut,
    RFQPartnerCandidateOut,
    RFQPartnerCandidateWithPartnerOut,
    RFQWorkspaceOut,
    RfqFileBrief,
)
from app.services.quotation_comparison import build_quotation_comparison


def _assignee_email(db: Session, uid: UUID | None) -> str | None:
    if not uid:
        return None
    u = db.query(User).filter(User.id == uid).first()
    return u.email if u else None


def _activity_summary(db: Session, object_id: UUID) -> ActivitySummaryOut:
    rows = (
        db.query(ActivityLog.action, func.count())
        .filter(ActivityLog.object_type == "rfq", ActivityLog.object_id == object_id)
        .group_by(ActivityLog.action)
        .all()
    )
    return ActivitySummaryOut(by_action={str(a): int(c) for a, c in rows})


def candidate_sort_key(c: RFQPartnerCandidate) -> tuple:
    pref = 0 if c.is_preferred else 1
    recv = c.quote_received_at.timestamp() if c.quote_received_at else -1.0
    fit_map = {"high": 0, "medium": 1, "low": 2, "": 3}
    fit = fit_map.get((c.product_fit or "").lower(), 3)
    lt = c.lead_time_days if c.lead_time_days is not None else 99999
    moq = c.partner_moq if c.partner_moq is not None else 999999
    ts = c.created_at.timestamp() if c.created_at else 0
    return (pref, -recv, fit, lt, moq, ts)


def build_rfq_workspace(db: Session, rfq_id: UUID) -> RFQWorkspaceOut | None:
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        return None

    company = db.query(Company).filter(Company.id == rfq.company_id).first() if rfq.company_id else None
    contact = db.query(Contact).filter(Contact.id == rfq.contact_id).first() if rfq.contact_id else None
    lead_row = db.query(Lead).filter(Lead.id == rfq.lead_id).first() if rfq.lead_id else None

    owner_display = None
    if rfq.owner_user_id:
        ou = db.query(User).filter(User.id == rfq.owner_user_id).first()
        if ou:
            owner_display = f"{ou.full_name} <{ou.email}>"

    items = db.query(RFQItem).filter(RFQItem.rfq_id == rfq_id).order_by(RFQItem.created_at.asc()).all()
    product_ids = {i.product_id for i in items if i.product_id}
    products = db.query(Product).filter(Product.id.in_(product_ids)).all() if product_ids else []
    pmap: dict[UUID, Product] = {p.id: p for p in products}
    rfq_items: list[RFQItemOut] = []
    for it in items:
        pb = ProductBrief.model_validate(pmap[it.product_id]) if it.product_id and it.product_id in pmap else None
        base = RFQItemOut.model_validate(it)
        rfq_items.append(base.model_copy(update={"product": pb}))

    cands = db.query(RFQPartnerCandidate).filter(RFQPartnerCandidate.rfq_id == rfq_id).all()
    cands_sorted = sorted(cands, key=candidate_sort_key)
    partner_ids = {c.partner_id for c in cands_sorted}
    partners = (
        db.query(ManufacturingPartner).filter(ManufacturingPartner.id.in_(partner_ids)).all() if partner_ids else []
    )
    part_map: dict[UUID, ManufacturingPartner] = {p.id: p for p in partners}

    candidate_briefs: list[PartnerBrief] = []
    seen_cb: set[UUID] = set()
    for c in cands_sorted:
        if c.partner_id in part_map and c.partner_id not in seen_cb:
            seen_cb.add(c.partner_id)
            candidate_briefs.append(PartnerBrief.model_validate(part_map[c.partner_id]))

    partner_detail_rows: list[RFQPartnerCandidateWithPartnerOut] = []
    for c in cands_sorted:
        p = part_map.get(c.partner_id)
        if not p:
            continue
        partner_detail_rows.append(
            RFQPartnerCandidateWithPartnerOut(
                **RFQPartnerCandidateOut.model_validate(c).model_dump(),
                partner=PartnerBrief.model_validate(p),
            )
        )

    quotations = db.query(Quotation).filter(Quotation.rfq_id == rfq_id).order_by(Quotation.created_at.asc()).all()
    q_partner_ids = {q.manufacturing_partner_id for q in quotations if q.manufacturing_partner_id}
    q_product_ids = {q.product_id for q in quotations if q.product_id}
    for qu in quotations:
        if qu.manufacturing_partner_id and qu.manufacturing_partner_id not in part_map:
            p2 = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == qu.manufacturing_partner_id).first()
            if p2:
                part_map[p2.id] = p2
        if qu.product_id and qu.product_id not in pmap:
            pr2 = db.query(Product).filter(Product.id == qu.product_id).first()
            if pr2:
                pmap[pr2.id] = pr2

    q_ids = [q.id for q in quotations]
    all_q_items: list[QuotationItem] = []
    if q_ids:
        all_q_items = (
            db.query(QuotationItem)
            .filter(QuotationItem.quotation_id.in_(q_ids))
            .order_by(QuotationItem.created_at)
            .all()
        )
    q_item_by_q: dict[UUID, list[QuotationItem]] = {}
    for li in all_q_items:
        q_item_by_q.setdefault(li.quotation_id, []).append(li)

    quotation_items_flat: list[QuotationItemOut] = [QuotationItemOut.model_validate(x) for x in all_q_items]

    quotations_out: list[QuotationDetailOut] = []
    for q in quotations:
        pp = (
            PartnerBrief.model_validate(part_map[q.manufacturing_partner_id])
            if q.manufacturing_partner_id and q.manufacturing_partner_id in part_map
            else None
        )
        pr = ProductBrief.model_validate(pmap[q.product_id]) if q.product_id and q.product_id in pmap else None
        lines = [QuotationItemOut.model_validate(li) for li in q_item_by_q.get(q.id, [])]
        quotations_out.append(
            QuotationDetailOut(
                id=q.id,
                rfq_id=q.rfq_id,
                manufacturing_partner_id=q.manufacturing_partner_id,
                product_id=q.product_id,
                quantity=q.quantity,
                unit_price=q.unit_price,
                currency=q.currency,
                incoterm=q.incoterm,
                moq=q.moq,
                lead_time=q.lead_time,
                sample_cost=q.sample_cost,
                tooling_cost=q.tooling_cost,
                packaging_cost=q.packaging_cost,
                estimated_shipping_cost=q.estimated_shipping_cost,
                landed_cost=q.landed_cost,
                target_margin=q.target_margin,
                notes=q.notes,
                valid_until=q.valid_until,
                created_at=q.created_at,
                updated_at=q.updated_at,
                partner=pp,
                product=pr,
                lines=lines,
            )
        )

    comparison = build_quotation_comparison(quotations, part_map)

    related_samples = (
        db.query(Sample).filter(Sample.rfq_id == rfq_id).order_by(Sample.created_at.desc()).limit(50).all()
    )
    related_orders = db.query(Order).filter(Order.rfq_id == rfq_id).order_by(Order.created_at.desc()).limit(50).all()

    recent_ix = (
        db.query(Interaction)
        .filter(Interaction.related_object_type == "rfq", Interaction.related_object_id == rfq_id)
        .order_by(Interaction.interaction_date.desc())
        .limit(25)
        .all()
    )
    open_tasks_q = (
        db.query(Task)
        .filter(
            Task.is_active.is_(True),
            Task.status != "done",
            Task.related_object_type == "rfq",
            Task.related_object_id == rfq_id,
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
        .filter(AIOutput.input_object_type == "rfq", AIOutput.input_object_id == rfq_id)
        .order_by(AIOutput.created_at.desc())
        .limit(20)
        .all()
    )

    fa_rows = (
        db.query(FileAttachment, File)
        .join(File, FileAttachment.file_id == File.id)
        .filter(FileAttachment.object_type == "rfq", FileAttachment.object_id == rfq_id)
        .order_by(FileAttachment.created_at.desc())
        .limit(100)
        .all()
    )
    files = [
        RfqFileBrief(id=att.id, file_id=att.file_id, original_filename=f.original_filename, purpose=att.purpose)
        for att, f in fa_rows
    ]

    return RFQWorkspaceOut(
        rfq=RFQDetailOut.model_validate(rfq),
        company=CompanySummaryMini.model_validate(company) if company else None,
        contact=ContactSummaryMini.model_validate(contact) if contact else None,
        lead=LeadSummaryMini.model_validate(lead_row) if lead_row else None,
        owner_display=owner_display,
        rfq_items=rfq_items,
        candidate_manufacturing_partners=candidate_briefs,
        partner_candidates_with_partner_detail=partner_detail_rows,
        quotations=quotations_out,
        quotation_items=quotation_items_flat,
        quotation_comparison=comparison,
        related_samples=[SampleWorkspaceBrief.model_validate(s) for s in related_samples],
        related_orders=[OrderWorkspaceBrief.model_validate(o) for o in related_orders],
        recent_interactions=[InteractionWorkspaceBrief.model_validate(i) for i in recent_ix],
        open_tasks=open_tasks,
        recent_ai_outputs=[AIOutputWorkspaceBrief.model_validate(a) for a in recent_ai],
        files=files,
        activity_summary=_activity_summary(db, rfq_id),
    )
