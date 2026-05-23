"""D5.18 — soft quote handoff brief (read-only, no quote creation or pricing)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.services.a_domain.pre_quote_prep import PRE_QUOTE_SAFETY
from app.services.a_domain.product_fit import (
    PRODUCT_FOCUS_DESK_LEGS,
    PRODUCT_FOCUS_EDUCATION,
    PRODUCT_FOCUS_FRAMES,
    PRODUCT_FOCUS_HEAVY_DUTY,
    PRODUCT_FOCUS_HOSUN,
    PRODUCT_FOCUS_MEDICAL,
    PRODUCT_FOCUS_OEM,
    PRODUCT_FOCUS_PROJECT,
    PRODUCT_FOCUS_COLUMNS,
)

HANDOFF_STATUSES = frozenset(
    {
        "ready_for_manual_quote_prep",
        "needs_customer_clarification",
        "not_ready",
    }
)

HANDOFF_PRIORITIES = frozenset({"high", "medium", "low"})

FORBIDDEN_HANDOFF_PHRASES = (
    "guaranteed price",
    "lowest price guaranteed",
    "in stock",
    "certified for",
    "delivery guaranteed",
    "lead time confirmed",
)

SCOPE_SLUGS = frozenset(
    {
        PRODUCT_FOCUS_FRAMES,
        PRODUCT_FOCUS_DESK_LEGS,
        PRODUCT_FOCUS_COLUMNS,
        PRODUCT_FOCUS_HEAVY_DUTY,
    }
)

ROUTE_LABELS: dict[str, str] = {
    "hosun_lifting_systems": "HOSUN lifting systems",
    "jooboo_education_furniture": "JOOBOO education furniture",
    "project_supply": "Project supply",
    "medical_workspace": "Medical / lab workspace",
    "oem_odm_components": "OEM / ODM components",
}

SCOPE_LABELS: dict[str, str] = {
    PRODUCT_FOCUS_FRAMES: "adjustable desk frames",
    PRODUCT_FOCUS_DESK_LEGS: "desk legs",
    PRODUCT_FOCUS_COLUMNS: "lifting columns",
    PRODUCT_FOCUS_HEAVY_DUTY: "heavy-duty lifting systems",
}

MISSING_LABELS: dict[str, str] = {
    "contact_email_or_linkedin": "Contact email or LinkedIn",
    "product_type": "Product type",
    "quantity_or_volume": "Quantity or volume",
    "frame_size_or_desktop_size": "Frame / desktop size",
    "desktop/frame size": "Frame / desktop size",
    "load_capacity_requirement": "Load capacity requirement",
    "color_or_finish": "Color or finish",
    "project_timeline": "Project timeline",
    "delivery_location": "Delivery location",
    "product_scope": "Product scope",
    "decision_maker_role": "Decision maker role",
    "classroom_or_campus_use_case": "Classroom or campus use case",
    "rfp_or_procurement_timeline": "RFP or procurement timeline",
    "volume_estimate": "Volume estimate",
    "model_or_configuration": "Model or configuration",
    "component_category": "Component category",
    "expected_volume_range": "Expected volume range",
    "customization_requirement": "Customization requirement",
    "technical_requirements": "Technical requirements",
    "workstation_use_case": "Workstation use case",
    "stability_or_load_requirement": "Stability or load requirement",
    "cleaning_or_environment_requirement": "Cleaning or environment requirement",
    "installation_or_packaging_need": "Installation or packaging need",
}

_QUOTE_SIGNAL = re.compile(r"\b(quote|quotation|sample|meeting|rfp|procurement)\b", re.I)
_QUANTITY_SIGNAL = re.compile(r"\b(quantity|volume|units|moq|qty)\b", re.I)
_PRODUCT_TYPE_SIGNAL = re.compile(
    r"\b(desk frame|lifting column|desk leg|adjustable desk|component|frames|columns)\b",
    re.I,
)


@dataclass
class QuoteHandoffInput:
    lead_id: str = ""
    company_name: str = ""
    company_type: str | None = None
    industry: str | None = None
    business_description: str | None = None
    segments: list[str] = field(default_factory=list)
    quote_readiness: str = "not_ready"
    sample_readiness: str = "not_ready"
    opportunity_score: int = 0
    opportunity_level: str = "low_incomplete"
    project_type: str = "unknown"
    recommended_product_focus: list[str] = field(default_factory=list)
    missing_quote_info: list[str] = field(default_factory=list)
    recommended_discovery_questions: list[str] = field(default_factory=list)
    recommended_next_action: str = ""
    next_action: str | None = None
    follow_up_date: str | None = None
    due_status: str | None = None
    has_contact_method: bool = False
    touchpoint_summary: str | None = None
    notes_blob: str = ""


def _label(slug: str) -> str:
    return MISSING_LABELS.get(slug, slug.replace("_", " ").title())


def _partner_routes(focus: list[str]) -> list[str]:
    routes: list[str] = []
    hosun_related = {
        PRODUCT_FOCUS_HOSUN,
        PRODUCT_FOCUS_FRAMES,
        PRODUCT_FOCUS_COLUMNS,
        PRODUCT_FOCUS_DESK_LEGS,
        PRODUCT_FOCUS_HEAVY_DUTY,
    }
    if any(f in focus for f in hosun_related):
        routes.append("hosun_lifting_systems")
    if PRODUCT_FOCUS_EDUCATION in focus:
        routes.append("jooboo_education_furniture")
    if PRODUCT_FOCUS_PROJECT in focus:
        routes.append("project_supply")
    if PRODUCT_FOCUS_MEDICAL in focus:
        routes.append("medical_workspace")
    if PRODUCT_FOCUS_OEM in focus:
        routes.append("oem_odm_components")
    return routes


def _product_scope(focus: list[str]) -> list[str]:
    return [f for f in focus if f in SCOPE_SLUGS]


def _missing_customer_info(inp: QuoteHandoffInput) -> list[str]:
    missing = list(inp.missing_quote_info or [])[:6]
    if not inp.has_contact_method and "contact_email_or_linkedin" not in missing:
        missing.insert(0, "contact_email_or_linkedin")
    return missing[:6]


def _has_project_signal(blob: str) -> bool:
    return bool(_QUOTE_SIGNAL.search(blob) or _QUANTITY_SIGNAL.search(blob))


def _handoff_status(inp: QuoteHandoffInput, missing: list[str]) -> str:
    focus = inp.recommended_product_focus
    blob = inp.notes_blob

    if not inp.has_contact_method or not focus:
        return "not_ready"
    if inp.quote_readiness == "not_ready":
        return "not_ready"

    has_type_signal = bool(
        _PRODUCT_TYPE_SIGNAL.search(blob)
        or inp.project_type not in ("unknown",)
        or "product_type" not in missing
    )
    has_engagement = _has_project_signal(blob)

    if (
        inp.quote_readiness == "ready"
        and len(missing) <= 2
        and (has_type_signal or has_engagement)
    ):
        return "ready_for_manual_quote_prep"
    if inp.quote_readiness == "almost_ready" and focus:
        return "needs_customer_clarification"
    if inp.quote_readiness == "ready" and focus:
        return "needs_customer_clarification"
    return "not_ready"


def _handoff_priority(inp: QuoteHandoffInput, routes: list[str]) -> str:
    score = inp.opportunity_score
    blob = inp.notes_blob
    focus = inp.recommended_product_focus

    lifting = "hosun_lifting_systems" in routes
    project = "project_supply" in routes
    oem = "oem_odm_components" in routes
    heavy = PRODUCT_FOCUS_HEAVY_DUTY in focus

    if score >= 80:
        return "high"
    if lifting and (project or oem or heavy):
        return "high"
    if project and _QUOTE_SIGNAL.search(blob):
        return "high"
    if 60 <= score <= 79 and focus:
        return "medium"
    if score < 60 or not inp.has_contact_method or not focus:
        return "low"
    return "medium"


def _known_context(inp: QuoteHandoffInput, routes: list[str]) -> list[str]:
    lines: list[str] = []
    if inp.company_type:
        lines.append(f"{inp.company_type} lead.")
    if inp.industry and inp.industry != inp.company_type:
        lines.append(f"Industry: {inp.industry}.")
    if inp.segments:
        lines.append(f"Market segments: {', '.join(inp.segments)}.")
    if inp.recommended_product_focus:
        focus_text = "; ".join(ROUTE_LABELS.get(r, r.replace("_", " ")) for r in routes[:3])
        if focus_text:
            lines.append(f"Product focus suggests: {focus_text}.")
    lines.append(f"Quote readiness: {inp.quote_readiness.replace('_', ' ')}.")
    lines.append(f"Sample readiness: {inp.sample_readiness.replace('_', ' ')}.")
    if inp.project_type and inp.project_type != "unknown":
        lines.append(f"Project type: {inp.project_type.replace('_', ' ')}.")
    if inp.next_action:
        lines.append(f"Next action: {inp.next_action}.")
    if inp.due_status:
        lines.append(f"Follow-up due status: {inp.due_status}.")
    if inp.touchpoint_summary:
        lines.append(inp.touchpoint_summary)
    if inp.opportunity_level:
        lines.append(f"Opportunity level: {inp.opportunity_level.replace('_', ' ')} (score {inp.opportunity_score}).")
    if not lines:
        lines.append("Limited profile context on file.")
    return lines[:8]


def _supplier_notes(routes: list[str], focus: list[str], status: str) -> list[str]:
    notes: list[str] = []
    if "hosun_lifting_systems" in routes:
        notes.extend(
            [
                "Prepare adjustable desk frame overview.",
                "Prepare lifting column / desk leg specification summary if component-level interest is confirmed.",
                "Avoid quoting before quantity, size, load capacity, and delivery location are confirmed.",
            ]
        )
        if PRODUCT_FOCUS_HEAVY_DUTY in focus:
            notes.append(
                "Consider heavy-duty 660 lb / 300 kg models only if load requirement is confirmed — do not assume."
            )
    if "jooboo_education_furniture" in routes:
        notes.extend(
            [
                "Prepare education furniture catalog overview.",
                "Confirm classroom / training / campus scenario before model recommendation.",
                "Avoid volume assumptions before RFP or procurement details are known.",
            ]
        )
    if "project_supply" in routes:
        notes.extend(
            [
                "Prepare project supply discussion outline.",
                "Confirm whether this is dealer stock supply or specific project procurement.",
                "Ask for project timeline and delivery location before quote preparation.",
            ]
        )
    if "oem_odm_components" in routes:
        notes.extend(
            [
                "Prepare technical discussion notes.",
                "Confirm component category and expected volume.",
                "Avoid customization promises before engineering review.",
            ]
        )
    if "medical_workspace" in routes:
        notes.append("Prepare medical / lab workspace overview — ask compliance questions only, do not promise certification.")
    if status == "not_ready":
        notes.insert(0, "Complete contact research and confirm product direction before supplier preparation.")
    notes.append("Do not prepare a formal quote until missing customer fields are confirmed.")
    seen: set[str] = set()
    out: list[str] = []
    for n in notes:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out[:8]


def _customer_questions(inp: QuoteHandoffInput, routes: list[str]) -> list[str]:
    if inp.recommended_discovery_questions:
        return inp.recommended_discovery_questions[:5]

    if "hosun_lifting_systems" in routes:
        return [
            "Are you looking for complete adjustable desk frames, desk legs, lifting columns, or component-level systems?",
            "What quantity range should we consider?",
            "Is this for dealer supply, a specific project, or OEM/ODM development?",
            "Are there frame size, load capacity, color, or finish requirements?",
            "What delivery location and timeline should we use for planning?",
        ][:5]
    if "project_supply" in routes:
        return [
            "Is this tied to a specific FF&E or office buildout project?",
            "What quantity range and timeline should we consider?",
            "Would a catalog, specification overview, or sample discussion help the next step?",
        ]
    if "jooboo_education_furniture" in routes:
        return [
            "Is this for classroom, training room, or campus furniture procurement?",
            "Do you have an RFP timeline or estimated volume?",
            "Are you looking for standard models or configurable options?",
        ]
    if "oem_odm_components" in routes:
        return [
            "Are you looking for private label, component sourcing, or custom development?",
            "Which components are most relevant: lifting columns, desk legs, frames, or control systems?",
            "What volume range and customization requirements should we consider?",
        ]
    return [
        "Which product type is most relevant for your current evaluation?",
        "What quantity range and timeline should we consider?",
        "What delivery location should we use for planning?",
    ][:5]


def _recommended_next_step(status: str, priority: str, inp: QuoteHandoffInput) -> str:
    if status == "ready_for_manual_quote_prep":
        return (
            "Confirm latest customer context, then prepare a human-reviewed quote outline "
            "for internal or partner review — no auto-generated quote."
        )
    if status == "needs_customer_clarification":
        return (
            "Send customer clarification questions, update the lead profile after replies, "
            "then revisit handoff before formal quote preparation."
        )
    if inp.recommended_next_action:
        return inp.recommended_next_action
    return "Complete contact research and product qualification before quote handoff."


def _format_brief_text(
    inp: QuoteHandoffInput,
    status: str,
    priority: str,
    routes: list[str],
    scope: list[str],
    known: list[str],
    missing: list[str],
    questions: list[str],
    supplier: list[str],
    next_step: str,
) -> str:
    route_text = "; ".join(ROUTE_LABELS.get(r, r) for r in routes) or "—"
    scope_text = "; ".join(SCOPE_LABELS.get(s, s.replace("_", " ")) for s in scope) or "—"
    status_label = status.replace("_", " ").title()
    lines = [
        f"Quote Handoff Brief — {inp.company_name}",
        "",
        f"Handoff status: {status_label}",
        f"Priority: {priority.title()}",
        f"Recommended route: {route_text}",
        f"Product scope: {scope_text}",
        "",
        "Known context:",
    ]
    for ctx in known:
        lines.append(f"- {ctx}")
    lines.extend(["", "Missing customer information:"])
    if missing:
        for m in missing:
            lines.append(f"- {_label(m)}")
    else:
        lines.append("- None flagged — still confirm latest specs with customer.")
    lines.extend(["", "Customer clarification questions:"])
    for i, q in enumerate(questions, 1):
        lines.append(f"{i}. {q}")
    lines.extend(["", "Internal preparation notes:"])
    for n in supplier:
        lines.append(f"- {n}")
    lines.extend(
        [
            "",
            f"Recommended next step: {next_step}",
            "",
            "Safety:",
            "This is an internal handoff brief only. It does not create a quote, generate pricing, "
            "promise inventory, confirm certification, or commit to lead time.",
        ]
    )
    return "\n".join(lines)


def build_quote_handoff_brief(inp: QuoteHandoffInput) -> dict[str, Any]:
    """Derive soft quote handoff brief — no DB writes, no quote creation."""
    routes = _partner_routes(inp.recommended_product_focus)
    scope = _product_scope(inp.recommended_product_focus)
    missing = _missing_customer_info(inp)
    status = _handoff_status(inp, missing)
    priority = _handoff_priority(inp, routes)
    known = _known_context(inp, routes)
    supplier = _supplier_notes(routes, inp.recommended_product_focus, status)
    questions = _customer_questions(inp, routes)
    next_step = _recommended_next_step(status, priority, inp)

    brief_text = _format_brief_text(
        inp, status, priority, routes, scope, known, missing, questions, supplier, next_step
    )
    supplier_text = "\n".join(f"- {n}" for n in supplier)
    questions_text = "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))

    warnings = [
        "Internal preparation aid only — not a quote, order, or customer-facing commitment.",
        "No pricing, inventory, certification, or lead-time commitments are generated.",
    ]
    if status == "not_ready":
        warnings.append("Lead is not ready for quote handoff — complete discovery first.")
    if status == "ready_for_manual_quote_prep":
        warnings.append("Ready for manual prep means information sufficiency — still requires human-reviewed quote.")

    return {
        "lead_id": inp.lead_id,
        "company_name": inp.company_name,
        "handoff_status": status,
        "handoff_priority": priority,
        "quote_readiness": inp.quote_readiness,
        "sample_readiness": inp.sample_readiness,
        "opportunity_score": inp.opportunity_score,
        "recommended_partner_route": routes,
        "recommended_product_scope": scope,
        "known_context": known,
        "missing_customer_info": missing,
        "supplier_preparation_notes": supplier,
        "customer_clarification_questions": questions,
        "recommended_next_step": next_step,
        "quote_handoff_brief_text": brief_text,
        "supplier_notes_text": supplier_text,
        "customer_questions_text": questions_text,
        "safety": dict(PRE_QUOTE_SAFETY),
        "warnings": warnings,
    }


def assert_no_forbidden_handoff_phrases(text: str) -> None:
    lower = text.lower()
    for phrase in FORBIDDEN_HANDOFF_PHRASES:
        if phrase in lower:
            raise ValueError(f"Forbidden phrase in handoff brief: {phrase}")
