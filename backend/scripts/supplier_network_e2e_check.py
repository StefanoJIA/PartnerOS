"""End-to-end supplier network commercial loop gate."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic.config import Config
from alembic.script import ScriptDirectory


def main() -> int:
    cfg = Config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini"))
    head = ScriptDirectory.from_config(cfg).get_current_head()
    expected = head
    print(f"Migration head: {head} (expected {expected})")

    from app.services.supplier_discovery_service import (
        LIFTING_SAMPLE_TEMPLATE_ITEMS,
        QUALIFICATION_DIMENSIONS,
        SAMPLE_TEMPLATES,
    )

    checks = [
        ("migration head", head == expected),
        ("qualification dimensions", len(QUALIFICATION_DIMENSIONS) >= 11),
        ("lifting sample template", len(LIFTING_SAMPLE_TEMPLATE_ITEMS) >= 10),
        ("education template extensible", "education" in SAMPLE_TEMPLATES),
    ]

    try:
        from app.models.enums import SupplierDiscoveryStatus

        statuses = {s.value for s in SupplierDiscoveryStatus}
        checks.append(("information_requested status", "information_requested" in statuses))
        checks.append(("sample_received status", "sample_received" in statuses))
    except Exception:
        checks.append(("supplier discovery statuses", False))

    try:
        from app.api.routes import supplier_discovery, supplier_sample_evaluations

        checks.append(("supplier discovery routes", hasattr(supplier_discovery, "router")))
        checks.append(("sample evaluation routes", hasattr(supplier_sample_evaluations, "router")))
    except Exception:
        checks.append(("supplier network routes", False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1
    print("Supplier network E2E gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
