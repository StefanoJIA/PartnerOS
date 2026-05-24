"""D6 Final Quote MVP closure check."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import get_backend_base_url, log_backend_base_url
from app.core.config import get_settings
from app.core.database_lifecycle import get_migration_revisions

FORBIDDEN = (
    "order created",
    "production started",
    "shipment created",
    "inventory confirmed",
    "lead time confirmed",
    "delivery guaranteed",
)

REQUIRED_DOCS = (
    ("release doc", REPO_ROOT / "docs" / "releases" / "d6_final_quote_mvp_release_20260523.md"),
    ("capability map", REPO_ROOT / "docs" / "architecture" / "d6_quote_capability_map.md"),
    ("D7 readiness brief", REPO_ROOT / "docs" / "phase3" / "d7_order_module_readiness_brief.md"),
    ("closure record", REPO_ROOT / "docs" / "records" / "d6_final_closure_20260523.md"),
)

CUSTOMER_ORDER_MIGRATION_MARKERS = (
    "customer_orders",
    "create_table(\n        \"orders\"",
    "quote_convert_to_order",
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


def _login(client: httpx.Client, base: str) -> dict[str, str] | None:
    r = client.post(f"{base}/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    if r.status_code != 200:
        return None
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _migration_head_ok() -> tuple[bool, str]:
    settings = get_settings()
    current, head, _ = get_migration_revisions(settings)
    if current == head:
        return True, head or "unknown"
    return False, f"current={current} head={head}"


def _order_mvp_migration_ok() -> tuple[bool, str]:
    versions_dir = BACKEND_ROOT / "alembic" / "versions"
    forbidden_tables = (
        "supplier_confirmations",
        "production_milestones",
        "shipment_plans",
        "order_partner_splits",
    )
    for path in sorted(versions_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8").lower()
        for tbl in forbidden_tables:
            if tbl in text:
                return False, f"{tbl} in {path.name}"
        if path.name.startswith("0012_"):
            return False, f"unexpected migration {path.name}"
    if (versions_dir / "0010_order_crud_mvp.py").is_file():
        t10 = (versions_dir / "0010_order_crud_mvp.py").read_text(encoding="utf-8").lower()
        if "customer_orders" not in t10:
            return False, "0010 missing customer_orders"
    if (versions_dir / "0011_order_customer_confirmations.py").is_file():
        t11 = (versions_dir / "0011_order_customer_confirmations.py").read_text(encoding="utf-8").lower()
        if "order_confirmations" not in t11:
            return False, "0011 missing order_confirmations"
    return True, "0010-0011 order MVP + confirmations only"


def main() -> int:
    base = log_backend_base_url()
    print("D6 Final Closure Check")
    checks = [
        Check("release docs"),
        Check("capability map"),
        Check("D7 readiness brief"),
        Check("closure record"),
        Check("quote APIs"),
        Check("alembic at head"),
        Check("order MVP scope"),
        Check("safety boundaries"),
    ]

    missing = [name for name, path in REQUIRED_DOCS if not path.is_file()]
    if not missing:
        checks[0].pass_("d6_final_quote_mvp_release")
        checks[1].pass_("d6_quote_capability_map")
        checks[2].pass_("d7_order_module_readiness_brief")
        checks[3].pass_("d6_final_closure")
    else:
        for i, (name, path) in enumerate(REQUIRED_DOCS):
            if path.is_file():
                checks[i].pass_(path.name)
            else:
                checks[i].fail(f"missing {path.name}")

    mig_ok, mig_detail = _migration_head_ok()
    if mig_ok:
        checks[5].pass_(mig_detail)
    else:
        checks[5].fail(mig_detail)

    no_order_mig, order_mig_detail = _order_mvp_migration_ok()
    if no_order_mig:
        checks[6].pass_(order_mig_detail)
    else:
        checks[6].fail(order_mig_detail)

    try:
        with httpx.Client(timeout=60.0) as client:
            headers = _login(client, base)
            if not headers:
                checks[4].fail("login failed")
                checks[7].fail("skipped")
            else:
                pr = client.get(f"{base}/api/v1/products?limit=1", headers=headers)
                qr = client.get(f"{base}/api/v1/quotes?limit=1", headers=headers)
                ok_apis = pr.status_code == 200 and qr.status_code == 200
                quote_id = None
                if qr.status_code == 200 and qr.json().get("data", {}).get("items"):
                    quote_id = qr.json()["data"]["items"][0]["id"]

                product_id = None
                if pr.status_code == 200 and pr.json().get("data", {}).get("items"):
                    product_id = pr.json()["data"]["items"][0]["id"]

                if product_id:
                    pp = client.post(
                        f"{base}/api/v1/quotes/pricing/preview",
                        headers=headers,
                        json={"product_id": product_id, "quantity": 10, "incoterm": "FOB"},
                    )
                    ok_apis = ok_apis and pp.status_code == 200

                if quote_id:
                    for suffix in ("pdf-exports", "delivery-logs", "order-readiness"):
                        r = client.get(f"{base}/api/v1/quotes/{quote_id}/{suffix}", headers=headers)
                        ok_apis = ok_apis and r.status_code == 200
                    convert = client.post(f"{base}/api/v1/quotes/{quote_id}/convert-to-order", headers=headers, json={})
                    if convert.status_code not in (404, 405, 501):
                        checks[6].fail(f"convert-to-order HTTP {convert.status_code}")
                        ok_apis = False

                    rr = client.get(f"{base}/api/v1/quotes/{quote_id}/order-readiness", headers=headers)
                    if rr.status_code == 200:
                        safety = rr.json().get("data", {}).get("safety") or {}
                        blob = rr.text.lower()
                        if all(
                            safety.get(k) is False
                            for k in (
                                "order_created",
                                "production_started",
                                "shipment_created",
                                "automatic_sending_enabled",
                            )
                        ) and not any(p in blob for p in FORBIDDEN):
                            checks[7].pass_()
                        else:
                            checks[7].fail(str(safety))
                    else:
                        checks[7].fail(f"readiness HTTP {rr.status_code}")
                else:
                    board = client.get(f"{base}/api/v1/quotes/order-readiness-board", headers=headers)
                    ok_apis = ok_apis and board.status_code == 200
                    checks[7].pass_("no quote sample; board OK") if board.status_code == 200 else checks[7].fail("no quote")

                if ok_apis:
                    checks[4].pass_("products/quotes/pricing/readiness")
                else:
                    checks[4].fail("one or more APIs failed")

    except httpx.ConnectError:
        for c in checks[4:]:
            if not c.ok:
                c.fail("backend unreachable")

    for c in checks:
        print(c.line())
    passed = all(c.ok for c in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
