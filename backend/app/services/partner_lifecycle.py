"""Partner lifecycle rules for multibrand export OS."""

from __future__ import annotations

from sqlalchemy.orm import Query, Session

from app.models import ManufacturingPartner
from app.models.enums import PartnerLifecycle

SELECTABLE_FOR_NEW_QUOTE = frozenset({PartnerLifecycle.active.value})
DEFAULT_RECOMMENDABLE = frozenset({PartnerLifecycle.active.value})
DEMO_MARKETING_VISIBLE = frozenset(
    {PartnerLifecycle.active.value, PartnerLifecycle.onboarding.value, PartnerLifecycle.candidate.value}
)


def normalize_lifecycle(partner: ManufacturingPartner | None) -> str:
    if not partner:
        return PartnerLifecycle.candidate.value
    return partner.lifecycle_status or PartnerLifecycle.active.value


def is_partner_selectable_for_new_quote(partner: ManufacturingPartner | None) -> bool:
    return normalize_lifecycle(partner) in SELECTABLE_FOR_NEW_QUOTE


def is_partner_default_recommendable(partner: ManufacturingPartner | None) -> bool:
    if not partner:
        return False
    return normalize_lifecycle(partner) in DEFAULT_RECOMMENDABLE


def is_partner_demo_marketing_visible(partner: ManufacturingPartner | None) -> bool:
    if not partner:
        return False
    return normalize_lifecycle(partner) in DEMO_MARKETING_VISIBLE


def filter_selectable_partners(query: Query) -> Query:
    return query.filter(ManufacturingPartner.lifecycle_status == PartnerLifecycle.active.value)


def filter_recommendable_partners(query: Query) -> Query:
    return query.filter(ManufacturingPartner.lifecycle_status == PartnerLifecycle.active.value)


def get_default_lifting_partner(db: Session) -> ManufacturingPartner | None:
    """Prefer active generic lifting fixture; never auto-return legacy partners."""
    generic = (
        db.query(ManufacturingPartner)
        .filter(
            ManufacturingPartner.partner_code == "LIFT-DEMO",
            ManufacturingPartner.lifecycle_status == PartnerLifecycle.active.value,
        )
        .first()
    )
    if generic:
        return generic
    return (
        filter_recommendable_partners(db.query(ManufacturingPartner))
        .filter(ManufacturingPartner.partner_type.ilike("%lifting%"))
        .order_by(ManufacturingPartner.created_at.desc())
        .first()
    )


def assert_partner_selectable_for_quote(partner: ManufacturingPartner) -> None:
    from fastapi import HTTPException

    if not is_partner_selectable_for_new_quote(partner):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Partner {partner.partner_code or partner.partner_name} is "
                f"{normalize_lifecycle(partner)} — manual legacy selection only for historical context."
            ),
        )
