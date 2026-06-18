"""Internal quote pricing assumptions.

These assumptions are operator-maintained inputs for pricing calculations.
They are internal-only and are not customer-facing quote content.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.models import PricingAssumption

OCEAN_FREIGHT_UNIT_PRICE_KEY = "ocean_freight_unit_price"
DEFAULT_OCEAN_FREIGHT_UNIT_PRICE = Decimal("22")


@dataclass(frozen=True)
class PricingAssumptionSnapshot:
    ocean_freight_unit_price: Decimal
    ocean_freight_unit: str
    ocean_freight_source: str
    ocean_freight_effective_from: date | None
    fallback_used: bool


def _effective_on(ref: date, effective_from: date | None, effective_to: date | None) -> bool:
    if effective_from and ref < effective_from:
        return False
    if effective_to and ref > effective_to:
        return False
    return True


def get_latest_pricing_assumption(
    db: Session,
    assumption_key: str,
    *,
    ref: date | None = None,
) -> PricingAssumption | None:
    effective_ref = ref or date.today()
    rows = (
        db.query(PricingAssumption)
        .filter(PricingAssumption.assumption_key == assumption_key, PricingAssumption.is_active.is_(True))
        .order_by(PricingAssumption.effective_from.desc(), PricingAssumption.created_at.desc())
        .all()
    )
    for row in rows:
        if _effective_on(effective_ref, row.effective_from, row.effective_to):
            return row
    return rows[0] if rows else None


def get_current_pricing_assumptions(db: Session, *, ref: date | None = None) -> PricingAssumptionSnapshot:
    ocean = get_latest_pricing_assumption(db, OCEAN_FREIGHT_UNIT_PRICE_KEY, ref=ref)
    if not ocean:
        return PricingAssumptionSnapshot(
            ocean_freight_unit_price=DEFAULT_OCEAN_FREIGHT_UNIT_PRICE,
            ocean_freight_unit="RMB/kg",
            ocean_freight_source="default_fallback",
            ocean_freight_effective_from=None,
            fallback_used=True,
        )
    try:
        value = Decimal(str(ocean.numeric_value))
    except (InvalidOperation, TypeError, ValueError):
        return PricingAssumptionSnapshot(
            ocean_freight_unit_price=DEFAULT_OCEAN_FREIGHT_UNIT_PRICE,
            ocean_freight_unit="RMB/kg",
            ocean_freight_source="default_fallback",
            ocean_freight_effective_from=None,
            fallback_used=True,
        )
    return PricingAssumptionSnapshot(
        ocean_freight_unit_price=value,
        ocean_freight_unit=ocean.unit or "RMB/kg",
        ocean_freight_source=ocean.source or "manual",
        ocean_freight_effective_from=ocean.effective_from,
        fallback_used=False,
    )


def upsert_ocean_freight_unit_price(
    db: Session,
    *,
    value: Decimal,
    effective_from: date | None = None,
    source: str = "manual_provider_quote",
    notes: str | None = None,
) -> PricingAssumption:
    row = (
        db.query(PricingAssumption)
        .filter(
            PricingAssumption.assumption_key == OCEAN_FREIGHT_UNIT_PRICE_KEY,
            PricingAssumption.effective_from == (effective_from or date.today()),
        )
        .first()
    )
    if row:
        row.numeric_value = value
        row.unit = "RMB/kg"
        row.source = source
        row.is_active = True
        row.notes = notes
    else:
        row = PricingAssumption(
            assumption_key=OCEAN_FREIGHT_UNIT_PRICE_KEY,
            numeric_value=value,
            unit="RMB/kg",
            source=source,
            effective_from=effective_from or date.today(),
            is_active=True,
            notes=notes,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row
