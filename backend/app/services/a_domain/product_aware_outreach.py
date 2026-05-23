"""D5.15 — product-aware discovery outreach drafts (read-only, human review only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.a_domain.outreach_templates import LINKEDIN_MAX, _truncate_linkedin
from app.services.a_domain.pre_quote_prep import PRE_QUOTE_SAFETY

DRAFT_PURPOSES = frozenset(
    {
        "general_intro",
        "product_discovery",
        "quote_readiness",
        "sample_discussion",
        "follow_up_after_intro",
        "follow_up_after_sample",
        "oem_odm_discovery",
        "project_discovery",
    }
)

CHANNELS = frozenset(
    {
        "email_intro",
        "email_followup",
        "linkedin_connect",
        "linkedin_followup",
    }
)

TONES = frozenset({"concise", "warm", "formal"})
LANGUAGES = frozenset({"en", "zh"})

FORBIDDEN_PHRASES = (
    "guaranteed price",
    "lowest price guaranteed",
    "in stock",
    "certified for",
    "delivery guaranteed",
    "lead time confirmed",
    "we spoke yesterday",
)

PRODUCT_CONTEXT_LABELS: dict[str, str] = {
    "hosun_lifting_systems": "HOSUN lifting systems",
    "adjustable_desk_frames": "adjustable desk frames",
    "lifting_columns": "lifting columns",
    "desk_legs": "desk legs",
    "jooboo_education_furniture": "JOOBOO education furniture",
    "medical_workspace": "medical / lab workspace",
    "project_supply": "project-based furniture supply",
    "oem_odm_components": "OEM / ODM lifting components",
    "general_office": "general office furniture",
}


@dataclass
class ProductAwareDraftInput:
    company_name: str = ""
    contact_name: str | None = None
    draft_purpose: str = "product_discovery"
    channel: str = "email_intro"
    tone: str = "concise"
    language: str = "en"
    include_questions: bool = True
    include_product_brief: bool = True
    recommended_product_focus: list[str] = field(default_factory=list)
    quote_readiness: str = "not_ready"
    sample_readiness: str = "not_ready"
    missing_quote_info: list[str] = field(default_factory=list)
    recommended_customer_questions: list[str] = field(default_factory=list)
    recommended_next_action: str = ""
    project_type: str = "unknown"


def _primary_product_context(focus: list[str]) -> str:
    if not focus:
        return "general_office"
    if "oem_odm_components" in focus:
        return "oem_odm_components"
    if "project_supply" in focus:
        return "project_supply"
    if "jooboo_education_furniture" in focus:
        return "jooboo_education_furniture"
    if "medical_workspace" in focus:
        return "medical_workspace"
    if "hosun_lifting_systems" in focus or "adjustable_desk_frames" in focus:
        return "hosun_lifting_systems"
    return focus[0]


def _greeting(company_name: str, contact_name: str | None, tone: str) -> str:
    if contact_name and contact_name.strip():
        first = contact_name.strip().split()[0]
        if tone == "formal":
            return f"Dear {first},"
        return f"Hi {first},"
    team = company_name.strip() or "there"
    return f"Hi {team} team,"


def _focus_phrase(focus: list[str]) -> str:
    if not focus:
        return "office furniture and adjustable desk frame options"
    labels = [PRODUCT_CONTEXT_LABELS.get(f, f.replace("_", " ")) for f in focus[:3]]
    return ", ".join(labels)


def _context_paragraph(ctx: str, purpose: str, company_name: str) -> str:
    lines = {
        "hosun_lifting_systems": (
            f"Based on your company profile, I thought it may be useful to discuss adjustable desk frames, "
            f"lifting columns, desk legs, and lifting system support for {company_name}."
        ),
        "project_supply": (
            f"Based on our notes, {company_name} may be evaluating project-based furniture supply, "
            "FF&E coordination, or commercial interiors support."
        ),
        "jooboo_education_furniture": (
            f"I thought a brief discussion on classroom, training room, or campus furniture procurement "
            f"could be relevant for {company_name}."
        ),
        "medical_workspace": (
            f"We support medical and lab workspace discussions involving stable adjustable workstations "
            f"and precision lifting components for {company_name}."
        ),
        "oem_odm_components": (
            f"We can explore component-level cooperation — lifting columns, desk legs, control systems, "
            f"or adjustable frames — for {company_name}."
        ),
        "general_office": (
            f"I thought it may be useful to share how we support office furniture supply and "
            f"adjustable desk frame introductions for {company_name}."
        ),
    }
    return lines.get(ctx, lines["general_office"])


def _subject_for(ctx: str, purpose: str) -> str:
    subjects = {
        "hosun_lifting_systems": "intelliOffice — adjustable desk frame / lifting system discussion",
        "project_supply": "intelliOffice — project furniture and lifting system supply discussion",
        "jooboo_education_furniture": "intelliOffice — education furniture and classroom project discussion",
        "medical_workspace": "intelliOffice — medical / lab workspace discussion",
        "oem_odm_components": "intelliOffice — lifting component / OEM discussion",
        "general_office": "intelliOffice — office furniture and adjustable desk frame discussion",
    }
    if purpose == "sample_discussion":
        return "intelliOffice — sample discussion for project evaluation"
    if purpose == "quote_readiness":
        return "intelliOffice — clarifying scope before quote preparation"
    return subjects.get(ctx, subjects["general_office"])


def _questions_for(inp: ProductAwareDraftInput, ctx: str) -> list[str]:
    sample_q = "Which model or product type should be considered for sample evaluation?"

    def _ensure_sample_questions(questions: list[str]) -> list[str]:
        if inp.draft_purpose != "sample_discussion":
            return questions
        if any("sample" in q.lower() for q in questions):
            return questions
        return [sample_q, *questions]

    if inp.recommended_customer_questions:
        base = _ensure_sample_questions(list(inp.recommended_customer_questions[:5]))
        if inp.draft_purpose == "quote_readiness" and inp.missing_quote_info:
            missing_labels = {
                "quantity_or_volume": "What quantity or volume should we consider?",
                "project_timeline": "What is the expected project timeline?",
                "delivery_location": "What delivery location should be used for quotation planning?",
                "load_capacity_requirement": "Are there load capacity requirements we should note?",
                "product_type": "Which product type is most relevant: frames, columns, legs, or components?",
            }
            for key in inp.missing_quote_info[:3]:
                q = missing_labels.get(key)
                if q and q not in base:
                    base.append(q)
        return base[:5]
    base: list[str] = []
    if ctx in ("hosun_lifting_systems", "adjustable_desk_frames", "lifting_columns"):
        base = [
            "Are you looking for complete adjustable desk frames, desk legs, or lifting components?",
            "Is this for dealer supply, a specific project, or OEM/ODM development?",
            "Do you have target load capacity, frame size, or color requirements?",
        ]
    elif ctx == "project_supply":
        base = [
            "Is this tied to a specific office buildout or FF&E project?",
            "What quantity range and project timeline should we consider?",
            "Would a sample or technical spec sheet help the next discussion?",
        ]
    elif ctx == "jooboo_education_furniture":
        base = [
            "Is this for classroom, training room, or campus furniture procurement?",
            "Do you have an RFP timeline or volume estimate?",
        ]
    elif ctx == "oem_odm_components":
        base = [
            "Are you looking for private label, component sourcing, or custom development?",
            "Which components are most relevant: lifting columns, desk legs, frames, or control systems?",
        ]
    elif ctx == "medical_workspace":
        base = [
            "Is the use case clinical workstation, lab bench, or general healthcare workspace?",
            "Are there stability, cleaning, or load requirements we should understand?",
        ]
    else:
        base = [
            "Which product type is most relevant for your current evaluation?",
            "What quantity range and timeline should we consider?",
        ]
    if inp.draft_purpose == "quote_readiness" and inp.missing_quote_info:
        missing_labels = {
            "quantity_or_volume": "What quantity or volume should we consider?",
            "project_timeline": "What is the expected project timeline?",
            "delivery_location": "What delivery location should be used for quotation planning?",
            "load_capacity_requirement": "Are there load capacity requirements we should note?",
            "product_type": "Which product type is most relevant: frames, columns, legs, or components?",
        }
        for key in inp.missing_quote_info[:3]:
            q = missing_labels.get(key)
            if q and q not in base:
                base.append(q)
    if inp.draft_purpose == "sample_discussion":
        base = _ensure_sample_questions(base)
    return base[:5]


def _intro_line(tone: str) -> str:
    warm = "Hope you're doing well. " if tone == "warm" else ""
    return (
        f"{warm}I'm with intelliOffice, and we support customers through manufacturing partners "
        "across lifting systems, education furniture, and project-based furniture supply."
    )


def _linkedin_note(inp: ProductAwareDraftInput, ctx: str) -> str:
    fn = inp.contact_name.strip().split()[0] if inp.contact_name else "there"
    phrase = _focus_phrase(inp.recommended_product_focus)
    if inp.draft_purpose == "quote_readiness":
        text = (
            f"Hi {fn} — intelliOffice here. Supporting {phrase} for {inp.company_name}. "
            "Happy to clarify scope before any quote discussion — no pricing commitments in this note."
        )
    elif inp.draft_purpose == "sample_discussion":
        text = (
            f"Hi {fn} — intelliOffice. We can discuss sample options for {phrase} "
            f"relevant to {inp.company_name}. Open to a short overview if useful."
        )
    else:
        text = (
            f"Hi {fn} — I'm with intelliOffice. We support {phrase} through manufacturing partners. "
            f"Would be glad to connect with {inp.company_name} and share a short overview if relevant."
        )
    return _truncate_linkedin(text)


def _email_body(inp: ProductAwareDraftInput, ctx: str) -> str:
    greeting = _greeting(inp.company_name, inp.contact_name, inp.tone)
    intro = _intro_line(inp.tone)
    context = _context_paragraph(ctx, inp.draft_purpose, inp.company_name)
    questions = _questions_for(inp, ctx) if inp.include_questions else []

    parts = [greeting, "", intro, "", context, ""]
    if inp.draft_purpose in ("follow_up_after_intro", "follow_up_after_sample"):
        parts.append(
            "I'm following up on my earlier note to see whether a short catalog or spec overview "
            "would still be useful."
        )
        parts.append("")
    elif inp.draft_purpose == "quote_readiness":
        parts.append(
            "Before preparing any formal quote, I'd like to confirm a few scope points — "
            "this note does not include pricing, inventory, certification, or lead-time commitments."
        )
        parts.append("")
    elif inp.draft_purpose == "sample_discussion":
        parts.append(
            "If a sample discussion would help, we can clarify product type, configuration, "
            "and use case first — without any sample price or ship-date promises in this message."
        )
        parts.append("")
    else:
        parts.append(
            "Before preparing any quote or sample discussion, I'd like to understand a few points:"
        )
        parts.append("")

    if questions:
        for i, q in enumerate(questions, 1):
            parts.append(f"{i}. {q}")
        parts.append("")
    parts.append(
        "Would it make sense to review a short catalog or spec overview first?"
    )
    parts.extend(["", "Best regards,", "intelliOffice"])
    return "\n".join(parts)


def _recommended_next_action(inp: ProductAwareDraftInput) -> str:
    if inp.recommended_next_action:
        return inp.recommended_next_action
    if inp.channel.startswith("linkedin"):
        return "Send LinkedIn note manually after review; follow up in 5 days if no reply."
    return "Send email manually after review; follow up in 5 days if no reply."


def _follow_up_days(purpose: str) -> int:
    if purpose.startswith("follow_up"):
        return 5
    if purpose == "sample_discussion":
        return 7
    return 5


def generate_product_aware_draft(inp: ProductAwareDraftInput) -> dict[str, Any]:
    if inp.channel not in CHANNELS:
        raise ValueError(f"Invalid channel; use one of: {sorted(CHANNELS)}")
    if inp.draft_purpose not in DRAFT_PURPOSES:
        raise ValueError(f"Invalid draft_purpose; use one of: {sorted(DRAFT_PURPOSES)}")
    if inp.tone not in TONES:
        raise ValueError(f"Invalid tone; use one of: {sorted(TONES)}")
    if inp.language not in LANGUAGES:
        raise ValueError("language must be en or zh")

    ctx = _primary_product_context(inp.recommended_product_focus)
    questions = _questions_for(inp, ctx)

    subject: str | None = None
    body: str | None = None
    linkedin_note: str | None = None

    if inp.channel.startswith("email"):
        subject = _subject_for(ctx, inp.draft_purpose)
        body = _email_body(inp, ctx)
    else:
        linkedin_note = _linkedin_note(inp, ctx)
        if inp.channel == "linkedin_followup":
            body = _email_body(inp, ctx)  # optional longer reference for copy

    safety = {
        "automatic_sending_enabled": False,
        "quote_created": PRE_QUOTE_SAFETY["quote_created"],
        "pricing_generated": PRE_QUOTE_SAFETY["pricing_generated"],
        "inventory_promised": PRE_QUOTE_SAFETY["inventory_promised"],
        "certification_promised": PRE_QUOTE_SAFETY["certification_promised"],
        "lead_time_promised": PRE_QUOTE_SAFETY["lead_time_promised"],
    }

    warnings = [
        "Human review required before sending.",
        "No pricing, inventory, certification, or lead-time commitments are included.",
    ]

    return {
        "company_name": inp.company_name,
        "channel": inp.channel,
        "draft_purpose": inp.draft_purpose,
        "tone": inp.tone,
        "language": inp.language,
        "subject": subject,
        "body": body,
        "linkedin_note": linkedin_note,
        "questions": questions,
        "recommended_next_action": _recommended_next_action(inp),
        "suggested_follow_up_days": _follow_up_days(inp.draft_purpose),
        "source_context": {
            "product_focus": inp.recommended_product_focus,
            "quote_readiness": inp.quote_readiness,
            "sample_readiness": inp.sample_readiness,
            "missing_quote_info": inp.missing_quote_info,
        },
        "safety": safety,
        "warnings": warnings,
    }


def build_product_aware_draft_from_brief(
    brief: dict[str, Any],
    *,
    contact_name: str | None,
    channel: str,
    draft_purpose: str,
    tone: str = "concise",
    language: str = "en",
    include_questions: bool = True,
    include_product_brief: bool = True,
) -> dict[str, Any]:
    inp = ProductAwareDraftInput(
        company_name=brief.get("company_name", ""),
        contact_name=contact_name,
        draft_purpose=draft_purpose,
        channel=channel,
        tone=tone,
        language=language,
        include_questions=include_questions,
        include_product_brief=include_product_brief,
        recommended_product_focus=brief.get("recommended_product_focus") or [],
        quote_readiness=brief.get("quote_readiness", "not_ready"),
        sample_readiness=brief.get("sample_readiness", "not_ready"),
        missing_quote_info=brief.get("missing_quote_info") or [],
        recommended_customer_questions=brief.get("recommended_customer_questions") or [],
        recommended_next_action=brief.get("recommended_next_action", ""),
        project_type=brief.get("project_type", "unknown"),
    )
    result = generate_product_aware_draft(inp)
    result["lead_id"] = brief.get("lead_id", "")
    return result


def assert_no_forbidden_promises(text: str) -> None:
    lower = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            raise ValueError(f"Forbidden phrase in draft: {phrase}")
