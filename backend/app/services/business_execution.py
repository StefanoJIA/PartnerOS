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
    MarketIntelligenceItem,
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
    CommercialIntelligenceOut,
    CompanyExecutionContext,
    CustomerAccountExecutionItem,
    CustomerLifecycleItem,
    DeliveryVisibilityItem,
    ExecutiveDecisionItem,
    OpportunityPipelineItem,
    PartnerIntelligenceItem,
    ProductIntelligenceItem,
    QuotationIntelligenceItem,
)
from app.services.growth_operations import (
    build_opportunity_execution_context,
    build_opportunity_partner_fit_recommendations,
    derive_opportunity_stage_gate,
)
from app.services.orders.order_fulfillment_intelligence import build_order_fulfillment_intelligence
from app.services.partner_capability_intelligence import build_partner_capability_intelligence
from app.services.partner_onboarding import build_partner_onboarding
from app.services.quotes.quote_learning import build_quote_commercial_intelligence
from app.services.quotes.quote_partner_readiness import build_quote_partner_readiness


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


def _fallback_owner(user: User | None) -> str:
    return user.email if user and user.email else "operator"


def _safety_flags() -> dict[str, bool]:
    return {
        "external_message_sent": False,
        "quote_status_changed": False,
        "order_status_changed": False,
        "raw_token_recorded": False,
        "staging_validated": False,
        "customer_forbidden_fields_exposed": False,
    }


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


def _next_lifecycle_stage(stage: str) -> str | None:
    stages = list(LIFECYCLE_ORDER)
    if stage not in LIFECYCLE_ORDER:
        return "Lead"
    index = stages.index(stage)
    return stages[index + 1] if index + 1 < len(stages) else None


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


def _priority_rank(value: str | None) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(value or "P3", 3)


def _merge_unique(values: list[str], limit: int = 8) -> list[str]:
    merged: list[str] = []
    for value in values:
        if value and value not in merged:
            merged.append(value)
        if len(merged) >= limit:
            break
    return merged


def _account_commercial_health(
    rows: list[CustomerLifecycleItem],
    highest_stage: CustomerLifecycleItem,
    action_source: CustomerLifecycleItem,
    blockers: list[str],
) -> dict[str, object]:
    source_types = {row.source_type for row in rows}
    has_delivery = bool({"order", "feedback"} & source_types)
    has_quote = "quote" in source_types
    has_opportunity = "opportunity" in source_types
    has_feedback = "feedback" in source_types
    stage_order = highest_stage.stage_order
    priority_rank = _priority_rank(action_source.priority)

    score = 45 + min(stage_order * 6, 42) - (len(blockers) * 8) - (priority_rank * 3)
    if has_quote:
        score += 6
    if has_opportunity:
        score += 5
    if has_delivery:
        score += -4 if blockers else 4
    score = max(0, min(100, score))

    if blockers and any("feedback" in blocker.lower() or "repeat" in blocker.lower() for blocker in blockers):
        health = "after_sales_attention"
        business_focus = "客户维护 / 复购"
        next_best_action = "先处理反馈和客户安全回复，再判断是否进入复购或 Market Response 复盘。"
    elif blockers and any("shipment" in blocker.lower() or "delivery" in blocker.lower() or "production" in blocker.lower() for blocker in blockers):
        health = "delivery_risk"
        business_focus = "交付风险"
        next_best_action = "先检查生产、物流和客户可见状态，避免交付风险影响复购。"
    elif blockers:
        health = "blocked"
        business_focus = "推进阻塞"
        next_best_action = action_source.next_action
    elif stage_order >= _stage_order("Quotation") and has_quote:
        health = "conversion_ready"
        business_focus = "报价成交"
        next_best_action = "围绕报价反馈、客户异议、交期和成交条件推进下一次商务动作。"
    elif has_opportunity or stage_order >= _stage_order("Opportunity"):
        health = "pipeline_active"
        business_focus = "项目机会"
        next_best_action = "确认项目规模、决策阶段、竞争情况和报价输入，把机会推进到 quotation。"
    else:
        health = "nurture"
        business_focus = "客户开发"
        next_best_action = "继续确认产品 fit、采购阶段、决策人和下一次人工触达。"

    business_questions = [
        "这个客户当前最接近成交、交付、售后还是复购？",
        "下一步动作是否有明确 owner 和对象入口？",
        "当前阻塞是否需要回流报价学习、Market Response 或 Partner 能力判断？",
    ]
    if has_quote:
        business_questions.append("报价是否已有客户反馈、修订原因、成交/丢单原因？")
    if has_delivery:
        business_questions.append("生产、物流和反馈是否会影响客户复购？")

    return {
        "health": health,
        "score": score,
        "business_focus": business_focus,
        "primary_stage": highest_stage.lifecycle_stage,
        "primary_source_type": action_source.source_type,
        "primary_source_id": action_source.source_id,
        "primary_path": action_source.path,
        "primary_risk": blockers[0] if blockers else None,
        "next_best_action": next_best_action,
        "conversion_signal": "有报价或机会可推进" if (has_quote or has_opportunity) else "仍在客户开发",
        "delivery_signal": "存在订单/反馈，需要交付和复购视角" if has_delivery else "暂无交付对象",
        "repeat_business_signal": "已有售后反馈，需判断复购/市场回流" if has_feedback else "暂无售后反馈",
        "business_questions": business_questions,
        "safety": _safety_flags(),
    }


def _account_stage_progression(
    rows: list[CustomerLifecycleItem],
    highest_stage: CustomerLifecycleItem,
    action_source: CustomerLifecycleItem,
    blockers: list[str],
) -> dict[str, object]:
    source_types = {row.source_type for row in rows}
    current_stage = highest_stage.lifecycle_stage
    next_stage = _next_lifecycle_stage(current_stage)
    missing_inputs: list[str] = []
    readiness_impact: list[str] = []

    if current_stage in {"Lead", "Qualified"} and "opportunity" not in source_types:
        missing_inputs.append("opportunity record")
        readiness_impact.append("opportunity pipeline")
    if current_stage in {"Opportunity"} and "quote" not in source_types:
        missing_inputs.append("linked quotation")
        readiness_impact.append("quotation readiness")
    if current_stage in {"Quotation"} and "order" not in source_types:
        missing_inputs.append("customer decision / order conversion")
        readiness_impact.append("order conversion")
    if current_stage in {"Order"}:
        if not any("production" in impact.lower() for row in rows for impact in row.readiness_impact):
            missing_inputs.append("production plan")
        if not any("customer portal" in impact.lower() for row in rows for impact in row.readiness_impact):
            missing_inputs.append("customer-visible delivery summary")
        readiness_impact.append("project delivery")
    if current_stage in {"Production", "Delivery"} and "feedback" not in source_types:
        missing_inputs.append("after-sales feedback capture")
        readiness_impact.append("repeat business")
    if current_stage == "After-Sales" and blockers:
        missing_inputs.append("customer-safe feedback response")
        readiness_impact.append("repeat business")
        readiness_impact.append("Market Response review")
    if current_stage == "Repeat Business" and not ({"opportunity", "quote"} & source_types):
        missing_inputs.append("repeat opportunity or quote")
        readiness_impact.append("repeat business pipeline")

    missing_inputs.extend(blockers[:3])
    missing_inputs = _merge_unique(missing_inputs, limit=8)
    readiness_impact = _merge_unique(readiness_impact + [impact for row in rows for impact in row.readiness_impact], limit=8)

    if blockers:
        health = "blocked"
        blocks_next_stage = True
        recommended_action = action_source.next_action
    elif missing_inputs:
        health = "needs_input"
        blocks_next_stage = True
        recommended_action = f"补齐 {missing_inputs[0]}，再推进到 {next_stage or '下一轮复购'}。"
    elif next_stage:
        health = "ready_to_advance"
        blocks_next_stage = False
        recommended_action = f"当前账户可准备推进到 {next_stage}，确认 owner、客户输入和下一步入口。"
    else:
        health = "repeat_business_ready"
        blocks_next_stage = False
        recommended_action = "账户已进入复购维护；从反馈、产品验证和新项目机会中选择下一轮商业动作。"

    if current_stage in {"Lead", "Qualified", "Opportunity"}:
        handoff_object = "opportunity"
        recommended_entry_path = "/growth-operations"
    elif current_stage == "Quotation":
        handoff_object = "order"
        recommended_entry_path = action_source.path if action_source.source_type == "quote" else "/quotes"
    elif current_stage in {"Order", "Production", "Delivery"}:
        handoff_object = "delivery"
        recommended_entry_path = action_source.path if action_source.source_type == "order" else "/orders"
    elif current_stage == "After-Sales":
        handoff_object = "feedback_to_market_response"
        recommended_entry_path = "/feedback-tickets"
    else:
        handoff_object = "repeat_business"
        recommended_entry_path = "/growth-operations"

    return {
        "health": health,
        "current_stage": current_stage,
        "next_stage": next_stage,
        "blocks_next_stage": blocks_next_stage,
        "missing_inputs": missing_inputs,
        "recommended_action": recommended_action,
        "handoff_object": handoff_object,
        "recommended_entry_path": recommended_entry_path,
        "readiness_impact": readiness_impact,
        "why_now": (
            f"账户当前最高阶段是 {current_stage}；优先处理 {action_source.source_type}，"
            f"再推进 {next_stage or '复购维护'}。"
        ),
        "safety": _safety_flags(),
    }


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


def _build_account_lifecycle(lifecycle: list[CustomerLifecycleItem]) -> list[CustomerAccountExecutionItem]:
    grouped: dict[str, list[CustomerLifecycleItem]] = {}
    for item in lifecycle:
        key = item.customer_name.strip().lower() or item.id
        grouped.setdefault(key, []).append(item)

    accounts: list[CustomerAccountExecutionItem] = []
    for key, rows in grouped.items():
        highest_stage = max(rows, key=lambda row: row.stage_order)
        highest_priority = min((row.priority for row in rows), key=_priority_rank)
        action_source = sorted(rows, key=_lifecycle_sort_key)[0]
        source_counts: dict[str, int] = {}
        for row in rows:
            source_counts[row.source_type] = source_counts.get(row.source_type, 0) + 1
        blockers = _merge_unique([row.blocker or "" for row in rows if row.blocker], limit=5)
        impacts = _merge_unique([impact for row in rows for impact in row.readiness_impact], limit=6)
        product_focus = _merge_unique([focus for row in rows for focus in row.product_focus], limit=6)
        active_paths = _merge_unique([row.path for row in rows], limit=5)
        accounts.append(
            CustomerAccountExecutionItem(
                account_key=key,
                customer_name=highest_stage.customer_name,
                current_stage=highest_stage.lifecycle_stage,
                stage_order=highest_stage.stage_order,
                priority=highest_priority,
                owner=action_source.owner,
                partner_focus=highest_stage.partner_focus or action_source.partner_focus,
                product_focus=product_focus,
                source_counts=source_counts,
                active_paths=active_paths,
                open_blockers=blockers,
                next_action=action_source.next_action,
                decision_reason=(
                    f"Highest lifecycle stage is {highest_stage.lifecycle_stage}; "
                    f"priority source is {action_source.source_type}; "
                    f"{len(blockers)} blocker(s) currently visible."
                ),
                readiness_impact=impacts,
                commercial_health=_account_commercial_health(rows, highest_stage, action_source, blockers),
                stage_progression=_account_stage_progression(rows, highest_stage, action_source, blockers),
            )
        )
    return sorted(accounts, key=lambda item: (_priority_rank(item.priority), bool(not item.open_blockers), -item.stage_order))[:16]


