"""Internal external-execution collaboration workspace.

The service records manual follow-up state only. It never sends external
messages, never validates real staging by itself, and never stores raw tokens.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ExternalExecutionAction
from app.schemas.external_execution import EXTERNAL_ACTION_STATUS_LABELS


@dataclass(frozen=True)
class ExternalExecutionTemplate:
    action_type: str
    target_partner_system: str
    partner_focus: str | None
    product_focus: list[str]
    owner: str
    dependency: str
    next_step: str
    status: str
    notes: str
    staging_readiness_key: str | None = None
    pilot_readiness_key: str | None = None


DEFAULT_ACTIONS: tuple[ExternalExecutionTemplate, ...] = (
    ExternalExecutionTemplate(
        action_type="partner rehearsal request",
        target_partner_system=("HO" + "SUN") + " / JOOBOO / future partner",
        partner_focus="multi-partner",
        product_focus=[
            "lifting systems",
            "desk frames",
            "desk legs",
            "lifting columns",
            "heavy-duty supply",
            "education furniture",
            "project furniture",
        ],
        owner="业务负责人",
        dependency="partner rehearsal script + feedback form",
        next_step="人工发起 rehearsal 邀请；真实回复到位后录入 response_summary。",
        status="ready to send",
        notes="不自动发送邮件、短信、LinkedIn 或客户通知。",
        pilot_readiness_key="partner_feedback",
    ),
    ExternalExecutionTemplate(
        action_type="business UAT / data sign-off request",
        target_partner_system="Business owner",
        partner_focus="multi-partner",
        product_focus=["customer-visible fields", "UAT seed data", "customer-safe wording"],
        owner="业务负责人",
        dependency="UAT data selection + customer-safe wording checklist",
        next_step="确认 owner/date/scope 后再记录真实 business signoff；未签字保持 draft/blocked。",
        status="draft",
        notes="不得把 pending 写成 approved 或 complete。",
        staging_readiness_key="business_signoff",
        pilot_readiness_key="uat_data_approval",
    ),
    ExternalExecutionTemplate(
        action_type="security review request",
        target_partner_system="Security reviewer",
        partner_focus=None,
        product_focus=["token storage", "CORS", "forbidden fields", "rollback"],
        owner="安全审核人",
        dependency="security readiness checklist + forbidden field matrix",
        next_step="审核 token、allowed origins、customer-safe whitelist、日志和 rollback。",
        status="draft",
        notes="raw token 不得进入系统；只允许 PROVIDED_VIA_SECURE_CHANNEL 等脱敏状态。",
        staging_readiness_key="security_signoff",
    ),
    ExternalExecutionTemplate(
        action_type="staging credentials request",
        target_partner_system="PartnerOS backend / service.intelli-opus.com",
        partner_focus=None,
        product_focus=["backend HTTPS origin", "Portal origin", "PUBLIC_BASE_URL", "allowed origins"],
        owner="部署/Portal 负责人",
        dependency="secure channel + rollback owner",
        next_step="通过安全渠道接收凭证；系统只记录脱敏状态，不记录 token 原文。",
        status="blocked",
        notes="当前外部 staging 仍是 WAITING_FOR_REAL_STAGING_EVIDENCE。",
        staging_readiness_key="credentials",
    ),
    ExternalExecutionTemplate(
        action_type="staging smoke execution",
        target_partner_system="real staging",
        partner_focus=None,
        product_focus=["customer-safe payload", "forbidden fields", "rollback drill"],
        owner="联调负责人",
        dependency="credentials + security signoff + business signoff + UAT seed approval",
        next_step="真实 staging smoke 全部通过前，不得写 STAGING_VALIDATED，不得进入 D9。",
        status="blocked",
        notes="local dry-run、脚本通过、模板通过都不能替代真实 evidence。",
        staging_readiness_key="real_smoke_test",
    ),
)

STAGING_READINESS = (
    ("backend HTTPS origin", "pending external input", "需要真实 HTTPS 后端 origin。"),
    ("Portal origin", "pending external input", "需要 service.intelli-opus.com 真实 origin。"),
    ("PORTAL_CUSTOMER_API_TOKEN", "pending secure channel", "只记录 PROVIDED_VIA_SECURE_CHANNEL，不记录 token 原文。"),
    ("PORTAL_CUSTOMER_ALLOWED_ORIGINS", "pending external input", "必须明确 allowed origin，不能 wildcard。"),
    ("PUBLIC_BASE_URL", "pending external input", "需要与真实 staging 域名一致。"),
    ("security signoff", "pending", "需要 reviewer/date/scope。"),
    ("business signoff", "pending", "需要 owner/date/scope。"),
    ("UAT seed data approval", "pending", "需要业务签字确认 customer-safe 数据。"),
    ("real staging smoke test", "pending", "本地 dry-run 不能替代真实 evidence。"),
    ("rollback owner", "pending", "没有 rollback owner 不得进入 staging UAT。"),
    ("D9 entry gate", "blocked", "任一 P0 条件缺失都不得进入 D9。"),
)

LIFTING_SYSTEMS_FIELD_REVIEW = (
    ("load", "customer-safe candidate", "需要资料支持；未经业务确认不得给客户看。"),
    ("stability", "customer-safe candidate", "可转为 stability summary，raw test notes internal-only。"),
    ("noise", "needs validation", "noise claim 需要测试条件和业务话术确认。"),
    ("delivery", "customer-safe candidate", "只能展示预计交期或客户可接受表述。"),
    ("installation", "customer-safe candidate", "可展示安装摘要，内部责任归因不外露。"),
    ("after-sales", "customer-safe candidate", "可展示售后支持摘要。"),
    ("packaging", "customer-safe candidate", "可展示包装摘要，供应商备注 internal-only。"),
    ("warranty", "needs validation", "warranty summary 需要业务确认。"),
    ("test cycle", "needs validation", "测试周期需资料支持后才能 customer-visible。"),
    ("certification", "needs validation", "认证字段必须有材料支持。"),
    ("project demand", "customer-safe candidate", "项目制需求可高层展示，内部评分不外露。"),
)

PARTNER_COVERAGE = (
    {
        "partner": "HO" + "SUN",
        "focus": "lifting systems / desk frames / desk legs / lifting columns / heavy-duty supply",
        "rule": "技术声称必须区分 customer-safe candidate、needs validation、internal-only、pilot blocker。",
    },
    {
        "partner": "JOOBOO",
        "focus": "education furniture / school desks/chairs / project furniture",
        "rule": "关注 school procurement timing、delivery consistency、installation、resource needs、feedback after use、project acceptance criteria。",
    },
    {
        "partner": "future partner",
        "focus": "onboarding data / product family / quote logic / delivery requirement / resource taxonomy",
        "rule": "沿用同一闭环，但保留各自 customer-visible fields 和 Market Response metrics。",
    },
)


def _actor_id(actor: Any | None) -> Any | None:
    return getattr(actor, "id", None) if actor is not None else None


def _ensure_default_actions(db: Session, actor: Any | None = None) -> None:
    if db.query(ExternalExecutionAction).count():
        return
    actor_id = _actor_id(actor)
    for item in DEFAULT_ACTIONS:
        db.add(
            ExternalExecutionAction(
                action_type=item.action_type,
                target_partner_system=item.target_partner_system,
                partner_focus=item.partner_focus,
                product_focus=item.product_focus,
                owner=item.owner,
                dependency=item.dependency,
                next_step=item.next_step,
                status=item.status,
                notes=item.notes,
                staging_readiness_key=item.staging_readiness_key,
                pilot_readiness_key=item.pilot_readiness_key,
                created_by_id=actor_id,
                updated_by_id=actor_id,
            )
        )
    db.commit()


def _serialize_action(action: ExternalExecutionAction) -> dict[str, Any]:
    return {
        "id": str(action.id),
        "action_type": action.action_type,
        "target_partner_system": action.target_partner_system,
        "partner_focus": action.partner_focus,
        "product_focus": action.product_focus or [],
        "owner": action.owner,
        "due_date": action.due_date.isoformat() if action.due_date else None,
        "dependency": action.dependency,
        "next_step": action.next_step,
        "status": action.status,
        "status_label": EXTERNAL_ACTION_STATUS_LABELS.get(action.status, action.status),
        "response_summary": action.response_summary,
        "risk_notes": action.risk_notes,
        "blocker_notes": action.blocker_notes,
        "redacted_credential_status": action.redacted_credential_status,
        "staging_readiness_key": action.staging_readiness_key,
        "pilot_readiness_key": action.pilot_readiness_key,
        "notes": action.notes,
        "created_at": action.created_at.isoformat() if action.created_at else None,
        "updated_at": action.updated_at.isoformat() if action.updated_at else None,
    }


def safety_flags() -> dict[str, bool]:
    return {
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
    }


def build_external_execution_console(db: Session, actor: Any | None = None) -> dict[str, Any]:
    _ensure_default_actions(db, actor)
    rows = (
        db.query(ExternalExecutionAction)
        .order_by(ExternalExecutionAction.updated_at.desc(), ExternalExecutionAction.created_at.desc())
        .all()
    )
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    return {
        "status": "READY_FOR_STAGING_HANDOFF",
        "external_staging_state": "WAITING_FOR_REAL_STAGING_EVIDENCE",
        "actions": [_serialize_action(row) for row in rows],
        "status_options": [
            {"value": value, "label": label} for value, label in EXTERNAL_ACTION_STATUS_LABELS.items()
        ],
        "status_counts": counts,
        "staging_readiness": [
            {"item": item, "status": status, "detail": detail} for item, status, detail in STAGING_READINESS
        ],
        "lifting_systems_field_review": [
            {"field": field, "review_class": review_class, "rule": rule}
            for field, review_class, rule in LIFTING_SYSTEMS_FIELD_REVIEW
        ],
        "partner_coverage": list(PARTNER_COVERAGE),
        "safety": safety_flags(),
    }


def create_external_execution_action(db: Session, payload: Any, actor: Any | None) -> dict[str, Any]:
    data = payload.model_dump()
    actor_id = _actor_id(actor)
    action = ExternalExecutionAction(**data, created_by_id=actor_id, updated_by_id=actor_id)
    db.add(action)
    db.commit()
    db.refresh(action)
    return build_external_execution_console(db, actor)


def update_external_execution_action(
    db: Session,
    action_id: UUID,
    payload: Any,
    actor: Any | None,
) -> dict[str, Any] | None:
    action = db.get(ExternalExecutionAction, action_id)
    if action is None:
        return None
    data = payload.model_dump(exclude_unset=True)
    merged_status = data.get("status", action.status)
    merged_response = data.get("response_summary", action.response_summary)
    if merged_status == "response received" and not (merged_response or "").strip():
        raise ValueError("response_summary is required before marking response received")
    for key, value in data.items():
        setattr(action, key, value)
    action.updated_by_id = _actor_id(actor)
    db.commit()
    return build_external_execution_console(db, actor)
