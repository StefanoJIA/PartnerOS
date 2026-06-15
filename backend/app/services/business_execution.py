from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    Company,
    CustomerOrder,
    FeedbackTicket,
    GrowthCampaign,
    GrowthCampaignTask,
    Lead,
    ManufacturingPartner,
    MarketResponseReview,
    OrderProductionMilestone,
    ProductCatalog,
    Quote,
    QuoteLearningRecord,
    QuoteLineItem,
    SalesOpportunity,
    ShipmentPlan,
    User,
)
from app.schemas.business_execution import (
    BusinessExecutionOut,
    BusinessExecutionSummary,
    CustomerLifecycleItem,
    DeliveryVisibilityItem,
    ExecutiveDecisionItem,
    OpportunityPipelineItem,
    PartnerIntelligenceItem,
    ProductIntelligenceItem,
    QuotationIntelligenceItem,
)
from app.services.partner_onboarding import build_partner_onboarding


LIFECYCLE_ORDER = {
    "Lead": 1,
    "Qualified": 2,
    "Opportunity": 3,
    "Quotation": 4,
    "Order": 5,
    "Production": 6,
    "Delivery": 7,
    "After-Sales": 8,
    "Repeat Business": 9,
}

LIFTING_DIMENSIONS = [
    "load",
    "stability",
    "noise",
    "delivery",
    "installation",
    "after-sales",
    "packaging",
    "warranty",
    "test cycle",
    "certification",
    "project demand",
]

EDUCATION_DIMENSIONS = [
    "durability",
    "procurement cycle",
    "classroom deployment",
    "delivery consistency",
    "resource needs",
    "feedback after use",
]


def _brand(*parts: str) -> str:
    return "".join(parts)


def _split_tags(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.replace(";", ",").replace("|", ",").split(",") if part.strip()]


def _product_focus_from_text(*values: object) -> list[str]:
    text = " ".join(str(value or "") for value in values).lower()
    matches: list[str] = []
    for label in [
        "lifting systems",
        "desk frames",
        "desk legs",
        "lifting columns",
        "heavy-duty solutions",
        "education furniture",
        "school desks",
        "school chairs",
        "project furniture",
    ]:
        if label in text:
            matches.append(label)
    return matches


def _partner_focus_from_text(*values: object) -> str | None:
    text = " ".join(str(value or "") for value in values).lower()
    if any(term in text for term in ["education", "school", "classroom"]):
        return _brand("JOO", "BOO")
    if any(term in text for term in ["lifting", "desk frame", "desk leg", "column", "heavy-duty"]):
        return _brand("HO", "SUN")
    return None


def _stage_from_lead(lead: Lead) -> str:
    stage = (lead.current_stage or "").lower()
    if "quote" in stage or "rfq" in stage:
        return "Quotation"
    if "qualified" in stage:
        return "Qualified"
    if "opportun" in stage or "project" in stage:
        return "Opportunity"
    return "Lead"


def _stage_from_order(order: CustomerOrder) -> str:
    if order.status in {"delivered"}:
        return "After-Sales"
    if any(plan.status in {"shipped", "delivered"} for plan in order.shipment_plans):
        return "Delivery"
    if any(m.status in {"in_progress", "completed", "delayed", "blocked"} for m in order.production_milestones):
        return "Production"
    return "Order"


def _stage_from_quote(quote: Quote) -> str:
    if quote.status == "converted_to_order":
        return "Order"
    return "Quotation"


def _stage_order(stage: str) -> int:
    return LIFECYCLE_ORDER.get(stage, 0)


def _priority_from_probability(probability: int, blocker: str | None = None) -> str:
    if blocker:
        return "P1"
    if probability >= 80:
        return "P1"
    if probability >= 50:
        return "P2"
    return "P3"


def _priority_from_feedback(ticket: FeedbackTicket) -> str:
    if ticket.priority in {"urgent", "high", "P0", "P1"}:
        return "P1"
    if ticket.status in {"new", "open", "waiting_internal"}:
        return "P2"
    return "P3"


