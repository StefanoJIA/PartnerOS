"""Tests for customer site compat feature gate."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_customer_site_compat_disabled_by_default():
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/site/products")
    assert response.status_code == 404


def test_customer_site_compat_enabled_exposes_route(monkeypatch):
    monkeypatch.setenv("CUSTOMER_SITE_COMPAT_ENABLED", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/site/products")
    get_settings.cache_clear()
    assert response.status_code in (200, 401, 403, 422)
