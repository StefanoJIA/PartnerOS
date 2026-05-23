"""API tests for lead completeness endpoint (D5.4)."""

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
    user = User(id=uuid4(), email="completeness@test.example", is_active=True)

    def override_user():
        return user

    def override_db():
        db = MagicMock()
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    monkeypatch.setattr(
        "app.api.routes.a_domain.build_lead_completeness_rows",
        lambda db: [
            {
                "lead_id": "abc",
                "company_name": "Demo Co",
                "lead_name": "Lead — Demo Co",
                "score": 72,
                "status": "ready_for_outreach",
                "status_label": "Ready for Outreach",
                "missing_fields": ["enrichment"],
                "recommended_research_action": "Run enrichment before outreach.",
                "segment": "lift_system_signal",
                "segments": ["lift_system_signal"],
                "next_action": "Follow up",
                "last_touchpoint": "—",
            }
        ],
    )
    monkeypatch.setattr(
        "app.api.routes.a_domain.summarize_completeness",
        lambda rows: {
            "total": 1,
            "complete": 0,
            "ready_for_outreach": 1,
            "needs_contact_research": 0,
            "incomplete": 0,
            "missing_website": 0,
            "missing_contact_method": 0,
        },
    )

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_lead_completeness_endpoint(client):
    r = client.get("/api/a-domain/lead-completeness")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["total"] == 1
    assert body["rows"][0]["company_name"] == "Demo Co"
    assert body["rows"][0]["score"] == 72