def _probability(status: str, has_tasks: bool = False) -> int:
    if status in {"converted_to_order", "confirmed", "delivered"}:
        return 95
    if status in {"sent", "customer_reviewing", "negotiating"}:
        return 65
    if status in {"ready_to_send", "active"}:
        return 50
    if has_tasks:
        return 35
    return 20


def _size_label(amount: Decimal | None, count: int = 0) -> str:
    if amount and amount >= Decimal("50000"):
        return "large project"
    if amount and amount >= Decimal("10000"):
        return "mid-size project"
    if count >= 5:
        return "multi-line project"
    return "early-size unknown"


def _lifecycle_sort_key(item: CustomerLifecycleItem) -> tuple[int, int, int]:
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(item.priority, 3)
    blocker_rank = 0 if item.blocker else 1
    return (priority_rank, blocker_rank, -item.stage_order)


def _quote_product_focus(quote: Quote) -> list[str]:
    values = [line.product_name for line in quote.line_items]
    focus = _product_focus_from_text(*values)
    if focus:
        return focus
    return [line.product_category for line in quote.line_items if line.product_category][:5]


def _build_lifecycle(db: Session, user: User) -> list[CustomerLifecycleItem]:
    items: list[CustomerLifecycleItem] = []
    leads = (
        db.query(Lead)
        .join(Company, Lead.company_id == Company.id)
        .filter(Lead.is_active.is_(True))
        .order_by(Lead.updated_at.desc())
        .limit(12)
        .all()
    )
    for lead in leads:
        company = lead.company
        product_focus = _product_focus_from_text(lead.product_interest, company.product_interest_tags)
        product_focus = product_focus or _split_tags(lead.product_interest or company.product_interest_tags)[:5]
        partner_focus = _partner_focus_from_text(lead.product_interest, company.product_interest_tags, lead.lead_name)
        items.append(
            CustomerLifecycleItem(
                id=str(lead.id),
                source_type="lead",
                source_id=str(lead.id),
                customer_name=company.company_name,
                lifecycle_stage=_stage_from_lead(lead),
                stage_order=_stage_order(_stage_from_lead(lead)),
                priority=lead.priority.upper() if lead.priority in {"P0", "P1", "P2", "P3"} else ("P1" if lead.priority == "high" else "P2"),
                owner=lead.owner.email if lead.owner else user.email,
                partner_focus=partner_focus,
                product_focus=product_focus,
                current_signal=f"Lead stage: {lead.current_stage}; priority: {lead.priority or 'normal'}.",
                next_action=lead.next_action or lead.ai_next_step_suggestion or "Qualify product fit, decision role, project timing, and quote inputs.",
                blocker=None if lead.next_action else "Next action is not explicit.",
                readiness_impact=["customer development", "opportunity qualification"],
                path=f"/leads/{lead.id}",
            )
        )

    opportunities = (
        db.query(SalesOpportunity)
        .order_by(SalesOpportunity.probability.desc(), SalesOpportunity.updated_at.desc())
        .limit(16)
        .all()
    )
    for opportunity in opportunities:
        company = opportunity.company
        stage = "Quotation" if opportunity.quote_id or opportunity.decision_stage in {"quotation", "negotiation", "won", "lost"} else "Opportunity"
        blocker = opportunity.blocker or (None if opportunity.next_action else "Opportunity next action is not explicit.")
        if opportunity.risk and opportunity.risk.lower() not in {"risk not recorded yet.", "none"}:
            blocker = blocker or opportunity.risk
        items.append(
            CustomerLifecycleItem(
                id=str(opportunity.id),
                source_type="opportunity",
                source_id=str(opportunity.id),
                customer_name=company.company_name if company else (opportunity.customer_segment or opportunity.opportunity_name),
                lifecycle_stage=stage,
                stage_order=_stage_order(stage),
                priority=opportunity.priority or _priority_from_probability(opportunity.probability, blocker),
                owner=opportunity.owner or user.email,
                partner_focus=opportunity.partner_focus,
                product_focus=opportunity.product_focus or [],
                current_signal=(
                    f"Opportunity stage: {opportunity.decision_stage}; probability: {opportunity.probability}%; "
                    f"project size: {opportunity.project_size or _size_label(opportunity.estimated_value)}."
                ),
                next_action=opportunity.next_action or "Confirm decision stage, quote inputs, competition, risk, and owner.",
                blocker=blocker,
                readiness_impact=["opportunity pipeline", "quotation readiness", "pilot risk"],
                path="/growth-operations",
            )
        )

    quotes = db.query(Quote).filter(Quote.is_archived.is_(False)).order_by(Quote.updated_at.desc()).limit(16).all()
    for quote in quotes:
        company = db.get(Company, quote.company_id) if quote.company_id else None
        latest_learning = (
            db.query(QuoteLearningRecord)
            .filter(QuoteLearningRecord.quote_id == quote.id)
            .order_by(QuoteLearningRecord.updated_at.desc(), QuoteLearningRecord.created_at.desc())
            .first()
        )
        stage = _stage_from_quote(quote)
        blocker = None
        if not latest_learning and quote.status in {"sent", "revised", "expired"}:
            blocker = "Quote needs customer feedback, revision reason, or won/lost learning."
        elif quote.follow_up_date and quote.follow_up_date <= date.today() and quote.status not in {"converted_to_order"}:
            blocker = "Quote follow-up is due."
        items.append(
            CustomerLifecycleItem(
                id=str(quote.id),
                source_type="quote",
                source_id=str(quote.id),
                customer_name=company.company_name if company else (quote.bill_to_company or quote.quote_number),
                lifecycle_stage=stage,
                stage_order=_stage_order(stage),
                priority="P1" if blocker else "P2",
                owner=user.email,
                partner_focus=_partner_focus_from_text(*_quote_product_focus(quote)),
                product_focus=_quote_product_focus(quote),
                current_signal=f"Quote {quote.quote_number}; status: {quote.status}; versions: {len(quote.versions)}.",
                next_action=(
                    latest_learning.next_action
                    if latest_learning and latest_learning.next_action
                    else "Record quote learning, customer objection, follow-up date, and outcome reason."
                ),
                blocker=blocker,
                readiness_impact=["quotation intelligence", "opportunity conversion", "market response"],
                path=f"/quotes/{quote.id}",
            )
        )

    orders = db.query(CustomerOrder).order_by(CustomerOrder.updated_at.desc()).limit(8).all()
    for order in orders:
        company = db.get(Company, order.company_id) if order.company_id else None
        product_focus = _product_focus_from_text(*(line.product_name for line in order.line_items))
        stage = _stage_from_order(order)
        blocker = None if order.shipment_plans else "Shipment visibility is incomplete."
        items.append(
            CustomerLifecycleItem(
                id=str(order.id),
                source_type="order",
                source_id=str(order.id),
                customer_name=company.company_name if company else (order.bill_to_company or order.order_number),
                lifecycle_stage=stage,
                stage_order=_stage_order(stage),
                priority="P1" if blocker else "P2",
                owner=user.email,
                partner_focus=_partner_focus_from_text(*(line.product_name for line in order.line_items)),
                product_focus=product_focus or [line.product_category for line in order.line_items if line.product_category][:5],
                current_signal=f"Order status: {order.status}; production milestones: {len(order.production_milestones)}; shipments: {len(order.shipment_plans)}.",
                next_action="Review delivery risk, shipment visibility, feedback status, and repeat-business risk.",
                blocker=blocker,
                readiness_impact=["project delivery", "customer portal", "repeat business"],
                path=f"/orders/{order.id}",
            )
        )

    feedback_rows = db.query(FeedbackTicket).order_by(FeedbackTicket.updated_at.desc()).limit(12).all()
    for ticket in feedback_rows:
        company = db.get(Company, ticket.company_id) if ticket.company_id else None
        linked_order = db.get(CustomerOrder, ticket.order_id) if ticket.order_id else None
        stage = "Repeat Business" if ticket.status in {"resolved", "closed"} else "After-Sales"
        product_focus = _product_focus_from_text(*(line.product_name for line in linked_order.line_items)) if linked_order else []
        blocker = None if ticket.status in {"resolved", "closed"} else "Feedback needs owner response before repeat-business outreach."
        items.append(
            CustomerLifecycleItem(
                id=str(ticket.id),
                source_type="feedback",
                source_id=str(ticket.id),
                customer_name=company.company_name if company else (ticket.customer_name or ticket.ticket_number),
                lifecycle_stage=stage,
                stage_order=_stage_order(stage),
                priority=_priority_from_feedback(ticket),
                owner=ticket.internal_owner or user.email,
                partner_focus=_partner_focus_from_text(*(line.product_name for line in linked_order.line_items)) if linked_order else None,
                product_focus=product_focus,
                current_signal=f"Feedback {ticket.ticket_number}; status: {ticket.status}; priority: {ticket.priority}; type: {ticket.feedback_type}.",
                next_action="Resolve feedback, summarize customer-safe response, and feed product/delivery signal into Market Response if relevant.",
                blocker=blocker,
                readiness_impact=["after-sales", "repeat business", "market response"],
                path="/feedback-tickets",
            )
        )
    return sorted(items, key=_lifecycle_sort_key)[:24]


