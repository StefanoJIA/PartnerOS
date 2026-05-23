"""API tests for contact research endpoint (D5.5)."""

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
    user = User(id=uuid4(), email="cr-api@test.example", is_active=True)

    def override_user():
        return user

    def override_db():
        db = MagicMock()
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    lead_id = uuid4()
    monkeypatch.setattr(
        "app.api.routes.a_domain.apply_contact_research",
        lambda db, u, lid, **kwargs: {
            "lead_id": str(lid),
            "interaction_id": str(uuid4()),
            "completeness": {
                "lead_id": str(lid),
                "company_name": "Demo Co",
                "lead_name": "Lead — Demo Co",
                "score": 75,
                "status": "ready_for_outreach",
                "status_label": "Ready for Outreach",
                "missing_fields": ["enrichment"],
                "recommended_research_action": "Run enrichment",
                "segment": None,
                "segments": [],
                "next_action": "Follow up",
                "last_touchpoint": "Contact research",
            },
        },
    )

    with TestClient(app) as c:
        yield c, str(lead_id)
    app.dependency_overrides.clear()


def test_contact_research_endpoint(client):
    c, lead_id = client
    r = c.post(
        f"/api/a-domain/leads/{lead_id}/contact-research",
        json={
            "company": {"website": "https://demo.example"},
            "contact": {"name": "Alex", "email": "alex@demo.example"},
            "lead": {"next_action": "Send intro"},
            "touchpoint_note": "Manual research",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["lead_id"] == lead_id
    assert body["interaction_id"]
    assert body["completeness"]["score"] == 75
    assert body["completeness"]["status"] == "ready_for_outreach"
