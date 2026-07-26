"""Tests for customer site compat feature gate."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.main import create_app


def _client(settings: Settings) -> TestClient:
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None
    with patch("app.main.get_settings", return_value=settings):
        app = create_app()
    app.dependency_overrides[get_db] = lambda: (yield db)
    return TestClient(app, raise_server_exceptions=False)


def test_customer_site_compat_disabled_by_default():
    get_settings.cache_clear()
    client = _client(Settings(CUSTOMER_SITE_COMPAT_ENABLED=False))
    response = client.get("/api/site/products")
    assert response.status_code == 404


def test_customer_site_compat_enabled_exposes_route():
    get_settings.cache_clear()
    client = _client(Settings(CUSTOMER_SITE_COMPAT_ENABLED=True))
    response = client.get("/api/site/products")
    get_settings.cache_clear()
    assert response.status_code == 200
