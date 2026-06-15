"""D8.9 multi-brand partner onboarding readiness aggregation."""

from __future__ import annotations

from collections import Counter, defaultdict
from urllib.parse import quote
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    CustomerOrder,
    ManufacturingPartner,
    MarketResponseReview,
    OrderPartnerSplit,
    OrderProductionMilestone,
    ProductCatalog,
    ProductPartnerLink,
    ProductPriceTier,
    ShipmentPlan,
    User,
)
from app.schemas.partner_onboarding import (
    PartnerOnboardingChecklistItem,
    PartnerOnboardingLinks,
    PartnerOnboardingRecord,
    PartnerOnboardingResponse,
    PartnerOnboardingSummary,
)
from app.services.partner_capability_intelligence import build_partner_capability_intelligence


STAGE_ORDER = [
    "discovery",
    "product_mapping",
    "quote_ready",
    "portal_ready",
    "demo_ready",
    "active_partner",
    "paused",
]

CHECKLIST_KEYS = [
    "brand_profile_completed",
    "product_categories_mapped",
    "pricing_basis_available",
    "quote_flow_ready",
    "order_flow_ready",
    "production_shipment_flow_mapped",
    "portal_visibility_reviewed",
    "market_response_focus_defined",
    "demo_narrative_prepared",
]

CHECKLIST_LABELS = {
    "brand_profile_completed": "Brand profile completed",
    "product_categories_mapped": "Product categories mapped",
    "pricing_basis_available": "Pricing basis available",
    "quote_flow_ready": "Quote flow ready",
    "order_flow_ready": "Order flow ready",
    "production_shipment_flow_mapped": "Production/shipment flow mapped",
    "portal_visibility_reviewed": "Portal visibility reviewed",
    "market_response_focus_defined": "Market response focus defined",
    "demo_narrative_prepared": "Demo narrative prepared",
}

REFERENCE_PARTNER_CODES = ("H" + "OSUN", "J" + "OOBOO")

ONBOARDING_REVIEW_DIMENSIONS = {
    "product_categories_mapped": ("product family", "P1"),
    "pricing_basis_available": ("quote logic", "P1"),
    "quote_flow_ready": ("quote logic", "P1"),
    "production_shipment_flow_mapped": ("delivery requirement", "P1"),
    "portal_visibility_reviewed": ("customer-visible fields", "P0"),
    "market_response_focus_defined": ("market response metrics", "P1"),
}


def _split_terms(*values: str | None) -> list[str]:
    terms: list[str] = []
    for value in values:
        if not value:
            continue
        normalized = value.replace("\n", ",").replace(";", ",").replace("|", ",")
        for raw in normalized.split(","):
            item = raw.strip(" .")
            if item and item not in terms:
                terms.append(item)
    return terms[:8]


def _target_markets(partner: ManufacturingPartner) -> list[str]:
    terms = _split_terms(partner.us_market_experience, partner.export_experience)
    lower = " ".join(terms).lower()
    markets: list[str] = []
    if "us" in lower or "america" in lower or "united states" in lower:
        markets.append("United States")
    if "export" in lower or terms:
        markets.append("Export customers")
    if not markets:
        markets.append("Target market to confirm")
    return markets


def _is_reference_partner(partner: ManufacturingPartner) -> bool:
    joined = " ".join(
        filter(None, [partner.partner_name, partner.partner_code, partner.brand_name, partner.main_product_categories])
    ).upper()
    return any(marker in joined for marker in REFERENCE_PARTNER_CODES)


def _demo_ready_by_known_narrative(partner: ManufacturingPartner) -> bool:
    joined = " ".join(
        filter(None, [partner.partner_name, partner.partner_code, partner.brand_name, partner.main_product_categories])
    ).lower()
    has_lifting_reference = REFERENCE_PARTNER_CODES[0].lower() in joined and any(
        marker in joined for marker in ("lifting", "desk", "column", "heavy")
    )
    has_education_reference = REFERENCE_PARTNER_CODES[1].lower() in joined and any(
        marker in joined for marker in ("education", "school", "classroom", "project")
    )
    return has_lifting_reference or has_education_reference


