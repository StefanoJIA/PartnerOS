"""D8.20 staging handoff contract documentation check."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs" / "phase3" / "d8_20_staging_handoff_contract.md"


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
        Check("D8.20 handoff contract exists"),
        Check("status boundary"),
        Check("required staging configuration"),
        Check("responsibility matrix"),
        Check("customer-safe and forbidden fields"),
        Check("staging smoke test flow"),
        Check("rollback and disable flow"),
        Check("pre-pilot prohibitions"),
        Check("HOSUN lifting systems field preparation"),
        Check("multi-partner expansion preparation"),
        Check("no forbidden positive claims"),
    ]

    if not CONTRACT.exists():
        checks[0].fail(str(CONTRACT))
        for check in checks:
            print(check.line())
        return 1

    text = CONTRACT.read_text(encoding="utf-8")
    checks[0].pass_("docs/phase3/d8_20_staging_handoff_contract.md")

    ok, missing = contains_all(
        text,
        (
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "Do not write a real staging validated status",
            "Do not enter D9",
            "Do not add proof records",
            "Do not treat local rehearsal as external staging validation",
        ),
    )
    checks[1].pass_("handoff-only status boundary present") if ok else checks[1].fail(missing)

    ok, missing = contains_all(
        text,
        (
            "Backend HTTPS origin",
            "`PORTAL_CUSTOMER_API_ENABLED`",
            "`PORTAL_CUSTOMER_API_TOKEN`",
            "`PORTAL_CUSTOMER_ALLOWED_ORIGINS`",
            "`PUBLIC_BASE_URL`",
            "`service.intelli-opus.com` real origin",
            "CORS allowlist",
            "server-to-server",
        ),
    )
    checks[2].pass_("real staging config requirements present") if ok else checks[2].fail(missing)

    ok, missing = contains_all(
        text,
        (
            "intelliOffice Backend Operator",
            "`service.intelli-opus.com` Portal Operator",
            "Infrastructure / Deployment Operator",
            "Business Owner",
            "Security Reviewer",
            "Provides:",
            "Verifies:",
        ),
    )
    checks[3].pass_("responsibility owners and duties present") if ok else checks[3].fail(missing)

    ok, missing = contains_all(
        text,
        (
            "Products:",
            "Orders:",
            "Production milestones:",
            "Shipment status:",
            "Resources:",
            "Feedback status:",
            "Customer-safe market signal preview:",
            "Cost.",
            "Margin.",
            "Pricing breakdown.",
            "Supplier private notes.",
            "Backend file paths.",
            "Storage keys.",
            "Token values.",
            "Internal-only comments.",
            "Private partner notes.",
            "Raw database IDs if not customer-safe.",
        ),
    )
    checks[4].pass_("customer-safe and forbidden field contract present") if ok else checks[4].fail(missing)

    ok, missing = contains_all(
        text,
        (
            "Backend health",
            "Portal bridge readiness",
            "Token auth success",
            "Wrong token rejected",
            "Disallowed origin rejected",
            "Customer-safe order list",
            "Order detail field whitelist",
            "Resources download manifest",
            "Feedback submit/read boundary",
            "Forbidden fields absent",
            "No automatic external messages",
            "No quote/order status auto-change",
        ),
    )
    checks[5].pass_("staging smoke sequence present") if ok else checks[5].fail(missing)

    ok, missing = contains_all(
        text,
        (
            "Set `PORTAL_CUSTOMER_API_ENABLED=false`",
            "Remove the current `PORTAL_CUSTOMER_API_TOKEN`",
            "Set `PORTAL_CUSTOMER_ALLOWED_ORIGINS` to an empty value",
            "Return to Internal-Only Mode",
            "Staging failure must not affect the local release candidate",
            "PartnerOS internal source of truth",
        ),
    )
    checks[6].pass_("rollback/disable flow present") if ok else checks[6].fail(missing)

    ok, missing = contains_all(
        text,
        (
            "Do not automatically send email.",
            "Do not automatically send SMS.",
            "Do not automatically send LinkedIn messages.",
            "Do not automatically notify customers.",
            "Do not connect real Constant Contact APIs.",
            "Do not connect real sales CRM",
            "Do not automatically change quote status.",
            "Do not automatically change order status.",
            "Do not expose cost, margin, pricing breakdown",
            "Do not commit `.env`, token values, PDFs, `local_data/`, `backend/storage/`, `IE Auto.pdf`, or `docs/activity_actions.md`.",
            "Do not claim production ready.",
        ),
    )
    checks[7].pass_("pre-pilot prohibitions present") if ok else checks[7].fail(missing)

    ok, missing = contains_all(
        text,
        (
            "HOSUN Lifting Systems Field Preparation",
            "lifting systems",
            "desk frames",
            "desk legs",
            "lifting columns",
            "heavy-duty supply",
            "load",
            "stability",
            "noise",
            "delivery",
            "installation",
            "after-sales",
            "project demand",
            "warranty",
            "test cycle",
            "certification",
            "packaging",
            "Customer-Safe HOSUN Fields",
            "Internal-Only HOSUN Fields",
        ),
    )
    checks[8].pass_("HOSUN customer-safe/internal-only field split present") if ok else checks[8].fail(missing)

    ok, missing = contains_all(
        text,
        (
            "HOSUN, JOOBOO, Chongqing Huiju, and future partners",
            "Shared Portal bridge surfaces",
            "Partner-specific configuration",
            "Product fields.",
            "Quote logic.",
            "Delivery requirements.",
            "Resource taxonomy.",
            "Market Response metrics.",
            "Do not hardcode one partner's product assumptions",
        ),
    )
    checks[9].pass_("multi-partner shared bridge and partner-specific rules present") if ok else checks[9].fail(missing)

    forbidden_positive_claims = [
        marker
        for marker in (
            "Current state: STAGING_VALIDATED",
            "Status: STAGING_VALIDATED",
            "External staging state: STAGING_VALIDATED",
            "D9 entered",
            "D9 is ready",
            "proof record created",
            "Status: production ready",
            "Current state: production ready",
            "This is production ready",
        )
        if marker in text
    ]
    if forbidden_positive_claims:
        checks[10].fail(", ".join(forbidden_positive_claims))
    else:
        checks[10].pass_("no D9/proof/validated positive claim")

    for check in checks:
        print(check.line())

    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.20 staging handoff contract check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1

    print("\nD8.20 staging handoff contract check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
