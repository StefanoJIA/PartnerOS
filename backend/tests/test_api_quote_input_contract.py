"""API tests for quote input contract endpoint (D5.19)."""

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
    user = User(id=uuid4(), email="contract@test.example", is_active=True)
    lead_id = uuid4()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield MagicMock())

    monkeypatch.setattr(
        "app.api.routes.a_domain.build_quote_input_contract_for_lead",
        lambda db, lid: {
            "lead_id": str(lid),
            "company_name": "SWC Office Furniture",
            "handoff_status": "needs_customer_clarification",
            "quote_module_readiness": "needs_more_customer_info",
            "recommended_partner_route": ["hosun_lifting_systems"],
            "recommended_product_scope": ["adjustable_desk_frames"],
            "quote_input_fields": {
                "customer": {
                    "company_name": "SWC Office Furniture",
                    "contact_name": "Alex",
                    "contact_method_available": True,
                },
                "product_intent": {
                    "product_focus": ["adjustable_desk_frames"],
                    "project_type": "dealer_project",
                    "sample_readiness": "needs_specs",
                    "quote_readiness": "almost_ready",
                },
                "known_requirements": {
                    "quantity_or_volume": None,
                    "product_type": None,
                    "frame_size_or_desktop_size": None,
                    "load_capacity_requirement": None,
                    "color_or_finish": None,
                    "delivery_location": None,
                    "project_timeline": None,
                    "certification_requirement": None,
                    "sample_quantity": None,
                    "oem_customization_requirement": None,
                    "component_category": None,
                },
                "missing_requirements": ["quantity_or_volume", "project_timeline"],
                "recommended_questions": ["What quantity range should we consider?"],
                "supplier_preparation_notes": ["Prepare adjustable desk frame overview."],
            },
            "copyable_json": '{"lead_id": "test"}',
            "copyable_handoff_summary": "Quote Input Contract — SWC Office Furniture",
            "warnings": ["Quote input contract is a Phase 2 handoff boundary only."],
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


def test_quote_input_contract_endpoint(client):
    c, lead_id = client
    r = c.get(f"/api/a-domain/leads/{lead_id}/quote-input-contract")
    assert r.status_code == 200
    body = r.json()
    assert body["quote_module_readiness"] == "needs_more_customer_info"
    assert body["safety"]["quote_created"] is False
    assert "hosun_lifting_systems" in body["recommended_partner_route"]


def test_quote_input_contract_not_found(client):
    c, _ = client
    r = c.get(f"/api/a-domain/leads/{uuid4()}/quote-input-contract")
    assert r.status_code == 404
