"""Pure pricing calculations (D6.2 — no DB, Decimal-safe)."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

TWO = Decimal("0.01")
FOUR = Decimal("0.0001")
ZERO = Decimal("0")

VALID_INCOTERMS = frozenset({"EXW", "FOB", "CIF", "DDP"})
VALID_STRATEGIES = frozenset({"traffic", "volume", "profit"})

FORBIDDEN_PHRASES = (
    "guaranteed price",
    "in stock",
    "certified for",
    "delivery guaranteed",
    "lead time confirmed",
)


def money(value: Decimal | None) -> str:
    if value is None:
        return "0.00"
    return str(value.quantize(TWO, rounding=ROUND_HALF_UP))


def qty_in_tier(quantity: int, min_qty: int, max_qty: int | None) -> bool:
    if quantity < min_qty:
        return False
    if max_qty is not None and quantity > max_qty:
        return False
    return True


def tier_unit_price(
    *,
    base_unit_price: Decimal | None,
    adjustment_value: Decimal | None,
    final_unit_price: Decimal | None,
) -> Decimal:
    if final_unit_price is not None:
        return final_unit_price
    base = base_unit_price or ZERO
    adj = adjustment_value or ZERO
    return (base + adj).quantize(FOUR, rounding=ROUND_HALF_UP)


def compute_cost_breakdown(
    *,
    unit_material_cost: Decimal | None,
    cost_currency: str,
    unit_weight: Decimal | None,
    ocean_freight_unit_price: Decimal | None,
    domestic_transport_cost: Decimal | None,
    domestic_profit_rate: Decimal | None,
    fx_rate_usd_cny: Decimal | None,
    stored_fob_cost_usd: Decimal | None,
    stored_ddp_cost_usd: Decimal | None,
) -> tuple[dict[str, str], Decimal | None]:
    """Return workbook-aligned cost breakdown and FOB unit cost.

    The source workbook's cost sheet calculates:
    - transport cost = weight * ocean freight unit price
    - transport USD = transport cost / FX
    - FOB cost USD = material cost / FX
    - DDP cost USD = (material cost + transport cost) / FX

    When stored FOB/DDP costs exist, they remain the source of truth. Otherwise
    the same workbook calculation is used, with domestic_profit_rate applied to
    material cost before currency conversion.
    """
    material_rmb = unit_material_cost or ZERO
    weight = unit_weight or ZERO
    calculated_transport = (weight * (ocean_freight_unit_price or ZERO)).quantize(
        FOUR, rounding=ROUND_HALF_UP
    )
    transport_rmb = domestic_transport_cost if domestic_transport_cost is not None else calculated_transport
    weight = unit_weight or ZERO
    profit_rate = domestic_profit_rate or ZERO
    material_after_domestic_profit = (material_rmb * (Decimal("1") + profit_rate)).quantize(
        FOUR, rounding=ROUND_HALF_UP
    )

    material_usd = ZERO
    transport_usd = ZERO
    material_after_profit_usd = ZERO
    if cost_currency.upper() == "CNY":
        if fx_rate_usd_cny is None or fx_rate_usd_cny <= ZERO:
            raise ValueError("FX_RATE_MISSING")
        material_usd = (material_rmb / fx_rate_usd_cny).quantize(FOUR, rounding=ROUND_HALF_UP)
        material_after_profit_usd = (material_after_domestic_profit / fx_rate_usd_cny).quantize(
            FOUR, rounding=ROUND_HALF_UP
        )
        transport_usd = (transport_rmb / fx_rate_usd_cny).quantize(FOUR, rounding=ROUND_HALF_UP)
    elif cost_currency.upper() == "USD":
        material_usd = material_rmb
        material_after_profit_usd = material_after_domestic_profit
        transport_usd = transport_rmb
    else:
        material_usd = material_rmb
        material_after_profit_usd = material_after_domestic_profit
        transport_usd = transport_rmb

    fob_cost = stored_fob_cost_usd
    if fob_cost is None:
        fob_cost = material_after_profit_usd.quantize(FOUR, rounding=ROUND_HALF_UP)
    ddp_cost = stored_ddp_cost_usd
    if ddp_cost is None:
        ddp_cost = (fob_cost + transport_usd).quantize(FOUR, rounding=ROUND_HALF_UP)

    breakdown = {
        "cost_currency": cost_currency.upper(),
        "unit_material_cost_rmb": money(material_rmb if cost_currency.upper() == "CNY" else ZERO),
        "unit_material_cost_after_domestic_profit_rmb": money(
            material_after_domestic_profit if cost_currency.upper() == "CNY" else ZERO
        ),
        "unit_material_cost_usd": money(material_usd),
        "unit_material_cost_after_domestic_profit_usd": money(material_after_profit_usd),
        "unit_weight": money(weight),
        "ocean_freight_unit_price": money(ocean_freight_unit_price or ZERO),
        "domestic_transport_cost": money(transport_rmb),
        "freight_cost_usd": money(transport_usd),
        "fob_cost_usd": money(fob_cost),
        "ddp_cost_usd": money(ddp_cost),
    }
    return breakdown, fob_cost


def apply_discount(unit_price: Decimal, quantity: int, discount: dict | None) -> tuple[Decimal, Decimal]:
    if not discount:
        return unit_price, ZERO
    dtype = (discount.get("type") or "").lower()
    value = Decimal(str(discount.get("value") or 0))
    if dtype == "percentage":
        disc = (unit_price * value / Decimal("100")).quantize(FOUR, rounding=ROUND_HALF_UP)
    elif dtype == "amount":
        disc = (value / Decimal(quantity)).quantize(FOUR, rounding=ROUND_HALF_UP) if quantity else ZERO
    else:
        disc = ZERO
    final = max(unit_price - disc, ZERO).quantize(FOUR, rounding=ROUND_HALF_UP)
    return final, (disc * quantity).quantize(TWO, rounding=ROUND_HALF_UP)


def compute_profit(final_unit: Decimal, unit_cost: Decimal | None, quantity: int) -> tuple[str, str]:
    cost = unit_cost or ZERO
    profit_unit = (final_unit - cost).quantize(FOUR, rounding=ROUND_HALF_UP)
    total_profit = (profit_unit * quantity).quantize(TWO, rounding=ROUND_HALF_UP)
    margin = ZERO
    if final_unit > ZERO:
        margin = (profit_unit / final_unit * Decimal("100")).quantize(TWO, rounding=ROUND_HALF_UP)
    return money(total_profit), money(margin)


def assert_no_forbidden_phrases(text: str) -> None:
    lower = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            raise ValueError(f"Forbidden phrase: {phrase}")
