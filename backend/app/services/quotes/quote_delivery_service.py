"""Quote delivery log and enhanced mark-sent (D6.5)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.errors import ApiError, NOT_FOUND, VALIDATION_ERROR
from app.models import User
from app.models.customer_quotes import Quote, QuoteDeliveryLog, QuotePdfExport, QuoteVersion
from app.services.quotes.quote_service import derived_expired, get_quote

DELIVERY_SAFETY: dict[str, bool] = {
    "automatic_sending_enabled": False,
    "email_sent_by_system": False,
    "linkedin_sent_by_system": False,
    "attachment_sent_by_system": False,
    "order_created": False,
    "inventory_promised": False,
    "certification_promised": False,
    "lead_time_promised": False,
}

SENT_CHANNELS = frozenset({"email", "linkedin", "in_person", "phone", "portal_manual", "other"})

FORBIDDEN_PHRASES = (
    "email sent automatically",
    "linkedin sent automatically",
    "attachment delivered by system",
    "guaranteed price",
    "in stock",
    "delivery guaranteed",
    "lead time confirmed",
)


def mask_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        masked_local = "*"
    else:
        masked_local = local[0] + "***"
    return f"{masked_local}@{domain}"


def delivery_log_to_dict(log: QuoteDeliveryLog, *, mask_email_field: bool = False) -> dict[str, Any]:
    email = log.sent_to_email
    if mask_email_field and email:
        email = mask_email(email)
    return {
        "id": str(log.id),
        "quote_id": str(log.quote_id),
        "quote_version_id": str(log.quote_version_id) if log.quote_version_id else None,
        "pdf_export_id": str(log.pdf_export_id) if log.pdf_export_id else None,
        "sent_channel": log.sent_channel,
        "sent_to_name": log.sent_to_name,
        "sent_to_email": email,
        "sent_to_company": log.sent_to_company,
        "sent_at": log.sent_at.isoformat() if log.sent_at else None,
        "sent_by_id": str(log.sent_by_id) if log.sent_by_id else None,
        "manual_sent": log.manual_sent,
        "follow_up_date": str(log.follow_up_date) if log.follow_up_date else None,
        "note": log.note,
        "status": log.status,
    }


def _validate_channel(channel: str) -> str:
    normalized = (channel or "other").strip().lower()
    legacy_map = {
        "manual_email": "email",
        "manual": "other",
        "email_manual": "email",
    }
    normalized = legacy_map.get(normalized, normalized)
    if normalized not in SENT_CHANNELS:
        raise ApiError(VALIDATION_ERROR, f"sent_channel must be one of {sorted(SENT_CHANNELS)}", status_code=400)
    return normalized


def _validate_version(db: Session, quote_id: UUID, version_id: UUID | None) -> QuoteVersion | None:
    if not version_id:
        return None
    version = (
        db.query(QuoteVersion)
        .filter(QuoteVersion.id == version_id, QuoteVersion.quote_id == quote_id)
        .first()
    )
    if not version:
        raise ApiError(VALIDATION_ERROR, "quote_version_id does not belong to this quote", status_code=400)
    return version


def _validate_pdf_export(db: Session, quote_id: UUID, export_id: UUID | None) -> QuotePdfExport | None:
    if not export_id:
        return None
    export = (
        db.query(QuotePdfExport)
        .filter(QuotePdfExport.id == export_id, QuotePdfExport.quote_id == quote_id)
        .first()
    )
    if not export:
        raise ApiError(VALIDATION_ERROR, "pdf_export_id does not belong to this quote", status_code=400)
    return export


def _parse_sent_at(value: datetime | str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ApiError(VALIDATION_ERROR, "invalid sent_at datetime", status_code=400) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def mark_sent_with_delivery(
    db: Session,
    quote_id: UUID,
    *,
    user: User,
    sent_channel: str | None = None,
    send_channel: str | None = None,
    quote_version_id: UUID | None = None,
    pdf_export_id: UUID | None = None,
    sent_to_name: str | None = None,
    sent_to_email: str | None = None,
    sent_to_company: str | None = None,
    sent_at: datetime | str | None = None,
    follow_up_date: date | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    quote = get_quote(db, quote_id)
    warnings: list[str] = []

    if quote.status == "converted_to_order":
        raise ApiError(VALIDATION_ERROR, "converted quote cannot be marked sent", status_code=400)
    if quote.status == "internal_review":
        raise ApiError(VALIDATION_ERROR, "internal_review quote cannot be marked sent", status_code=400)
    if derived_expired(quote) or quote.status == "expired":
        raise ApiError(VALIDATION_ERROR, "expired quote cannot be marked sent", status_code=400)

    already_sent = quote.status == "sent"
    if not already_sent and quote.status != "ready_to_send":
        raise ApiError(
            VALIDATION_ERROR,
            f"quote must be ready_to_send before mark-sent (current: {quote.status})",
            status_code=400,
        )

    channel = _validate_channel(sent_channel or send_channel or "other")
    _validate_version(db, quote_id, quote_version_id)
    _validate_pdf_export(db, quote_id, pdf_export_id)

    if note:
        lower = note.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in lower:
                raise ApiError(VALIDATION_ERROR, f"forbidden phrase in note: {phrase}", status_code=400)

    sent_dt = _parse_sent_at(sent_at)
    log = QuoteDeliveryLog(
        id=uuid4(),
        quote_id=quote_id,
        quote_version_id=quote_version_id,
        pdf_export_id=pdf_export_id,
        sent_channel=channel,
        sent_to_name=sent_to_name or quote.bill_to_name,
        sent_to_email=sent_to_email,
        sent_to_company=sent_to_company or quote.bill_to_company,
        sent_at=sent_dt,
        sent_by_id=user.id,
        manual_sent=True,
        follow_up_date=follow_up_date,
        note=note,
        status="recorded",
    )
    db.add(log)
    db.flush()

    if not already_sent:
        quote.status = "sent"
        quote.manual_sent = True
    else:
        warnings.append("quote already sent; delivery log appended")

    quote.sent_at = sent_dt
    quote.sent_by_id = user.id
    quote.send_channel = channel
    quote.last_delivery_log_id = log.id
    if follow_up_date is not None:
        quote.follow_up_date = follow_up_date
    quote.updated_by_id = user.id

    db.commit()
    db.refresh(quote)
    db.refresh(log)

    return {
        "quote_id": str(quote.id),
        "status": quote.status,
        "delivery_log": delivery_log_to_dict(log),
        "follow_up_date": str(quote.follow_up_date) if quote.follow_up_date else None,
        "warnings": warnings,
        "safety": dict(DELIVERY_SAFETY),
    }


def list_delivery_logs(db: Session, quote_id: UUID) -> list[dict[str, Any]]:
    get_quote(db, quote_id)
    rows = (
        db.query(QuoteDeliveryLog)
        .filter(QuoteDeliveryLog.quote_id == quote_id, QuoteDeliveryLog.status == "recorded")
        .order_by(QuoteDeliveryLog.sent_at.desc())
        .all()
    )
    return [delivery_log_to_dict(r) for r in rows]


def list_delivery_due(db: Session, *, as_of: date | None = None) -> list[dict[str, Any]]:
    ref = as_of or date.today()
    quotes = (
        db.query(Quote)
        .filter(
            Quote.is_archived.is_(False),
            Quote.status == "sent",
            Quote.follow_up_date.isnot(None),
            Quote.follow_up_date <= ref,
        )
        .order_by(Quote.follow_up_date.asc())
        .all()
    )
    return [
        {
            "quote_id": str(q.id),
            "quote_number": q.quote_number,
            "follow_up_date": str(q.follow_up_date),
            "bill_to_company": q.bill_to_company,
            "sent_at": q.sent_at.isoformat() if q.sent_at else None,
        }
        for q in quotes
    ]
