from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.services.quotes import fx_rates


class _Response:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"amount": 1.0, "base": "USD", "date": "2026-06-18", "rates": {"CNY": 6.7716}}


class _Client:
    def __init__(self, *args, **kwargs) -> None:
        self.requests: list[tuple[str, dict]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def get(self, url: str, params: dict):
        self.requests.append((url, params))
        return _Response()


def test_fetch_online_fx_rate_parses_usd_cny(monkeypatch):
    monkeypatch.setattr(fx_rates.httpx, "Client", _Client)

    rate, rate_date, source = fx_rates.fetch_online_fx_rate(base="USD", quote="CNY")

    assert rate == Decimal("6.7716")
    assert rate_date == date(2026, 6, 18)
    assert source == "frankfurter.app"
