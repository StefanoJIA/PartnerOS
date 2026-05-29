"""Lightweight role permission helpers for internal APIs."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, status

from app.core.deps import get_current_user
from app.models import User

PERMISSION_ALL = "*"

PERM_ADMIN_MANAGE = "admin:manage"
PERM_FEEDBACK_READ = "feedback:read"
PERM_FEEDBACK_WRITE = "feedback:write"
PERM_MARKET_READ = "market:read"
PERM_ORDERS_READ = "orders:read"
PERM_ORDERS_WRITE = "orders:write"
PERM_PORTAL_READINESS = "portal:readiness"
PERM_RESOURCES_READ = "resources:read"
PERM_RESOURCES_WRITE = "resources:write"
PERM_SYSTEM_READINESS = "system:readiness"

ADMIN_PERMISSIONS = {PERMISSION_ALL}
OPERATOR_PERMISSIONS = {
    PERM_FEEDBACK_READ,
    PERM_FEEDBACK_WRITE,
    PERM_MARKET_READ,
    PERM_ORDERS_READ,
    PERM_ORDERS_WRITE,
    PERM_PORTAL_READINESS,
    PERM_RESOURCES_READ,
    PERM_RESOURCES_WRITE,
    PERM_SYSTEM_READINESS,
}
VIEWER_PERMISSIONS = {
    PERM_FEEDBACK_READ,
    PERM_MARKET_READ,
    PERM_ORDERS_READ,
    PERM_PORTAL_READINESS,
    PERM_RESOURCES_READ,
    PERM_SYSTEM_READINESS,
}

ROLE_PERMISSION_PRESETS: dict[str, set[str]] = {
    "admin": ADMIN_PERMISSIONS,
    "administrator": ADMIN_PERMISSIONS,
    "operations": OPERATOR_PERMISSIONS,
    "operator": OPERATOR_PERMISSIONS,
    "supplier manager": OPERATOR_PERMISSIONS,
    "sales": OPERATOR_PERMISSIONS,
    "viewer": VIEWER_PERMISSIONS,
}


def normalize_role_name(value: str | None) -> str:
    return (value or "").strip().lower()


def _permissions_from_json(value: Any) -> set[str]:
    if not value:
        return set()
    if isinstance(value, list | tuple | set):
        return {str(item).strip() for item in value if str(item).strip()}
    if isinstance(value, dict):
        enabled = value.get("permissions")
        if isinstance(enabled, list | tuple | set):
            return {str(item).strip() for item in enabled if str(item).strip()}
        return {str(key).strip() for key, item in value.items() if item and str(key).strip()}
    return set()


def user_permissions(user: User) -> set[str]:
    role = getattr(user, "role", None)
    role_name = normalize_role_name(getattr(role, "name", None))
    explicit = _permissions_from_json(getattr(role, "permissions", None))
    if explicit:
        return explicit
    if not role_name:
        return set(OPERATOR_PERMISSIONS)
    return set(ROLE_PERMISSION_PRESETS.get(role_name, VIEWER_PERMISSIONS))


def has_permission(user: User, permission: str) -> bool:
    permissions = user_permissions(user)
    return PERMISSION_ALL in permissions or permission in permissions


def require_permission(permission: str) -> Callable[[User], User]:
    def dependency(user: User = Depends(get_current_user)) -> User:
        if not has_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return user

    return dependency


def permission_list(user: User) -> list[str]:
    return sorted(user_permissions(user))
