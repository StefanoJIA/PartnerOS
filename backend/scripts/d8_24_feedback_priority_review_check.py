"""D8.24 feedback priority review board documentation check."""

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
        Check("D8.24 required files"),
        Check("feedback priority review board fields"),
        Check("pilot gate decision template"),
        Check("feedback-to-roadmap rules"),
        Check("empty partner feedback review"),
        Check("HOSUN review dimensions"),
        Check("JOOBOO review dimensions"),
        Check("future partner review dimensions"),
        Check("handoff boundary and no forbidden claims"),
        Check("D8.23/D8.22 continuity"),
    ]

    required_files = (
        "docs/phase3/d8_24_feedback_priority_review_board.md",
        "docs/phase3/d8_24_pilot_gate_decision_template.md",
        "docs/phase3/d8_24_feedback_to_roadmap_rules.md",
        "docs/demo/d8_24_empty_partner_feedback_review.md",
    )
    missing_files = [path for path in required_files if not (ROOT / path).exists()]
    if missing_files:
        checks[0].fail(", ".join(missing_files))
        for check in checks:
            print(check.line())
        return 1
    checks[0].pass_("review board, gate template, roadmap rules, empty review exist")

    board = read(required_files[0])
    gate = read(required_files[1])
    rules = read(required_files[2])
    empty = read(required_files[3])
    combined = "\n".join([board, gate, rules, empty])

    ok, missing = contains_all(
        board,
        (
            "Feedback ID",
            "Source Type",
            "real partner quote",
            "internal observation",
            "system issue",
            "roadmap candidate",
            "Partner",
            "HOSUN",
            "JOOBOO",
            "Chongqing Huiju",
            "future partner",
            "Product Focus",
            "Original Quote or Observation",
            "Related Module",
            "Impact",
            "Risk",
            "Priority",
            "P0",
            "P1",
            "P2",
            "P3",
            "Dependency",
            "staging credentials",
            "security review",
            "business sign-off",
            "partner data",
            "none",
            "Decision",
            "do now",
            "defer",
            "needs more feedback",
            "blocked",
            "Owner",
            "Due Date",
            "Status",
        ),
    )
    checks[1].pass_("review board has required fields and values") if ok else checks[1].fail(missing)

    ok, missing = contains_all(
        gate,
        (
            "Is there real partner feedback?",
            "Are real staging credentials available?",
            "Is security review complete?",
            "Is business UAT field approval complete?",
            "Are customer-safe fields confirmed?",
            "Are forbidden fields still prohibited?",
            "Is there any P0 blocker?",
            "Is staging UAT allowed?",
            "Is pilot allowed?",
            "Does the system remain READY_FOR_STAGING_HANDOFF until external evidence exists?",
            "Is writing STAGING_VALIDATED forbidden before real evidence?",
            "Allow staging UAT",
            "Allow pilot",
            "D9 remains gated",
        ),
    )
    checks[2].pass_("pilot gate template answers required gate questions") if ok else checks[2].fail(missing)

    ok, missing = contains_all(
        rules,
        (
            "Do not treat internal dry-run as partner feedback",
            "Do not treat presenter guess as a real requirement",
            "Real partner original words must be preserved",
            "P0:",
            "P1:",
            "P2:",
            "P3:",
            "token",
            "CORS",
            "customer-safe fields",
            "forbidden fields",
            "security review",
            "business owner sign-off",
            "Do not write STAGING_VALIDATED without real external staging evidence",
            "Do not enter D9 while external staging remains WAITING_FOR_REAL_STAGING_EVIDENCE",
        ),
    )
    checks[3].pass_("feedback-to-roadmap rules present") if ok else checks[3].fail(missing)

    ok, missing = contains_all(
        empty,
        (
            "No real partner session recorded yet.",
            "No real HOSUN/JOOBOO/Chongqing Huiju/future partner feedback has been recorded yet.",
            "Internal observations are not partner feedback.",
            "pending real partner session",
            "This document can only be used to prepare records after a real rehearsal",
            "does not write STAGING_VALIDATED",
        ),
    )
    checks[4].pass_("empty review clearly prevents fabricated feedback") if ok else checks[4].fail(missing)

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
            "Customer-Safe Feedback",
            "Internal-Only Feedback",
            "Market Response Signal",
            "Product Expectation",
            "Quote Blocker",
            "Order Blocker",
            "Pilot Blocker",
        ),
    )
    checks[5].pass_("HOSUN dimensions and blocker classifications covered") if ok else checks[5].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "education furniture",
            "school desks/chairs",
            "project furniture",
            "school procurement timing",
            "delivery consistency",
            "resource needs",
            "feedback after use",
            "project acceptance criteria",
        ),
    )
    checks[6].pass_("JOOBOO review dimensions covered") if ok else checks[6].fail(missing)

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
    checks[7].pass_("future partner review dimensions covered") if ok else checks[7].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "no D9 entry",
            "no proof record expansion",
            "no real staging validation claim",
            "no fabricated partner feedback",
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
        checks[8].fail(", ".join(forbidden))
    elif not ok:
        checks[8].fail(missing)
    else:
        checks[8].pass_("handoff boundary retained; no forbidden claim")

    continuity_paths = (
        "docs/demo/d8_23_partner_rehearsal_execution_log.md",
        "docs/phase3/d8_23_feedback_capture_rules.md",
        "docs/demo/d8_22_partner_rehearsal_feedback_intake.md",
        "docs/phase3/d8_22_pilot_readiness_matrix.md",
    )
    try:
        continuity = "\n".join(read(path) for path in continuity_paths)
        ok, missing = contains_all(
            continuity,
            (
                "No real partner session recorded yet",
                "Do not invent partner feedback",
                "READY_FOR_STAGING_HANDOFF",
                "WAITING_FOR_REAL_STAGING_EVIDENCE",
                "HOSUN",
                "JOOBOO",
                "future partner",
            ),
        )
        checks[9].pass_("D8.22-D8.23 source docs remain aligned") if ok else checks[9].fail(missing)
    except FileNotFoundError as exc:
        checks[9].fail(str(exc))

    for check in checks:
        print(check.line())

    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.24 feedback priority review check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1

    print("\nD8.24 feedback priority review check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
