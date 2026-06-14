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


LIFTING_SYSTEMS_PARTNER = "HO" + "SUN"


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

READINESS_ACTION_KEYS = {
    "backend HTTPS origin": ("credentials",),
    "Portal origin": ("credentials",),
    "PORTAL_CUSTOMER_API_TOKEN": ("credentials",),
    "PORTAL_CUSTOMER_ALLOWED_ORIGINS": ("credentials",),
    "PUBLIC_BASE_URL": ("credentials",),
    "security signoff": ("security_signoff",),
    "business signoff": ("business_signoff",),
    "UAT seed data approval": ("uat_data_approval",),
    "real staging smoke test": ("real_smoke_test",),
    "rollback owner": ("credentials", "real_smoke_test"),
    "D9 entry gate": (
        "credentials",
        "security_signoff",
        "business_signoff",
        "uat_data_approval",
        "real_smoke_test",
        "partner_feedback",
    ),
}

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

READINESS_GAP_CLASSIFICATION: dict[str, dict[str, Any]] = {
    "backend HTTPS origin": {
        "gap_id": "staging.backend_https_origin",
        "area": "staging",
        "severity": "P0",
        "affects_d9": True,
        "affects_pilot": True,
        "needs_staging_credentials": True,
        "evidence_required": "real backend HTTPS origin verified by staging operator",
    },
    "Portal origin": {
        "gap_id": "staging.portal_origin",
        "area": "staging",
        "severity": "P0",
        "affects_d9": True,
        "affects_pilot": True,
        "needs_staging_credentials": True,
        "evidence_required": "service.intelli-opus.com real origin confirmed by Portal operator",
    },
    "PORTAL_CUSTOMER_API_TOKEN": {
        "gap_id": "staging.portal_token",
        "area": "staging",
        "severity": "P0",
        "affects_d9": True,
        "affects_pilot": True,
        "needs_security_signoff": True,
        "needs_staging_credentials": True,
        "evidence_required": "token received through secure channel and recorded only as redacted status",
    },
    "PORTAL_CUSTOMER_ALLOWED_ORIGINS": {
        "gap_id": "staging.allowed_origins",
        "area": "staging",
        "severity": "P0",
        "affects_d9": True,
        "affects_pilot": True,
        "needs_security_signoff": True,
        "needs_staging_credentials": True,
        "evidence_required": "allowed origin success and disallowed origin rejection",
    },
    "PUBLIC_BASE_URL": {
        "gap_id": "staging.public_base_url",
        "area": "staging",
        "severity": "P0",
        "affects_d9": True,
        "affects_pilot": True,
        "needs_staging_credentials": True,
        "evidence_required": "PUBLIC_BASE_URL matches the real staging URL",
    },
    "security signoff": {
        "gap_id": "signoff.security",
        "area": "security",
        "severity": "P0",
        "affects_d9": True,
        "affects_pilot": True,
        "needs_security_signoff": True,
        "evidence_required": "reviewer, date, scope, required fixes, and approval state",
    },
    "business signoff": {
        "gap_id": "signoff.business",
        "area": "business UAT",
        "severity": "P0",
        "affects_d9": True,
        "affects_pilot": True,
        "needs_business_signoff": True,
        "evidence_required": "owner, date, scope, approved customer-safe fields, and conditions",
    },
    "UAT seed data approval": {
        "gap_id": "uat.seed_data",
        "area": "business UAT",
        "severity": "P0",
        "affects_d9": True,
        "affects_pilot": True,
        "needs_business_signoff": True,
        "evidence_required": "approved products, customers, orders, feedback, resources, and market preview",
    },
    "real staging smoke test": {
        "gap_id": "staging.real_smoke",
        "area": "staging",
        "severity": "P0",
        "affects_d9": True,
        "affects_pilot": True,
        "needs_security_signoff": True,
        "needs_business_signoff": True,
        "needs_staging_credentials": True,
        "evidence_required": "real staging smoke evidence without secrets and rollback result",
    },
    "rollback owner": {
        "gap_id": "staging.rollback_owner",
        "area": "staging",
        "severity": "P0",
        "affects_d9": True,
        "affects_pilot": True,
        "needs_staging_credentials": True,
        "evidence_required": "named rollback owner and disable path",
    },
    "D9 entry gate": {
        "gap_id": "d9.entry_gate",
        "area": "D9 gate",
        "severity": "P0",
        "affects_d9": True,
        "affects_pilot": False,
        "needs_security_signoff": True,
        "needs_business_signoff": True,
        "needs_partner_feedback": True,
        "needs_staging_credentials": True,
        "evidence_required": "all P0 staging, security, business, UAT, rollback, and smoke conditions resolved",
    },
}

