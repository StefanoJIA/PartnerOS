"""Tests for D7.9 order resource center."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from app.core.config import Settings
from app.services.portal.order_resource_service import (
    resource_to_dict,
    sign_resource_download,
    verify_resource_signature,
)


def _resource(**overrides):
    row = MagicMock()
    row.id = overrides.get("id", uuid4())
    row.order_id = overrides.get("order_id", uuid4())
    row.file_id = overrides.get("file_id", uuid4())
    row.title = overrides.get("title", "Packing List")
    row.category = overrides.get("category", "packing_list")
    row.description = overrides.get("description", "Customer visible packing list")
    row.status = overrides.get("status", "published")
    row.customer_visible = overrides.get("customer_visible", True)
    row.published_at = overrides.get("published_at", datetime(2026, 5, 29, tzinfo=timezone.utc))
    row.created_at = overrides.get("created_at", datetime(2026, 5, 29, tzinfo=timezone.utc))
    row.updated_at = overrides.get("updated_at", datetime(2026, 5, 29, tzinfo=timezone.utc))
    return row


def _file(**overrides):
    row = MagicMock()
    row.id = overrides.get("id", uuid4())
    row.original_filename = overrides.get("original_filename", "packing-list.pdf")
    row.mime = overrides.get("mime", "application/pdf")
    row.size = overrides.get("size", 1024)
    row.storage_key = overrides.get("storage_key", "secret/path/packing-list.pdf")
    return row


def test_resource_to_dict_hides_storage_path_and_adds_signed_url():
    data = resource_to_dict(_resource(), _file(), include_signed_url=True)

    raw = str(data).lower()
    assert "storage_key" not in raw
    assert "secret/path" not in raw
    assert data["download_url"].startswith("/api/v1/portal/customer/resources/")
    assert data["safety"]["file_location_exposed"] is False
    assert data["safety"]["filesystem_path_exposed"] is False
    assert data["safety"]["customer_notified"] is False


def test_resource_signature_roundtrip_and_tamper_rejected():
    resource_id = uuid4()
    settings = Settings(SECRET_KEY="unit-test-secret")
    signed = sign_resource_download(resource_id, settings=settings, expires_in_minutes=10)

    verify_resource_signature(
        resource_id,
        expires_at=int(signed["expires_at"]),
        token=str(signed["token"]),
        settings=settings,
    )

    try:
        verify_resource_signature(
            uuid4(),
            expires_at=int(signed["expires_at"]),
            token=str(signed["token"]),
            settings=settings,
        )
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403
    else:
        raise AssertionError("tampered resource id should be rejected")
