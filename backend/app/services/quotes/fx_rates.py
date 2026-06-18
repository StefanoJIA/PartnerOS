"""FX rate service for quote pricing.

USD/CNY used by quote cost models must come from a current online source, not
from historical Excel workbook snapshots. The database stores the fetched daily
rate so quote calculations remain reproducible for that day.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.models import FxRate

ONLINE_FX_SOURCE = "frankfurter.app"
ONLINE_FX_URL = "https://api.frankfurter.dev/v1/latest"


def get_latest_fx(db: Session, *, base: str, quote: str, rate_date: date | None) -> FxRate | None:
    base = base.upper()
    quote = quote.upper()
    q = db.query(FxRate).filter(FxRate.base_currency == base, FxRate.quote_currency == quote)
    if rate_date:
        row = q.filter(FxRate.rate_date <= rate_date).order_by(FxRate.rate_date.desc()).first()
        if row:
            return row
    return q.order_by(FxRate.rate_date.desc()).first()


def fetch_online_fx_rate(*, base: str = "USD", quote: str = "CNY", timeout: float = 8.0) -> tuple[Decimal, date, str]:
    """Fetch the latest public FX rate.

    Frankfurter is a no-key public ECB reference-rate API. If it is unavailable,
    callers should fall back to the latest stored DB row and mark it stale.
    """

    base = base.upper()
    quote = quote.upper()
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(ONLINE_FX_URL, params={"from": base, "to": quote})
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
    rates = payload.get("rates") or {}
    raw_rate = rates.get(quote)
    raw_date = payload.get("date")
    if raw_rate is None or not raw_date:
        raise ValueError("ONLINE_FX_PAYLOAD_MISSING_RATE")
    return Decimal(str(raw_rate)), date.fromisoformat(str(raw_date)), ONLINE_FX_SOURCE


def upsert_fx_rate(
    db: Session,
    *,
    base: str,
    quote: str,
    rate: Decimal,
    rate_date: date,
    source: str,
    is_manual_override: bool = False,
) -> FxRate:
    base = base.upper()
    quote = quote.upper()
    row = (
        db.query(FxRate)
        .filter(FxRate.base_currency == base, FxRate.quote_currency == quote, FxRate.rate_date == rate_date)
        .first()
    )
    if row:
        row.rate = rate
        row.source = source
        row.is_manual_override = is_manual_override
    else:
        row = FxRate(
            base_currency=base,
            quote_currency=quote,
            rate=rate,
            rate_date=rate_date,
            source=source,
            is_manual_override=is_manual_override,
            created_at=datetime.now(timezone.utc),
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def ensure_latest_fx_rate(
    db: Session,
    *,
    base: str = "USD",
    quote: str = "CNY",
    rate_date: date | None = None,
    refresh_online: bool = True,
) -> FxRate | None:
    """Return a current FX row, fetching online for today's USD/CNY if needed.

    Historical quote previews can still ask for a prior rate_date. Current quote
    and product pricing paths refresh today's online USD/CNY first, then fall
    back to the latest stored row if the network source is unavailable.
    """

    ref = rate_date or date.today()
    base = base.upper()
    quote = quote.upper()
    if refresh_online and ref >= date.today() and base == "USD" and quote == "CNY":
        try:
            rate, online_date, source = fetch_online_fx_rate(base=base, quote=quote)
            return upsert_fx_rate(
                db,
                base=base,
                quote=quote,
                rate=rate,
                rate_date=online_date,
                source=source,
                is_manual_override=False,
            )
        except Exception:
            return get_latest_fx(db, base=base, quote=quote, rate_date=ref)
    return get_latest_fx(db, base=base, quote=quote, rate_date=ref)