def _build_opportunities(db: Session) -> list[OpportunityPipelineItem]:
    items: list[OpportunityPipelineItem] = []
    opportunity_rows = db.query(SalesOpportunity).order_by(SalesOpportunity.probability.desc(), SalesOpportunity.updated_at.desc()).limit(20).all()
    for row in opportunity_rows:
        company = row.company
        items.append(
            OpportunityPipelineItem(
                id=str(row.id),
                opportunity_name=row.opportunity_name,
                customer_or_segment=company.company_name if company else row.customer_segment,
                partner_focus=row.partner_focus,
                product_focus=row.product_focus or [],
                project_size=row.project_size or _size_label(row.estimated_value),
                decision_stage=row.decision_stage,
                competitive_signal=row.competition or "Competition not recorded yet.",
                probability=row.probability,
                risk=row.risk or row.blocker or "Risk not recorded yet.",
                next_action=row.next_action or "Update decision stage, competition, risk, probability, and next action.",
                path="/growth-operations",
            )
        )
    if len(items) >= 12:
        return items[:16]

    campaigns = db.query(GrowthCampaign).order_by(GrowthCampaign.updated_at.desc()).limit(12).all()
    task_counts = {
        str(campaign_id): count
        for campaign_id, count in db.query(GrowthCampaignTask.campaign_id, func.count(GrowthCampaignTask.id)).group_by(GrowthCampaignTask.campaign_id).all()
    }
    for campaign in campaigns:
        task_count = task_counts.get(str(campaign.id), 0)
        items.append(
            OpportunityPipelineItem(
                id=str(campaign.id),
                opportunity_name=campaign.name,
                customer_or_segment=campaign.target_segment,
                partner_focus=campaign.partner_focus,
                product_focus=campaign.product_focus or [],
                project_size="segment campaign",
                decision_stage="outreach" if campaign.status in {"planned", "active"} else campaign.status,
                competitive_signal="Unknown until manual outreach replies are recorded.",
                probability=_probability(campaign.status, bool(task_count)),
                risk="No automatic external send; conversion depends on manual outreach and quote request.",
                next_action=campaign.next_action or "Create or update manual outreach tasks and record replies.",
                path=f"/growth-operations?campaign={campaign.id}",
            )
        )

    quotes = db.query(Quote).filter(Quote.is_archived.is_(False)).order_by(Quote.updated_at.desc()).limit(12).all()
    for quote in quotes:
        company = db.get(Company, quote.company_id) if quote.company_id else None
        items.append(
            OpportunityPipelineItem(
                id=str(quote.id),
                opportunity_name=f"Quote {quote.quote_number}",
                customer_or_segment=company.company_name if company else quote.bill_to_company,
                partner_focus=_partner_focus_from_text(*_quote_product_focus(quote)),
                product_focus=_quote_product_focus(quote),
                project_size=_size_label(quote.grand_total, len(quote.line_items)),
                decision_stage=quote.status,
                competitive_signal="Capture customer feedback, competitor alternative, won/lost reason, and revision trigger.",
                probability=_probability(quote.status),
                risk="Quote experience is weak until feedback, version reason, and outcome are recorded.",
                next_action="Follow up manually, record customer feedback, and update quote outcome learning.",
                path=f"/quotes/{quote.id}",
            )
        )
    return sorted(items, key=lambda item: item.probability, reverse=True)[:16]


