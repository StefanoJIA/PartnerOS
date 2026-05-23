"""API tests for lead intake endpoints (D5.3)."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import create_app
from app.models import User
from app.services.a_domain import lead_import_service as svc


@pytest.fixture
def client(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="intake@test.example", is_active=True)

    def override_user():
        return user

    def override_db():
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    monkeypatch.setattr(
        svc,
        "preview_lead_csv_text",
        lambda db, text: svc.LeadIntakePreviewResult(
            rows=[],
            summary=svc.LeadIntakePreviewSummary(
                total=0, ok=0, warnings=0, errors=0, duplicates=0, ready_to_import=0
            ),
        ),
    )

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_lead_intake_preview_endpoint(client):
    r = client.post("/api/a-domain/lead-intake/preview", json={"csv_text": "company_name\nTest Co,,,,,,,,,,,,,,,,\n"})
    assert r.status_code == 200
    body = r.json()
    assert "rows" in body
    assert "summary" in body


def test_lead_intake_apply_requires_confirm(client):
    r = client.post(
        "/api/a-domain/lead-intake/apply",
        json={"csv_text": "company_name\nAcme,,,,,,,,,,,,,,,,\n", "confirm": False},
    )
    assert r.status_code == 400
    assert "confirm" in r.json()["detail"].lower()


def test_lead_intake_template_download(client):
    r = client.get("/api/a-domain/lead-intake/template")
    assert r.status_code == 200
    assert "company_name" in r.text
