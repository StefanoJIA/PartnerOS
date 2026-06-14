"""Daily operating decision queue for internal PartnerOS users.

The queue derives priority from existing internal records only. It does not
send external messages, update source records, validate staging, or store
secrets.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from urllib.parse import urlencode

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import DailyQueueHandlingRecord, FeedbackTicket, User
from app.schemas.dashboard_actions import (
    DailyDecisionQueueItem,
    DailyDecisionQueueOut,
    DailyDecisionQueueSummary,
    DailyQueueHandlingRecordOut,
    DailyQueueHandlingUpdate,
)
from app.services.dashboard_actions import build_dashboard_actions
from app.services.external_execution import build_external_execution_console
from app.services.market_response_reviews import build_market_response_review_console
from app.services.partner_onboarding import build_partner_onboarding

ALLOWED_HANDLING_ACTIONS = {
    "acknowledge",
    "assign",
    "defer",
    "mark_blocked",
    "add_note",
    "set_follow_up",
    "record_decision",
    "wait_external",
}

ALLOWED_HANDLING_STATUSES = {
    "new",
    "acknowledged",
    "in_progress",
    "deferred",
    "blocked",
    "waiting_external",
    "decision_recorded",
}

UNSAFE_HANDLING_STATUSES = {
    "approved",
    "complete",
    "completed",
    "response received",
    "staging_validated",
    "STAGING_VALIDATED",
    "d9_entered",
}

UNSAFE_TEXT_MARKERS = (
    "STAGING_VALIDATED",
    "raw token",
    "PORTAL_CUSTOMER_API_TOKEN=",
    "Bearer ",
    "sk-",
)


def _path(path: str, **query: str | None) -> str:
    clean = {key: value for key, value in query.items() if value}
    return f"{path}?{urlencode(clean)}" if clean else path


def _priority_rank(value: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(value, 9)


def _state_rank(value: str) -> int:
    return {
        "blocked": 0,
        "overdue": 1,
        "needs review": 2,
        "waiting_external": 3,
        "ready to send": 3,
        "draft": 4,
        "deferred": 4,
        "in_progress": 5,
        "acknowledged": 6,
        "waiting response": 5,
        "pending": 6,
    }.get(value, 9)


def _decision_id(prefix: str, value: object) -> str:
    return f"{prefix}:{value}"


def _handling_status_for_action(action: str, existing_status: str | None = None) -> str:
    if action == "acknowledge":
        return "acknowledged"
    if action in {"assign", "set_follow_up"}:
        return "in_progress"
    if action == "defer":
        return "deferred"
    if action == "mark_blocked":
        return "blocked"
    if action == "record_decision":
        return "decision_recorded"
    if action == "wait_external":
        return "waiting_external"
    return existing_status if existing_status in ALLOWED_HANDLING_STATUSES else "in_progress"


def _assert_safe_handling_text(*values: str | None) -> None:
    for value in values:
        if not value:
            continue
        for marker in UNSAFE_TEXT_MARKERS:
            if marker in value:
                raise ValueError(f"Unsafe handling text contains forbidden marker: {marker}")


def _append_event(record: DailyQueueHandlingRecord, user: User, body: DailyQueueHandlingUpdate) -> None:
    events = list(record.handling_events or [])
    events.append(
        {
            "at": datetime.now(timezone.utc).isoformat(),
            "actor_email": user.email,
            "action": body.action,
            "handling_status": record.handling_status,
            "owner": record.owner,
            "follow_up_date": record.follow_up_date.isoformat() if record.follow_up_date else None,
            "blocked_reason": body.blocked_reason,
            "internal_note": body.internal_note,
            "decision_summary": body.decision_summary,
        }
    )
    record.handling_events = events[-25:]
    record.action_count = (record.action_count or 0) + 1


def _handling_out(record: DailyQueueHandlingRecord) -> DailyQueueHandlingRecordOut:
    return DailyQueueHandlingRecordOut.model_validate(record)


def update_daily_queue_handling(
    db: Session,
    user: User,
    body: DailyQueueHandlingUpdate,
) -> DailyQueueHandlingRecordOut:
    if body.action not in ALLOWED_HANDLING_ACTIONS:
        raise ValueError(f"Unsupported handling action: {body.action}")
    if body.handling_status in UNSAFE_HANDLING_STATUSES:
        raise ValueError("Handling status cannot claim external approval, completion, staging validation, or response receipt.")
    if body.handling_status and body.handling_status not in ALLOWED_HANDLING_STATUSES:
        raise ValueError(f"Unsupported handling status: {body.handling_status}")

    _assert_safe_handling_text(
        body.owner,
        body.blocked_reason,
        body.internal_note,
        body.decision_summary,
        body.title,
        body.source_path,
    )

    record = (
        db.query(DailyQueueHandlingRecord)
        .filter(DailyQueueHandlingRecord.queue_item_id == body.queue_item_id)
        .first()
    )
    if record is None:
        record = DailyQueueHandlingRecord(
            queue_item_id=body.queue_item_id,
            created_by_id=user.id,
        )
        db.add(record)

    record.source_type = body.source_type
    record.source_id = body.source_id
    record.source_path = body.source_path
    record.title = body.title
    record.category = body.category
    record.priority = body.priority
    record.partner_focus = body.partner_focus
    record.product_focus = body.product_focus
    record.customer_or_account = body.customer_or_account
    record.owner = body.owner if body.owner is not None else record.owner
    record.handling_status = body.handling_status or _handling_status_for_action(body.action, record.handling_status)
    record.follow_up_date = body.follow_up_date if body.follow_up_date is not None else record.follow_up_date
    record.blocked_reason = body.blocked_reason if body.blocked_reason is not None else record.blocked_reason
    record.internal_note = body.internal_note if body.internal_note is not None else record.internal_note
    record.decision_summary = body.decision_summary if body.decision_summary is not None else record.decision_summary
    record.last_action = body.action
    record.updated_by_id = user.id
    _append_event(record, user, body)

    db.commit()
    db.refresh(record)
    return _handling_out(record)


def list_daily_queue_handling(db: Session) -> list[DailyQueueHandlingRecordOut]:
    rows = db.query(DailyQueueHandlingRecord).order_by(DailyQueueHandlingRecord.updated_at.desc()).limit(200).all()
    return [_handling_out(row) for row in rows]


def _risk_for_gap(gap: dict) -> str:
    if gap.get("work_state") == "blocked":
        return "blocked"
    if gap.get("affects_d9"):
        return "D9 gate risk"
    if gap.get("affects_pilot"):
        return "pilot readiness risk"
    return "operating gap"


def _gap_item(gap: dict) -> DailyDecisionQueueItem:
    readiness_impact: list[str] = []
    if gap.get("affects_d9"):
        readiness_impact.append("D9")
    if gap.get("affects_pilot"):
        readiness_impact.append("pilot")
    if gap.get("needs_staging_credentials"):
        readiness_impact.append("staging credentials")
    if gap.get("needs_business_signoff"):
        readiness_impact.append("business sign-off")
    if gap.get("needs_security_signoff"):
        readiness_impact.append("security sign-off")
    if gap.get("needs_partner_feedback"):
        readiness_impact.append("partner feedback")
    return DailyDecisionQueueItem(
        id=_decision_id("readiness-gap", gap["gap_id"]),
        title=f"推进 readiness 缺口：{gap['title']}",
        category="readiness gap",
        priority=gap.get("severity") or "P2",
        severity=gap.get("work_state") or "pending",
        owner=gap.get("owner"),
        partner_focus=gap.get("partner_focus"),
        product_focus=gap.get("product_focus") or [],
        readiness_impact=readiness_impact,
        risk=_risk_for_gap(gap),
        reason=gap.get("blocker_reason") or gap.get("evidence_required") or "Missing required evidence.",
        next_action=gap.get("next_action") or "Assign owner and next action.",
        source_type="readiness_gap",
        source_id=gap.get("gap_id"),
        source_path=_path("/external-execution", status="blocked" if gap.get("work_state") == "blocked" else None),
        depends_on_external_input=bool(
            gap.get("needs_staging_credentials")
            or gap.get("needs_business_signoff")
            or gap.get("needs_security_signoff")
            or gap.get("needs_partner_feedback")
        ),
        needs_business_signoff=bool(gap.get("needs_business_signoff")),
        needs_security_signoff=bool(gap.get("needs_security_signoff")),
        needs_partner_feedback=bool(gap.get("needs_partner_feedback")),
        needs_staging_credentials=bool(gap.get("needs_staging_credentials")),
        affects_d9=bool(gap.get("affects_d9")),
        affects_pilot=bool(gap.get("affects_pilot")),
        customer_safe_boundary=gap.get("customer_safe_boundary"),
    )


def _external_action_item(row: dict) -> DailyDecisionQueueItem:
    status = row.get("status") or "draft"
    priority = "P0" if status == "blocked" else "P1" if status in {"ready to send", "draft"} else "P2"
    external_input = status in {"sent manually", "response received", "blocked"} or bool(row.get("redacted_credential_status"))
    return DailyDecisionQueueItem(
        id=_decision_id("external-action", row["id"]),
        title=f"外部动作：{row.get('action_type')}",
        category="external execution",
        priority=priority,
        severity=status,
        owner=row.get("owner"),
        due_date=date.fromisoformat(row["due_date"]) if row.get("due_date") else None,
        partner_focus=row.get("partner_focus"),
        product_focus=row.get("product_focus") or [],
        readiness_impact=[value for value in [row.get("staging_readiness_key"), row.get("pilot_readiness_key")] if value],
        risk=row.get("blocker_notes") or row.get("dependency") or "manual external action needs follow-up",
        reason=row.get("notes") or row.get("dependency") or "Manual status requires owner follow-up.",
        next_action=row.get("next_step") or "Update owner, next step, due date, or real response summary.",
        source_type="external_action",
        source_id=row["id"],
        source_path=_path("/external-execution", status=status),
        depends_on_external_input=external_input,
        needs_business_signoff=row.get("action_type") == "business UAT / data sign-off request",
        needs_security_signoff=row.get("action_type") == "security review request",
        needs_partner_feedback=row.get("action_type") == "partner rehearsal request",
        needs_staging_credentials=row.get("action_type") == "staging credentials request",
        affects_d9=bool(row.get("staging_readiness_key")),
        affects_pilot=bool(row.get("pilot_readiness_key")),
        customer_safe_boundary="No automatic send; no raw token; no unconfirmed sign-off.",
    )


def _market_review_item(row: dict) -> DailyDecisionQueueItem:
    priority = row.get("priority") or "P2"
    visibility = row.get("visibility_class") or ""
    status = row.get("status") or "needs review"
    return DailyDecisionQueueItem(
        id=_decision_id("market-review", row["id"]),
        title=f"Market Response 审查：{row.get('review_dimension_label') or row.get('review_dimension')}",
        category="market response",
        priority=priority,
        severity=status if status == "blocked" else visibility,
        owner=row.get("owner"),
        due_date=date.fromisoformat(row["due_date"]) if row.get("due_date") else None,
        partner_focus=row.get("partner_focus"),
        product_focus=row.get("product_focus") or [],
        readiness_impact=["pilot", "customer-safe wording"] if visibility in {"needs validation", "pilot blocker", "customer-safe candidate"} else ["market response"],
        risk=row.get("source_summary") or "Market signal needs manual review.",
        reason=row.get("evidence_summary") or row.get("internal_notes") or "Review before using in customer-visible copy or pilot claims.",
        next_action=row.get("next_action") or "Classify visibility and decide whether this becomes customer-safe, internal-only, or pilot blocker.",
        source_type="market_response_review",
        source_id=row["id"],
        source_path=_path("/market-response", partner_focus=row.get("partner_focus"), status=row.get("status")),
        depends_on_external_input=row.get("source_type") in {"feedback", "market signal"} and row.get("visibility_class") == "pilot blocker",
        needs_business_signoff=visibility in {"customer-safe candidate", "needs validation", "pilot blocker"},
        needs_security_signoff=visibility in {"internal-only", "pilot blocker"},
        needs_partner_feedback=row.get("source_type") == "feedback",
        affects_pilot=priority in {"P0", "P1"} or visibility == "pilot blocker",
        customer_safe_boundary="Customer-safe candidate is not approved; internal-only and pilot blocker must not be customer-visible.",
    )


def _partner_onboarding_item(record) -> DailyDecisionQueueItem:
    missing = record.missing_items or []
    priority = "P0" if "portal_visibility_reviewed" in missing else "P1" if missing else "P3"
    impact: list[str] = []
    if "portal_visibility_reviewed" in missing:
        impact.append("customer-safe fields")
    if "pricing_basis_available" in missing or "quote_flow_ready" in missing:
        impact.append("quote readiness")
    if "production_shipment_flow_mapped" in missing:
        impact.append("delivery readiness")
    if "market_response_focus_defined" in missing:
        impact.append("Market Response metrics")
    if "demo_narrative_prepared" in missing:
        impact.append("partner rehearsal")
    if not impact:
        impact.append("partner onboarding")
    return DailyDecisionQueueItem(
        id=_decision_id("partner-onboarding", record.partner_id),
        title=f"Partner Onboarding 缺口：{record.partner_name}",
        category="partner onboarding",
        priority=priority,
        severity=record.onboarding_stage,
        owner="partner onboarding owner",
        partner_focus=record.partner_name,
        product_focus=record.product_focus,
        readiness_impact=impact,
        risk=record.readiness_summary,
        reason=", ".join(missing[:4]) if missing else "Partner is ready for active operating use.",
        next_action=record.next_action,
        source_type="partner_onboarding",
        source_id=str(record.partner_id),
        source_path="/partner-onboarding",
        depends_on_external_input=record.onboarding_stage == "discovery",
        needs_business_signoff=bool(missing),
        needs_partner_feedback="demo_narrative_prepared" in missing or "market_response_focus_defined" in missing,
        affects_pilot=bool(missing),
        customer_safe_boundary="Partner-specific fields must be reviewed before customer-visible Portal or pilot use.",
    )


def _order_item(row, kind: str, title: str, reason: str) -> DailyDecisionQueueItem:
    return DailyDecisionQueueItem(
        id=_decision_id(kind, row.id),
        title=title,
        category="order delivery",
        priority="P1",
        severity=row.risk_level or kind,
        owner="operator",
        due_date=row.target_delivery_date,
        readiness_impact=["Market Response", "customer-visible order status"],
        risk=reason,
        reason=f"Order {row.order_number} needs operational review before customer-visible status is updated.",
        next_action="Open order detail, review production/shipment/feedback summary, and update manual operating notes.",
        source_type=kind,
        source_id=str(row.id),
        source_path=f"/orders/{row.id}",
        affects_pilot=True,
        customer_safe_boundary="Do not expose internal delay attribution, supplier private notes, cost, or margin.",
    )


def _feedback_item(row: FeedbackTicket) -> DailyDecisionQueueItem:
    return DailyDecisionQueueItem(
        id=_decision_id("feedback-ticket", row.id),
        title=f"客户反馈待处理：{row.subject}",
        category="feedback",
        priority="P1" if row.priority in {"high", "urgent"} else "P2",
        severity=row.status,
        owner=row.internal_owner or "operator",
        customer_or_account=row.customer_name,
        readiness_impact=["Market Response", "customer Portal feedback"],
        risk=f"{row.priority} feedback / {row.feedback_type}",
        reason="Feedback should be triaged and reflected into Market Response when it changes product, delivery, or pilot risk.",
        next_action="Review ticket, update response summary, link order if relevant, and decide whether a Market Response review is needed.",
        source_type="feedback_ticket",
        source_id=str(row.id),
        source_path="/feedback-tickets",
        depends_on_external_input=False,
        needs_partner_feedback=False,
        affects_pilot=row.priority in {"high", "urgent"},
        customer_safe_boundary="Do not auto-reply; response summary is internal until reviewed.",
    )


def _summary(items: list[DailyDecisionQueueItem], user: User) -> DailyDecisionQueueSummary:
    today = date.today()
    return DailyDecisionQueueSummary(
        total=len(items),
        p0=sum(1 for item in items if item.priority == "P0"),
        p1=sum(1 for item in items if item.priority == "P1"),
        staging_or_d9=sum(1 for item in items if item.affects_d9 or "staging credentials" in item.readiness_impact),
        pilot=sum(1 for item in items if item.affects_pilot),
        external_input_required=sum(1 for item in items if item.depends_on_external_input),
        business_signoff_required=sum(1 for item in items if item.needs_business_signoff),
        security_signoff_required=sum(1 for item in items if item.needs_security_signoff),
        partner_feedback_required=sum(1 for item in items if item.needs_partner_feedback),
        order_or_feedback_risk=sum(1 for item in items if item.category in {"order delivery", "feedback"}),
        acknowledged=sum(1 for item in items if item.handling and item.handling.handling_status == "acknowledged"),
        in_progress=sum(1 for item in items if item.handling and item.handling.handling_status == "in_progress"),
        blocked=sum(1 for item in items if item.handling and item.handling.handling_status == "blocked"),
        deferred=sum(1 for item in items if item.handling and item.handling.handling_status == "deferred"),
        waiting_external=sum(1 for item in items if item.handling and item.handling.handling_status == "waiting_external"),
        overdue_followups=sum(
            1
            for item in items
            if item.handling and item.handling.follow_up_date is not None and item.handling.follow_up_date < today
        ),
        my_items=sum(1 for item in items if item.handling and item.handling.owner == user.email),
        status="READY_FOR_STAGING_HANDOFF",
        external_staging_state="WAITING_FOR_REAL_STAGING_EVIDENCE",
    )


def _sort_items(items: list[DailyDecisionQueueItem]) -> list[DailyDecisionQueueItem]:
    return sorted(
        items,
        key=lambda item: (
            _priority_rank(item.priority),
            _state_rank(item.severity),
            item.due_date or date.max,
            item.category,
            item.title,
        ),
    )


def _apply_handling_layer(db: Session, items: list[DailyDecisionQueueItem]) -> None:
    item_ids = [item.id for item in items]
    if not item_ids:
        return
    rows = (
        db.query(DailyQueueHandlingRecord)
        .filter(DailyQueueHandlingRecord.queue_item_id.in_(item_ids))
        .all()
    )
    handling_by_item = {row.queue_item_id: _handling_out(row) for row in rows}
    for item in items:
        item.handling = handling_by_item.get(item.id)


def build_daily_decision_queue(db: Session, user: User) -> DailyDecisionQueueOut:
    actions = build_dashboard_actions(db, user)
    external = build_external_execution_console(db, user)
    market_reviews = build_market_response_review_console(db, user)
    partner_onboarding = build_partner_onboarding(db)

    items: list[DailyDecisionQueueItem] = []
    for gap in external.get("readiness_gap_intelligence") or []:
        if gap.get("severity") in {"P0", "P1"} or gap.get("affects_d9") or gap.get("affects_pilot"):
            items.append(_gap_item(gap))

    for row in external.get("actions") or []:
        if row.get("status") in {"blocked", "draft", "ready to send", "sent manually", "response received"}:
            items.append(_external_action_item(row))

    for row in market_reviews.get("reviews") or []:
        if row.get("priority") in {"P0", "P1"} or row.get("status") in {"blocked", "needs review"}:
            items.append(_market_review_item(row))

    for record in partner_onboarding.items:
        if record.missing_items:
            items.append(_partner_onboarding_item(record))

    for row in actions.high_risk_orders[:5]:
        items.append(_order_item(row, "high_risk_order", f"高风险订单：{row.order_number}", "High-risk order may affect delivery confidence."))
    for row in actions.orders_eta_missing[:5]:
        items.append(_order_item(row, "eta_missing_order", f"订单缺少 ETA / 物流记录：{row.order_number}", "Near-term delivery order lacks shipment visibility."))
    for row in actions.orders_eta_passed_not_delivered[:5]:
        items.append(_order_item(row, "eta_passed_order", f"ETA 已过但未交付：{row.order_number}", "Shipment ETA has passed without delivered status."))

    feedback_rows = (
        db.query(FeedbackTicket)
        .filter(
            or_(
                FeedbackTicket.status.in_(("new", "in_review")),
                FeedbackTicket.priority.in_(("high", "urgent")),
            )
        )
        .order_by(FeedbackTicket.priority.desc(), FeedbackTicket.created_at.desc())
        .limit(8)
        .all()
    )
    items.extend(_feedback_item(row) for row in feedback_rows)

    _apply_handling_layer(db, items)
    sorted_items = _sort_items(items)[:40]
    return DailyDecisionQueueOut(
        summary=_summary(sorted_items, user),
        items=sorted_items,
        safety={
            "manual_only": True,
            "email_sent": False,
            "sms_sent": False,
            "linkedin_sent": False,
            "customer_notified": False,
            "supplier_notified": False,
            "external_api_called": False,
            "raw_token_recorded": False,
            "staging_validated": False,
            "d9_entered": False,
            "quote_status_changed": False,
            "order_status_changed": False,
        },
    )