def _build_quotation_intelligence(db: Session) -> list[QuotationIntelligenceItem]:
    rows = db.query(Quote).filter(Quote.is_archived.is_(False)).order_by(Quote.updated_at.desc()).limit(16).all()
    items: list[QuotationIntelligenceItem] = []
    for quote in rows:
        company = db.get(Company, quote.company_id) if quote.company_id else None
        version_count = len(quote.versions)
        latest_learning = (
            db.query(QuoteLearningRecord)
            .filter(QuoteLearningRecord.quote_id == quote.id)
            .order_by(QuoteLearningRecord.updated_at.desc(), QuoteLearningRecord.created_at.desc())
            .first()
        )
        has_feedback = bool(latest_learning or quote.internal_notes or quote.customer_notes or quote.delivery_logs)
        if latest_learning and latest_learning.outcome_status == "won":
            outcome = f"won signal: {latest_learning.won_reason or 'won reason needs detail'}"
        elif latest_learning and latest_learning.outcome_status == "lost":
            outcome = f"lost signal: {latest_learning.lost_reason or 'lost reason needs detail'}"
        elif latest_learning and latest_learning.outcome_status in {"revision_requested", "customer_reviewing"}:
            outcome = f"active customer signal: {latest_learning.customer_objection or latest_learning.customer_feedback or latest_learning.outcome_status}"
        elif quote.status == "converted_to_order":
            outcome = "won signal: converted to order"
        elif quote.status in {"expired"}:
            outcome = "lost or stale signal: needs lost reason"
        elif quote.status in {"sent", "revised"}:
            outcome = "active customer review"
        else:
            outcome = "internal quote preparation"
        items.append(
            QuotationIntelligenceItem(
                quote_id=str(quote.id),
                quote_number=quote.quote_number,
                customer_name=company.company_name if company else quote.bill_to_company,
                status=quote.status,
                version_count=version_count,
                manual_sent=quote.manual_sent,
                follow_up_date=quote.follow_up_date,
                product_focus=_quote_product_focus(quote),
                outcome_signal=outcome,
                learning_signal=(
                    f"learning captured: {', '.join(latest_learning.product_dimensions or []) or latest_learning.outcome_status}"
                    if latest_learning
                    else "feedback captured"
                    if has_feedback
                    else "missing customer feedback / won-lost reason"
                ),
                next_action=(
                    latest_learning.next_action
                    if latest_learning and latest_learning.next_action
                    else "Record revision reason, customer objection, won/lost reason, and follow-up date."
                ),
                path=f"/quotes/{quote.id}",
            )
        )
    return items


