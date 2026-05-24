"""V1 FX rate routes (D6.2)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import ApiError, NOT_FOUND
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import FxRate, User
from app.schemas.quote_catalog import FxRateCreate, FxRateOut
from app.services.quotes.pricing_service import get_latest_fx

router = APIRouter(prefix="/fx-rates", tags=["v1-fx-rates"])


@router.get("/latest")
def get_latest_fx_rate(
    request: Request,
    base: str = Query("USD"),
    quote: str = Query("CNY"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from datetime import date

    row = get_latest_fx(db, base=base.upper(), quote=quote.upper(), rate_date=date.today())
    if not row:
        raise ApiError(NOT_FOUND, "fx rate not found", status_code=404)
    rid = get_request_id(request)
    return success_envelope(FxRateOut.model_validate(row).model_dump(mode="json"), request_id=rid)


@router.post("")
def create_fx_rate(
    body: FxRateCreate,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    existing = (
        db.query(FxRate)
        .filter(
            FxRate.base_currency == body.base_currency.upper(),
            FxRate.quote_currency == body.quote_currency.upper(),
            FxRate.rate_date == body.rate_date,
        )
        .first()
    )
    if existing:
        existing.rate = body.rate
        existing.source = body.source
        existing.is_manual_override = body.is_manual_override
        db.commit()
        db.refresh(existing)
        row = existing
    else:
        row = FxRate(
            base_currency=body.base_currency.upper(),
            quote_currency=body.quote_currency.upper(),
            rate=body.rate,
            rate_date=body.rate_date,
            source=body.source,
            is_manual_override=body.is_manual_override,
            created_at=datetime.now(timezone.utc),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    rid = get_request_id(request)
    return success_envelope(FxRateOut.model_validate(row).model_dump(mode="json"), request_id=rid, status_code=201)
