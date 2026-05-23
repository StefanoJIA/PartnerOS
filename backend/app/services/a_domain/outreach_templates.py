"""Segment-based outreach draft templates (D5.2.4 — human copy only, no send)."""

from __future__ import annotations

from dataclasses import dataclass

LINKEDIN_MAX = 300

CHANNELS = frozenset(
    {
        "linkedin_connect",
        "linkedin_followup",
        "email_intro",
        "email_followup",
    }
)

PRODUCT_FOCUSES = frozenset(
    {
        "hosun_lifting",
        "jooboo_education",
        "medical_workspace",
        "project_supply",
        "general",
    }
)


@dataclass(frozen=True)
class OutreachDraftResult:
    channel: str
    language: str
    tone: str
    product_focus: str
    company_name: str
    segments: list[str]
    linkedin_connect_note: str | None
    email_subject: str | None
    email_body: str | None
    suggested_next_action: str
    suggested_touchpoint_type: str


def _first_name(contact_name: str | None) -> str:
    if not contact_name or not contact_name.strip():
        return "there"
    return contact_name.strip().split()[0]


def _truncate_linkedin(text: str) -> str:
    text = " ".join(text.split())
    if len(text) <= LINKEDIN_MAX:
        return text
    return text[: LINKEDIN_MAX - 1].rstrip() + "…"


def _pick_focus(segments: list[str], product_focus: str) -> str:
    if product_focus != "general":
        return product_focus
    if "lift_system_signal" in segments or "oem_odm_fit" in segments:
        return "hosun_lifting"
    if "education_vertical" in segments:
        return "jooboo_education"
    if "project_based_furniture" in segments:
        return "project_supply"
    if "medical_vertical" in segments:
        return "medical_workspace"
    return "general"


def _next_action_for(channel: str, focus: str) -> tuple[str, str]:
    touch = {
        "linkedin_connect": "linkedin_connect_note",
        "linkedin_followup": "waiting_for_reply",
        "email_intro": "catalog_sent",
        "email_followup": "quotation_follow_up",
    }.get(channel, "follow_up")
    actions = {
        "linkedin_connect": "Send LinkedIn connect note (manual review before send)",
        "linkedin_followup": "Follow up on LinkedIn in 5 days if no reply",
        "email_intro": "Send catalog by email after internal review",
        "email_followup": "Follow up on email intro in 5 days",
    }
    if focus == "hosun_lifting":
        actions["email_intro"] = "Send lifting systems overview — ask about frame/column needs"
    return actions.get(channel, "Set next action in Lead Intelligence"), touch


def generate_outreach_draft(
    *,
    company_name: str,
    segments: list[str],
    contact_name: str | None = None,
    channel: str = "linkedin_connect",
    language: str = "en",
    tone: str = "concise",
    product_focus: str = "general",
    notes: str | None = None,
) -> OutreachDraftResult:
    if channel not in CHANNELS:
        raise ValueError(f"Invalid channel; use one of: {sorted(CHANNELS)}")
    if product_focus not in PRODUCT_FOCUSES:
        raise ValueError(f"Invalid product_focus; use one of: {sorted(PRODUCT_FOCUSES)}")
    if language not in ("en", "zh"):
        raise ValueError("language must be en or zh")

    focus = _pick_focus(segments, product_focus)
    fn = _first_name(contact_name)
    seg_key = segments[0] if segments else "general_office_furniture_only"
    suggested_next, touch_type = _next_action_for(channel, focus)

    if language == "zh":
        return _generate_zh(
            company_name=company_name,
            fn=fn,
            channel=channel,
            tone=tone,
            focus=focus,
            segments=segments,
            suggested_next=suggested_next,
            touch_type=touch_type,
        )

    return _generate_en(
        company_name=company_name,
        fn=fn,
        channel=channel,
        tone=tone,
        focus=focus,
        segments=segments,
        seg_key=seg_key,
        suggested_next=suggested_next,
        touch_type=touch_type,
        notes=notes,
    )


