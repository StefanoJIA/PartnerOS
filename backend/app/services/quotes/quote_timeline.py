"""Quote timeline builder (D6.5)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models import User
from app.models.customer_quotes import Quote, QuoteDeliveryLog, QuotePdfExport, QuoteVersion
from app.services.quotes.quote_delivery_service import delivery_log_to_dict, mask_email
from app.services.quotes.quote_service import get_quote


def _actor_name(user: User | None) -> str:
    if not user:
        return ""
    return user.email or str(user.id)


def build_quote_timeline(db: Session, quote_id: UUID) -> dict[str, Any]:
    quote = (
        db.query(Quote)
        .options(
            joinedload(Quote.versions),
            joinedload(Quote.pdf_exports),
            joinedload(Quote.delivery_logs),
        )
        .filter(Quote.id == quote_id, Quote.is_archived.is_(False))
        .first()
    )
    if not quote:
        get_quote(db, quote_id)

    items: list[dict[str, Any]] = []

    if quote.created_at:
        items.append(
            {
                "type": "quote_created",
                "title": "Quote created",
                "timestamp": quote.created_at.isoformat(),
                "actor": "",
                "meta": {"quote_number": quote.quote_number},
            }
        )

    for version in sorted(quote.versions, key=lambda v: v.version_number):
        actor = ""
        if version.created_by_id:
            user = db.query(User).filter(User.id == version.created_by_id).first()
            actor = _actor_name(user)
        items.append(
            {
                "type": "version_created",
                "title": f"Version {version.version_label or version.version_number} created",
                "timestamp": version.created_at.isoformat() if version.created_at else None,
                "actor": actor,
                "meta": {
                    "version_number": version.version_number,
                    "version_type": version.version_type,
                },
            }
        )

    for export in sorted(
        (e for e in quote.pdf_exports if e.status == "generated"),
        key=lambda e: e.exported_at or e.created_at,
    ):
        actor = ""
        if export.exported_by_id:
            user = db.query(User).filter(User.id == export.exported_by_id).first()
            actor = _actor_name(user)
        items.append(
            {
                "type": "pdf_exported",
                "title": "Customer PDF exported",
                "timestamp": (export.exported_at or export.created_at).isoformat(),
                "actor": actor,
                "meta": {
                    "export_id": str(export.id),
                    "file_name": export.file_name,
                },
            }
        )

    for log in sorted(
        (l for l in quote.delivery_logs if l.status == "recorded"),
        key=lambda l: l.sent_at,
    ):
        actor = ""
        if log.sent_by_id:
            user = db.query(User).filter(User.id == log.sent_by_id).first()
            actor = _actor_name(user)
        log_dict = delivery_log_to_dict(log, mask_email_field=True)
        items.append(
            {
                "type": "manual_sent",
                "title": "Quote manually sent",
                "timestamp": log.sent_at.isoformat(),
                "actor": actor,
                "channel": log.sent_channel,
                "meta": {
                    "delivery_log_id": str(log.id),
                    "sent_to_name": log.sent_to_name,
                    "sent_to_email": log_dict.get("sent_to_email"),
                    "sent_to_company": log.sent_to_company,
                    "sent_channel": log.sent_channel,
                },
            }
        )

    if quote.follow_up_date:
        items.append(
            {
                "type": "follow_up_scheduled",
                "title": "Follow-up date set",
                "timestamp": quote.sent_at.isoformat() if quote.sent_at else quote.updated_at.isoformat(),
                "actor": "",
                "meta": {"follow_up_date": str(quote.follow_up_date)},
            }
        )

    items.sort(key=lambda x: x.get("timestamp") or "")

    return {"items": items, "total": len(items)}