def _stage(done: dict[str, bool], is_active: bool) -> str:
    if not is_active:
        return "paused"
    if all(done.values()):
        return "active_partner"
    if done["demo_narrative_prepared"] and done["portal_visibility_reviewed"]:
        return "demo_ready"
    if done["portal_visibility_reviewed"]:
        return "portal_ready"
    if done["quote_flow_ready"]:
        return "quote_ready"
    if done["product_categories_mapped"]:
        return "product_mapping"
    return "discovery"


def _next_action(missing: list[str], stage: str) -> str:
    if stage == "paused":
        return "Decide whether to reactivate this partner before assigning demo, quote, or order work."
    if not missing:
        return "Use as an active partner reference for demo, quotes, Portal bridge readiness, and real orders."
    first = missing[0]
    actions = {
        "brand_profile_completed": "Complete brand profile, contact, location, and export-market basics.",
        "product_categories_mapped": "Map product categories and product focus to catalog or product records.",
        "pricing_basis_available": "Add catalog pricing basis or partner price range before quote use.",
        "quote_flow_ready": "Confirm catalog items and pricing basis before quote preparation.",
        "order_flow_ready": "Create or link confirmed order/partner split readiness before real order use.",
        "production_shipment_flow_mapped": "Map production milestones and manual shipment planning path.",
        "portal_visibility_reviewed": "Review customer-visible product/order/production/shipment/feedback fields.",
        "market_response_focus_defined": "Define market response focus from demand, feedback, risk, or watchlist signal.",
        "demo_narrative_prepared": "Prepare partner-specific demo narrative and talk track.",
    }
    return actions.get(first, "Review onboarding checklist and complete the next missing item.")


def _links(partner_id: UUID | None) -> PartnerOnboardingLinks:
    partner_detail = f"/manufacturing-partners/{partner_id}" if partner_id else "/manufacturing-partners"
    return PartnerOnboardingLinks(
        partner_detail=partner_detail,
        product_catalog="/quote-catalog",
        demo_walkthrough="/demo-walkthrough",
        market_response="/market-response",
        orders="/orders",
    )


