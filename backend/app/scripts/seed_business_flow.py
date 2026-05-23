"""Idempotent full business-flow demo for Jefferson Group (neutral partner names).

Prerequisites: run `python -m app.scripts.seed` first so Admin user exists.

Run:
  cd backend
  python -m app.scripts.seed_business_flow

Safe to re-run: rows are keyed by demo RFQ / sample / order numbers and stable task titles.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.core.database import get_session_factory
from app.models import (
    AIOutput,
    Company,
    Contact,
    Interaction,
    Lead,
    ManufacturingPartner,
    Note,
    ObjectTag,
    Order,
    OrderItem,
    ProductionMilestone,
    Product,
    ProductPartnerLink,
    Quotation,
    RFQ,
    RFQItem,
    RFQPartnerCandidate,
    Sample,
    ShippingRecord,
    Tag,
    Task,
    User,
)
from app.models.enums import (
    RFQPartnerCandidateStatus,
    RFQStatus,
    SampleStatus,
)

MARKER_RFQ_NUMBER = "RFQ-DEMO-JEFFERSON"
MARKER_SAMPLE_NUMBER = "SMP-DEMO-JEFFERSON"
MARKER_ORDER_NUMBER = "ORD-DEMO-JEFFERSON"
SEED_AI_PROMPT_MARKER = "seed_business_flow"


def _apply_product_partner_link(
    db,
    *,
    uid: uuid.UUID,
    product_id: uuid.UUID,
    partner_id: uuid.UUID,
    is_preferred: bool,
    notes: str | None,
    capability_level: str | None,
    partner_moq: int | None,
    lead_time_days: int | None,
    partner_price_range: str | None,
    sample_available: bool | None,
    certification_status: str | None,
) -> None:
    row = (
        db.query(ProductPartnerLink)
        .filter(
            ProductPartnerLink.product_id == product_id,
            ProductPartnerLink.manufacturing_partner_id == partner_id,
        )
        .first()
    )
    if row:
        row.is_preferred = is_preferred
        row.notes = notes
        row.capability_level = capability_level
        row.partner_moq = partner_moq
        row.lead_time_days = lead_time_days
        row.partner_price_range = partner_price_range
        row.sample_available = sample_available
        row.certification_status = certification_status
        row.updated_by_id = uid
    else:
        db.add(
            ProductPartnerLink(
                product_id=product_id,
                manufacturing_partner_id=partner_id,
                is_preferred=is_preferred,
                notes=notes,
                capability_level=capability_level,
                partner_moq=partner_moq,
                lead_time_days=lead_time_days,
                partner_price_range=partner_price_range,
                sample_available=sample_available,
                certification_status=certification_status,
                created_by_id=uid,
                updated_by_id=uid,
            )
        )
    db.commit()


def _ensure_quotation(
    db,
    *,
    uid: uuid.UUID,
    rfq_id: uuid.UUID,
    partner_id: uuid.UUID,
    product_id: uuid.UUID,
    quantity: int,
    unit_price: Decimal,
    currency: str,
    incoterm: str | None,
    moq: int,
    lead_time: str,
    sample_cost: Decimal,
    tooling_cost: Decimal | None,
    packaging_cost: Decimal | None,
    estimated_shipping_cost: Decimal | None,
    landed_cost: Decimal,
    target_margin: Decimal,
    valid_until: date | None,
    notes: str | None,
) -> None:
    row = (
        db.query(Quotation)
        .filter(
            Quotation.rfq_id == rfq_id,
            Quotation.manufacturing_partner_id == partner_id,
            Quotation.product_id == product_id,
        )
        .first()
    )
    if row:
        row.quantity = quantity
        row.unit_price = unit_price
        row.currency = currency
        row.incoterm = incoterm
        row.moq = moq
        row.lead_time = lead_time
        row.sample_cost = sample_cost
        row.tooling_cost = tooling_cost
        row.packaging_cost = packaging_cost
        row.estimated_shipping_cost = estimated_shipping_cost
        row.landed_cost = landed_cost
        row.target_margin = target_margin
        row.valid_until = valid_until
        row.notes = notes
        row.updated_by_id = uid
    else:
        db.add(
            Quotation(
                rfq_id=rfq_id,
                manufacturing_partner_id=partner_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                currency=currency,
                incoterm=incoterm,
                moq=moq,
                lead_time=lead_time,
                sample_cost=sample_cost,
                tooling_cost=tooling_cost,
                packaging_cost=packaging_cost,
                estimated_shipping_cost=estimated_shipping_cost,
                landed_cost=landed_cost,
                target_margin=target_margin,
                valid_until=valid_until,
                notes=notes,
                created_by_id=uid,
                updated_by_id=uid,
            )
        )
    db.commit()


def _ensure_task(
    db,
    *,
    uid: uuid.UUID,
    title: str,
    due_at: datetime,
    priority: str,
    related_object_type: str,
    related_object_id: uuid.UUID,
) -> None:
    row = (
        db.query(Task)
        .filter(Task.title == title, Task.related_object_type == related_object_type, Task.related_object_id == related_object_id)
        .first()
    )
    if row:
        row.due_at = due_at
        row.priority = priority
        row.status = "open"
        row.updated_by_id = uid
    else:
        db.add(
            Task(
                title=title,
                due_at=due_at,
                status="open",
                priority=priority,
                related_object_type=related_object_type,
                related_object_id=related_object_id,
                created_by_id=uid,
                updated_by_id=uid,
            )
        )
    db.commit()


def _ensure_ai_demo_outputs(db, *, uid: uuid.UUID, rfq_id: uuid.UUID, lead_id: uuid.UUID) -> None:
    specs = [
        ("rfq_summary", "rfq", rfq_id, "Neutral RFQ recap for customer-facing review (no supplier bias)."),
        (
            "partner_recommendation",
            "lead",
            lead_id,
            "Compare Demo Lifting System Partner vs Demo Education Furniture Partner on schedule and landed cost.",
        ),
    ]
    for task_type, obj_type, obj_id, text in specs:
        exists = (
            db.query(AIOutput)
            .filter(
                AIOutput.task_type == task_type,
                AIOutput.input_object_type == obj_type,
                AIOutput.input_object_id == obj_id,
                AIOutput.prompt == SEED_AI_PROMPT_MARKER,
            )
            .first()
        )
        if exists:
            exists.output_text = text
            exists.updated_by_id = uid
        else:
            db.add(
                AIOutput(
                    task_type=task_type,
                    input_object_type=obj_type,
                    input_object_id=obj_id,
                    prompt=SEED_AI_PROMPT_MARKER,
                    output_text=text,
                    status="draft",
                    created_by_id=uid,
                    updated_by_id=uid,
                )
            )
    db.commit()


def main() -> None:
    db = get_session_factory()()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            raise RuntimeError("admin@example.com not found — run: python -m app.scripts.seed")

        uid = admin.id
        now = datetime.now(timezone.utc)
        today = date.today()
        vu = today + timedelta(days=21)

        company = db.query(Company).filter(Company.company_name == "Jefferson Group Demo").first()
        if not company:
            company = Company(
                company_name="Jefferson Group Demo",
                company_type="Office Furniture Dealer",
                city="Indianapolis",
                state="IN",
                country="United States",
                notes="Demo tenant for end-to-end PartnerOS walkthrough.",
                created_by_id=uid,
                updated_by_id=uid,
            )
            db.add(company)
            db.commit()
            db.refresh(company)
        else:
            company.updated_by_id = uid

        contact = db.query(Contact).filter(Contact.email == "tamara.demo@jefferson-group.example").first()
        if not contact:
            contact = Contact(
                first_name="Tamara",
                last_name="Demo Contact",
                company_id=company.id,
                email="tamara.demo@jefferson-group.example",
                title="Procurement",
                contact_type="Buyer",
                created_by_id=uid,
                updated_by_id=uid,
            )
            db.add(contact)
            db.commit()
            db.refresh(contact)

        lead = (
            db.query(Lead)
            .filter(Lead.company_id == company.id, Lead.lead_name == "Heavy-duty adjustable desk frame opportunity")
            .first()
        )
        if not lead:
            lead = Lead(
                lead_name="Heavy-duty adjustable desk frame opportunity",
                company_id=company.id,
                primary_contact_id=contact.id,
                source="LinkedIn",
                lead_type="RFQ Opportunity",
                current_stage="RFQ Created",
                priority="high",
                next_action_due_date=today + timedelta(days=3),
                created_by_id=uid,
                updated_by_id=uid,
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)

        def ensure_partner(name: str, ptype: str, city: str) -> ManufacturingPartner:
            row = db.query(ManufacturingPartner).filter(ManufacturingPartner.partner_name == name).first()
            if row:
                return row
            row = ManufacturingPartner(
                partner_name=name,
                partner_type=ptype,
                country="China",
                city=city,
                certifications="Demo certifications on file.",
                project_fit_rating=4,
                risk_level="low",
                notes="Neutral demo manufacturing partner — equal weighting to any other row.",
                created_by_id=uid,
                updated_by_id=uid,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return row

        partner_lift = ensure_partner(
            "Demo Lifting System Partner",
            "Lifting System Manufacturer",
            "Shenzhen",
        )
        partner_edu = ensure_partner(
            "Demo Education Furniture Partner",
            "Education Furniture Manufacturer",
            "Dongguan",
        )

        def ensure_product(name: str, category: str) -> Product:
            row = db.query(Product).filter(Product.product_name == name).first()
            if row:
                return row
            row = Product(
                product_name=name,
                product_category=category,
                description="Catalog SKU for Jefferson demo flow.",
                created_by_id=uid,
                updated_by_id=uid,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return row

        prod_frame = ensure_product(
            "660 lb Heavy-duty Adjustable Desk Frame",
            "Adjustable Desk Frame",
        )
        prod_table = ensure_product(
            "Collaborative Education Table Demo",
            "Education Furniture",
        )

        _apply_product_partner_link(
            db,
            uid=uid,
            product_id=prod_frame.id,
            partner_id=partner_lift.id,
            is_preferred=True,
            notes="Preferred for lifting / heavy-duty frame programs in this demo dataset.",
            capability_level="high",
            partner_moq=20,
            lead_time_days=35,
            partner_price_range="USD 210–280 / unit",
            sample_available=True,
            certification_status="UL/BIFMA evidence available",
        )
        _apply_product_partner_link(
            db,
            uid=uid,
            product_id=prod_frame.id,
            partner_id=partner_edu.id,
            is_preferred=False,
            notes="Secondary path: education supplier with cross-category bundle option.",
            capability_level="medium",
            partner_moq=30,
            lead_time_days=42,
            partner_price_range="USD 230–300 / unit",
            sample_available=True,
            certification_status="ISO process; project certs TBD",
        )
        _apply_product_partner_link(
            db,
            uid=uid,
            product_id=prod_table.id,
            partner_id=partner_edu.id,
            is_preferred=True,
            notes="Primary education SKU alignment for collaborative learning installs.",
            capability_level="high",
            partner_moq=15,
            lead_time_days=40,
            partner_price_range="USD 280–360 / unit",
            sample_available=True,
            certification_status="complete",
        )

        rfq = db.query(RFQ).filter(RFQ.rfq_number == MARKER_RFQ_NUMBER).first()
        if not rfq:
            rfq = RFQ(
                rfq_number=MARKER_RFQ_NUMBER,
                lead_id=lead.id,
                company_id=company.id,
                contact_id=contact.id,
                customer_requirement="20 units heavy-duty frame evaluation for pilot install.",
                quantity=20,
                target_delivery_date=today + timedelta(days=90),
                required_certifications="BIFMA / stability documentation",
                status=RFQStatus.partner_quoted.value,
                owner_user_id=uid,
                created_by_id=uid,
                updated_by_id=uid,
            )
            db.add(rfq)
            db.commit()
            db.refresh(rfq)
        else:
            rfq.customer_requirement = "20 units heavy-duty frame evaluation for pilot install."
            rfq.quantity = 20
            rfq.status = RFQStatus.partner_quoted.value
            rfq.updated_by_id = uid
            db.commit()

        item = db.query(RFQItem).filter(RFQItem.rfq_id == rfq.id, RFQItem.product_id == prod_frame.id).first()
        if not item:
            item = RFQItem(
                rfq_id=rfq.id,
                product_id=prod_frame.id,
                quantity=20,
                spec_notes="660 lb rated frame; anti-collision; cable routing.",
                created_by_id=uid,
                updated_by_id=uid,
            )
            db.add(item)
            db.commit()
            db.refresh(item)

        def ensure_candidate(partner: ManufacturingPartner) -> None:
            row = (
                db.query(RFQPartnerCandidate)
                .filter(RFQPartnerCandidate.rfq_id == rfq.id, RFQPartnerCandidate.partner_id == partner.id)
                .first()
            )
            if partner.id == partner_lift.id:
                status = RFQPartnerCandidateStatus.quote_requested.value
                qreq = now - timedelta(days=2)
                qrec = None
                cap = "high"
                moq = 20
                lt = 35
                pr = "USD 210–280"
                cert = "complete"
                pfit = "high"
            else:
                status = RFQPartnerCandidateStatus.quote_received.value
                qreq = now - timedelta(days=3)
                qrec = now - timedelta(days=1)
                cap = "medium"
                moq = 30
                lt = 42
                pr = "USD 230–300"
                cert = "pending UL submittal"
                pfit = "medium"
            if row:
                row.partner_status = status
                row.quote_requested_at = qreq
                row.quote_received_at = qrec
                row.capability_level = cap
                row.partner_moq = moq
                row.lead_time_days = lt
                row.partner_price_range = pr
                row.sample_available = True
                row.certification_status = cert
                row.product_fit = pfit
                row.updated_by_id = uid
            else:
                db.add(
                    RFQPartnerCandidate(
                        rfq_id=rfq.id,
                        partner_id=partner.id,
                        partner_status=status,
                        quote_requested_at=qreq,
                        quote_received_at=qrec,
                        capability_level=cap,
                        partner_moq=moq,
                        lead_time_days=lt,
                        partner_price_range=pr,
                        sample_available=True,
                        certification_status=cert,
                        product_fit=pfit,
                        created_by_id=uid,
                        updated_by_id=uid,
                    )
                )
            db.commit()

        ensure_candidate(partner_lift)
        ensure_candidate(partner_edu)

        _ensure_quotation(
            db,
            uid=uid,
            rfq_id=rfq.id,
            partner_id=partner_lift.id,
            product_id=prod_frame.id,
            quantity=20,
            unit_price=Decimal("248.50"),
            currency="USD",
            incoterm="FOB",
            moq=20,
            lead_time="34 days",
            sample_cost=Decimal("120"),
            tooling_cost=Decimal("800"),
            packaging_cost=Decimal("90"),
            estimated_shipping_cost=Decimal("420"),
            landed_cost=Decimal("5680.00"),
            target_margin=Decimal("0.27"),
            valid_until=vu,
            notes="Steel gauge upgrade included.",
        )
        _ensure_quotation(
            db,
            uid=uid,
            rfq_id=rfq.id,
            partner_id=partner_edu.id,
            product_id=prod_frame.id,
            quantity=20,
            unit_price=Decimal("265.00"),
            currency="USD",
            incoterm="CIF",
            moq=30,
            lead_time="40 days",
            sample_cost=Decimal("135"),
            tooling_cost=Decimal("650"),
            packaging_cost=Decimal("110"),
            estimated_shipping_cost=Decimal("510"),
            landed_cost=Decimal("5920.00"),
            target_margin=Decimal("0.24"),
            valid_until=vu,
            notes="Bundle discount if combined with table SKU.",
        )

        sample = db.query(Sample).filter(Sample.sample_request_number == MARKER_SAMPLE_NUMBER).first()
        if not sample:
            sample = Sample(
                sample_request_number=MARKER_SAMPLE_NUMBER,
                company_id=company.id,
                contact_id=contact.id,
                lead_id=lead.id,
                rfq_id=rfq.id,
                product_id=prod_frame.id,
                manufacturing_partner_id=partner_lift.id,
                sample_status=SampleStatus.delivered.value,
                courier="DemoParcel",
                tracking_number="DEMO-JEFF-TRACK-7788",
                shipped_date=today - timedelta(days=4),
                delivered_date=today - timedelta(days=1),
                sample_cost=Decimal("120"),
                shipping_cost=Decimal("64.50"),
                customer_feedback="Demo feedback: stability and cable management meet lab checklist.",
                follow_up_due_date=today + timedelta(days=5),
                notes="Delivered for lab evaluation.",
                created_by_id=uid,
                updated_by_id=uid,
            )
            db.add(sample)
            db.commit()
            db.refresh(sample)
        else:
            sample.sample_status = SampleStatus.delivered.value
            sample.shipping_cost = Decimal("64.50")
            sample.customer_feedback = sample.customer_feedback or "Demo feedback: stability and cable management meet lab checklist."
            sample.tracking_number = sample.tracking_number or "DEMO-JEFF-TRACK-7788"
            sample.updated_by_id = uid
            db.commit()

        order = db.query(Order).filter(Order.order_number == MARKER_ORDER_NUMBER).first()
        if not order:
            order = Order(
                order_number=MARKER_ORDER_NUMBER,
                company_id=company.id,
                contact_id=contact.id,
                lead_id=lead.id,
                rfq_id=rfq.id,
                sample_id=sample.id,
                manufacturing_partner_id=partner_lift.id,
                order_date=today - timedelta(days=5),
                target_delivery_date=today + timedelta(days=60),
                total_amount=Decimal("12000.00"),
                currency="USD",
                production_status="Production",
                shipping_status="Booking",
                risk_level="medium",
                notes="Pilot PO tied to Jefferson demo RFQ.",
                created_by_id=uid,
                updated_by_id=uid,
            )
            db.add(order)
            db.commit()
            db.refresh(order)
        else:
            order.sample_id = sample.id
            order.rfq_id = rfq.id
            order.updated_by_id = uid
            db.commit()

        if not db.query(OrderItem).filter(OrderItem.order_id == order.id, OrderItem.product_id == prod_frame.id).first():
            db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=prod_frame.id,
                    quantity=40,
                    unit_price=Decimal("300.00"),
                    created_by_id=uid,
                    updated_by_id=uid,
                )
            )
            db.commit()

        def ensure_milestone(name: str, planned: date, actual: date | None, st: str, delay_days: int | None, note: str | None) -> None:
            m = db.query(ProductionMilestone).filter(ProductionMilestone.order_id == order.id, ProductionMilestone.milestone_name == name).first()
            if m:
                m.planned_date = planned
                m.actual_date = actual
                m.status = st
                m.delay_days = delay_days
                m.notes = note
                m.updated_by_id = uid
            else:
                db.add(
                    ProductionMilestone(
                        order_id=order.id,
                        milestone_name=name,
                        planned_date=planned,
                        actual_date=actual,
                        status=st,
                        delay_days=delay_days,
                        notes=note,
                        created_by_id=uid,
                        updated_by_id=uid,
                    )
                )
            db.commit()

        ensure_milestone(
            "Order Confirmed",
            today - timedelta(days=6),
            today - timedelta(days=6),
            "completed",
            0,
            None,
        )
        ensure_milestone(
            "Material Preparation",
            today - timedelta(days=3),
            None,
            "delayed",
            4,
            "Mill batch slipped — neutral supplier capacity constraint.",
        )

        ship = (
            db.query(ShippingRecord)
            .filter(ShippingRecord.order_id == order.id, ShippingRecord.origin_port == "Yantian")
            .first()
        )
        if not ship:
            db.add(
                ShippingRecord(
                    order_id=order.id,
                    origin_port="Yantian",
                    destination_port="Long Beach",
                    freight_forwarder="Demo Global Forwarding",
                    booking_date=today,
                    etd=today + timedelta(days=12),
                    eta=today + timedelta(days=35),
                    delivery_status="Booking",
                    created_by_id=uid,
                    updated_by_id=uid,
                )
            )
            db.commit()

        due_end_today = now.replace(hour=23, minute=0, second=0, microsecond=0)
        _ensure_task(
            db,
            uid=uid,
            title="Demo Jefferson: follow up on frame feedback",
            due_at=due_end_today,
            priority="high",
            related_object_type="lead",
            related_object_id=lead.id,
        )
        _ensure_task(
            db,
            uid=uid,
            title="Demo Jefferson: overdue pricing check",
            due_at=now - timedelta(days=4),
            priority="medium",
            related_object_type="rfq",
            related_object_id=rfq.id,
        )
        _ensure_task(
            db,
            uid=uid,
            title="Demo Jefferson: schedule education table review",
            due_at=now + timedelta(days=3),
            priority="low",
            related_object_type="lead",
            related_object_id=lead.id,
        )

        def ensure_interaction(obj_type: str, obj_id: uuid.UUID, itype: str, channel: str, subj: str, summary: str) -> None:
            row = (
                db.query(Interaction)
                .filter(
                    Interaction.related_object_type == obj_type,
                    Interaction.related_object_id == obj_id,
                    Interaction.subject == subj,
                )
                .first()
            )
            if row:
                row.summary = summary
                row.updated_by_id = uid
            else:
                db.add(
                    Interaction(
                        related_object_type=obj_type,
                        related_object_id=obj_id,
                        interaction_type=itype,
                        channel=channel,
                        subject=subj,
                        summary=summary,
                        direction="outbound",
                        created_by_id=uid,
                        updated_by_id=uid,
                    )
                )
            db.commit()

        ensure_interaction(
            "lead",
            lead.id,
            "LinkedIn Note",
            "LinkedIn",
            "Connection note — adjustable frame pilot",
            "Sent connection request referencing 660 lb frame evaluation.",
        )
        ensure_interaction(
            "lead",
            lead.id,
            "Email",
            "Email",
            "RFQ scope confirmation",
            "Confirmed 20-unit evaluation timeline and cert expectations.",
        )
        ensure_interaction(
            "sample",
            sample.id,
            "Sample Discussion",
            "Email",
            "Sample tracking shared with customer",
            "Shared DEMO-JEFF-TRACK-7788 and expected lab date.",
        )

        _ensure_ai_demo_outputs(db, uid=uid, rfq_id=rfq.id, lead_id=lead.id)

        note_body = "Internal: prioritize stability test photos with Tamara's team."
        note = db.query(Note).filter(Note.object_type == "rfq", Note.object_id == rfq.id, Note.body == note_body).first()
        if not note:
            db.add(Note(object_type="rfq", object_id=rfq.id, body=note_body, author_id=uid, created_by_id=uid, updated_by_id=uid))
            db.commit()

        tag = db.query(Tag).filter(Tag.name == "jefferson-demo").first()
        if not tag:
            tag = Tag(name="jefferson-demo", color="#64748b", created_by_id=uid, updated_by_id=uid)
            db.add(tag)
            db.commit()
            db.refresh(tag)
        if not db.query(ObjectTag).filter(ObjectTag.object_type == "lead", ObjectTag.object_id == lead.id, ObjectTag.tag_id == tag.id).first():
            db.add(ObjectTag(object_type="lead", object_id=lead.id, tag_id=tag.id, created_by_id=uid, updated_by_id=uid))
            db.commit()

        print("Jefferson Group demo flow ensured (idempotent).")
        print(f"  Company: {company.company_name} ({company.id})")
        print(f"  RFQ: {rfq.rfq_number} ({rfq.id})")
        print(f"  Sample: {sample.sample_request_number} ({sample.id})")
        print(f"  Order: {order.order_number} ({order.id})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
