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


def _quantity_range_label(min_qty: int, max_qty: int | None) -> str:
    if max_qty is None or max_qty >= 99999999:
        return f">={min_qty}"
    if min_qty == max_qty:
        return str(min_qty)
    return f"{min_qty}-{max_qty}"


def _tier_customer_unit_price(tier: ProductPriceTier) -> Decimal | None:
    if tier.final_unit_price is None and tier.base_unit_price is None and tier.adjustment_value is None:
        return None
    return tier_unit_price(
        base_unit_price=tier.base_unit_price,
        adjustment_value=tier.adjustment_value,
        final_unit_price=tier.final_unit_price,
    )


def build_product_interval_quote_table(
    db: Session,
    *,
    product_id: UUID,
    pricing_strategy: str | None = None,
    ref: date | None = None,
) -> list[dict[str, Any]]:
    """Build the customer-safe product quantity range price table.

    The source quote workbook prices each product as a range table, not as a
    single quantity point. Ranges must be derived from ProductPriceTier rows so
    each product can keep its own interval structure and FOB/DDP availability.
    """
    effective_ref = ref or date.today()
    tiers = (
        db.query(ProductPriceTier)
        .filter(ProductPriceTier.product_id == product_id)
        .order_by(ProductPriceTier.min_qty.asc(), ProductPriceTier.max_qty.asc().nullslast(), ProductPriceTier.incoterm.asc())
        .all()
    )
    active = [row for row in tiers if _effective_on(effective_ref, row.effective_from, row.effective_to)]
    if pricing_strategy:
        matching = [row for row in active if not row.pricing_strategy or row.pricing_strategy == pricing_strategy]
        if matching:
            active = matching

    grouped: dict[tuple[int, int | None], dict[str, Any]] = {}
    for tier in active:
        price = _tier_customer_unit_price(tier)
        if price is None:
            continue
        key = (tier.min_qty, tier.max_qty)
        row = grouped.setdefault(
            key,
            {
                "min_qty": tier.min_qty,
                "max_qty": tier.max_qty,
                "quantity_label": _quantity_range_label(tier.min_qty, tier.max_qty),
                "currency": tier.currency or "USD",
                "fob_unit_price": None,
                "ddp_unit_price": None,
                "incoterms_available": [],
                "pricing_strategies": [],
                "customer_visible": True,
            },
        )
        incoterm = (tier.incoterm or "").upper()
        if incoterm == "FOB":
            row["fob_unit_price"] = money(price)
        elif incoterm == "DDP":
            row["ddp_unit_price"] = money(price)
        else:
            row[f"{incoterm.lower()}_unit_price"] = money(price)
        if incoterm and incoterm not in row["incoterms_available"]:
            row["incoterms_available"].append(incoterm)
        if tier.pricing_strategy and tier.pricing_strategy not in row["pricing_strategies"]:
            row["pricing_strategies"].append(tier.pricing_strategy)

    return [grouped[key] for key in sorted(grouped, key=lambda item: (item[0], item[1] or 99999999))]


def _selected_interval_row(
    interval_quote_table: list[dict[str, Any]],
    *,
    quantity: int,
) -> dict[str, Any] | None:
    for row in interval_quote_table:
        if qty_in_tier(quantity, int(row["min_qty"]), row.get("max_qty")):
            return row
    return None


