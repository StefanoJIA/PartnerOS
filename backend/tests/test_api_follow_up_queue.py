"""API tests for follow-up queue endpoints (D5.7)."""

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
    user = User(id=uuid4(), email="fuq@test.example", is_active=True)

    def override_user():
        return user

    def override_db():
        db = MagicMock()
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    lead_id = uuid4()
    monkeypatch.setattr(
        "app.api.routes.a_domain.build_follow_up_queue_rows",
        lambda db: [
            {
                "lead_id": str(lead_id),
                "company_name": "Demo Co",
                "lead_score": 70,
                "segments": ["lift_system_signal"],
                "next_action": "Follow up",
                "next_follow_up_date": "2026-05-28",
                "due_status": "due_soon",
                "days_until_due": 5,
                "last_touchpoint_at": None,
                "waiting_reply": True,
                "recommended_action": "Follow up today",
                "touch_count": 1,
            }
        ],
    )
    monkeypatch.setattr(
        "app.api.routes.a_domain.summarize_follow_up_queue",
        lambda rows: {
            "total": 1,
            "overdue": 0,
            "due_today": 0,
            "due_soon": 1,
            "no_follow_up_date": 0,
            "waiting_reply": 1,
        },
    )
    monkeypatch.setattr(
        "app.api.routes.a_domain.apply_follow_up_schedule",
        lambda db, user, lid, **kw: {
            "lead_id": str(lid),
            "company_name": "Demo Co",
            "next_action": kw.get("next_action"),
            "next_follow_up_date": "2026-05-28",
            "due_status": "due_soon",
            "days_until_due": 5,
            "interaction_id": str(uuid4()),
        },
    )

    with TestClient(app) as c:
        yield c, str(lead_id)
    app.dependency_overrides.clear()


def test_follow_up_queue_endpoint(client):
    c, _ = client
    r = c.get("/api/a-domain/follow-up-queue")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["due_soon"] == 1
    assert body["rows"][0]["due_status"] == "due_soon"


def test_patch_follow_up_endpoint(client):
    c, lead_id = client
    r = c.patch(
        f"/api/a-domain/leads/{lead_id}/follow-up",
        json={
            "next_follow_up_date": "2026-05-28",
            "next_action": "Follow up in 5 days",
            "status_note": "Manual schedule",
        },
    )
    assert r.status_code == 200
    assert r.json()["due_status"] == "due_soon"
