"""D8.26 business owner sign-off checklist documentation check."""

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
        Check("D8.26 required files"),
        Check("business owner sign-off checklist"),
        Check("customer-safe wording review"),
        Check("staging seed selection checklist"),
        Check("HOSUN lifting systems field review"),
        Check("JOOBOO coverage"),
        Check("future partner coverage"),
        Check("handoff boundary and no forbidden claims"),
        Check("D8.25/D8.24 continuity"),
    ]

    required_files = (
        "docs/phase3/d8_26_business_owner_signoff_checklist.md",
        "docs/phase3/d8_26_customer_safe_wording_review.md",
        "docs/phase3/d8_26_staging_seed_selection_checklist.md",
        "docs/phase3/d8_26_hosun_lifting_systems_field_review.md",
    )
    missing_files = [path for path in required_files if not (ROOT / path).exists()]
    if missing_files:
        checks[0].fail(", ".join(missing_files))
        for check in checks:
            print(check.line())
        return 1
    checks[0].pass_("sign-off, wording, seed selection, and HOSUN review docs exist")

    signoff = read(required_files[0])
    wording = read(required_files[1])
    seed = read(required_files[2])
    hosun = read(required_files[3])
    combined = "\n".join([signoff, wording, seed, hosun])

    ok, missing = contains_all(
        signoff,
        (
            "Sign-off Session Information",
            "Owner",
            "Date",
            "Scope",
            "Partner",
            "Product family",
            "Customer-Visible Fields Checklist",
            "Forbidden Fields Checklist",
            "Approved Products Checklist",
            "Approved Customer Segments Checklist",
            "Approved Orders Checklist",
            "Approved Feedback Records Checklist",
            "Approved Market Response Preview Checklist",
            "Approved Resources Checklist",
            "Pilot Entry Condition Checklist",
            "Sign-off status",
            "pending / approved / changes required",
            "No real business owner sign-off recorded yet",
            "Pending does not mean approved",
        ),
    )
    checks[1].pass_("sign-off checklist has required execution sections") if ok else checks[1].fail(missing)

    ok, missing = contains_all(
        wording,
        (
            "planned dates must say planned / 预计",
            "shipment risk must be rewritten into customer-safe wording",
            "production delay must not expose internal responsibility assignment",
            "Market Response may show high-level preview only",
            "cost",
            "margin",
            "pricing breakdown",
            "supplier private notes",
            "internal comments",
            "private partner notes",
            "backend paths",
            "storage keys",
            "token values",
            "unsafe raw database IDs",
            "validated claim",
            "internal note",
            "draft wording",
        ),
    )
    checks[2].pass_("wording review covers dates, risk, delays, forbidden fields, claim classes") if ok else checks[2].fail(missing)

    ok, missing = contains_all(
        seed,
        (
            "Products Checklist",
            "Customers Checklist",
            "Quotes Checklist",
            "Orders Checklist",
            "Production Milestones Checklist",
            "Shipment Status Checklist",
            "Resources Checklist",
            "Feedback Checklist",
            "Market Response Preview Checklist",
            "demo seed",
            "sanitized real record",
            "synthetic sample",
            "pending",
            "customer-safe",
            "internal-only",
            "requires approval",
            "Do not write pending records as approved",
        ),
    )
    checks[3].pass_("seed checklist covers required record types and classifications") if ok else checks[3].fail(missing)

    ok, missing = contains_all(
        hosun,
        (
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
            "Customer-Safe Candidate",
            "Internal-Only",
            "Needs Validation",
            "Needs Business Wording",
            "Pilot Blocker",
            "load, noise, test cycle, certification, and warranty can only become customer-visible",
            "Business owner confirms the exact customer-safe wording",
            "Supporting product material exists",
        ),
    )
    checks[4].pass_("HOSUN field review covers products, fields, classifications, and sensitive metrics") if ok else checks[4].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "education furniture",
            "school desks/chairs",
            "project furniture",
            "school procurement timing",
            "delivery consistency",
            "installation",
            "resource needs",
            "feedback after use",
            "project acceptance criteria",
        ),
    )
    checks[5].pass_("JOOBOO field and wording coverage present") if ok else checks[5].fail(missing)

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
    checks[6].pass_("future partner fields covered") if ok else checks[6].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "No real business owner sign-off recorded yet",
            "Pending records must not be written as approved",
            "Do not enter D9",
            "Do not create proof records",
            "Do not write STAGING_VALIDATED",
            "Do not fabricate real sign-off",
            "Do not fabricate real partner feedback",
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
            "real business owner approved",
            "real sign-off completed",
            "real partner feedback recorded",
        )
        if marker in combined
    ]
    if forbidden:
        checks[7].fail(", ".join(forbidden))
    elif not ok:
        checks[7].fail(missing)
    else:
        checks[7].pass_("handoff boundary retained; no fabricated approval or staging claim")

    continuity_paths = (
        "docs/phase3/d8_25_uat_data_selection_plan.md",
        "docs/phase3/d8_25_business_owner_data_signoff.md",
        "docs/phase3/d8_25_customer_safe_copy_rules.md",
        "docs/phase3/d8_24_pilot_gate_decision_template.md",
    )
    try:
        continuity = "\n".join(read(path) for path in continuity_paths)
        ok, missing = contains_all(
            continuity,
            (
                "No real business owner sign-off recorded yet",
                "READY_FOR_STAGING_HANDOFF",
                "WAITING_FOR_REAL_STAGING_EVIDENCE",
                "Do not write STAGING_VALIDATED",
                "HOSUN",
                "JOOBOO",
                "future partner",
            ),
        )
        checks[8].pass_("D8.25/D8.24 source docs remain aligned") if ok else checks[8].fail(missing)
    except FileNotFoundError as exc:
        checks[8].fail(str(exc))

    for check in checks:
        print(check.line())

    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.26 business owner sign-off check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1

    print("\nD8.26 business owner sign-off check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
