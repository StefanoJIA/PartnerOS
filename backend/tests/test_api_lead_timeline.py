"""API tests for lead timeline endpoint (D5.6)."""

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
def client(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="timeline@test.example", is_active=True)

    def override_user():
        return user

    def override_db():
        db = MagicMock()
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    lead_id = uuid4()
    monkeypatch.setattr(
        "app.api.routes.a_domain.build_lead_timeline",
        lambda db, lid: {
            "lead_id": str(lid),
            "company_name": "Demo Co",
            "next_action": "Follow up in 5 days",
            "last_touchpoint_at": "2026-05-22T10:00:00+00:00",
            "follow_up_hint": "Waiting for reply",
            "items": [
                {
                    "id": str(uuid4()),
                    "timestamp": "2026-05-22T10:00:00+00:00",
                    "type": "catalog_sent",
                    "channel": "email",
                    "title": "Email intro marked as sent",
                    "summary": "[manually_sent=true]",
                    "is_manual_send": True,
                    "is_contact_research": False,
                }
            ],
            "stats": {
                "total_touchpoints": 1,
                "manual_sent_count": 1,
                "contact_research_count": 0,
                "last_channel": "email",
            },
        },
    )

    with TestClient(app) as c:
        yield c, str(lead_id)
    app.dependency_overrides.clear()


def test_timeline_endpoint(client):
    c, lead_id = client
    r = c.get(f"/api/a-domain/leads/{lead_id}/timeline")
    assert r.status_code == 200
    body = r.json()
    assert body["company_name"] == "Demo Co"
    assert body["follow_up_hint"] == "Waiting for reply"
    assert len(body["items"]) == 1
    assert body["items"][0]["is_manual_send"] is True


def test_timeline_invalid_lead_404(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="tl404@test.example", is_active=True)

    def override_user():
        return user

    def override_db():
        db = MagicMock()
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    def raise_not_found(db, lid):
        raise ValueError("Lead not found")

    monkeypatch.setattr("app.api.routes.a_domain.build_lead_timeline", raise_not_found)

    with TestClient(app) as c:
        r = c.get(f"/api/a-domain/leads/{uuid4()}/timeline")
        assert r.status_code == 404
    app.dependency_overrides.clear()
