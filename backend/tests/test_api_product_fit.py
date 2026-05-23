"""API tests for product fit endpoint (D5.12)."""

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
    user = User(id=uuid4(), email="productfit@test.example", is_active=True)
    lead_id = uuid4()

    def override_user():
        return user

    def override_db():
        db = MagicMock()
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    monkeypatch.setattr(
        "app.api.routes.a_domain.build_product_fit_for_lead",
        lambda db, lid: {
            "lead_id": str(lid),
            "company_name": "Ergo Sit Stand Workspace",
            "recommended_product_focus": ["hosun_lifting_systems", "adjustable_desk_frames"],
            "project_opportunity_score": 78,
            "opportunity_level": "promising",
            "project_type": "dealer_supply",
            "quote_readiness": "almost_ready",
            "sample_readiness": "needs_specs",
            "missing_quote_info": ["quantity_or_volume", "project_timeline"],
            "recommended_discovery_questions": [
                "Are you currently sourcing adjustable desk frames or lifting columns?"
            ],
            "recommended_next_product_action": "Ask for quantity before preparing quote.",
            "sales_angle": "Position HOSUN lifting systems for Ergo Sit Stand Workspace.",
            "warnings": ["Suggestions only — no prices confirmed."],
        }
        if lid == lead_id
        else None,
    )

    with TestClient(app) as c:
        yield c, lead_id
    app.dependency_overrides.clear()


def test_product_fit_endpoint(client):
    c, lead_id = client
    r = c.get(f"/api/a-domain/leads/{lead_id}/product-fit")
    assert r.status_code == 200
    body = r.json()
    assert body["company_name"] == "Ergo Sit Stand Workspace"
    assert body["project_opportunity_score"] == 78
    assert "hosun_lifting_systems" in body["recommended_product_focus"]


def test_product_fit_not_found(client):
    c, _ = client
    r = c.get(f"/api/a-domain/leads/{uuid4()}/product-fit")
    assert r.status_code == 404


@pytest.fixture
def board_client(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="board@test.example", is_active=True)

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield MagicMock())

    monkeypatch.setattr(
        "app.api.routes.a_domain.build_product_opportunity_board",
        lambda db: {
            "summary": {
                "total": 1,
                "high_opportunity": 1,
                "promising": 0,
                "quote_ready": 1,
                "almost_ready": 0,
                "almost_quote_ready": 0,
                "sample_ready": 0,
                "needs_specs": 1,
                "lifting_system_fit": 0,
                "project_supply_fit": 1,
                "education_fit": 0,
                "medical_fit": 0,
                "oem_odm_fit": 0,
                "oem_odm_potential": 0,
            },
            "missing_info_summary": {"quantity_or_volume": 1},
            "rows": [
                {
                    "lead_id": "a",
                    "company_name": "Demo",
                    "project_opportunity_score": 85,
                    "opportunity_score": 85,
                    "opportunity_level": "high_opportunity",
                    "project_type": "project_based",
                    "quote_readiness": "ready",
                    "sample_readiness": "needs_specs",
                    "recommended_product_focus": ["project_supply"],
                    "missing_quote_info": ["quantity_or_volume"],
                    "recommended_next_product_action": "Confirm specs.",
                    "sales_angle": "Project supply partner.",
                    "next_action": "Follow up",
                    "follow_up_date": None,
                    "due_status": "no_follow_up_date",
                }
            ],
            "safety": {
                "automatic_quote_creation": False,
                "automatic_sending_enabled": False,
                "price_promises_enabled": False,
                "inventory_promises_enabled": False,
            },
            "warnings": [],
            "degraded": False,
        },
    )

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_product_opportunity_board_endpoint(board_client):
    r = board_client.get("/api/a-domain/product-opportunity-board")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["total"] == 1
    assert body["rows"][0]["quote_readiness"] == "ready"
    assert body["safety"]["automatic_quote_creation"] is False
    assert body["missing_info_summary"]["quantity_or_volume"] == 1
