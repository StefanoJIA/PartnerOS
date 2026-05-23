"""API tests for pre-quote brief endpoint (D5.14)."""

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
    user = User(id=uuid4(), email="prequote@test.example", is_active=True)
    lead_id = uuid4()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield MagicMock())

    monkeypatch.setattr(
        "app.api.routes.a_domain.build_pre_quote_brief_for_lead",
        lambda db, lid: {
            "lead_id": str(lid),
            "company_name": "Contract Project Interiors",
            "quote_readiness": "almost_ready",
            "sample_readiness": "needs_specs",
            "recommended_product_focus": ["project_supply", "hosun_lifting_systems"],
            "project_type": "project_based",
            "opportunity_score": 72,
            "missing_quote_info": ["quantity_or_volume", "project_timeline"],
            "quote_preparation_checklist": ["Confirm project timeline.", "Confirm quantity."],
            "sample_preparation_checklist": ["Confirm sample purpose."],
            "recommended_customer_questions": ["What quantity should we consider?"],
            "recommended_internal_next_steps": ["Send discovery questions."],
            "recommended_next_action": "Ask for quantity and timeline.",
            "pre_quote_brief_text": "Pre-Quote Preparation Brief — Contract Project Interiors",
            "sample_discussion_brief_text": "Sample Discussion Brief — Contract Project Interiors",
            "warnings": ["No pricing commitments."],
            "safety": {
                "quote_created": False,
                "pricing_generated": False,
                "inventory_promised": False,
                "certification_promised": False,
                "lead_time_promised": False,
                "automatic_sending_enabled": False,
            },
        }
        if lid == lead_id
        else None,
    )

    with TestClient(app) as c:
        yield c, lead_id
    app.dependency_overrides.clear()


def test_pre_quote_brief_endpoint(client):
    c, lead_id = client
    r = c.get(f"/api/a-domain/leads/{lead_id}/pre-quote-brief")
    assert r.status_code == 200
    body = r.json()
    assert body["company_name"] == "Contract Project Interiors"
    assert body["safety"]["quote_created"] is False
    assert "project_supply" in body["recommended_product_focus"]


def test_pre_quote_brief_not_found(client):
    c, _ = client
    r = c.get(f"/api/a-domain/leads/{uuid4()}/pre-quote-brief")
    assert r.status_code == 404