PARTNER_PILOT_GAP_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "gap_id": "partner_rehearsal.feedback",
        "title": "Partner rehearsal feedback is still required before pilot prioritization",
        "area": "partner rehearsal",
        "severity": "P1",
        "partner_focus": "multi-partner",
        "product_focus": [
            "lifting systems",
            "desk frames",
            "desk legs",
            "lifting columns",
            "heavy-duty supply",
            "education furniture",
            "project furniture",
        ],
        "affects_d9": False,
        "affects_pilot": True,
        "needs_partner_feedback": True,
        "evidence_required": "real partner quote or approved transcript, not internal observation",
        "default_owner": "业务负责人",
        "default_next_action": "Schedule rehearsal and capture real feedback separately from internal observations.",
    },
    {
        "gap_id": "lifting_partner.lifting_systems_claims",
        "title": f"{LIFTING_SYSTEMS_PARTNER} lifting systems customer-safe claims need validation",
        "area": "pilot readiness",
        "severity": "P1",
        "partner_focus": LIFTING_SYSTEMS_PARTNER,
        "product_focus": [
            "lifting systems",
            "desk frames",
            "desk legs",
            "lifting columns",
            "heavy-duty supply",
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
        ],
        "affects_d9": False,
        "affects_pilot": True,
        "needs_business_signoff": True,
        "needs_security_signoff": True,
        "evidence_required": "business-approved customer-safe wording and security-reviewed forbidden field boundary",
        "default_owner": "业务负责人 / 安全审核人",
        "default_next_action": "Validate load, noise, test cycle, certification, warranty, delivery, and project-demand wording before customer-visible use.",
    },
    {
        "gap_id": "jooboo.project_furniture_path",
        "title": "JOOBOO education/project furniture pilot path needs field approval",
        "area": "pilot readiness",
        "severity": "P1",
        "partner_focus": "JOOBOO",
        "product_focus": [
            "education furniture",
            "school desks/chairs",
            "project furniture",
            "school procurement timing",
            "delivery consistency",
            "installation",
            "resource needs",
            "feedback after use",
        ],
        "affects_d9": False,
        "affects_pilot": True,
        "needs_business_signoff": True,
        "needs_partner_feedback": True,
        "evidence_required": "business-approved project acceptance fields and real partner/customer feedback",
        "default_owner": "业务负责人",
        "default_next_action": "Confirm JOOBOO project timing, resource needs, delivery consistency, and feedback-after-use fields.",
    },
    {
        "gap_id": "future_partner.onboarding_decision_model",
        "title": "Future partner onboarding decision model needs reusable field mapping",
        "area": "partner onboarding",
        "severity": "P2",
        "partner_focus": "future partner",
        "product_focus": [
            "onboarding data",
            "product family",
            "quote logic",
            "delivery requirement",
            "resource taxonomy",
            "customer-visible fields",
            "Market Response metrics",
        ],
        "affects_d9": False,
        "affects_pilot": True,
        "needs_business_signoff": True,
        "needs_partner_feedback": True,
        "evidence_required": "field mapping approved by business owner and validated with at least one future partner rehearsal",
        "default_owner": "业务负责人",
        "default_next_action": "Use Partner Onboarding to map product family, quote logic, delivery requirements, resources, and market metrics.",
    },
)


def _actor_id(actor: Any | None) -> Any | None:
    return getattr(actor, "id", None) if actor is not None else None


def _ensure_default_actions(db: Session, actor: Any | None = None) -> None:
    actor_id = _actor_id(actor)
    existing = {
        (row.action_type, row.target_partner_system)
        for row in db.query(ExternalExecutionAction.action_type, ExternalExecutionAction.target_partner_system).all()
    }
    inserted = False
    for item in DEFAULT_ACTIONS:
        if (item.action_type, item.target_partner_system) in existing:
            continue
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
        inserted = True
    if inserted:
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


def _actions_for_readiness_key(rows: list[ExternalExecutionAction], key: str) -> list[ExternalExecutionAction]:
    return [
        row
        for row in rows
        if row.staging_readiness_key == key or row.pilot_readiness_key == key
    ]


def _readiness_status(base_status: str, linked_actions: list[ExternalExecutionAction], item: str) -> str:
    if item == "D9 entry gate":
        return "blocked"
    statuses = {row.status for row in linked_actions}
    if not linked_actions:
        return base_status
    if "blocked" in statuses:
        return "blocked by action"
    if "response received" in statuses:
        return "response received - review required"
    if "sent manually" in statuses:
        return "sent manually - waiting response"
    if "ready to send" in statuses:
        return "ready to send"
    if "complete" in statuses:
        return "manual record complete - evidence still required"
    if "draft" in statuses:
        return "draft"
    return base_status