def build_company_execution_context(db: Session, company_id: str, user: User | None = None) -> CompanyExecutionContext:
    company = db.get(Company, company_id)
    if not company:
        return CompanyExecutionContext(safety=_safety_flags())

    owner = _fallback_owner(user)
    items: list[CustomerLifecycleItem] = []

    leads = (
        db.query(Lead)
        .filter(Lead.company_id == company_id, Lead.is_active.is_(True))
        .order_by(Lead.updated_at.desc())
        .limit(20)
        .all()
    )
    for lead in leads:
        product_focus = _product_focus_from_text(lead.product_interest, company.product_interest_tags)
        product_focus = product_focus or _split_tags(lead.product_interest or company.product_interest_tags)[:5]
        stage = _stage_from_lead(lead)
        items.append(
            CustomerLifecycleItem(
                id=str(lead.id),
                source_type="lead",
                source_id=str(lead.id),
                customer_name=company.company_name,
                lifecycle_stage=stage,
                stage_order=_stage_order(stage),
                priority=lead.priority.upper() if lead.priority in {"P0", "P1", "P2", "P3"} else ("P1" if lead.priority == "high" else "P2"),
                owner=lead.owner.email if lead.owner else owner,
                partner_focus=_partner_focus_from_text(lead.product_interest, company.product_interest_tags, lead.lead_name),
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
        .filter(SalesOpportunity.company_id == company_id)
        .order_by(SalesOpportunity.probability.desc(), SalesOpportunity.updated_at.desc())
        .limit(20)
        .all()
    )
    for opportunity in opportunities:
        stage = "Quotation" if opportunity.quote_id or opportunity.decision_stage in {"quotation", "negotiation", "won", "lost"} else "Opportunity"
        blocker = opportunity.blocker or (None if opportunity.next_action else "Opportunity next action is not explicit.")
        if opportunity.risk and opportunity.risk.lower() not in {"risk not recorded yet.", "none"}:
            blocker = blocker or opportunity.risk
        items.append(
            CustomerLifecycleItem(
                id=str(opportunity.id),
                source_type="opportunity",
                source_id=str(opportunity.id),
                customer_name=company.company_name,
                lifecycle_stage=stage,
                stage_order=_stage_order(stage),
                priority=opportunity.priority or _priority_from_probability(opportunity.probability, blocker),
                owner=opportunity.owner or owner,
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

    quotes = (
        db.query(Quote)
        .filter(Quote.company_id == company_id, Quote.is_archived.is_(False))
        .order_by(Quote.updated_at.desc())
        .limit(20)
        .all()
    )
    for quote in quotes:
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
                customer_name=company.company_name,
                lifecycle_stage=stage,
                stage_order=_stage_order(stage),
                priority="P1" if blocker else "P2",
                owner=owner,
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

    orders = (
        db.query(CustomerOrder)
        .filter(CustomerOrder.company_id == company_id)
        .order_by(CustomerOrder.updated_at.desc())
        .limit(20)
        .all()
    )
    order_ids = [order.id for order in orders]
    for order in orders:
        product_focus = _product_focus_from_text(*(line.product_name for line in order.line_items))
        stage = _stage_from_order(order)
        blocker = None if order.shipment_plans else "Shipment visibility is incomplete."
        items.append(
            CustomerLifecycleItem(
                id=str(order.id),
                source_type="order",
                source_id=str(order.id),
                customer_name=company.company_name,
                lifecycle_stage=stage,
                stage_order=_stage_order(stage),
                priority="P1" if blocker else "P2",
                owner=owner,
                partner_focus=_partner_focus_from_text(*(line.product_name for line in order.line_items)),
                product_focus=product_focus or [line.product_category for line in order.line_items if line.product_category][:5],
                current_signal=f"Order status: {order.status}; production milestones: {len(order.production_milestones)}; shipments: {len(order.shipment_plans)}.",
                next_action="Review delivery risk, shipment visibility, feedback status, and repeat-business risk.",
                blocker=blocker,
                readiness_impact=["project delivery", "customer portal", "repeat business"],
                path=f"/orders/{order.id}",
            )
        )

    feedback_by_id: dict[str, FeedbackTicket] = {}
    for ticket in db.query(FeedbackTicket).filter(FeedbackTicket.company_id == company_id).order_by(FeedbackTicket.updated_at.desc()).limit(20).all():
        feedback_by_id[str(ticket.id)] = ticket
    if order_ids:
        for ticket in (
            db.query(FeedbackTicket)
            .filter(FeedbackTicket.order_id.in_(order_ids))
            .order_by(FeedbackTicket.updated_at.desc())
            .limit(20)
            .all()
        ):
            feedback_by_id[str(ticket.id)] = ticket

    for ticket in feedback_by_id.values():
        linked_order = db.get(CustomerOrder, ticket.order_id) if ticket.order_id else None
        stage = "Repeat Business" if ticket.status in {"resolved", "closed"} else "After-Sales"
        product_focus = _product_focus_from_text(*(line.product_name for line in linked_order.line_items)) if linked_order else []
        blocker = None if ticket.status in {"resolved", "closed"} else "Feedback needs owner response before repeat-business outreach."
        items.append(
            CustomerLifecycleItem(
                id=str(ticket.id),
                source_type="feedback",
                source_id=str(ticket.id),
                customer_name=company.company_name,
                lifecycle_stage=stage,
                stage_order=_stage_order(stage),
                priority=_priority_from_feedback(ticket),
                owner=ticket.internal_owner or owner,
                partner_focus=_partner_focus_from_text(*(line.product_name for line in linked_order.line_items)) if linked_order else None,
                product_focus=product_focus,
                current_signal=f"Feedback {ticket.ticket_number}; status: {ticket.status}; priority: {ticket.priority}; type: {ticket.feedback_type}.",
                next_action="Resolve feedback, summarize customer-safe response, and feed product/delivery signal into Market Response if relevant.",
                blocker=blocker,
                readiness_impact=["after-sales", "repeat business", "market response"],
                path="/feedback-tickets",
            )
        )

    lifecycle = sorted(items, key=_lifecycle_sort_key)[:24]
    account = _build_account_lifecycle(lifecycle)
    return CompanyExecutionContext(
        account=account[0] if account else None,
        lifecycle=lifecycle,
        safety=_safety_flags(),
    )


def _build_opportunities(db: Session) -> list[OpportunityPipelineItem]:
    items: list[OpportunityPipelineItem] = []
    opportunity_rows = db.query(SalesOpportunity).order_by(SalesOpportunity.probability.desc(), SalesOpportunity.updated_at.desc()).limit(20).all()
    for row in opportunity_rows:
        company = row.company
        partner_fit_recommendations = build_opportunity_partner_fit_recommendations(db, row, limit=1)
        partner_fit = partner_fit_recommendations[0].get("partner_fit", {}) if partner_fit_recommendations else {}
        stage_gate = derive_opportunity_stage_gate(row, partner_fit_recommendations)
        execution_context = build_opportunity_execution_context(db, row, partner_fit_recommendations, stage_gate)
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
                stage_gate=stage_gate,
                partner_fit=partner_fit,
                execution_context=execution_context,
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
                stage_gate={
                    "health": "needs_input",
                    "current_stage": "outreach",
                    "current_stage_label": "人工外联",
                    "suggested_next_stage": "discovery",
                    "suggested_next_stage_label": "需求发现",
                    "blocks_next_stage": True,
                    "missing_inputs": ["manual_reply", "qualified_requirement", "quote_request"],
                    "exit_criteria": ["人工发送完成", "记录客户回复", "形成明确项目机会或报价请求"],
                    "dimension_review_needs": campaign.product_focus or ["product family", "quote logic"],
                    "market_response_impacts": [],
                    "quote_learning_impacts": [],
                    "business_questions": [
                        "该 Campaign 是否已产生真实客户回复？",
                        "是否应创建 Sales Opportunity 或报价输入？",
                    ],
                    "next_best_action": campaign.next_action or "Create or update manual outreach tasks and record replies.",
                    "safety": _safety_flags(),
                },
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
        commercial_intelligence = build_quote_commercial_intelligence(quote)
        partner_readiness = build_quote_partner_readiness(quote, db)
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
        next_action = commercial_intelligence.get("next_best_action") or (
            latest_learning.next_action
            if latest_learning and latest_learning.next_action
            else "Record revision reason, customer objection, won/lost reason, and follow-up date."
        )
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
                next_action=next_action,
                path=f"/quotes/{quote.id}",
                commercial_intelligence=commercial_intelligence,
                partner_readiness=partner_readiness,
            )
        )
    return items


def _dimensions_for_focus(product_focus: list[str], partner_focus: str | None) -> list[str]:
    partner_text = (partner_focus or "").lower()
    if _brand("jo", "oboo") in partner_text or "education" in partner_text or "school" in partner_text:
        return EDUCATION_DIMENSIONS
    if _brand("ho", "sun") in partner_text or "lifting" in partner_text:
        return LIFTING_DIMENSIONS
    text = " ".join(product_focus + [partner_focus or ""]).lower()
    if any(term in text for term in ["lifting", "desk", "column", "heavy-duty"]):
        return LIFTING_DIMENSIONS
    if any(term in text for term in ["education", "school", "classroom", "furniture"]):
        return EDUCATION_DIMENSIONS
    return ["product family", "quote logic", "delivery requirement", "resource taxonomy", "customer-visible fields", "Market Response metrics"]


PRODUCT_CONTEXT_SAFETY: dict[str, bool] = {
    "external_message_sent": False,
    "quote_status_changed": False,
    "order_status_changed": False,
    "raw_token_recorded": False,
    "customer_forbidden_fields_exposed": False,
    "cost_exposed": False,
    "margin_exposed": False,
    "supplier_private_notes_exposed": False,
    "staging_validated": False,
}


def _product_terms(partner_focus: str | None, product_focus: list[str], dimensions: list[str]) -> set[str]:
    text = " ".join([partner_focus or "", *product_focus, *dimensions]).lower()
    terms = {item.lower() for item in product_focus if item}
    lifting_brand = _brand("ho", "sun")
    if lifting_brand in text or any(term in text for term in ["lifting", "desk frame", "desk leg", "column", "heavy-duty"]):
        terms.update(
            {
                lifting_brand,
                "lifting",
                "lifting systems",
                "desk frame",
                "desk frames",
                "desk leg",
                "desk legs",
                "lifting column",
                "lifting columns",
                "heavy-duty",
                "load",
                "stability",
                "noise",
                "warranty",
                "certification",
                "test cycle",
            }
        )
    if "jooboo" in text or any(term in text for term in ["education", "school", "classroom", "project furniture"]):
        terms.update(
            {
                "jooboo",
                "education",
                "education furniture",
                "school",
                "school desks",
                "school chairs",
                "classroom",
                "project furniture",
                "durability",
                "procurement",
                "delivery consistency",
            }
        )
    if not terms:
        terms.update(item.lower() for item in dimensions if item and item.lower() not in {"delivery", "resource taxonomy"})
    return {term for term in terms if term}


def _contains_any(text: str, terms: set[str]) -> bool:
    lower = text.lower()
    return any(term in lower for term in terms)


def _line_text(line: object) -> str:
    return " ".join(
        str(getattr(line, attr, "") or "")
        for attr in [
            "product_name",
            "manual_product_name",
            "product_category",
            "description_customer",
            "description_internal",
            "internal_sku",
            "partner_product_code",
        ]
    )


def _product_validation_context(
    db: Session,
    partner_focus: str | None,
    product_focus: list[str],
    dimensions: list[str],
) -> dict[str, object]:
    terms = _product_terms(partner_focus, product_focus, dimensions)
    partner_lower = (partner_focus or "").lower()

    opportunities: list[SalesOpportunity] = []
    for row in db.query(SalesOpportunity).order_by(SalesOpportunity.updated_at.desc()).limit(200).all():
        text = " ".join(
            [
                row.opportunity_name or "",
                row.partner_focus or "",
                " ".join(row.product_focus or []),
                row.customer_segment or "",
                row.risk or "",
                row.next_action or "",
            ]
        )
        if (partner_lower and partner_lower in (row.partner_focus or "").lower()) or _contains_any(text, terms):
            opportunities.append(row)
        if len(opportunities) >= 8:
            break

    quote_ids: dict[str, Quote] = {}
    for line in db.query(QuoteLineItem).order_by(QuoteLineItem.updated_at.desc()).limit(500).all():
        if not _contains_any(_line_text(line), terms):
            continue
        quote = line.quote
        if quote and not quote.is_archived:
            quote_ids[str(quote.id)] = quote
        if len(quote_ids) >= 8:
            break

    order_ids: dict[str, CustomerOrder] = {}
    for order in db.query(CustomerOrder).order_by(CustomerOrder.updated_at.desc()).limit(160).all():
        line_text = " ".join(_line_text(line) for line in order.line_items)
        if _contains_any(line_text + " " + (order.customer_notes or ""), terms) or str(order.source_quote_id) in quote_ids:
            order_ids[str(order.id)] = order
        if len(order_ids) >= 8:
            break

    order_rows = list(order_ids.values())
    order_id_set = {order.id for order in order_rows}
    feedback_rows: list[FeedbackTicket] = []
    for ticket in db.query(FeedbackTicket).order_by(FeedbackTicket.updated_at.desc(), FeedbackTicket.created_at.desc()).limit(200).all():
        text = " ".join([ticket.feedback_type or "", ticket.subject or "", ticket.message or "", ticket.response_summary or ""])
        if (ticket.order_id and ticket.order_id in order_id_set) or _contains_any(text, terms):
            feedback_rows.append(ticket)
        if len(feedback_rows) >= 8:
            break

    market_reviews: list[MarketResponseReview] = []
    for review in db.query(MarketResponseReview).order_by(MarketResponseReview.updated_at.desc()).limit(160).all():
        text = " ".join(
            [
                review.partner_focus,
                review.focus_category,
                " ".join(review.product_focus or []),
                review.review_dimension,
                review.visibility_class,
                review.source_summary,
                review.evidence_summary or "",
                review.customer_safe_summary or "",
            ]
        )
        if (partner_lower and partner_lower in review.partner_focus.lower()) or _contains_any(text, terms):
            market_reviews.append(review)
        if len(market_reviews) >= 8:
            break

    market_items: list[MarketIntelligenceItem] = []
    for item in db.query(MarketIntelligenceItem).order_by(MarketIntelligenceItem.updated_at.desc()).limit(160).all():
        text = " ".join(
            [
                item.title,
                item.related_product_category or "",
                item.market_segment or "",
                item.content or "",
                item.tags or "",
                item.ai_summary or "",
                item.ai_opportunity_analysis or "",
            ]
        )
        if _contains_any(text, terms):
            market_items.append(item)
        if len(market_items) >= 8:
            break

    fulfillment_contexts = [build_order_fulfillment_intelligence(db, order) for order in order_rows[:5]]
    delivery_risks = [
        item
        for item in fulfillment_contexts
        if item.get("risk_level") in {"high", "medium"} or item.get("health") in {"delivery_blocked", "shipment_gap", "after_sales_attention"}
    ]
    high_feedback = [row for row in feedback_rows if row.priority in {"urgent", "high", "P0", "P1"}]
    open_feedback = [row for row in feedback_rows if row.status not in {"closed", "resolved", "archived"}]
    customer_safe_reviews = [row for row in market_reviews if row.visibility_class == "customer-safe"]
    blocked_reviews = [row for row in market_reviews if row.priority in {"P0", "P1"} or row.status in {"blocked", "needs validation"}]

    evidence_count = len(opportunities) + len(quote_ids) + len(order_ids) + len(feedback_rows) + len(market_reviews) + len(market_items)
    if delivery_risks or high_feedback or blocked_reviews:
        health = "needs_product_review"
        priority = "P1"
        next_action = "Review delivery, feedback, and Market Response evidence before using this product line in pilot or customer-safe wording."
    elif customer_safe_reviews and order_ids:
        health = "customer_safe_evidence_ready"
        priority = "P2"
        next_action = "Use approved customer-safe wording in quote/Portal materials and keep collecting order and after-sales evidence."
    elif evidence_count:
        health = "market_validation_in_progress"
        priority = "P2"
        next_action = "Connect opportunity, quote, order, and feedback evidence into Market Response before making product positioning decisions."
    else:
        health = "baseline_only"
        priority = "P3"
        next_action = "Capture real opportunities, quote objections, order delivery notes, and feedback against this product line."

    if partner_focus and partner_focus.upper().startswith("HO"):
        dimensions_requiring_evidence = [
            item
            for item in ["load", "stability", "noise", "warranty", "test cycle", "certification", "project demand"]
            if item in dimensions
        ]
    elif partner_focus and partner_focus.upper().startswith("JOO"):
        dimensions_requiring_evidence = [
            item
            for item in ["durability", "procurement cycle", "classroom deployment", "delivery consistency", "feedback after use"]
            if item in dimensions
        ]
    else:
        dimensions_requiring_evidence = [
            item
            for item in ["product family", "quote logic", "delivery requirement", "resource taxonomy", "customer-visible fields", "Market Response metrics"]
            if item in dimensions
        ]

    readiness_impact: list[str] = []
    if quote_ids:
        readiness_impact.append("quote wording")
    if order_ids:
        readiness_impact.append("delivery visibility")
    if feedback_rows:
        readiness_impact.append("after-sales learning")
    if market_reviews or market_items:
        readiness_impact.append("Market Response")
    if delivery_risks:
        readiness_impact.append("pilot delivery risk")
    if not customer_safe_reviews:
        readiness_impact.append("customer-safe wording")

    return {
        "health": health,
        "priority": priority,
        "evidence_counts": {
            "opportunities": len(opportunities),
            "quotes": len(quote_ids),
            "orders": len(order_ids),
            "feedback": len(feedback_rows),
            "open_feedback": len(open_feedback),
            "high_priority_feedback": len(high_feedback),
            "delivery_risks": len(delivery_risks),
            "market_reviews": len(market_reviews),
            "market_items": len(market_items),
            "customer_safe_reviews": len(customer_safe_reviews),
        },
        "source_paths": {
            "opportunity": "/growth-operations" if opportunities else None,
            "quote": f"/quotes/{next(iter(quote_ids))}" if quote_ids else None,
            "order": f"/orders/{next(iter(order_ids))}" if order_ids else None,
            "feedback": "/feedback-tickets" if feedback_rows else None,
            "market_response": f"/market-response?partner_focus={partner_focus}" if market_reviews or market_items else None,
        },
        "dimensions_requiring_evidence": dimensions_requiring_evidence,
        "readiness_impact": _merge_unique(readiness_impact),
        "next_best_action": next_action,
        "customer_safe_boundary": (
            "Product validation context is internal-only. Customer-visible product claims still require business approval, "
            "security review, and customer-safe wording; no cost, margin, supplier private notes, raw token, or internal scoring is exposed."
        ),
        "safety": dict(PRODUCT_CONTEXT_SAFETY),
    }


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
                validation_context=_product_validation_context(
                    db,
                    review.partner_focus,
                    review.product_focus,
                    [review.review_dimension, *[d for d in dimensions if d != review.review_dimension]][:8],
                ),
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
                    validation_context=_product_validation_context(db, partner_focus, focus, _dimensions_for_focus(focus, partner_focus)[:8]),
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
                validation_context=_product_validation_context(
                    db,
                    lifting_partner,
                    ["lifting systems", "desk frames", "desk legs", "lifting columns", "heavy-duty solutions"],
                    LIFTING_DIMENSIONS,
                ),
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
                validation_context=_product_validation_context(
                    db,
                    education_partner,
                    ["education furniture", "school desks", "school chairs", "project furniture"],
                    EDUCATION_DIMENSIONS,
                ),
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
                validation_context=_product_validation_context(
                    db,
                    "future partner",
                    ["onboarding data", "product family", "quote logic", "delivery requirement", "resource taxonomy"],
                    ["customer-visible fields", "Market Response metrics", "quote logic", "delivery requirement", "resource taxonomy"],
                ),
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
        capability = build_partner_capability_intelligence(db, partner)
        missing = readiness.missing_items if readiness else []
        coverage = _split_tags(partner.main_product_categories or partner.preferred_product_categories)[:6]
        if not coverage:
            coverage = capability.get("product_coverage") or [cap.capability_key for cap in partner.capabilities[:6]]
        items.append(
            PartnerIntelligenceItem(
                partner_id=str(partner.id),
                partner_name=partner.partner_name,
                product_coverage=coverage,
                readiness_level="ready" if not missing else f"{len(missing)} onboarding gaps",
                delivery_ability=capability.get("delivery_reliability") or partner.lead_time or f"delivery rating {partner.delivery_rating or 'unknown'}",
                risk_assessment=", ".join(capability.get("risk_signals") or [])
                or partner.risk_level
                or partner.ai_risk_summary
                or "risk not assessed",
                next_action=capability.get("next_best_action")
                or "Update profile, product coverage, delivery ability, readiness gaps, and customer-visible resources.",
                path="/partner-onboarding",
                capability_intelligence=capability,
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
        fulfillment = build_order_fulfillment_intelligence(db, order)
        risk_level = fulfillment.get("risk_level") or ("high" if delayed or not shipments else "medium" if feedback_count else "normal")
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
                repeat_business_risk=(
                    "delivery/feedback risk may affect repeat business"
                    if risk_level != "normal"
                    else "no immediate repeat-business risk signal"
                ),
                next_action=fulfillment.get("next_best_action")
                or "Review production, shipment, and feedback before customer-visible update or repeat-business outreach.",
                path=f"/orders/{order.id}",
                fulfillment_intelligence=fulfillment,
            )
        )
    return items


def _decimal_to_float(value: Decimal | None) -> float:
    return float(value or Decimal("0"))


def _quote_partner_names(db: Session, quote: Quote) -> list[str]:
    names: list[str] = []
    for line in quote.line_items:
        partner = db.get(ManufacturingPartner, line.partner_id) if line.partner_id else None
        if partner and partner.partner_name:
            names.append(partner.partner_name)
    return _merge_unique(names, limit=6)


def _order_partner_names(db: Session, order: CustomerOrder) -> list[str]:
    names: list[str] = []
    for line in order.line_items:
        partner = db.get(ManufacturingPartner, line.partner_id) if line.partner_id else None
        if partner and partner.partner_name:
            names.append(partner.partner_name)
    return _merge_unique(names, limit=6)


def _safe_company_name(company: Company | None, fallback: str | None = None) -> str:
    return company.company_name if company else fallback or "Unknown customer"


def _win_loss_reason_category(*values: str | None) -> str:
    text = " ".join(value or "" for value in values).lower()
    if any(term in text for term in ["price", "pricing", "cost", "budget", "expensive", "discount"]):
        return "price_or_budget"
    if any(term in text for term in ["delivery", "lead time", "eta", "shipment", "logistics"]):
        return "delivery_or_timing"
    if any(term in text for term in ["load", "stability", "noise", "certification", "warranty", "durability", "quality", "product"]):
        return "product_fit"
    if any(term in text for term in ["competitor", "alternative", "incumbent", "supplier"]):
        return "competition"
    if any(term in text for term in ["project", "procurement", "timing", "school", "installation"]):
        return "project_requirement"
    if any(term in text for term in ["relationship", "trust", "service", "after-sales", "support"]):
        return "trust_or_service"
    return "reason_needs_structure"


def _win_loss_next_quote_guidance(outcome: str, reason_category: str, product_focus: list[str]) -> str:
    focus_text = " / ".join(product_focus[:3]) if product_focus else "this product line"
    if outcome == "won":
        if reason_category == "product_fit":
            return f"Reuse the winning product-fit proof for {focus_text}, but keep customer-visible claims reviewed."
        if reason_category == "delivery_or_timing":
            return f"Reuse delivery confidence for {focus_text} and confirm planned dates before sending the next quote."
        if reason_category == "price_or_budget":
            return f"Reuse the value framing for {focus_text}; do not expose internal cost or margin."
        return f"Turn this win into quote positioning and partner allocation guidance for {focus_text}."
    if outcome == "lost":
        if reason_category == "price_or_budget":
            return f"Review value framing and pricing conversation for {focus_text}; do not expose cost or margin."
        if reason_category == "delivery_or_timing":
            return f"Clarify lead time, shipment plan, and delivery risk before quoting {focus_text} again."
        if reason_category == "product_fit":
            return f"Validate product claims and missing specifications before pitching {focus_text} again."
        if reason_category == "competition":
            return f"Capture competitor positioning and adjust differentiation for {focus_text}."
        return f"Record a sharper lost reason before reusing this quote pattern for {focus_text}."
    return f"Keep this outcome as internal learning until the customer decision is confirmed for {focus_text}."


def _win_loss_record_amount(record: dict[str, object]) -> float:
    return float(record.get("estimated_value") or record.get("quote_value") or 0)


def _win_loss_rollup(records: list[dict[str, object]], field: str) -> list[dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for record in records:
        values = record.get(field)
        if isinstance(values, list):
            keys = [str(value) for value in values if value]
        else:
            keys = [str(values)] if values else ["unassigned"]
        for key in keys:
            row = rows.setdefault(
                key,
                {
                    "name": key,
                    "total": 0,
                    "won": 0,
                    "lost": 0,
                    "open_or_unclear": 0,
                    "commercial_amount": 0.0,
                    "sample_lessons": [],
                },
            )
            row["total"] = int(row["total"]) + 1
            outcome = str(record.get("outcome") or "")
            if outcome == "won":
                row["won"] = int(row["won"]) + 1
            elif outcome == "lost":
                row["lost"] = int(row["lost"]) + 1
            else:
                row["open_or_unclear"] = int(row["open_or_unclear"]) + 1
            row["commercial_amount"] = round(float(row["commercial_amount"]) + _win_loss_record_amount(record), 2)
            row["sample_lessons"] = _merge_unique(
                [*list(row.get("sample_lessons") or []), str(record.get("commercial_lesson") or "")],
                limit=5,
            )
    return sorted(
        rows.values(),
        key=lambda row: (int(row.get("total") or 0), float(row.get("commercial_amount") or 0)),
        reverse=True,
    )


def _win_loss_factor_rows(records: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for record in records:
        for factor in record.get("decision_factors", []) or []:
            key = str(factor)
            row = rows.setdefault(
                key,
                {"factor": key, "total": 0, "won": 0, "lost": 0, "sample_lessons": [], "product_focus": []},
            )
            row["total"] = int(row["total"]) + 1
            if record.get("outcome") == "won":
                row["won"] = int(row["won"]) + 1
            elif record.get("outcome") == "lost":
                row["lost"] = int(row["lost"]) + 1
            row["sample_lessons"] = _merge_unique(
                [*list(row.get("sample_lessons") or []), str(record.get("commercial_lesson") or "")],
                limit=4,
            )
            row["product_focus"] = _merge_unique(
                [*list(row.get("product_focus") or []), *[str(item) for item in (record.get("product_focus") or [])]],
                limit=6,
            )
    return sorted(rows.values(), key=lambda row: int(row.get("total") or 0), reverse=True)[:24]


def build_win_loss_intelligence(db: Session, limit: int = 80) -> dict[str, object]:
    items: list[dict[str, object]] = []
    opportunities = (
        db.query(SalesOpportunity)
        .filter(
            (SalesOpportunity.status.in_(["won", "lost", "closed_won", "closed_lost"]))
            | (SalesOpportunity.decision_stage.in_(["won", "lost"]))
            | (SalesOpportunity.won_reason.isnot(None))
            | (SalesOpportunity.lost_reason.isnot(None))
        )
        .order_by(SalesOpportunity.updated_at.desc())
        .limit(160)
        .all()
    )
    for row in opportunities:
        outcome = "won" if "won" in row.status or row.decision_stage == "won" else "lost"
        reason = row.won_reason if outcome == "won" else row.lost_reason
        company = row.company
        product_focus = row.product_focus or _product_focus_from_text(row.opportunity_name, row.risk, row.notes)
        reason_category = _win_loss_reason_category(reason, row.risk, row.notes, row.competition)
        decision_factors = _merge_unique(
            [
                reason or "reason not recorded",
                row.competition or "",
                row.risk or "",
                row.notes or "",
                *product_focus,
            ],
            limit=10,
        )
        items.append(
            {
                "source_type": "opportunity",
                "source_id": str(row.id),
                "record_key": f"opportunity:{row.id}",
                "outcome": outcome,
                "customer": _safe_company_name(company, row.customer_segment),
                "opportunity_name": row.opportunity_name,
                "partner_focus": row.partner_focus,
                "product_focus": product_focus,
                "estimated_value": _decimal_to_float(row.estimated_value),
                "commercial_amount": _decimal_to_float(row.estimated_value),
                "reason_category": reason_category,
                "decision_factors": decision_factors,
                "competitor_signal": row.competition or "competitor not recorded",
                "commercial_lesson": reason or "Record why this opportunity was won or lost.",
                "next_quote_guidance": _win_loss_next_quote_guidance(outcome, reason_category, product_focus),
                "management_question": "Why did this opportunity win or lose, and what should change in the next quote?",
                "path": "/growth-operations",
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "safety": _safety_flags(),
            }
        )

    learning_rows = (
        db.query(QuoteLearningRecord)
        .filter(QuoteLearningRecord.outcome_status.in_(["won", "lost", "no_decision", "on_hold"]))
        .order_by(QuoteLearningRecord.updated_at.desc(), QuoteLearningRecord.created_at.desc())
        .limit(200)
        .all()
    )
    for learning in learning_rows:
        quote = learning.quote
        if quote is None or quote.is_archived:
            continue
        company = db.get(Company, quote.company_id) if quote.company_id else None
        reason = learning.won_reason if learning.outcome_status == "won" else learning.lost_reason
        product_focus = _quote_product_focus(quote)
        partner_focus = ", ".join(_quote_partner_names(db, quote)) or _partner_focus_from_text(*product_focus)
        reason_category = _win_loss_reason_category(
            reason,
            learning.customer_objection,
            learning.competitor_signal,
            learning.price_feedback,
            learning.delivery_feedback,
            learning.customer_feedback,
        )
        decision_factors = _merge_unique(
            [
                reason or "reason not recorded",
                learning.customer_objection or "",
                learning.competitor_signal or "",
                learning.price_feedback or "",
                learning.delivery_feedback or "",
                *(learning.product_dimensions or []),
                *product_focus,
            ],
            limit=10,
        )
        items.append(
            {
                "source_type": "quote_learning",
                "source_id": str(learning.id),
                "record_key": f"quote_learning:{learning.id}",
                "quote_id": str(quote.id),
                "quote_number": quote.quote_number,
                "outcome": learning.outcome_status,
                "customer": _safe_company_name(company, quote.bill_to_company),
                "partner_focus": partner_focus,
                "product_focus": product_focus,
                "quote_value": _decimal_to_float(quote.grand_total),
                "commercial_amount": _decimal_to_float(quote.grand_total),
                "reason_category": reason_category,
                "decision_factors": decision_factors,
                "competitor_signal": learning.competitor_signal or "competitor not recorded",
                "commercial_lesson": reason or "Record customer decision reason before using this as commercial learning.",
                "next_quote_guidance": _win_loss_next_quote_guidance(learning.outcome_status, reason_category, product_focus),
                "management_question": "What did this quote teach us about customer decision factors?",
                "path": f"/quotes/{quote.id}",
                "updated_at": learning.updated_at.isoformat() if learning.updated_at else None,
                "safety": _safety_flags(),
            }
        )
    items = sorted(items, key=lambda item: str(item.get("updated_at") or ""), reverse=True)[:limit]
    wins = [item for item in items if item.get("outcome") == "won"]
    losses = [item for item in items if item.get("outcome") == "lost"]
    open_or_unclear = [item for item in items if item.get("outcome") not in {"won", "lost"}]
    reason_rows = _win_loss_rollup(items, "reason_category")
    partner_rows = _win_loss_rollup(items, "partner_focus")
    product_rows = _win_loss_rollup(items, "product_focus")
    factor_rows = _win_loss_factor_rows(items)
    return {
        "summary": {
            "total": len(items),
            "won": len(wins),
            "lost": len(losses),
            "open_or_unclear": len(open_or_unclear),
            "win_rate": round(len(wins) / (len(wins) + len(losses)), 2) if wins or losses else None,
            "commercial_amount": round(sum(_win_loss_record_amount(item) for item in items), 2),
            "opportunity_records": len([item for item in items if item.get("source_type") == "opportunity"]),
            "quote_learning_records": len([item for item in items if item.get("source_type") == "quote_learning"]),
        },
        "items": items,
        "reason_clusters": reason_rows,
        "partner_rollup": partner_rows,
        "product_rollup": product_rows,
        "decision_factor_rows": factor_rows,
        "competitor_signals": _merge_unique(
            [
                str(item.get("competitor_signal") or "")
                for item in items
                if item.get("competitor_signal") and item.get("competitor_signal") != "competitor not recorded"
            ],
            limit=16,
        ),
        "management_questions": {
            "why_we_win": wins[:8],
            "why_we_lose": losses[:8],
            "what_to_change_next_quote": [
                {
                    "customer": item.get("customer"),
                    "partner_focus": item.get("partner_focus"),
                    "product_focus": item.get("product_focus"),
                    "outcome": item.get("outcome"),
                    "reason_category": item.get("reason_category"),
                    "next_quote_guidance": item.get("next_quote_guidance"),
                    "path": item.get("path"),
                }
                for item in items[:12]
            ],
            "which_factors_show_up_most": factor_rows[:10],
        },
        "next_action": "Review top win/loss factors before changing campaign targeting, quote wording, product positioning, or partner allocation.",
        "customer_safe_boundary": (
            "Internal commercial learning only. Do not expose cost, margin, supplier private notes, raw IDs, internal scoring, "
            "or unreviewed competitor/customer notes to customer Portal."
        ),
        "safety": _safety_flags(),
    }


def _build_win_loss_intelligence(db: Session) -> list[dict[str, object]]:
    return list(build_win_loss_intelligence(db, limit=16).get("items", []))


def _build_customer_value_intelligence(db: Session) -> list[dict[str, object]]:
    return list(build_customer_value_intelligence(db, limit=16).get("items", []))


def _learning_records_for_quote_ids(db: Session, quote_ids: set[object]) -> list[QuoteLearningRecord]:
    if not quote_ids:
        return []
    return (
        db.query(QuoteLearningRecord)
        .filter(QuoteLearningRecord.quote_id.in_(quote_ids))
        .order_by(QuoteLearningRecord.updated_at.desc())
        .all()
    )


def _customer_value_tier(
    *,
    won_order_amount: Decimal,
    weighted_pipeline_amount: Decimal,
    quote_count: int,
    order_count: int,
    feedback_count: int,
    has_won_learning: bool,
) -> tuple[str, int]:
    score = 20
    if won_order_amount >= Decimal("100000"):
        score += 35
    elif won_order_amount >= Decimal("50000"):
        score += 28
    elif won_order_amount > 0:
        score += 18
    if weighted_pipeline_amount >= Decimal("50000"):
        score += 20
    elif weighted_pipeline_amount > 0:
        score += 12
    if order_count > 1:
        score += 12
    elif order_count == 1:
        score += 7
    if quote_count >= 3:
        score += 8
    elif quote_count:
        score += 4
    if has_won_learning:
        score += 8
    if feedback_count:
        score -= min(feedback_count * 4, 12)
    score = max(0, min(score, 100))
    if score >= 75:
        return "strategic_account", score
    if score >= 55:
        return "growth_account", score
    if score >= 35:
        return "active_prospect", score
    return "early_signal", score


def _customer_value_priority(value_tier: str, weighted_pipeline_amount: Decimal, feedback_count: int) -> str:
    if feedback_count and value_tier in {"strategic_account", "growth_account"}:
        return "P1"
    if value_tier == "strategic_account" or weighted_pipeline_amount >= Decimal("50000"):
        return "P1"
    if value_tier in {"growth_account", "active_prospect"}:
        return "P2"
    return "P3"


def _customer_service_burden(
    *,
    unresolved_feedback_count: int,
    delivery_risk_count: int,
    lost_learning_count: int,
) -> tuple[str, int]:
    burden_score = unresolved_feedback_count * 18 + delivery_risk_count * 20 + lost_learning_count * 5
    if burden_score >= 45:
        return "high_service_burden", min(burden_score, 100)
    if burden_score >= 18:
        return "watch_service_burden", burden_score
    return "clean_or_light_burden", burden_score


def _customer_commercial_quality(
    *,
    value_score: int,
    conversion_rate: float,
    repeat_business_count: int,
    unresolved_feedback_count: int,
    delivery_risk_count: int,
    lost_learning_count: int,
    weighted_pipeline_amount: Decimal,
    won_order_amount: Decimal,
) -> dict[str, object]:
    quality_score = value_score
    quality_score += min(int(conversion_rate * 18), 18)
    quality_score += min(repeat_business_count * 8, 16)
    quality_score -= min(unresolved_feedback_count * 10, 25)
    quality_score -= min(delivery_risk_count * 12, 30)
    quality_score -= min(lost_learning_count * 3, 12)
    quality_score = max(0, min(quality_score, 100))
    service_burden, service_burden_score = _customer_service_burden(
        unresolved_feedback_count=unresolved_feedback_count,
        delivery_risk_count=delivery_risk_count,
        lost_learning_count=lost_learning_count,
    )
    if quality_score >= 75 and service_burden == "clean_or_light_burden":
        tier = "healthy_growth_account"
    elif quality_score >= 60:
        tier = "commercially_promising_but_needs_follow_up"
    elif service_burden != "clean_or_light_burden":
        tier = "value_at_risk"
    else:
        tier = "qualification_needed"
    healthy_revenue_proxy = won_order_amount + (
        weighted_pipeline_amount * Decimal("0.5") if service_burden == "clean_or_light_burden" else Decimal("0")
    )
    return {
        "score": quality_score,
        "tier": tier,
        "service_burden": service_burden,
        "service_burden_score": min(service_burden_score, 100),
        "unresolved_feedback_count": unresolved_feedback_count,
        "delivery_risk_count": delivery_risk_count,
        "loss_learning_count": lost_learning_count,
        "healthy_revenue_proxy": _decimal_to_float(healthy_revenue_proxy),
        "uses_cost_or_margin": False,
        "management_answer": (
            "Healthy commercial value: conversion/repeat potential is supported by low delivery and feedback burden."
            if tier == "healthy_growth_account"
            else "Promising account: revenue signal exists, but follow-up is needed before treating it as clean growth."
            if tier == "commercially_promising_but_needs_follow_up"
            else "Value at risk: resolve delivery, feedback, or lost-decision learning before pursuing repeat business."
            if tier == "value_at_risk"
            else "Qualification needed: build product fit and decision-factor evidence before management attention."
        ),
    }


def _build_customer_value_profile(db: Session, company_id: object) -> dict[str, object] | None:
    company = db.get(Company, company_id)
    quotes = (
        db.query(Quote)
        .filter(Quote.company_id == company_id, Quote.is_archived.is_(False))
        .order_by(Quote.updated_at.desc())
        .all()
    )
    orders = (
        db.query(CustomerOrder)
        .filter(CustomerOrder.company_id == company_id)
        .order_by(CustomerOrder.updated_at.desc())
        .all()
    )
    opportunities = (
        db.query(SalesOpportunity)
        .filter(SalesOpportunity.company_id == company_id)
        .order_by(SalesOpportunity.updated_at.desc())
        .all()
    )
    feedback = (
        db.query(FeedbackTicket)
        .filter(FeedbackTicket.company_id == company_id)
        .order_by(FeedbackTicket.updated_at.desc())
        .all()
    )
    quote_ids = {quote.id for quote in quotes}
    learning_records = _learning_records_for_quote_ids(db, quote_ids)

    quote_total = sum((quote.grand_total or Decimal("0")) for quote in quotes)
    order_total = sum((order.grand_total or Decimal("0")) for order in orders)
    open_opportunities = [row for row in opportunities if row.status not in {"won", "lost", "cancelled"}]
    weighted_pipeline = sum(
        (row.estimated_value or Decimal("0")) * Decimal(row.probability or 0) / Decimal("100")
        for row in open_opportunities
    )
    open_quote_rows = [quote for quote in quotes if quote.status in {"ready_to_send", "sent", "revised"}]
    open_quote_amount = sum((quote.grand_total or Decimal("0")) for quote in open_quote_rows)
    won_learning = [row for row in learning_records if row.outcome_status == "won"]
    lost_learning = [row for row in learning_records if row.outcome_status == "lost"]
    unresolved_feedback = [ticket for ticket in feedback if ticket.status not in {"closed", "resolved"}]
    delivery_risk_orders = [
        order
        for order in orders
        if order.status == "on_hold"
        or any(milestone.status in {"delayed", "blocked"} for milestone in order.production_milestones)
        or (
            order.status in {"ready_to_ship", "in_production"}
            and any(plan.status in {"draft", "planned"} for plan in order.shipment_plans)
        )
    ]

    partner_focus = _merge_unique(
        [
            *[name for quote in quotes for name in _quote_partner_names(db, quote)],
            *[name for order in orders for name in _order_partner_names(db, order)],
            *[row.partner_focus or "" for row in opportunities],
        ],
        limit=6,
    )
    product_focus = _merge_unique(
        [
            *[focus for quote in quotes for focus in _quote_product_focus(quote)],
            *[focus for row in opportunities for focus in (row.product_focus or [])],
            *_product_focus_from_text(company.product_interest_tags if company else ""),
        ],
        limit=10,
    )
    customer_decision_factors = _merge_unique(
        [
            *[factor for row in learning_records for factor in (row.product_dimensions or [])],
            *[row.won_reason or "" for row in won_learning],
            *[row.lost_reason or "" for row in lost_learning],
            *[row.customer_objection or "" for row in learning_records],
            *[row.delivery_feedback or "" for row in learning_records],
        ],
        limit=10,
    )
    active_risks = _merge_unique(
        [
            *[row.risk or "" for row in open_opportunities],
            *[ticket.subject for ticket in feedback if ticket.status not in {"closed", "resolved"}],
        ],
        limit=6,
    )
    value_tier, value_score = _customer_value_tier(
        won_order_amount=order_total,
        weighted_pipeline_amount=weighted_pipeline,
        quote_count=len(quotes),
        order_count=len(orders),
        feedback_count=len(feedback),
        has_won_learning=bool(won_learning),
    )
    priority = _customer_value_priority(value_tier, weighted_pipeline, len(feedback))
    conversion_rate = round(len(orders) / len(quotes), 2) if quotes else 0
    repeat_business_count = max(0, len(orders) - 1)
    commercial_quality = _customer_commercial_quality(
        value_score=value_score,
        conversion_rate=conversion_rate,
        repeat_business_count=repeat_business_count,
        unresolved_feedback_count=len(unresolved_feedback),
        delivery_risk_count=len(delivery_risk_orders),
        lost_learning_count=len(lost_learning),
        weighted_pipeline_amount=weighted_pipeline,
        won_order_amount=order_total,
    )
    project_scale = _size_label(order_total or quote_total or weighted_pipeline, len(quotes) + len(orders))
    recommended_reason = (
        commercial_quality["management_answer"]
        if commercial_quality.get("tier") in {"healthy_growth_account", "value_at_risk"}
        else
        "Existing order value and repeat signal make this account worth management attention."
        if order_total and repeat_business_count
        else "Open weighted pipeline makes this account a near-term revenue source."
        if weighted_pipeline > 0
        else "Quote history exists; convert learning into the next commercial action."
        if quotes
        else "Commercial history is thin; qualify strategic fit before deeper investment."
    )
    next_action = (
        "Resolve feedback risk before asking for repeat business or referral."
        if feedback and value_tier in {"strategic_account", "growth_account"}
        else "Advance the highest-probability opportunity and confirm customer decision factors."
        if weighted_pipeline > 0
        else "Review quote learning and decide whether this account deserves a new campaign touch."
        if quotes
        else "Qualify product fit, project timing, and stakeholder value."
    )
    return {
        "company_id": str(company_id),
        "customer_name": _safe_company_name(company),
        "value_tier": value_tier,
        "value_score": value_score,
        "priority": priority,
        "historical_quote_amount": _decimal_to_float(quote_total),
        "won_order_amount": _decimal_to_float(order_total),
        "weighted_pipeline_amount": _decimal_to_float(weighted_pipeline),
        "open_quote_amount": _decimal_to_float(open_quote_amount),
        "quote_count": len(quotes),
        "order_count": len(orders),
        "opportunity_count": len(opportunities),
        "open_opportunity_count": len(open_opportunities),
        "conversion_rate": conversion_rate,
        "repeat_business_count": repeat_business_count,
        "feedback_count": len(feedback),
        "win_learning_count": len(won_learning),
        "loss_learning_count": len(lost_learning),
        "project_scale": project_scale,
        "strategic_value": value_tier,
        "referral_value": "candidate_after_delivery_success" if len(orders) and not feedback else "needs_relationship_proof",
        "partner_focus": partner_focus,
        "product_focus": product_focus,
        "customer_decision_factors": customer_decision_factors,
        "active_risks": active_risks,
        "recommended_reason": recommended_reason,
        "next_action": next_action,
        "future_revenue_signal": (
            "weighted_pipeline"
            if weighted_pipeline > 0
            else "repeat_business"
            if repeat_business_count
            else "quote_reactivation"
            if quotes
            else "qualification_needed"
        ),
        "commercial_quality": commercial_quality,
        "healthy_revenue_proxy": commercial_quality.get("healthy_revenue_proxy", 0),
        "service_burden": commercial_quality.get("service_burden"),
        "unresolved_feedback_count": len(unresolved_feedback),
        "delivery_risk_order_count": len(delivery_risk_orders),
        "management_question": "Which customers are commercially valuable without relying on internal cost or margin exposure?",
        "path": f"/companies/{company_id}" if company else "/lead-intelligence",
        "safety": _safety_flags(),
    }


def build_customer_value_intelligence(db: Session, limit: int = 50) -> dict[str, object]:
    company_ids = {
        row[0]
        for row in db.query(Quote.company_id).filter(Quote.company_id.isnot(None), Quote.is_archived.is_(False)).all()
    } | {row[0] for row in db.query(CustomerOrder.company_id).filter(CustomerOrder.company_id.isnot(None)).all()} | {
        row[0] for row in db.query(SalesOpportunity.company_id).filter(SalesOpportunity.company_id.isnot(None)).all()
    } | {row[0] for row in db.query(FeedbackTicket.company_id).filter(FeedbackTicket.company_id.isnot(None)).all()}
    items = [profile for company_id in company_ids if (profile := _build_customer_value_profile(db, company_id))]
    items = sorted(
        items,
        key=lambda item: (
            _priority_rank(str(item.get("priority"))),
            -int((item.get("commercial_quality") or {}).get("score") or 0) if isinstance(item.get("commercial_quality"), dict) else 0,
            -int(item.get("value_score") or 0),
            -float(item.get("weighted_pipeline_amount") or 0),
            -float(item.get("won_order_amount") or 0),
        ),
    )[:limit]
    commercial_quality_leaders = [
        item
        for item in items
        if isinstance(item.get("commercial_quality"), dict)
        and item["commercial_quality"].get("tier") in {"healthy_growth_account", "commercially_promising_but_needs_follow_up"}
    ][:8]
    service_burden_accounts = [
        item
        for item in items
        if isinstance(item.get("commercial_quality"), dict)
        and item["commercial_quality"].get("service_burden") != "clean_or_light_burden"
    ][:8]
    return {
        "items": items,
        "summary": {
            "total_accounts": len(items),
            "strategic_accounts": len([item for item in items if item.get("value_tier") == "strategic_account"]),
            "growth_accounts": len([item for item in items if item.get("value_tier") == "growth_account"]),
            "active_prospects": len([item for item in items if item.get("value_tier") == "active_prospect"]),
            "weighted_pipeline_amount": round(sum(float(item.get("weighted_pipeline_amount") or 0) for item in items), 2),
            "won_order_amount": round(sum(float(item.get("won_order_amount") or 0) for item in items), 2),
            "open_quote_amount": round(sum(float(item.get("open_quote_amount") or 0) for item in items), 2),
            "healthy_revenue_proxy": round(sum(float(item.get("healthy_revenue_proxy") or 0) for item in items), 2),
            "commercial_quality_leader_count": len(commercial_quality_leaders),
            "service_burden_account_count": len(service_burden_accounts),
        },
        "commercial_quality_leaders": commercial_quality_leaders,
        "service_burden_accounts": service_burden_accounts,
        "management_questions": {
            "who_to_follow": [item.get("customer_name") for item in items[:5]],
            "why_follow": [item.get("recommended_reason") for item in items[:5]],
            "what_is_commercially_healthy": [
                {
                    "customer_name": item.get("customer_name"),
                    "commercial_quality": item.get("commercial_quality"),
                    "healthy_revenue_proxy": item.get("healthy_revenue_proxy"),
                    "conversion_rate": item.get("conversion_rate"),
                    "repeat_business_count": item.get("repeat_business_count"),
                    "next_action": item.get("next_action"),
                    "path": item.get("path"),
                }
                for item in commercial_quality_leaders
            ],
            "which_value_is_at_risk": [
                {
                    "customer_name": item.get("customer_name"),
                    "service_burden": item.get("service_burden"),
                    "unresolved_feedback_count": item.get("unresolved_feedback_count"),
                    "delivery_risk_order_count": item.get("delivery_risk_order_count"),
                    "next_action": item.get("next_action"),
                    "path": item.get("path"),
                }
                for item in service_burden_accounts
            ],
            "future_revenue_from": [
                {
                    "customer_name": item.get("customer_name"),
                    "signal": item.get("future_revenue_signal"),
                    "weighted_pipeline_amount": item.get("weighted_pipeline_amount"),
                    "open_quote_amount": item.get("open_quote_amount"),
                }
                for item in items[:5]
            ],
        },
        "customer_safe_boundary": (
            "Customer value intelligence uses quote/order/pipeline/repeat/feedback/delivery signals only. "
            "It does not use or expose cost, margin, pricing breakdown, supplier private notes, raw IDs, or internal scoring."
        ),
        "safety": _safety_flags(),
    }


OPEN_OPPORTUNITY_STATUSES = {"open", "active", "qualified", "negotiating"}
OPEN_QUOTE_STATUSES = {"ready_to_send", "sent", "revised"}
ORDER_BACKLOG_STATUSES = {
    "pending_customer_confirmation",
    "confirmed",
    "supplier_confirmation_pending",
    "supplier_confirmed",
    "production_pending",
    "in_production",
    "ready_to_ship",
    "on_hold",
}


def _forecast_period(value: date | None) -> str:
    return value.strftime("%Y-%m") if value else "unscheduled"


def _forecast_risk_level(*values: str | None) -> str:
    text = " ".join(value or "" for value in values).lower()
    if any(term in text for term in ["blocked", "delayed", "high", "urgent", "risk", "complaint", "on_hold"]):
        return "high"
    if any(term in text for term in ["review", "pending", "medium", "follow", "open"]):
        return "medium"
    return "low"


def _forecast_item(
    *,
    source_type: str,
    source_id: object,
    name: str,
    customer_name: str,
    partner_focus: str | None,
    product_focus: list[str],
    amount: Decimal,
    probability: int,
    forecast_date: date | None,
    status: str,
    risk_level: str,
    risk_reason: str,
    next_action: str,
    path: str,
) -> dict[str, object]:
    weighted_amount = amount * Decimal(probability) / Decimal("100")
    return {
        "source_type": source_type,
        "source_id": str(source_id),
        "name": name,
        "customer_name": customer_name,
        "partner_focus": partner_focus,
        "product_focus": product_focus,
        "amount": _decimal_to_float(amount),
        "probability": probability,
        "weighted_amount": _decimal_to_float(weighted_amount),
        "forecast_period": _forecast_period(forecast_date),
        "forecast_date": forecast_date.isoformat() if forecast_date else None,
        "status": status,
        "risk_level": risk_level,
        "risk_reason": risk_reason,
        "next_action": next_action,
        "path": path,
        "safety": _safety_flags(),
    }


def _forecast_rollup(items: list[dict[str, object]], key: str) -> list[dict[str, object]]:
    buckets: dict[str, dict[str, object]] = {}
    for item in items:
        raw_values = item.get(key)
        values = raw_values if isinstance(raw_values, list) else [raw_values]
        for raw_value in values:
            label = str(raw_value or "unassigned")
            bucket = buckets.setdefault(label, {"name": label, "weighted_amount": 0.0, "amount": 0.0, "item_count": 0})
            bucket["weighted_amount"] = round(float(bucket["weighted_amount"]) + float(item.get("weighted_amount") or 0), 2)
            bucket["amount"] = round(float(bucket["amount"]) + float(item.get("amount") or 0), 2)
            bucket["item_count"] = int(bucket["item_count"]) + 1
    return sorted(buckets.values(), key=lambda row: float(row["weighted_amount"]), reverse=True)[:12]


def _opportunity_path(opportunity: SalesOpportunity) -> str:
    if opportunity.quote_id:
        return f"/quotes/{opportunity.quote_id}"
    if opportunity.order_id:
        return f"/orders/{opportunity.order_id}"
    if opportunity.campaign_id:
        return f"/growth-operations?campaign={opportunity.campaign_id}"
    if opportunity.lead_id:
        return f"/leads/{opportunity.lead_id}"
    if opportunity.company_id:
        return f"/companies/{opportunity.company_id}"
    return "/growth-operations"


def build_revenue_forecast_intelligence(db: Session, limit: int = 80) -> dict[str, object]:
    items: list[dict[str, object]] = []

    open_opportunities = (
        db.query(SalesOpportunity)
        .filter(SalesOpportunity.status.in_(OPEN_OPPORTUNITY_STATUSES))
        .order_by(SalesOpportunity.probability.desc(), SalesOpportunity.updated_at.desc())
        .limit(160)
        .all()
    )
    for row in open_opportunities:
        company = row.company
        amount = row.estimated_value or Decimal("0")
        risk_level = _forecast_risk_level(row.risk, row.blocker, row.status)
        items.append(
            _forecast_item(
                source_type="opportunity",
                source_id=row.id,
                name=row.opportunity_name,
                customer_name=_safe_company_name(company, row.customer_segment),
                partner_focus=row.partner_focus,
                product_focus=row.product_focus or [],
                amount=amount,
                probability=row.probability or 0,
                forecast_date=row.expected_close_date,
                status=row.status,
                risk_level=risk_level,
                risk_reason=row.blocker or row.risk or "Opportunity risk not recorded.",
                next_action=row.next_action or "Confirm customer decision factors and expected close date.",
                path=_opportunity_path(row),
            )
        )

    open_quotes = (
        db.query(Quote)
        .filter(Quote.is_archived.is_(False), Quote.status.in_(OPEN_QUOTE_STATUSES))
        .order_by(Quote.follow_up_date.asc().nullslast(), Quote.updated_at.desc())
        .limit(160)
        .all()
    )
    for quote in open_quotes:
        company = db.get(Company, quote.company_id) if quote.company_id else None
        product_focus = _quote_product_focus(quote)
        partner_names = _quote_partner_names(db, quote)
        risk_level = _forecast_risk_level(quote.status, "pending" if quote.follow_up_date else None)
        items.append(
            _forecast_item(
                source_type="quote",
                source_id=quote.id,
                name=quote.quote_number,
                customer_name=_safe_company_name(company, quote.bill_to_company),
                partner_focus=", ".join(partner_names) or _partner_focus_from_text(*product_focus),
                product_focus=product_focus,
                amount=quote.grand_total or Decimal("0"),
                probability=_probability(quote.status),
                forecast_date=quote.follow_up_date or quote.valid_until,
                status=quote.status,
                risk_level=risk_level,
                risk_reason="Quote is still open; follow-up timing drives forecast confidence.",
                next_action="Follow up manually and capture win/loss learning when customer responds.",
                path=f"/quotes/{quote.id}",
            )
        )

    backlog_orders = (
        db.query(CustomerOrder)
        .filter(CustomerOrder.status.in_(ORDER_BACKLOG_STATUSES))
        .order_by(CustomerOrder.order_date.desc(), CustomerOrder.updated_at.desc())
        .limit(160)
        .all()
    )
    for order in backlog_orders:
        company = db.get(Company, order.company_id) if order.company_id else None
        delayed_or_blocked = any(m.status in {"delayed", "blocked"} for m in order.production_milestones)
        shipment_risk = any(plan.status in {"draft", "planned"} for plan in order.shipment_plans) and order.status in {"ready_to_ship", "in_production"}
        risk_level = "high" if delayed_or_blocked else "medium" if shipment_risk or order.status == "on_hold" else "low"
        product_focus = _merge_unique(
            [
                *_product_focus_from_text(*[line.product_name for line in order.line_items]),
                *[line.product_category for line in order.line_items if line.product_category],
            ],
            limit=8,
        )
        partner_names = _order_partner_names(db, order)
        items.append(
            _forecast_item(
                source_type="order_backlog",
                source_id=order.id,
                name=order.order_number,
                customer_name=_safe_company_name(company, order.bill_to_company),
                partner_focus=", ".join(partner_names) or _partner_focus_from_text(*product_focus),
                product_focus=product_focus,
                amount=order.grand_total or Decimal("0"),
                probability=100,
                forecast_date=order.order_date,
                status=order.status,
                risk_level=risk_level,
                risk_reason=(
                    "Production milestone is delayed or blocked."
                    if delayed_or_blocked
                    else "Shipment plan still needs operational follow-up."
                    if shipment_risk
                    else "Booked order is part of committed backlog."
                ),
                next_action=(
                    "Resolve production/shipment risk before treating this revenue as clean delivery."
                    if risk_level != "low"
                    else "Keep delivery execution current and watch for feedback/repeat-business signal."
                ),
                path=f"/orders/{order.id}",
            )
        )

    items = sorted(items, key=lambda item: (float(item.get("weighted_amount") or 0), int(item.get("probability") or 0)), reverse=True)[:limit]
    high_probability = [item for item in items if int(item.get("probability") or 0) >= 60][:12]
    high_risk = [item for item in items if item.get("risk_level") == "high"][:12]
    total_weighted = round(sum(float(item.get("weighted_amount") or 0) for item in items), 2)
    total_amount = round(sum(float(item.get("amount") or 0) for item in items), 2)
    at_risk_amount = round(sum(float(item.get("weighted_amount") or 0) for item in high_risk), 2)
    weighted_opportunity_amount = round(
        sum(float(item.get("weighted_amount") or 0) for item in items if item.get("source_type") == "opportunity"),
        2,
    )
    open_quote_amount = round(
        sum(float(item.get("amount") or 0) for item in items if item.get("source_type") == "quote"),
        2,
    )
    weighted_quote_amount = round(
        sum(float(item.get("weighted_amount") or 0) for item in items if item.get("source_type") == "quote"),
        2,
    )
    return {
        "summary": {
            "total_forecast_amount": total_amount,
            "total_weighted_amount": total_weighted,
            "weighted_opportunity_amount": weighted_opportunity_amount,
            "open_quote_amount": open_quote_amount,
            "weighted_quote_amount": weighted_quote_amount,
            "booked_backlog_amount": round(
                sum(float(item.get("amount") or 0) for item in items if item.get("source_type") == "order_backlog"),
                2,
            ),
            "at_risk_weighted_amount": at_risk_amount,
            "item_count": len(items),
            "high_probability_count": len(high_probability),
            "high_risk_count": len(high_risk),
        },
        "forecast_items": items,
        "high_probability_projects": high_probability,
        "high_risk_projects": high_risk,
        "forecast_by_partner": _forecast_rollup(items, "partner_focus"),
        "forecast_by_product": _forecast_rollup(items, "product_focus"),
        "forecast_by_customer": _forecast_rollup(items, "customer_name"),
        "future_revenue_sources": [
            "open opportunities weighted by probability",
            "sent/revised quotes still under manual follow-up",
            "confirmed or active customer-order backlog",
        ],
        "management_questions": {
            "future_revenue_from": [
                {
                    "name": item.get("name"),
                    "customer_name": item.get("customer_name"),
                    "source_type": item.get("source_type"),
                    "weighted_amount": item.get("weighted_amount"),
                    "probability": item.get("probability"),
                    "risk_level": item.get("risk_level"),
                    "next_action": item.get("next_action"),
                }
                for item in items[:8]
            ],
            "high_probability_projects": high_probability[:8],
            "high_risk_revenue": high_risk[:8],
        },
        "next_action": "Review high-probability projects, quote follow-ups, and at-risk backlog before weekly revenue forecast.",
        "safety": _safety_flags(),
    }


def _partner_performance_health(
    *,
    quote_support_count: int,
    order_count: int,
    win_rate: float,
    on_time_delivery_rate: float | None,
    feedback_issue_count: int,
    missing_inputs: list[str],
    risk_signals: list[str],
) -> tuple[str, str, str]:
    if risk_signals or feedback_issue_count or (on_time_delivery_rate is not None and on_time_delivery_rate < 0.8):
        return (
            "delivery_or_feedback_risk",
            "P1",
            "Review delivery and feedback before allocating more high-value projects.",
        )
    if order_count and win_rate >= 0.5:
        return (
            "proven_commercial_partner",
            "P1",
            "Use this partner as a benchmark for quote allocation, product focus, and repeat-business planning.",
        )
    if quote_support_count and not order_count:
        return (
            "quote_support_needs_conversion",
            "P2",
            "Review quote follow-up and win/loss factors before expanding quote volume.",
        )
    if missing_inputs:
        return (
            "capability_gap",
            "P2",
            "Complete product coverage, pricing basis, delivery ability, and customer-safe resources before pilot allocation.",
        )
    return (
        "early_partner_candidate",
        "P3",
        "Capture quote support, product coverage, and delivery evidence before using this partner in commercial decisions.",
    )


def _partner_allocation_profile(
    *,
    quote_support_amount: Decimal,
    order_amount: Decimal,
    quote_support_count: int,
    order_count: int,
    win_rate: float,
    on_time_delivery_rate: float | None,
    feedback_issue_count: int,
    delayed_or_blocked_orders: int,
    missing_inputs: list[str],
    risk_signals: list[str],
    product_focus: list[str],
) -> dict[str, object]:
    score = 25
    score += min(order_count * 12, 24)
    score += min(quote_support_count * 5, 20)
    score += min(int(win_rate * 24), 24)
    if on_time_delivery_rate is not None:
        score += min(int(on_time_delivery_rate * 16), 16)
    if product_focus:
        score += min(len(product_focus) * 2, 10)
    score -= min(feedback_issue_count * 8, 24)
    score -= min(delayed_or_blocked_orders * 10, 25)
    score -= min(len(risk_signals) * 8, 24)
    score -= min(len(missing_inputs) * 3, 15)
    score = max(0, min(score, 100))

    commercial_amount = order_amount if order_amount > 0 else quote_support_amount
    if score >= 75 and order_count:
        allocation_fit = "allocate_next_quotes"
        pilot_fit = "pilot_candidate"
        action = "Allocate the next matching quote or pilot opportunity, while keeping delivery and feedback monitoring current."
    elif score >= 55 and quote_support_count:
        allocation_fit = "selective_quote_allocation"
        pilot_fit = "needs_conversion_proof"
        action = "Use this partner selectively on matching quotes and capture win/loss learning before pilot expansion."
    elif feedback_issue_count or delayed_or_blocked_orders or risk_signals:
        allocation_fit = "hold_expansion_until_risk_review"
        pilot_fit = "pilot_risk"
        action = "Do not expand high-value allocation until delivery, feedback, or partner risk signals are reviewed."
    elif missing_inputs:
        allocation_fit = "complete_inputs_before_allocation"
        pilot_fit = "needs_partner_inputs"
        action = "Complete product, delivery, resource, and customer-safe inputs before using this partner for commercial allocation."
    else:
        allocation_fit = "exploratory_support_only"
        pilot_fit = "early_candidate"
        action = "Use only for exploratory quote support until conversion, delivery, and feedback evidence exists."

    return {
        "allocation_score": score,
        "allocation_fit": allocation_fit,
        "pilot_fit": pilot_fit,
        "commercial_amount": _decimal_to_float(commercial_amount),
        "quote_support_amount": _decimal_to_float(quote_support_amount),
        "order_amount": _decimal_to_float(order_amount),
        "delivery_confidence": on_time_delivery_rate,
        "conversion_confidence": win_rate,
        "service_risk_count": feedback_issue_count + delayed_or_blocked_orders + len(risk_signals),
        "product_lines_supported": product_focus,
        "next_allocation_action": action,
        "uses_cost_or_margin": False,
    }


def _partner_product_contribution(
    partner_name: str,
    product_focus: list[str],
    allocation_profile: dict[str, object],
    win_rate: float,
    feedback_issue_count: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for focus in product_focus[:8]:
        rows.append(
            {
                "partner_name": partner_name,
                "product_focus": focus,
                "allocation_fit": allocation_profile.get("allocation_fit"),
                "pilot_fit": allocation_profile.get("pilot_fit"),
                "allocation_score": allocation_profile.get("allocation_score"),
                "win_rate": win_rate,
                "feedback_issue_count": feedback_issue_count,
                "next_action": allocation_profile.get("next_allocation_action"),
            }
        )
    return rows


def build_partner_performance_intelligence(db: Session, limit: int = 50) -> dict[str, object]:
    partners = db.query(ManufacturingPartner).filter(ManufacturingPartner.is_active.is_(True)).order_by(ManufacturingPartner.updated_at.desc()).limit(24).all()
    items: list[dict[str, object]] = []
    for partner in partners:
        capability = build_partner_capability_intelligence(db, partner)
        quote_lines = db.query(QuoteLineItem).filter(QuoteLineItem.partner_id == partner.id).all()
        quote_ids = {line.quote_id for line in quote_lines}
        quotes = [db.get(Quote, quote_id) for quote_id in quote_ids]
        quotes = [quote for quote in quotes if quote and not quote.is_archived]
        order_lines = [line for order in db.query(CustomerOrder).order_by(CustomerOrder.updated_at.desc()).limit(200).all() for line in order.line_items if line.partner_id == partner.id]
        order_ids = {line.order_id for line in order_lines}
        orders = [db.get(CustomerOrder, order_id) for order_id in order_ids]
        orders = [order for order in orders if order]
        product_focus = _merge_unique(
            [
                *(_split_tags(partner.main_product_categories) or []),
                *(_split_tags(partner.preferred_product_categories) or []),
                *[line.product_category for line in quote_lines if line.product_category],
                *[line.product_name for line in quote_lines if line.product_name],
                *[line.product_category for line in order_lines if line.product_category],
                *[line.product_name for line in order_lines if line.product_name],
                *[str(item) for item in capability.get("product_coverage", [])],
            ],
            limit=10,
        )
        quote_support_amount = sum((line.total_price or Decimal("0")) for line in quote_lines)
        order_amount = sum((order.grand_total or Decimal("0")) for order in orders)
        won_quote_count = sum(1 for quote in quotes if quote and quote.status == "converted_to_order")
        win_rate = round(won_quote_count / len(quotes), 2) if quotes else 0
        delayed_or_blocked_orders = sum(
            1
            for order in orders
            if any(milestone.status in {"delayed", "blocked"} for milestone in order.production_milestones)
        )
        feedback_issue_count = sum(
            int(db.query(func.count(FeedbackTicket.id)).filter(FeedbackTicket.order_id == order.id).scalar() or 0)
            for order in orders
        )
        on_time_delivery_rate = round((len(orders) - delayed_or_blocked_orders) / len(orders), 2) if orders else None
        missing_inputs = list(capability.get("missing_inputs") or [])
        risk_signals = list(capability.get("risk_signals") or [])
        health, investment_priority, recommended_action = _partner_performance_health(
            quote_support_count=len(quotes),
            order_count=len(orders),
            win_rate=win_rate,
            on_time_delivery_rate=on_time_delivery_rate,
            feedback_issue_count=feedback_issue_count,
            missing_inputs=missing_inputs,
            risk_signals=risk_signals,
        )
        allocation_profile = _partner_allocation_profile(
            quote_support_amount=quote_support_amount,
            order_amount=order_amount,
            quote_support_count=len(quotes),
            order_count=len(orders),
            win_rate=win_rate,
            on_time_delivery_rate=on_time_delivery_rate,
            feedback_issue_count=feedback_issue_count,
            delayed_or_blocked_orders=delayed_or_blocked_orders,
            missing_inputs=missing_inputs,
            risk_signals=risk_signals,
            product_focus=product_focus,
        )
        items.append(
            {
                "partner_id": str(partner.id),
                "partner_name": partner.partner_name,
                "product_focus": product_focus,
                "quote_support_count": len(quotes),
                "quote_support_amount": _decimal_to_float(quote_support_amount),
                "won_quote_count": won_quote_count,
                "win_rate": win_rate,
                "order_amount": _decimal_to_float(order_amount),
                "order_count": len(orders),
                "on_time_delivery_rate": on_time_delivery_rate,
                "feedback_issue_count": feedback_issue_count,
                "health": health,
                "investment_priority": investment_priority,
                "cooperation_history": {
                    "quote_lines": len(quote_lines),
                    "order_lines": len(order_lines),
                    "delayed_or_blocked_orders": delayed_or_blocked_orders,
                    "active_order_statuses": sorted({order.status for order in orders}),
                },
                "capability_score": capability.get("score"),
                "capability_health": capability.get("health"),
                "missing_inputs": missing_inputs,
                "risk_signals": risk_signals,
                "readiness_impact": capability.get("readiness_impact") or [],
                "risk_assessment": partner.risk_level or partner.ai_risk_summary or "risk not assessed",
                "commercial_question": "Which partner deserves the next quote or pilot allocation?",
                "recommended_action": recommended_action,
                "allocation_profile": allocation_profile,
                "allocation_fit": allocation_profile.get("allocation_fit"),
                "pilot_fit": allocation_profile.get("pilot_fit"),
                "allocation_score": allocation_profile.get("allocation_score"),
                "product_line_contribution": _partner_product_contribution(
                    partner.partner_name,
                    product_focus,
                    allocation_profile,
                    win_rate,
                    feedback_issue_count,
                ),
                "next_allocation_action": allocation_profile.get("next_allocation_action"),
                "next_action": allocation_profile.get("next_allocation_action") or recommended_action,
                "path": "/partner-onboarding",
                "customer_safe_boundary": "Internal partner performance judgment only; do not expose supplier private notes, internal scoring, cost, margin, or unreviewed risk notes.",
                "safety": _safety_flags(),
            }
        )
    items = sorted(
        items,
        key=lambda item: (
            _priority_rank(str(item.get("investment_priority") or "P3")),
            int(item.get("allocation_score") or 0),
            float(item.get("order_amount") or 0),
            float(item.get("win_rate") or 0),
            int(item.get("quote_support_count") or 0),
        ),
    )[:limit]
    total_order_amount = round(sum(float(item.get("order_amount") or 0) for item in items), 2)
    total_quote_amount = round(sum(float(item.get("quote_support_amount") or 0) for item in items), 2)
    active_partners = [item for item in items if item.get("order_count") or item.get("quote_support_count")]
    risk_partners = [
        item
        for item in items
        if item.get("health") == "delivery_or_feedback_risk" or item.get("risk_signals") or item.get("feedback_issue_count")
    ]
    top_investment = [
        item
        for item in items
        if item.get("health") in {"proven_commercial_partner", "quote_support_needs_conversion", "delivery_or_feedback_risk"}
    ][:8]
    quote_allocation_candidates = [
        item
        for item in items
        if item.get("allocation_fit") in {"allocate_next_quotes", "selective_quote_allocation"}
    ][:8]
    pilot_candidates = [item for item in items if item.get("pilot_fit") == "pilot_candidate"][:8]
    allocation_risks = [
        item
        for item in items
        if item.get("allocation_fit") in {"hold_expansion_until_risk_review", "complete_inputs_before_allocation"}
    ][:8]
    product_line_allocation = sorted(
        [
            row
            for item in items
            for row in list(item.get("product_line_contribution") or [])
        ],
        key=lambda row: int(row.get("allocation_score") or 0),
        reverse=True,
    )[:24]
    return {
        "summary": {
            "partner_count": len(items),
            "active_partner_count": len(active_partners),
            "quote_support_amount": total_quote_amount,
            "order_amount": total_order_amount,
            "risk_partner_count": len(risk_partners),
            "p1_partner_count": sum(1 for item in items if item.get("investment_priority") == "P1"),
            "feedback_issue_count": sum(int(item.get("feedback_issue_count") or 0) for item in items),
            "quote_allocation_candidate_count": len(quote_allocation_candidates),
            "pilot_candidate_count": len(pilot_candidates),
            "allocation_risk_count": len(allocation_risks),
        },
        "items": items,
        "top_investment_candidates": top_investment,
        "quote_allocation_candidates": quote_allocation_candidates,
        "pilot_candidates": pilot_candidates,
        "allocation_risks": allocation_risks,
        "product_line_allocation": product_line_allocation,
        "delivery_or_feedback_risks": risk_partners[:8],
        "partner_scoreboard": [
            {
                "partner_name": item.get("partner_name"),
                "health": item.get("health"),
                "investment_priority": item.get("investment_priority"),
                "allocation_fit": item.get("allocation_fit"),
                "pilot_fit": item.get("pilot_fit"),
                "allocation_score": item.get("allocation_score"),
                "quote_support_count": item.get("quote_support_count"),
                "win_rate": item.get("win_rate"),
                "order_amount": item.get("order_amount"),
                "on_time_delivery_rate": item.get("on_time_delivery_rate"),
                "feedback_issue_count": item.get("feedback_issue_count"),
                "recommended_action": item.get("recommended_action"),
            }
            for item in items
        ],
        "management_questions": {
            "which_partner_to_invest": top_investment,
            "who_gets_next_quote_allocation": quote_allocation_candidates,
            "who_is_ready_for_pilot": pilot_candidates,
            "who_should_not_get_expanded_allocation_yet": allocation_risks,
            "which_partner_has_delivery_or_feedback_risk": risk_partners[:8],
            "which_product_lines_are_supported": [
                {
                    "partner_name": item.get("partner_name"),
                    "product_focus": item.get("product_focus"),
                    "quote_support_count": item.get("quote_support_count"),
                    "order_count": item.get("order_count"),
                }
                for item in items[:12]
            ],
        },
        "next_action": "Use allocation fit before assigning the next quote, pilot demand, or product-line responsibility to a partner.",
        "customer_safe_boundary": (
            "Internal partner allocation judgement only. It uses quote/order/delivery/feedback/product evidence and does not expose "
            "cost, margin, supplier private notes, raw IDs, token values, or internal-only comments."
        ),
        "safety": _safety_flags(),
    }


def _build_partner_performance_intelligence(db: Session) -> list[dict[str, object]]:
    return list(build_partner_performance_intelligence(db, limit=16).get("items", []))


def _pmf_item_key(partner_focus: str | None, product_focus: list[str]) -> tuple[str, str]:
    partner = partner_focus or _partner_focus_from_text(*product_focus) or "future partner"
    focus = product_focus or ["future product family"]
    return partner, focus[0]


def _pmf_new_item(partner_focus: str, product_focus: list[str]) -> dict[str, object]:
    dimensions = _dimensions_for_focus(product_focus, partner_focus)
    return {
        "partner_focus": partner_focus,
        "product_focus": product_focus,
        "dimensions": dimensions,
        "evidence_counts": {
            "opportunities": 0,
            "open_opportunities": 0,
            "quotes": 0,
            "quote_learning": 0,
            "wins": 0,
            "losses": 0,
            "orders": 0,
            "feedback": 0,
            "open_feedback": 0,
            "delivery_risks": 0,
            "market_reviews": 0,
            "customer_safe_reviews": 0,
        },
        "commercial_value": {
            "pipeline_amount": 0.0,
            "quote_amount": 0.0,
            "order_amount": 0.0,
        },
        "factor_evidence": {dimension: {"evidence": 0, "wins": 0, "losses": 0, "feedback": 0} for dimension in dimensions},
        "customer_objections": [],
        "competitor_signals": [],
        "project_experience": [],
        "source_paths": [],
    }


def _pmf_factor_hits(text: str, dimensions: list[str]) -> list[str]:
    lower = text.lower()
    hits = [dimension for dimension in dimensions if dimension.lower() in lower]
    return hits or [dimension for dimension in dimensions[:2] if dimension]


def _pmf_add_factor(
    item: dict[str, object],
    *,
    text: str,
    source: str,
    outcome: str | None = None,
) -> None:
    factors = item.setdefault("factor_evidence", {})
    dimensions = list(item.get("dimensions") or [])
    for factor in _pmf_factor_hits(text, dimensions):
        row = factors.setdefault(factor, {"evidence": 0, "wins": 0, "losses": 0, "feedback": 0})
        row["evidence"] = int(row.get("evidence") or 0) + 1
        if outcome == "won":
            row["wins"] = int(row.get("wins") or 0) + 1
        elif outcome == "lost":
            row["losses"] = int(row.get("losses") or 0) + 1
        if source == "feedback":
            row["feedback"] = int(row.get("feedback") or 0) + 1


def _pmf_status(item: dict[str, object]) -> tuple[str, str, str]:
    counts = item.get("evidence_counts", {})
    delivery_risks = int(counts.get("delivery_risks") or 0)
    open_feedback = int(counts.get("open_feedback") or 0)
    losses = int(counts.get("losses") or 0)
    orders = int(counts.get("orders") or 0)
    wins = int(counts.get("wins") or 0)
    quotes = int(counts.get("quotes") or 0)
    market_reviews = int(counts.get("market_reviews") or 0)
    customer_safe_reviews = int(counts.get("customer_safe_reviews") or 0)
    if delivery_risks or open_feedback:
        return (
            "pilot_risk",
            "P1",
            "Resolve delivery or after-sales evidence before treating this product line as repeatable.",
        )
    if losses > wins and losses:
        return (
            "conversion_risk",
            "P1",
            "Review lost reasons and customer objections before expanding Campaign or quote volume.",
        )
    if orders and wins:
        return (
            "order_validated",
            "P1",
            "Use won/order evidence to refine quote positioning, partner allocation, and repeat-business targeting.",
        )
    if quotes or market_reviews:
        return (
            "market_learning",
            "P2",
            "Connect quote learning and Market Response reviews into customer-safe wording after business review.",
        )
    if customer_safe_reviews:
        return (
            "customer_safe_preview",
            "P2",
            "Reuse customer-safe preview cautiously and keep capturing quote/order/feedback evidence.",
        )
    return (
        "baseline_only",
        "P3",
        "Capture opportunity, quote, order, and feedback evidence before making product-market claims.",
    )


def build_product_market_fit_intelligence(db: Session, limit: int = 50) -> dict[str, object]:
    items_by_key: dict[tuple[str, str], dict[str, object]] = {}

    def ensure_item(partner_focus: str | None, product_focus: list[str]) -> dict[str, object]:
        partner, primary_focus = _pmf_item_key(partner_focus, product_focus)
        key = (partner, primary_focus)
        if key not in items_by_key:
            items_by_key[key] = _pmf_new_item(partner, product_focus or [primary_focus])
        return items_by_key[key]

    for row in db.query(SalesOpportunity).order_by(SalesOpportunity.updated_at.desc()).limit(240).all():
        product_focus = row.product_focus or _product_focus_from_text(row.opportunity_name, row.risk, row.next_action)
        item = ensure_item(row.partner_focus or _partner_focus_from_text(*product_focus, row.opportunity_name), product_focus)
        counts = item["evidence_counts"]
        counts["opportunities"] = int(counts.get("opportunities") or 0) + 1
        if row.status not in {"won", "lost", "closed_won", "closed_lost", "cancelled"}:
            counts["open_opportunities"] = int(counts.get("open_opportunities") or 0) + 1
        if "won" in row.status:
            counts["wins"] = int(counts.get("wins") or 0) + 1
        if "lost" in row.status:
            counts["losses"] = int(counts.get("losses") or 0) + 1
        value = item["commercial_value"]
        value["pipeline_amount"] = round(float(value.get("pipeline_amount") or 0) + _decimal_to_float(row.estimated_value), 2)
        _pmf_add_factor(
            item,
            text=" ".join([row.opportunity_name or "", row.won_reason or "", row.lost_reason or "", row.risk or "", row.notes or ""]),
            source="opportunity",
            outcome="won" if "won" in row.status else "lost" if "lost" in row.status else None,
        )
        if row.lost_reason or row.risk or row.blocker:
            item["customer_objections"] = _merge_unique(
                [*list(item.get("customer_objections") or []), row.lost_reason or row.risk or row.blocker or ""],
                limit=8,
            )
        if row.competition:
            item["competitor_signals"] = _merge_unique([*list(item.get("competitor_signals") or []), row.competition], limit=8)
        item["source_paths"] = _merge_unique([*list(item.get("source_paths") or []), _opportunity_path(row)], limit=8)

    quote_ids_seen: set[object] = set()
    for line in db.query(QuoteLineItem).order_by(QuoteLineItem.updated_at.desc()).limit(700).all():
        quote = line.quote
        if quote is None or quote.is_archived:
            continue
        product_focus = _product_focus_from_text(_line_text(line)) or _quote_product_focus(quote)
        partner = db.get(ManufacturingPartner, line.partner_id) if line.partner_id else None
        partner_focus = partner.partner_name if partner else ", ".join(_quote_partner_names(db, quote)) or _partner_focus_from_text(*product_focus)
        item = ensure_item(partner_focus, product_focus)
        counts = item["evidence_counts"]
        if quote.id not in quote_ids_seen:
            counts["quotes"] = int(counts.get("quotes") or 0) + 1
            value = item["commercial_value"]
            value["quote_amount"] = round(float(value.get("quote_amount") or 0) + _decimal_to_float(quote.grand_total), 2)
            quote_ids_seen.add(quote.id)
        learning_records = quote.learning_records or []
        for learning in learning_records:
            counts["quote_learning"] = int(counts.get("quote_learning") or 0) + 1
            if learning.outcome_status == "won":
                counts["wins"] = int(counts.get("wins") or 0) + 1
            elif learning.outcome_status == "lost":
                counts["losses"] = int(counts.get("losses") or 0) + 1
            text = " ".join(
                [
                    learning.won_reason or "",
                    learning.lost_reason or "",
                    learning.customer_objection or "",
                    learning.price_feedback or "",
                    learning.delivery_feedback or "",
                    " ".join(learning.product_dimensions or []),
                ]
            )
            _pmf_add_factor(item, text=text, source="quote_learning", outcome=learning.outcome_status)
            if learning.customer_objection or learning.lost_reason:
                item["customer_objections"] = _merge_unique(
                    [*list(item.get("customer_objections") or []), learning.customer_objection or learning.lost_reason or ""],
                    limit=8,
                )
            if learning.competitor_signal:
                item["competitor_signals"] = _merge_unique([*list(item.get("competitor_signals") or []), learning.competitor_signal], limit=8)
        _pmf_add_factor(item, text=_line_text(line), source="quote")
        item["source_paths"] = _merge_unique([*list(item.get("source_paths") or []), f"/quotes/{quote.id}"], limit=8)

    order_ids_seen: set[object] = set()
    for order in db.query(CustomerOrder).order_by(CustomerOrder.updated_at.desc()).limit(220).all():
        product_focus = _merge_unique(
            [
                *_product_focus_from_text(*[_line_text(line) for line in order.line_items]),
                *[line.product_category for line in order.line_items if line.product_category],
            ],
            limit=6,
        )
        partner_names = _order_partner_names(db, order)
        item = ensure_item(", ".join(partner_names) or _partner_focus_from_text(*product_focus), product_focus)
        counts = item["evidence_counts"]
        if order.id not in order_ids_seen:
            counts["orders"] = int(counts.get("orders") or 0) + 1
            value = item["commercial_value"]
            value["order_amount"] = round(float(value.get("order_amount") or 0) + _decimal_to_float(order.grand_total), 2)
            order_ids_seen.add(order.id)
        delivery_risk = any(milestone.status in {"delayed", "blocked"} for milestone in order.production_milestones) or not order.shipment_plans
        if delivery_risk:
            counts["delivery_risks"] = int(counts.get("delivery_risks") or 0) + 1
        _pmf_add_factor(item, text=" ".join([*[_line_text(line) for line in order.line_items], order.customer_notes or ""]), source="order")
        item["project_experience"] = _merge_unique(
            [
                *list(item.get("project_experience") or []),
                f"{order.order_number}: {order.status}; shipment {'present' if order.shipment_plans else 'missing'}",
            ],
            limit=8,
        )
        item["source_paths"] = _merge_unique([*list(item.get("source_paths") or []), f"/orders/{order.id}"], limit=8)

    for ticket in db.query(FeedbackTicket).order_by(FeedbackTicket.updated_at.desc(), FeedbackTicket.created_at.desc()).limit(240).all():
        order = db.get(CustomerOrder, ticket.order_id) if ticket.order_id else None
        product_focus = (
            _merge_unique(
                [
                    *_product_focus_from_text(*[_line_text(line) for line in order.line_items]),
                    *[line.product_category for line in order.line_items if line.product_category],
                ],
                limit=6,
            )
            if order
            else _product_focus_from_text(ticket.subject, ticket.message, ticket.feedback_type)
        )
        partner_focus = ", ".join(_order_partner_names(db, order)) if order else _partner_focus_from_text(*product_focus, ticket.subject, ticket.message)
        item = ensure_item(partner_focus, product_focus)
        counts = item["evidence_counts"]
        counts["feedback"] = int(counts.get("feedback") or 0) + 1
        if ticket.status not in {"resolved", "closed", "archived"}:
            counts["open_feedback"] = int(counts.get("open_feedback") or 0) + 1
        _pmf_add_factor(item, text=" ".join([ticket.feedback_type, ticket.subject, ticket.message, ticket.response_summary or ""]), source="feedback")
        item["customer_objections"] = _merge_unique(
            [*list(item.get("customer_objections") or []), ticket.subject],
            limit=8,
        )
        item["source_paths"] = _merge_unique([*list(item.get("source_paths") or []), "/feedback-tickets"], limit=8)

    for review in db.query(MarketResponseReview).order_by(MarketResponseReview.updated_at.desc()).limit(240).all():
        item = ensure_item(review.partner_focus, review.product_focus or [review.focus_category])
        counts = item["evidence_counts"]
        counts["market_reviews"] = int(counts.get("market_reviews") or 0) + 1
        if review.visibility_class == "customer-safe":
            counts["customer_safe_reviews"] = int(counts.get("customer_safe_reviews") or 0) + 1
        _pmf_add_factor(
            item,
            text=" ".join([review.review_dimension, review.source_summary, review.evidence_summary or "", review.customer_safe_summary or ""]),
            source="market_response",
        )
        item["source_paths"] = _merge_unique(
            [*list(item.get("source_paths") or []), f"/market-response?partner_focus={review.partner_focus}"],
            limit=8,
        )

    baseline_items = [
        (_brand("HO", "SUN"), ["lifting systems", "desk frames", "desk legs", "lifting columns", "heavy-duty solutions"]),
        (_brand("JOO", "BOO"), ["education furniture", "school desks", "school chairs", "project furniture"]),
        ("future partner", ["onboarding data", "product family", "quote logic", "delivery requirement", "resource taxonomy"]),
    ]
    for partner, focus in baseline_items:
        ensure_item(partner, focus)

    items: list[dict[str, object]] = []
    for item in items_by_key.values():
        status, priority, next_action = _pmf_status(item)
        factors = item.get("factor_evidence", {})
        ranked_factors = sorted(
            [
                {
                    "factor": factor,
                    "evidence_count": int(values.get("evidence") or 0),
                    "wins": int(values.get("wins") or 0),
                    "losses": int(values.get("losses") or 0),
                    "feedback": int(values.get("feedback") or 0),
                    "status": "validated" if values.get("wins") or values.get("feedback") else "needs evidence",
                }
                for factor, values in factors.items()
            ],
            key=lambda row: (int(row["evidence_count"]), int(row["wins"]), int(row["feedback"])),
            reverse=True,
        )
        counts = item.get("evidence_counts", {})
        quotes = int(counts.get("quotes") or 0)
        orders = int(counts.get("orders") or 0)
        wins = int(counts.get("wins") or 0)
        losses = int(counts.get("losses") or 0)
        item.update(
            {
                "fit_status": status,
                "priority": priority,
                "purchase_factors": [str(row["factor"]) for row in ranked_factors[:10]] or list(item.get("dimensions") or []),
                "buying_factors_ranked": ranked_factors,
                "conversion_signal": {
                    "quote_to_order_rate": round(orders / quotes, 2) if quotes else 0,
                    "win_loss_ratio": round(wins / (wins + losses), 2) if wins + losses else 0,
                    "validated_by_orders": bool(orders),
                    "validated_by_learning": bool(wins or losses),
                },
                "commercial_question": "Which product factors are actually driving wins, losses, orders, feedback, or pilot risk?",
                "next_action": next_action,
                "path": (list(item.get("source_paths") or []) or ["/market-response"])[0],
                "customer_safe_boundary": (
                    "Internal Product-Market Fit intelligence only. Customer-visible claims still require business approval; "
                    "do not expose cost, margin, supplier private notes, raw IDs, internal scoring, or unreviewed risk notes."
                ),
                "safety": _safety_flags(),
            }
        )
        items.append(item)

    items = sorted(
        items,
        key=lambda item: (
            _priority_rank(str(item.get("priority") or "P3")),
            float(item.get("commercial_value", {}).get("order_amount") or 0),
            int(item.get("evidence_counts", {}).get("wins") or 0),
            int(item.get("evidence_counts", {}).get("market_reviews") or 0),
        ),
    )[:limit]
    return {
        "summary": {
            "product_line_count": len(items),
            "p1_product_line_count": sum(1 for item in items if item.get("priority") == "P1"),
            "order_validated_count": sum(1 for item in items if item.get("fit_status") == "order_validated"),
            "pilot_risk_count": sum(1 for item in items if item.get("fit_status") == "pilot_risk"),
            "quote_learning_count": sum(int(item.get("evidence_counts", {}).get("quote_learning") or 0) for item in items),
            "feedback_signal_count": sum(int(item.get("evidence_counts", {}).get("feedback") or 0) for item in items),
            "order_amount": round(sum(float(item.get("commercial_value", {}).get("order_amount") or 0) for item in items), 2),
        },
        "items": items,
        "top_product_lines": items[:12],
        "pilot_risk_product_lines": [item for item in items if item.get("fit_status") == "pilot_risk"][:8],
        "validated_buying_factors": [
            {
                "partner_focus": item.get("partner_focus"),
                "product_focus": item.get("product_focus"),
                "buying_factors": item.get("buying_factors_ranked", [])[:5],
            }
            for item in items
            if item.get("buying_factors_ranked")
        ][:12],
        "management_questions": {
            "what_converts": [item for item in items if item.get("fit_status") == "order_validated"][:8],
            "why_customers_buy_or_decline": [
                {
                    "partner_focus": item.get("partner_focus"),
                    "product_focus": item.get("product_focus"),
                    "customer_objections": item.get("customer_objections"),
                    "competitor_signals": item.get("competitor_signals"),
                    "buying_factors": item.get("buying_factors_ranked", [])[:5],
                }
                for item in items[:8]
            ],
            "which_product_lines_need_validation_before_pilot": [
                item for item in items if item.get("fit_status") in {"pilot_risk", "conversion_risk", "baseline_only"}
            ][:8],
        },
        "next_action": "Review P1 PMF lines before campaign expansion, quote wording, customer-safe claims, or pilot allocation.",
        "safety": _safety_flags(),
    }


def _build_product_market_fit_intelligence(
    db: Session,
    products: list[ProductIntelligenceItem],
    quotations: list[QuotationIntelligenceItem],
) -> list[dict[str, object]]:
    pmf_payload = build_product_market_fit_intelligence(db, limit=16)
    if pmf_payload.get("items"):
        return list(pmf_payload["items"])
    items: list[dict[str, object]] = []
    quote_dimensions = {
        dimension
        for quote in quotations
        for dimension in quote.commercial_intelligence.get("captured_dimensions", []) + quote.commercial_intelligence.get("dimension_review_needs", [])
    }
    for product in products:
        context = product.validation_context or {}
        counts = context.get("evidence_counts", {})
        purchase_factors = _merge_unique(
            [
                *product.dimensions,
                *context.get("dimensions_requiring_evidence", []),
                *list(quote_dimensions),
            ],
            limit=10,
        )
        items.append(
            {
                "partner_focus": product.partner_focus,
                "product_focus": product.product_focus,
                "purchase_factors": purchase_factors,
                "project_experience": {
                    "opportunities": counts.get("opportunities", 0),
                    "quotes": counts.get("quotes", 0),
                    "orders": counts.get("orders", 0),
                    "feedback": counts.get("feedback", 0),
                    "delivery_risks": counts.get("delivery_risks", 0),
                    "market_reviews": counts.get("market_reviews", 0),
                },
                "fit_status": context.get("health") or "baseline_only",
                "commercial_question": (
                    "Which buying factor most improves win rate or repeat business for this product family?"
                    if counts
                    else "What real customer evidence is needed before treating this product family as validated?"
                ),
                "next_action": context.get("next_best_action") or product.next_action,
                "path": product.source_path,
                "customer_safe_boundary": context.get("customer_safe_boundary"),
                "safety": context.get("safety") or _safety_flags(),
            }
        )
    return items[:16]


def _build_revenue_forecast_intelligence(
    opportunities: list[OpportunityPipelineItem],
    quotations: list[QuotationIntelligenceItem],
    db: Session,
) -> dict[str, object]:
    forecast = build_revenue_forecast_intelligence(db, limit=80)
    summary = forecast.get("summary", {})
    forecast["weighted_opportunity_amount"] = summary.get("weighted_opportunity_amount", 0)
    forecast["open_quote_amount"] = summary.get("open_quote_amount", 0)
    forecast["weighted_quote_amount"] = summary.get("weighted_quote_amount", 0)
    return forecast


def _account_360_path(
    *,
    company_id: object,
    leads: list[Lead],
    opportunities: list[SalesOpportunity],
    quotes: list[Quote],
    orders: list[CustomerOrder],
    feedback: list[FeedbackTicket],
) -> str:
    if opportunities:
        return f"/growth-operations?company={company_id}"
    if quotes:
        return f"/quotes/{quotes[0].id}"
    if orders:
        return f"/orders/{orders[0].id}"
    if feedback:
        return "/feedback-tickets"
    if leads:
        return f"/leads/{leads[0].id}"
    return f"/companies/{company_id}"


def _account_360_stage(
    *,
    leads: list[Lead],
    opportunities: list[SalesOpportunity],
    quotes: list[Quote],
    orders: list[CustomerOrder],
    feedback: list[FeedbackTicket],
) -> str:
    if len(orders) > 1:
        return "Repeat Business"
    if feedback:
        return "After-Sales"
    if orders:
        return "Order / Delivery"
    if quotes:
        return "Quotation"
    if opportunities:
        return "Opportunity"
    if leads:
        return "Lead"
    return "Company"


def _account_360_next_action(
    *,
    weighted_pipeline: Decimal,
    open_quotes: list[Quote],
    open_feedback: list[FeedbackTicket],
    orders: list[CustomerOrder],
    opportunities: list[SalesOpportunity],
    value_tier: str,
) -> str:
    if open_feedback:
        return "Resolve open feedback before asking for repeat business, referral, or customer-visible success story."
    if weighted_pipeline > 0 and opportunities:
        return "Advance the highest-probability opportunity and capture customer decision factors."
    if open_quotes:
        return "Follow up open quotes manually and record win/loss learning when the customer responds."
    if len(orders) > 1 or value_tier in {"strategic_account", "growth_account"}:
        return "Review delivery outcome and decide whether to create a repeat-business or referral motion."
    return "Qualify product fit, project timing, stakeholder value, and partner fit before deeper investment."


def _build_account_360_profile(db: Session, company_id: object) -> dict[str, object] | None:
    company = db.get(Company, company_id)
    if company is None:
        return None
    leads = (
        db.query(Lead)
        .filter(Lead.company_id == company_id, Lead.is_active.is_(True))
        .order_by(Lead.updated_at.desc())
        .all()
    )
    opportunities = (
        db.query(SalesOpportunity)
        .filter(SalesOpportunity.company_id == company_id)
        .order_by(SalesOpportunity.updated_at.desc())
        .all()
    )
    quotes = (
        db.query(Quote)
        .filter(Quote.company_id == company_id, Quote.is_archived.is_(False))
        .order_by(Quote.updated_at.desc())
        .all()
    )
    orders = (
        db.query(CustomerOrder)
        .filter(CustomerOrder.company_id == company_id)
        .order_by(CustomerOrder.updated_at.desc())
        .all()
    )
    feedback = (
        db.query(FeedbackTicket)
        .filter(FeedbackTicket.company_id == company_id)
        .order_by(FeedbackTicket.updated_at.desc())
        .all()
    )
    learning_records = _learning_records_for_quote_ids(db, {quote.id for quote in quotes})
    customer_value = _build_customer_value_profile(db, company_id) or {}

    open_opportunities = [row for row in opportunities if row.status not in {"won", "lost", "closed_won", "closed_lost", "cancelled"}]
    open_quotes = [quote for quote in quotes if quote.status in OPEN_QUOTE_STATUSES]
    open_feedback = [ticket for ticket in feedback if ticket.status not in {"resolved", "closed"}]
    won_learning = [row for row in learning_records if row.outcome_status == "won"]
    lost_learning = [row for row in learning_records if row.outcome_status == "lost"]
    weighted_pipeline = sum(
        (row.estimated_value or Decimal("0")) * Decimal(row.probability or 0) / Decimal("100")
        for row in open_opportunities
    )
    quote_amount = sum((quote.grand_total or Decimal("0")) for quote in quotes)
    order_amount = sum((order.grand_total or Decimal("0")) for order in orders)
    delayed_or_blocked_orders = sum(
        1
        for order in orders
        if any(milestone.status in {"delayed", "blocked"} for milestone in order.production_milestones)
    )
    shipment_missing_orders = sum(1 for order in orders if not order.shipment_plans)
    partner_focus = _merge_unique(
        [
            *[name for quote in quotes for name in _quote_partner_names(db, quote)],
            *[name for order in orders for name in _order_partner_names(db, order)],
            *[row.partner_focus or "" for row in opportunities],
        ],
        limit=8,
    )
    product_focus = _merge_unique(
        [
            *_product_focus_from_text(company.product_interest_tags, company.business_description),
            *[focus for quote in quotes for focus in _quote_product_focus(quote)],
            *[focus for row in opportunities for focus in (row.product_focus or [])],
            *[line.product_category for order in orders for line in order.line_items if line.product_category],
        ],
        limit=10,
    )
    decision_factors = _merge_unique(
        [
            *[factor for record in learning_records for factor in (record.product_dimensions or [])],
            *[record.won_reason or "" for record in won_learning],
            *[record.lost_reason or "" for record in lost_learning],
            *[record.customer_objection or "" for record in learning_records],
            *[row.risk or "" for row in opportunities],
        ],
        limit=10,
    )
    blockers = _merge_unique(
        [
            *[ticket.subject for ticket in open_feedback],
            *[row.blocker or "" for row in open_opportunities],
            *["delivery risk" for _ in range(delayed_or_blocked_orders)],
            *["shipment visibility missing" for _ in range(shipment_missing_orders)],
        ],
        limit=8,
    )
    value_tier = str(customer_value.get("value_tier") or "early_signal")
    value_score = int(customer_value.get("value_score") or 0)
    stage = _account_360_stage(
        leads=leads,
        opportunities=opportunities,
        quotes=quotes,
        orders=orders,
        feedback=feedback,
    )
    priority = _customer_value_priority(value_tier, weighted_pipeline, len(open_feedback))
    next_action = _account_360_next_action(
        weighted_pipeline=weighted_pipeline,
        open_quotes=open_quotes,
        open_feedback=open_feedback,
        orders=orders,
        opportunities=open_opportunities,
        value_tier=value_tier,
    )
    return {
        "account_key": f"company:{company.id}",
        "company_id": str(company.id),
        "customer_name": company.company_name,
        "current_stage": stage,
        "priority": priority,
        "value_tier": value_tier,
        "value_score": value_score,
        "company_profile": {
            "company_type": company.company_type,
            "industry": company.industry,
            "customer_segment": company.customer_segment,
            "strategic_level": company.strategic_level,
            "country": company.country,
        },
        "source_counts": {
            "leads": len(leads),
            "opportunities": len(opportunities),
            "open_opportunities": len(open_opportunities),
            "quotes": len(quotes),
            "open_quotes": len(open_quotes),
            "orders": len(orders),
            "feedback": len(feedback),
            "open_feedback": len(open_feedback),
            "win_loss_records": len(learning_records),
        },
        "commercial_value": {
            "historical_quote_amount": _decimal_to_float(quote_amount),
            "won_order_amount": _decimal_to_float(order_amount),
            "weighted_pipeline_amount": _decimal_to_float(weighted_pipeline),
            "conversion_rate": round(len(orders) / len(quotes), 2) if quotes else 0,
            "repeat_business_count": max(0, len(orders) - 1),
            "strategic_value": customer_value.get("strategic_value") or value_tier,
        },
        "object_timeline": [
            {
                "source_type": "lead",
                "source_id": str(row.id),
                "label": row.lead_name,
                "status": row.current_stage,
                "path": f"/leads/{row.id}",
            }
            for row in leads[:4]
        ]
        + [
            {
                "source_type": "opportunity",
                "source_id": str(row.id),
                "label": row.opportunity_name,
                "status": row.status,
                "path": _opportunity_path(row),
            }
            for row in opportunities[:4]
        ]
        + [
            {
                "source_type": "quote",
                "source_id": str(row.id),
                "label": row.quote_number,
                "status": row.status,
                "path": f"/quotes/{row.id}",
            }
            for row in quotes[:4]
        ]
        + [
            {
                "source_type": "order",
                "source_id": str(row.id),
                "label": row.order_number,
                "status": row.status,
                "path": f"/orders/{row.id}",
            }
            for row in orders[:4]
        ]
        + [
            {
                "source_type": "feedback",
                "source_id": str(row.id),
                "label": row.ticket_number,
                "status": row.status,
                "path": "/feedback-tickets",
            }
            for row in feedback[:4]
        ],
        "partner_focus": partner_focus,
        "product_focus": product_focus,
        "decision_factors": decision_factors,
        "win_loss_summary": {
            "won": len(won_learning),
            "lost": len(lost_learning),
            "lessons": _merge_unique(
                [record.won_reason or record.lost_reason or record.customer_objection or "" for record in learning_records],
                limit=6,
            ),
        },
        "delivery_summary": {
            "order_count": len(orders),
            "delayed_or_blocked_orders": delayed_or_blocked_orders,
            "shipment_missing_orders": shipment_missing_orders,
            "open_feedback_count": len(open_feedback),
        },
        "repeat_business_signal": (
            "repeat_ready"
            if len(orders) > 1 and not open_feedback
            else "resolve_feedback_first"
            if open_feedback
            else "pipeline_or_quote_follow_up"
            if weighted_pipeline or open_quotes
            else "qualification_needed"
        ),
        "open_blockers": blockers,
        "active_paths": _merge_unique(
            [
                _account_360_path(
                    company_id=company.id,
                    leads=leads,
                    opportunities=opportunities,
                    quotes=quotes,
                    orders=orders,
                    feedback=feedback,
                ),
                *[f"/orders/{order.id}" for order in orders[:2]],
                *[f"/quotes/{quote.id}" for quote in quotes[:2]],
                "/feedback-tickets" if feedback else "",
            ],
            limit=6,
        ),
        "decision_reason": (
            blockers[0]
            if blockers
            else f"{stage}: quote {len(quotes)}, order {len(orders)}, pipeline {_decimal_to_float(weighted_pipeline)}."
        ),
        "next_action": next_action,
        "path": _account_360_path(
            company_id=company.id,
            leads=leads,
            opportunities=opportunities,
            quotes=quotes,
            orders=orders,
            feedback=feedback,
        ),
        "customer_safe_boundary": "Internal Account 360 profile; do not expose feedback details, internal notes, cost, margin, pricing breakdown, supplier private notes, or raw IDs to customer Portal.",
        "safety": _safety_flags(),
    }


def build_account_360_intelligence(db: Session, limit: int = 50) -> dict[str, object]:
    company_ids: set[object] = set()
    for (company_id,) in db.query(Company.id).filter(Company.is_active.is_(True)).limit(200).all():
        company_ids.add(company_id)
    for model in [Lead, SalesOpportunity, Quote, CustomerOrder, FeedbackTicket]:
        query = db.query(model.company_id).filter(model.company_id.isnot(None))
        if model is Quote:
            query = query.filter(Quote.is_archived.is_(False))
        for (company_id,) in query.limit(200).all():
            company_ids.add(company_id)

    items = [profile for company_id in company_ids if (profile := _build_account_360_profile(db, company_id))]
    items = sorted(
        items,
        key=lambda item: (
            _priority_rank(str(item.get("priority") or "P3")),
            -int(item.get("value_score") or 0),
            -float(item.get("commercial_value", {}).get("weighted_pipeline_amount") or 0),
            -float(item.get("commercial_value", {}).get("won_order_amount") or 0),
        ),
    )[:limit]
    return {
        "summary": {
            "account_count": len(items),
            "p1_account_count": sum(1 for item in items if item.get("priority") == "P1"),
            "strategic_account_count": sum(1 for item in items if item.get("value_tier") == "strategic_account"),
            "open_opportunity_count": sum(int(item.get("source_counts", {}).get("open_opportunities") or 0) for item in items),
            "open_quote_count": sum(int(item.get("source_counts", {}).get("open_quotes") or 0) for item in items),
            "open_feedback_count": sum(int(item.get("source_counts", {}).get("open_feedback") or 0) for item in items),
            "weighted_pipeline_amount": round(
                sum(float(item.get("commercial_value", {}).get("weighted_pipeline_amount") or 0) for item in items),
                2,
            ),
            "won_order_amount": round(
                sum(float(item.get("commercial_value", {}).get("won_order_amount") or 0) for item in items),
                2,
            ),
        },
        "items": items,
        "recommended_accounts": items[:12],
        "accounts_with_open_feedback": [item for item in items if item.get("source_counts", {}).get("open_feedback")][:12],
        "repeat_business_candidates": [item for item in items if item.get("repeat_business_signal") == "repeat_ready"][:12],
        "management_questions": {
            "who_to_follow": items[:8],
            "which_accounts_have_full_history": [
                item
                for item in items
                if item.get("source_counts", {}).get("leads")
                and item.get("source_counts", {}).get("quotes")
                and item.get("source_counts", {}).get("orders")
            ][:8],
            "which_accounts_need_feedback_before_repeat": [
                item for item in items if item.get("repeat_business_signal") == "resolve_feedback_first"
            ][:8],
        },
        "next_action": "Use Account 360 to choose the next customer follow-up, quote/order review, feedback resolution, or repeat-business motion.",
        "safety": _safety_flags(),
    }


def _build_account_360_intelligence(
    db: Session,
    account_lifecycle: list[CustomerAccountExecutionItem],
    customer_value: list[dict[str, object]],
) -> list[dict[str, object]]:
    account_payload = build_account_360_intelligence(db, limit=16)
    if account_payload.get("items"):
        return list(account_payload["items"])
    value_by_name = {str(item.get("customer_name")): item for item in customer_value}
    items: list[dict[str, object]] = []
    for account in account_lifecycle[:16]:
        value = value_by_name.get(account.customer_name, {})
        items.append(
            {
                "account_key": account.account_key,
                "customer_name": account.customer_name,
                "current_stage": account.current_stage,
                "source_counts": account.source_counts,
                "commercial_value": {
                    "historical_quote_amount": value.get("historical_quote_amount", 0),
                    "won_order_amount": value.get("won_order_amount", 0),
                    "conversion_rate": value.get("conversion_rate", 0),
                    "repeat_business_count": value.get("repeat_business_count", 0),
                    "strategic_value": value.get("strategic_value", "unknown"),
                },
                "active_paths": account.active_paths,
                "open_blockers": account.open_blockers,
                "next_action": account.next_action,
                "decision_reason": account.decision_reason,
                "path": account.active_paths[0] if account.active_paths else "/",
                "safety": _safety_flags(),
            }
        )
    return items


def _build_commercial_intelligence(
    db: Session,
    account_lifecycle: list[CustomerAccountExecutionItem],
    opportunities: list[OpportunityPipelineItem],
    quotations: list[QuotationIntelligenceItem],
    products: list[ProductIntelligenceItem],
) -> CommercialIntelligenceOut:
    customer_value = _build_customer_value_intelligence(db)
    return CommercialIntelligenceOut(
        win_loss=_build_win_loss_intelligence(db),
        customer_value=customer_value,
        partner_performance=_build_partner_performance_intelligence(db),
        product_market_fit=_build_product_market_fit_intelligence(db, products, quotations),
        revenue_forecast=_build_revenue_forecast_intelligence(opportunities, quotations, db),
        account_360=_build_account_360_intelligence(db, account_lifecycle, customer_value),
    )


def _build_executive_decisions(
    account_lifecycle: list[CustomerAccountExecutionItem],
    lifecycle: list[CustomerLifecycleItem],
    opportunities: list[OpportunityPipelineItem],
    quotations: list[QuotationIntelligenceItem],
    products: list[ProductIntelligenceItem],
    partners: list[PartnerIntelligenceItem],
    delivery: list[DeliveryVisibilityItem],
) -> list[ExecutiveDecisionItem]:
    items: list[ExecutiveDecisionItem] = []
    account_gap = next((row for row in account_lifecycle if row.open_blockers), None)
    if account_gap:
        items.append(
            ExecutiveDecisionItem(
                decision_id="account-lifecycle-next-action",
                question="Which customer account needs the next coordinated action?",
                answer=f"{account_gap.customer_name}: {account_gap.current_stage}; {account_gap.open_blockers[0]}.",
                priority=account_gap.priority,
                owner=account_gap.owner or "account owner",
                next_action=account_gap.next_action,
                path=account_gap.active_paths[0] if account_gap.active_paths else "/",
            )
        )
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
    partner_gap = next(
        (
            row
            for row in partners
            if "gaps" in row.readiness_level
            or row.capability_intelligence.get("investment_priority") == "P1"
            or row.capability_intelligence.get("risk_signals")
        ),
        None,
    )
    if partner_gap:
        items.append(
            ExecutiveDecisionItem(
                decision_id="partner-investment-gap",
                question="Which partner needs resource before commercial pilot?",
                answer=(
                    f"{partner_gap.partner_name}: "
                    f"{partner_gap.capability_intelligence.get('business_focus') or partner_gap.readiness_level}; "
                    f"score {partner_gap.capability_intelligence.get('score', 'n/a')}."
                ),
                priority=partner_gap.capability_intelligence.get("investment_priority") or "P1",
                owner="partner owner",
                next_action=partner_gap.capability_intelligence.get("next_best_action") or partner_gap.next_action,
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
    account_lifecycle = _build_account_lifecycle(lifecycle)
    opportunities = _build_opportunities(db)
    quotations = _build_quotation_intelligence(db)
    products = _build_product_intelligence(db)
    partners = _build_partner_intelligence(db)
    delivery = _build_delivery_visibility(db)
    commercial = _build_commercial_intelligence(db, account_lifecycle, opportunities, quotations, products)
    decisions = _build_executive_decisions(account_lifecycle, lifecycle, opportunities, quotations, products, partners, delivery)

    return BusinessExecutionOut(
        summary=BusinessExecutionSummary(
            lifecycle_accounts=len(account_lifecycle),
            active_opportunities=len(opportunities),
            quote_learning_items=len([row for row in quotations if "missing" in row.learning_signal or row.version_count > 1]),
            delivery_risks=len([row for row in delivery if row.risk_level in {"high", "medium"}]),
            product_validation_items=len(products),
            partner_investment_items=len(
                [
                    row
                    for row in partners
                    if "gaps" in row.readiness_level
                    or "unknown" in row.risk_assessment
                    or row.capability_intelligence.get("investment_priority") == "P1"
                    or row.capability_intelligence.get("risk_signals")
                ]
            ),
            commercial_intelligence_items=(
                len(commercial.win_loss)
                + len(commercial.customer_value)
                + len(commercial.partner_performance)
                + len(commercial.product_market_fit)
                + len(commercial.account_360)
            ),
            executive_decisions=len(decisions),
        ),
        account_lifecycle=account_lifecycle,
        lifecycle=lifecycle,
        opportunities=opportunities,
        quotations=quotations,
        products=products,
        partners=partners,
        delivery=delivery,
        commercial_intelligence=commercial,
        executive_decisions=decisions,
        safety=_safety_flags(),
    )
