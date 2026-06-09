from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel


PartnerOnboardingStage = Literal[
    "discovery",
    "product_mapping",
    "quote_ready",
    "portal_ready",
    "demo_ready",
    "active_partner",
    "paused",
]


class PartnerOnboardingChecklistItem(BaseModel):
    key: str
    label: str
    done: bool
    detail: str


class PartnerOnboardingLinks(BaseModel):
    partner_detail: str
    product_catalog: str
    demo_walkthrough: str
    market_response: str
    orders: str


class PartnerOnboardingRecord(BaseModel):
    partner_id: UUID
    partner_name: str
    partner_code: str | None
    partner_type: str | None
    product_focus: list[str]
    target_markets: list[str]
    onboarding_stage: PartnerOnboardingStage
    readiness_score: int
    readiness_summary: str
    missing_items: list[str]
    next_action: str
    checklist: list[PartnerOnboardingChecklistItem]
    links: PartnerOnboardingLinks
    is_reference_partner: bool
    safety: dict[str, bool]


class PartnerOnboardingSummary(BaseModel):
    total_partners: int
    reference_partner_count: int
    demo_ready_count: int
    quote_ready_count: int
    portal_ready_count: int
    active_partner_count: int
    paused_count: int
    safety: dict[str, bool]


class PartnerOnboardingResponse(BaseModel):
    status: str
    stage_order: list[str]
    checklist_keys: list[str]
    summary: PartnerOnboardingSummary
    items: list[PartnerOnboardingRecord]
    future_partner_placeholder: PartnerOnboardingRecord | None
    safety: dict[str, bool]

