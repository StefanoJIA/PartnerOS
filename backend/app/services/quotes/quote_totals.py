"""Quote totals calculation (D6.3)."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.customer_quotes import Quote, QuoteAdjustment, QuoteLineItem

DEFAULT_SUBJECT = "Subject to confirmation"


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def line_total(line: QuoteLineItem) -> Decimal:
    return money(Decimal(str(line.total_price)))


def adjustment_amount(adj: QuoteAdjustment, *, subtotal: Decimal) -> Decimal:
    if adj.percentage is not None:
        return money(subtotal * (Decimal(str(adj.percentage)) / Decimal("100")))
    return money(Decimal(str(adj.amount)))


def calculate_quote_totals(quote: Quote) -> dict[str, Decimal]:
    subtotal = money(sum((line_total(li) for li in quote.line_items), Decimal("0")))
    discount_total = Decimal("0")
    shipping_total = Decimal("0")
    sample_fee_total = Decimal("0")
    tax_total = Decimal("0")
    other_total = Decimal("0")

    for adj in quote.adjustments:
        amt = adjustment_amount(adj, subtotal=subtotal)
        if adj.type == "discount":
            discount_total += amt
        elif adj.type == "shipping":
            shipping_total += amt
        elif adj.type == "sample_fee":
            sample_fee_total += amt
        elif adj.type == "tax":
            tax_total += amt
        else:
            other_total += amt

    adjustment_total = money(shipping_total + sample_fee_total + other_total - discount_total)
    grand = money(subtotal + adjustment_total + tax_total)
    if grand < Decimal("0"):
        grand = Decimal("0")

    return {
        "subtotal": subtotal,
        "adjustment_total": adjustment_total,
        "discount_total": money(discount_total),
        "shipping_total": money(shipping_total),
        "sample_fee_total": money(sample_fee_total),
        "tax_total": money(tax_total),
        "grand_total": grand,
    }


def apply_totals_to_quote(quote: Quote) -> dict[str, Decimal]:
    totals = calculate_quote_totals(quote)
    quote.subtotal = totals["subtotal"]
    quote.adjustment_total = totals["adjustment_total"]
    quote.tax_total = totals["tax_total"]
    quote.grand_total = totals["grand_total"]
    return totals