def _readiness_next_action(linked_actions: list[ExternalExecutionAction], item: str) -> str:
    if item == "D9 entry gate":
        return "Do not enter D9 until real staging smoke, security signoff, business signoff, UAT seed approval, rollback owner, and no P0 blockers are all confirmed."
    blocked = [row for row in linked_actions if row.status == "blocked"]
    if blocked:
        return blocked[0].blocker_notes or blocked[0].next_step or blocked[0].dependency or "Resolve the blocked external action first."
    received = [row for row in linked_actions if row.status == "response received"]
    if received:
        return received[0].next_step or "Review the real response and decide whether it affects staging, pilot, or roadmap priority."
    sent = [row for row in linked_actions if row.status == "sent manually"]
    if sent:
        return sent[0].next_step or "Wait for a real reply before marking response received."
    ready = [row for row in linked_actions if row.status == "ready to send"]
    if ready:
        return ready[0].next_step or "Manually send through the approved external channel."
    draft = [row for row in linked_actions if row.status == "draft"]
    if draft:
        return draft[0].next_step or "Assign owner, due date, dependency, and manual send plan."
    complete = [row for row in linked_actions if row.status == "complete"]
    if complete:
        return "Verify owner/date/scope and attach only redacted evidence references; do not write STAGING_VALIDATED from this local record."
    return "Create or link an External Execution action so this gate has an owner and next step."


def _build_staging_readiness(rows: list[ExternalExecutionAction]) -> list[dict[str, Any]]:
    readiness: list[dict[str, Any]] = []
    for item, base_status, detail in STAGING_READINESS:
        keys = READINESS_ACTION_KEYS.get(item, ())
        linked: list[ExternalExecutionAction] = []
        for key in keys:
            linked.extend(_actions_for_readiness_key(rows, key))
        unique_linked = list({row.id: row for row in linked}.values())
        readiness.append(
            {
                "item": item,
                "status": _readiness_status(base_status, unique_linked, item),
                "detail": detail,
                "next_action": _readiness_next_action(unique_linked, item),
                "linked_action_ids": [str(row.id) for row in unique_linked],
                "linked_action_statuses": sorted({row.status for row in unique_linked}),
            }
        )
    return readiness


def _gap_work_state(readiness_status: str, linked_actions: list[ExternalExecutionAction]) -> str:
    statuses = {row.status for row in linked_actions}
    if "blocked" in statuses or "blocked" in readiness_status:
        return "blocked"
    if "response received" in statuses:
        return "needs review"
    if "sent manually" in statuses:
        return "waiting response"
    if "ready to send" in statuses:
        return "ready to send"
    if "draft" in statuses:
        return "draft"
    if "complete" in statuses:
        return "record complete - external evidence still required"
    return "pending"


def _first_non_empty(values: list[str | None], fallback: str) -> str:
    for value in values:
        if value and value.strip():
            return value
    return fallback


def _linked_action_ids(rows: list[ExternalExecutionAction]) -> list[str]:
    return [str(row.id) for row in rows]


def _linked_action_statuses(rows: list[ExternalExecutionAction]) -> list[str]:
    return sorted({row.status for row in rows})


def _build_gap_from_readiness(
    readiness_row: dict[str, Any],
    linked_actions: list[ExternalExecutionAction],
) -> dict[str, Any]:
    item = readiness_row["item"]
    classification = READINESS_GAP_CLASSIFICATION[item]
    blocker = _first_non_empty(
        [row.blocker_notes for row in linked_actions if row.status == "blocked"],
        readiness_row.get("detail") or "Missing required external evidence.",
    )
    owner = _first_non_empty(
        [row.owner for row in linked_actions],
        "unassigned",
    )
    next_action = _first_non_empty(
        [row.next_step for row in linked_actions],
        readiness_row.get("next_action") or "Assign owner and create an External Execution action.",
    )
    product_focus: list[str] = []
    partner_focus = "multi-partner"
    for row in linked_actions:
        if row.partner_focus:
            partner_focus = row.partner_focus
        product_focus.extend(row.product_focus or [])
    return {
        "gap_id": classification["gap_id"],
        "title": item,
        "area": classification["area"],
        "severity": classification["severity"],
        "work_state": _gap_work_state(readiness_row.get("status", "pending"), linked_actions),
        "owner": owner,
        "next_action": next_action,
        "blocker_reason": blocker,
        "affects_d9": bool(classification.get("affects_d9")),
        "affects_pilot": bool(classification.get("affects_pilot")),
        "needs_business_signoff": bool(classification.get("needs_business_signoff")),
        "needs_security_signoff": bool(classification.get("needs_security_signoff")),
        "needs_partner_feedback": bool(classification.get("needs_partner_feedback")),
        "needs_staging_credentials": bool(classification.get("needs_staging_credentials")),
        "partner_focus": partner_focus,
        "product_focus": sorted(set(product_focus)),
        "readiness_item": item,
        "source_action_ids": _linked_action_ids(linked_actions),
        "source_action_statuses": _linked_action_statuses(linked_actions),
        "evidence_required": classification["evidence_required"],
        "customer_safe_boundary": "Do not expose cost, margin, supplier private notes, raw token, internal scoring, or unapproved claims.",
    }


