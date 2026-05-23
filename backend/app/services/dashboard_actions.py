from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import (
    AIOutput,
    Interaction,
    Lead,
    Order,
    ProductionMilestone,
    RFQ,
    RFQPartnerCandidate,
    Sample,
    ShippingRecord,
    Task,
    User,
)
from app.models.enums import RFQStatus, RiskLevel, SampleStatus
from app.schemas.dashboard_actions import (
    AIOutputBrief,
    DashboardActionsOut,
    LeadActionBrief,
    OrderActionBrief,
    OrderMilestoneRisk,
    RecommendedAction,
    RFQActionBrief,
    SampleActionBrief,
    TaskActionBrief,
)


def _assignee_email(db: Session, uid: UUID | None) -> str | None:
    if not uid:
        return None
    u = db.query(User).filter(User.id == uid).first()
    return u.email if u else None


def _task_brief(db: Session, t: Task) -> TaskActionBrief:
    return TaskActionBrief(
        id=t.id,
        title=t.title,
        status=t.status,
        priority=t.priority,
        due_at=t.due_at,
        completed_at=t.completed_at,
        assignee_email=_assignee_email(db, t.assignee_user_id),
        related_object_type=t.related_object_type,
        related_object_id=t.related_object_id,
        created_at=t.created_at,
    )


def _lead_action_brief(l: Lead) -> LeadActionBrief:
    return LeadActionBrief(
        id=l.id,
        lead_name=l.lead_name,
        current_stage=l.current_stage,
        priority=l.priority,
        source=l.source,
        next_action_due_date=l.next_action_due_date,
        company_id=l.company_id,
    )


def _rfq_brief(r: RFQ) -> RFQActionBrief:
    return RFQActionBrief(
        id=r.id,
        rfq_number=r.rfq_number,
        status=r.status,
        lead_id=r.lead_id,
        company_id=r.company_id,
        updated_at=r.updated_at,
    )


def _sample_brief(s: Sample) -> SampleActionBrief:
    return SampleActionBrief(
        id=s.id,
        sample_request_number=s.sample_request_number,
        sample_status=s.sample_status,
        lead_id=s.lead_id,
        delivered_date=s.delivered_date,
        follow_up_due_date=s.follow_up_due_date,
    )


def _build_recommended(
    *,
    overdue: list[Task],
    followup_leads: list[Lead],
    stale_partner_rfqs: list[RFQ],
    samples_no_feedback: list[Sample],
    samples_follow_up_due: list[Sample],
    delayed_ms: list[tuple[Order, ProductionMilestone]],
    high_risk: list[Order],
    orders_eta_missing: list[Order],
    orders_eta_passed: list[Order],
) -> list[RecommendedAction]:
    out: list[RecommendedAction] = []
    if overdue:
        t = overdue[0]
        out.append(
            RecommendedAction(
                id=f"rec-overdue-task-{t.id}",
                title="优先处理逾期任务",
                message=f"有 {len(overdue)} 项任务已逾期，建议从「{t.title}」开始处理。",
                severity="high",
                object_type="task",
                object_id=t.id,
                path="/tasks",
            )
        )
    if followup_leads:
        l = followup_leads[0]
        out.append(
            RecommendedAction(
                id=f"rec-followup-lead-{l.id}",
                title="跟进已到期线索",
                message=f"线索「{l.lead_name}」的下一步动作日期已过，建议尽快联系。",
                severity="high",
                object_type="lead",
                object_id=l.id,
                path=f"/leads/{l.id}",
            )
        )
    if samples_no_feedback:
        s = samples_no_feedback[0]
        out.append(
            RecommendedAction(
                id=f"rec-sample-feedback-{s.id}",
                title="索取样品反馈",
                message=f"样品 {s.sample_request_number} 已送达但尚未记录客户反馈，可发送跟进邮件。",
                severity="medium",
                object_type="sample",
                object_id=s.id,
                path=f"/samples/{s.id}",
            )
        )
    if samples_follow_up_due:
        s = samples_follow_up_due[0]
        out.append(
            RecommendedAction(
                id=f"rec-sample-followup-due-{s.id}",
                title="样品跟进日期已到",
                message=f"样品 {s.sample_request_number} 已到跟进日期，建议查看状态并联系客户。",
                severity="medium",
                object_type="sample",
                object_id=s.id,
                path=f"/samples/{s.id}",
            )
        )
    if stale_partner_rfqs:
        r = stale_partner_rfqs[0]
        out.append(
            RecommendedAction(
                id=f"rec-rfq-partner-{r.id}",
                title="催促制造伙伴报价",
                message=f"RFQ {r.rfq_number} 等待伙伴报价已超过建议时限，建议联系相关 manufacturing partner。",
                severity="medium",
                object_type="rfq",
                object_id=r.id,
                path=f"/rfqs/{r.id}",
            )
        )
    if delayed_ms:
        o, m = delayed_ms[0]
        out.append(
            RecommendedAction(
                id=f"rec-order-milestone-{m.id}",
                title="订单节点延误",
                message=f"订单 {o.order_number} 的节点「{m.milestone_name}」已延误，建议准备客户进度说明或邮件。",
                severity="high",
                object_type="order",
                object_id=o.id,
                path=f"/orders/{o.id}",
            )
        )
    if high_risk:
        o = high_risk[0]
        out.append(
            RecommendedAction(
                id=f"rec-high-risk-order-{o.id}",
                title="高风险订单复核",
                message=f"订单 {o.order_number} 标记为高风险，建议复盘交期与客户沟通。",
                severity="high",
                object_type="order",
                object_id=o.id,
                path=f"/orders/{o.id}",
            )
        )
    if orders_eta_missing:
        o = orders_eta_missing[0]
        out.append(
            RecommendedAction(
                id=f"rec-order-ship-missing-{o.id}",
                title="临近交期但无海运记录",
                message=f"订单 {o.order_number} 目标交期临近，建议添加或完善海运记录与 ETA。",
                severity="medium",
                object_type="order",
                object_id=o.id,
                path=f"/orders/{o.id}",
            )
        )
    if orders_eta_passed:
        o = orders_eta_passed[0]
        out.append(
            RecommendedAction(
                id=f"rec-order-eta-passed-{o.id}",
                title="ETA 已过但未签收",
                message=f"订单 {o.order_number} 存在已过期的 ETA，建议与货代确认并更新客户。",
                severity="high",
                object_type="order",
                object_id=o.id,
                path=f"/orders/{o.id}",
            )
        )
    return out


