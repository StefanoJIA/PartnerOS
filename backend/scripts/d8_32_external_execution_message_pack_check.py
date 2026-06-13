"""D8.32 external execution message pack documentation check."""

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


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def contains_all(text: str, markers: tuple[str, ...]) -> tuple[bool, str]:
    missing = [marker for marker in markers if marker not in text]
    return not missing, ", ".join(missing)


def main() -> int:
    checks = [
        Check("D8.32 required files"),
        Check("external execution message pack"),
        Check("staging credentials request message"),
        Check("security review request message"),
        Check("business UAT signoff message"),
        Check("partner rehearsal message"),
        Check("external action tracker dry-run"),
        Check("HOSUN/JOOBOO/future partner coverage"),
        Check("handoff boundary and no forbidden claims"),
        Check("D8.31/D8.30 continuity"),
    ]

    required_files = (
        "docs/phase3/d8_32_external_execution_message_pack.md",
        "docs/phase3/d8_32_staging_credentials_request_message.md",
        "docs/phase3/d8_32_security_review_request_message.md",
        "docs/phase3/d8_32_business_uat_signoff_message.md",
        "docs/demo/d8_32_partner_rehearsal_message.md",
        "docs/phase3/d8_32_external_action_tracker_dry_run.md",
    )
    missing_files = [path for path in required_files if not (ROOT / path).exists()]
    if missing_files:
        checks[0].fail(", ".join(missing_files))
        for check in checks:
            print(check.line())
        return 1
    checks[0].pass_("message pack, four message templates, and tracker dry-run exist")

    pack = read(required_files[0])
    credentials = read(required_files[1])
    security = read(required_files[2])
    business = read(required_files[3])
    rehearsal = read(required_files[4])
    tracker = read(required_files[5])
    combined = "\n".join([pack, credentials, security, business, rehearsal, tracker])

    ok, missing = contains_all(
        pack,
        (
            "partner rehearsal request",
            "business UAT / data sign-off request",
            "security review request",
            "staging credentials request",
            "Purpose",
            "Recipient Role",
            "Send Prerequisites",
            "Attachments / Reference Docs",
            "Expected Reply",
            "Must Not Include",
        ),
    )
    checks[1].pass_("message pack summarizes four external action templates") if ok else checks[1].fail(missing)

    ok, missing = contains_all(
        credentials,
        (
            "Backend HTTPS origin",
            "service.intelli-opus.com real origin",
            "PORTAL_CUSTOMER_API_ENABLED",
            "PORTAL_CUSTOMER_API_TOKEN",
            "PORTAL_CUSTOMER_ALLOWED_ORIGINS",
            "PUBLIC_BASE_URL",
            "Planned staging window",
            "Rollback owner",
            "Do not paste raw token values",
            "secure channel",
        ),
    )
    checks[2].pass_("staging credentials request covers required credentials and token handling") if ok else checks[2].fail(missing)

    ok, missing = contains_all(
        security,
        (
            "Token storage / rotation / revocation",
            "CORS / allowed origins / no wildcard",
            "Forbidden field audit",
            "Logs / screenshots / docs secret exposure",
            "No automatic external sending",
            "No quote/order auto-change",
            "Rollback / disable Portal API",
            "No real security approval recorded",
        ),
    )
    checks[3].pass_("security review request covers required review areas") if ok else checks[3].fail(missing)

    ok, missing = contains_all(
        business,
        (
            "Customer-visible fields",
            "Forbidden fields",
            "Approved products",
            "Approved customers",
            "Approved orders",
            "Approved feedback records",
            "Approved resources",
            "Pilot partner",
            "Pilot product family",
            "Pilot customer segment",
            "load",
            "stability",
            "noise",
            "warranty",
            "test cycle",
            "certification",
            "Pending must not be written as approved",
        ),
    )
    checks[4].pass_("business UAT message requests required field/product/pilot signoff") if ok else checks[4].fail(missing)

    ok, missing = contains_all(
        rehearsal,
        (
            "PartnerOS",
            "10-15 minute walkthrough",
            "HOSUN",
            "JOOBOO",
            "future partner",
            "Campaign",
            "manual outreach",
            "Quote",
            "order",
            "Customer Portal",
            "Feedback",
            "Market Response",
            "feedback form",
            "does not automatically send",
            "does not connect to real external APIs",
            "does not automatically change quote/order/shipment status",
        ),
    )
    checks[5].pass_("partner rehearsal message includes positioning, flow, feedback, and safety boundaries") if ok else checks[5].fail(missing)

    ok, missing = contains_all(
        tracker,
        (
            "No external message has been sent from this dry-run.",
            "Action ID",
            "Action Type",
            "Owner Role",
            "Target",
            "Dependency",
            "Expected Response",
            "Next Step",
            "Status",
            "status=pending",
            "pending",
            "Do not fabricate replies",
        ),
    )
    checks[6].pass_("tracker dry-run uses placeholder actions and pending status") if ok else checks[6].fail(missing)

    ok, missing = contains_all(
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
            "delivery",
            "installation",
            "after-sales",
            "packaging",
            "warranty",
            "test cycle",
            "certification",
            "project demand",
            "customer-safe",
            "internal-only",
            "JOOBOO",
            "education furniture",
            "school desks/chairs",
            "project furniture",
            "future partner onboarding data",
            "product family",
            "quote logic",
            "delivery requirement",
            "resource taxonomy",
            "customer-visible fields",
            "Market Response metrics",
        ),
    )
    checks[7].pass_("HOSUN/JOOBOO/future partner messaging coverage present") if ok else checks[7].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "Template only; not sent",
            "No external message has been sent",
            "Do not write STAGING_VALIDATED",
            "Do not enter D9",
            "Do not create proof records",
            "Do not fabricate credentials",
            "Do not fabricate credentials, evidence, sign-off, or partner feedback",
            "Do not process or record real token values",
            "Pending does not mean complete or approved",
        ),
    )
    forbidden = [
        marker
        for marker in (
            "Current state: STAGING_VALIDATED",
            "External staging state: STAGING_VALIDATED",
            "Status: STAGING_VALIDATED",
            "proof record created",
            "D9 entered",
            "D9 status: entered",
            "real staging validated: yes",
            "production ready",
            "real credentials received",
            "real staging evidence recorded: yes",
            "partner feedback complete",
            "message sent: yes",
            "status=complete",
            "status=approved",
        )
        if marker in combined
    ]
    if forbidden:
        checks[8].fail(", ".join(forbidden))
    elif not ok:
        checks[8].fail(missing)
    else:
        checks[8].pass_("handoff boundary retained; no send/D9/STAGING_VALIDATED/fabricated claim")

    continuity_paths = (
        "docs/phase3/d8_31_external_execution_packet.md",
        "docs/phase3/d8_31_next_external_actions_tracker.md",
        "docs/phase3/d8_30_d9_entry_gate.md",
        "docs/phase3/d8_29_staging_validation_boundary.md",
    )
    try:
        continuity = "\n".join(read(path) for path in continuity_paths)
        ok, missing = contains_all(
            continuity,
            (
                "READY_FOR_STAGING_HANDOFF",
                "WAITING_FOR_REAL_STAGING_EVIDENCE",
                "Do not write STAGING_VALIDATED",
                "D9 remains blocked",
                "HOSUN",
                "JOOBOO",
            ),
        )
        checks[9].pass_("D8.31/D8.30/D8.29 source docs remain aligned") if ok else checks[9].fail(missing)
    except FileNotFoundError as exc:
        checks[9].fail(str(exc))

    for check in checks:
        print(check.line())

    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.32 external execution message pack check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1

    print("\nD8.32 external execution message pack check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
