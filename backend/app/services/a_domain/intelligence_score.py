"""Deterministic lead intelligence scoring (D5) — no partner name bias, market-focus heuristics."""

from __future__ import annotations

from dataclasses import dataclass

# Signals aligned with product_vision: height-adjustable / ergonomic / project-table demand
ERGONOMIC_KEYWORD_WEIGHT = 4
ERGONOMIC_KEYWORDS: frozenset[str] = frozenset(
    {
        "height adjustable desk",
        "height-adjustable desk",
        "sit-stand desk",
        "sit stand desk",
        "sit-stand",
        "sit stand",
        "adjustable desk frame",
        "adjustable desk",
        "lifting column",
        "lifting leg",
        "lift column",
        "desk leg",
        "desk frame",
        "heavy-duty adjustable desk",
        "heavy duty adjustable desk",
        "heavy duty adjustable",
        "ergonomic workstation",
        "medical workstation",
        "education adjustable table",
        "education adjustable",
        "electric desk",
        "standing desk",
        "height adjustable",
        "height-adjustable",
    }
)

# D5.1: broad office-furniture industry without (yet) explicit lift-system cues
GENERAL_OFFICE_FURNITURE_SIGNALS: frozenset[str] = frozenset(
    {
        "office furniture",
        "contract furniture",
        "commercial furniture",
        "workplace furniture",
        "furniture dealer",
        "office furnishings",
        "commercial interiors",
    }
)

# Phrases for OEM/ODM / project lift (not counted in generic ergonomic cap — see segments)
OEM_ODM_SIGNALS: frozenset[str] = frozenset(
    {
        "oem lifting",
        "odm lifting",
        "oem/odm",
        "odm solution",
        "oem solution",
        "lifting solution",
        "private label",
        "custom actuator",
    }
)

MEDICAL_SIGNALS: frozenset[str] = frozenset(
    {
        "medical workstation",
        "healthcare furniture",
        "hospital furniture",
        "patient care",
        "medical furniture",
        "lab bench",
        "lab furniture",
        "laboratory workstation",
        "healthcare workstation",
        "medical-grade",
        "medical grade",
        "clinical workstation",
        "examination table",
        "nurse station",
        "clinic furniture",
    }
)

PROJECT_BASED_FURNITURE_SIGNALS: frozenset[str] = frozenset(
    {
        "project furniture",
        "contract interiors",
        "furniture installation",
        "workplace project",
        "ff&e",
        "project procurement",
        "office buildout",
        "office build-out",
        "dealer project",
        "installation service",
        "corporate interiors",
        "project-based furniture",
        "contract project",
    }
)

EDUCATION_SIGNALS: frozenset[str] = frozenset(
    {
        "education adjustable table",
        "education adjustable",
        "school furniture",
        "classroom table",
        "campus furniture",
    }
)

HEAVY_DUTY_SIGNALS: frozenset[str] = frozenset(
    {
        "heavy-duty adjustable",
        "heavy duty adjustable",
        "industrial height adjustable",
        "重载",
        "heavy load desk",
    }
)


@dataclass
class IntelligenceScoreInput:
    has_primary_contact: bool
    market_intel_count: int
    product_interest_tags: str | None
    business_description: str | None
    lead_product_interest: str | None
    lead_priority: str | None
    company_strategic_level: str | None


@dataclass(frozen=True)
class IntelligenceScoreResult:
    """Structured result for Lead Intelligence scoring (D5.1 — avoids growing positional tuples)."""

    score: int
    breakdown: dict[str, int]
    suggestions: list[str]
    market_fit_segments: list[str]


def _text_blob(inp: IntelligenceScoreInput) -> str:
    parts = [
        inp.product_interest_tags or "",
        inp.business_description or "",
        inp.lead_product_interest or "",
    ]
    return " \n ".join(parts).lower()


def _any_signal(text: str, phrases: frozenset[str]) -> bool:
    return any(p in text for p in phrases)


def _ergonomic_keyword_score(text: str) -> int:
    score = 0
    for kw in ERGONOMIC_KEYWORDS:
        if kw in text:
            score += ERGONOMIC_KEYWORD_WEIGHT
    return min(score, 28)


def _lift_system_signal_present(blob: str) -> bool:
    """True iff lift_system_signal would be assigned (explicit lift / height-adjustable vocabulary)."""
    return _ergonomic_keyword_score(blob) > 0


def _oem_odm_fit_present(blob: str) -> bool:
    """Same predicate as oem_odm_fit segment (lift/frame context required)."""
    return _any_signal(blob, OEM_ODM_SIGNALS) and (
        _lift_system_signal_present(blob)
        or "lift" in blob
        or "column" in blob
        or "leg" in blob
        or "frame" in blob
        or "desk" in blob
        or "table" in blob
        or "adjustable" in blob
    )