def _quote_model_snapshot(
    *,
    source: str,
    product: ProductCatalog,
    quantity: int,
    incoterm: str,
    pricing_strategy: str,
    discount: dict | None,
    fx_payload: dict[str, str] | None,
    cost_breakdown: dict[str, str],
    price_breakdown: dict[str, str],
    profit_breakdown: dict[str, str],
    tier_snapshot: dict[str, Any] | None,
    margin_snapshot: dict[str, str] | None,
    interval_quote_table: list[dict[str, Any]],
    selected_interval: dict[str, Any] | None,
    warnings: list[str],
) -> dict[str, Any]:
    """Internal fixed quote-model flow based on the Excel workbook pages."""
    cost_basis = cost_breakdown.get("ddp_cost_usd") if incoterm == "DDP" else cost_breakdown.get("fob_cost_usd")
    logistics_basis = (
        "DDP uses FOB cost plus freight/transport converted by FX."
        if incoterm == "DDP"
        else "FOB uses material/domestic-profit cost converted by FX; freight remains visible for comparison."
    )
    internal_snapshot = {
        "cost_breakdown": dict(cost_breakdown),
        "profit_breakdown": dict(profit_breakdown),
        "pricing_source": source,
        "margin_strategy": pricing_strategy,
        "tier": tier_snapshot,
        "warnings": list(warnings),
    }
    return {
        "workflow": [
            {"step": "cost", "workbook_sheet": "cost", "status": "calculated"},
            {"step": "logistics", "workbook_sheet": "cost", "status": "calculated"},
            {"step": "fx", "workbook_sheet": "cost", "status": "latest_stored_rate" if fx_payload else "missing_or_not_required"},
            {"step": "price_tier", "workbook_sheet": "price_list", "status": "interval_table_ready" if interval_quote_table else ("selected" if tier_snapshot else "cost_model_fallback")},
            {"step": "profit_check", "workbook_sheet": "profit_calculator", "status": "calculated"},
            {"step": "customer_quote", "workbook_sheet": "Quote", "status": "customer_safe_output"},
        ],
        "product": {
            "id": str(product.id),
            "name": product.product_name,
            "category": product.product_category,
            "family": product.product_family,
        },
        "inputs": {
            "quantity": quantity,
            "incoterm": incoterm,
            "pricing_strategy": pricing_strategy,
            "discount": discount,
        },
        "fx_stage": fx_payload
        or {
            "base_currency": "USD",
            "quote_currency": "CNY",
            "rate": None,
            "source": "not_available",
        },
        "cost_stage": {
            "material_cost_rmb": cost_breakdown.get("unit_material_cost_rmb"),
            "material_cost_after_domestic_profit_rmb": cost_breakdown.get(
                "unit_material_cost_after_domestic_profit_rmb"
            ),
            "fob_cost_usd": cost_breakdown.get("fob_cost_usd"),
            "ddp_cost_usd": cost_breakdown.get("ddp_cost_usd"),
            "selected_cost_basis_usd": cost_basis,
            "internal_only": True,
        },
        "logistics_stage": {
            "unit_weight": cost_breakdown.get("unit_weight"),
            "ocean_freight_unit_price": cost_breakdown.get("ocean_freight_unit_price"),
            "domestic_transport_cost": cost_breakdown.get("domestic_transport_cost"),
            "freight_cost_usd": cost_breakdown.get("freight_cost_usd"),
            "basis": logistics_basis,
            "internal_only": True,
        },
        "pricing_stage": {
            "source": source,
            "tier": tier_snapshot,
            "interval_quote_table": interval_quote_table,
            "selected_interval": selected_interval,
            "margin": margin_snapshot,
            "base_unit_price": price_breakdown.get("base_unit_price"),
            "final_unit_price_before_discount": price_breakdown.get("final_unit_price"),
        },
        "discount_stage": {
            "discount_amount": price_breakdown.get("discount_amount"),
            "final_unit_price_after_discount": price_breakdown.get("final_unit_price_after_discount"),
        },
        "final_quote_stage": {
            "currency": "USD",
            "unit_price": price_breakdown.get("final_unit_price_after_discount"),
            "line_subtotal": price_breakdown.get("line_subtotal"),
            "interval_quote_table": interval_quote_table,
            "selected_interval": selected_interval,
            "customer_visible": True,
            "pdf_ready_fields": [
                "product_name",
                "quantity_ranges",
                "fob_unit_price",
                "ddp_unit_price",
                "incoterm",
                "unit_price",
                "line_subtotal",
            ],
        },
        "profit_stage": {
            "estimated_unit_profit": profit_breakdown.get("estimated_unit_profit"),
            "estimated_total_profit": profit_breakdown.get("estimated_total_profit"),
            "estimated_margin": profit_breakdown.get("estimated_margin"),
            "internal_only": True,
        },
        "customer_safe_boundary": (
            "PDF/customer output may show product, quantity ranges, FOB/DDP unit prices, selected incoterm, final unit price and totals only. "
            "Cost, margin, pricing breakdown, supplier private notes and internal calculations remain internal."
        ),
        "internal_cost_snapshot": internal_snapshot,
        "warnings": list(warnings),
        "safety": dict(PRICING_SAFETY),
    }


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
    if fx and fx.rate_date < date.today():
        warnings.append("fx_rate_stale")

    interval_quote_table = build_product_interval_quote_table(
        db,
        product_id=product_id,
        pricing_strategy=pricing_strategy,
        ref=ref,
    )
    selected_interval = _selected_interval_row(interval_quote_table, quantity=quantity)
    if not interval_quote_table:
        warnings.append("interval_quote_table_missing")

    source = "price_tier"
    base_unit = Decimal("0")
    unit_cost_for_margin: Decimal | None = None
    tier_snapshot: dict[str, Any] | None = None
    margin_snapshot: dict[str, str] | None = None
    cost_breakdown: dict[str, str] = {
        "cost_currency": "CNY",
        "unit_material_cost_rmb": "0.00",
        "unit_material_cost_after_domestic_profit_rmb": "0.00",
        "unit_material_cost_usd": "0.00",
        "unit_material_cost_after_domestic_profit_usd": "0.00",
        "unit_weight": "0.00",
        "ocean_freight_unit_price": "0.00",
        "domestic_transport_cost": "0.00",
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
            tier_snapshot = {
                "id": str(tier.id),
                "min_qty": tier.min_qty,
                "max_qty": tier.max_qty,
                "incoterm": tier.incoterm,
                "currency": tier.currency,
                "pricing_strategy": tier.pricing_strategy,
                "base_unit_price": str(tier.base_unit_price) if tier.base_unit_price is not None else None,
                "adjustment_value": str(tier.adjustment_value) if tier.adjustment_value is not None else None,
                "final_unit_price": str(tier.final_unit_price) if tier.final_unit_price is not None else None,
                "source": tier.source,
            }
        elif selected_interval and inc not in selected_interval.get("incoterms_available", []):
            raise ApiError(
                VALIDATION_ERROR,
                f"{inc} is not available for quantity range {selected_interval.get('quantity_label')} on this product",
                status_code=400,
                details={
                    "quantity_range": selected_interval.get("quantity_label"),
                    "available_incoterms": selected_interval.get("incoterms_available", []),
                },
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
            margin_snapshot = {"strategy": pricing_strategy, "multiplier": str(mult)}
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
        if unit_cost_for_margin is not None and inc == "DDP" and cost_breakdown.get("ddp_cost_usd"):
            unit_cost_for_margin = Decimal(cost_breakdown["ddp_cost_usd"])

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

    price_breakdown = {
        "base_unit_price": money(base_unit),
        "adjustment_value": "0.00",
        "final_unit_price": money(base_unit),
        "discount_amount": money(discount_amount),
        "final_unit_price_after_discount": money(final_unit),
        "line_subtotal": money(line_subtotal),
    }
    profit_breakdown = {
        "estimated_unit_profit": money(
            (final_unit - (unit_cost_for_margin or Decimal("0"))).quantize(Decimal("0.0001"))
        ),
        "estimated_total_profit": profit_total,
        "estimated_margin": margin_pct,
    }
    quote_model = _quote_model_snapshot(
        source=source,
        product=product,
        quantity=quantity,
        incoterm=inc,
        pricing_strategy=pricing_strategy,
        discount=discount,
        fx_payload=fx_payload,
        cost_breakdown=cost_breakdown,
        price_breakdown=price_breakdown,
        profit_breakdown=profit_breakdown,
        tier_snapshot=tier_snapshot,
        margin_snapshot=margin_snapshot,
        interval_quote_table=interval_quote_table,
        selected_interval=selected_interval,
        warnings=warnings,
    )

    return {
        "product_id": str(product_id),
        "quantity": quantity,
        "incoterm": inc,
        "pricing_strategy": pricing_strategy,
        "currency": "USD",
        "fx_rate_used": fx_payload,
        "cost_breakdown": cost_breakdown,
        "price_breakdown": price_breakdown,
        "profit_breakdown": profit_breakdown,
        "quote_model": quote_model,
        "warnings": warnings,
        "source": source,
        "safety": dict(PRICING_SAFETY),
    }
