from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import AIOutput, User
from app.schemas.ai import AIOutputOut, AIOutputUpdate, GenericAIRequest
from app.schemas.pagination import PaginatedResponse
from app.services.ai import client as ai_client
from app.services.ai import prompts as prompt_lib
from app.services.activity import log_activity

router = APIRouter(prefix="/ai", tags=["ai"])


def _save_output(
    db: Session,
    *,
    user: User,
    task_type: str,
    text: str,
    prompt_dump: str,
    input_object_type: str | None,
    input_object_id: UUID | None,
) -> AIOutput:
    settings = get_settings()
    row = AIOutput(
        task_type=task_type,
        input_object_type=input_object_type,
        input_object_id=input_object_id,
        prompt=prompt_dump[:50000],
        model=settings.DEFAULT_MODEL,
        output_text=text,
        status="draft",
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    if input_object_type and input_object_id:
        log_activity(
            db,
            object_type=input_object_type,
            object_id=input_object_id,
            action="ai_output_generated",
            actor_id=user.id,
            diff={"ai_output_id": str(row.id), "task_type": task_type},
        )
    else:
        log_activity(
            db,
            object_type="ai_output",
            object_id=row.id,
            action="ai_output_generated",
            actor_id=user.id,
            diff={"task_type": task_type},
        )
    db.commit()
    return row


@router.post("/linkedin-note", response_model=AIOutputOut)
def ai_linkedin_note(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.linkedin_connection_note_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    out = ai_client.truncate_linkedin_note(out)
    row = _save_output(
        db,
        user=user,
        task_type="linkedin_note",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/follow-up", response_model=AIOutputOut)
def ai_follow_up(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.follow_up_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="linkedin_follow_up",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/email", response_model=AIOutputOut)
def ai_email(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.email_generation_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="email_generation",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/customer-profile", response_model=AIOutputOut)
def ai_customer_profile(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.customer_profile_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="customer_profile",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/product-recommendation", response_model=AIOutputOut)
def ai_product_recommendation(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.customer_profile_prompt({"task": "product fit", **body.context})
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="product_recommendation",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/partner-recommendation", response_model=AIOutputOut)
def ai_partner_recommendation(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.partner_recommendation_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="partner_recommendation",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/supplier-risk-summary", response_model=AIOutputOut)
def ai_supplier_risk(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.supplier_risk_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="supplier_risk_summary",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/field-visit-brief", response_model=AIOutputOut)
def ai_field_brief(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.field_visit_brief_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="field_visit_brief",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/market-summary", response_model=AIOutputOut)
def ai_market_summary(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.market_trend_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="market_trend_summary",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/rfq-summary", response_model=AIOutputOut)
def ai_rfq_summary(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.rfq_summary_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="rfq_summary",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/quotation-analysis", response_model=AIOutputOut)
def ai_quotation_analysis(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.quotation_analysis_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="quotation_analysis",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/rfq-requirement-summary", response_model=AIOutputOut)
def ai_rfq_requirement_summary(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    return ai_rfq_summary(body, db, user)


@router.post("/compare-partner-quotations", response_model=AIOutputOut)
def ai_compare_partner_quotations(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.compare_partner_quotations_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="compare_partner_quotations",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/customer-quotation-email", response_model=AIOutputOut)
def ai_customer_quotation_email(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.customer_quotation_email_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="customer_quotation_email",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/partner-quote-request-email", response_model=AIOutputOut)
def ai_partner_quote_request_email(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.partner_quote_request_email_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="partner_quote_request_email",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/rfq-follow-up-email", response_model=AIOutputOut)
def ai_rfq_follow_up_email(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.rfq_follow_up_email_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="rfq_follow_up_email",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/rfq-missing-information-checklist", response_model=AIOutputOut)
def ai_rfq_missing_information_checklist(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.rfq_missing_information_checklist_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="rfq_missing_information_checklist",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/rfq-internal-risk-summary", response_model=AIOutputOut)
def ai_rfq_internal_risk_summary(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.rfq_internal_risk_summary_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="rfq_internal_risk_summary",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/order-update-email", response_model=AIOutputOut)
def ai_order_update_email(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.order_update_email_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="order_update_email",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/company-outreach-strategy", response_model=AIOutputOut)
def ai_company_outreach_strategy(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.company_outreach_strategy_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="company_outreach_strategy",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/recommend-product-categories", response_model=AIOutputOut)
def ai_recommend_product_categories(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.recommend_product_categories_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="recommend_product_categories",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/partner-english-summary", response_model=AIOutputOut)
def ai_partner_english_summary(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.partner_english_summary_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="partner_english_summary",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/partner-product-fit", response_model=AIOutputOut)
def ai_partner_product_fit(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.partner_product_fit_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="partner_product_fit",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/partner-missing-info-checklist", response_model=AIOutputOut)
def ai_partner_missing_info(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.partner_missing_information_checklist_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="partner_missing_info_checklist",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/product-english-description", response_model=AIOutputOut)
def ai_product_english_description(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.product_english_description_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="product_english_description",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/product-short-sales-paragraph", response_model=AIOutputOut)
def ai_product_short_sales(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.product_short_sales_paragraph_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="product_short_sales_paragraph",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/recommend-customer-types", response_model=AIOutputOut)
def ai_recommend_customer_types(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.recommend_customer_types_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="recommend_customer_types",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/email-paragraph", response_model=AIOutputOut)
def ai_email_paragraph(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.email_paragraph_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="email_paragraph",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/linkedin-product-message", response_model=AIOutputOut)
def ai_linkedin_product_message(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.linkedin_product_message_prompt(body.context)
    out = ai_client.truncate_linkedin_note(ai_client.chat_completion(msgs))
    row = _save_output(
        db,
        user=user,
        task_type="linkedin_product_message",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/contact-role-analysis", response_model=AIOutputOut)
def ai_contact_role_analysis(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.contact_role_analysis_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="contact_role_analysis",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/meeting-request-email", response_model=AIOutputOut)
def ai_meeting_request_email(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.meeting_request_email_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="meeting_request_email",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/match-partners-for-product", response_model=AIOutputOut)
def ai_match_partners_for_product(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.partner_recommendation_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="match_partners_for_product",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/product-sales-description", response_model=AIOutputOut)
def ai_product_sales_description(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.product_sales_description_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="product_sales_description",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/sample-follow-up-email", response_model=AIOutputOut)
def ai_sample_follow_up_email(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.sample_follow_up_email_ai_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="sample_follow_up_email",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/sample-feedback-request", response_model=AIOutputOut)
def ai_sample_feedback_request(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.sample_feedback_request_ai_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="sample_feedback_request",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/sample-internal-risk-summary", response_model=AIOutputOut)
def ai_sample_internal_risk_summary(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.sample_internal_risk_summary_ai_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="sample_internal_risk_summary",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/sample-customer-update", response_model=AIOutputOut)
def ai_sample_customer_update(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.sample_customer_update_ai_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="sample_customer_update_message",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/sample-next-step-recommendation", response_model=AIOutputOut)
def ai_sample_next_step_recommendation(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.sample_next_step_recommendation_ai_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="sample_next_step_recommendation",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/order-delay-explanation-email", response_model=AIOutputOut)
def ai_order_delay_explanation_email(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.order_delay_explanation_ai_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="order_delay_explanation_email",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/order-internal-risk-summary", response_model=AIOutputOut)
def ai_order_internal_risk_summary(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.order_internal_risk_summary_ai_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="order_internal_risk_summary",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/order-shipping-status-update", response_model=AIOutputOut)
def ai_order_shipping_status_update(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.order_shipping_status_update_ai_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="order_shipping_status_update",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/order-partner-followup", response_model=AIOutputOut)
def ai_order_partner_followup(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.order_partner_followup_ai_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="order_partner_followup",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.post("/order-next-step-recommendation", response_model=AIOutputOut)
def ai_order_next_step_recommendation(
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    msgs = prompt_lib.order_next_step_recommendation_ai_prompt(body.context)
    out = ai_client.chat_completion(msgs)
    row = _save_output(
        db,
        user=user,
        task_type="order_next_step_recommendation",
        text=out,
        prompt_dump=str(msgs),
        input_object_type=body.input_object_type,
        input_object_id=body.input_object_id,
    )
    return AIOutputOut.model_validate(row)


@router.get("/outputs", response_model=PaginatedResponse[AIOutputOut])
def list_outputs(
    task_type: str | None = None,
    object_type: str | None = None,
    object_id: UUID | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[AIOutputOut]:
    q = db.query(AIOutput)
    if task_type:
        q = q.filter(AIOutput.task_type == task_type)
    if object_type:
        q = q.filter(AIOutput.input_object_type == object_type)
    if object_id:
        q = q.filter(AIOutput.input_object_id == object_id)
    total = q.count()
    rows = q.order_by(AIOutput.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(items=[AIOutputOut.model_validate(r) for r in rows], total=total, page=page, limit=limit)


@router.put("/outputs/{output_id}", response_model=AIOutputOut)
def update_output(
    output_id: UUID,
    body: AIOutputUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIOutputOut:
    row = db.query(AIOutput).filter(AIOutput.id == output_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="AI output not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    return AIOutputOut.model_validate(row)
