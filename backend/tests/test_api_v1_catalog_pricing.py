"""API tests for v1 pricing preview (D6.2)."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import create_app
from app.models import User


def test_pricing_preview_envelope(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="p@test.example", is_active=True)
    product_id = uuid4()
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield MagicMock())
    monkeypatch.setattr(
        "app.api.v1.routes.pricing.calculate_line_price",
        lambda db, **kw: {
            "product_id": str(product_id),
            "quantity": 50,
            "incoterm": "FOB",
            "pricing_strategy": "volume",
            "currency": "USD",
            "source": "price_tier",
            "warnings": [],
            "safety": {
                "quote_created": False,
                "automatic_sending_enabled": False,
                "inventory_promised": False,
                "certification_promised": False,
                "lead_time_promised": False,
            },
        },
    )
    with TestClient(app) as c:
        r = c.post(
            "/api/v1/quotes/pricing/preview",
            json={"product_id": str(product_id), "quantity": 50, "incoterm": "FOB", "pricing_strategy": "volume"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["safety"]["quote_created"] is False
    app.dependency_overrides.clear()