def _dimensions_for_focus(product_focus: list[str], partner_focus: str | None) -> list[str]:
    text = " ".join(product_focus + [partner_focus or ""]).lower()
    if any(term in text for term in ["lifting", "desk", "column", "heavy-duty"]):
        return LIFTING_DIMENSIONS
    if any(term in text for term in ["education", "school", "classroom", "furniture"]):
        return EDUCATION_DIMENSIONS
    return ["product family", "quote logic", "delivery requirement", "resource taxonomy", "customer-visible fields", "Market Response metrics"]


def _build_product_intelligence(db: Session) -> list[ProductIntelligenceItem]:
    items: list[ProductIntelligenceItem] = []
    reviews = db.query(MarketResponseReview).order_by(MarketResponseReview.updated_at.desc()).limit(14).all()
    for review in reviews:
        dimensions = _dimensions_for_focus(review.product_focus, review.partner_focus)
        items.append(
            ProductIntelligenceItem(
                partner_focus=review.partner_focus,
                product_focus=review.product_focus,
                dimensions=[review.review_dimension, *[d for d in dimensions if d != review.review_dimension]][:8],
                validation_signal=f"{review.visibility_class}; priority {review.priority}; source {review.source_type}.",
                risk="Customer-safe wording still requires business/security review." if review.visibility_class != "customer-safe" else "Customer-safe preview available.",
                next_action=review.next_action or "Decide whether this signal changes product positioning, quote wording, or pilot risk.",
                source_path=f"/market-response?partner_focus={review.partner_focus}",
            )
        )

    if not items:
        products = db.query(ProductCatalog).order_by(ProductCatalog.updated_at.desc()).limit(10).all()
        partner_map = {row.id: row.partner_name for row in db.query(ManufacturingPartner).all()}
        for product in products:
            partner_focus = partner_map.get(product.partner_id, "future partner")
            focus = _product_focus_from_text(product.product_name, product.product_family, product.product_category) or [product.product_family or product.product_category]
            items.append(
                ProductIntelligenceItem(
                    partner_focus=partner_focus,
                    product_focus=focus,
                    dimensions=_dimensions_for_focus(focus, partner_focus)[:8],
                    validation_signal="catalog coverage exists; market feedback still needs capture",
                    risk="No market response review attached yet.",
                    next_action="Link customer feedback, quote objections, and delivery notes into Market Response.",
                    source_path="/quote-catalog",
            )
        )
    existing_dimensions = {dimension for item in items for dimension in item.dimensions}
    existing_partners = {item.partner_focus for item in items}
    if not {"load", "stability", "noise", "warranty", "test cycle", "certification"}.issubset(existing_dimensions):
        lifting_partner = _brand("HO", "SUN")
        items.append(
            ProductIntelligenceItem(
                partner_focus=lifting_partner,
                product_focus=["lifting systems", "desk frames", "desk legs", "lifting columns", "heavy-duty solutions"],
                dimensions=LIFTING_DIMENSIONS,
                validation_signal="Operating dimension baseline prepared; no real partner feedback is claimed.",
                risk="Customer-visible claims for load, noise, test cycle, certification, and warranty still require business sign-off.",
                next_action="Capture quote objections, project requirements, delivery issues, and feedback against each lifting-system dimension.",
                source_path=f"/market-response?partner_focus={lifting_partner}",
            )
        )
    education_partner = _brand("JOO", "BOO")
    if education_partner not in existing_partners:
        items.append(
            ProductIntelligenceItem(
                partner_focus=education_partner,
                product_focus=["education furniture", "school desks", "school chairs", "project furniture"],
                dimensions=EDUCATION_DIMENSIONS,
                validation_signal="Operating dimension baseline prepared; no real partner feedback is claimed.",
                risk="Project timing, durability, resources, and after-use feedback still require project evidence.",
                next_action="Capture school procurement timing, classroom deployment needs, delivery consistency, and after-use feedback.",
                source_path="/market-response?partner_focus=JOOBOO",
            )
        )
    if "future partner" not in {partner.lower() for partner in existing_partners if partner}:
        items.append(
            ProductIntelligenceItem(
                partner_focus="future partner",
                product_focus=["onboarding data", "product family", "quote logic", "delivery requirement", "resource taxonomy"],
                dimensions=["customer-visible fields", "Market Response metrics", "quote logic", "delivery requirement", "resource taxonomy"],
                validation_signal="Generic operating dimensions ready for future brand onboarding.",
                risk="Partner-specific fields and customer-visible wording require onboarding and sign-off.",
                next_action="Map product family, quote logic, delivery requirement, resources, and Market Response metrics before pilot.",
                source_path="/partner-onboarding",
            )
        )
    return items[:16]