def build_dashboard_actions(db: Session, user: User) -> DashboardActionsOut:
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    tomorrow = today_start + timedelta(days=1)
    week_start_date = now.date() - timedelta(days=now.weekday())
    week_start = datetime.combine(week_start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    week_end = week_start + timedelta(days=7)
    today_d = date.today()
    week_ago = now - timedelta(days=7)
    stale_quote_cutoff = now - timedelta(days=5)

    base_open = db.query(Task).filter(Task.is_active.is_(True), Task.status != "done")

    due_today_rows = (
        base_open.filter(Task.due_at.isnot(None), Task.due_at >= today_start, Task.due_at < tomorrow)
        .order_by(Task.due_at.asc())
        .limit(40)
        .all()
    )
    overdue_rows = (
        base_open.filter(Task.due_at.isnot(None), Task.due_at < now)
        .order_by(Task.due_at.asc())
        .limit(40)
        .all()
    )
    week_rows = (
        base_open.filter(Task.due_at.isnot(None), Task.due_at >= week_start, Task.due_at < week_end)
        .order_by(Task.due_at.asc())
        .limit(40)
        .all()
    )

    pl = func.lower(func.coalesce(Lead.priority, ""))
    hot_leads = (
        db.query(Lead)
        .filter(Lead.is_active.is_(True), pl == "high")
        .order_by(Lead.updated_at.desc())
        .limit(15)
        .all()
    )

    followup_today = (
        db.query(Lead)
        .filter(Lead.is_active.is_(True), Lead.next_action_due_date == today_d)
        .order_by(Lead.lead_name.asc())
        .limit(25)
        .all()
    )

    followup_leads = (
        db.query(Lead)
        .filter(
            Lead.is_active.is_(True),
            Lead.next_action_due_date.isnot(None),
            Lead.next_action_due_date < today_d,
        )
        .order_by(Lead.next_action_due_date.asc())
        .limit(20)
        .all()
    )

    recent_lead_ids = (
        db.query(Interaction.related_object_id)
        .filter(
            Interaction.related_object_type == "lead",
            Interaction.interaction_date >= week_ago,
        )
        .distinct()
        .limit(30)
        .all()
    )
    rid = [x[0] for x in recent_lead_ids]
    leads_recent = db.query(Lead).filter(Lead.id.in_(rid), Lead.is_active.is_(True)).limit(20).all() if rid else []

    leads_waiting = (
        db.query(Lead)
        .filter(
            Lead.is_active.is_(True),
            Lead.current_stage.notin_(["Won", "Lost", "Dormant"]),
            or_(Lead.next_action.isnot(None), Lead.ai_next_step_suggestion.isnot(None)),
        )
        .order_by(Lead.updated_at.desc())
        .limit(15)
        .all()
    )

    rfq_partner_wait_ids = {x[0] for x in db.query(RFQ.id).filter(RFQ.status == RFQStatus.waiting_partner_quote.value).all()}
    cand_wait_ids = {
        x[0]
        for x in db.query(RFQPartnerCandidate.rfq_id)
        .filter(
            RFQPartnerCandidate.partner_status == "Quote Requested",
            RFQPartnerCandidate.quote_received_at.is_(None),
        )
        .distinct()
        .all()
    }
    merged_ids = list(rfq_partner_wait_ids | cand_wait_ids)
    rfq_partner_wait = (
        db.query(RFQ).filter(RFQ.id.in_(merged_ids)).order_by(RFQ.updated_at.desc()).limit(20).all()
        if merged_ids
        else []
    )
    rfq_customer = (
        db.query(RFQ)
        .filter(RFQ.status == RFQStatus.customer_reviewing.value)
        .order_by(RFQ.updated_at.desc())
        .limit(15)
        .all()
    )
    rfq_neg = (
        db.query(RFQ)
        .filter(RFQ.status == RFQStatus.negotiating.value)
        .order_by(RFQ.updated_at.desc())
        .limit(15)
        .all()
    )

    stale_rfq_ids = (
        db.query(RFQ.id)
        .join(RFQPartnerCandidate, RFQPartnerCandidate.rfq_id == RFQ.id)
        .filter(
            RFQPartnerCandidate.quote_requested_at.isnot(None),
            RFQPartnerCandidate.quote_received_at.is_(None),
            RFQPartnerCandidate.quote_requested_at < stale_quote_cutoff,
        )
        .distinct()
        .limit(30)
        .all()
    )
    stale_rfqs = (
        db.query(RFQ).filter(RFQ.id.in_([x[0] for x in stale_rfq_ids])).all() if stale_rfq_ids else []
    )

    samples_req = (
        db.query(Sample)
        .filter(Sample.sample_status == SampleStatus.requested.value)
        .order_by(Sample.created_at.desc())
        .limit(15)
        .all()
    )
    samples_ship = (
        db.query(Sample)
        .filter(Sample.sample_status == SampleStatus.shipped.value)
        .order_by(Sample.updated_at.desc())
        .limit(15)
        .all()
    )
    samples_no_fb = (
        db.query(Sample)
        .filter(
            Sample.delivered_date.isnot(None),
            or_(Sample.customer_feedback.is_(None), Sample.customer_feedback == ""),
            Sample.sample_status != SampleStatus.feedback_received.value,
        )
        .order_by(Sample.delivered_date.desc())
        .limit(20)
        .all()
    )

    delayed_q = (
        db.query(Order, ProductionMilestone)
        .join(ProductionMilestone, ProductionMilestone.order_id == Order.id)
        .filter(
            ProductionMilestone.planned_date.isnot(None),
            ProductionMilestone.planned_date < today_d,
            ProductionMilestone.actual_date.is_(None),
        )
        .order_by(ProductionMilestone.planned_date.asc())
        .limit(25)
        .all()
    )
    orders_delayed: list[OrderMilestoneRisk] = []
    for o, m in delayed_q:
        orders_delayed.append(
            OrderMilestoneRisk(
                order_id=o.id,
                order_number=o.order_number,
                rfq_id=o.rfq_id,
                milestone_id=m.id,
                milestone_name=m.milestone_name,
                planned_date=m.planned_date,
                delay_days=m.delay_days,
                risk_level=o.risk_level,
            )
        )

    high_risk_orders = (
        db.query(Order)
        .filter(Order.risk_level == RiskLevel.high.value)
        .order_by(Order.updated_at.desc())
        .limit(15)
        .all()
    )

    ai_rows = (
        db.query(AIOutput)
        .filter(AIOutput.created_by_id == user.id)
        .order_by(AIOutput.created_at.desc())
        .limit(15)
        .all()
    )

    samples_follow_up_due_rows = (
        db.query(Sample)
        .filter(
            Sample.follow_up_due_date.isnot(None),
            Sample.follow_up_due_date <= today_d,
            Sample.sample_status.notin_([SampleStatus.closed.value, SampleStatus.converted.value]),
        )
        .order_by(Sample.follow_up_due_date.asc())
        .limit(20)
        .all()
    )

    ship_horizon = today_d + timedelta(days=21)
    near_orders = (
        db.query(Order)
        .filter(Order.target_delivery_date.isnot(None), Order.target_delivery_date <= ship_horizon)
        .order_by(Order.target_delivery_date.asc())
        .limit(50)
        .all()
    )
    orders_eta_missing_list: list[Order] = []
    for o in near_orders:
        if db.query(ShippingRecord).filter(ShippingRecord.order_id == o.id).count() == 0:
            orders_eta_missing_list.append(o)

    stale_eta_rows = (
        db.query(ShippingRecord, Order)
        .join(Order, ShippingRecord.order_id == Order.id)
        .filter(ShippingRecord.eta.isnot(None), ShippingRecord.eta < today_d)
        .limit(50)
        .all()
    )
    orders_eta_passed_list: list[Order] = []
    seen_ord: set[UUID] = set()
    for rec, o in stale_eta_rows:
        ds = (rec.delivery_status or "").lower()
        if ds in ("delivered", "final delivered"):
            continue
        if o.id not in seen_ord:
            seen_ord.add(o.id)
            orders_eta_passed_list.append(o)

    recommended = _build_recommended(
        overdue=overdue_rows,
        followup_leads=followup_leads,
        stale_partner_rfqs=stale_rfqs,
        samples_no_feedback=samples_no_fb,
        samples_follow_up_due=samples_follow_up_due_rows,
        delayed_ms=delayed_q,
        high_risk=high_risk_orders,
        orders_eta_missing=orders_eta_missing_list,
        orders_eta_passed=orders_eta_passed_list,
    )

    return DashboardActionsOut(
        due_today_tasks=[_task_brief(db, t) for t in due_today_rows],
        overdue_tasks=[_task_brief(db, t) for t in overdue_rows],
        this_week_tasks=[_task_brief(db, t) for t in week_rows],
        leads_follow_up_due_today=[_lead_action_brief(l) for l in followup_today],
        hot_leads=[_lead_action_brief(l) for l in hot_leads],
        leads_needing_follow_up=[_lead_action_brief(l) for l in followup_leads],
        leads_recent_activity=[_lead_action_brief(l) for l in leads_recent],
        leads_waiting_next_step=[_lead_action_brief(l) for l in leads_waiting],
        rfqs_waiting_partner_quote=[_rfq_brief(r) for r in rfq_partner_wait],
        rfqs_customer_reviewing=[_rfq_brief(r) for r in rfq_customer],
        rfqs_negotiating=[_rfq_brief(r) for r in rfq_neg],
        samples_requested=[_sample_brief(s) for s in samples_req],
        samples_shipped=[_sample_brief(s) for s in samples_ship],
        samples_delivered_no_feedback=[_sample_brief(s) for s in samples_no_fb],
        samples_follow_up_due=[_sample_brief(s) for s in samples_follow_up_due_rows],
        orders_delayed_milestones=orders_delayed,
        high_risk_orders=[
            OrderActionBrief(
                id=o.id,
                order_number=o.order_number,
                risk_level=o.risk_level,
                production_status=o.production_status,
                rfq_id=o.rfq_id,
                target_delivery_date=o.target_delivery_date,
                updated_at=o.updated_at,
            )
            for o in high_risk_orders
        ],
        orders_eta_missing=[
            OrderActionBrief(
                id=o.id,
                order_number=o.order_number,
                risk_level=o.risk_level,
                production_status=o.production_status,
                rfq_id=o.rfq_id,
                target_delivery_date=o.target_delivery_date,
                updated_at=o.updated_at,
            )
            for o in orders_eta_missing_list
        ],
        orders_eta_passed_not_delivered=[
            OrderActionBrief(
                id=o.id,
                order_number=o.order_number,
                risk_level=o.risk_level,
                production_status=o.production_status,
                rfq_id=o.rfq_id,
                target_delivery_date=o.target_delivery_date,
                updated_at=o.updated_at,
            )
            for o in orders_eta_passed_list
        ],
        recent_ai_outputs=[
            AIOutputBrief(
                id=a.id,
                task_type=a.task_type,
                status=a.status,
                input_object_type=a.input_object_type,
                input_object_id=a.input_object_id,
                created_at=a.created_at,
            )
            for a in ai_rows
        ],
        recommended_actions=recommended,
    )
