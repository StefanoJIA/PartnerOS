"""D7.5.1 Existing cloud portal integration review check."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import log_backend_base_url
from app.core.config import get_settings
from app.core.database_lifecycle import get_migration_revisions

DOC = REPO_ROOT / "docs" / "phase3" / "d7_5_1_existing_cloud_portal_integration_review.md"
VERSIONS_DIR = BACKEND_ROOT / "alembic" / "versions"

FORBIDDEN_NEW_TABLES = ("feedback_tickets", "portal_customer_sessions")


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


def _migration_ok() -> tuple[bool, str]:
    settings = get_settings()
    current, head, _ = get_migration_revisions(settings)
    if current != head:
        return False, f"current={current} head={head}"
    if head not in ("0013_prod_milestones", "0014_shipment_plans"):
        return False, f"unexpected head={head}"
    return True, head or "unknown"


def _no_new_migrations() -> tuple[bool, str]:
    unexpected = [p.name for p in VERSIONS_DIR.glob("*.py") if p.name.startswith(("0015_", "0016_", "0017_", "0018_", "0019_"))]
    if unexpected:
        return False, f"unexpected migration found: {unexpected[0]}"
    return True, "no portal/feedback migration beyond D7.6"


def _no_forbidden_tables_in_migrations() -> tuple[bool, str]:
    for path in VERSIONS_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for tbl in FORBIDDEN_NEW_TABLES:
            if tbl in text:
                return False, f"{tbl} in {path.name}"
    return True, "no feedback/portal tables"


def main() -> int:
    log_backend_base_url()
    print("D7.5.1 Portal Integration Review Check")
    checks = [
        Check("review document exists"),
        Check("doc covers product selection"),
        Check("doc covers tracking"),
        Check("doc covers feedback"),
        Check("doc covers resources"),
        Check("doc contains PartnerOS mapping"),
        Check("doc contains D7.6 / D7.7 / D7.8 route"),
        Check("migration at D7.5.1/D7.6 head"),
        Check("no migration beyond D7.6"),
        Check("no feedback/portal tables"),
        Check("final judgment A"),
    ]

    if DOC.is_file():
        checks[0].pass_(str(DOC.name))
        text = DOC.read_text(encoding="utf-8").lower()
        checks[1].pass_() if "product selection" in text or "商品选购" in text else checks[1].fail("missing")
        checks[2].pass_() if "tracking" in text or "物流" in text or "order tracking" in text else checks[2].fail("missing")
        checks[3].pass_() if "feedback" in text or "反馈" in text else checks[3].fail("missing")
        checks[4].pass_() if "resource" in text or "download" in text or "下载" in text else checks[4].fail("missing")
        checks[5].pass_() if "product_catalog" in text and "customer_orders" in text else checks[5].fail("missing")
        route_ok = all(x in text for x in ("d7.6", "d7.7", "d7.8"))
        checks[6].pass_() if route_ok else checks[6].fail("missing stages")
        if "judgment" in text and "retained as customer-facing" in text:
            checks[10].pass_()
        else:
            checks[10].fail("not A")
    else:
        for c in checks[:7]:
            c.fail("doc missing")
        checks[10].fail("doc missing")

    mig_ok, mig_detail = _migration_ok()
    checks[7].pass_(mig_detail) if mig_ok else checks[7].fail(mig_detail)

    nm_ok, nm_detail = _no_new_migrations()
    checks[8].pass_(nm_detail) if nm_ok else checks[8].fail(nm_detail)

    tbl_ok, tbl_detail = _no_forbidden_tables_in_migrations()
    checks[9].pass_(tbl_detail) if tbl_ok else checks[9].fail(tbl_detail)

    for c in checks:
        print(c.line())
    passed = all(c.ok for c in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
