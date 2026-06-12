"""D8.25 UAT data selection and staging-safe seed documentation check."""

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
        Check("D8.25 required files"),
        Check("UAT data selection plan"),
        Check("staging-safe seed manifest"),
        Check("business owner data sign-off template"),
        Check("customer-safe copy rules"),
        Check("HOSUN staging-safe field coverage"),
        Check("JOOBOO staging-safe field coverage"),
        Check("future partner staging-safe field coverage"),
        Check("handoff boundary and no forbidden claims"),
        Check("D8.24/D8.23 continuity"),
    ]

    required_files = (
        "docs/phase3/d8_25_uat_data_selection_plan.md",
        "docs/phase3/d8_25_staging_safe_seed_manifest.md",
        "docs/phase3/d8_25_business_owner_data_signoff.md",
        "docs/phase3/d8_25_customer_safe_copy_rules.md",
    )
    missing_files = [path for path in required_files if not (ROOT / path).exists()]
    if missing_files:
        checks[0].fail(", ".join(missing_files))
        for check in checks:
            print(check.line())
        return 1
    checks[0].pass_("plan, manifest, sign-off template, and copy rules exist")

    plan = read(required_files[0])
    manifest = read(required_files[1])
    signoff = read(required_files[2])
    copy_rules = read(required_files[3])
    combined = "\n".join([plan, manifest, signoff, copy_rules])

    ok, missing = contains_all(
        plan,
        (
            "business owner",
            "staging, rehearsal, and pilot",
            "unreviewed real customers",
            "real orders",
            "real prices",
            "real supplier notes",
            "products",
            "customers",
            "quotes",
            "orders",
            "production milestones",
            "shipment status",
            "resources",
            "feedback",
            "Market Response preview",
            "customer-safe",
            "internal-only",
            "demo-only",
            "requires approval",
        ),
    )
    checks[1].pass_("plan explains owner selection and data classifications") if ok else checks[1].fail(missing)

    ok, missing = contains_all(
        manifest,
        (
            "No real staging record approved yet",
            "Record ID",
            "Display Name",
            "Partner",
            "HOSUN",
            "JOOBOO",
            "Chongqing Huiju",
            "future partner",
            "Product Family",
            "Customer Segment",
            "Intended Use",
            "demo",
            "rehearsal",
            "staging UAT",
            "pilot",
            "Customer-Visible Fields",
            "Internal-Only Fields",
            "Approval Owner",
            "Approval Status",
            "Risk Notes",
            "Source",
            "demo seed",
            "sanitized real record",
            "synthetic sample",
            "pending",
        ),
    )
    checks[2].pass_("manifest has required template fields and pending state") if ok else checks[2].fail(missing)

    ok, missing = contains_all(
        signoff,
        (
            "No real business owner sign-off recorded yet",
            "Approved Customer-Visible Fields",
            "Forbidden Fields",
            "Approved Products",
            "Approved Customers",
            "Approved Orders",
            "Approved Feedback Records",
            "Approved Market Response Preview",
            "Approved Resources",
            "Pilot partner",
            "Pilot product family",
            "Pilot customer segment",
            "Sign-off owner",
            "Date",
            "Conditions",
            "Pending does not mean approved",
        ),
    )
    checks[3].pass_("sign-off template covers required approval areas") if ok else checks[3].fail(missing)

    ok, missing = contains_all(
        copy_rules,
        (
            "cost",
            "margin",
            "pricing breakdown",
            "supplier private notes",
            "internal-only comments",
            "private partner notes",
            "backend paths",
            "storage keys",
            "token values",
            "unsafe raw database IDs",
            "Planned dates must be labeled as planned",
            "Shipment risk must be converted into customer-safe wording",
            "Market Response shown outside PartnerOS must be a high-level preview only",
            "Do not expose internal scoring",
            "Do not expose ranking",
            "HOSUN technical metrics may only become customer-visible after business confirmation",
        ),
    )
    checks[4].pass_("copy rules cover forbidden fields and safe wording") if ok else checks[4].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "lifting systems",
            "desk frames",
            "desk legs",
            "lifting columns",
            "heavy-duty supply",
            "product family",
            "load range",
            "stability summary",
            "noise claim",
            "delivery window",
            "installation summary",
            "after-sales support",
            "warranty summary",
            "test cycle summary",
            "certification summary",
            "packaging summary",
            "project demand category",
            "raw test notes",
            "complaint details",
            "delivery risk analysis",
            "warranty cost exposure",
            "supplier private notes",
            "internal Market Response scoring",
        ),
    )
    checks[5].pass_("HOSUN customer-safe and internal-only fields covered") if ok else checks[5].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "education furniture",
            "school desks/chairs",
            "project furniture",
            "school procurement timing",
            "delivery consistency",
            "installation notes",
            "resource needs",
            "feedback after use",
            "project acceptance criteria",
        ),
    )
    checks[6].pass_("JOOBOO education/project furniture fields covered") if ok else checks[6].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "onboarding data",
            "product family",
            "quote logic",
            "delivery requirement",
            "resource taxonomy",
            "customer-visible fields",
            "Market Response metrics",
        ),
    )
    checks[7].pass_("future partner data model fields covered") if ok else checks[7].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "Do not enter D9",
            "Do not create proof records",
            "Do not write STAGING_VALIDATED",
            "Do not fabricate real business owner sign-off",
            "Do not fabricate real partner feedback",
            "Do not automatically send",
            "Do not automatically change quote or order status",
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
            "real staging validated",
            "production ready",
            "business owner approved",
            "approved real staging record",
            "real partner feedback recorded",
        )
        if marker in combined
    ]
    if forbidden:
        checks[8].fail(", ".join(forbidden))
    elif not ok:
        checks[8].fail(missing)
    else:
        checks[8].pass_("handoff boundary retained; no fabricated approval or staging claim")

    continuity_paths = (
        "docs/phase3/d8_24_feedback_priority_review_board.md",
        "docs/phase3/d8_24_pilot_gate_decision_template.md",
        "docs/demo/d8_24_empty_partner_feedback_review.md",
        "docs/demo/d8_23_partner_rehearsal_execution_log.md",
    )
    try:
        continuity = "\n".join(read(path) for path in continuity_paths)
        ok, missing = contains_all(
            continuity,
            (
                "No real partner session recorded yet",
                "Internal observations are not partner feedback",
                "READY_FOR_STAGING_HANDOFF",
                "WAITING_FOR_REAL_STAGING_EVIDENCE",
                "HOSUN",
                "JOOBOO",
                "future partner",
            ),
        )
        checks[9].pass_("D8.24/D8.23 source docs remain aligned") if ok else checks[9].fail(missing)
    except FileNotFoundError as exc:
        checks[9].fail(str(exc))

    for check in checks:
        print(check.line())

    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.25 UAT data selection check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1

    print("\nD8.25 UAT data selection check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