def infer_market_fit_segments(blob: str) -> list[str]:
    """
    Explainable segment tags (API-stable slugs). Overlapping is allowed — except
    general_office_furniture_only MUST NOT co-occur with lift_system_signal (D5.1).
    """
    segments: list[str] = []
    if _lift_system_signal_present(blob):
        segments.append("lift_system_signal")
    if _oem_odm_fit_present(blob):
        segments.append("oem_odm_fit")
    if _any_signal(blob, MEDICAL_SIGNALS):
        segments.append("medical_vertical")
    if _any_signal(blob, EDUCATION_SIGNALS):
        segments.append("education_vertical")
    if _any_signal(blob, HEAVY_DUTY_SIGNALS):
        segments.append("heavy_duty_fit")
    if _any_signal(blob, PROJECT_BASED_FURNITURE_SIGNALS):
        segments.append("project_based_furniture")

    # D5.1 weak-fit: industry-related office furniture, no lift-system evidence (and no stronger vertical)
    has_stronger_vertical = (
        _oem_odm_fit_present(blob)
        or _any_signal(blob, MEDICAL_SIGNALS)
        or _any_signal(blob, EDUCATION_SIGNALS)
        or _any_signal(blob, HEAVY_DUTY_SIGNALS)
        or _any_signal(blob, PROJECT_BASED_FURNITURE_SIGNALS)
    )
    if (
        _any_signal(blob, GENERAL_OFFICE_FURNITURE_SIGNALS)
        and not _lift_system_signal_present(blob)
        and not has_stronger_vertical
    ):
        segments.append("general_office_furniture_only")

    seen: set[str] = set()
    out: list[str] = []
    for s in segments:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _segment_suggestions(segments: list[str]) -> list[str]:
    sug: list[str] = []
    if "general_office_furniture_only" in segments:
        sug.append(
            "标签「一般办公家具相关」：属于办公家具相关行业，但当前尚未看到明确升降桌、桌架、桌腿、升降柱等意向；"
            "可低频维护，或待公开信息补充后再判断是否转入升降系统重点跟进（非负面，仅分层）。"
        )
    if "oem_odm_fit" in segments:
        sug.append(
            "场景：OEM/ODM 或项目制升降方案 — 建议核对图纸、认证、MOQ 与工程接口，避免仅用标准品话术。"
        )
    if "medical_vertical" in segments:
        sug.append("场景：医疗/医护工作站 — 建议确认护栏、清洁、静音与合规文档需求。")
    if "education_vertical" in segments:
        sug.append("场景：教育可调桌 — 建议关注批量、交付节奏、现场安装与安全规范。")
    if "project_based_furniture" in segments:
        sug.append(
            "场景：项目制家具 / 合同内装 — 建议核对 FF&E 清单、安装窗口、样品与报价节奏，区分标准品与定制项。"
        )
    if "heavy_duty_fit" in segments:
        sug.append("场景：重载/工业级升降 — 建议核实承重、行程、同步与使用环境。")
    if "lift_system_signal" in segments and "oem_odm_fit" not in segments:
        sug.append(
            "已识别升降系统兴趣信号：区分渠道批发（标准品）与项目制客户，再匹配品类与工厂能力（按品类，不按单一伙伴名称）。"
        )
    return sug


def _priority_points(priority: str | None) -> int:
    if not priority:
        return 0
    p = priority.lower()
    if p == "high":
        return 15
    if p == "medium":
        return 10
    if p == "low":
        return 5
    return 5


def _strategic_points(level: str | None) -> int:
    if not level:
        return 0
    l = level.lower()
    if ("tier" in l and "1" in l) or l in ("strategic", "key", "vip"):
        return 12
    if "tier" in l and "2" in l:
        return 8
    if "tier" in l and "3" in l:
        return 5
    return 4


def compute_intelligence_score(inp: IntelligenceScoreInput) -> IntelligenceScoreResult:
    """
    Explainable score 0–100; suggestions + market_fit_segments.
    general_office_furniture_only does not change the numeric total (D5.1).
    """
    blob = _text_blob(inp)
    segments = infer_market_fit_segments(blob)

    breakdown: dict[str, int] = {}
    suggestions: list[str] = []

    base = 18
    breakdown["base"] = base

    contact_pts = 18 if inp.has_primary_contact else 0
    breakdown["primary_contact"] = contact_pts
    if not inp.has_primary_contact:
        suggestions.append("关联或创建主联系人以便执行情报→销售闭环。")

    mi_pts = min(inp.market_intel_count * 8, 24)
    breakdown["market_intelligence_items"] = mi_pts
    if inp.market_intel_count == 0:
        suggestions.append("在「市场情报」中关联该公司，沉淀升降 / 工装品类信号。")

    ergo = _ergonomic_keyword_score(blob)
    breakdown["ergonomic_market_fit"] = ergo
    if ergo < 8:
        suggestions.append(
            "在公司的 product interest 或商机描述中补充人体工学 / 升降系统（桌架、桌腿、升降柱等）关键词，便于与战略品类对齐。"
        )

    pri = _priority_points(inp.lead_priority)
    breakdown["lead_priority"] = pri

    strat = _strategic_points(inp.company_strategic_level)
    breakdown["strategic_level"] = strat

    total = min(
        100,
        base + contact_pts + mi_pts + ergo + pri + strat,
    )

    if total >= 70:
        suggestions.append("高分线索：建议记录一次跟进并设定明确的 next action。")
    elif total >= 45:
        suggestions.append("中等热度：可安排需求确认或样品路径相关的下一步。")

    suggestions.extend(_segment_suggestions(segments))

    seen: set[str] = set()
    uniq: list[str] = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            uniq.append(s)

    return IntelligenceScoreResult(
        score=total,
        breakdown=breakdown,
        suggestions=uniq,
        market_fit_segments=segments,
    )
