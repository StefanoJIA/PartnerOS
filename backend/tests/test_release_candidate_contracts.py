"""Release candidate contract tests — portal security, feature flags, site stub."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes.customer_site_compat import PUBLIC_PRODUCT_GROUPS
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.main import create_app
from app.services.market_response_intelligence import build_lifting_project_expectations
from app.services.portal.customer_field_filter import strip_forbidden_internal_fields
from app.services.portal.customer_portal_bridge import _product_to_customer_dict
from app.services.quotes.pdf_data_builder import _sanitize_interval_quote_table
from app.services.quotes.pricing_service import validate_interval_quote_table


def _client(settings: Settings | None = None) -> tuple[TestClient, MagicMock]:
    resolved = settings or Settings()
    get_settings.cache_clear()
    db = MagicMock()
    with patch("app.main.get_settings", return_value=resolved):
        app = create_app()
    app.dependency_overrides[get_db] = lambda: (yield db)
    app.dependency_overrides[get_settings] = lambda: resolved
    return TestClient(app, raise_server_exceptions=False), db


def test_config_schema_defaults_disable_portal_and_site():
    assert Settings.model_fields["PORTAL_CUSTOMER_API_ENABLED"].default is False
    assert Settings.model_fields["CUSTOMER_SITE_COMPAT_ENABLED"].default is False


def test_site_routes_absent_when_compat_disabled():
    client, _ = _client(Settings(CUSTOMER_SITE_COMPAT_ENABLED=False))
    assert client.get("/api/site/products").status_code == 404


def test_site_routes_present_when_compat_enabled():
    client, db = _client(Settings(CUSTOMER_SITE_COMPAT_ENABLED=True))
    db.query.return_value.filter.return_value.all.return_value = []
    response = client.get("/api/site/products/categories/groups")
    assert response.status_code == 200
    groups = response.json()
    education = next(item for item in groups if item["group_name"] == "Education Furniture")
    assert education["is_pending"] is True
    assert education["is_available"] is False


def test_site_order_post_persists_project_request_reference():
    client, _ = _client(Settings(CUSTOMER_SITE_COMPAT_ENABLED=True))
    fake_id = uuid4()
    fake_row = MagicMock()
    fake_row.id = fake_id
    fake_row.request_reference = "CPR-RC0001"
    with patch(
        "app.api.routes.customer_site_compat.create_project_request_from_site",
        return_value=fake_row,
    ):
        response = client.post("/api/site/customer/orders", json={"items": []})
    assert response.status_code == 200
    data = response.json()
    assert data["order_created"] is False
    assert data["status"] == "project_request_submitted"
    assert data["request_reference"] == "CPR-RC0001"
    assert data["intake_type"] == "project_request"
    assert "formal order" in data["message"].lower() or "not" in data["message"].lower()


def test_portal_disabled_returns_service_unavailable():
    client, _ = _client(Settings(PORTAL_CUSTOMER_API_ENABLED=False))
    response = client.get("/api/v1/portal/customer/products")
    assert response.status_code == 503
    assert response.json()["ok"] is False


def test_portal_requires_token_when_enabled(monkeypatch):
    client, _ = _client(
        Settings(
            PORTAL_CUSTOMER_API_ENABLED=True,
            PORTAL_CUSTOMER_API_REQUIRE_TOKEN=True,
            PORTAL_CUSTOMER_API_TOKEN="rc-test-token",
        )
    )
    monkeypatch.setattr(
        "app.api.v1.routes.portal_customer.build_customer_product_list",
        lambda *args, **kwargs: {"items": [], "total": 0},
    )
    missing = client.get("/api/v1/portal/customer/products")
    wrong = client.get("/api/v1/portal/customer/products", headers={"Authorization": "Bearer wrong"})
    ok = client.get("/api/v1/portal/customer/products", headers={"Authorization": "Bearer rc-test-token"})
    assert missing.status_code == 401
    assert wrong.status_code == 403
    assert ok.status_code == 200


def test_portal_product_bridge_strips_margin_and_pricing_internals():
    row = MagicMock()
    row.id = uuid4()
    row.partner_product_code = "DF0102"
    row.internal_sku = "DF0102"
    row.product_name = "Demo Frame"
    row.product_category = "adjustable_desk_frames"
    row.product_family = "frames"
    row.description_customer = "Customer safe"
    row.status = "active"
    row.default_uom = "EA"
    row.base_currency = "USD"
    row.default_incoterm = "DDP"
    row.image_url = None
    row.attributes_json = {
        "target_margin": "0.25",
        "pricing_model": "interval_margin",
        "pricing_model_steps": ["margin multiplier"],
        "load_capacity_kg": 120,
    }
    payload = _product_to_customer_dict(row)
    blob = json.dumps(payload).lower()
    assert "target_margin" not in blob
    assert "pricing_model_steps" not in blob
    assert "load_capacity_kg" in blob


def test_portal_field_filter_strips_supplier_notes_and_internal_paths():
    payload = {
        "customer_notes": "visible",
        "supplier_notes": "hidden",
        "margin_pct": 0.2,
        "internal_attachment_path": "/data/internal/file.pdf",
        "fit_risk": {"score": 90},
    }
    cleaned = strip_forbidden_internal_fields(payload)
    blob = json.dumps(cleaned).lower()
    assert cleaned["customer_notes"] == "visible"
    assert "supplier_notes" not in blob
    assert "margin_pct" not in blob
    assert "internal_attachment_path" not in blob
    assert "fit_risk" not in blob


def test_portal_order_detail_unknown_id_returns_not_found():
    client, db = _client(
        Settings(
            PORTAL_CUSTOMER_API_ENABLED=True,
            PORTAL_CUSTOMER_API_REQUIRE_TOKEN=True,
            PORTAL_CUSTOMER_API_TOKEN="rc-test-token",
        )
    )
    db.query.return_value.filter.return_value.first.return_value = None
    foreign_id = uuid4()
    response = client.get(
        f"/api/v1/portal/customer/orders/{foreign_id}",
        headers={"Authorization": "Bearer rc-test-token"},
    )
    assert response.status_code == 404


def test_feature_flag_matrix_portal_on_site_off():
    client, _ = _client(
        Settings(
            PORTAL_CUSTOMER_API_ENABLED=True,
            PORTAL_CUSTOMER_API_REQUIRE_TOKEN=True,
            PORTAL_CUSTOMER_API_TOKEN="rc-test-token",
            CUSTOMER_SITE_COMPAT_ENABLED=False,
        )
    )
    assert client.get("/api/site/products").status_code == 404
    assert client.get("/api/v1/portal/customer/manifest", headers={"X-Portal-Customer-Token": "rc-test-token"}).status_code == 200


def test_feature_flag_matrix_site_on_portal_off():
    client, db = _client(
        Settings(
            PORTAL_CUSTOMER_API_ENABLED=False,
            CUSTOMER_SITE_COMPAT_ENABLED=True,
        )
    )
    db.query.return_value.filter.return_value.all.return_value = []
    assert client.get("/api/v1/portal/customer/products").status_code == 503
    assert client.get("/api/site/products/categories/groups").status_code == 200


def test_jooboo_education_group_is_explicitly_pending():
    education = PUBLIC_PRODUCT_GROUPS["Education Furniture"]
    assert education["is_pending"] is True
    assert "JOOBOO" in education["description"] or "approval" in education["description"].lower()


def test_hosun_groups_do_not_carry_pending_flag():
    for name in ("Standalone Frames", "Multi-User Benching", "Electric Columns", "Accessories"):
        assert PUBLIC_PRODUCT_GROUPS[name].get("is_pending") is not True


def test_lifting_expectations_mark_demo_boundary():
    db = MagicMock()
    db.query.return_value.all.return_value = []
    payload = build_lifting_project_expectations(db)
    assert payload["safety"]["read_only"] is True
    assert payload["requirements"]
    assert payload["requirements"][0]["single_feedback_is_not_conclusion"] is True


def test_pdf_interval_table_matches_pricing_validation():
    rows = [
        {"min_qty": 1, "max_qty": 49, "fob_unit_price": "10.00", "ddp_unit_price": "12.00"},
        {"min_qty": 50, "max_qty": None, "fob_unit_price": "9.00", "ddp_unit_price": "11.00"},
    ]
    line = {
        "currency": "USD",
        "pricing_breakdown_json": {"quote_model": {"final_quote_stage": {"interval_quote_table": rows}}},
    }
    pdf_rows = _sanitize_interval_quote_table(line)
    assert validate_interval_quote_table(pdf_rows) == []
    assert pdf_rows[0]["fob_unit_price"] == "10.00"
