"""Seed the D8.3 business demo scenario into the local demo database.

This is idempotent and intended for local/demo data only. It does not send email,
notify customers or suppliers, call carrier APIs, deploy, or mark staging validated.
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import get_session_factory
from app.models import (
    Company,
    Contact,
    CustomerOrder,
    FeedbackTicket,
    ManufacturingPartner,
    MarketIntelligenceItem,
    OrderConfirmation,
    OrderLineItem,
    OrderPartnerSplit,
    OrderProductionMilestone,
    Quote,
    QuoteLineItem,
    ShipmentPlan,
    SupplierConfirmation,
    User,
)


QUOTE_NUMBER = "Q-D83-DEMO-001"
ORDER_NUMBER = "O-D83-DEMO-001"


def _admin(db) -> User:
    user = db.query(User).filter(User.email == "admin@example.com").first()
    if not user:
        raise RuntimeError("admin@example.com not found; run the base seed first")
    return user


def _ensure_company(db, user: User) -> tuple[Company, Contact]:
    company = db.query(Company).filter(Company.company_name == "D8.3 Multi-Partner Demo Account").first()
    if not company:
        company = Company(
            company_name="D8.3 Multi-Partner Demo Account",
            website="https://demo-d83.example",
            company_type="Office and Education Furniture Dealer",
            industry="Furniture distribution",
            city="Chicago",
            state="IL",
            country="United States",
            product_interest_tags="adjustable desk frames; lifting columns; education furniture; project furniture",
            source="D8.3 demo seed",
            status="active",
            priority="high",
            notes="Local demo account for business walkthrough.",
            created_by_id=user.id,
            updated_by_id=user.id,
        )
        db.add(company)
        db.commit()
        db.refresh(company)

    contact = db.query(Contact).filter(Contact.email == "d83.demo@example.com").first()
    if not contact:
        contact = Contact(
            first_name="Dana",
            last_name="Demo",
            title="Operations Buyer",
            company_id=company.id,
            email="d83.demo@example.com",
            contact_type="Buyer",
            decision_maker_level="Influencer",
            communication_preference="email",
            status="active",
            notes="Local demo contact.",
            created_by_id=user.id,
            updated_by_id=user.id,
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
    return company, contact


def _ensure_partner(db, user: User, *, code: str, name: str, partner_type: str, category: str) -> ManufacturingPartner:
    partner = db.query(ManufacturingPartner).filter(ManufacturingPartner.partner_code == code).first()
    if not partner:
        partner = db.query(ManufacturingPartner).filter(ManufacturingPartner.partner_name == name).first()
    if not partner:
        partner = ManufacturingPartner(
            partner_code=code,
            partner_name=name,
            brand_name=code,
            partner_type=partner_type,
            country="China",
            city="Demo City",
            main_product_categories=category,
            manufacturing_capabilities=category,
            certifications="Demo customer-safe certifications metadata on file.",
            project_fit_rating=4,
            risk_level="low",
            preferred_product_categories=category,
            notes="D8.3 demo partner. Peer manufacturing partner row; not a platform default.",
            created_by_id=user.id,
            updated_by_id=user.id,
        )
        db.add(partner)
        db.commit()
        db.refresh(partner)
    else:
        partner.partner_code = partner.partner_code or code
        partner.partner_name = name
        partner.brand_name = code
        partner.partner_type = partner_type
        partner.main_product_categories = category
        partner.manufacturing_capabilities = category
        partner.updated_by_id = user.id
        db.commit()
    return partner


def _ensure_quote(db, user: User, company: Company, contact: Contact, hosun: ManufacturingPartner, jooboo: ManufacturingPartner) -> Quote:
    today = date.today()
    quote = db.query(Quote).filter(Quote.quote_number == QUOTE_NUMBER).first()
    if not quote:
        quote = Quote(
            quote_number=QUOTE_NUMBER,
            company_id=company.id,
            contact_id=contact.id,
            sales_owner_id=user.id,
            quote_date=today - timedelta(days=12),
            valid_until=today + timedelta(days=18),
            status="converted_to_order",
            currency="USD",
            default_incoterm="FOB",
            payment_terms="Demo terms only.",
            shipping_terms="Planned ocean freight; dates are not guarantees.",
            bill_to_name="Dana Demo",
            bill_to_company=company.company_name,
            ship_to_name="Dana Demo",
            ship_to_company=company.company_name,
            customer_notes="Demo multi-partner quote for lifting systems plus education furniture.",
            subtotal=Decimal("19680.00"),
            adjustment_total=Decimal("0.00"),
            tax_total=Decimal("0.00"),
            grand_total=Decimal("19680.00"),
            manual_sent=True,
            sent_at=datetime.now(timezone.utc) - timedelta(days=10),
            sent_by_id=user.id,
            send_channel="demo",
            created_by_id=user.id,
            updated_by_id=user.id,
        )
        db.add(quote)
        db.commit()
        db.refresh(quote)
    else:
        quote.status = "converted_to_order"
        quote.subtotal = Decimal("19680.00")
        quote.grand_total = Decimal("19680.00")
        quote.updated_by_id = user.id
        db.commit()

    specs = [
        (
            1,
            hosun,
            "HOSUN-HDLIFT-001",
            "HOSUN heavy-duty lifting column system",
            "lifting columns",
            12,
            Decimal("680.00"),
        ),
        (
            2,
            jooboo,
            "JOOBOO-EDU-TABLE-001",
            "JOOBOO collaborative education table set",
            "education furniture",
            24,
            Decimal("480.00"),
        ),
    ]
    for line_number, partner, sku, name, category, qty, price in specs:
        line = db.query(QuoteLineItem).filter(QuoteLineItem.quote_id == quote.id, QuoteLineItem.line_number == line_number).first()
        total = price * qty
        if not line:
            line = QuoteLineItem(
                quote_id=quote.id,
                line_number=line_number,
                partner_id=partner.id,
                internal_sku=sku,
                product_name=name,
                product_category=category,
                description_customer=f"Customer-visible demo line for {category}.",
                quantity=qty,
                unit_price=price,
                final_unit_price=price,
                total_price=total,
                currency="USD",
                incoterm="FOB",
                pricing_source="demo",
                customer_visible=True,
                requires_review=False,
                created_by_id=user.id,
                updated_by_id=user.id,
            )
            db.add(line)
        else:
            line.partner_id = partner.id
            line.internal_sku = sku
            line.product_name = name
            line.product_category = category
            line.quantity = qty
            line.unit_price = price
            line.final_unit_price = price
            line.total_price = total
            line.customer_visible = True
            line.updated_by_id = user.id
    db.commit()
    return quote


def _ensure_order(db, user: User, company: Company, contact: Contact, quote: Quote) -> CustomerOrder:
    today = date.today()
    now = datetime.now(timezone.utc)
    order = db.query(CustomerOrder).filter(CustomerOrder.order_number == ORDER_NUMBER).first()
    if not order:
        order = CustomerOrder(
            order_number=ORDER_NUMBER,
            source_quote_id=quote.id,
            company_id=company.id,
            contact_id=contact.id,
            status="confirmed",
            order_date=today - timedelta(days=8),
            customer_confirmed_at=now - timedelta(days=7),
            customer_confirmation_method="purchase_order",
            customer_confirmation_note="Demo customer confirmation for walkthrough.",
            bill_to_name="Dana Demo",
            bill_to_company=company.company_name,
            ship_to_name="Dana Demo",
            ship_to_company=company.company_name,
            currency="USD",
            subtotal=quote.subtotal,
            adjustment_total=Decimal("0.00"),
            tax_total=Decimal("0.00"),
            grand_total=quote.grand_total,
            payment_terms="Demo terms only.",
            shipping_terms="Planned ocean freight; dates are not guarantees.",
            customer_notes="Customer-visible demo order.",
            internal_notes="D8.3 demo seed only.",
            created_by_id=user.id,
        )
        db.add(order)
        db.commit()
        db.refresh(order)
    else:
        order.status = "confirmed"
        order.customer_confirmed_at = order.customer_confirmed_at or now - timedelta(days=7)
        order.subtotal = quote.subtotal
        order.grand_total = quote.grand_total
        db.commit()

    if not db.query(OrderConfirmation).filter(OrderConfirmation.order_id == order.id).first():
        db.add(
            OrderConfirmation(
                order_id=order.id,
                confirmation_type="purchase_order",
                confirmation_strength="strong",
                confirmed_by_name="Dana Demo",
                confirmed_by_email="d83.demo@example.com",
                confirmed_by_company=company.company_name,
                confirmed_at=now - timedelta(days=7),
                source_channel="demo",
                evidence_reference="D8.3 demo PO reference",
                status="active",
                created_by_id=user.id,
            )
        )
        db.commit()
    return order


def _ensure_order_lines_and_splits(db, user: User, order: CustomerOrder, quote: Quote) -> list[OrderPartnerSplit]:
    splits: list[OrderPartnerSplit] = []
    quote_lines = db.query(QuoteLineItem).filter(QuoteLineItem.quote_id == quote.id).order_by(QuoteLineItem.line_number).all()
    for quote_line in quote_lines:
        order_line = (
            db.query(OrderLineItem)
            .filter(OrderLineItem.order_id == order.id, OrderLineItem.source_quote_line_item_id == quote_line.id)
            .first()
        )
        if not order_line:
            order_line = OrderLineItem(
                order_id=order.id,
                source_quote_line_item_id=quote_line.id,
                partner_id=quote_line.partner_id,
                internal_sku=quote_line.internal_sku,
                partner_product_code=quote_line.partner_product_code,
                product_name=quote_line.product_name,
                product_category=quote_line.product_category,
                description_customer=quote_line.description_customer,
                quantity=quote_line.quantity,
                unit_price=quote_line.final_unit_price,
                total_price=quote_line.total_price,
                currency=quote_line.currency,
                incoterm=quote_line.incoterm,
                customer_visible=True,
                supplier_visible=True,
                status="confirmed",
            )
            db.add(order_line)
        else:
            order_line.partner_id = quote_line.partner_id
            order_line.product_name = quote_line.product_name
            order_line.product_category = quote_line.product_category
            order_line.quantity = quote_line.quantity
            order_line.unit_price = quote_line.final_unit_price
            order_line.total_price = quote_line.total_price
            order_line.status = "confirmed"
        db.commit()

        split = (
            db.query(OrderPartnerSplit)
            .filter(OrderPartnerSplit.order_id == order.id, OrderPartnerSplit.partner_id == quote_line.partner_id)
            .first()
        )
        split_number = f"SPLIT-{len(splits) + 1:02d}"
        if not split:
            split = OrderPartnerSplit(
                order_id=order.id,
                partner_id=quote_line.partner_id,
                split_number=split_number,
                split_status="supplier_confirmed",
                supplier_confirmation_status="confirmed",
                supplier_confirmed_at=datetime.now(timezone.utc) - timedelta(days=5),
                expected_production_start=date.today() - timedelta(days=3),
                expected_ready_date=date.today() + timedelta(days=18),
                line_item_count=1,
                subtotal=quote_line.total_price,
                currency=quote_line.currency,
                notes="D8.3 demo split.",
            )
            db.add(split)
            db.commit()
            db.refresh(split)
        else:
            split.split_status = "supplier_confirmed"
            split.supplier_confirmation_status = "confirmed"
            split.line_item_count = 1
            split.subtotal = quote_line.total_price
            split.currency = quote_line.currency
            db.commit()
        splits.append(split)
    return splits


def _ensure_execution_records(db, user: User, order: CustomerOrder, splits: list[OrderPartnerSplit]) -> None:
    today = date.today()
    for index, split in enumerate(splits):
        if not db.query(SupplierConfirmation).filter(SupplierConfirmation.partner_split_id == split.id).first():
            db.add(
                SupplierConfirmation(
                    order_id=order.id,
                    partner_split_id=split.id,
                    partner_id=split.partner_id,
                    confirmation_status="confirmed",
                    confirmed_at=datetime.now(timezone.utc) - timedelta(days=5),
                    confirmed_by_name="Demo partner operations",
                    confirmation_channel="demo",
                    inventory_confirmed=False,
                    certification_confirmed=False,
                    lead_time_confirmed=False,
                    production_capacity_confirmed=True,
                    expected_production_start=today - timedelta(days=3),
                    expected_ready_date=today + timedelta(days=18 + index * 4),
                    supplier_reference=f"D83-SUP-{index + 1}",
                    note="Demo supplier confirmation; does not promise inventory, certification, or lead time.",
                    status="active",
                    created_by_id=user.id,
                )
            )
        milestones = [
            ("supplier_confirmed", "Supplier confirmed", 1, "completed", today - timedelta(days=5), today - timedelta(days=5)),
            ("materials_prepared", "Materials prepared", 2, "in_progress" if index == 0 else "completed", today - timedelta(days=1), None if index == 0 else today - timedelta(days=1)),
            ("ready_to_ship", "Ready to ship", 3, "planned", today + timedelta(days=18 + index * 4), None),
        ]
        for milestone_type, label, sequence, status, planned, actual in milestones:
            milestone = (
                db.query(OrderProductionMilestone)
                .filter(OrderProductionMilestone.partner_split_id == split.id, OrderProductionMilestone.milestone_type == milestone_type)
                .first()
            )
            if not milestone:
                db.add(
                    OrderProductionMilestone(
                        order_id=order.id,
                        partner_split_id=split.id,
                        partner_id=split.partner_id,
                        milestone_type=milestone_type,
                        milestone_label=label,
                        sequence=sequence,
                        status=status,
                        planned_date=planned,
                        actual_date=actual,
                        responsible_party="Partner operations",
                        source="manual",
                        notes="D8.3 demo milestone.",
                        created_by_id=user.id,
                    )
                )
            else:
                milestone.status = status
                milestone.planned_date = planned
                milestone.actual_date = actual
        shipment = db.query(ShipmentPlan).filter(ShipmentPlan.order_id == order.id, ShipmentPlan.partner_split_id == split.id).first()
        if not shipment:
            db.add(
                ShipmentPlan(
                    order_id=order.id,
                    partner_split_id=split.id,
                    shipment_method="sea",
                    incoterm="FOB",
                    origin="Shanghai" if index else "Shenzhen",
                    destination="Los Angeles",
                    estimated_ship_date=today + timedelta(days=22 + index * 4),
                    estimated_arrival_date=today + timedelta(days=52 + index * 4),
                    tracking_number="D83-DEMO-TRACK" if index == 1 else None,
                    status="planned" if index == 0 else "shipped",
                    notes="D8.3 demo shipment plan; no carrier API called.",
                    created_by_id=user.id,
                )
            )
        else:
            shipment.status = "planned" if index == 0 else "shipped"
            shipment.estimated_ship_date = today + timedelta(days=22 + index * 4)
            shipment.estimated_arrival_date = today + timedelta(days=52 + index * 4)
            shipment.tracking_number = "D83-DEMO-TRACK" if index == 1 else None
    db.commit()


def _ensure_feedback_and_market(db, order: CustomerOrder, company: Company) -> None:
    tickets = [
        ("FB-D83-HOSUN", "shipment", "Confirm lifting-system ETD", "Customer asked when heavy-duty lifting columns leave port.", "high"),
        ("FB-D83-JOOBOO", "product_quality", "Education furniture finish sample", "Customer asked for finish durability notes for classroom tables.", "normal"),
    ]
    for number, feedback_type, subject, message, priority in tickets:
        ticket = db.query(FeedbackTicket).filter(FeedbackTicket.ticket_number == number).first()
        if not ticket:
            db.add(
                FeedbackTicket(
                    ticket_number=number,
                    source="customer_portal",
                    order_id=order.id,
                    company_id=company.id,
                    feedback_type=feedback_type,
                    subject=subject,
                    message=message,
                    status="new",
                    priority=priority,
                    customer_name="Dana Demo",
                    customer_email="d83.demo@example.com",
                )
            )
        else:
            ticket.order_id = order.id
            ticket.company_id = company.id
            ticket.status = "new"
            ticket.priority = priority
            ticket.response_summary = None

    market_items = [
        (
            "D8.3 lifting systems watchlist",
            "lifting columns",
            "dealer channel",
            "Heavy-duty lifting columns and desk legs need ETD visibility before broader outreach.",
            "lifting columns, desk legs, HOSUN",
            "high",
        ),
        (
            "D8.3 education furniture watchlist",
            "education furniture",
            "education projects",
            "Classroom table finish questions indicate JOOBOO education line needs clearer customer resources.",
            "education furniture, project furniture, JOOBOO",
            "medium",
        ),
    ]
    for title, category, segment, content, tags, importance in market_items:
        item = db.query(MarketIntelligenceItem).filter(MarketIntelligenceItem.title == title).first()
        if not item:
            db.add(
                MarketIntelligenceItem(
                    title=title,
                    source_type="demo_signal",
                    related_company_id=company.id,
                    related_product_category=category,
                    market_segment=segment,
                    content=content,
                    tags=tags,
                    importance=importance,
                    ai_summary="D8.3 demo signal for human review only.",
                    ai_opportunity_analysis="Use as walkthrough evidence; do not auto-execute.",
                )
            )
        else:
            item.related_company_id = company.id
            item.related_product_category = category
            item.market_segment = segment
            item.content = content
            item.tags = tags
            item.importance = importance
    db.commit()


def main() -> int:
    db = get_session_factory()()
    try:
        user = _admin(db)
        company, contact = _ensure_company(db, user)
        hosun = _ensure_partner(
            db,
            user,
            code="HOSUN",
            name="HOSUN Lifting Systems (D8.3 demo)",
            partner_type="Lifting System Manufacturer",
            category="desk frames; desk legs; lifting columns; heavy-duty lifting systems",
        )
        jooboo = _ensure_partner(
            db,
            user,
            code="JOOBOO",
            name="JOOBOO Education Furniture (D8.3 demo)",
            partner_type="Education Furniture Manufacturer",
            category="education furniture; project furniture; classroom tables",
        )
        quote = _ensure_quote(db, user, company, contact, hosun, jooboo)
        order = _ensure_order(db, user, company, contact, quote)
        splits = _ensure_order_lines_and_splits(db, user, order, quote)
        _ensure_execution_records(db, user, order, splits)
        _ensure_feedback_and_market(db, order, company)
        print("D8.3 business demo seed complete")
        print(f"quote={QUOTE_NUMBER}")
        print(f"order={ORDER_NUMBER}")
        print("safety=no notifications, no carrier APIs, no staging validation")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
