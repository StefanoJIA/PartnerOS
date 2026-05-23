"""API tests for quote handoff brief endpoint (D5.18)."""

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
    user = User(id=uuid4(), email="handoff@test.example", is_active=True)
    lead_id = uuid4()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield MagicMock())

    monkeypatch.setattr(
        "app.api.routes.a_domain.build_quote_handoff_for_lead",
        lambda db, lid: {
            "lead_id": str(lid),
            "company_name": "SWC Office Furniture",
            "handoff_status": "needs_customer_clarification",
            "handoff_priority": "medium",
            "quote_readiness": "almost_ready",
            "sample_readiness": "needs_specs",
            "opportunity_score": 75,
            "recommended_partner_route": ["hosun_lifting_systems"],
            "recommended_product_scope": ["adjustable_desk_frames"],
            "known_context": ["Office furniture dealer lead."],
            "missing_customer_info": ["quantity_or_volume", "project_timeline"],
            "supplier_preparation_notes": ["Prepare adjustable desk frame overview."],
            "customer_clarification_questions": ["What quantity range should we consider?"],
            "recommended_next_step": "Send clarification questions before quote prep.",
            "quote_handoff_brief_text": "Quote Handoff Brief — SWC Office Furniture",
            "supplier_notes_text": "- Prepare adjustable desk frame overview.",
            "customer_questions_text": "1. What quantity range should we consider?",
            "warnings": ["Internal preparation aid only."],
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


def test_quote_handoff_brief_endpoint(client):
    c, lead_id = client
    r = c.get(f"/api/a-domain/leads/{lead_id}/quote-handoff-brief")
    assert r.status_code == 200
    body = r.json()
    assert body["handoff_status"] == "needs_customer_clarification"
    assert body["safety"]["quote_created"] is False
    assert "hosun_lifting_systems" in body["recommended_partner_route"]


def test_quote_handoff_brief_not_found(client):
    c, _ = client
    r = c.get(f"/api/a-domain/leads/{uuid4()}/quote-handoff-brief")
    assert r.status_code == 404
