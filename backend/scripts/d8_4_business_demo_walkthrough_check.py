"""D8.4 business demo walkthrough static check.

This check validates the demo and sales-kit artifacts without creating data,
proof records, staging evidence, or external requests.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Check:
    label: str
    ok: bool = False
    detail: str = ""

    def pass_(self, detail: str = "") -> None:
        self.ok = True
        self.detail = detail

    def fail(self, detail: str) -> None:
        self.ok = False
        self.detail = detail

    def line(self) -> str:
        suffix = f" ({self.detail})" if self.detail else ""
        return f"[{'PASS' if self.ok else 'FAIL'}] {self.label}{suffix}"


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8")


def contains_all(text: str, markers: tuple[str, ...]) -> tuple[bool, str]:
    lower = text.lower()
    missing = [marker for marker in markers if marker.lower() not in lower]
    return not missing, ", ".join(missing)


def main() -> int:
    checks = [
        Check("/demo-walkthrough business story"),
        Check("HOSUN and JOOBOO scenarios"),
        Check("Portal Operations value copy"),
        Check("Market Response explanation copy"),
        Check("Order Detail customer-visible summary"),
        Check("sales operating kit"),
        Check("handoff and no-D9 safety boundary"),
    ]

    try:
        demo = read("frontend/src/pages/demo/DemoWalkthroughPage.vue")
        portal = read("frontend/src/pages/system/PortalOperationsPage.vue")
        market = read("frontend/src/pages/market/MarketPage.vue")
        order = read("frontend/src/pages/orders/OrderDetailPage.vue")
        d84_doc = read("docs/phase3/d8_4_business_demo_walkthrough.md")
        sales_kit = read("docs/demo/sales_operating_kit.md")
    except OSError as exc:
        checks[0].fail(str(exc))
        for check in checks:
            print(check.line())
        return 1

    ok, missing = contains_all(
        demo,
        (
            "customer development",
            "product adaptation",
            "quote",
            "order",
            "partner split",
            "production",
            "shipment",
            "Portal",
            "feedback",
            "market response",
        ),
    )
    checks[0].pass_("full loop present") if ok else checks[0].fail(missing)

    ok, missing = contains_all(demo + d84_doc + sales_kit, ("HOSUN", "JOOBOO", "lifting systems", "education furniture"))
    checks[1].pass_("two partner directions present") if ok else checks[1].fail(missing)

    ok, missing = contains_all(portal, ("Customer Portal operating value", "product", "order", "production", "shipment", "feedback"))
    checks[2].pass_("Portal value copy present") if ok else checks[2].fail(missing)

    ok, missing = contains_all(market, ("Why operators should care", "Demand fit", "Customer friction", "Partner focus"))
    checks[3].pass_("market explanation present") if ok else checks[3].fail(missing)

    ok, missing = contains_all(order, ("Current customer-facing step", "Portal safe", "customerVisibleSummary"))
    checks[4].pass_("customer status demo copy present") if ok else checks[4].fail(missing)

    ok, missing = contains_all(sales_kit, ("PartnerOS Sales Operating Kit", "Recommended Demo Path", "Demo Safety Script"))
    checks[5].pass_("sales kit present") if ok else checks[5].fail(missing)

    combined = "\n".join([demo, portal, market, order, d84_doc, sales_kit])
    unsafe = "Status: STAGING_VALIDATED" in combined or "D9 is ready" in combined
    if "READY_FOR_STAGING_HANDOFF" in combined and not unsafe:
        checks[6].pass_("handoff only; no staging validation claim")
    else:
        checks[6].fail("missing READY_FOR_STAGING_HANDOFF or unsafe staging/D9 wording")

    print("D8.4 Business Demo Walkthrough Check")
    for check in checks:
        print(check.line())
    failed = [check for check in checks if not check.ok]
    print("Result: " + ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
