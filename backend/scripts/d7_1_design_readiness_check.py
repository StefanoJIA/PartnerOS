"""D7.1 Order Schema & API Design Review readiness check (design gate only)."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings
from app.core.database_lifecycle import get_migration_revisions

EXPECTED_HEAD = "0009_quote_send_tracking"

REQUIRED_DOCS = (
    ("D6 closure docs", REPO_ROOT / "docs" / "releases" / "d6_final_quote_mvp_release_20260523.md"),
    ("D6 capability map", REPO_ROOT / "docs" / "architecture" / "d6_quote_capability_map.md"),
    ("D7 readiness brief", REPO_ROOT / "docs" / "phase3" / "d7_order_module_readiness_brief.md"),
    ("D7.1 design doc", REPO_ROOT / "docs" / "phase3" / "d7_1_order_schema_api_design_review.md"),
    ("phase3 roadmap", REPO_ROOT / "docs" / "phase3" / "phase3_roadmap.md"),
)

ORDER_MIGRATION_MARKERS = (
    "customer_orders",
    'create_table("customer_orders"',
    "create_table(\n        \"customer_orders\"",
    "order_line_items",
    "order_partner_splits",
)

ORDER_API_MARKERS = (
    "routes/orders.py",
    "router.include_router(orders",
    'prefix="/orders"',
)

SAFETY_SECTION_MARKERS = (
    "## Safety Rules",
    "production_started",
    "shipment_created",
    "automatic_sending_enabled",
    "payment_received",
)


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


def _no_order_migration() -> tuple[bool, str]:
    versions_dir = BACKEND_ROOT / "alembic" / "versions"
    for path in sorted(versions_dir.glob("*.py")):
        if path.name.startswith("0010_"):
            return False, f"unexpected migration {path.name}"
        text = path.read_text(encoding="utf-8").lower()
        for marker in ORDER_MIGRATION_MARKERS:
            if marker.lower() in text:
                return False, f"{marker} in {path.name}"
    return True, f"head={EXPECTED_HEAD}"


def _no_order_api() -> tuple[bool, str]:
    routes_dir = BACKEND_ROOT / "app" / "api" / "v1" / "routes"
    if (routes_dir / "orders.py").is_file():
        return False, "routes/orders.py exists"
    router_path = BACKEND_ROOT / "app" / "api" / "v1" / "router.py"
    if router_path.is_file():
        router_text = router_path.read_text(encoding="utf-8")
        if "from app.api.v1.routes import orders" in router_text or "orders.router" in router_text:
            return False, "orders router registered"
    models_dir = BACKEND_ROOT / "app" / "models"
    for path in models_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "class CustomerOrder" in text:
            return False, f"CustomerOrder in {path.name}"
    return True, "no order routes/models"


def _safety_documented() -> tuple[bool, str]:
    design_doc = REPO_ROOT / "docs" / "phase3" / "d7_1_order_schema_api_design_review.md"
    if not design_doc.is_file():
        return False, "design doc missing"
    text = design_doc.read_text(encoding="utf-8")
    missing = [m for m in SAFETY_SECTION_MARKERS if m not in text]
    if missing:
        return False, f"missing: {missing[0]}"
    return True, "safety rules documented"


def main() -> int:
    print("D7.1 Design Readiness Check")

    checks = [
        Check("D6 closure docs"),
        Check("D7 readiness brief"),
        Check("D7.1 design doc"),
        Check("phase3 roadmap"),
        Check("no order implementation"),
        Check("no migration"),
        Check("safety boundaries"),
    ]

    d6_ok = all(
        p.is_file()
        for _, p in REQUIRED_DOCS[:2]  # release + capability map
    ) and (REPO_ROOT / "docs" / "records" / "d6_final_closure_20260523.md").is_file()
    if d6_ok:
        checks[0].pass_("d6 final release + closure")
    else:
        checks[0].fail("missing D6 closure artifact")

    brief = REPO_ROOT / "docs" / "phase3" / "d7_order_module_readiness_brief.md"
    if brief.is_file():
        checks[1].pass_()
    else:
        checks[1].fail("missing")

    design = REPO_ROOT / "docs" / "phase3" / "d7_1_order_schema_api_design_review.md"
    if design.is_file() and "customer_orders" in design.read_text(encoding="utf-8"):
        checks[2].pass_("schema + API design")
    else:
        checks[2].fail("missing or incomplete")

    roadmap = REPO_ROOT / "docs" / "phase3" / "phase3_roadmap.md"
    if roadmap.is_file() and "D7.2" in roadmap.read_text(encoding="utf-8"):
        checks[3].pass_()
    else:
        checks[3].fail("missing or incomplete")

    mig_ok, mig_detail = _no_order_migration()
    api_ok, api_detail = _no_order_api()
    if mig_ok and api_ok:
        checks[4].pass_(api_detail)
        checks[5].pass_(mig_detail)
    else:
        if not mig_ok:
            checks[5].fail(mig_detail)
            checks[4].fail("migration present") if not api_ok else checks[4].pass_(api_detail)
        elif not api_ok:
            checks[4].fail(api_detail)
            checks[5].pass_(mig_detail)
        else:
            checks[4].fail("unknown")
            checks[5].fail("unknown")

    settings = get_settings()
    current, head, _ = get_migration_revisions(settings)
    if current != head:
        checks[5].fail(f"current={current} head={head}")
    elif checks[5].ok:
        checks[5].pass_(head or EXPECTED_HEAD)

    safety_ok, safety_detail = _safety_documented()
    if safety_ok:
        checks[6].pass_(safety_detail)
    else:
        checks[6].fail(safety_detail)

    for c in checks:
        print(c.line())
    passed = all(c.ok for c in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