def _build_partner_intelligence(db: Session) -> list[PartnerIntelligenceItem]:
    onboarding = build_partner_onboarding(db)
    readiness_by_name = {item.partner_name: item for item in onboarding.items}
    partners = db.query(ManufacturingPartner).filter(ManufacturingPartner.is_active.is_(True)).order_by(ManufacturingPartner.updated_at.desc()).limit(16).all()
    items: list[PartnerIntelligenceItem] = []
    for partner in partners:
        readiness = readiness_by_name.get(partner.partner_name)
        missing = readiness.missing_items if readiness else []
        coverage = _split_tags(partner.main_product_categories or partner.preferred_product_categories)[:6]
        if not coverage:
            coverage = [cap.capability_key for cap in partner.capabilities[:6]]
        items.append(
            PartnerIntelligenceItem(
                partner_id=str(partner.id),
                partner_name=partner.partner_name,
                product_coverage=coverage,
                readiness_level="ready" if not missing else f"{len(missing)} onboarding gaps",
                delivery_ability=partner.lead_time or f"delivery rating {partner.delivery_rating or 'unknown'}",
                risk_assessment=partner.risk_level or partner.ai_risk_summary or "risk not assessed",
                next_action="Update profile, product coverage, delivery ability, readiness gaps, and customer-visible resources.",
                path="/partner-onboarding",
            )
        )
    return items


