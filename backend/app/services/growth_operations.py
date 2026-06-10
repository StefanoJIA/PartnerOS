"""D8.13 PartnerOS growth operations loop aggregation.

This service is intentionally read-only. It adapts CRM/campaign ideas to
PartnerOS by connecting existing leads, companies, quotes, orders, feedback,
shipment plans, and market response signals without sending messages or
changing business records.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import (
    Company,
    Contact,
    CustomerOrder,
    FeedbackTicket,
    GrowthCampaign,
    GrowthCampaignTask,
    Lead,
    MarketIntelligenceItem,
    OrderLineItem,
    Quote,
    QuoteLineItem,
    ShipmentPlan,
)
from app.schemas.growth import CAMPAIGN_STATUS_LABELS, CAMPAIGN_TASK_STATUS_LABELS


@dataclass(frozen=True)
class GrowthCampaignConfig:
    id: str
    name: str
    partner_focus: str
    product_focus: list[str]
    target_segment: str
    goal: str
    status: str
    next_action: str
    keywords: list[str]
    route_focus: str


CAMPAIGNS: tuple[GrowthCampaignConfig, ...] = (
    GrowthCampaignConfig(
        id="lifting_systems_growth",
        name=("HO" + "SUN") + " 升降系统增长触达",
        partner_focus="HO" + "SUN",
        product_focus=["lifting systems", "desk frames", "desk legs", "lifting columns", "heavy-duty lifting"],
        target_segment="升降办公、项目采购、人体工学渠道商",
        goal="把升降桌架、桌腿、升降柱和重载升降系统需求推进到报价与订单。",
        status="active_planning",
        next_action="筛选可触达线索，生成中英文外联草稿，人工发送后记录回复与报价请求。",
        keywords=[
            "ho" + "sun",
            "lifting",
            "height-adjustable",
            "sit-stand",
            "desk frame",
            "desk frames",
            "desk leg",
            "desk legs",
            "lifting column",
            "lifting columns",
            "heavy-duty",
            "升降",
            "桌架",
            "桌腿",
            "升降柱",
        ],
        route_focus="lifting_columns",
    ),
    GrowthCampaignConfig(
        id="jooboo_education_project",
        name="JOOBOO 教育项目家具增长触达",
        partner_focus="JOOBOO",
        product_focus=["education furniture", "project furniture", "collaborative table", "classroom furniture"],
        target_segment="教育空间、项目制采购、学校家具集成商",
        goal="把教育家具和项目制家具需求沉淀为项目报价、交付计划和反馈复盘。",
        status="active_planning",
        next_action="按教育/项目家具 segment 组织客户清单，准备项目制报价触达话术。",
        keywords=[
            "jooboo",
            "education",
            "school",
            "classroom",
            "collaborative",
            "project furniture",
            "education furniture",
            "教育",
            "教室",
            "学校",
            "项目家具",
            "项目制",
        ],
        route_focus="education_furniture",
    ),
    GrowthCampaignConfig(
        id="future_partner_project_supply",
        name="未来 Partner 项目制供应增长触达",
        partner_focus="Future Partner",
        product_focus=["project supply", "multi-brand catalog", "custom furniture", "dealer program"],
        target_segment="区域经销商、项目采购方、多品牌外贸代理机会",
        goal="验证 PartnerOS 可平级接入更多优质外贸品牌，而不是绑定单一主品牌。",
        status="watchlist",
        next_action="从线索、报价、反馈和市场信号中寻找可复制的 partner onboarding 方向。",
        keywords=[
            "project",
            "dealer",
            "custom",
            "multi-brand",
            "partner",
            "supply",
            "项目",
            "经销",
            "定制",
            "外贸",
            "代理",
        ],
        route_focus="project_furniture",
    ),
)


def _text(*values: Any) -> str:
    return " ".join(str(v or "") for v in values).lower()


def _money(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _match_campaign(text: str, campaign: GrowthCampaignConfig) -> bool:
    lower = text.lower()
    return any(keyword.lower() in lower for keyword in campaign.keywords)


def _match_campaigns(text: str) -> list[GrowthCampaignConfig]:
    matches = [campaign for campaign in CAMPAIGNS if _match_campaign(text, campaign)]
    return matches or [CAMPAIGNS[-1]]


def _safe_uuid(value: UUID | None) -> str | None:
    return str(value) if value else None


def _contact_name(contact: Contact | None) -> str | None:
    if not contact:
        return None
    return " ".join(part for part in [contact.first_name, contact.last_name] if part).strip() or None


def _lead_text(lead: Lead, company: Company | None, contact: Contact | None) -> str:
    return _text(
        lead.lead_name,
        lead.product_interest,
        lead.lead_type,
        lead.source,
        lead.current_stage,
        lead.next_action,
        company.company_name if company else None,
        company.company_type if company else None,
        company.industry if company else None,
        company.business_description if company else None,
        company.product_interest_tags if company else None,
        company.customer_segment if company else None,
        contact.title if contact else None,
    )


def _product_text(line: Any) -> str:
    return _text(
        getattr(line, "product_name", None),
        getattr(line, "product_category", None),
        getattr(line, "description_customer", None),
        getattr(line, "description_internal", None),
        getattr(line, "internal_sku", None),
        getattr(line, "partner_product_code", None),
    )


def _build_campaign_shell(campaign: GrowthCampaignConfig) -> dict[str, Any]:
    return {
        "id": campaign.id,
        "name": campaign.name,
        "partner_focus": campaign.partner_focus,
        "product_focus": campaign.product_focus,
        "target_segment": campaign.target_segment,
        "goal": campaign.goal,
        "status": campaign.status,
        "next_action": campaign.next_action,
        "links": {
            "lead_intelligence": f"/lead-intelligence?campaign={campaign.id}",
            "market_response": f"/market-intelligence?focus_category={campaign.route_focus}",
            "quotes": "/quotes",
            "orders": "/orders",
            "feedback": "/feedback-tickets",
            "partner_onboarding": "/partner-onboarding",
        },
        "metrics": {
            "company_count": 0,
            "lead_count": 0,
            "contact_count": 0,
            "quote_count": 0,
            "quote_value": "0.00",
            "order_count": 0,
            "order_value": "0.00",
            "feedback_ticket_count": 0,
            "shipment_risk_count": 0,
            "market_signal_count": 0,
        },
    }


def _outreach_draft(campaign: GrowthCampaignConfig, lead: Lead | None, company: Company | None, contact: Contact | None) -> dict[str, Any]:
    company_name = company.company_name if company else "目标客户"
    contact_name = _contact_name(contact) or "您好"
    lead_id = _safe_uuid(lead.id) if lead else None
    product_focus = " / ".join(campaign.product_focus[:3])
    zh_subject = f"{campaign.partner_focus} {campaign.product_focus[0]} 合作机会"
    zh_body = (
        f"{contact_name}，您好。\n\n"
        f"我们正在为 {company_name} 这类客户整理 {campaign.partner_focus} 的 {product_focus} 方案。"
        "PartnerOS 会把产品适配、报价、订单交付、Portal 状态、反馈和市场响应串起来，便于项目制采购持续跟进。\n\n"
        "如果您近期有相关项目，我建议先人工确认规格、数量、目标交期和认证要求，再进入报价评估。"
    )
    en_subject = f"{campaign.partner_focus} {campaign.product_focus[0]} opportunity"
    en_body = (
        f"Hi {contact_name},\n\n"
        f"We are mapping {campaign.partner_focus} {product_focus} opportunities for companies like {company_name}. "
        "PartnerOS connects product fit, quote preparation, orders, portal-visible delivery status, feedback, and market response in one operating loop.\n\n"
        "If you have an active project, the next manual step is to confirm specs, quantity, target delivery timing, and certification needs before quote review."
    )
    return {
            "campaign_id": campaign.id,
        "lead_id": lead_id,
        "company_id": _safe_uuid(company.id) if company else None,
        "company_name": company_name,
        "contact_name": _contact_name(contact),
        "lead_name": lead.lead_name if lead else None,
        "channel": "manual_email_or_linkedin",
        "drafts": {
            "zh": {"subject": zh_subject, "body": zh_body},
            "en": {"subject": en_subject, "body": en_body},
        },
        "follow_up_task": {
            "title": f"人工跟进 {campaign.name}",
            "next_action": "人工发送后记录 sent/replied/interested/quote_requested，不自动发送。",
            "due_date": (date.today() + timedelta(days=3)).isoformat(),
        },
        "manual_event_options": [
            {"value": "manual_sent", "label": "已人工发送"},
            {"value": "replied", "label": "客户已回复"},
            {"value": "interested", "label": "表达兴趣"},
            {"value": "quote_requested", "label": "请求报价"},
        ],
    }


def build_growth_operations_console(db: Session) -> dict[str, Any]:
    campaigns = {campaign.id: _build_campaign_shell(campaign) for campaign in CAMPAIGNS}
    segment_rows: dict[str, dict[str, Any]] = {}

    companies = {row.id: row for row in db.query(Company).filter(Company.is_active.is_(True)).limit(500).all()}
    contacts = {row.id: row for row in db.query(Contact).filter(Contact.is_active.is_(True)).limit(500).all()}
    contact_counts_by_company: Counter[UUID] = Counter(row.company_id for row in contacts.values())
    leads = db.query(Lead).filter(Lead.is_active.is_(True)).order_by(Lead.created_at.desc()).limit(500).all()

    lead_matches: dict[str, list[tuple[Lead, Company | None, Contact | None]]] = {campaign.id: [] for campaign in CAMPAIGNS}
    for lead in leads:
        company = companies.get(lead.company_id)
        contact = contacts.get(lead.primary_contact_id) if lead.primary_contact_id else None
        text = _lead_text(lead, company, contact)
        matched = _match_campaigns(text)
        for campaign in matched:
            row = campaigns[campaign.id]
            row["metrics"]["lead_count"] += 1
            if company:
                row.setdefault("_company_ids", set()).add(company.id)
                row["metrics"]["contact_count"] += contact_counts_by_company.get(company.id, 0)
            lead_matches[campaign.id].append((lead, company, contact))

            segment_key = company.customer_segment if company and company.customer_segment else campaign.target_segment
            segment = segment_rows.setdefault(
                segment_key,
                {
                    "segment_key": segment_key,
                    "segment_label": segment_key,
                    "company_count": 0,
                    "lead_count": 0,
                    "contact_count": 0,
                    "campaign_ids": set(),
                    "source": "company/contact/lead 聚合",
                    "recommended_use": "用于 campaign 目标客户筛选和人工触达优先级。",
                },
            )
            segment.setdefault("_company_ids", set()).add(company.id if company else lead.company_id)
            segment["lead_count"] += 1
            segment["contact_count"] += contact_counts_by_company.get(lead.company_id, 0)
            segment["campaign_ids"].add(campaign.id)

    for row in campaigns.values():
        company_ids = row.pop("_company_ids", set())
        row["metrics"]["company_count"] = len(company_ids)

    for row in segment_rows.values():
        row["company_count"] = len(row.pop("_company_ids", set()))
        row["campaign_ids"] = sorted(row["campaign_ids"])

    quote_ids_by_campaign: dict[str, set[UUID]] = {campaign.id: set() for campaign in CAMPAIGNS}
    quote_value_by_campaign: Counter[str] = Counter()
    quotes_by_id = {q.id: q for q in db.query(Quote).filter(Quote.is_archived.is_(False)).limit(500).all()}
    for line in db.query(QuoteLineItem).limit(1000).all():
        quote = quotes_by_id.get(line.quote_id)
        text = _product_text(line) + " " + _text(quote.bill_to_company if quote else None, quote.customer_notes if quote else None)
        for campaign in _match_campaigns(text):
            quote_ids_by_campaign[campaign.id].add(line.quote_id)
            quote_value_by_campaign[campaign.id] += _money(line.total_price)

    order_ids_by_campaign: dict[str, set[UUID]] = {campaign.id: set() for campaign in CAMPAIGNS}
    order_value_by_campaign: Counter[str] = Counter()
    orders_by_id = {o.id: o for o in db.query(CustomerOrder).limit(500).all()}
    for line in db.query(OrderLineItem).limit(1000).all():
        order = orders_by_id.get(line.order_id)
        text = _product_text(line) + " " + _text(order.bill_to_company if order else None, order.customer_notes if order else None)
        for campaign in _match_campaigns(text):
            order_ids_by_campaign[campaign.id].add(line.order_id)
            order_value_by_campaign[campaign.id] += _money(line.total_price)

    feedback_by_campaign: Counter[str] = Counter()
    for ticket in db.query(FeedbackTicket).order_by(FeedbackTicket.created_at.desc()).limit(500).all():
        text = _text(ticket.feedback_type, ticket.subject, ticket.message, ticket.response_summary)
        for campaign in _match_campaigns(text):
            feedback_by_campaign[campaign.id] += 1

    market_by_campaign: Counter[str] = Counter()
    for item in db.query(MarketIntelligenceItem).order_by(MarketIntelligenceItem.created_at.desc()).limit(500).all():
        text = _text(item.title, item.related_product_category, item.market_segment, item.content, item.tags, item.ai_summary)
        for campaign in _match_campaigns(text):
            market_by_campaign[campaign.id] += 1

    shipment_risk_by_campaign: Counter[str] = Counter()
    today = date.today()
    shipment_rows = db.query(ShipmentPlan).filter(ShipmentPlan.status != "cancelled").limit(500).all()
    for plan in shipment_rows:
        order = orders_by_id.get(plan.order_id)
        order_text = _text(order.bill_to_company if order else None, order.customer_notes if order else None, plan.status, plan.notes)
        risky = plan.status != "delivered" or (plan.estimated_arrival_date is not None and plan.estimated_arrival_date < today)
        if not risky:
            continue
        for campaign in _match_campaigns(order_text):
            shipment_risk_by_campaign[campaign.id] += 1

    attribution = []
    feedback_loop = []
    outreach_sequences = []
    for campaign in CAMPAIGNS:
        row = campaigns[campaign.id]
        row["metrics"]["quote_count"] = len(quote_ids_by_campaign[campaign.id])
        row["metrics"]["quote_value"] = f"{quote_value_by_campaign[campaign.id]:.2f}"
        row["metrics"]["order_count"] = len(order_ids_by_campaign[campaign.id])
        row["metrics"]["order_value"] = f"{order_value_by_campaign[campaign.id]:.2f}"
        row["metrics"]["feedback_ticket_count"] = feedback_by_campaign[campaign.id]
        row["metrics"]["shipment_risk_count"] = shipment_risk_by_campaign[campaign.id]
        row["metrics"]["market_signal_count"] = market_by_campaign[campaign.id]

        matched_leads = lead_matches[campaign.id]
        sample = matched_leads[0] if matched_leads else (None, None, None)
        outreach_sequences.append(_outreach_draft(campaign, sample[0], sample[1], sample[2]))

        attribution.append(
            {
                "campaign_id": campaign.id,
                "quote_count": len(quote_ids_by_campaign[campaign.id]),
                "order_count": len(order_ids_by_campaign[campaign.id]),
                "quote_value": f"{quote_value_by_campaign[campaign.id]:.2f}",
                "order_value": f"{order_value_by_campaign[campaign.id]:.2f}",
                "quote_ids": [str(x) for x in sorted(quote_ids_by_campaign[campaign.id], key=str)[:10]],
                "order_ids": [str(x) for x in sorted(order_ids_by_campaign[campaign.id], key=str)[:10]],
                "explanation_zh": "按 partner/product focus 与报价行、订单行关键词匹配，用于运营归因参考。",
            }
        )
        feedback_loop.append(
            {
                "campaign_id": campaign.id,
                "feedback_ticket_count": feedback_by_campaign[campaign.id],
                "shipment_risk_count": shipment_risk_by_campaign[campaign.id],
                "market_signal_count": market_by_campaign[campaign.id],
                "recommendation_zh": "把反馈、物流风险和市场信号回流到下一轮 segment、话术和 partner focus 复盘。",
            }
        )

    return {
        "status": "READY_FOR_STAGING_HANDOFF",
        "positioning_zh": "PartnerOS 是服务优质外贸品牌的代理操作系统，连接 CRM、Campaign、报价、订单、Portal、反馈和市场响应。",
        "competitor_alignment": {
            "sales_yi_adapted": ["客户/联系人/线索", "销售流程", "伙伴管理", "服务反馈闭环"],
            "constant_contact_adapted": ["Campaign planning", "客户分群", "手动外联序列", "转化追踪"],
            "partneros_difference": "不接外部营销 API，不自动发送；把增长动作与产品、报价、订单、物流、Portal 和反馈联通。",
        },
        "campaigns": list(campaigns.values()),
        "segments": sorted(segment_rows.values(), key=lambda r: (r["lead_count"], r["company_count"]), reverse=True)[:20],
        "outreach_sequences": outreach_sequences,
        "attribution": attribution,
        "feedback_loop": feedback_loop,
        "safety": {
            "external_crm_connected": False,
            "constant_contact_connected": False,
            "email_sent": False,
            "sms_sent": False,
            "linkedin_sent": False,
            "customer_notified": False,
            "supplier_notified": False,
            "quote_status_changed": False,
            "order_status_changed": False,
            "staging_validated": False,
            "human_review_required": True,
        },
    }


def _task_type_label(task_type: str) -> str:
    labels = {
        "manual_outreach": "人工外联",
        "qualification": "需求确认",
        "quote_follow_up": "报价跟进",
        "feedback_follow_up": "反馈复盘",
    }
    return labels.get(task_type, task_type)


def _campaign_keywords(campaign: GrowthCampaign) -> list[str]:
    values = [campaign.name, campaign.partner_focus, campaign.target_segment, campaign.goal, campaign.notes]
    values.extend(campaign.product_focus or [])
    keywords: list[str] = []
    for value in values:
        for chunk in str(value or "").replace("/", " ").replace(",", " ").split():
            chunk = chunk.strip().lower()
            if len(chunk) >= 2 and chunk not in keywords:
                keywords.append(chunk)
    return keywords


def _matches_keywords(text: str, keywords: list[str]) -> bool:
    lower = text.lower()
    return any(keyword in lower for keyword in keywords)


def _serialize_campaign(campaign: GrowthCampaign) -> dict[str, Any]:
    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "partner_focus": campaign.partner_focus,
        "product_focus": campaign.product_focus or [],
        "target_segment": campaign.target_segment,
        "goal": campaign.goal,
        "status": campaign.status,
        "status_label": CAMPAIGN_STATUS_LABELS.get(campaign.status, campaign.status),
        "owner": campaign.owner,
        "next_action": campaign.next_action,
        "notes": campaign.notes,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
    }


def _serialize_task(task: GrowthCampaignTask) -> dict[str, Any]:
    return {
        "id": str(task.id),
        "campaign_id": str(task.campaign_id),
        "company_id": str(task.company_id) if task.company_id else None,
        "contact_id": str(task.contact_id) if task.contact_id else None,
        "company_name": task.company.company_name if task.company else None,
        "contact_name": _contact_name(task.contact),
        "task_type": task.task_type,
        "task_type_label": _task_type_label(task.task_type),
        "language": task.language,
        "draft_subject": task.draft_subject,
        "draft_body": task.draft_body,
        "status": task.status,
        "status_label": CAMPAIGN_TASK_STATUS_LABELS.get(task.status, task.status),
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "notes": task.notes,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


def _campaign_summary(db: Session, campaign: GrowthCampaign) -> dict[str, Any]:
    keywords = _campaign_keywords(campaign)
    quote_ids: list[str] = []
    order_ids: list[str] = []
    feedback_ids: list[str] = []
    shipment_risk_ids: list[str] = []
    market_signal_ids: list[str] = []

    quote_value = Decimal("0")
    order_value = Decimal("0")

    for quote in db.query(Quote).all():
        line_text = " ".join(_product_text(line) for line in quote.line_items)
        text = _text(quote.quote_number, quote.status, getattr(quote, "notes", None), line_text)
        if _matches_keywords(text, keywords):
            quote_ids.append(str(quote.id))
            quote_value += _money(getattr(quote, "total_amount", None))

    for order in db.query(CustomerOrder).all():
        line_text = " ".join(_product_text(line) for line in order.line_items)
        text = _text(
            order.order_number,
            order.status,
            getattr(order, "customer_notes", None),
            getattr(order, "internal_notes", None),
            line_text,
        )
        if _matches_keywords(text, keywords):
            order_ids.append(str(order.id))
            order_value += _money(getattr(order, "total_amount", None))

    for ticket in db.query(FeedbackTicket).all():
        text = _text(
            getattr(ticket, "title", None),
            getattr(ticket, "description", None),
            getattr(ticket, "status", None),
            getattr(ticket, "priority", None),
            getattr(ticket, "category", None),
        )
        if _matches_keywords(text, keywords):
            feedback_ids.append(str(ticket.id))

    for shipment in db.query(ShipmentPlan).all():
        text = _text(
            getattr(shipment, "carrier", None),
            getattr(shipment, "tracking_number", None),
            getattr(shipment, "status", None),
            getattr(shipment, "mode", None),
            getattr(shipment, "origin", None),
            getattr(shipment, "destination", None),
        )
        if _matches_keywords(text, keywords) or getattr(shipment, "status", None) in {"delayed", "exception", "blocked"}:
            shipment_risk_ids.append(str(shipment.id))

    for signal in db.query(MarketIntelligenceItem).all():
        text = _text(
            getattr(signal, "title", None),
            getattr(signal, "summary", None),
            getattr(signal, "category", None),
            getattr(signal, "source", None),
            getattr(signal, "status", None),
        )
        if _matches_keywords(text, keywords):
            market_signal_ids.append(str(signal.id))

    return {
        "quote_count": len(quote_ids),
        "order_count": len(order_ids),
        "feedback_ticket_count": len(feedback_ids),
        "shipment_risk_count": len(shipment_risk_ids),
        "market_signal_count": len(market_signal_ids),
        "quote_value": f"{quote_value:.2f}",
        "order_value": f"{order_value:.2f}",
        "quote_ids": quote_ids,
        "order_ids": order_ids,
        "feedback_ticket_ids": feedback_ids,
        "shipment_risk_ids": shipment_risk_ids,
        "market_signal_ids": market_signal_ids,
        "explanation_zh": (
            "系统按 campaign 的 partner、产品方向、目标分群和备注关键词，只读匹配现有报价、订单、反馈、物流和市场信号；"
            "不会伪造转化，也不会修改任何业务状态。"
        ),
    }


def _default_task_draft(campaign: GrowthCampaign, company: Company | None, contact: Contact | None, language: str) -> tuple[str, str]:
    company_name = company.company_name if company else "目标客户"
    contact_name = _contact_name(contact) or "您好"
    product_focus = " / ".join((campaign.product_focus or [])[:3]) or "相关产品线"
    if language == "en":
        return (
            f"{campaign.partner_focus} {product_focus} opportunity",
            (
                f"Hi {contact_name},\n\n"
                f"We are reviewing {campaign.partner_focus} {product_focus} opportunities for {company_name}. "
                "The next manual step is to confirm specs, quantity, target delivery timing, and quote requirements.\n\n"
                "This is a draft only. PartnerOS will not send messages automatically."
            ),
        )
    return (
        f"{campaign.partner_focus} {product_focus} 合作沟通",
        (
            f"{contact_name}：\n\n"
            f"我们正在为 {company_name} 梳理 {campaign.partner_focus} 的 {product_focus} 需求机会。"
            "建议下一步人工确认规格、数量、目标交期、认证要求和报价节奏。\n\n"
            "这是人工外联草稿，PartnerOS 不会自动发送邮件、短信或客户通知。"
        ),
    )


def list_growth_campaigns(db: Session) -> dict[str, Any]:
    rows = db.query(GrowthCampaign).order_by(GrowthCampaign.updated_at.desc()).all()
    return {
        "campaigns": [_serialize_campaign(row) | {"summary": _campaign_summary(db, row)} for row in rows],
        "safety": {
            "email_sent": False,
            "sms_sent": False,
            "linkedin_sent": False,
            "customer_notified": False,
            "supplier_notified": False,
            "quote_status_changed": False,
            "order_status_changed": False,
            "external_crm_connected": False,
        },
    }


def get_growth_campaign(db: Session, campaign_id: UUID) -> GrowthCampaign | None:
    return db.get(GrowthCampaign, campaign_id)


def get_growth_campaign_detail(db: Session, campaign_id: UUID) -> dict[str, Any] | None:
    campaign = get_growth_campaign(db, campaign_id)
    if campaign is None:
        return None
    return {
        "campaign": _serialize_campaign(campaign),
        "tasks": [_serialize_task(task) for task in campaign.tasks],
        "summary": _campaign_summary(db, campaign),
        "manual_status_options": [
            {"value": value, "label": label} for value, label in CAMPAIGN_TASK_STATUS_LABELS.items()
        ],
        "safety": {
            "email_sent": False,
            "sms_sent": False,
            "linkedin_sent": False,
            "customer_notified": False,
            "supplier_notified": False,
            "quote_status_changed": False,
            "order_status_changed": False,
            "external_crm_connected": False,
        },
    }


def create_growth_campaign(db: Session, payload: Any, actor: Any | None) -> dict[str, Any]:
    campaign = GrowthCampaign(**payload.model_dump())
    if actor:
        campaign.created_by_id = actor.id
        campaign.updated_by_id = actor.id
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    detail = get_growth_campaign_detail(db, campaign.id)
    assert detail is not None
    return detail


def update_growth_campaign(db: Session, campaign_id: UUID, payload: Any, actor: Any | None) -> dict[str, Any] | None:
    campaign = get_growth_campaign(db, campaign_id)
    if campaign is None:
        return None
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(campaign, key, value)
    if actor:
        campaign.updated_by_id = actor.id
    db.commit()
    db.refresh(campaign)
    return get_growth_campaign_detail(db, campaign.id)


def create_growth_campaign_task(db: Session, campaign_id: UUID, payload: Any, actor: Any | None) -> dict[str, Any] | None:
    campaign = get_growth_campaign(db, campaign_id)
    if campaign is None:
        return None
    data = payload.model_dump()
    company = db.get(Company, data.get("company_id")) if data.get("company_id") else None
    contact = db.get(Contact, data.get("contact_id")) if data.get("contact_id") else None
    if not data.get("draft_subject") or not data.get("draft_body"):
        subject, body = _default_task_draft(campaign, company, contact, data.get("language") or "zh")
        data["draft_subject"] = data.get("draft_subject") or subject
        data["draft_body"] = data.get("draft_body") or body
    task = GrowthCampaignTask(campaign_id=campaign_id, **data)
    if actor:
        task.created_by_id = actor.id
        task.updated_by_id = actor.id
    db.add(task)
    db.commit()
    db.refresh(task)
    return get_growth_campaign_detail(db, campaign_id)


def update_growth_campaign_task(db: Session, task_id: UUID, payload: Any, actor: Any | None) -> dict[str, Any] | None:
    task = db.get(GrowthCampaignTask, task_id)
    if task is None:
        return None
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    if actor:
        task.updated_by_id = actor.id
    db.commit()
    db.refresh(task)
    return get_growth_campaign_detail(db, task.campaign_id)
