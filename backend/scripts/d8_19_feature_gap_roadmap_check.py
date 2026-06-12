"""D8.19 feature gap and roadmap documentation check."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROADMAP = ROOT / "docs" / "phase3" / "d8_19_feature_gap_and_roadmap.md"


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


def contains_all(text: str, markers: tuple[str, ...]) -> tuple[bool, str]:
    missing = [marker for marker in markers if marker not in text]
    return not missing, ", ".join(missing)


def main() -> int:
    checks = [
        Check("D8.19 roadmap document exists"),
        Check("completed capability summary"),
        Check("priority model P0-P3"),
        Check("feature gap fields"),
        Check("required roadmap gaps"),
        Check("HOSUN lifting systems analysis"),
        Check("JOOBOO and multi-partner analysis"),
        Check("handoff boundary and no forbidden claims"),
    ]

    if not ROADMAP.exists():
        checks[0].fail(str(ROADMAP))
        for check in checks:
            print(check.line())
        return 1

    checks[0].pass_("docs/phase3/d8_19_feature_gap_and_roadmap.md")
    text = ROADMAP.read_text(encoding="utf-8")

    ok, missing = contains_all(
        text,
        (
            "Workbench / Daily Operating Map",
            "Customer Development",
            "Growth Operations / Campaign",
            "Manual Outreach",
            "Quote",
            "Order Detail",
            "Production / Shipment",
            "Feedback Tickets",
            "Market Response",
            "Partner Onboarding",
            "Demo / Rehearsal Pack",
            "READY_FOR_STAGING_HANDOFF Boundary",
        ),
    )
    checks[1].pass_("current D8 capabilities summarized") if ok else checks[1].fail(missing)

    ok, missing = contains_all(
        text,
        (
            "P0: must be resolved before real staging / pilot",
            "P1: should be prioritized after partner rehearsal feedback",
            "P2: useful during pilot",
            "P3: longer-term platform capability",
            "P0: Before Real Staging / Pilot",
            "P1: After Partner Rehearsal Feedback",
            "P2: Pilot Enhancements",
            "P3: Long-Term Platform Capabilities",
        ),
    )
    checks[2].pass_("P0/P1/P2/P3 roadmap structure present") if ok else checks[2].fail(missing)

    ok, missing = contains_all(
        text,
        (
            "Business Value",
            "Current Gap",
            "Needs Partner Feedback",
            "Needs Staging Credentials",
            "Can Start With Docs / Prototype",
            "Suggested Stage",
            "D8.x",
            "Pilot",
            "Later",
        ),
    )
    checks[3].pass_("feature table includes required decision fields") if ok else checks[3].fail(missing)

    ok, missing = contains_all(
        text,
        (
            "Real service Portal staging validation",
            "RBAC / role permissions",
            "Audit log / operation audit",
            "Real data import plan",
            "Partner product data and resource center management",
            "Customer Portal deepening",
            "Task / due date / internal reminder / handoff",
            "Quote approval / margin review",
            "Payment / PO / PI / contract workflow",
            "Supplier / partner collaboration",
            "Shipment tracking / carrier integration roadmap",
            "Feedback to Market Response metrics",
            "Analytics dashboard",
            "External integrations roadmap",
            "Backup, monitoring, and security hardening",
        ),
    )
    checks[4].pass_("required feature gaps covered") if ok else checks[4].fail(missing)

    ok, missing = contains_all(
        text,
        (
            "HOSUN Lifting Systems Gap Analysis",
            "lifting systems",
            "desk frames",
            "desk legs",
            "lifting columns",
            "heavy-duty lifting",
            "Load capacity range",
            "Stability requirement",
            "Noise level target",
            "Delivery delay frequency",
            "Installation issue frequency",
            "After-sales issue frequency",
        ),
    )
    checks[5].pass_("HOSUN fields and market response metrics covered") if ok else checks[5].fail(missing)

    ok, missing = contains_all(
        text,
        (
            "JOOBOO Project Furniture Gap Analysis",
            "education furniture",
            "school desks/chairs",
            "project furniture",
            "Project timing risk",
            "Multi-Partner Expansion Analysis",
            "HOSUN, JOOBOO, Chongqing Huiju, and future partners",
            "shared workflow plus partner-specific configuration",
            "Partner-Specific",
            "partner capability profile",
        ),
    )
    checks[6].pass_("JOOBOO and multi-partner expansion covered") if ok else checks[6].fail(missing)

    forbidden = [
        marker
        for marker in (
            "Current state: STAGING_VALIDATED",
            "Status: STAGING_VALIDATED",
            "real external staging validated",
            "proof record created",
            "auto-send enabled",
            "automatically send customer notifications",
        )
        if marker in text
    ]
    ok, missing = contains_all(
        text,
        (
            "Current state: READY_FOR_STAGING_HANDOFF",
            "Local rehearsal does not equal real external staging validation",
            "does not add product modules",
            "does not automatically change order status",
            "service Portal credentials and origin are verified",
        ),
    )
    if forbidden:
        checks[7].fail(", ".join(forbidden))
    elif not ok:
        checks[7].fail(missing)
    else:
        checks[7].pass_("handoff state retained; no forbidden claim")

    for check in checks:
        print(check.line())

    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.19 feature gap roadmap check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1

    print("\nD8.19 feature gap roadmap check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
