"""D5.14 — pre-quote and sample prep briefs (read-only, no quotes or pricing)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.services.a_domain.product_fit import (
    PRODUCT_FOCUS_EDUCATION,
    PRODUCT_FOCUS_HOSUN,
    PRODUCT_FOCUS_MEDICAL,
    PRODUCT_FOCUS_OEM,
    PRODUCT_FOCUS_PROJECT,
)

PRE_QUOTE_SAFETY: dict[str, bool] = {
    "quote_created": False,
    "pricing_generated": False,
    "inventory_promised": False,
    "certification_promised": False,
    "lead_time_promised": False,
    "automatic_sending_enabled": False,
}

FORBIDDEN_BRIEF_PHRASES = (
    "guaranteed price",
    "in stock",
    "certified for",
    "delivery guaranteed",
    "lead time confirmed",
    "$",
)

GENERAL_QUOTE_CHECKLIST = [
    "Confirm product type.",
    "Confirm quantity or volume.",
    "Confirm project timeline.",
    "Confirm delivery location.",
    "Confirm decision maker or buyer role.",
    "Confirm target use case.",
    "Confirm whether sample is needed before quote.",
]

HOSUN_QUOTE_CHECKLIST = [
    "Confirm whether they need complete adjustable desk frames, desk legs, lifting columns, or component-level systems.",
    "Confirm load capacity requirement.",
    "Confirm frame size / desktop size range.",
    "Confirm color / finish.",
    "Confirm control system needs, if relevant.",
    "Confirm whether this is dealer supply, project supply, or OEM / ODM.",
]

EDUCATION_QUOTE_CHECKLIST = [
    "Confirm classroom / training room / campus use case.",
    "Confirm estimated volume.",
    "Confirm RFP or procurement timeline.",
    "Confirm preferred desk/chair model or configuration.",
    "Confirm delivery location.",
]

PROJECT_QUOTE_CHECKLIST = [
    "Confirm whether there is a specific FF&E or office buildout project.",
    "Confirm project timeline.",
    "Confirm quantity estimate.",
    "Confirm installation / packaging needs.",
    "Confirm sample or mockup requirement.",
]

MEDICAL_QUOTE_CHECKLIST = [
    "Confirm lab / clinical / healthcare workspace use case.",
    "Confirm stability / load / cleaning requirements.",
    "Confirm whether adjustable workstation or lifting components are needed.",
    "Confirm compliance/certification questions as questions only — do not promise certification.",
]

OEM_QUOTE_CHECKLIST = [
    "Confirm whether they seek private label, component sourcing, or custom development.",
    "Confirm component category.",
    "Confirm expected volume range.",
    "Confirm customization requirements.",
    "Confirm engineering discussion needs.",
]

GENERAL_SAMPLE_CHECKLIST = [
    "Confirm which model or product type should be sampled.",
    "Confirm whether the sample is for internal evaluation, showroom, customer demo, or project mockup.",
    "Confirm destination and receiver.",
    "Confirm whether sample needs special color, load capacity, or configuration.",
    "Confirm whether customer expects catalog first before sample.",
]

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


@dataclass
class PreQuotePrepInput:
    lead_id: str = ""
    company_name: str = ""
    company_type: str | None = None
    business_description: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    quote_readiness: str = "not_ready"
    sample_readiness: str = "not_ready"
    recommended_product_focus: list[str] = field(default_factory=list)
    project_type: str = "unknown"
    opportunity_score: int = 0
    opportunity_level: str = "low_incomplete"
    missing_quote_info: list[str] = field(default_factory=list)
    recommended_discovery_questions: list[str] = field(default_factory=list)
    recommended_next_product_action: str = ""
    sales_angle: str = ""
    next_action: str | None = None
    follow_up_date: str | None = None


def _focus_label(slug: str) -> str:
    labels = {
        PRODUCT_FOCUS_HOSUN: "HOSUN lifting systems",
        "adjustable_desk_frames": "adjustable desk frames",
        "lifting_columns": "lifting columns",
        PRODUCT_FOCUS_EDUCATION: "JOOBOO education furniture",
        PRODUCT_FOCUS_MEDICAL: "medical / lab workspace",
        PRODUCT_FOCUS_PROJECT: "project supply",
        PRODUCT_FOCUS_OEM: "OEM / ODM components",
    }
    return labels.get(slug, slug.replace("_", " "))


def _opportunity_label(level: str) -> str:
    return {
        "high_opportunity": "High opportunity",
        "promising": "Promising",
        "needs_qualification": "Needs qualification",
        "low_incomplete": "Low / incomplete",
    }.get(level, level.replace("_", " ").title())


def _quote_checklist_for_focus(focus: list[str]) -> list[str]:
    items: list[str] = list(GENERAL_QUOTE_CHECKLIST)
    seen = set(items)
    focus_sets: list[tuple[str, list[str]]] = []
    if PRODUCT_FOCUS_PROJECT in focus:
        focus_sets.append((PRODUCT_FOCUS_PROJECT, PROJECT_QUOTE_CHECKLIST))
    if PRODUCT_FOCUS_EDUCATION in focus:
        focus_sets.append((PRODUCT_FOCUS_EDUCATION, EDUCATION_QUOTE_CHECKLIST))
    if PRODUCT_FOCUS_MEDICAL in focus:
        focus_sets.append((PRODUCT_FOCUS_MEDICAL, MEDICAL_QUOTE_CHECKLIST))
    if PRODUCT_FOCUS_OEM in focus:
        focus_sets.append((PRODUCT_FOCUS_OEM, OEM_QUOTE_CHECKLIST))
    if any(f in focus for f in (PRODUCT_FOCUS_HOSUN, "adjustable_desk_frames", "lifting_columns")):
        focus_sets.append((PRODUCT_FOCUS_HOSUN, HOSUN_QUOTE_CHECKLIST))
    for _key, checklist in focus_sets:
        for item in checklist:
            if item not in seen:
                seen.add(item)
                items.append(item)
    return items[:12]


def _internal_next_steps(inp: PreQuotePrepInput) -> list[str]:
    steps: list[str] = []
    if inp.quote_readiness == "ready":
        steps.append("Review latest customer context before drafting a human-reviewed quote outline.")
        steps.append("Confirm quantity, dimensions, delivery location, and certification questions with the customer.")
    elif inp.quote_readiness == "almost_ready":
        steps.append("Send discovery questions to confirm missing quote fields before any quote discussion.")
        steps.append("Update lead profile after customer replies.")
    else:
        steps.append("Complete contact research and confirm product interest before quote discussion.")
        steps.append("Set a clear next action and follow-up date after contact is validated.")
    if inp.sample_readiness in ("ready", "needs_specs"):
        steps.append("Clarify sample purpose, configuration, and receiver before any sample commitment.")
    if inp.follow_up_date:
        steps.append(f"Follow up by scheduled date ({inp.follow_up_date}).")
    return steps[:5]


def _recommended_next_action(inp: PreQuotePrepInput) -> str:
    if inp.recommended_next_product_action:
        return inp.recommended_next_product_action
    if inp.quote_readiness == "ready":
        return "Confirm latest specs with the customer, then prepare a formal quote manually."
    if inp.quote_readiness == "almost_ready":
        return "Ask for product type, quantity, and project timeline before preparing a formal quote."
    return "Complete contact research and confirm product direction before quote or sample discussion."


def _missing_labels(missing: list[str]) -> list[str]:
    labels = {
        "contact_email_or_linkedin": "Contact email or LinkedIn",
        "product_type": "Product type",
        "quantity_or_volume": "Quantity or volume",
        "desktop/frame size": "Desktop / frame size",
        "load_capacity_requirement": "Load capacity requirement",
        "color_or_finish": "Color or finish",
        "project_timeline": "Project timeline",
        "delivery_location": "Delivery location",
        "certification_requirement": "Certification requirement",
        "sample_quantity": "Sample quantity",
        "target_price_or_budget": "Target price or budget",
        "decision_maker_role": "Decision maker role",
    }
    return [labels.get(m, m.replace("_", " ")) for m in missing]


def _mask_sensitive(text: str) -> str:
    return _EMAIL_RE.sub("[contact on file]", text)


def _known_context(inp: PreQuotePrepInput) -> list[str]:
    lines: list[str] = []
    if inp.company_type:
        lines.append(f"{inp.company_type} lead.")
    if inp.business_description:
        desc = _mask_sensitive(inp.business_description.strip())
        if len(desc) > 200:
            desc = desc[:197] + "..."
        lines.append(desc)
    if inp.contact_name:
        lines.append(f"Primary contact: {inp.contact_name}.")
    if inp.sales_angle:
        lines.append(_mask_sensitive(inp.sales_angle))
    if not lines:
        lines.append("Limited profile context — enrich lead before quote preparation.")
    return lines


def _build_pre_quote_brief_text(inp: PreQuotePrepInput) -> str:
    focus = "; ".join(_focus_label(f) for f in inp.recommended_product_focus[:4]) or "—"
    missing = _missing_labels(inp.missing_quote_info)
    questions = inp.recommended_discovery_questions[:5]
    if not questions:
        questions = [
            "Are you looking for complete adjustable desk frames, desk legs, or lifting components?",
            "What quantity range and timeline should we consider?",
            "What delivery location should be used for quotation planning?",
        ]

    lines = [
        f"Pre-Quote Preparation Brief — {inp.company_name}",
        "",
        f"Opportunity level: {_opportunity_label(inp.opportunity_level)}",
        f"Product focus: {focus}",
        f"Quote readiness: {inp.quote_readiness.replace('_', ' ').title()}",
        f"Sample readiness: {inp.sample_readiness.replace('_', ' ').title()}",
        "",
        "Known context:",
    ]
    for ctx in _known_context(inp):
        lines.append(f"- {ctx}")
    lines.extend(["", "Missing information before quote:"])
    if missing:
        for m in missing[:8]:
            lines.append(f"- {m}")
    else:
        lines.append("- None flagged — still confirm latest specs with customer.")
    lines.extend(["", "Recommended customer questions:"])
    for i, q in enumerate(questions, 1):
        lines.append(f"{i}. {q}")
    lines.extend(
        [
            "",
            f"Recommended next action:",
            _recommended_next_action(inp),
            "",
            "Safety:",
            "This is a preparation brief only. It does not include pricing, inventory, certification, or lead-time commitments.",
        ]
    )
    return _mask_sensitive("\n".join(lines))


def _build_sample_discussion_brief_text(inp: PreQuotePrepInput) -> str:
    focus = "; ".join(_focus_label(f) for f in inp.recommended_product_focus[:3]) or "—"
    lines = [
        f"Sample Discussion Brief — {inp.company_name}",
        "",
        f"Sample readiness: {inp.sample_readiness.replace('_', ' ').title()}",
        f"Product focus: {focus}",
        "",
        "Sample preparation checklist:",
    ]
    for item in GENERAL_SAMPLE_CHECKLIST[:6]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "Discussion guidance:",
            "- Confirm sample purpose (evaluation, showroom, demo, or project mockup).",
            "- Do not quote sample price, availability, or ship date without human review.",
            "",
            f"Recommended next action: {_recommended_next_action(inp)}",
            "",
            "Safety: No sample pricing, availability, or delivery commitments are generated.",
        ]
    )
    return _mask_sensitive("\n".join(lines))


def build_pre_quote_brief(inp: PreQuotePrepInput) -> dict[str, Any]:
    """Derive pre-quote and sample prep brief from product fit context."""
    quote_checklist = _quote_checklist_for_focus(inp.recommended_product_focus)
    sample_checklist = list(GENERAL_SAMPLE_CHECKLIST[:6])
    questions = inp.recommended_discovery_questions[:5]
    if not questions:
        questions = [
            "Are you looking for complete adjustable desk frames, desk legs, or lifting components?",
            "Is this for dealer supply, a specific project, or OEM/ODM development?",
            "What quantity range and timeline should we consider?",
        ]

    warnings = [
        "No pricing, inventory, certification, or lead-time commitments are generated.",
        "This is preparation support only — not a quote or order.",
    ]

    result = {
        "lead_id": inp.lead_id,
        "company_name": inp.company_name,
        "quote_readiness": inp.quote_readiness,
        "sample_readiness": inp.sample_readiness,
        "recommended_product_focus": inp.recommended_product_focus,
        "project_type": inp.project_type,
        "opportunity_score": inp.opportunity_score,
        "missing_quote_info": inp.missing_quote_info,
        "quote_preparation_checklist": quote_checklist,
        "sample_preparation_checklist": sample_checklist,
        "recommended_customer_questions": questions,
        "recommended_internal_next_steps": _internal_next_steps(inp),
        "recommended_next_action": _recommended_next_action(inp),
        "pre_quote_brief_text": _build_pre_quote_brief_text(inp),
        "sample_discussion_brief_text": _build_sample_discussion_brief_text(inp),
        "warnings": warnings,
        "safety": dict(PRE_QUOTE_SAFETY),
    }
    return result


def build_pre_quote_brief_from_product_fit(
    product_fit: dict[str, Any],
    *,
    company_type: str | None = None,
    business_description: str | None = None,
    contact_name: str | None = None,
    contact_email: str | None = None,
    next_action: str | None = None,
    follow_up_date: str | None = None,
) -> dict[str, Any]:
    inp = PreQuotePrepInput(
        lead_id=product_fit.get("lead_id", ""),
        company_name=product_fit.get("company_name", ""),
        company_type=company_type,
        business_description=business_description,
        contact_name=contact_name,
        contact_email=contact_email,
        quote_readiness=product_fit.get("quote_readiness", "not_ready"),
        sample_readiness=product_fit.get("sample_readiness", "not_ready"),
        recommended_product_focus=product_fit.get("recommended_product_focus") or [],
        project_type=product_fit.get("project_type", "unknown"),
        opportunity_score=product_fit.get("project_opportunity_score", 0),
        opportunity_level=product_fit.get("opportunity_level", "low_incomplete"),
        missing_quote_info=product_fit.get("missing_quote_info") or [],
        recommended_discovery_questions=product_fit.get("recommended_discovery_questions") or [],
        recommended_next_product_action=product_fit.get("recommended_next_product_action", ""),
        sales_angle=product_fit.get("sales_angle", ""),
        next_action=next_action,
        follow_up_date=follow_up_date,
    )
    return build_pre_quote_brief(inp)
