"""D8.31 closeout index and external execution packet documentation check."""

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
        Check("D8.31 required files"),
        Check("D8 closeout index"),
        Check("external execution packet"),
        Check("next external actions tracker"),
        Check("D8-to-D9 transition brief"),
        Check("HOSUN external execution focus"),
        Check("JOOBOO and future partner execution focus"),
        Check("handoff boundary and no forbidden claims"),
        Check("D8.30/D8.29 continuity"),
    ]

    required_files = (
        "docs/phase3/d8_31_d8_closeout_index.md",
        "docs/phase3/d8_31_external_execution_packet.md",
        "docs/phase3/d8_31_next_external_actions_tracker.md",
        "docs/phase3/d8_31_d8_to_d9_transition_brief.md",
    )
    missing_files = [path for path in required_files if not (ROOT / path).exists()]
    if missing_files:
        checks[0].fail(", ".join(missing_files))
        for check in checks:
            print(check.line())
        return 1
    checks[0].pass_("closeout index, execution packet, tracker, and transition brief exist")

    closeout = read(required_files[0])
    packet = read(required_files[1])
    tracker = read(required_files[2])
    transition = read(required_files[3])
    combined = "\n".join([closeout, packet, tracker, transition])

    ok, missing = contains_all(
        closeout,
        (
            "D8.12 local RC",
            "D8.14 Growth Operations",
            "D8.17 full-chain acceptance",
            "D8.18 partner rehearsal pack",
            "D8.19 feature gap roadmap",
            "D8.20 staging handoff contract",
            "D8.21 pre-staging readiness",
            "D8.22 feedback intake",
            "D8.23 rehearsal execution log",
            "D8.24 priority review board",
            "D8.25 UAT data selection",
            "D8.26 business owner signoff",
            "D8.27 security review readiness",
            "D8.28 credentials intake",
            "D8.29 staging smoke evidence template",
            "D8.30 final handoff readiness",
            "Status",
            "Output Docs",
            "Checks",
            "Depends On External Input",
            "Executable Now",
        ),
    )
    checks[1].pass_("closeout index summarizes D8.12-D8.30 with required columns") if ok else checks[1].fail(missing)

    ok, missing = contains_all(
        packet,
        (
            "A. Partner Rehearsal",
            "B. Business UAT Data And Sign-off",
            "C. Staging And Security Request",
            "Purpose",
            "Responsible owner",
            "Inputs",
            "Outputs",
            "Success conditions",
            "Failure handling",
            "demo script",
            "feedback form",
            "execution log",
            "data selection",
            "signoff",
            "customer-safe wording",
            "seed manifest",
            "credentials intake",
            "smoke plan",
            "Go/No-Go",
        ),
    )
    checks[2].pass_("execution packet covers partner rehearsal, business UAT, staging/security") if ok else checks[2].fail(missing)

    ok, missing = contains_all(
        tracker,
        (
            "Action ID",
            "Action Type",
            "partner rehearsal",
            "business signoff",
            "security review",
            "credentials request",
            "staging smoke",
            "Owner",
            "Target Partner or System",
            "Dependency",
            "Status",
            "pending",
            "requested",
            "received",
            "blocked",
            "complete",
            "Due Date",
            "Next Step",
            "Do not mark pending as complete",
        ),
    )
    checks[3].pass_("external action tracker includes required fields/statuses and pending rule") if ok else checks[3].fail(missing)

    ok, missing = contains_all(
        transition,
        (
            "D8 has completed local readiness and handoff readiness",
            "real staging smoke test passed",
            "security signoff approved",
            "business signoff approved",
            "UAT data approval complete",
            "rollback drill passed",
            "no P0 blocker remains",
            "D9 is not allowed",
            "STAGING_VALIDATED is not allowed",
            "Local RC does not equal real staging evidence",
            "Dry-run does not equal real validation",
            "Documentation does not equal real validation",
            "Script pass does not equal real validation",
            "Template pass does not equal real validation",
            "D8 is ready for external execution; D9 remains blocked",
        ),
    )
    checks[4].pass_("transition brief states D8 complete locally and D9 blocked until external evidence") if ok else checks[4].fail(missing)

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
        ),
    )
    checks[5].pass_("HOSUN rehearsal/UAT field focus covered") if ok else checks[5].fail(missing)

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
        ),
    )
    checks[6].pass_("JOOBOO and future partner confirmation path covered") if ok else checks[6].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "No real staging credentials",
            "No real partner feedback",
            "Do not enter D9",
            "Do not create proof records",
            "Do not write STAGING_VALIDATED",
            "Do not fabricate credentials",
            "Do not fabricate credentials, evidence, sign-off, or partner feedback",
            "Do not treat pending as approved or complete",
            "Do not process or record real token values",
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
        checks[7].pass_("handoff boundary retained; no D9/STAGING_VALIDATED/fabricated completion claim")

    continuity_paths = (
        "docs/phase3/d8_30_final_handoff_readiness_index.md",
        "docs/phase3/d8_30_d9_entry_gate.md",
        "docs/phase3/d8_29_staging_validation_boundary.md",
        "docs/phase3/d8_28_staging_go_no_go_checklist.md",
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
                "No real staging evidence recorded",
                "HOSUN",
            ),
        )
        checks[8].pass_("D8.30/D8.29/D8.28 source docs remain aligned") if ok else checks[8].fail(missing)
    except FileNotFoundError as exc:
        checks[8].fail(str(exc))

    for check in checks:
        print(check.line())

    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.31 closeout execution packet check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1

    print("\nD8.31 closeout execution packet check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
