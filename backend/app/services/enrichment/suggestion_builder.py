"""Derive enrichment suggestions from fetched sources using existing A-domain rules (D5.2)."""

from __future__ import annotations

import json
from typing import Any

from app.models.enrichment import (
    FETCH_OK,
    REVIEW_PENDING,
    SUGGESTION_BUSINESS_SUMMARY,
    SUGGESTION_MARKET_SEGMENT,
    SUGGESTION_SCORE_HINT,
    SUGGESTION_TAG,
    CompanyEnrichmentSource,
)
from app.services.a_domain.intelligence_score import (
    IntelligenceScoreInput,
    compute_intelligence_score,
    infer_market_fit_segments,
)

TAG_SUGGESTION_RULES: tuple[tuple[str, str, str], ...] = (
    ("height adjustable desk", "height_adjustable_desk", "页面文本出现 height adjustable desk（升降桌相关）"),
    ("height-adjustable desk", "height_adjustable_desk", "页面文本出现 height-adjustable desk"),
    ("sit-stand desk", "sit_stand", "页面文本出现 sit-stand desk"),
    ("sit stand desk", "sit_stand", "页面文本出现 sit stand desk"),
    ("adjustable desk frame", "desk_frame_interest", "页面文本出现 adjustable desk frame"),
    ("desk frame", "desk_frame_interest", "页面文本出现 desk frame"),
    ("lifting column", "lifting_column_interest", "页面文本出现 lifting column"),
    ("lifting leg", "lifting_leg_interest", "页面文本出现 lifting leg"),
    ("heavy duty adjustable", "heavy_duty_interest", "页面文本出现 heavy duty adjustable"),
    ("ergonomic workstation", "ergonomic_solution", "页面文本出现 ergonomic workstation"),
    ("medical workstation", "healthcare_market", "页面文本出现 medical workstation"),
    ("education adjustable", "education_market", "页面文本出现 education adjustable"),
    ("oem lifting", "oem_odm_candidate", "页面文本出现 OEM/lifting 组合信号"),
    ("odm lifting", "oem_odm_candidate", "页面文本出现 ODM/lifting 组合信号"),
    ("furniture dealer", "importer", "页面文本出现 furniture dealer"),
    ("furniture showroom", "showroom", "页面文本出现 furniture showroom"),
    ("office furniture", "importer", "页面文本出现 office furniture（渠道/办公家具）"),
    ("contract furniture", "importer", "页面文本出现 contract furniture"),
    ("installation services", "installer", "页面文本出现 installation 服务"),
    ("project furniture", "project_buyer", "页面文本出现 project furniture"),
)


