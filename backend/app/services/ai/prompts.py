SYSTEM_NO_HOSUN_BIAS = (
    "You assist intelliOffice (US market brand). Manufacturing partners are equal; never assume any "
    "factory is the default or parent brand. Be factual, professional, not hype."
)

RFQ_AI_BIAS_GUARD = (
    " All manufacturing partners are equal-level partners. Do not prioritize HOSUN, JOOBOO, or any partner by name. "
    "Compare using only available data: product fit, certification, MOQ, lead time, price, sample support, "
    "partner quality_rating when present, communication/project suitability if present. "
    "If information is insufficient, state what is missing; do not invent."
)


def _user_block(payload: dict) -> str:
    return "\n".join(f"{k}: {v}" for k, v in payload.items() if v)


def linkedin_connection_note_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + " Write a LinkedIn connection note in English, soft tone, under 300 characters.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def follow_up_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + " Write a concise English follow-up for LinkedIn or email.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def email_generation_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + " Write a full professional B2B email in English.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def customer_profile_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + " Summarize customer profile, fit, and recommended next steps.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def partner_recommendation_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + RFQ_AI_BIAS_GUARD
            + " Recommend manufacturing partners with equal comparison, rationale, risks, open questions.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def supplier_risk_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + " Summarize strengths, risks, missing info, next actions.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def field_visit_brief_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + " Produce a field visit brief: visit order, talking points, materials to bring, follow-up.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def order_update_email_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + " Draft a customer-facing English order status update email.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def market_trend_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + " Summarize trend, opportunity, threat, suggested action for intelliOffice.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def product_sales_description_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + " Write concise English sales copy for the product.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def rfq_summary_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + RFQ_AI_BIAS_GUARD + " Summarize RFQ requirements and internal checklist for quoting.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def quotation_analysis_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + RFQ_AI_BIAS_GUARD + " Analyze pricing/margin/logistics risks for the quote.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def compare_partner_quotations_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + RFQ_AI_BIAS_GUARD
            + " Compare partner quotations side-by-side in English; use only numeric/text fields given; note tradeoffs and gaps.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def customer_quotation_email_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + RFQ_AI_BIAS_GUARD + " Draft a professional customer-facing quotation email in English (no factory favoritism).",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def partner_quote_request_email_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + RFQ_AI_BIAS_GUARD
            + " Draft an English email to request a formal quote from a manufacturing partner; neutral tone, clear specs and deadlines.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def rfq_follow_up_email_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + RFQ_AI_BIAS_GUARD + " Draft a concise English follow-up about this RFQ (customer or partner as indicated in context).",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def rfq_missing_information_checklist_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + RFQ_AI_BIAS_GUARD + " Produce a bullet checklist of missing RFQ/quote information; do not assume unstated factory strengths.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def rfq_internal_risk_summary_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + RFQ_AI_BIAS_GUARD + " Summarize internal commercial and delivery risks for this RFQ; cite only evidence from context.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def company_outreach_strategy_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + " Draft a neutral, actionable B2B outreach strategy (channels, cadence, open questions).",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def recommend_product_categories_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + " Suggest relevant product categories/tags for this account without favoring any factory.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def partner_english_summary_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + " Write a concise English supplier overview for internal use.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def partner_product_fit_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + " Analyze product fit vs stated capabilities; note gaps and verification steps.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def partner_missing_information_checklist_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + " List missing information as a checklist for qualification.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def product_english_description_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + " Write a clear English product description for US B2B buyers (specs + benefits).",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def product_short_sales_paragraph_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + " Write one short English sales paragraph (4-6 sentences).",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def recommend_customer_types_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + " Recommend plausible customer segments; stay neutral and evidence-based.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def email_paragraph_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + " Write one email-ready English paragraph for outreach.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def linkedin_product_message_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + " Write a short LinkedIn DM about this product, under 300 characters.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def contact_role_analysis_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + " Analyze the contact's likely role/influence and how to engage professionally.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def meeting_request_email_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + " Draft a concise English meeting request email.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def _sample_order_guard() -> str:
    return (
        RFQ_AI_BIAS_GUARD
        + " Base actions on fields and current status only. English; U.S. business tone. "
    )


def sample_follow_up_email_ai_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS + _sample_order_guard() + "Draft a concise sample follow-up email for the customer.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def sample_feedback_request_ai_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + _sample_order_guard()
            + "Ask politely for structured feedback on the sample (fit, quality, lead time, next steps).",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def sample_internal_risk_summary_ai_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + _sample_order_guard()
            + "Summarize internal risks and blockers for this sample (shipping, partner, cost, feedback). Bullet list.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def sample_customer_update_ai_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + _sample_order_guard()
            + "Draft a short customer-facing status update about the sample (no blame; factual).",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def sample_next_step_recommendation_ai_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + _sample_order_guard()
            + "Recommend concrete next internal and customer-facing actions for this sample.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def order_delay_explanation_ai_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + _sample_order_guard()
            + "Draft a professional delay explanation email tied to milestones or shipping facts only.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def order_internal_risk_summary_ai_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + _sample_order_guard()
            + "Summarize order risks from milestones, shipping, dates, and status fields. Bullet list.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def order_shipping_status_update_ai_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + _sample_order_guard()
            + "Draft a factual shipping status update (ETD/ETA/customs) without naming any partner as default.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def order_partner_followup_ai_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + _sample_order_guard()
            + "Draft an internal follow-up message to the assigned manufacturing partner about open production/shipping gaps.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]


def order_next_step_recommendation_ai_prompt(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_NO_HOSUN_BIAS
            + _sample_order_guard()
            + "Recommend prioritized next steps for production, shipping, and customer comms.",
        },
        {"role": "user", "content": _user_block(payload)},
    ]