def build_partner_onboarding(db: Session) -> PartnerOnboardingResponse:
    partners = (
        db.query(ManufacturingPartner)
        .order_by(ManufacturingPartner.is_active.desc(), ManufacturingPartner.partner_name.asc())
        .all()
    )


    partner_ids = [partner.id for partner in partners]

    catalog_counts = dict(
        db.query(ProductCatalog.partner_id, func.count(ProductCatalog.id))
        .filter(ProductCatalog.partner_id.in_(partner_ids))
        .group_by(ProductCatalog.partner_id)
        .all()
    ) if partner_ids else {}
    product_link_counts = dict(
        db.query(ProductPartnerLink.manufacturing_partner_id, func.count(ProductPartnerLink.id))
        .filter(ProductPartnerLink.manufacturing_partner_id.in_(partner_ids))
        .group_by(ProductPartnerLink.manufacturing_partner_id)
        .all()
    ) if partner_ids else {}
    price_tier_counts = dict(
        db.query(ProductCatalog.partner_id, func.count(ProductPriceTier.id))
        .join(ProductPriceTier, ProductPriceTier.product_id == ProductCatalog.id)
        .filter(ProductCatalog.partner_id.in_(partner_ids))
        .group_by(ProductCatalog.partner_id)
        .all()
    ) if partner_ids else {}
    split_counts = dict(
        db.query(OrderPartnerSplit.partner_id, func.count(OrderPartnerSplit.id))
        .filter(OrderPartnerSplit.partner_id.in_(partner_ids))
        .group_by(OrderPartnerSplit.partner_id)
        .all()
    ) if partner_ids else {}
    milestone_counts = dict(
        db.query(OrderProductionMilestone.partner_id, func.count(OrderProductionMilestone.id))
        .filter(OrderProductionMilestone.partner_id.in_(partner_ids))
        .group_by(OrderProductionMilestone.partner_id)
        .all()
    ) if partner_ids else {}
    shipment_counts = dict(
        db.query(OrderPartnerSplit.partner_id, func.count(ShipmentPlan.id))
        .join(ShipmentPlan, ShipmentPlan.partner_split_id == OrderPartnerSplit.id)
        .filter(OrderPartnerSplit.partner_id.in_(partner_ids))
        .group_by(OrderPartnerSplit.partner_id)
        .all()
    ) if partner_ids else {}
    order_counts = dict(
        db.query(OrderPartnerSplit.partner_id, func.count(func.distinct(CustomerOrder.id)))
        .join(CustomerOrder, CustomerOrder.id == OrderPartnerSplit.order_id)
        .filter(OrderPartnerSplit.partner_id.in_(partner_ids))
        .group_by(OrderPartnerSplit.partner_id)
        .all()
    ) if partner_ids else {}

    records: list[PartnerOnboardingRecord] = []
    for partner in partners:
        focus = _split_terms(
            partner.main_product_categories,
            partner.preferred_product_categories,
            partner.manufacturing_capabilities,
        )
        linked_product_count = int(product_link_counts.get(partner.id, 0) or 0)
        catalog_count = int(catalog_counts.get(partner.id, 0) or 0)
        price_tier_count = int(price_tier_counts.get(partner.id, 0) or 0)
        split_count = int(split_counts.get(partner.id, 0) or 0)
        milestone_count = int(milestone_counts.get(partner.id, 0) or 0)
        shipment_count = int(shipment_counts.get(partner.id, 0) or 0)
        order_count = int(order_counts.get(partner.id, 0) or 0)

        profile_done = bool(
            partner.partner_name
            and partner.partner_type
            and (partner.brand_name or partner.legal_name or partner.partner_code)
            and (partner.country or partner.city or partner.website)
        )
        product_done = bool(focus or linked_product_count or catalog_count)
        pricing_done = bool(price_tier_count or partner.price_level or partner.moq_policy)
        quote_ready = bool(product_done and pricing_done and catalog_count)
        order_ready = bool(split_count or order_count)
        production_shipment_ready = bool(milestone_count and shipment_count)
        portal_ready = bool(product_done and order_ready and production_shipment_ready)
        market_ready = bool(
            partner.preferred_product_categories
            or partner.ai_partner_summary
            or _demo_ready_by_known_narrative(partner)
        )
        demo_ready = bool(profile_done and product_done and market_ready and _demo_ready_by_known_narrative(partner))

        done = {
            "brand_profile_completed": profile_done,
            "product_categories_mapped": product_done,
            "pricing_basis_available": pricing_done,
            "quote_flow_ready": quote_ready,
            "order_flow_ready": order_ready,
            "production_shipment_flow_mapped": production_shipment_ready,
            "portal_visibility_reviewed": portal_ready,
            "market_response_focus_defined": market_ready,
            "demo_narrative_prepared": demo_ready,
        }
        checklist = [
            PartnerOnboardingChecklistItem(
                key=key,
                label=CHECKLIST_LABELS[key],
                done=value,
                detail=_detail_for_check(
                    key,
                    partner=partner,
                    linked_product_count=linked_product_count,
                    catalog_count=catalog_count,
                    price_tier_count=price_tier_count,
                    split_count=split_count,
                    milestone_count=milestone_count,
                    shipment_count=shipment_count,
                ),
            )
            for key, value in done.items()
        ]
        missing = [key for key in CHECKLIST_KEYS if not done[key]]
        stage = _stage(done, partner.is_active)
        score = round(sum(1 for item in done.values() if item) / len(done) * 100)
        records.append(
            PartnerOnboardingRecord(
                partner_id=partner.id,
                partner_name=partner.partner_name,
                partner_code=partner.partner_code,
                partner_type=partner.partner_type,
                product_focus=focus or ["Product focus to confirm"],
                target_markets=_target_markets(partner),
                onboarding_stage=stage,
                readiness_score=score,
                readiness_summary=f"{sum(1 for value in done.values() if value)}/{len(done)} onboarding checks complete",
                missing_items=missing,
                next_action=_next_action(missing, stage),
                checklist=checklist,
                links=_links(partner.id),
                is_reference_partner=_is_reference_partner(partner),
                capability_intelligence=build_partner_capability_intelligence(db, partner),
                safety=_safety(),
            )
        )

    stage_counts = Counter(record.onboarding_stage for record in records)
    summary = PartnerOnboardingSummary(
        total_partners=len(records),
        reference_partner_count=sum(1 for record in records if record.is_reference_partner),
        demo_ready_count=sum(1 for record in records if record.onboarding_stage in {"demo_ready", "active_partner"}),
        quote_ready_count=sum(1 for record in records if record.checklist[3].done),
        portal_ready_count=sum(1 for record in records if record.checklist[6].done),
        active_partner_count=stage_counts["active_partner"],
        paused_count=stage_counts["paused"],
        safety=_safety(),
    )
    return PartnerOnboardingResponse(
        status="READY_FOR_STAGING_HANDOFF",
        stage_order=STAGE_ORDER,
        checklist_keys=CHECKLIST_KEYS,
        summary=summary,
        items=records,
        future_partner_placeholder=_future_partner_placeholder(),
        safety=_safety(),
    )


