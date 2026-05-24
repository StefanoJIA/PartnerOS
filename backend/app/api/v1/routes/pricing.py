"""V1 pricing preview routes (D6.2 — no quote creation)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.schemas.quote_catalog import PricingPreviewRequest
from app.services.quotes.pricing_calculations import assert_no_forbidden_phrases
from app.services.quotes.pricing_service import calculate_line_price

router = APIRouter(prefix="/quotes/pricing", tags=["v1-pricing"])


@router.post("/preview")
def pricing_preview(
    body: PricingPreviewRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = calculate_line_price(
        db,
        product_id=body.product_id,
        quantity=body.quantity,
        incoterm=body.incoterm,
        pricing_strategy=body.pricing_strategy,
        discount=body.discount.model_dump() if body.discount else None,
        fx_rate_date=body.fx_rate_date,
        manual_unit_price=body.manual_unit_price,
    )
    assert_no_forbidden_phrases(str(result))
    rid = get_request_id(request)
    return success_envelope(result, request_id=rid)