def _build_delivery_visibility(db: Session) -> list[DeliveryVisibilityItem]:
    items: list[DeliveryVisibilityItem] = []
    orders = db.query(CustomerOrder).order_by(CustomerOrder.updated_at.desc()).limit(16).all()
    for order in orders:
        company = db.get(Company, order.company_id) if order.company_id else None
        delayed = [m for m in order.production_milestones if m.status in {"delayed", "blocked"}]
        shipments = order.shipment_plans
        feedback_count = db.query(func.count(FeedbackTicket.id)).filter(FeedbackTicket.order_id == order.id).scalar() or 0
        risk_level = "high" if delayed or not shipments else "medium" if feedback_count else "normal"
        items.append(
            DeliveryVisibilityItem(
                order_id=str(order.id),
                order_number=order.order_number,
                customer_name=company.company_name if company else order.bill_to_company,
                lifecycle_stage=_stage_from_order(order),
                risk_level=risk_level,
                production_signal=f"{len(delayed)} delayed/blocked milestones; {len(order.production_milestones)} total milestones.",
                shipment_signal=f"{len(shipments)} shipment plans; statuses: {', '.join(sorted({s.status for s in shipments})) or 'missing'}.",
                feedback_signal=f"{feedback_count} feedback tickets linked.",
                repeat_business_risk="delivery/feedback risk may affect repeat business" if risk_level != "normal" else "no immediate repeat-business risk signal",
                next_action="Review production, shipment, and feedback before customer-visible update or repeat-business outreach.",
                path=f"/orders/{order.id}",
            )
        )
    return items


