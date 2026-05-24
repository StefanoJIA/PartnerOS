"""API tests for D6.5 quote delivery."""

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
def delivery_client(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="d@test.example", is_active=True)
    quote_id = uuid4()
    log_id = uuid4()

    db = MagicMock()

    monkeypatch.setattr(
        "app.api.v1.routes.quotes.mark_sent_with_delivery",
        lambda db, qid, user, **kw: {
            "quote_id": str(quote_id),
            "status": "sent",
            "delivery_log": {
                "id": str(log_id),
                "quote_id": str(quote_id),
                "sent_channel": "email",
                "manual_sent": True,
            },
            "warnings": [],
            "safety": {
                "automatic_sending_enabled": False,
                "email_sent_by_system": False,
                "linkedin_sent_by_system": False,
                "attachment_sent_by_system": False,
                "order_created": False,
            },
        },
    )
    monkeypatch.setattr(
        "app.api.v1.routes.quote_delivery.list_delivery_logs",
        lambda db, qid: [{"id": str(log_id), "sent_channel": "email"}],
    )
    monkeypatch.setattr(
        "app.api.v1.routes.quote_delivery.build_quote_timeline",
        lambda db, qid: {"items": [{"type": "manual_sent", "title": "Quote manually sent"}], "total": 1},
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    yield client, quote_id, log_id
    app.dependency_overrides.clear()


def test_mark_sent_returns_delivery_log(delivery_client):
    client, quote_id, log_id = delivery_client
    r = client.post(
        f"/api/v1/quotes/{quote_id}/mark-sent",
        json={"sent_channel": "email", "sent_to_name": "Bob"},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "sent"
    assert data["delivery_log"]["id"] == str(log_id)
    assert data["safety"]["email_sent_by_system"] is False


def test_delivery_logs_list(delivery_client):
    client, quote_id, _ = delivery_client
    r = client.get(f"/api/v1/quotes/{quote_id}/delivery-logs")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 1


def test_timeline(delivery_client):
    client, quote_id, _ = delivery_client
    r = client.get(f"/api/v1/quotes/{quote_id}/timeline")
    assert r.status_code == 200
    assert any(i["type"] == "manual_sent" for i in r.json()["data"]["items"])
