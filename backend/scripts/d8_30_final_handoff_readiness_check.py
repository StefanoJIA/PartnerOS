"""D8.30 final D8 handoff readiness index documentation check."""

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
        Check("D8.30 required files"),
        Check("final handoff readiness index"),
        Check("D9 entry gate"),
        Check("remaining external inputs"),
        Check("no-go conditions"),
        Check("HOSUN D9 conditions"),
        Check("JOOBOO and future partner D9 conditions"),
        Check("handoff boundary and no forbidden claims"),
        Check("D8.29/D8.28 continuity"),
    ]

    required_files = (
        "docs/phase3/d8_30_final_handoff_readiness_index.md",
        "docs/phase3/d8_30_d9_entry_gate.md",
        "docs/phase3/d8_30_remaining_external_inputs.md",
        "docs/phase3/d8_30_no_go_conditions.md",
    )
    missing_files = [path for path in required_files if not (ROOT / path).exists()]
    if missing_files:
        checks[0].fail(", ".join(missing_files))
        for check in checks:
            print(check.line())
        return 1
    checks[0].pass_("readiness index, D9 gate, external inputs, and no-go docs exist")

    index = read(required_files[0])
    gate = read(required_files[1])
    inputs = read(required_files[2])
    no_go = read(required_files[3])
    combined = "\n".join([index, gate, inputs, no_go])

    ok, missing = contains_all(
        index,
        (
            "local RC",
            "Chinese UI usability",
            "Growth Operations / Campaign",
            "full-chain manual acceptance",
            "partner-facing rehearsal pack",
            "feature gap roadmap",
            "staging handoff contract",
            "pre-staging drill",
            "partner feedback intake",
            "feedback priority review board",
            "UAT data selection",
            "business owner signoff checklist",
            "security review readiness",
            "credentials intake playbook",
            "real staging smoke test template",
            "ready",
            "pending external input",
            "blocked",
            "not started",
            "local validation",
            "documentation",
            "dry-run",
            "real external evidence",
        ),
    )
    checks[1].pass_("index summarizes D8.12-D8.29 readiness and evidence types") if ok else checks[1].fail(missing)

    ok, missing = contains_all(
        gate,
        (
            "real backend HTTPS origin verified",
            "real Portal origin verified",
            "`PORTAL_CUSTOMER_API_TOKEN` securely configured",
            "allowed origins verified",
            "`PUBLIC_BASE_URL` verified",
            "security signoff approved",
            "business owner signoff approved",
            "UAT seed data approved",
            "real staging smoke test passed",
            "forbidden fields absent",
            "rollback drill passed",
            "no P0 blockers",
            "If any one item is pending, rejected, blocked, or unreviewed",
            "D8.30 does not enter D9",
        ),
    )
    checks[2].pass_("D9 gate includes all hard entry conditions and blocking rule") if ok else checks[2].fail(missing)

    ok, missing = contains_all(
        inputs,
        (
            "staging credentials",
            "security reviewer signoff",
            "business owner signoff",
            "partner rehearsal feedback",
            "UAT seed records",
            "Portal operator confirmation",
            "infrastructure deployment window",
            "rollback owner",
            "Owner",
            "Status",
            "Dependency",
            "Next Action",
            "pending",
        ),
    )
    checks[3].pass_("remaining external inputs include required owners/status/dependencies/actions") if ok else checks[3].fail(missing)

    ok, missing = contains_all(
        no_go,
        (
            "local-only test is treated as staging evidence",
            "dry-run is treated as real validation",
            "pending is written as approved",
            "token appears in Git/docs/logs/screenshots/chat",
            "forbidden fields appear in Portal payload",
            "automatic email/SMS/LinkedIn/customer notification occurs",
            "quote/order is automatically changed",
            "rollback owner is missing",
            "security signoff is missing",
            "business signoff is missing",
            "partner feedback or sign-off is fabricated",
            "STAGING_VALIDATED is written before real evidence",
            "D9 is entered before all gates pass",
        ),
    )
    checks[4].pass_("no-go document lists required stop conditions") if ok else checks[4].fail(missing)

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
            "business owner and security reviewer approval",
        ),
    )
    checks[5].pass_("HOSUN D9 field and approval conditions covered") if ok else checks[5].fail(missing)

    ok, missing = contains_all(
        combined,
        (
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
            "sign-off",
        ),
    )
    checks[6].pass_("JOOBOO and future partner D9 prerequisites covered") if ok else checks[6].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "No real staging credentials",
            "No real staging evidence recorded",
            "Do not enter D9",
            "Do not create proof records",
            "Do not write STAGING_VALIDATED",
            "Do not fabricate credentials",
            "Do not fabricate credentials, evidence, sign-off, or partner feedback",
            "Do not process or record real token values",
            "Pending does not mean approved",
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
            "security signoff approved: yes",
            "business owner signoff approved: yes",
        )
        if marker in combined
    ]
    if forbidden:
        checks[7].fail(", ".join(forbidden))
    elif not ok:
        checks[7].fail(missing)
    else:
        checks[7].pass_("handoff boundary retained; no D9/STAGING_VALIDATED/fabricated evidence claim")

    continuity_paths = (
        "docs/phase3/d8_29_real_staging_smoke_test_plan.md",
        "docs/phase3/d8_29_staging_validation_boundary.md",
        "docs/phase3/d8_28_staging_go_no_go_checklist.md",
        "docs/phase3/d8_27_security_review_readiness_checklist.md",
    )
    try:
        continuity = "\n".join(read(path) for path in continuity_paths)
        ok, missing = contains_all(
            continuity,
            (
                "READY_FOR_STAGING_HANDOFF",
                "WAITING_FOR_REAL_STAGING_EVIDENCE",
                "Do not write STAGING_VALIDATED",
                "No real staging evidence recorded yet",
                "No real security sign-off recorded yet",
                "HOSUN",
            ),
        )
        checks[8].pass_("D8.29/D8.28/D8.27 source docs remain aligned") if ok else checks[8].fail(missing)
    except FileNotFoundError as exc:
        checks[8].fail(str(exc))

    for check in checks:
        print(check.line())

    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.30 final handoff readiness check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1

    print("\nD8.30 final handoff readiness check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
