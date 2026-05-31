"""D7.5.1 Existing cloud portal integration review check."""

from __future__ import annotations

import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import log_backend_base_url

DOC = REPO_ROOT / "docs" / "phase3" / "d7_5_1_existing_cloud_portal_integration_review.md"
VERSIONS_DIR = BACKEND_ROOT / "alembic" / "versions"
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"

FORBIDDEN_NEW_TABLES = ("portal_customer_sessions",)
FORBIDDEN_DOC_MARKERS = (
    "0013_prod_milestones",
    "shipment_plans 仅设计",
    "roadmap 标注 Future",
    "未实现",
    "future `shipment_plans`",
    "鍟",
    "閿",
    "鐗",
    "鈹",
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


def _migration_ok() -> tuple[bool, str]:
    cfg = Config(str(ALEMBIC_INI))
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    if len(heads) != 1:
        return False, f"unexpected heads={heads}"
    head = heads[0]
    if head not in (
        "0013_prod_milestones",
        "0014_shipment_plans",
        "0015_feedback_tickets",
        "0016_feedback_ops",
        "0017_order_resources",
    ):
        return False, f"unexpected head={head}"
    return True, head or "unknown"


def _no_new_migrations() -> tuple[bool, str]:
    unexpected = [p.name for p in VERSIONS_DIR.glob("*.py") if p.name.startswith(("0018_", "0019_"))]
    if unexpected:
        return False, f"unexpected migration found: {unexpected[0]}"
    return True, "no migration beyond D7.9"


def _no_forbidden_tables_in_migrations() -> tuple[bool, str]:
    for path in VERSIONS_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for tbl in FORBIDDEN_NEW_TABLES:
            if tbl in text:
                return False, f"{tbl} in {path.name}"
    return True, "no portal session tables"


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
        Check("doc reflects current implemented bridge state"),
        Check("migration at D7.5.1-D7.9 head"),
        Check("no migration beyond D7.9"),
        Check("no portal session tables"),
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
        current_ok = (
            "0017_order_resources" in text
            and "implemented in d7.6" in text
            and "implemented in d7.7" in text
            and not any(marker.lower() in text for marker in FORBIDDEN_DOC_MARKERS)
        )
        checks[7].pass_() if current_ok else checks[7].fail("stale or mojibake markers")
        if "judgment" in text and "retained as customer-facing" in text:
            checks[11].pass_()
        else:
            checks[11].fail("not A")
    else:
        for c in checks[:8]:
            c.fail("doc missing")
        checks[11].fail("doc missing")

    mig_ok, mig_detail = _migration_ok()
    checks[8].pass_(mig_detail) if mig_ok else checks[8].fail(mig_detail)

    nm_ok, nm_detail = _no_new_migrations()
    checks[9].pass_(nm_detail) if nm_ok else checks[9].fail(nm_detail)

    tbl_ok, tbl_detail = _no_forbidden_tables_in_migrations()
    checks[10].pass_(tbl_detail) if tbl_ok else checks[10].fail(tbl_detail)

    for c in checks:
        print(c.line())
    passed = all(c.ok for c in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
