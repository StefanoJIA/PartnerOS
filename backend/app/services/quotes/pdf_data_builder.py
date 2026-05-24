"""Build customer-visible quote data for PDF export (D6.4)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ApiError, NOT_FOUND, VALIDATION_ERROR
from app.models import ManufacturingPartner
from app.models.customer_quotes import Quote, QuoteVersion
from app.services.quotes.quote_service import get_quote
from app.services.quotes.quote_totals import DEFAULT_SUBJECT

PDF_SAFETY: dict[str, bool] = {
    "automatic_sending_enabled": False,
    "inventory_promised": False,
    "certification_promised": False,
    "lead_time_promised": False,
    "order_created": False,
}

COMPANY_PROFILE: dict[str, str] = {
    "brand": "IntelliOpus Engineering / intelliOffice",
    "address_line": "529 Main Street, Suite 2000, Charlestown, MA 02129",
    "website": "",
    "phone": "",
}

INTERNAL_LINE_KEYS = frozenset(
    {
        "internal_cost",
        "estimated_margin",
        "pricing_breakdown_json",
        "cost_snapshot_json",
        "pricing_source",
        "pricing_strategy",
        "internal_sku",
        "requires_review",
        "warnings",
        "partner_product_code",
        "product_catalog_id",
    }
)

FOOTER_SAFETY = (
    "This quote is subject to final confirmation of availability, specifications, and logistics where applicable."
)


def _partner_names(db: Session, partner_ids: set[str]) -> dict[str, str]:
    if not partner_ids:
        return {}
    uuids = []
    for pid in partner_ids:
        try:
            uuids.append(UUID(pid))
        except ValueError:
            continue
    if not uuids:
        return {}
    rows = db.query(ManufacturingPartner).filter(ManufacturingPartner.id.in_(uuids)).all()
    return {str(r.id): r.partner_name for r in rows}


def _line_description(line: dict[str, Any]) -> str:
    parts: list[str] = []
    category = line.get("product_category")
    if category:
        parts.append(str(category))
    color = line.get("color_finish")
    if color:
        parts.append(f"Color/Finish: {color}")
    size = line.get("size_dimension")
    if size:
        parts.append(f"Size: {size}")
    return " | ".join(parts)


def _sanitize_line(line: dict[str, Any], *, partner_name: str | None, export_type: str) -> dict[str, Any]:
    clean = {k: v for k, v in line.items() if k not in INTERNAL_LINE_KEYS}
    if export_type != "internal_pdf":
        clean.pop("internal_notes", None)
    return {
        "line_number": clean.get("line_number"),
        "partner": partner_name or "",
        "product_name": clean.get("product_name") or clean.get("manual_product_name") or "",
        "description": _line_description(clean),
        "quantity": clean.get("quantity"),
        "uom": clean.get("uom") or "EA",
        "unit_price": clean.get("final_unit_price") or clean.get("unit_price") or "0",
        "total_price": clean.get("total_price") or "0",
        "currency": clean.get("currency") or "USD",
        "incoterm": clean.get("incoterm") or "",
        "color_finish": clean.get("color_finish") or "",
        "size_dimension": clean.get("size_dimension") or "",
    }


def _sanitize_adjustment(adj: dict[str, Any], *, export_type: str) -> dict[str, Any] | None:
    if export_type == "customer_pdf" and adj.get("customer_visible") is False:
        return None
    return {
        "type": adj.get("type"),
        "label": adj.get("label"),
        "amount": adj.get("amount"),
        "percentage": adj.get("percentage"),
    }


def _totals_from_snapshot(snapshot: dict[str, Any]) -> dict[str, str]:
    totals = snapshot.get("totals") or {}
    subtotal = totals.get("subtotal", "0")
    tax = totals.get("tax_total", "0")
    grand = totals.get("grand_total", "0")
    adjustments = snapshot.get("adjustments") or []
    discount = "0"
    shipping = "0"
    sample_fee = "0"
    for adj in adjustments:
        if adj.get("customer_visible") is False:
            continue
        amt = adj.get("amount", "0")
        t = adj.get("type")
        if t == "discount":
            discount = amt
        elif t == "shipping":
            shipping = amt
        elif t == "sample_fee":
            sample_fee = amt
    return {
        "subtotal": str(subtotal),
        "discount": str(discount),
        "shipping": str(shipping),
        "sample_fee": str(sample_fee),
        "tax": str(tax),
        "grand_total": str(grand),
        "currency": snapshot.get("currency") or "USD",
    }


def _totals_from_quote(quote: Quote) -> dict[str, str]:
    discount = "0"
    shipping = "0"
    sample_fee = "0"
    for adj in quote.adjustments:
        if not adj.customer_visible:
            continue
        amt = str(adj.amount)
        if adj.type == "discount":
            discount = amt
        elif adj.type == "shipping":
            shipping = amt
        elif adj.type == "sample_fee":
            sample_fee = amt
    return {
        "subtotal": str(quote.subtotal),
        "discount": discount,
        "shipping": shipping,
        "sample_fee": sample_fee,
        "tax": str(quote.tax_total),
        "grand_total": str(quote.grand_total),
        "currency": quote.currency,
    }


def _terms_from_quote(quote: Quote) -> dict[str, str]:
    validity = DEFAULT_SUBJECT
    notes = quote.customer_notes or ""
    if quote.terms:
        validity = quote.terms.validity_terms or validity
        notes = quote.terms.notes or notes
    return {
        "payment_terms": quote.payment_terms or DEFAULT_SUBJECT,
        "shipping_terms": quote.shipping_terms or DEFAULT_SUBJECT,
        "validity_terms": validity,
        "notes": notes or "",
    }


def _terms_from_snapshot(snapshot: dict[str, Any]) -> dict[str, str]:
    terms = snapshot.get("terms") or {}
    return {
        "payment_terms": terms.get("payment_terms") or DEFAULT_SUBJECT,
        "shipping_terms": terms.get("shipping_terms") or DEFAULT_SUBJECT,
        "validity_terms": terms.get("validity_terms") or DEFAULT_SUBJECT,
        "notes": terms.get("notes") or snapshot.get("customer_notes") or "",
    }


def build_quote_pdf_data(
    db: Session,
    quote_id: UUID,
    *,
    version_id: UUID | None = None,
    export_type: str = "customer_pdf",
) -> dict[str, Any]:
    if export_type not in ("customer_pdf", "internal_pdf", "partner_pdf", "summary_pdf"):
        raise ApiError(VALIDATION_ERROR, f"unsupported export_type: {export_type}", status_code=400)

    quote = get_quote(db, quote_id)
    version: QuoteVersion | None = None
    if version_id:
        version = (
            db.query(QuoteVersion)
            .filter(QuoteVersion.id == version_id, QuoteVersion.quote_id == quote_id)
            .first()
        )
        if not version:
            raise ApiError(NOT_FOUND, "quote version not found", status_code=404)

    if version and version.snapshot_json:
        snapshot = version.snapshot_json
        partner_ids = {str(li.get("partner_id")) for li in snapshot.get("line_items") or [] if li.get("partner_id")}
        partners = _partner_names(db, partner_ids)
        line_items = []
        for raw in sorted(snapshot.get("line_items") or [], key=lambda x: x.get("line_number", 0)):
            pname = partners.get(str(raw.get("partner_id")), "")
            line_items.append(_sanitize_line(raw, partner_name=pname, export_type=export_type))
        adjustments = [
            a
            for a in (
                _sanitize_adjustment(x, export_type=export_type) for x in snapshot.get("adjustments") or []
            )
            if a
        ]
        bill = snapshot.get("bill_to") or {}
        ship = snapshot.get("ship_to") or {}
        return {
            "quote": {
                "id": str(quote.id),
                "quote_number": snapshot.get("quote_number") or quote.quote_number,
                "quote_date": snapshot.get("quote_date") or str(quote.quote_date),
                "valid_until": snapshot.get("valid_until") or str(quote.valid_until),
                "status": snapshot.get("status") or quote.status,
                "currency": snapshot.get("currency") or quote.currency,
                "default_incoterm": quote.default_incoterm or "",
                "sales_owner": "",
            },
            "version": {
                "id": str(version.id),
                "version_number": version.version_number,
                "version_label": version.version_label,
            },
            "bill_to": {
                "company": bill.get("company") or "",
                "contact": bill.get("name") or "",
                "address": bill.get("address") or "",
            },
            "ship_to": {
                "company": ship.get("company") or "",
                "contact": ship.get("name") or "",
                "address": ship.get("address") or "",
            },
            "line_items": line_items,
            "adjustments": adjustments,
            "totals": _totals_from_snapshot(snapshot),
            "terms": _terms_from_snapshot(snapshot),
            "company_profile": dict(COMPANY_PROFILE),
            "safety": dict(PDF_SAFETY),
            "footer_safety": FOOTER_SAFETY,
        }

    partner_ids = {str(li.partner_id) for li in quote.line_items}
    partners = _partner_names(db, partner_ids)
    line_items = []
    for li in sorted(quote.line_items, key=lambda x: x.line_number):
        raw = {
            "line_number": li.line_number,
            "partner_id": str(li.partner_id),
            "product_name": li.product_name,
            "manual_product_name": li.manual_product_name,
            "product_category": li.product_category,
            "quantity": li.quantity,
            "uom": li.uom,
            "unit_price": str(li.unit_price),
            "final_unit_price": str(li.final_unit_price),
            "total_price": str(li.total_price),
            "currency": li.currency,
            "incoterm": li.incoterm,
            "color_finish": li.color_finish,
            "size_dimension": li.size_dimension,
            "internal_cost": str(li.internal_cost) if li.internal_cost is not None else None,
            "estimated_margin": str(li.estimated_margin) if li.estimated_margin is not None else None,
            "pricing_breakdown_json": li.pricing_breakdown_json,
        }
        line_items.append(_sanitize_line(raw, partner_name=partners.get(str(li.partner_id)), export_type=export_type))

    adjustments = [
        a
        for a in (
            _sanitize_adjustment(
                {
                    "type": adj.type,
                    "label": adj.label,
                    "amount": str(adj.amount),
                    "percentage": str(adj.percentage) if adj.percentage is not None else None,
                    "customer_visible": adj.customer_visible,
                },
                export_type=export_type,
            )
            for adj in quote.adjustments
        )
        if a
    ]

    version_info = None
    if version:
        version_info = {
            "id": str(version.id),
            "version_number": version.version_number,
            "version_label": version.version_label,
        }

    return {
        "quote": {
            "id": str(quote.id),
            "quote_number": quote.quote_number,
            "quote_date": str(quote.quote_date),
            "valid_until": str(quote.valid_until),
            "status": quote.status,
            "currency": quote.currency,
            "default_incoterm": quote.default_incoterm or "",
            "sales_owner": "",
        },
        "version": version_info,
        "bill_to": {
            "company": quote.bill_to_company or "",
            "contact": quote.bill_to_name or "",
            "address": quote.bill_to_address or "",
        },
        "ship_to": {
            "company": quote.ship_to_company or "",
            "contact": quote.ship_to_name or "",
            "address": quote.ship_to_address or "",
        },
        "line_items": line_items,
        "adjustments": adjustments,
        "totals": _totals_from_quote(quote),
        "terms": _terms_from_quote(quote),
        "company_profile": dict(COMPANY_PROFILE),
        "safety": dict(PDF_SAFETY),
        "footer_safety": FOOTER_SAFETY,
    }
