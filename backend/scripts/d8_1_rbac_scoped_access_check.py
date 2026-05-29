"""D8.1 RBAC scoped access smoke check."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import PERM_ORDERS_READ, PERM_RESOURCES_WRITE, has_permission
from app.main import create_app
from app.models import Role, User


class Check:
    def __init__(self, label: str) -> None:
        self.label = label
        self.ok = False
        self.detail = ""

    def pass_(self, detail: str = "") -> None:
        self.ok = True
        self.detail = detail

    def fail(self, detail: str) -> None:
        self.ok = False
        self.detail = detail

    def line(self) -> str:
        status = "PASS" if self.ok else "FAIL"
        suffix = f" ({self.detail})" if self.detail else ""
        return f"[{status}] {self.label}{suffix}"


def _user(role_name: str) -> User:
    role = Role(id=uuid4(), name=role_name, permissions=None)
    user = User(
        id=uuid4(),
        email=f"{role_name.lower()}@d8-1.example",
        full_name=role_name,
        role_id=role.id,
        is_active=True,
    )
    user.role = role
    return user


def main() -> int:
    checks = [
        Check("viewer has read scope"),
        Check("viewer cannot write resources"),
        Check("write route returns 403 for viewer"),
        Check("admin /auth/me exposes permissions"),
    ]

    viewer = _user("Viewer")
    if has_permission(viewer, PERM_ORDERS_READ):
        checks[0].pass_("orders:read")
    else:
        checks[0].fail("missing orders:read")

    if not has_permission(viewer, PERM_RESOURCES_WRITE):
        checks[1].pass_("resources:write denied")
    else:
        checks[1].fail("resources:write unexpectedly allowed")

    app = create_app()
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: (yield db)
    app.dependency_overrides[get_current_user] = lambda: viewer
    with TestClient(app) as client:
        order_id = uuid4()
        file_id = uuid4()
        denied = client.post(
            f"/api/v1/orders/{order_id}/resources",
            json={"file_id": str(file_id), "title": "Packing List"},
        )
    if denied.status_code == 403:
        checks[2].pass_("HTTP 403")
    else:
        checks[2].fail(f"HTTP {denied.status_code}")

    admin = _user("Admin")
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: admin
    with TestClient(app) as client:
        me = client.get("/api/auth/me")
    data = me.json() if me.status_code == 200 else {}
    if me.status_code == 200 and "*" in data.get("permissions", []):
        checks[3].pass_("admin wildcard exposed")
    else:
        checks[3].fail(f"HTTP {me.status_code}: {data}")

    print("D8.1 RBAC Scoped Access Check")
    for check in checks:
        print(check.line())
    return 0 if all(c.ok for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
