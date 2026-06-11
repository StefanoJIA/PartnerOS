"""D8.18 partner rehearsal package check."""

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


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _contains_all(text: str, markers: tuple[str, ...]) -> tuple[bool, str]:
    missing = [marker for marker in markers if marker not in text]
    return not missing, ", ".join(missing)


def main() -> int:
    checks = [
        Check("D8.18 document files"),
        Check("10-15 minute script route"),
        Check("HOSUN JOOBOO future partner narratives"),
        Check("partner feedback form"),
        Check("pre-demo checklist and staging boundary"),
        Check("safety boundary and no forbidden status claims"),
        Check("demo README links"),
    ]

    required_files = (
        "docs/demo/d8_18_partner_rehearsal_pack.md",
        "docs/demo/d8_18_partner_feedback_form.md",
        "docs/demo/d8_18_demo_script_final.md",
    )
    missing_files = [path for path in required_files if not (ROOT / path).exists()]
    if missing_files:
        checks[0].fail(", ".join(missing_files))
    else:
        checks[0].pass_("partner rehearsal pack, feedback form, and final script exist")

    pack = _read("docs/demo/d8_18_partner_rehearsal_pack.md")
    feedback = _read("docs/demo/d8_18_partner_feedback_form.md")
    script = _read("docs/demo/d8_18_demo_script_final.md")
    readme = _read("docs/demo/README.md")
    combined = "\n".join([pack, feedback, script])

    ok, missing = _contains_all(
        script,
        (
            "10-15 minutes",
            "Workbench",
            "Customer Development",
            "Growth Operations / Campaign",
            "Manual Outreach",
            "Quote",
            "Order Detail",
            "Customer Portal Operations",
            "Feedback Tickets",
            "Market Response",
            "Partner Onboarding",
        ),
    )
    checks[1].pass_("final demo script covers required route") if ok else checks[1].fail(missing)

    ok, missing = _contains_all(
        combined,
        (
            "HOSUN",
            "lifting systems",
            "desk frames",
            "desk legs",
            "lifting columns",
            "heavy-duty supply",
            "load",
            "stability",
            "noise",
            "JOOBOO",
            "education furniture",
            "school desks and chairs",
            "project furniture",
            "future partner",
            "Chongqing Huiju",
            "not a HOSUN-only",
            "multi-brand agent operating system",
        ),
    )
    checks[2].pass_("partner-specific narratives present") if ok else checks[2].fail(missing)

    ok, missing = _contains_all(
        feedback,
        (
            "Positioning",
            "Demo Flow",
            "Campaign / Growth Operations",
            "Customer Portal Interest",
            "Order / Production / Shipment Tracking",
            "Feedback and Market Response",
            "Partner Fit",
            "Next Step",
            "Are you willing to enter staging UAT or a pilot?",
        ),
    )
    checks[3].pass_("feedback form covers positioning, flow, interest, and pilot readiness") if ok else checks[3].fail(missing)

    ok, missing = _contains_all(
        pack,
        (
            "Pre-Demo Checklist",
            "Backend is available on `http://127.0.0.1:8014`",
            "Frontend is available on `http://127.0.0.1:5173`",
            "VITE_API_PROXY_TARGET=http://127.0.0.1:8014",
            "READY_FOR_STAGING_HANDOFF",
            "Backend HTTPS origin",
            "PORTAL_CUSTOMER_API_TOKEN",
            "PORTAL_CUSTOMER_ALLOWED_ORIGINS",
            "PUBLIC_BASE_URL",
        ),
    )
    checks[4].pass_("pre-demo checklist and staging env boundary present") if ok else checks[4].fail(missing)

    ok, missing = _contains_all(
        combined,
        (
            "does not automatically send email, SMS, LinkedIn messages, or customer notifications",
            "does not automatically change quote or order status",
            "does not connect real Constant Contact or sales CRM APIs",
            "Token values and `.env` files must not be committed",
            "Local rehearsal does not equal real external staging validation",
            "no D9 entry",
            "no proof record expansion",
        ),
    )
    forbidden = [
        marker
        for marker in (
            "Status: STAGING_VALIDATED",
            "Current state: STAGING_VALIDATED",
            "D9 is entered",
            "proof record created",
            "auto-send enabled",
            "customer notifications enabled",
        )
        if marker in combined
    ]
    if not ok:
        checks[5].fail(missing)
    elif forbidden:
        checks[5].fail(", ".join(forbidden))
    else:
        checks[5].pass_("safety boundary present; no forbidden status claim")

    ok, missing = _contains_all(
        readme,
        (
            "d8_18_partner_rehearsal_pack.md",
            "d8_18_demo_script_final.md",
            "d8_18_partner_feedback_form.md",
        ),
    )
    checks[6].pass_("D8.18 materials linked from docs/demo README") if ok else checks[6].fail(missing)

    for check in checks:
        print(check.line())
    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.18 partner rehearsal check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1
    print("\nD8.18 partner rehearsal check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
