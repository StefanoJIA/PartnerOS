"""Customer Order CRUD service (D7.2)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.core.errors import CONFLICT, NOT_FOUND, VALIDATION_ERROR, ApiError
from app.models import User
from app.models.customer_orders import (
    CUSTOMER_CONFIRMATION_TYPES,
    CustomerOrder,
    OrderConfirmation,
    OrderLineItem,
    STRENGTH_BY_TYPE,
)
from app.models.customer_quotes import Quote, QuoteLineItem
from app.services.quotes.order_readiness import build_quote_order_readiness
from app.services.quotes.quote_service import derived_expired, get_quote

ORDER_SAFETY: dict[str, bool] = {
    "order_created": True,
    "order_confirmed": False,
    "customer_confirmation_recorded": False,
    "supplier_confirmation_recorded": False,
    "production_started": False,
    "shipment_created": False,
    "supplier_notified": False,
    "automatic_sending_enabled": False,
    "inventory_promised": False,
    "certification_promised": False,
    "lead_time_promised": False,
    "payment_received": False,
}

ORDER_SAFETY_RESPONSE: dict[str, bool] = dict(ORDER_SAFETY)

FORBIDDEN_PHRASES = (
    "production started",
    "shipment created",
    "shipment booked",
    "supplier notified automatically",
    "inventory confirmed",
    "certification confirmed",
    "lead time confirmed",
    "delivery guaranteed",
    "payment received",
)

ACTIVE_ORDER_STATUSES = ("pending_customer_confirmation", "confirmed")


def assert_no_forbidden_phrases(text: str) -> None:
    lower = (text or "").lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            raise ApiError(VALIDATION_ERROR, f"forbidden phrase in order content: {phrase}", status_code=400)


def generate_order_number(db: Session, order_date: date) -> str:
    prefix = f"O-{order_date.year}-"
    last = (
        db.query(CustomerOrder)
        .filter(CustomerOrder.order_number.like(f"{prefix}%"))
        .order_by(CustomerOrder.order_number.desc())
        .with_for_update()
        .first()
    )
    seq = 1
    if last:
        try:
            seq = int(last.order_number.split("-")[-1]) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:04d}"


def get_active_order_for_quote(db: Session, quote_id: UUID) -> CustomerOrder | None:
    return (
        db.query(CustomerOrder)
        .filter(
            CustomerOrder.source_quote_id == quote_id,
            CustomerOrder.status.in_(ACTIVE_ORDER_STATUSES),
        )
        .first()
    )


def get_order(db: Session, order_id: UUID) -> CustomerOrder:
    order = (
        db.query(CustomerOrder)
        .options(joinedload(CustomerOrder.line_items))
        .filter(CustomerOrder.id == order_id)
        .first()
    )
    if not order:
        raise ApiError(NOT_FOUND, "Order not found", status_code=404)
    return order


def _serialize_line(line: OrderLineItem) -> dict[str, Any]:
    return {
        "id": str(line.id),
        "source_quote_line_item_id": str(line.source_quote_line_item_id),
        "partner_id": str(line.partner_id),
        "product_catalog_id": str(line.product_catalog_id) if line.product_catalog_id else None,
        "internal_sku": line.internal_sku,
        "partner_product_code": line.partner_product_code,
        "product_name": line.product_name,
        "product_category": line.product_category,
        "description_customer": line.description_customer,
        "description_internal": line.description_internal,
        "quantity": line.quantity,
        "uom": line.uom,
        "unit_price": str(line.unit_price),
        "total_price": str(line.total_price),
        "currency": line.currency,
        "incoterm": line.incoterm,
        "color_finish": line.color_finish,
        "size_dimension": line.size_dimension,
        "attributes_snapshot_json": line.attributes_snapshot_json,
        "customer_visible": line.customer_visible,
        "supplier_visible": line.supplier_visible,
        "status": line.status,
        "notes": line.notes,
    }


def order_list_item(order: CustomerOrder) -> dict[str, Any]:
    return {
        "id": str(order.id),
        "order_number": order.order_number,
        "source_quote_id": str(order.source_quote_id),
        "company_id": str(order.company_id) if order.company_id else None,
        "status": order.status,
        "order_date": str(order.order_date),
        "currency": order.currency,
        "grand_total": str(order.grand_total),
        "bill_to_company": order.bill_to_company,
        "customer_confirmed_at": order.customer_confirmed_at.isoformat() if order.customer_confirmed_at else None,
        "safety": ORDER_SAFETY_RESPONSE,
    }


def order_to_dict(order: CustomerOrder, *, include_lines: bool = True) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": str(order.id),
        "order_number": order.order_number,
        "source_quote_id": str(order.source_quote_id),
        "source_quote_version_id": str(order.source_quote_version_id) if order.source_quote_version_id else None,
        "source_pdf_export_id": str(order.source_pdf_export_id) if order.source_pdf_export_id else None,
        "source_delivery_log_id": str(order.source_delivery_log_id) if order.source_delivery_log_id else None,
        "company_id": str(order.company_id) if order.company_id else None,
        "contact_id": str(order.contact_id) if order.contact_id else None,
        "status": order.status,
        "order_date": str(order.order_date),
        "customer_confirmed_at": order.customer_confirmed_at.isoformat() if order.customer_confirmed_at else None,
        "customer_confirmation_method": order.customer_confirmation_method,
        "customer_confirmation_note": order.customer_confirmation_note,
        "bill_to_name": order.bill_to_name,
        "bill_to_company": order.bill_to_company,
        "bill_to_address": order.bill_to_address,
        "ship_to_name": order.ship_to_name,
        "ship_to_company": order.ship_to_company,
        "ship_to_address": order.ship_to_address,
        "currency": order.currency,
        "subtotal": str(order.subtotal),
        "adjustment_total": str(order.adjustment_total),
        "tax_total": str(order.tax_total),
        "grand_total": str(order.grand_total),
        "payment_terms": order.payment_terms,
        "shipping_terms": order.shipping_terms,
        "internal_notes": order.internal_notes,
        "customer_notes": order.customer_notes,
        "cancelled_at": order.cancelled_at.isoformat() if order.cancelled_at else None,
        "cancelled_reason": order.cancelled_reason,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        "safety": ORDER_SAFETY_RESPONSE,
    }
    if include_lines:
        data["line_items"] = [_serialize_line(li) for li in sorted(order.line_items, key=lambda x: x.created_at)]
    return data


def _source_quote_summary(db: Session, quote_id: UUID) -> dict[str, Any]:
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        return {"quote_id": str(quote_id)}
    return {
        "quote_id": str(quote.id),
        "quote_number": quote.quote_number,
        "status": quote.status,
        "valid_until": str(quote.valid_until),
    }


def _resolve_addresses(
    quote: Quote,
    bill_to: dict[str, str] | None,
    ship_to: dict[str, str] | None,
) -> tuple[dict[str, str | None], dict[str, str | None]]:
    bt = {
        "name": (bill_to or {}).get("name") or quote.bill_to_name,
        "company": (bill_to or {}).get("company") or quote.bill_to_company,
        "address": (bill_to or {}).get("address") or quote.bill_to_address,
    }
    st = {
        "name": (ship_to or {}).get("name") or quote.ship_to_name,
        "company": (ship_to or {}).get("company") or quote.ship_to_company,
        "address": (ship_to or {}).get("address") or quote.ship_to_address,
    }
    return bt, st


def _select_quote_lines(
    quote: Quote,
    selected_ids: list[UUID] | None,
) -> list[QuoteLineItem]:
    visible = [li for li in quote.line_items if li.customer_visible]
    if not selected_ids:
        return visible
    id_set = {str(x) for x in selected_ids}
    selected = [li for li in quote.line_items if str(li.id) in id_set]
    if len(selected) != len(selected_ids):
        raise ApiError(VALIDATION_ERROR, "One or more selected line items do not belong to this quote", status_code=400)
    return selected


def _compute_totals(quote: Quote, selected_lines: list[QuoteLineItem]) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    line_subtotal = sum((li.total_price for li in selected_lines), Decimal("0"))
    all_visible = [li for li in quote.line_items if li.customer_visible]
    if len(selected_lines) == len(all_visible) and len(all_visible) > 0:
        return quote.subtotal, quote.adjustment_total, quote.tax_total, quote.grand_total
    return line_subtotal, Decimal("0"), Decimal("0"), line_subtotal


def create_order_from_quote(
    db: Session,
    user: User,
    *,
    quote_id: UUID,
    quote_version_id: UUID | None = None,
    pdf_export_id: UUID | None = None,
    delivery_log_id: UUID | None = None,
    customer_confirmation: dict[str, Any] | None = None,
    selected_line_item_ids: list[UUID] | None = None,
    bill_to: dict[str, str] | None = None,
    ship_to: dict[str, str] | None = None,
    internal_notes: str | None = None,
    customer_notes: str | None = None,
) -> CustomerOrder:
    quote = (
        db.query(Quote)
        .options(joinedload(Quote.line_items))
        .filter(Quote.id == quote_id, Quote.is_archived.is_(False))
        .first()
    )
    if not quote:
        get_quote(db, quote_id)

    if quote.status != "sent":
        raise ApiError(VALIDATION_ERROR, "Quote must be sent before creating an order", status_code=400)
    if derived_expired(quote) or quote.status == "expired":
        raise ApiError(VALIDATION_ERROR, "Expired quote cannot be converted to order", status_code=400)
    if not quote.line_items:
        raise ApiError(VALIDATION_ERROR, "Quote has no line items", status_code=400)
    if quote.grand_total <= 0:
        raise ApiError(VALIDATION_ERROR, "Quote grand total must be positive", status_code=400)

    existing = get_active_order_for_quote(db, quote_id)
    if existing:
        raise ApiError(
            CONFLICT,
            f"Active order already exists for this quote: {existing.order_number}",
            status_code=409,
            details={"order_id": str(existing.id), "order_number": existing.order_number},
        )

    readiness = build_quote_order_readiness(db, quote_id)
    if readiness.get("blocking_items"):
        raise ApiError(
            VALIDATION_ERROR,
            "Quote is not ready for order creation",
            status_code=400,
            details={"blocking_items": readiness["blocking_items"]},
        )

    selected_lines = _select_quote_lines(quote, selected_line_item_ids)
    if not selected_lines:
        raise ApiError(VALIDATION_ERROR, "No line items selected for order", status_code=400)
    for li in selected_lines:
        if li.quantity <= 0 or li.final_unit_price <= 0 or li.total_price <= 0:
            raise ApiError(VALIDATION_ERROR, "All selected lines must have quantity and price", status_code=400)

    contract = readiness.get("order_input_contract") or {}
    source = contract.get("source_quote") or {}
    version_id = quote_version_id or (UUID(source["quote_version_id"]) if source.get("quote_version_id") else None)
    pdf_id = pdf_export_id or (UUID(source["pdf_export_id"]) if source.get("pdf_export_id") else None)
    delivery_id = delivery_log_id or (UUID(source["delivery_log_id"]) if source.get("delivery_log_id") else None)

    bt, st = _resolve_addresses(quote, bill_to, ship_to)
    subtotal, adjustment_total, tax_total, grand_total = _compute_totals(quote, selected_lines)

    now = datetime.now(timezone.utc)
    order_date = date.today()
    has_confirmation = bool(customer_confirmation and customer_confirmation.get("type"))
    if has_confirmation:
        ctype = customer_confirmation.get("type")
        if ctype not in CUSTOMER_CONFIRMATION_TYPES:
            raise ApiError(VALIDATION_ERROR, f"Invalid confirmation type: {ctype}", status_code=400)
        status = "confirmed"
        confirmed_at_raw = customer_confirmation.get("confirmed_at")
        if confirmed_at_raw:
            try:
                customer_confirmed_at = datetime.fromisoformat(str(confirmed_at_raw).replace("Z", "+00:00"))
            except ValueError:
                customer_confirmed_at = now
        else:
            customer_confirmed_at = now
        confirmation_method = ctype
        confirmation_note = customer_confirmation.get("note")
    else:
        status = "pending_customer_confirmation"
        customer_confirmed_at = None
        confirmation_method = None
        confirmation_note = None

    order = CustomerOrder(
        order_number=generate_order_number(db, order_date),
        source_quote_id=quote.id,
        source_quote_version_id=version_id,
        source_pdf_export_id=pdf_id,
        source_delivery_log_id=delivery_id,
        company_id=quote.company_id,
        contact_id=quote.contact_id,
        status=status,
        order_date=order_date,
        customer_confirmed_at=customer_confirmed_at,
        customer_confirmation_method=confirmation_method,
        customer_confirmation_note=confirmation_note,
        bill_to_name=bt["name"],
        bill_to_company=bt["company"],
        bill_to_address=bt["address"],
        ship_to_name=st["name"],
        ship_to_company=st["company"],
        ship_to_address=st["address"],
        currency=quote.currency,
        subtotal=subtotal,
        adjustment_total=adjustment_total,
        tax_total=tax_total,
        grand_total=grand_total,
        payment_terms=quote.payment_terms,
        shipping_terms=quote.shipping_terms,
        order_input_contract_json=contract,
        readiness_snapshot_json=readiness,
        internal_notes=internal_notes,
        customer_notes=customer_notes,
        created_by_id=user.id,
    )
    db.add(order)
    db.flush()

    line_status = "confirmed" if status == "confirmed" else "pending"
    for qli in selected_lines:
        oli = OrderLineItem(
            order_id=order.id,
            source_quote_line_item_id=qli.id,
            partner_id=qli.partner_id,
            product_catalog_id=qli.product_catalog_id,
            internal_sku=qli.internal_sku,
            partner_product_code=qli.partner_product_code,
            product_name=qli.product_name,
            product_category=qli.product_category,
            description_customer=qli.description_customer,
            description_internal=qli.description_internal,
            quantity=qli.quantity,
            uom=qli.uom,
            unit_price=qli.final_unit_price,
            total_price=qli.total_price,
            currency=qli.currency,
            incoterm=qli.incoterm or quote.default_incoterm,
            color_finish=qli.color_finish,
            size_dimension=qli.size_dimension,
            attributes_snapshot_json=qli.attributes_snapshot_json,
            customer_visible=qli.customer_visible,
            supplier_visible=True,
            status=line_status,
            notes=qli.notes,
        )
        db.add(oli)

    if has_confirmation:
        conf_row = OrderConfirmation(
            order_id=order.id,
            confirmation_type=confirmation_method,
            confirmation_strength=STRENGTH_BY_TYPE.get(confirmation_method or "other", "weak"),
            confirmed_at=customer_confirmed_at or datetime.now(timezone.utc),
            source_channel=confirmation_method,
            note=confirmation_note,
            status="active",
            created_by_id=user.id,
        )
        db.add(conf_row)

    db.commit()
    db.refresh(order)
    return order


def update_order(
    db: Session,
    order_id: UUID,
    *,
    bill_to_name: str | None = None,
    bill_to_company: str | None = None,
    bill_to_address: str | None = None,
    ship_to_name: str | None = None,
    ship_to_company: str | None = None,
    ship_to_address: str | None = None,
    internal_notes: str | None = None,
    customer_notes: str | None = None,
    payment_terms: str | None = None,
    shipping_terms: str | None = None,
) -> CustomerOrder:
    order = get_order(db, order_id)
    if order.status == "cancelled":
        raise ApiError(VALIDATION_ERROR, "Cancelled order cannot be updated", status_code=400)

    fields = {
        "bill_to_name": bill_to_name,
        "bill_to_company": bill_to_company,
        "bill_to_address": bill_to_address,
        "ship_to_name": ship_to_name,
        "ship_to_company": ship_to_company,
        "ship_to_address": ship_to_address,
        "internal_notes": internal_notes,
        "customer_notes": customer_notes,
        "payment_terms": payment_terms,
        "shipping_terms": shipping_terms,
    }
    for key, val in fields.items():
        if val is not None:
            setattr(order, key, val)

    db.commit()
    db.refresh(order)
    return order


def order_detail_payload(db: Session, order: CustomerOrder) -> dict[str, Any]:
    from app.services.orders.order_confirmation_service import confirmation_summary, confirmation_safety
    from app.services.orders.partner_split_service import partner_splits_summary, split_safety
    from app.services.orders.production_milestone_service import milestone_safety, production_summary
    from app.services.orders.shipment_plan_service import shipment_safety, shipment_summary
    from app.services.orders.supplier_confirmation_service import (
        supplier_confirmation_summary,
        supplier_confirmation_safety,
    )

    payload = order_to_dict(order)
    payload["source_quote"] = _source_quote_summary(db, order.source_quote_id)
    summary = confirmation_summary(db, order)
    payload["confirmation_summary"] = summary
    payload["partner_splits_summary"] = partner_splits_summary(db, order)
    payload["supplier_confirmation_summary"] = supplier_confirmation_summary(db, order.id)
    payload["production_summary"] = production_summary(db, order.id)
    payload["shipment_summary"] = shipment_summary(db, order.id)
    payload["warnings"] = list(summary.get("warnings") or [])
    has_active = summary.get("active_count", 0) > 0
    sc_summary = payload["supplier_confirmation_summary"]
    payload["safety"] = {
        **confirmation_safety(order_confirmed=has_active or order.status == "confirmed"),
        **split_safety(),
        **supplier_confirmation_safety(recorded=sc_summary.get("active_confirmations", 0) > 0),
        **milestone_safety(),
        **shipment_safety(),
    }
    return payload


def cancel_order(db: Session, order_id: UUID, *, reason: str | None = None) -> CustomerOrder:
    order = get_order(db, order_id)
    if order.status == "cancelled":
        raise ApiError(VALIDATION_ERROR, "Order is already cancelled", status_code=400)

    order.status = "cancelled"
    order.cancelled_at = datetime.now(timezone.utc)
    order.cancelled_reason = reason
    for li in order.line_items:
        if li.status != "cancelled":
            li.status = "cancelled"

    db.commit()
    db.refresh(order)
    return order
