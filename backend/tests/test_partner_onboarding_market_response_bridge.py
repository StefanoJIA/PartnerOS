"""Tests for Partner Onboarding to Market Response review bridge."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import create_app
from app.models import User


def test_partner_onboarding_market_response_review_route(monkeypatch):
    partner_id = uuid4()
    app = create_app()
    user = User(id=uuid4(), email="onboarding-market@test.example", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield object())

    def fake_create(db, requested_partner_id, actor):
        assert requested_partner_id == partner_id
        assert actor.email == user.email
        return {
            "found": True,
            "partner_id": str(partner_id),
            "partner_name": "Future Partner",
            "created": [str(uuid4())],
            "existing": [],
            "market_response_link": "/market-response?partner_focus=Future%20Partner",
            "safety": {
                "staging_validated": False,
                "proof_record_created": False,
                "d9_entered": False,
                "customer_notified": False,
                "supplier_notified": False,
                "quote_status_changed": False,
                "order_status_changed": False,
            },
        }

    monkeypatch.setattr(
        "app.api.v1.routes.partner_onboarding.create_partner_market_response_reviews",
        fake_create,
    )

    with TestClient(app) as client:
        response = client.post(f"/api/v1/partner-onboarding/{partner_id}/market-response-reviews")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["created"]
    assert payload["market_response_link"].startswith("/market-response")
    assert payload["safety"]["customer_notified"] is False
    assert payload["safety"]["order_status_changed"] is False


def test_partner_onboarding_market_response_review_route_404(monkeypatch):
    partner_id = uuid4()
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User(
        id=uuid4(),
        email="onboarding-market-404@test.example",
        is_active=True,
    )
    app.dependency_overrides[get_db] = lambda: (yield object())
    monkeypatch.setattr(
        "app.api.v1.routes.partner_onboarding.create_partner_market_response_reviews",
        lambda db, requested_partner_id, actor: {"found": False, "created": [], "existing": [], "safety": {}},
    )

    with TestClient(app) as client:
        response = client.post(f"/api/v1/partner-onboarding/{partner_id}/market-response-reviews")

    assert response.status_code == 404
