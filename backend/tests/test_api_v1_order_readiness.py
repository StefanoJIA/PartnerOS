"""API tests for D6.6 order readiness."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import create_app
from app.models import User


@pytest.fixture
def readiness_client(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="r@test.example", is_active=True)
    quote_id = uuid4()
    payload = {
        "quote_id": str(quote_id),
        "quote_number": "Q-2026-0001",
        "readiness_status": "needs_customer_confirmation",
        "readiness_score": 85,
        "blocking_items": [],
        "warning_items": ["supplier_confirmation_needed"],
        "checklist": [],
        "order_input_contract": {"source_quote": {"quote_id": str(quote_id)}},
        "recommended_next_action": "Obtain customer confirmation",
        "safety": {
            "order_created": False,
            "production_started": False,
            "shipment_created": False,
            "automatic_sending_enabled": False,
        },
    }

    monkeypatch.setattr(
        "app.api.v1.routes.quote_order_readiness.build_quote_order_readiness",
        lambda db, qid: payload,
    )
    monkeypatch.setattr(
        "app.api.v1.routes.quote_order_readiness.build_order_readiness_board",
        lambda db, limit=50: [payload],
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    yield client, quote_id
    app.dependency_overrides.clear()


def test_order_readiness_route(readiness_client):
    client, quote_id = readiness_client
    r = client.get(f"/api/v1/quotes/{quote_id}/order-readiness")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["readiness_status"] == "needs_customer_confirmation"
    assert data["safety"]["order_created"] is False


def test_order_readiness_board(readiness_client):
    client, _ = readiness_client
    r = client.get("/api/v1/quotes/order-readiness-board")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 1
