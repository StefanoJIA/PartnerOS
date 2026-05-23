"""Apply accepted enrichment suggestions to formal Company profile (D5.2)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.constants.object_type import ObjectType
from app.models import Company, Note, ObjectTag, Tag
from app.models.enrichment import (
    REVIEW_ACCEPTED,
    SUGGESTION_BUSINESS_SUMMARY,
    SUGGESTION_MARKET_SEGMENT,
    SUGGESTION_SCORE_HINT,
    SUGGESTION_TAG,
    CompanyEnrichmentRun,
    CompanyEnrichmentSuggestion,
)
from app.services.activity import log_activity


def _merge_csv(existing: str | None, token: str) -> str:
    parts = [p.strip() for p in (existing or "").split(",") if p.strip()]
    if token not in parts:
        parts.append(token)
    return ", ".join(parts)


def apply_enrichment_suggestion(
    db: Session,
    company_id: uuid.UUID,
    suggestion_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> CompanyEnrichmentSuggestion:
    sug = (
        db.query(CompanyEnrichmentSuggestion)
        .join(CompanyEnrichmentRun, CompanyEnrichmentSuggestion.enrichment_run_id == CompanyEnrichmentRun.id)
        .filter(
            CompanyEnrichmentSuggestion.id == suggestion_id,
            CompanyEnrichmentRun.company_id == company_id,
        )
        .first()
    )
    if not sug:
        raise ValueError("suggestion not found")
    if sug.review_status != REVIEW_ACCEPTED:
        raise ValueError("suggestion must be accepted before apply")

    company = db.get(Company, company_id)
    if not company:
        raise ValueError("company not found")

    if sug.suggestion_type == SUGGESTION_TAG and sug.suggested_value:
        name = sug.suggested_value.strip()
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name, created_by_id=actor_id, updated_by_id=actor_id)
            db.add(tag)
            db.flush()
        exists_ot = (
            db.query(ObjectTag)
            .filter(
                ObjectTag.object_type == ObjectType.company.value,
                ObjectTag.object_id == company_id,
                ObjectTag.tag_id == tag.id,
            )
            .first()
        )
        if not exists_ot:
            db.add(
                ObjectTag(
                    object_type=ObjectType.company.value,
                    object_id=company_id,
                    tag_id=tag.id,
                    created_by_id=actor_id,
                    updated_by_id=actor_id,
                )
            )
        log_activity(
            db,
            object_type=ObjectType.company.value,
            object_id=company_id,
            action="enrichment_tag_applied",
            actor_id=actor_id,
            diff={"suggestion_id": str(sug.id), "tag": name},
        )

    elif sug.suggestion_type == SUGGESTION_BUSINESS_SUMMARY and sug.suggested_value:
        company.business_description = sug.suggested_value.strip()
        company.updated_by_id = actor_id
        log_activity(
            db,
            object_type=ObjectType.company.value,
            object_id=company_id,
            action="enrichment_summary_applied",
            actor_id=actor_id,
            diff={"suggestion_id": str(sug.id)},
        )

    elif sug.suggestion_type == SUGGESTION_MARKET_SEGMENT and sug.suggested_value:
        token = sug.suggested_value.strip()
        company.product_interest_tags = _merge_csv(company.product_interest_tags, token)
        company.updated_by_id = actor_id
        log_activity(
            db,
            object_type=ObjectType.company.value,
            object_id=company_id,
            action="enrichment_segment_merged_to_tags",
            actor_id=actor_id,
            diff={"suggestion_id": str(sug.id), "segment": token},
        )

    elif sug.suggestion_type == SUGGESTION_SCORE_HINT and sug.suggested_value:
        body = (
            "[Enrichment score hint / 非正式评分]\n"
            + (sug.suggested_value or "")[:8000]
            + "\n\n来源：公开页 enrichment，仅供参考。"
        )
        db.add(
            Note(
                object_type=ObjectType.company.value,
                object_id=company_id,
                body=body,
                author_id=actor_id,
                created_by_id=actor_id,
                updated_by_id=actor_id,
            )
        )
        log_activity(
            db,
            object_type=ObjectType.company.value,
            object_id=company_id,
            action="enrichment_score_hint_noted",
            actor_id=actor_id,
            diff={"suggestion_id": str(sug.id)},
        )
    else:
        raise ValueError("unsupported suggestion type for apply")

    db.flush()
    return sug
