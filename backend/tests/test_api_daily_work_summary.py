"""API tests for daily work summary endpoint (D5.10)."""

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
    user = User(id=uuid4(), email="work@test.example", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield MagicMock())

    monkeypatch.setattr(
        "app.api.routes.a_domain.build_daily_work_summary",
        lambda db, target_date=None: {
            "date": "2026-05-23",
            "summary": {
                "manual_outreach_sent": 2,
                "contact_research_updates": 1,
                "follow_ups_scheduled": 3,
                "drafts_generated": None,
                "leads_touched": 4,
                "overdue_remaining": 1,
                "due_today_remaining": 0,
                "due_soon": 5,
                "needs_contact_research": 10,
                "high_priority_remaining": 8,
            },
            "highlights": [
                {
                    "lead_id": str(uuid4()),
                    "company_name": "Demo Co",
                    "action": "Manual email intro marked as sent",
                    "next_action": "Follow up in 5 days",
                }
            ],
            "tomorrow_focus": [
                {
                    "lead_id": str(uuid4()),
                    "company_name": "Tomorrow Co",
                    "reason": "Due soon",
                    "next_action": "Call back",
                }
            ],
            "copyable_summary": "Daily intelliOffice Summary — 2026-05-23\nManual outreach sent: 2",
            "warnings": [],
            "degraded": False,
        },
    )

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_daily_work_summary_endpoint(client):
    r = client.get("/api/a-domain/daily-work-summary")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["manual_outreach_sent"] == 2
    assert body["highlights"][0]["action"]
    assert "copyable_summary" in body
    assert "password" not in r.text.lower()


def test_daily_work_summary_date_query(client):
    r = client.get("/api/a-domain/daily-work-summary", params={"date": "2026-05-22"})
    assert r.status_code == 200


def test_daily_work_degraded(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="w2@test.example", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield MagicMock())

    def boom(_db, target_date=None):
        raise RuntimeError("db down")

    monkeypatch.setattr("app.api.routes.a_domain.build_daily_work_summary", boom)

    with TestClient(app) as c:
        r = c.get("/api/a-domain/daily-work-summary")
        assert r.status_code == 200
        body = r.json()
        assert body["degraded"] is True
        assert body["warnings"]
    app.dependency_overrides.clear()
