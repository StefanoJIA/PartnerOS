"""Customer project request intake, fit matching, and operator workflow tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.main import create_app
from app.models.customer_project_requests import CustomerProjectRequest
from app.schemas.customer_project_request_domain import ProjectRequirementFields, SiteProjectRequestIn
from app.services.customer_project_requests.intake_service import (
    build_fit_summary,
    compute_completeness,
    create_project_request_from_site,
    site_payload_to_request_fields,
)
from app.services.customer_project_requests.market_signal_service import build_market_signal_draft


def test_site_payload_maps_line_items_and_quantities():
    body = SiteProjectRequestIn(
        items=[{"product_name": "Dual Motor Frame", "sku": "HS-DEMO-001", "quantity": 50}],
        shipping_name="Pilot Buyer",
        customer_email="pilot.demo@example.com",
        notes="Need 300kg load desk frame for industrial bench",
        requirements=ProjectRequirementFields(load_capacity_kg=300, noise_db_target=48),
    )
    fields = site_payload_to_request_fields(body)
    assert fields["quantity_min"] == 50
    assert fields["sku"] == "HS-DEMO-001"
    assert fields["requirements_json"]["load_capacity_kg"] == 300


def test_completeness_flags_missing_lifting_fields():
    row = CustomerProjectRequest(
        request_reference="CPR-TEST0001",
        status="submitted",
        customer_name="Demo",
        product_interest="Frame",
        quantity_min=10,
        requirements_json={"load_capacity_kg": 120},
    )
    result = compute_completeness(row)
    assert result["completeness_pct"] < 100
    assert "noise_db_target" in result["missing_fields"]


def test_fit_summary_pending_jooboo_is_unknown_not_hosun_default():
    db = MagicMock()
    catalog = MagicMock()
    catalog.sku = "JB-DEMO-SCHOOL-DESK"
    catalog.partner_id = uuid4()
    catalog.attributes_json = {"is_pending": True, "catalog_pending": True}
    partner = MagicMock()
    partner.partner_code = "JOOBOO"
    db.query.return_value.filter.return_value.first.return_value = partner

    row = CustomerProjectRequest(
        request_reference="CPR-JB001",
        status="submitted",
        sku="JB-DEMO-SCHOOL-DESK",
        product_catalog_id=uuid4(),
        requirements_json={"load_capacity_kg": 80},
    )
    summary = build_fit_summary(db, row, catalog_row=catalog)
    assert summary["partner_code"] == "JOOBOO"
    assert summary["partner_pending"] is True
    assert summary["overall_status"] == "UNKNOWN"


def test_fit_summary_hosun_heavy_load_match():
    db = MagicMock()
    catalog = MagicMock()
    catalog.sku = "HS-HRD-300"
    catalog.partner_id = uuid4()
    catalog.attributes_json = {"load_capacity_kg": 300, "noise_db": 45, "certifications": ["CE"]}
    partner = MagicMock()
    partner.partner_code = "HOSUN"

    row = CustomerProjectRequest(
        request_reference="CPR-HD001",
        status="submitted",
        requirements_json={"load_capacity_kg": 300},
    )
    summary = build_fit_summary(db, row, catalog_row=catalog)
    heavy = next(m for m in summary["matches"] if m["dimension"] == "heavy_load")
    assert heavy["match_status"] == "MATCH"


def test_market_signal_draft_marks_assumption_vs_real():
    row = CustomerProjectRequest(
        request_reference="CPR-REAL01",
        status="submitted",
        source="customer_site",
        project_scenario="Need quiet 300kg frame for open office",
        requirements_json={"load_capacity_kg": 300, "noise_db_target": 48},
        fit_summary_json={"overall_status": "PARTIAL", "matches": []},
    )
    draft = build_market_signal_draft(MagicMock(), row)
    assert draft["signal_class"] == "REAL"
    assert draft["requires_operator_approval"] is True
    assert "disclaimer" in draft


def _api_client(settings: Settings | None = None):
    resolved = settings or Settings(CUSTOMER_SITE_COMPAT_ENABLED=True)
    get_settings.cache_clear()
    db = MagicMock()
    with patch("app.main.get_settings", return_value=resolved):
        app = create_app()
    app.dependency_overrides[get_db] = lambda: (yield db)
    app.dependency_overrides[get_settings] = lambda: resolved
    return TestClient(app, raise_server_exceptions=False), db


def test_site_order_post_persists_project_request_not_order():
    client, db = _api_client()
    fake_row = CustomerProjectRequest(
        id=uuid4(),
        request_reference="CPR-API001",
        status="submitted",
    )
    with patch(
        "app.api.routes.customer_site_compat.create_project_request_from_site",
        return_value=fake_row,
    ) as mocked:
        response = client.post(
            "/api/site/customer/orders",
            json={"items": [{"quantity": 5, "product_name": "Frame"}]},
            headers={"Idempotency-Key": "demo-key-1"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["order_created"] is False
    assert data["status"] == "project_request_submitted"
    assert data["request_reference"] == "CPR-API001"
    assert data["intake_type"] == "project_request"
    mocked.assert_called_once()


def test_admin_project_requests_requires_auth():
    client, _ = _api_client()
    response = client.get("/api/project-requests")
    assert response.status_code in {401, 403}


def test_illegal_status_transition_rejected():
    from app.core.deps import get_current_user
    from app.models import User

    client, db = _api_client()
    user = User(id=uuid4(), email="admin@test.example", is_active=True)
    client.app.dependency_overrides[get_current_user] = lambda: user
    row_id = uuid4()
    row = CustomerProjectRequest(
        id=row_id,
        request_reference="CPR-TRANS01",
        status="submitted",
        fit_summary_json={"overall_status": "PARTIAL", "matches": []},
        sku="HS-HRD-300",
    )
    db.query.return_value.filter.return_value.first.return_value = row
    with patch(
        "app.api.routes.customer_project_requests.update_request_status",
        side_effect=__import__("fastapi").HTTPException(status_code=400, detail="Illegal status transition"),
    ):
        response = client.patch(
            f"/api/project-requests/{row_id}",
            json={"status": "converted"},
        )
    assert response.status_code == 400