def _generate_en(
    *,
    company_name: str,
    fn: str,
    channel: str,
    tone: str,
    focus: str,
    segments: list[str],
    seg_key: str,
    suggested_next: str,
    touch_type: str,
    notes: str | None,
) -> OutreachDraftResult:
    platform = "intelliOffice"
    partner_line = (
        "We work with manufacturing partners such as HOSUN (lifting systems) and JOOBOO (education furniture) "
        "as equal supply sources — not a single-vendor pitch."
    )

    focus_blurbs = {
        "hosun_lifting": (
            "adjustable desk frames, lifting columns, and desk legs with an emphasis on stability, low noise, "
            "and project/OEM support"
        ),
        "jooboo_education": (
            "durable education furniture for classrooms, training rooms, and campus projects through our JOOBOO partner line"
        ),
        "medical_workspace": (
            "healthcare and lab workstation configurations supported by precision lifting system manufacturing partners"
        ),
        "project_supply": (
            "project-based office furniture supply, FF&E coordination, and installation-friendly packaging"
        ),
        "general": "office and project furniture supply coordination through intelliOffice",
    }
    blurb = focus_blurbs.get(focus, focus_blurbs["general"])

    warm = "Hope you're doing well. " if tone == "warm" else ""
    formal = "Dear " + fn + ",\n\n" if tone == "formal" else f"Hi {fn},\n\n"

    linkedin_note: str | None = None
    email_subject: str | None = None
    email_body: str | None = None

    if channel == "linkedin_connect":
        linkedin_note = _truncate_linkedin(
            f"Hi {fn} — I'm with {platform}, supporting {blurb}. "
            f"Noticed {company_name} and thought a brief connect could help if adjustable/project supply ever comes up. "
            "Happy to share a short catalog overview — no pricing commitments here. "
            "Best regards"
        )
    elif channel == "linkedin_followup":
        linkedin_note = _truncate_linkedin(
            f"Hi {fn} — following up from {platform} on project/adjustable supply topics for {company_name}. "
            "If timing isn't right, no worries — open to a quick note when relevant."
        )
    elif channel == "email_intro":
        email_subject = f"{platform} — introduction re: {company_name}"
        email_body = (
            f"{formal}{warm}"
            f"I'm reaching out from {platform}. We help teams evaluate {blurb}.\n\n"
            f"{partner_line}\n\n"
            f"If {company_name} is exploring adjustable frames, project furniture, or vertical-specific lines, "
            "I'd welcome a 15-minute call to understand requirements — samples and quotations can be discussed "
            "after scope is clear (no stock or lead-time promises in this note).\n\n"
            "Best regards,\n"
            f"{platform} team"
        )
    elif channel == "email_followup":
        email_subject = f"Following up — {company_name} / {platform}"
        email_body = (
            f"{formal}{warm}"
            f"Checking whether my earlier note about {blurb} was useful for {company_name}.\n\n"
            "If you prefer, I can send a focused one-pager on lifting systems or education lines — "
            "still subject to your review before any customer-facing send.\n\n"
            "Best regards,\n"
            f"{platform} team"
        )

    if "project_based_furniture" in segments and channel.startswith("email"):
        email_body = (email_body or "") + "\n\nP.S. We also support project-based FF&E coordination and sample timing."

    return OutreachDraftResult(
        channel=channel,
        language="en",
        tone=tone,
        product_focus=focus,
        company_name=company_name,
        segments=segments,
        linkedin_connect_note=linkedin_note,
        email_subject=email_subject,
        email_body=email_body,
        suggested_next_action=suggested_next,
        suggested_touchpoint_type=touch_type,
    )


def _generate_zh(
    *,
    company_name: str,
    fn: str,
    channel: str,
    tone: str,
    focus: str,
    segments: list[str],
    suggested_next: str,
    touch_type: str,
) -> OutreachDraftResult:
    platform = "intelliOffice"
    linkedin_note: str | None = None
    email_subject: str | None = None
    email_body: str | None = None

    if channel == "linkedin_connect":
        linkedin_note = _truncate_linkedin(
            f"您好 {fn}，我是 {platform} 团队，协助对接升降系统/项目家具供应（含 HOSUN、JOOBOO 等平级伙伴资源）。"
            f"关注到 {company_name}，如方便希望简短连接，可分享产品概览（不含价格/交期承诺）。"
        )
    elif channel == "email_intro":
        email_subject = f"{platform} — 关于 {company_name} 的简要介绍"
        email_body = (
            f"您好 {fn}，\n\n"
            f"我是 {platform} 团队。我们帮助客户评估升降桌架/立柱、教育家具及项目制供应方案；"
            "HOSUN、JOOBOO 等为平级制造伙伴，非单一品牌绑定。\n\n"
            f"如 {company_name} 有相关需求，欢迎安排简短沟通；样品与报价在明确需求后再议。\n\n"
            "此致\n"
            f"{platform} 团队"
        )
    elif channel == "email_followup":
        email_subject = f"跟进 — {company_name}"
        email_body = f"您好 {fn}，\n\n想跟进此前关于 {company_name} 供应协作的邮件，如有需要可补发针对性资料页。\n\n{platform} 团队"
    elif channel == "linkedin_followup":
        linkedin_note = _truncate_linkedin(f"您好 {fn}，跟进 {company_name} 相关供应话题，如暂不合适可改日再联系。—— {platform}")

    return OutreachDraftResult(
        channel=channel,
        language="zh",
        tone=tone,
        product_focus=focus,
        company_name=company_name,
        segments=segments,
        linkedin_connect_note=linkedin_note,
        email_subject=email_subject,
        email_body=email_body,
        suggested_next_action=suggested_next,
        suggested_touchpoint_type=touch_type,
    )
