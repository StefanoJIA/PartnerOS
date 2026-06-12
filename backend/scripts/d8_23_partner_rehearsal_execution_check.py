"""D8.23 partner rehearsal execution log documentation check."""

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
        Check("D8.23 required files"),
        Check("real rehearsal execution log template"),
        Check("no fabricated partner feedback boundary"),
        Check("internal dry-run rehearsal coverage"),
        Check("feedback capture rules"),
        Check("next action queue"),
        Check("HOSUN/JOOBOO/future partner rules"),
        Check("handoff boundary and no forbidden claims"),
        Check("D8.18-D8.22 continuity"),
    ]

    required_files = (
        "docs/demo/d8_23_partner_rehearsal_execution_log.md",
        "docs/demo/d8_23_internal_rehearsal_dry_run.md",
        "docs/phase3/d8_23_feedback_capture_rules.md",
        "docs/phase3/d8_23_next_action_queue.md",
    )
    missing_files = [path for path in required_files if not (ROOT / path).exists()]
    if missing_files:
        checks[0].fail(", ".join(missing_files))
        for check in checks:
            print(check.line())
        return 1
    checks[0].pass_("execution log, internal dry-run, capture rules, queue exist")

    execution = read(required_files[0])
    dry_run = read(required_files[1])
    rules = read(required_files[2])
    queue = read(required_files[3])
    combined = "\n".join([execution, dry_run, rules, queue])

    ok, missing = contains_all(
        execution,
        (
            "Session id:",
            "Partner / company:",
            "Attendees:",
            "Presenter:",
            "Date / time:",
            "Demo environment:",
            "Product focus:",
            "Pages shown:",
            "Questions Asked",
            "Partner Original Words",
            "Concerns",
            "Requested Features",
            "Staging / Pilot Interest",
            "Follow-up owner:",
            "Follow-up deadline:",
            "Decision: ready for staging UAT / needs another rehearsal / not ready",
        ),
    )
    checks[1].pass_("execution log has required session template") if ok else checks[1].fail(missing)

    ok, missing = contains_all(
        execution,
        (
            "No real partner session recorded yet",
            "Do not invent partner feedback",
            "Do not convert internal dry-run observations",
            "pending real partner session",
            "Do not fabricate feedback",
            "HOSUN",
            "JOOBOO",
            "Chongqing Huiju",
            "future partner",
        ),
    )
    checks[2].pass_("pending state and no-fabrication rule present") if ok else checks[2].fail(missing)

    ok, missing = contains_all(
        dry_run,
        (
            "Can the story be completed in 10-15 minutes?",
            "Workbench Opening",
            "Growth Operations / Campaign",
            "Manual Outreach",
            "Quote / Order / Production / Shipment",
            "Feedback / Market Response",
            "HOSUN Talk Track",
            "JOOBOO Talk Track",
            "Future Partner Talk Track",
            "Pages That Can Slow the Rehearsal",
            "Recommended Presenter Script Compression",
            "internal observation only",
        ),
    )
    checks[3].pass_("internal dry-run covers timing, flow, talk tracks, compression") if ok else checks[3].fail(missing)

    ok, missing = contains_all(
        rules,
        (
            "Real partner original words must be recorded verbatim",
            "Do not write internal guesses as partner feedback",
            "Do not write internal dry-run observations as real customer or partner feedback",
            "partner quote",
            "presenter observation",
            "system issue",
            "roadmap candidate",
            "Do not record token values, cost, margin, pricing breakdown",
            "Forbidden Capture Content",
            "Routing Rules",
        ),
    )
    checks[4].pass_("feedback capture rules distinguish feedback types and forbidden content") if ok else checks[4].fail(missing)

    ok, missing = contains_all(
        queue,
        (
            "staging credential request",
            "security review",
            "business UAT",
            "partner follow-up",
            "product data cleanup",
            "HOSUN market response refinement",
            "JOOBOO project furniture refinement",
            "future partner onboarding refinement",
            "Owner",
            "Due Date",
            "Priority",
            "Dependency",
            "Status",
        ),
    )
    checks[5].pass_("next action queue has required categories and fields") if ok else checks[5].fail(missing)

    ok, missing = contains_all(
        combined,
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
            "education furniture",
            "school desks/chairs",
            "project furniture",
            "school procurement timing",
            "delivery consistency",
            "resource needs",
            "feedback after use",
            "project acceptance criteria",
            "onboarding data",
            "product family",
            "quote logic",
            "delivery requirement",
            "resource taxonomy",
            "customer-visible fields",
            "Market Response metrics",
        ),
    )
    checks[6].pass_("HOSUN, JOOBOO, and future partner dimensions covered") if ok else checks[6].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "no D9 entry",
            "no proof record expansion",
            "no real staging validation claim",
            "Do not automatically send",
            "Do not automatically change quote/order status",
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
            "HOSUN approved",
            "JOOBOO approved",
            "Chongqing Huiju approved",
        )
        if marker in combined
    ]
    if forbidden:
        checks[7].fail(", ".join(forbidden))
    elif not ok:
        checks[7].fail(missing)
    else:
        checks[7].pass_("handoff boundary retained; no fabricated approval/status")

    continuity_paths = (
        "docs/demo/d8_18_partner_rehearsal_pack.md",
        "docs/phase3/d8_21_pre_staging_readiness_drill.md",
        "docs/demo/d8_22_partner_rehearsal_feedback_intake.md",
        "docs/phase3/d8_22_pilot_readiness_matrix.md",
        "docs/phase3/d8_22_rehearsal_to_roadmap_decision_log.md",
    )
    try:
        continuity = "\n".join(read(path) for path in continuity_paths)
        ok, missing = contains_all(
            continuity,
            (
                "READY_FOR_STAGING_HANDOFF",
                "PartnerOS",
                "HOSUN",
                "JOOBOO",
                "future partner",
                "staging",
                "pilot",
            ),
        )
        checks[8].pass_("D8.18-D8.22 source docs remain present") if ok else checks[8].fail(missing)
    except FileNotFoundError as exc:
        checks[8].fail(str(exc))

    for check in checks:
        print(check.line())

    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.23 partner rehearsal execution check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1

    print("\nD8.23 partner rehearsal execution check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