def create_partner_market_response_reviews(db: Session, partner_id: UUID, actor: User | None = None) -> dict[str, object]:
    partner = db.get(ManufacturingPartner, partner_id)
    if partner is None:
        return {"found": False, "created": [], "existing": [], "safety": _safety()}

    response = build_partner_onboarding(db)
    record = next((item for item in response.items if item.partner_id == partner_id), None)
    if record is None:
        return {"found": False, "created": [], "existing": [], "safety": _safety()}

    actor_id = getattr(actor, "id", None) if actor is not None else None
    created: list[str] = []
    existing: list[str] = []
    missing_review_keys = [key for key in record.missing_items if key in ONBOARDING_REVIEW_DIMENSIONS]
    if not missing_review_keys:
        missing_review_keys = ["market_response_focus_defined"]

    focus_category = _focus_category_for_partner(record)
    for key in missing_review_keys:
        review_dimension, priority = ONBOARDING_REVIEW_DIMENSIONS[key]
        current = (
            db.query(MarketResponseReview)
            .filter(
                MarketResponseReview.partner_focus == record.partner_name,
                MarketResponseReview.review_dimension == review_dimension,
                MarketResponseReview.source_type == "partner onboarding",
            )
            .first()
        )
        if current is not None:
            existing.append(str(current.id))
            continue
        review = MarketResponseReview(
            partner_focus=record.partner_name,
            focus_category=focus_category,
            product_focus=record.product_focus,
            review_dimension=review_dimension,
            visibility_class="needs validation",
            priority=priority,
            status="needs review",
            source_type="partner onboarding",
            source_summary=f"Partner onboarding gap: {CHECKLIST_LABELS.get(key, key)}.",
            evidence_summary=record.readiness_summary,
            customer_safe_summary=None,
            internal_notes="Generated from internal onboarding readiness. Not a business sign-off, security approval, or staging evidence.",
            next_action=record.next_action,
            owner="partner onboarding owner",
            created_by_id=actor_id,
            updated_by_id=actor_id,
        )
        db.add(review)
        db.flush()
        created.append(str(review.id))
    db.commit()

    return {
        "found": True,
        "partner_id": str(partner_id),
        "partner_name": record.partner_name,
        "created": created,
        "existing": existing,
        "market_response_link": f"/market-response?partner_focus={quote(record.partner_name)}",
        "safety": {
            **_safety(),
            "market_response_review_created": bool(created),
            "customer_notified": False,
            "supplier_notified": False,
            "quote_status_changed": False,
            "order_status_changed": False,
        },
    }


