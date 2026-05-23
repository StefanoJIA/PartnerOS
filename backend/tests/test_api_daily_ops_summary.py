"""API tests for daily ops summary endpoint (D5.8)."""

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
    user = User(id=uuid4(), email="ops@test.example", is_active=True)

    def override_user():
        return user

    def override_db():
        db = MagicMock()
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    lead_id = uuid4()
    monkeypatch.setattr(
        "app.api.routes.a_domain.build_daily_ops_summary",
        lambda db: {
            "summary": {
                "total_leads": 2,
                "overdue": 1,
                "due_today": 0,
                "due_soon": 1,
                "high_priority": 1,
                "needs_contact_research": 1,
                "ready_for_outreach": 1,
                "waiting_reply": 0,
                "needs_enrichment": 1,
            },
            "today_focus": [
                {
                    "lead_id": str(lead_id),
                    "company_name": "Demo Co",
                    "reason": "Overdue follow-up",
                    "segments": ["lift_system_signal"],
                    "due_status": "overdue",
                    "next_action": "Follow up",
                    "priority": "high",
                    "lead_score": 80,
                }
            ],
            "recent_activity": [
                {
                    "lead_id": str(lead_id),
                    "company_name": "Demo Co",
                    "type": "email_intro",
                    "channel": "email",
                    "summary": "Marked sent",
                    "timestamp": "2026-05-22T10:00:00+00:00",
                    "badge": "Manual sent",
                    "is_manual_send": True,
                    "is_contact_research": False,
                }
            ],
            "recent_manual_outreach": [
                {
                    "lead_id": str(lead_id),
                    "company_name": "Demo Co",
                    "type": "email_intro",
                    "channel": "email",
                    "summary": "Marked sent",
                    "timestamp": "2026-05-22T10:00:00+00:00",
                    "badge": "Manual sent",
                    "is_manual_send": True,
                    "is_contact_research": False,
                }
            ],
            "recent_contact_research": [],
            "recent_outreach": [],
            "quick_actions": [{"label": "Import Leads", "path": "/lead-intake"}],
            "safety": {
                "automatic_sending_enabled": False,
                "linkedin_automation_enabled": False,
                "outlook_integration_enabled": False,
            },
            "warnings": [],
            "degraded": False,
        },
    )

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_daily_ops_summary_endpoint(client):
    r = client.get("/api/a-domain/daily-ops-summary")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["overdue"] == 1
    assert body["today_focus"][0]["reason"] == "Overdue follow-up"
    assert body["safety"]["automatic_sending_enabled"] is False
    assert isinstance(body.get("recent_activity"), list)
    assert body["recent_manual_outreach"][0]["badge"] == "Manual sent"
    assert "secret" not in r.text.lower()
    assert "password" not in r.text.lower()


def test_daily_ops_degraded_on_error(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="ops2@test.example", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield MagicMock())

    def boom(_db):
        raise RuntimeError("db unavailable")

    monkeypatch.setattr("app.api.routes.a_domain.build_daily_ops_summary", boom)

    with TestClient(app) as c:
        r = c.get("/api/a-domain/daily-ops-summary")
        assert r.status_code == 200
        body = r.json()
        assert body["degraded"] is True
        assert body["summary"]["overdue"] == 0
        assert body["warnings"]
    app.dependency_overrides.clear()