def _snippet_around(full: str, phrase: str, width: int = 160) -> str:
    low = full.lower()
    p = phrase.lower()
    i = low.find(p)
    if i < 0:
        t = " ".join(full.split())
        return (t[:width] + "…") if len(t) > width else t
    start = max(0, i - width // 2)
    end = min(len(full), i + len(phrase) + width // 2)
    chunk = full[start:end].strip()
    return chunk + ("…" if end < len(full) else "")


def _first_source_for_needle(
    sources: list[CompanyEnrichmentSource], needle: str
) -> CompanyEnrichmentSource | None:
    n = needle.lower()
    for s in sources:
        if s.fetch_status != FETCH_OK or not s.content_text:
            continue
        if n in s.content_text.lower():
            return s
    return None


def _first_source_for_segment(
    sources: list[CompanyEnrichmentSource], segment: str
) -> CompanyEnrichmentSource | None:
    for s in sources:
        if s.fetch_status != FETCH_OK or not s.content_text:
            continue
        blob = s.content_text.lower()
        if segment in infer_market_fit_segments(blob):
            return s
    return None


def build_suggestion_dicts(
    sources: list[CompanyEnrichmentSource],
    company_name: str,
) -> list[dict[str, Any]]:
    """Produce rows compatible with CompanyEnrichmentSuggestion(...)."""
    ok_sources = [s for s in sources if s.fetch_status == FETCH_OK and s.content_text]
    crawl_blob_lower = "\n\n".join(
        f"--- {s.url} ---\n{s.content_text.lower()}" for s in ok_sources
    )
    crawl_blob = "\n\n".join(f"--- {s.url} ---\n{(s.content_text or '')}" for s in ok_sources)

    out: list[dict[str, Any]] = []
    seen_tag: set[str] = set()
    seen_seg: set[str] = set()

    # Segments from combined evidence
    segments = infer_market_fit_segments(crawl_blob_lower)
    for seg in segments:
        if seg in seen_seg:
            continue
        seen_seg.add(seg)
        ev = _first_source_for_segment(ok_sources, seg)
        snippet = (ev.content_excerpt or None) if ev else None
        out.append(
            {
                "suggestion_type": SUGGESTION_MARKET_SEGMENT,
                "suggested_value": seg,
                "confidence": "rule:segment_v1",
                "reason": f"基于公开页正文聚合推断 segment「{seg}」（与 Lead Intelligence 规则一致）。",
                "evidence_source_id": ev.id if ev else None,
                "evidence_snippet": snippet[:2000] if snippet else None,
                "matched_phrase": seg,
                "review_status": REVIEW_PENDING,
            }
        )

    # Tag rules
    for needle, tag_slug, reason in TAG_SUGGESTION_RULES:
        if needle not in crawl_blob_lower or tag_slug in seen_tag:
            continue
        seen_tag.add(tag_slug)
        ev = _first_source_for_needle(ok_sources, needle)
        out.append(
            {
                "suggestion_type": SUGGESTION_TAG,
                "suggested_value": tag_slug,
                "confidence": "rule:keyword_v1",
                "reason": reason,
                "evidence_source_id": ev.id if ev else None,
                "evidence_snippet": (_snippet_around(ev.content_text, needle) if ev else "")[:2000]
                or None,
                "matched_phrase": needle,
                "review_status": REVIEW_PENDING,
            }
        )

    # Business summary (conservative, evidence-first)
    titles = [s.page_title for s in ok_sources if s.page_title]
    lift_hit = any(
        k in crawl_blob_lower
        for k in (
            "height adjustable",
            "sit-stand",
            "lifting column",
            "desk frame",
            "standing desk",
        )
    )
    office_hit = "office furniture" in crawl_blob_lower or "contract furniture" in crawl_blob_lower
    parts = [
        f"根据 {len(ok_sources)} 个已成功抓取的公开页面整理的草稿摘要（需人工审阅，不得视为事实）：",
        f"公司：{company_name}。",
    ]
    if titles:
        parts.append("页面标题包括：" + "；".join(titles[:8]) + ("…" if len(titles) > 8 else "") + "。")
    if lift_hit:
        parts.append("文本中出现可调/升降/桌架或立柱等相关措辞，建议复核是否与升降系统业务相关。")
    elif office_hit:
        parts.append("文本主要为广义办公家具/合同家具表述，尚未观察到明确升降系统强信号，可考虑弱分层或继续 enrichment。")
    else:
        parts.append("当前页面词面较泛，建议在审阅后再补充关键字或等待更多来源。")
    summary_text = "".join(parts)
    primary = ok_sources[0] if ok_sources else None
    out.append(
        {
            "suggestion_type": SUGGESTION_BUSINESS_SUMMARY,
            "suggested_value": summary_text,
            "confidence": "rule:assembly_v1",
            "reason": "由页面标题与关键词规则拼装的业务摘要草稿（非 LLM 武断结论）。",
            "evidence_source_id": primary.id if primary else None,
            "evidence_snippet": (primary.content_excerpt if primary else None),
            "matched_phrase": None,
            "review_status": REVIEW_PENDING,
        }
    )

    # Score hint — synthetic profile from crawl only (does not write to CRM)
    lim = min(len(crawl_blob), 50_000)
    score_r = compute_intelligence_score(
        IntelligenceScoreInput(
            has_primary_contact=False,
            market_intel_count=0,
            product_interest_tags=None,
            business_description=crawl_blob[:lim],
            lead_product_interest=None,
            lead_priority=None,
            company_strategic_level=None,
        )
    )
    out.append(
        {
            "suggestion_type": SUGGESTION_SCORE_HINT,
            "suggested_value": json.dumps(
                {
                    "score": score_r.score,
                    "breakdown": score_r.breakdown,
                    "suggestions": score_r.suggestions,
                    "market_fit_segments": score_r.market_fit_segments,
                    "source": "rule_based_crawl_only_candidate",
                },
                ensure_ascii=False,
            ),
            "confidence": "rule:intelligence_score_v1",
            "reason": "若将公开页正文视为唯一描述时的规则评分候选；正式 Lead 评分仍以 CRM 人工字段为准。",
            "evidence_source_id": primary.id if primary else None,
            "evidence_snippet": (primary.content_excerpt[:500] if primary and primary.content_excerpt else None),
            "matched_phrase": None,
            "review_status": REVIEW_PENDING,
        }
    )

    return out
