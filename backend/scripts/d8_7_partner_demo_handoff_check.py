"""D8.7 partner demo and staging handoff package check."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

DOCS = {
    "partner demo script": ROOT / "docs/demo/partner_demo_script.md",
    "value proposition": ROOT / "docs/demo/partneros_value_proposition.md",
    "staging handoff checklist": ROOT / "docs/demo/service_portal_staging_handoff_checklist.md",
    "HOSUN/JOOBOO narrative": ROOT / "docs/demo/hosun_jooboo_demo_narrative.md",
    "demo index": ROOT / "docs/demo/README.md",
}


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


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _contains_all(text: str, markers: tuple[str, ...]) -> tuple[bool, str]:
    lower = text.lower()
    missing = [marker for marker in markers if marker.lower() not in lower]
    return not missing, ", ".join(missing)


def main() -> int:
    checks = [
        Check("required docs exist"),
        Check("partner demo script flow"),
        Check("PartnerOS value proposition"),
        Check("service portal staging handoff"),
        Check("HOSUN/JOOBOO narrative"),
        Check("source-of-truth boundary"),
        Check("handoff-only state boundary"),
        Check("no forbidden artifact instructions"),
    ]

    missing_docs = [label for label, path in DOCS.items() if not path.exists()]
    if missing_docs:
        checks[0].fail(", ".join(missing_docs))
        for check in checks:
            print(check.line())
        return 1
    checks[0].pass_(f"{len(DOCS)} doc(s)")

    texts = {label: _read(path) for label, path in DOCS.items()}
    combined = "\n".join(texts.values())

    ok, missing = _contains_all(
        texts["partner demo script"],
        (
            "10 to 15 minutes",
            "PartnerOS",
            "/demo-walkthrough",
            "HOSUN",
            "JOOBOO",
            "Portal Operations",
            "Market Response",
            "Featured Order Detail",
            "Feedback Tickets",
            "staging UAT",
        ),
    )
    checks[1].pass_("ordered walkthrough present") if ok else checks[1].fail(missing)

    ok, missing = _contains_all(
        texts["value proposition"],
        (
            "traditional export-agent problem",
            "customer development",
            "quote",
            "order",
            "partner split",
            "production",
            "shipment",
            "feedback",
            "market response",
            "not a single CRM",
            "multi-brand",
        ),
    )
    checks[2].pass_("business value present") if ok else checks[2].fail(missing)

    ok, missing = _contains_all(
        texts["staging handoff checklist"],
        (
            "Backend HTTPS origin",
            "PORTAL_CUSTOMER_API_TOKEN",
            "PORTAL_CUSTOMER_ALLOWED_ORIGINS",
            "PUBLIC_BASE_URL",
            "Products",
            "Order",
            "Production",
            "Shipment",
            "Resources",
            "Feedback",
            "forbidden-field",
        ),
    )
    checks[3].pass_("staging handoff requirements present") if ok else checks[3].fail(missing)

    ok, missing = _contains_all(
        texts["HOSUN/JOOBOO narrative"],
        (
            "HOSUN",
            "JOOBOO",
            "desk frames",
            "desk legs",
            "lifting columns",
            "heavy-duty lifting systems",
            "education furniture",
            "project furniture",
            "multiple premium export brands",
        ),
    )
    checks[4].pass_("two partner narratives present") if ok else checks[4].fail(missing)

    ok, missing = _contains_all(
        combined,
        (
            "PartnerOS is the internal source of truth",
            "service.intelli-opus.com",
            "customer-facing Portal",
        ),
    )
    checks[5].pass_("PartnerOS/Portal boundary present") if ok else checks[5].fail(missing)

    unsafe_status = "Status: STAGING_VALIDATED" in combined or "D9 is ready" in combined
    if "READY_FOR_STAGING_HANDOFF" in combined and not unsafe_status:
        checks[6].pass_("READY_FOR_STAGING_HANDOFF only")
    else:
        checks[6].fail("unsafe staging or D9 status wording")

    forbidden = (".env", "local_data/", "backend/storage/", "IE Auto.pdf")
    ok, missing = _contains_all(combined, forbidden)
    if ok and "Do not commit token values" in combined:
        checks[7].pass_("sensitive artifact warnings present")
    else:
        checks[7].fail(missing or "missing token warning")

    print("D8.7 Partner Demo Handoff Check")
    for check in checks:
        print(check.line())
    failed = [check for check in checks if not check.ok]
    print("Result: " + ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

