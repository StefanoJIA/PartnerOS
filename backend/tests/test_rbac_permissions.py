"""Tests for D8.1 internal role permission boundaries."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import (
    PERM_FEEDBACK_WRITE,
    PERM_MARKET_READ,
    PERM_ORDERS_READ,
    PERM_RESOURCES_WRITE,
    has_permission,
    permission_list,
    user_permissions,
)
from app.main import create_app
from app.models import Role, User


def _user(role_name: str, permissions: dict | list | None = None) -> User:
    role = Role(id=uuid4(), name=role_name, permissions=permissions)
    user = User(
        id=uuid4(),
        email=f"{role_name.lower().replace(' ', '_')}@test.example",
        full_name=role_name,
        role_id=role.id,
        is_active=True,
    )
    user.role = role
    return user


def test_role_presets_allow_viewer_reads_but_block_writes():
    viewer = _user("Viewer")

    assert PERM_ORDERS_READ in user_permissions(viewer)
    assert PERM_MARKET_READ in user_permissions(viewer)
    assert has_permission(viewer, PERM_ORDERS_READ) is True
    assert has_permission(viewer, PERM_MARKET_READ) is True
    assert has_permission(viewer, PERM_RESOURCES_WRITE) is False
    assert has_permission(viewer, PERM_FEEDBACK_WRITE) is False


def test_explicit_role_permissions_override_presets():
    custom = _user("Viewer", {"permissions": [PERM_FEEDBACK_WRITE]})

    assert permission_list(custom) == [PERM_FEEDBACK_WRITE]
    assert has_permission(custom, PERM_FEEDBACK_WRITE) is True
    assert has_permission(custom, PERM_ORDERS_READ) is False


def test_viewer_can_read_feedback_but_cannot_patch_or_create_resources(monkeypatch):
    app = create_app()
    viewer = _user("Viewer")
    db = MagicMock()
    ticket_id = uuid4()
    file_id = uuid4()
    order_id = uuid4()

    monkeypatch.setattr(
        "app.api.v1.routes.feedback_tickets.list_feedback_tickets",
        lambda *a, **k: {"items": [], "total": 0, "page": 1, "limit": 50},
    )
    app.dependency_overrides[get_current_user] = lambda: viewer
    app.dependency_overrides[get_db] = lambda: (yield db)

    with TestClient(app) as client:
        feedback_list = client.get("/api/v1/feedback-tickets")
        feedback_patch = client.patch(
            f"/api/v1/feedback-tickets/{ticket_id}",
            json={"status": "resolved"},
        )
        resource_create = client.post(
            f"/api/v1/orders/{order_id}/resources",
            json={"file_id": str(file_id), "title": "Packing List"},
        )

    assert feedback_list.status_code == 200
    assert feedback_patch.status_code == 403
    assert resource_create.status_code == 403
