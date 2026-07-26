"""E2E supplier convergence smoke — catalog/pricing/portal/market chain."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import log_backend_base_url
from app.core.config import get_settings
from app.core.database_lifecycle import get_migration_revisions


def main() -> int:
    log_backend_base_url()
    print("E2E Supplier Convergence Check")
    settings = get_settings()
    current, head, _ = get_migration_revisions(settings)
    checks: list[tuple[str, bool, str]] = []

    mig_ok = current == head == "0026_customer_project_requests"
    checks.append(("migration head 0026", mig_ok, f"{current}/{head}"))

    portal_off = not settings.PORTAL_CUSTOMER_API_ENABLED or settings.PORTAL_CUSTOMER_API_TOKEN == ""
    checks.append(("portal bridge default safe", portal_off or settings.PORTAL_CUSTOMER_API_REQUIRE_TOKEN, "token gate"))

    site_off = not settings.CUSTOMER_SITE_COMPAT_ENABLED
    checks.append(("customer site compat default off", site_off, str(settings.CUSTOMER_SITE_COMPAT_ENABLED)))

    try:
        from app.services.quotes.pricing_service import validate_interval_quote_table

        issues = validate_interval_quote_table(
            [
                {"min_qty": 1, "max_qty": 49, "fob_unit_price": "10", "ddp_unit_price": "12"},
                {"min_qty": 50, "max_qty": None, "fob_unit_price": "9", "ddp_unit_price": "11"},
            ]
        )
        checks.append(("interval validation helper", not issues, str(issues)))
    except Exception as exc:
        checks.append(("interval validation helper", False, str(exc)))

    try:
        from app.services.market_response_intelligence import build_lifting_project_expectations
        from app.core.database import SessionLocal

        with SessionLocal() as db:
            payload = build_lifting_project_expectations(db)
        checks.append(
            (
                "lifting project expectations",
                bool(payload.get("requirements")),
                f"{payload.get('summary', {}).get('requirement_count', 0)} requirements",
            )
        )
    except Exception as exc:
        checks.append(("lifting project expectations", False, str(exc)))

    passed = True
    for label, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {label} ({detail})")
        passed = passed and ok
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
