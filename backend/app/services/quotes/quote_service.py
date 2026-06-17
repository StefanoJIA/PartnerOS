"""Customer Quote CRUD service (D6.3)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session, joinedload, object_session

from app.core.errors import ApiError, NOT_FOUND, VALIDATION_ERROR
from app.models import ProductCatalog, User
from app.models.customer_quotes import (
    QUOTE_STATUSES,
    Quote,
    QuoteAdjustment,
    QuoteLineItem,
    QuoteTerms,
    QuoteVersion,
)
from app.services.a_domain.quote_input_contract_board import build_quote_input_contract_for_lead
from app.services.quotes.pricing_service import PRICING_SAFETY, calculate_line_price
from app.services.quotes.quote_totals import DEFAULT_SUBJECT, apply_totals_to_quote

QUOTE_SAFETY: dict[str, bool] = {
    "quote_created": True,
    "automatic_sending_enabled": False,
    "inventory_promised": False,
    "certification_promised": False,
    "lead_time_promised": False,
}

FORBIDDEN_PHRASES = (
    "guaranteed price",
    "in stock",
    "certified for",
    "delivery guaranteed",
    "lead time confirmed",
)

VALIDITY_DAYS = 21
REVIEW_SOURCES = {"manual_unit_price", "cost_model", "unknown"}


def assert_no_forbidden_phrases(text: str) -> None:
    lower = (text or "").lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            raise ApiError(VALIDATION_ERROR, f"forbidden phrase in quote content: {phrase}", status_code=400)


def generate_quote_number(db: Session, quote_date: date) -> str:
    prefix = f"Q-{quote_date.year}-"
    last = (
        db.query(Quote)
        .filter(Quote.quote_number.like(f"{prefix}%"))
        .order_by(Quote.quote_number.desc())
        .with_for_update()
        .first()
    )
    seq = 1
    if last:
        try:
            seq = int(last.quote_number.split("-")[-1]) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:04d}"


def derived_expired(quote: Quote, *, today: date | None = None) -> bool:
    ref = today or date.today()
    return quote.valid_until < ref and quote.status not in ("expired", "converted_to_order", "sent")


def resolve_initial_status(sources: list[str]) -> str:
    if any(s in REVIEW_SOURCES for s in sources):
        return "internal_review"
    return "ready_to_send"


def _serialize_line(line: QuoteLineItem, *, include_internal: bool = True) -> dict[str, Any]:
    data = {
        "id": str(line.id),
        "line_number": line.line_number,
        "partner_id": str(line.partner_id),
        "product_catalog_id": str(line.product_catalog_id) if line.product_catalog_id else None,
        "internal_sku": line.internal_sku,
        "partner_product_code": line.partner_product_code,
        "manual_product_name": line.manual_product_name,
        "product_name": line.product_name,
        "product_category": line.product_category,
        "quantity": line.quantity,
        "uom": line.uom,
        "unit_price": str(line.unit_price),
        "final_unit_price": str(line.final_unit_price),
        "total_price": str(line.total_price),
        "currency": line.currency,
        "incoterm": line.incoterm,
        "pricing_source": line.pricing_source,
        "pricing_strategy": line.pricing_strategy,
        "color_finish": line.color_finish,
        "size_dimension": line.size_dimension,
        "customer_visible": line.customer_visible,
        "requires_review": line.requires_review,
        "warnings": [],
    }
    if line.pricing_source == "manual_unit_price":
        data["warnings"].append("manual price requires review")
    if line.pricing_source == "cost_model":
        data["warnings"].append("estimated_from_cost_model")
    if include_internal:
        data["internal_cost"] = str(line.internal_cost) if line.internal_cost is not None else None
        data["estimated_margin"] = str(line.estimated_margin) if line.estimated_margin is not None else None
        data["pricing_breakdown_json"] = line.pricing_breakdown_json
    return data


def _serialize_adjustment(adj: QuoteAdjustment) -> dict[str, Any]:
    return {
        "id": str(adj.id),
        "type": adj.type,
        "label": adj.label,
        "amount": str(adj.amount),
        "percentage": str(adj.percentage) if adj.percentage is not None else None,
        "taxable": adj.taxable,
        "customer_visible": adj.customer_visible,
        "notes": adj.notes,
    }


def build_quote_snapshot(quote: Quote) -> dict[str, Any]:
    return {
        "quote_number": quote.quote_number,
        "status": quote.status,
        "quote_date": str(quote.quote_date),
        "valid_until": str(quote.valid_until),
        "currency": quote.currency,
        "bill_to": {
            "name": quote.bill_to_name,
            "company": quote.bill_to_company,
            "address": quote.bill_to_address,
        },
        "ship_to": {
            "name": quote.ship_to_name,
            "company": quote.ship_to_company,
            "address": quote.ship_to_address,
        },
        "line_items": [_serialize_line(li) for li in sorted(quote.line_items, key=lambda x: x.line_number)],
        "adjustments": [_serialize_adjustment(a) for a in quote.adjustments],
        "totals": {
            "subtotal": str(quote.subtotal),
            "adjustment_total": str(quote.adjustment_total),
            "tax_total": str(quote.tax_total),
            "grand_total": str(quote.grand_total),
        },
        "terms": {
            "payment_terms": quote.payment_terms,
            "shipping_terms": quote.shipping_terms,
        },
    }


def create_version_snapshot(
    db: Session,
    quote: Quote,
    *,
    user: User,
    version_type: str = "revised",
    version_label: str | None = None,
    notes: str | None = None,
    created_from_version_id: UUID | None = None,
) -> QuoteVersion:
    latest = (
        db.query(QuoteVersion)
        .filter(QuoteVersion.quote_id == quote.id)
        .order_by(QuoteVersion.version_number.desc())
        .first()
    )
    version_number = (latest.version_number + 1) if latest else 1
    version = QuoteVersion(
        quote_id=quote.id,
        version_number=version_number,
        version_label=version_label or f"v{version_number}",
        version_type=version_type,
        created_from_version_id=created_from_version_id,
        status=quote.status,
        snapshot_json=build_quote_snapshot(quote),
        created_by_id=user.id,
        created_at=datetime.now(timezone.utc),
        notes=notes,
    )
    db.add(version)
    db.flush()
    return version


def quote_list_item(quote: Quote) -> dict[str, Any]:
    return {
        "id": str(quote.id),
        "quote_number": quote.quote_number,
        "company_id": str(quote.company_id) if quote.company_id else None,
        "status": quote.status,
        "quote_date": str(quote.quote_date),
        "valid_until": str(quote.valid_until),
        "grand_total": str(quote.grand_total),
        "currency": quote.currency,
        "bill_to_company": quote.bill_to_company,
        "derived_expired": derived_expired(quote),
        "manual_sent": quote.manual_sent,
        "safety": dict(QUOTE_SAFETY),
    }


def quote_to_dict(quote: Quote, *, include_internal: bool = True) -> dict[str, Any]:
    from app.services.quotes.quote_learning import build_quote_commercial_intelligence, latest_quote_learning
    from app.services.quotes.quote_partner_readiness import build_quote_partner_readiness

    expired = derived_expired(quote)
    db = object_session(quote)
    commercial_intelligence = build_quote_commercial_intelligence(quote, db)
    if db is not None:
        from app.services.business_execution import build_product_partner_playbook_refs

        commercial_intelligence["product_partner_playbook_refs"] = build_product_partner_playbook_refs(
            db,
            partner_focus=str(commercial_intelligence.get("partner_focus") or ""),
            product_focus=[str(value) for value in commercial_intelligence.get("product_focus", []) or []],
            limit=3,
        )
    warnings: list[str] = []
    if expired:
        warnings.append("quote_validity_expired")
    for li in quote.line_items:
        if li.requires_review:
            warnings.append(f"line {li.line_number} requires review")
    return {
        "id": str(quote.id),
        "quote_number": quote.quote_number,
        "lead_id": str(quote.lead_id) if quote.lead_id else None,
        "company_id": str(quote.company_id) if quote.company_id else None,
        "contact_id": str(quote.contact_id) if quote.contact_id else None,
        "quote_date": str(quote.quote_date),
        "valid_until": str(quote.valid_until),
        "status": quote.status,
        "derived_expired": expired,
        "currency": quote.currency,
        "default_incoterm": quote.default_incoterm,
        "payment_terms": quote.payment_terms,
        "shipping_terms": quote.shipping_terms,
        "bill_to_name": quote.bill_to_name,
        "bill_to_company": quote.bill_to_company,
        "bill_to_address": quote.bill_to_address,
        "ship_to_name": quote.ship_to_name,
        "ship_to_company": quote.ship_to_company,
        "ship_to_address": quote.ship_to_address,
        "customer_notes": quote.customer_notes,
        "internal_notes": quote.internal_notes if include_internal else None,
        "subtotal": str(quote.subtotal),
        "adjustment_total": str(quote.adjustment_total),
        "tax_total": str(quote.tax_total),
        "grand_total": str(quote.grand_total),
        "manual_sent": quote.manual_sent,
        "sent_at": quote.sent_at.isoformat() if quote.sent_at else None,
        "send_channel": quote.send_channel,
        "follow_up_date": str(quote.follow_up_date) if quote.follow_up_date else None,
        "line_items": [_serialize_line(li, include_internal=include_internal) for li in sorted(quote.line_items, key=lambda x: x.line_number)],
        "adjustments": [_serialize_adjustment(a) for a in quote.adjustments],
        "versions_count": len(quote.versions),
        "latest_learning": latest_quote_learning(quote),
        "commercial_intelligence": commercial_intelligence,
        "partner_readiness": build_quote_partner_readiness(quote),
        "warnings": warnings,
        "safety": dict(QUOTE_SAFETY),
    }


def get_quote(db: Session, quote_id: UUID) -> Quote:
    quote = (
        db.query(Quote)
        .options(
            joinedload(Quote.line_items),
            joinedload(Quote.adjustments),
            joinedload(Quote.versions),
            joinedload(Quote.terms),
            joinedload(Quote.learning_records),
        )
        .filter(Quote.id == quote_id, Quote.is_archived.is_(False))
        .first()
    )
    if not quote:
        raise ApiError(NOT_FOUND, "quote not found", status_code=404)
    return quote


def _build_line_from_pricing(
    db: Session,
    *,
    quote: Quote,
    line_number: int,
    product: ProductCatalog | None,
    partner_id: UUID,
    quantity: int,
    incoterm: str,
    pricing_strategy: str,
    discount: dict | None,
    manual_unit_price: Decimal | None,
    manual_product_name: str | None,
    color_finish: str | None,
    size_dimension: str | None,
    user: User,
) -> QuoteLineItem:
    pricing_source = "manual_unit_price"
    pricing_breakdown: dict | None = None
    unit_price = manual_unit_price
    final_unit = manual_unit_price
    internal_cost = None
    estimated_margin = None
    requires_review = True
    warnings: list[str] = []

    if product and manual_unit_price is None:
        preview = calculate_line_price(
            db,
            product_id=product.id,
            quantity=quantity,
            incoterm=incoterm,
            pricing_strategy=pricing_strategy,
            discount=discount,
        )
        pricing_source = preview.get("source", "unknown")
        pricing_breakdown = preview
        pb = preview.get("price_breakdown") or {}
        unit_price = Decimal(pb.get("base_unit_price", "0"))
        final_unit = Decimal(pb.get("final_unit_price_after_discount", pb.get("final_unit_price", "0")))
        warnings = list(preview.get("warnings") or [])
        profit = preview.get("profit_breakdown") or {}
        if profit.get("estimated_margin"):
            try:
                estimated_margin = Decimal(str(profit["estimated_margin"]))
            except Exception:
                estimated_margin = None
        cost = preview.get("cost_breakdown") or {}
        if cost.get("fob_cost_usd"):
            try:
                internal_cost = Decimal(str(cost["fob_cost_usd"]))
            except Exception:
                internal_cost = None
        requires_review = pricing_source in REVIEW_SOURCES
    elif manual_unit_price is not None:
        warnings.append("manual price requires review")
        final_unit = manual_unit_price
        unit_price = manual_unit_price
    elif product is None:
        raise ApiError(VALIDATION_ERROR, "manual product requires manual_product_name and unit_price", status_code=400)
    else:
        raise ApiError(VALIDATION_ERROR, "line item must have pricing", status_code=400)

    if final_unit is None or final_unit <= 0:
        raise ApiError(VALIDATION_ERROR, "line item must have a positive price", status_code=400)

    total = (final_unit * quantity).quantize(Decimal("0.01"))
    name = product.product_name if product else manual_product_name or ""
    assert_no_forbidden_phrases(name)

    return QuoteLineItem(
        quote_id=quote.id,
        line_number=line_number,
        partner_id=partner_id,
        product_catalog_id=product.id if product else None,
        internal_sku=product.internal_sku if product else None,
        partner_product_code=product.partner_product_code if product else None,
        manual_product_name=manual_product_name if not product else None,
        product_name=name,
        product_category=product.product_category if product else "other",
        description_customer=product.description_customer if product else None,
        quantity=quantity,
        unit_price=unit_price or final_unit,
        final_unit_price=final_unit,
        total_price=total,
        incoterm=incoterm,
        pricing_source=pricing_source,
        pricing_strategy=pricing_strategy,
        color_finish=color_finish,
        size_dimension=size_dimension,
        attributes_snapshot_json=product.attributes_json if product else None,
        pricing_breakdown_json=pricing_breakdown,
        internal_cost=internal_cost,
        estimated_margin=estimated_margin,
        requires_review=requires_review,
        created_by_id=user.id,
        updated_by_id=user.id,
    )


def create_quote(
    db: Session,
    *,
    user: User,
    line_items_in: list[dict[str, Any]],
    lead_id: UUID | None = None,
    company_id: UUID | None = None,
    contact_id: UUID | None = None,
    bill_to: dict | None = None,
    ship_to: dict | None = None,
    payment_terms: str | None = None,
    shipping_terms: str | None = None,
    internal_notes: str | None = None,
    customer_notes: str | None = None,
    contract_snapshot: dict | None = None,
    default_incoterm: str | None = "FOB",
) -> Quote:
    if not line_items_in:
        raise ApiError(VALIDATION_ERROR, "quote requires at least one line item", status_code=400)

    quote_date = date.today()
    quote = Quote(
        quote_number=generate_quote_number(db, quote_date),
        lead_id=lead_id,
        company_id=company_id,
        contact_id=contact_id,
        sales_owner_id=user.id,
        quote_date=quote_date,
        valid_until=quote_date + timedelta(days=VALIDITY_DAYS),
        currency="USD",
        default_incoterm=default_incoterm,
        payment_terms=payment_terms or DEFAULT_SUBJECT,
        shipping_terms=shipping_terms or DEFAULT_SUBJECT,
        bill_to_name=(bill_to or {}).get("name"),
        bill_to_company=(bill_to or {}).get("company"),
        bill_to_address=(bill_to or {}).get("address"),
        ship_to_name=(ship_to or {}).get("name"),
        ship_to_company=(ship_to or {}).get("company"),
        ship_to_address=(ship_to or {}).get("address"),
        internal_notes=internal_notes,
        customer_notes=customer_notes,
        source_quote_input_contract_json=contract_snapshot,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(quote)
    db.flush()

    sources: list[str] = []
    for idx, item in enumerate(line_items_in, start=1):
        product = None
        product_id = item.get("product_id") or item.get("product_catalog_id")
        if product_id:
            product = db.query(ProductCatalog).filter(ProductCatalog.id == UUID(str(product_id))).first()
            if not product:
                raise ApiError(NOT_FOUND, f"product not found: {product_id}", status_code=404)
            partner_id = product.partner_id
        else:
            partner_id = UUID(str(item["partner_id"]))
            if not item.get("manual_product_name"):
                raise ApiError(VALIDATION_ERROR, "manual line requires manual_product_name", status_code=400)

        manual_price = item.get("manual_unit_price") or item.get("unit_price")
        line = _build_line_from_pricing(
            db,
            quote=quote,
            line_number=idx,
            product=product,
            partner_id=partner_id,
            quantity=int(item["quantity"]),
            incoterm=str(item.get("incoterm") or default_incoterm or "FOB"),
            pricing_strategy=str(item.get("pricing_strategy") or "volume"),
            discount=item.get("discount"),
            manual_unit_price=Decimal(str(manual_price)) if manual_price is not None else None,
            manual_product_name=item.get("manual_product_name"),
            color_finish=item.get("color_finish"),
            size_dimension=item.get("size_dimension"),
            user=user,
        )
        sources.append(line.pricing_source)
        db.add(line)

    quote.status = resolve_initial_status(sources)
    db.flush()
    db.refresh(quote)
    apply_totals_to_quote(quote)

    terms = QuoteTerms(
        quote_id=quote.id,
        payment_terms=quote.payment_terms,
        shipping_terms=quote.shipping_terms,
        validity_terms=f"Valid for {VALIDITY_DAYS} days from quote date.",
    )
    db.add(terms)
    create_version_snapshot(db, quote, user=user, version_type="internal_version", version_label="v1")
    db.commit()
    db.refresh(quote)
    return quote


def create_quote_from_contract(
    db: Session,
    *,
    user: User,
    lead_id: UUID,
    line_items_in: list[dict[str, Any]],
    **kwargs: Any,
) -> Quote:
    from app.models import Lead

    contract = build_quote_input_contract_for_lead(db, lead_id)
    if not contract:
        raise ApiError(VALIDATION_ERROR, "quote input contract not available for lead", status_code=400)
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    company_id = kwargs.pop("company_id", None) or (lead.company_id if lead else None)
    contact_id = kwargs.pop("contact_id", None) or (lead.primary_contact_id if lead else None)
    return create_quote(
        db,
        user=user,
        line_items_in=line_items_in,
        lead_id=lead_id,
        company_id=company_id,
        contact_id=contact_id,
        contract_snapshot=contract,
        **kwargs,
    )


def mark_ready(db: Session, quote_id: UUID, *, user: User) -> Quote:
    quote = get_quote(db, quote_id)
    if not quote.line_items:
        raise ApiError(VALIDATION_ERROR, "quote has no line items", status_code=400)
    if quote.status not in ("internal_review", "revised"):
        raise ApiError(VALIDATION_ERROR, f"cannot mark ready from status {quote.status}", status_code=400)
    if derived_expired(quote):
        raise ApiError(VALIDATION_ERROR, "quote is expired", status_code=400)
    for li in quote.line_items:
        if li.final_unit_price <= 0:
            raise ApiError(VALIDATION_ERROR, "all line items must be priced", status_code=400)
    quote.status = "ready_to_send"
    quote.updated_by_id = user.id
    db.commit()
    db.refresh(quote)
    return quote


def mark_sent(
    db: Session,
    quote_id: UUID,
    *,
    user: User,
    send_channel: str | None = None,
    **kwargs: Any,
) -> Quote:
    from app.services.quotes.quote_delivery_service import mark_sent_with_delivery

    mark_sent_with_delivery(db, quote_id, user=user, send_channel=send_channel, **kwargs)
    return get_quote(db, quote_id)


def mark_expired(db: Session, quote_id: UUID, *, user: User) -> Quote:
    quote = get_quote(db, quote_id)
    quote.status = "expired"
    quote.updated_by_id = user.id
    db.commit()
    db.refresh(quote)
    return quote


def add_line_item(db: Session, quote_id: UUID, *, user: User, item: dict[str, Any]) -> Quote:
    quote = get_quote(db, quote_id)
    if quote.status in ("sent", "expired", "converted_to_order"):
        raise ApiError(VALIDATION_ERROR, f"cannot edit quote in status {quote.status}", status_code=400)
    next_num = max((li.line_number for li in quote.line_items), default=0) + 1
    product = None
    product_id = item.get("product_id") or item.get("product_catalog_id")
    if product_id:
        product = db.query(ProductCatalog).filter(ProductCatalog.id == UUID(str(product_id))).first()
        partner_id = product.partner_id if product else UUID(str(item["partner_id"]))
    else:
        partner_id = UUID(str(item["partner_id"]))
    manual_price = item.get("manual_unit_price") or item.get("unit_price")
    line = _build_line_from_pricing(
        db,
        quote=quote,
        line_number=next_num,
        product=product,
        partner_id=partner_id,
        quantity=int(item["quantity"]),
        incoterm=str(item.get("incoterm") or quote.default_incoterm or "FOB"),
        pricing_strategy=str(item.get("pricing_strategy") or "volume"),
        discount=item.get("discount"),
        manual_unit_price=Decimal(str(manual_price)) if manual_price is not None else None,
        manual_product_name=item.get("manual_product_name"),
        color_finish=item.get("color_finish"),
        size_dimension=item.get("size_dimension"),
        user=user,
    )
    db.add(line)
    if quote.status == "sent":
        quote.status = "revised"
    apply_totals_to_quote(quote)
    quote.updated_by_id = user.id
    db.commit()
    db.refresh(quote)
    return quote


def recalculate_quote(db: Session, quote_id: UUID) -> Quote:
    quote = get_quote(db, quote_id)
    apply_totals_to_quote(quote)
    db.commit()
    db.refresh(quote)
    return quote
