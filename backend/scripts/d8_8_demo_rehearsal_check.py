"""D8.8 demo rehearsal and staging credential request check."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

DOCS = {
    "demo rehearsal checklist": ROOT / "docs/demo/d8_8_demo_rehearsal_checklist.md",
    "staging credentials request pack": ROOT / "docs/demo/staging_credentials_request_pack.md",
    "demo index": ROOT / "docs/demo/README.md",
    "partner demo script": ROOT / "docs/demo/partner_demo_script.md",
    "HOSUN/JOOBOO narrative": ROOT / "docs/demo/hosun_jooboo_demo_narrative.md",
    "value proposition": ROOT / "docs/demo/partneros_value_proposition.md",
    "demo walkthrough page": ROOT / "frontend/src/pages/demo/DemoWalkthroughPage.vue",
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
        Check("required docs and page exist"),
        Check("rehearsal checklist covers real demo flow"),
        Check("staging credential request covers private values"),
        Check("demo script and page stay aligned"),
        Check("HOSUN/JOOBOO narrative supports rehearsal"),
        Check("value proposition supports premium export-brand agency positioning"),
        Check("handoff-only state boundary"),
        Check("sensitive artifact and token boundary"),
        Check("demo index links D8.8 materials"),
    ]

    missing_docs = [label for label, path in DOCS.items() if not path.exists()]
    if missing_docs:
        checks[0].fail(", ".join(missing_docs))
        for check in checks:
            print(check.line())
        return 1
    checks[0].pass_(f"{len(DOCS)} artifact(s)")

    texts = {label: _read(path) for label, path in DOCS.items()}
    combined_docs = "\n".join(
        text for label, text in texts.items() if label != "demo walkthrough page"
    )

    ok, missing = _contains_all(
        texts["demo rehearsal checklist"],
        (
            "10 to 15 minute",
            "Pre-Demo Startup",
            "Login",
            "/demo-walkthrough",
            "HOSUN Lifting Systems",
            "JOOBOO Education Furniture",
            "Portal Operations",
            "Market Response",
            "Order Detail",
            "Feedback Tickets",
            "Common Questions",
            "Finish Within 15 Minutes",
            "Backup Paths",
        ),
    )
    checks[1].pass_("ordered rehearsal flow present") if ok else checks[1].fail(missing)

    ok, missing = _contains_all(
        texts["staging credentials request pack"],
        (
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "Backend HTTPS origin",
            "PORTAL_CUSTOMER_API_TOKEN",
            "PORTAL_CUSTOMER_ALLOWED_ORIGINS",
            "https://service.intelli-opus.com",
            "PUBLIC_BASE_URL",
            "server-to-server token",
            "not be committed to Git",
            "Products",
            "Orders",
            "Production",
            "Shipment",
            "Resources",
            "Feedback",
            "forbidden-field",
        ),
    )
    checks[2].pass_("credential request complete") if ok else checks[2].fail(missing)

    ok, missing = _contains_all(
        texts["demo walkthrough page"] + texts["partner demo script"],
        (
            "/demo-walkthrough",
            "Portal Operations",
            "Market Response",
            "Featured Order Detail",
            "Feedback Tickets",
            "HOSUN",
            "JOOBOO",
        ),
    )
    checks[3].pass_("script/page shared demo anchors present") if ok else checks[3].fail(missing)

    ok, missing = _contains_all(
        texts["HOSUN/JOOBOO narrative"] + texts["demo rehearsal checklist"],
        (
            "desk frames",
            "desk legs",
            "lifting columns",
            "heavy-duty lifting systems",
            "education furniture",
            "project furniture",
            "multiple premium export brands",
        ),
    )
    checks[4].pass_("two partner tracks support rehearsal") if ok else checks[4].fail(missing)

    ok, missing = _contains_all(
        texts["value proposition"] + texts["demo rehearsal checklist"],
        (
            "premium export",
            "agent operating system",
            "not a single CRM",
            "customer development",
            "quote",
            "order",
            "partner split",
            "production",
            "shipment",
            "feedback",
            "market response",
        ),
    )
    checks[5].pass_("business positioning present") if ok else checks[5].fail(missing)

    unsafe_claims = (
        "Status: STAGING_VALIDATED",
        "D9 is ready",
        "proof record created",
        "staging has been validated",
    )
    unsafe_hit = [marker for marker in unsafe_claims if marker.lower() in combined_docs.lower()]
    if "READY_FOR_STAGING_HANDOFF" in combined_docs and not unsafe_hit:
        checks[6].pass_("READY_FOR_STAGING_HANDOFF only")
    else:
        checks[6].fail(", ".join(unsafe_hit) or "missing READY_FOR_STAGING_HANDOFF")

    ok, missing = _contains_all(
        combined_docs,
        (
            ".env",
            "token values",
            "generated PDFs",
            "IE Auto.pdf",
            "local_data/",
            "backend/storage/",
        ),
    )
    checks[7].pass_("sensitive boundary present") if ok else checks[7].fail(missing)

    ok, missing = _contains_all(
        texts["demo index"],
        (
            "D8.8 demo rehearsal checklist",
            "Staging credentials request pack",
        ),
    )
    checks[8].pass_("README links D8.8 docs") if ok else checks[8].fail(missing)

    print("D8.8 Demo Rehearsal Check")
    for check in checks:
        print(check.line())
    failed = [check for check in checks if not check.ok]
    print("Result: " + ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