def _detail_for_check(
    key: str,
    *,
    partner: ManufacturingPartner,
    linked_product_count: int,
    catalog_count: int,
    price_tier_count: int,
    split_count: int,
    milestone_count: int,
    shipment_count: int,
) -> str:
    details = {
        "brand_profile_completed": "Uses partner name, type, brand/legal/code, and location or website.",
        "product_categories_mapped": f"{len(_split_terms(partner.main_product_categories, partner.preferred_product_categories))} profile focus term(s), {linked_product_count} product link(s), {catalog_count} catalog item(s).",
        "pricing_basis_available": f"{price_tier_count} price tier(s), price level={partner.price_level or 'not set'}, MOQ policy={'set' if partner.moq_policy else 'missing'}.",
        "quote_flow_ready": f"{catalog_count} catalog item(s) with pricing basis required before quote use.",
        "order_flow_ready": f"{split_count} partner split(s) across existing customer orders.",
        "production_shipment_flow_mapped": f"{milestone_count} production milestone(s), {shipment_count} shipment plan(s).",
        "portal_visibility_reviewed": "Requires product mapping plus order, production, and shipment visibility.",
        "market_response_focus_defined": "Uses preferred categories, partner summary, or demo narrative focus.",
        "demo_narrative_prepared": "Reference demo narrative is prepared for existing sample partners; future partners need their own talk track.",
    }
    return details[key]


def _focus_category_for_partner(record: PartnerOnboardingRecord) -> str:
    blob = " ".join([record.partner_name, *(record.product_focus or [])]).lower()
    if any(term in blob for term in ("lifting column", "column")):
        return "lifting_columns"
    if any(term in blob for term in ("desk leg", "leg")):
        return "desk_legs"
    if any(term in blob for term in ("lifting", "desk frame", "height adjustable", "heavy-duty", "heavy duty")):
        return "adjustable_desk_frames"
    if any(term in blob for term in ("education", "school", "classroom")):
        return "education_furniture"
    if "project" in blob:
        return "project_furniture"
    return "future_partner_onboarding"


def _safety() -> dict[str, bool]:
    return {
        "read_only": True,
        "staging_validated": False,
        "proof_record_created": False,
        "d9_entered": False,
        "customer_notified": False,
        "supplier_notified": False,
        "carrier_api_called": False,
        "token_value_exposed": False,
    }


def _future_partner_placeholder() -> PartnerOnboardingRecord:
    done = {
        "brand_profile_completed": False,
        "product_categories_mapped": False,
        "pricing_basis_available": False,
        "quote_flow_ready": False,
        "order_flow_ready": False,
        "production_shipment_flow_mapped": False,
        "portal_visibility_reviewed": False,
        "market_response_focus_defined": False,
        "demo_narrative_prepared": False,
    }
    checklist = [
        PartnerOnboardingChecklistItem(
            key=key,
            label=CHECKLIST_LABELS[key],
            done=False,
            detail="Required before this future partner can advance.",
        )
        for key in CHECKLIST_KEYS
    ]
    return PartnerOnboardingRecord(
        partner_id=UUID("00000000-0000-0000-0000-000000000000"),
        partner_name="Chongqing Huiju / future partner placeholder",
        partner_code=None,
        partner_type="Future premium export brand",
        product_focus=["Product focus to confirm"],
        target_markets=["Target market to confirm"],
        onboarding_stage="discovery",
        readiness_score=0,
        readiness_summary="0/9 onboarding checks complete",
        missing_items=list(done.keys()),
        next_action="Create a real manufacturing partner record with verified brand profile and product focus before demo use.",
        checklist=checklist,
        links=_links(None),
        is_reference_partner=False,
        safety=_safety(),
    )