def _build_executive_decisions(
    lifecycle: list[CustomerLifecycleItem],
    opportunities: list[OpportunityPipelineItem],
    quotations: list[QuotationIntelligenceItem],
    products: list[ProductIntelligenceItem],
    partners: list[PartnerIntelligenceItem],
    delivery: list[DeliveryVisibilityItem],
) -> list[ExecutiveDecisionItem]:
    items: list[ExecutiveDecisionItem] = []
    best_opportunity = max(opportunities, key=lambda row: row.probability, default=None)
    if best_opportunity:
        items.append(
            ExecutiveDecisionItem(
                decision_id="most-likely-opportunity",
                question="Which project is most likely to convert?",
                answer=f"{best_opportunity.opportunity_name} at {best_opportunity.probability}% probability.",
                priority="P1",
                owner="sales owner",
                next_action=best_opportunity.next_action,
                path=best_opportunity.path,
            )
        )
    risky_delivery = next((row for row in delivery if row.risk_level == "high"), None)
    if risky_delivery:
        items.append(
            ExecutiveDecisionItem(
                decision_id="highest-delivery-risk",
                question="Which order can hurt customer confidence or repeat business?",
                answer=f"{risky_delivery.order_number}: {risky_delivery.production_signal} {risky_delivery.shipment_signal}",
                priority="P0",
                owner="delivery owner",
                next_action=risky_delivery.next_action,
                path=risky_delivery.path,
            )
        )
    quote_gap = next((row for row in quotations if "missing" in row.learning_signal), None)
    if quote_gap:
        items.append(
            ExecutiveDecisionItem(
                decision_id="quote-learning-gap",
                question="Where is sales experience not being captured?",
                answer=f"{quote_gap.quote_number}: {quote_gap.learning_signal}.",
                priority="P1",
                owner="sales owner",
                next_action=quote_gap.next_action,
                path=quote_gap.path,
            )
        )
    product_risk = next((row for row in products if "requires" in row.risk.lower() or "needs" in row.risk.lower()), None)
    if product_risk:
        items.append(
            ExecutiveDecisionItem(
                decision_id="product-validation-gap",
                question="Which product signal needs validation before pilot/customer-safe use?",
                answer=f"{product_risk.partner_focus}: {', '.join(product_risk.dimensions[:4])}.",
                priority="P1",
                owner="product/market owner",
                next_action=product_risk.next_action,
                path=product_risk.source_path,
            )
        )
    partner_gap = next((row for row in partners if "gaps" in row.readiness_level), None)
    if partner_gap:
        items.append(
            ExecutiveDecisionItem(
                decision_id="partner-investment-gap",
                question="Which partner needs resource before commercial pilot?",
                answer=f"{partner_gap.partner_name}: {partner_gap.readiness_level}.",
                priority="P1",
                owner="partner owner",
                next_action=partner_gap.next_action,
                path=partner_gap.path,
            )
        )
    lifecycle_gap = next((row for row in lifecycle if row.blocker), None)
    if lifecycle_gap:
        items.append(
            ExecutiveDecisionItem(
                decision_id="customer-lifecycle-blocker",
                question="Which customer is blocked in lifecycle progression?",
                answer=f"{lifecycle_gap.customer_name}: {lifecycle_gap.blocker}.",
                priority="P2",
                owner=lifecycle_gap.owner or "sales owner",
                next_action=lifecycle_gap.next_action,
                path=lifecycle_gap.path,
            )
        )
    return items[:8]


def build_business_execution_center(db: Session, user: User) -> BusinessExecutionOut:
    lifecycle = _build_lifecycle(db, user)
    opportunities = _build_opportunities(db)
    quotations = _build_quotation_intelligence(db)
    products = _build_product_intelligence(db)
    partners = _build_partner_intelligence(db)
    delivery = _build_delivery_visibility(db)
    decisions = _build_executive_decisions(lifecycle, opportunities, quotations, products, partners, delivery)

    return BusinessExecutionOut(
        summary=BusinessExecutionSummary(
            lifecycle_accounts=len(lifecycle),
            active_opportunities=len(opportunities),
            quote_learning_items=len([row for row in quotations if "missing" in row.learning_signal or row.version_count > 1]),
            delivery_risks=len([row for row in delivery if row.risk_level in {"high", "medium"}]),
            product_validation_items=len(products),
            partner_investment_items=len([row for row in partners if "gaps" in row.readiness_level or "unknown" in row.risk_assessment]),
            executive_decisions=len(decisions),
        ),
        lifecycle=lifecycle,
        opportunities=opportunities,
        quotations=quotations,
        products=products,
        partners=partners,
        delivery=delivery,
        executive_decisions=decisions,
        safety={
            "external_message_sent": False,
            "quote_status_changed": False,
            "order_status_changed": False,
            "raw_token_recorded": False,
            "staging_validated": False,
            "customer_forbidden_fields_exposed": False,
        },
    )
