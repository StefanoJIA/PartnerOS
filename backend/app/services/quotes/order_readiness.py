"""Quote-to-order readiness gate (D6.6) — derived checks only, no order creation."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models import Company, Contact, ManufacturingPartner
from app.models.customer_quotes import Quote, QuoteDeliveryLog, QuotePdfExport
from app.services.quotes.quote_service import derived_expired, get_quote

READINESS_SAFETY: dict[str, bool] = {
    "order_created": False,
    "production_started": False,
    "shipment_created": False,
    "automatic_sending_enabled": False,
    "inventory_promised": False,
    "certification_promised": False,
    "lead_time_promised": False,
}

FORBIDDEN_PHRASES = (
    "order created",
    "production started",
    "shipment created",
    "inventory confirmed",
    "lead time confirmed",
    "delivery guaranteed",
    "in stock",
)

HIGH_DISCOUNT_THRESHOLD = Decimal("15")

INTERNAL_PRICING_SOURCES = frozenset({"manual_unit_price", "cost_model", "unknown"})


def _check_item(key: str, label: str, *, passed: bool, warning: bool = False, details: str = "") -> dict[str, Any]:
    if passed:
        status = "pass"
    elif warning:
        status = "warning"
    else:
        status = "fail"
    return {"key": key, "label": label, "status": status, "details": details}


def _has_text(value: str | None) -> bool:
    return bool((value or "").strip())


def _partner_map(db: Session, partner_ids: set[UUID]) -> dict[str, str]:
    if not partner_ids:
        return {}
    rows = db.query(ManufacturingPartner).filter(ManufacturingPartner.id.in_(partner_ids)).all()
    return {str(r.id): r.partner_name for r in rows}


def _latest_version(quote: Quote):
    if not quote.versions:
        return None
    return max(quote.versions, key=lambda v: v.version_number)


def _latest_pdf_export(quote: Quote) -> QuotePdfExport | None:
    exports = [e for e in quote.pdf_exports if e.status == "generated"]
    if not exports:
        return None
    return max(exports, key=lambda e: e.exported_at or e.created_at)


def _latest_delivery_log(quote: Quote) -> QuoteDeliveryLog | None:
    logs = [l for l in quote.delivery_logs if l.status == "recorded"]
    if not logs:
        return None
    return max(logs, key=lambda l: l.sent_at)


def _build_order_input_contract(
    db: Session,
    quote: Quote,
    *,
    partners: dict[str, str],
    version_id: UUID | None,
    pdf_export_id: UUID | None,
    delivery_log_id: UUID | None,
) -> dict[str, Any]:
    company_name = quote.bill_to_company
    contact_name = quote.bill_to_name
    if quote.company_id:
        company = db.query(Company).filter(Company.id == quote.company_id).first()
        if company:
            company_name = company_name or company.company_name
    if quote.contact_id:
        contact = db.query(Contact).filter(Contact.id == quote.contact_id).first()
        if contact:
            contact_name = contact_name or f"{contact.first_name} {contact.last_name}".strip() or contact.email

    line_items = []
    partner_routes: dict[str, list[str]] = {}
    for li in sorted(quote.line_items, key=lambda x: x.line_number):
        pname = partners.get(str(li.partner_id), "")
        partner_routes.setdefault(pname or str(li.partner_id), []).append(str(li.id))
        line_items.append(
            {
                "quote_line_item_id": str(li.id),
                "partner_id": str(li.partner_id),
                "partner_name": pname,
                "product_catalog_id": str(li.product_catalog_id) if li.product_catalog_id else None,
                "product_name": li.product_name,
                "quantity": li.quantity,
                "unit_price": str(li.final_unit_price),
                "total_price": str(li.total_price),
                "incoterm": li.incoterm or quote.default_incoterm or "",
                "color_finish": li.color_finish,
                "size_dimension": li.size_dimension,
                "attributes_snapshot_json": li.attributes_snapshot_json,
            }
        )

    return {
        "customer": {
            "company_id": str(quote.company_id) if quote.company_id else None,
            "company_name": company_name or "",
            "contact_id": str(quote.contact_id) if quote.contact_id else None,
            "contact_name": contact_name or "",
        },
        "billing": {
            "bill_to_name": quote.bill_to_name or "",
            "bill_to_company": quote.bill_to_company or "",
            "bill_to_address": quote.bill_to_address or "",
        },
        "shipping": {
            "ship_to_name": quote.ship_to_name or "",
            "ship_to_company": quote.ship_to_company or "",
            "ship_to_address": quote.ship_to_address or "",
        },
        "line_items": line_items,
        "partner_routes": [{"partner_name": k, "line_item_ids": v} for k, v in partner_routes.items()],
        "totals": {
            "subtotal": str(quote.subtotal),
            "adjustments": str(quote.adjustment_total),
            "grand_total": str(quote.grand_total),
            "currency": quote.currency,
        },
        "terms": {
            "payment_terms": quote.payment_terms or "",
            "shipping_terms": quote.shipping_terms or "",
            "valid_until": str(quote.valid_until),
        },
        "source_quote": {
            "quote_id": str(quote.id),
            "quote_number": quote.quote_number,
            "quote_version_id": str(version_id) if version_id else None,
            "pdf_export_id": str(pdf_export_id) if pdf_export_id else None,
            "delivery_log_id": str(delivery_log_id) if delivery_log_id else None,
        },
        "safety": {
            "order_created": False,
            "production_started": False,
            "shipment_created": False,
        },
    }


def _resolve_status(
    *,
    quote: Quote,
    blocking: list[str],
    internal_review: list[str],
) -> str:
    if blocking or quote.status != "sent":
        return "not_ready"
    if internal_review:
        return "needs_internal_review"
    return "needs_customer_confirmation"


def _recommended_action(status: str, blocking: list[str], warnings: list[str]) -> str:
    if status == "not_ready":
        if blocking:
            return f"Resolve blocking items before order review: {', '.join(blocking[:3])}"
        return "Quote is not ready for order review — ensure quote is sent and complete."
    if status == "needs_internal_review":
        return "Complete internal pricing and supplier review before order planning."
    if status == "needs_customer_confirmation":
        return "Obtain explicit customer order confirmation outside intelliOffice before future order conversion."
    return "Ready for manual order review in a future order module — no order is created in this stage."


def build_quote_order_readiness(db: Session, quote_id: UUID) -> dict[str, Any]:
    quote = (
        db.query(Quote)
        .options(
            joinedload(Quote.line_items),
            joinedload(Quote.adjustments),
            joinedload(Quote.versions),
            joinedload(Quote.pdf_exports),
            joinedload(Quote.delivery_logs),
        )
        .filter(Quote.id == quote_id, Quote.is_archived.is_(False))
        .first()
    )
    if not quote:
        get_quote(db, quote_id)

    expired = derived_expired(quote) or quote.status == "expired"
    latest_version = _latest_version(quote)
    latest_pdf = _latest_pdf_export(quote)
    latest_delivery = _latest_delivery_log(quote)

    partner_ids = {li.partner_id for li in quote.line_items}
    partners = _partner_map(db, partner_ids)
    multi_partner = len(partner_ids) > 1

    checklist: list[dict[str, Any]] = []
    blocking_items: list[str] = []
    warning_items: list[str] = []
    internal_review_flags: list[str] = []

    checklist.append(_check_item("quote_created", "Quote created", passed=True, details=quote.quote_number))
    sent = quote.status == "sent" and quote.manual_sent
    checklist.append(
        _check_item(
            "quote_sent",
            "Quote has been sent",
            passed=sent,
            details=f"status={quote.status}, manual_sent={quote.manual_sent}",
        )
    )
    if not sent:
        blocking_items.append("quote_not_sent")

    checklist.append(
        _check_item(
            "not_expired",
            "Quote validity not expired",
            passed=not expired,
            details=f"valid_until={quote.valid_until}",
        )
    )
    if expired:
        blocking_items.append("quote_expired")

    checklist.append(
        _check_item(
            "latest_version_identified",
            "Latest quote version identified",
            passed=latest_version is not None,
            warning=latest_version is None and bool(quote.versions),
            details=latest_version.version_label if latest_version else "no version snapshot",
        )
    )

    has_pdf = latest_pdf is not None
    checklist.append(
        _check_item(
            "pdf_export_exists",
            "Customer PDF export exists",
            passed=has_pdf,
            details=latest_pdf.file_name if latest_pdf else "no PDF export",
        )
    )
    if not has_pdf:
        blocking_items.append("missing_pdf_export")

    has_delivery = latest_delivery is not None
    checklist.append(
        _check_item(
            "delivery_log_exists",
            "Manual delivery recorded",
            passed=has_delivery,
            warning=not has_delivery and sent,
            details=latest_delivery.sent_channel if latest_delivery else "no delivery log",
        )
    )
    if sent and not has_delivery:
        warning_items.append("missing_delivery_log")

    bill_ok = _has_text(quote.bill_to_company) or _has_text(quote.bill_to_address)
    ship_ok = _has_text(quote.ship_to_company) or _has_text(quote.ship_to_address)
    contact_ok = _has_text(quote.bill_to_name) or quote.contact_id is not None

    checklist.append(_check_item("customer_company_present", "Customer company present", passed=bill_ok))
    checklist.append(_check_item("contact_present", "Contact present", passed=contact_ok, warning=not contact_ok))
    checklist.append(_check_item("bill_to_present", "Bill To present", passed=bill_ok))
    checklist.append(_check_item("ship_to_present", "Ship To present", passed=ship_ok))
    if not bill_ok:
        blocking_items.append("missing_bill_to")
    if not ship_ok:
        blocking_items.append("missing_ship_to")
    if not contact_ok:
        warning_items.append("missing_contact")

    has_lines = len(quote.line_items) > 0
    checklist.append(_check_item("line_items_present", "Line items present", passed=has_lines))
    if not has_lines:
        blocking_items.append("missing_line_items")

    all_priced = all(li.final_unit_price > 0 and li.total_price > 0 for li in quote.line_items) if has_lines else False
    checklist.append(_check_item("all_lines_priced", "All lines priced", passed=all_priced))
    if has_lines and not all_priced:
        blocking_items.append("unpriced_lines")

    qty_ok = all(li.quantity > 0 for li in quote.line_items) if has_lines else False
    checklist.append(_check_item("quantity_present", "Quantities present", passed=qty_ok))

    grand_positive = quote.grand_total > 0
    checklist.append(
        _check_item(
            "grand_total_positive",
            "Grand total positive",
            passed=grand_positive,
            details=str(quote.grand_total),
        )
    )
    if not grand_positive:
        blocking_items.append("invalid_grand_total")

    payment_ok = _has_text(quote.payment_terms)
    shipping_terms_ok = _has_text(quote.shipping_terms)
    checklist.append(_check_item("payment_terms_present", "Payment terms present", passed=payment_ok))
    checklist.append(_check_item("shipping_terms_present", "Shipping terms present", passed=shipping_terms_ok))
    if not payment_ok:
        warning_items.append("missing_payment_terms")
    if not shipping_terms_ok:
        warning_items.append("missing_shipping_terms")

    checklist.append(_check_item("currency_present", "Currency present", passed=_has_text(quote.currency)))

    partner_each = all(li.partner_id for li in quote.line_items)
    checklist.append(_check_item("partner_present_for_each_line", "Partner on each line", passed=partner_each))
    checklist.append(
        _check_item(
            "product_scope_clear",
            "Product scope clear",
            passed=all(_has_text(li.product_name) for li in quote.line_items) if has_lines else False,
        )
    )
    checklist.append(
        _check_item(
            "multi_partner_detected",
            "Multi-partner quote",
            passed=not multi_partner,
            warning=multi_partner,
            details=f"{len(partner_ids)} partner(s)" if multi_partner else "single partner",
        )
    )
    if multi_partner:
        internal_review_flags.append("multi_partner")
        warning_items.append("multi_partner_quote")

    manual_product = any(not li.product_catalog_id for li in quote.line_items)
    checklist.append(
        _check_item(
            "manual_product_detected",
            "Manual product line detected",
            passed=not manual_product,
            warning=manual_product,
        )
    )
    if manual_product:
        warning_items.append("manual_product_lines")

    manual_price = any(li.pricing_source in INTERNAL_PRICING_SOURCES for li in quote.line_items)
    cost_model = any(li.pricing_source == "cost_model" for li in quote.line_items)
    requires_review = any(li.requires_review for li in quote.line_items)

    checklist.append(
        _check_item(
            "manual_price_present",
            "Manual pricing present",
            passed=not manual_price,
            warning=manual_price,
        )
    )
    checklist.append(
        _check_item(
            "cost_model_estimate_present",
            "Cost-model estimate present",
            passed=not cost_model,
            warning=cost_model,
        )
    )
    if manual_price:
        internal_review_flags.append("manual_pricing")
        warning_items.append("manual_pricing")
    if cost_model:
        internal_review_flags.append("cost_model_estimate")
        warning_items.append("cost_model_estimate")
    if requires_review:
        internal_review_flags.append("requires_review")
        warning_items.append("line_requires_review")

    high_discount = False
    for adj in quote.adjustments:
        if adj.type == "discount" and adj.percentage and Decimal(str(adj.percentage)) >= HIGH_DISCOUNT_THRESHOLD:
            high_discount = True
        elif adj.type == "discount" and quote.subtotal > 0:
            pct = (Decimal(str(adj.amount)) / Decimal(str(quote.subtotal))) * Decimal("100")
            if pct >= HIGH_DISCOUNT_THRESHOLD:
                high_discount = True
    checklist.append(
        _check_item(
            "high_discount_present",
            "High discount present",
            passed=not high_discount,
            warning=high_discount,
        )
    )
    if high_discount:
        internal_review_flags.append("high_discount")
        warning_items.append("high_discount")

    checklist.append(
        _check_item(
            "supplier_confirmation_needed",
            "Supplier confirmation needed",
            passed=False,
            warning=True,
            details="Subject to supplier confirmation where applicable",
        )
    )
    checklist.append(
        _check_item(
            "logistics_confirmation_needed",
            "Logistics confirmation needed",
            passed=False,
            warning=True,
            details="Logistics subject to confirmation",
        )
    )
    warning_items.append("supplier_confirmation_needed")
    warning_items.append("logistics_confirmation_needed")

    checklist.append(_check_item("order_created", "No order record (expected)", passed=True, details="future order stage only"))
    checklist.append(_check_item("production_started", "No production record (expected)", passed=True, details="future production stage only"))
    checklist.append(_check_item("shipment_created", "No shipment record (expected)", passed=True, details="future shipment stage only"))

    status = _resolve_status(quote=quote, blocking=blocking_items, internal_review=internal_review_flags)

    pass_count = sum(1 for c in checklist if c["status"] == "pass")
    score = int(round((pass_count / len(checklist)) * 100)) if checklist else 0

    version_id = latest_version.id if latest_version else None
    pdf_id = latest_pdf.id if latest_pdf else None
    delivery_id = latest_delivery.id if latest_delivery else None

    order_input_contract = _build_order_input_contract(
        db,
        quote,
        partners=partners,
        version_id=version_id,
        pdf_export_id=pdf_id,
        delivery_log_id=delivery_id,
    )

    return {
        "quote_id": str(quote.id),
        "quote_number": quote.quote_number,
        "readiness_status": status,
        "readiness_score": score,
        "blocking_items": blocking_items,
        "warning_items": warning_items,
        "checklist": checklist,
        "order_input_contract": order_input_contract,
        "recommended_next_action": _recommended_action(status, blocking_items, warning_items),
        "safety": dict(READINESS_SAFETY),
    }


def build_order_readiness_board(db: Session, *, limit: int = 50) -> list[dict[str, Any]]:
    quotes = (
        db.query(Quote)
        .filter(
            Quote.is_archived.is_(False),
            Quote.status.in_(("sent", "ready_to_send", "expired", "revised")),
        )
        .order_by(Quote.updated_at.desc())
        .limit(limit)
        .all()
    )
    summaries = []
    for q in quotes:
        try:
            readiness = build_quote_order_readiness(db, q.id)
            summaries.append(
                {
                    "quote_id": readiness["quote_id"],
                    "quote_number": readiness["quote_number"],
                    "quote_status": q.status,
                    "readiness_status": readiness["readiness_status"],
                    "readiness_score": readiness["readiness_score"],
                    "blocking_count": len(readiness["blocking_items"]),
                    "warning_count": len(readiness["warning_items"]),
                }
            )
        except Exception:
            continue
    return summaries
