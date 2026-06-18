"""Internal quote pricing assumptions routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.schemas.quote_catalog import PricingAssumptionSnapshotOut, PricingAssumptionUpdate
from app.services.quotes.pricing_assumptions import (
    OCEAN_FREIGHT_UNIT_PRICE_KEY,
    get_current_pricing_assumptions,
    upsert_ocean_freight_unit_price,
)

router = APIRouter(prefix="/quotes/pricing/assumptions", tags=["v1-pricing-assumptions"])


def _snapshot_payload(db: Session) -> dict:
    snapshot = get_current_pricing_assumptions(db)
    return PricingAssumptionSnapshotOut(
        ocean_freight={
            "assumption_key": OCEAN_FREIGHT_UNIT_PRICE_KEY,
            "numeric_value": snapshot.ocean_freight_unit_price,
            "unit": snapshot.ocean_freight_unit,
            "source": snapshot.ocean_freight_source,
            "effective_from": snapshot.ocean_freight_effective_from,
            "fallback_used": snapshot.fallback_used,
            "internal_only": True,
        },
        safety={
            "internal_only": True,
            "customer_visible": False,
            "automatic_sending_enabled": False,
            "quote_status_auto_change": False,
            "raw_token_recorded": False,
        },
    ).model_dump(mode="json")


@router.get("")
def get_pricing_assumptions(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rid = get_request_id(request)
    return success_envelope(_snapshot_payload(db), request_id=rid)


@router.put("/ocean-freight")
def update_ocean_freight_assumption(
    body: PricingAssumptionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    upsert_ocean_freight_unit_price(
        db,
        value=body.ocean_freight_unit_price,
        effective_from=body.effective_from,
        source=body.source,
        notes=body.notes,
    )
    rid = get_request_id(request)
    return success_envelope(_snapshot_payload(db), request_id=rid)
