"""API tests for product-aware draft endpoint (D5.15)."""

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
    user = User(id=uuid4(), email="pad@test.example", is_active=True)
    lead_id = uuid4()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield MagicMock())

    monkeypatch.setattr(
        "app.api.routes.a_domain.build_product_aware_draft_for_lead",
        lambda db, lid, **kw: {
            "lead_id": str(lid),
            "company_name": "Ergo Sit Stand Workspace",
            "channel": kw.get("channel", "email_intro"),
            "draft_purpose": kw.get("draft_purpose", "product_discovery"),
            "tone": "concise",
            "language": "en",
            "subject": "intelliOffice — adjustable desk frame / lifting system discussion",
            "body": "Hi Alex,\n\nDraft body without pricing promises.",
            "linkedin_note": None,
            "questions": ["Are you sourcing lifting columns?"],
            "recommended_next_action": "Send manually after review.",
            "suggested_follow_up_days": 5,
            "source_context": {
                "product_focus": ["hosun_lifting_systems"],
                "quote_readiness": "almost_ready",
                "sample_readiness": "needs_specs",
                "missing_quote_info": ["quantity_or_volume"],
            },
            "safety": {
                "quote_created": False,
                "pricing_generated": False,
                "inventory_promised": False,
                "certification_promised": False,
                "lead_time_promised": False,
                "automatic_sending_enabled": False,
            },
            "warnings": ["Human review required."],
        }
        if lid == lead_id
        else None,
    )

    with TestClient(app) as c:
        yield c, lead_id
    app.dependency_overrides.clear()


def test_product_aware_draft_endpoint(client):
    c, lead_id = client
    r = c.post(
        f"/api/a-domain/leads/{lead_id}/product-aware-draft",
        json={"channel": "email_intro", "draft_purpose": "product_discovery"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["company_name"] == "Ergo Sit Stand Workspace"
    assert body["safety"]["quote_created"] is False


def test_product_aware_draft_not_found(client):
    c, _ = client
    r = c.post(
        f"/api/a-domain/leads/{uuid4()}/product-aware-draft",
        json={"channel": "email_intro"},
    )
    assert r.status_code == 404
