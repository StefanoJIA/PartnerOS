"""Quote line pricing preview service (D6.2 — no quote record creation)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ApiError, NOT_FOUND, VALIDATION_ERROR
from app.models import FxRate, MarginStrategyTier, ProductCatalog, ProductCostModel, ProductPriceTier
from app.services.quotes.pricing_calculations import (
    VALID_INCOTERMS,
    VALID_STRATEGIES,
    apply_discount,
    compute_cost_breakdown,
    compute_profit,
    money,
    qty_in_tier,
    tier_unit_price,
)

PRICING_SAFETY: dict[str, bool] = {
    "quote_created": False,
    "automatic_sending_enabled": False,
    "inventory_promised": False,
    "certification_promised": False,
    "lead_time_promised": False,
}


def _effective_on(ref: date, effective_from: date | None, effective_to: date | None) -> bool:
    if effective_from and ref < effective_from:
        return False
    if effective_to and ref > effective_to:
        return False
    return True


def get_latest_fx(db: Session, *, base: str, quote: str, rate_date: date | None) -> FxRate | None:
    q = db.query(FxRate).filter(FxRate.base_currency == base, FxRate.quote_currency == quote)
    if rate_date:
        row = q.filter(FxRate.rate_date <= rate_date).order_by(FxRate.rate_date.desc()).first()
        if row:
            return row
    return q.order_by(FxRate.rate_date.desc()).first()


def _select_price_tier(
    db: Session,
    product_id: UUID,
    quantity: int,
    incoterm: str,
    pricing_strategy: str | None,
    ref: date,
) -> ProductPriceTier | None:
    tiers = (
        db.query(ProductPriceTier)
        .filter(ProductPriceTier.product_id == product_id, ProductPriceTier.incoterm == incoterm.upper())
        .order_by(ProductPriceTier.min_qty.asc())
        .all()
    )
    matches: list[ProductPriceTier] = []
    for t in tiers:
        if not _effective_on(ref, t.effective_from, t.effective_to):
            continue
        if not qty_in_tier(quantity, t.min_qty, t.max_qty):
            continue
        if t.pricing_strategy and pricing_strategy and t.pricing_strategy != pricing_strategy:
            continue
        matches.append(t)
    if not matches:
        return None
    return matches[0]


def _select_cost_model(db: Session, product_id: UUID, ref: date) -> ProductCostModel | None:
    rows = (
        db.query(ProductCostModel)
        .filter(ProductCostModel.product_id == product_id)
        .order_by(ProductCostModel.effective_from.desc().nullslast(), ProductCostModel.created_at.desc())
        .all()
    )
    for row in rows:
        if _effective_on(ref, row.effective_from, row.effective_to):
            return row
    return rows[0] if rows else None


def _select_margin_multiplier(
    db: Session, strategy: str, quantity: int
) -> tuple[Decimal, list[str]]:
    warnings: list[str] = []
    rows = (
        db.query(MarginStrategyTier)
        .filter(MarginStrategyTier.strategy_code == strategy)
        .order_by(MarginStrategyTier.min_qty.asc())
        .all()
    )
    for row in rows:
        if qty_in_tier(quantity, row.min_qty, row.max_qty):
            return row.multiplier, warnings
    if rows:
        warnings.append("margin_strategy_tier_fallback")
        return rows[0].multiplier, warnings
    return Decimal("1"), warnings


def calculate_line_price(
    db: Session,
    *,
    product_id: UUID,
    quantity: int,
    incoterm: str,
    pricing_strategy: str = "volume",
    discount: dict | None = None,
    fx_rate_date: date | None = None,
    manual_unit_price: Decimal | None = None,
) -> dict[str, Any]:
    """Pricing preview — does not create quotes or persist prices."""
    warnings: list[str] = []
    if quantity <= 0:
        raise ApiError(VALIDATION_ERROR, "quantity must be > 0", status_code=400)
    inc = incoterm.upper()
    if inc not in VALID_INCOTERMS:
        raise ApiError(VALIDATION_ERROR, f"invalid incoterm: {incoterm}", status_code=400)
    if pricing_strategy not in VALID_STRATEGIES:
        raise ApiError(VALIDATION_ERROR, f"invalid pricing_strategy: {pricing_strategy}", status_code=400)

    product = db.query(ProductCatalog).filter(ProductCatalog.id == product_id).first()
    if not product:
        raise ApiError(NOT_FOUND, "product not found", status_code=404)

    ref = fx_rate_date or date.today()
    fx = get_latest_fx(db, base="USD", quote="CNY", rate_date=ref)
    fx_rate_usd_cny = fx.rate if fx else None

    source = "price_tier"
    base_unit = Decimal("0")
    unit_cost_for_margin: Decimal | None = None
    cost_breakdown: dict[str, str] = {
        "unit_material_cost_rmb": "0.00",
        "unit_material_cost_usd": "0.00",
        "unit_weight": "0.00",
        "freight_cost_usd": "0.00",
        "fob_cost_usd": "0.00",
        "ddp_cost_usd": "0.00",
    }

    if manual_unit_price is not None:
        source = "manual_unit_price"
        base_unit = manual_unit_price
        warnings.append("manual price requires review")
    else:
        tier = _select_price_tier(db, product_id, quantity, inc, pricing_strategy, ref)
        if tier:
            base_unit = tier_unit_price(
                base_unit_price=tier.base_unit_price,
                adjustment_value=tier.adjustment_value,
                final_unit_price=tier.final_unit_price,
            )
        else:
            cost = _select_cost_model(db, product_id, ref)
            if not cost:
                raise ApiError(
                    VALIDATION_ERROR,
                    "no price tier or cost model available for product",
                    status_code=400,
                )
            try:
                cost_breakdown, unit_cost_for_margin = compute_cost_breakdown(
                    unit_material_cost=cost.unit_material_cost,
                    cost_currency=cost.cost_currency or "CNY",
                    unit_weight=cost.unit_weight,
                    ocean_freight_unit_price=cost.ocean_freight_unit_price,
                    domestic_transport_cost=cost.domestic_transport_cost,
                    domestic_profit_rate=cost.domestic_profit_rate,
                    fx_rate_usd_cny=fx_rate_usd_cny,
                    stored_fob_cost_usd=cost.fob_cost_usd,
                    stored_ddp_cost_usd=cost.ddp_cost_usd,
                )
            except ValueError as e:
                if str(e) == "FX_RATE_MISSING":
                    raise ApiError(
                        VALIDATION_ERROR,
                        "FX rate required for RMB cost conversion",
                        status_code=400,
                        details={"fx_pair": "USD/CNY"},
                    ) from e
                raise
            source = "cost_model"
            warnings.append("estimated_from_cost_model")
            if inc == "DDP" and cost_breakdown.get("ddp_cost_usd"):
                base_unit = Decimal(cost_breakdown["ddp_cost_usd"])
            elif cost_breakdown.get("fob_cost_usd"):
                base_unit = Decimal(cost_breakdown["fob_cost_usd"])
            unit_cost_for_margin = base_unit

            mult, w = _select_margin_multiplier(db, pricing_strategy, quantity)
            warnings.extend(w)
            base_unit = (base_unit * mult).quantize(Decimal("0.0001"))

    if unit_cost_for_margin is None and source == "price_tier":
        cost = _select_cost_model(db, product_id, ref)
        if cost and fx_rate_usd_cny:
            try:
                cost_breakdown, unit_cost_for_margin = compute_cost_breakdown(
                    unit_material_cost=cost.unit_material_cost,
                    cost_currency=cost.cost_currency or "CNY",
                    unit_weight=cost.unit_weight,
                    ocean_freight_unit_price=cost.ocean_freight_unit_price,
                    domestic_transport_cost=cost.domestic_transport_cost,
                    domestic_profit_rate=cost.domestic_profit_rate,
                    fx_rate_usd_cny=fx_rate_usd_cny,
                    stored_fob_cost_usd=cost.fob_cost_usd,
                    stored_ddp_cost_usd=cost.ddp_cost_usd,
                )
            except ValueError:
                unit_cost_for_margin = None

    final_unit, discount_amount = apply_discount(base_unit, quantity, discount)
    line_subtotal = (final_unit * quantity).quantize(Decimal("0.01"))
    profit_total, margin_pct = compute_profit(final_unit, unit_cost_for_margin, quantity)

    fx_payload = None
    if fx:
        fx_payload = {
            "base_currency": fx.base_currency,
            "quote_currency": fx.quote_currency,
            "rate": str(fx.rate),
            "rate_date": str(fx.rate_date),
            "source": fx.source or "manual",
        }

    return {
        "product_id": str(product_id),
        "quantity": quantity,
        "incoterm": inc,
        "pricing_strategy": pricing_strategy,
        "currency": "USD",
        "fx_rate_used": fx_payload,
        "cost_breakdown": cost_breakdown,
        "price_breakdown": {
            "base_unit_price": money(base_unit),
            "adjustment_value": "0.00",
            "final_unit_price": money(base_unit),
            "discount_amount": money(discount_amount),
            "final_unit_price_after_discount": money(final_unit),
            "line_subtotal": money(line_subtotal),
        },
        "profit_breakdown": {
            "estimated_unit_profit": money(
                (final_unit - (unit_cost_for_margin or Decimal("0"))).quantize(Decimal("0.0001"))
            ),
            "estimated_total_profit": profit_total,
            "estimated_margin": margin_pct,
        },
        "warnings": warnings,
        "source": source,
        "safety": dict(PRICING_SAFETY),
    }