def _build_partner_pilot_gap(
    template: dict[str, Any],
    linked_actions: list[ExternalExecutionAction],
) -> dict[str, Any]:
    return {
        "gap_id": template["gap_id"],
        "title": template["title"],
        "area": template["area"],
        "severity": template["severity"],
        "work_state": _gap_work_state("pending", linked_actions),
        "owner": _first_non_empty([row.owner for row in linked_actions], template["default_owner"]),
        "next_action": _first_non_empty([row.next_step for row in linked_actions], template["default_next_action"]),
        "blocker_reason": _first_non_empty(
            [row.blocker_notes for row in linked_actions if row.status == "blocked"],
            "Requires real external input or sign-off before pilot use.",
        ),
        "affects_d9": bool(template.get("affects_d9")),
        "affects_pilot": bool(template.get("affects_pilot")),
        "needs_business_signoff": bool(template.get("needs_business_signoff")),
        "needs_security_signoff": bool(template.get("needs_security_signoff")),
        "needs_partner_feedback": bool(template.get("needs_partner_feedback")),
        "needs_staging_credentials": bool(template.get("needs_staging_credentials")),
        "partner_focus": template["partner_focus"],
        "product_focus": template["product_focus"],
        "readiness_item": None,
        "source_action_ids": _linked_action_ids(linked_actions),
        "source_action_statuses": _linked_action_statuses(linked_actions),
        "evidence_required": template["evidence_required"],
        "customer_safe_boundary": "Only business-approved, security-reviewed customer-safe wording can be used externally.",
    }


def _build_readiness_gap_intelligence(
    rows: list[ExternalExecutionAction],
    readiness: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    action_by_id = {str(row.id): row for row in rows}
    for readiness_row in readiness:
        linked = [action_by_id[action_id] for action_id in readiness_row.get("linked_action_ids", []) if action_id in action_by_id]
        gaps.append(_build_gap_from_readiness(readiness_row, linked))

    partner_feedback_actions = [
        row for row in rows if row.pilot_readiness_key == "partner_feedback"
    ]
    business_actions = [
        row for row in rows if row.staging_readiness_key == "business_signoff" or row.pilot_readiness_key == "uat_data_approval"
    ]
    security_actions = [
        row for row in rows if row.staging_readiness_key == "security_signoff"
    ]
    for template in PARTNER_PILOT_GAP_TEMPLATES:
        partner = template["partner_focus"]
        if partner == "multi-partner":
            linked = partner_feedback_actions
        elif partner == LIFTING_SYSTEMS_PARTNER:
            linked = business_actions + security_actions
        elif partner == "JOOBOO":
            linked = partner_feedback_actions + business_actions
        else:
            linked = partner_feedback_actions + business_actions
        gaps.append(_build_partner_pilot_gap(template, linked))

    severity_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    state_order = {
        "blocked": 0,
        "draft": 1,
        "ready to send": 2,
        "waiting response": 3,
        "needs review": 4,
        "pending": 5,
        "record complete - external evidence still required": 6,
    }
    return sorted(
        gaps,
        key=lambda gap: (
            severity_order.get(gap["severity"], 9),
            state_order.get(gap["work_state"], 9),
            gap["area"],
            gap["gap_id"],
        ),
    )


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
    staging_readiness = _build_staging_readiness(rows)
    return {
        "status": "READY_FOR_STAGING_HANDOFF",
        "external_staging_state": "WAITING_FOR_REAL_STAGING_EVIDENCE",
        "actions": [_serialize_action(row) for row in rows],
        "status_options": [
            {"value": value, "label": label} for value, label in EXTERNAL_ACTION_STATUS_LABELS.items()
        ],
        "status_counts": counts,
        "staging_readiness": staging_readiness,
        "readiness_gap_intelligence": _build_readiness_gap_intelligence(rows, staging_readiness),
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
