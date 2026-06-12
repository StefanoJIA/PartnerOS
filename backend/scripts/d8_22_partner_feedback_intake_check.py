"""D8.22 partner rehearsal feedback intake documentation check."""

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
        Check("D8.22 required files"),
        Check("partner feedback intake coverage"),
        Check("pilot readiness matrix coverage"),
        Check("rehearsal-to-roadmap decision log coverage"),
        Check("HOSUN lifting systems feedback dimensions"),
        Check("JOOBOO project furniture feedback dimensions"),
        Check("future partner feedback dimensions"),
        Check("handoff boundary and no forbidden claims"),
        Check("D8.21/D8.20/D8.19 continuity"),
    ]

    required_files = (
        "docs/demo/d8_22_partner_rehearsal_feedback_intake.md",
        "docs/phase3/d8_22_pilot_readiness_matrix.md",
        "docs/phase3/d8_22_rehearsal_to_roadmap_decision_log.md",
    )
    missing_files = [path for path in required_files if not (ROOT / path).exists()]
    if missing_files:
        checks[0].fail(", ".join(missing_files))
        for check in checks:
            print(check.line())
        return 1
    checks[0].pass_("intake, matrix, and decision log exist")

    intake = read(required_files[0])
    matrix = read(required_files[1])
    decision = read(required_files[2])
    combined = "\n".join([intake, matrix, decision])

    ok, missing = contains_all(
        intake,
        (
            "Partner:",
            "Attendees:",
            "Date:",
            "Presenter:",
            "Product focus:",
            "Is the PartnerOS positioning clear?",
            "Is the demo flow clear?",
            "Is Workbench suitable as the daily operating entry?",
            "Does Campaign / 营销活动 have business value?",
            "Does Manual Outreach have business value?",
            "Does the Quote -> Order -> Production -> Shipment flow match real work?",
            "Customer Portal Field Review",
            "Are Feedback and Market Response valuable?",
            "Staging UAT interest",
            "Pilot interest",
            "Partner Original Comments",
            "Follow-Up Issues",
        ),
    )
    checks[1].pass_("feedback intake captures required rehearsal fields") if ok else checks[1].fail(missing)

    ok, missing = contains_all(
        matrix,
        (
            "P0: staging / pilot 前必须解决",
            "P1: partner rehearsal 后优先解决",
            "P2: pilot 期间增强",
            "P3: 长期平台化能力",
            "Feature or Issue",
            "Related Module",
            "Impacted Partner",
            "Business Value",
            "Risk",
            "Needs Real Staging Credentials",
            "Needs Security Review",
            "Needs Business Owner Sign-Off",
            "Suggested Owner",
            "Suggested Stage",
            "Decision",
            "do now",
            "defer",
            "needs feedback",
            "blocked",
        ),
    )
    checks[2].pass_("pilot matrix includes required columns, priorities, decisions") if ok else checks[2].fail(missing)

    ok, missing = contains_all(
        decision,
        (
            "How Feedback Enters D8.23 / D9 / Pilot",
            "Feedback That Cannot Be Developed Immediately",
            "Feedback That Is Documentation or Demo Copy Only",
            "Feedback That Affects Data Model or Permissions",
            "Feedback That Affects HOSUN / JOOBOO / Future Partner Product Fields",
            "Decision Log Template",
            "D8.23 / D9 / Pilot / Later",
            "Do not enter D9 from rehearsal feedback alone",
        ),
    )
    checks[3].pass_("decision log defines routing to D8.23/D9/Pilot/Later") if ok else checks[3].fail(missing)

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
            "customer-safe feedback",
            "internal-only feedback",
            "Market Response signal",
            "product expectation",
            "quote/order/pilot blocker",
        ),
    )
    checks[4].pass_("HOSUN dimensions and classifications covered") if ok else checks[4].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "JOOBOO",
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
    checks[5].pass_("JOOBOO project furniture dimensions covered") if ok else checks[5].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "Chongqing Huiju",
            "future partner",
            "onboarding data",
            "product family",
            "quote logic",
            "delivery requirement",
            "resource taxonomy",
            "customer-visible fields",
            "Market Response metrics",
        ),
    )
    checks[6].pass_("future partner extension dimensions covered") if ok else checks[6].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "no D9 entry",
            "no proof record expansion",
            "no real staging validation claim",
            "Do not automatically",
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
            "Current state: real staging validated",
            "Status: production ready",
        )
        if marker in combined
    ]
    if forbidden:
        checks[7].fail(", ".join(forbidden))
    elif not ok:
        checks[7].fail(missing)
    else:
        checks[7].pass_("handoff state retained; no forbidden claim")

    continuity_paths = (
        "docs/phase3/d8_21_pre_staging_readiness_drill.md",
        "docs/phase3/d8_20_staging_handoff_contract.md",
        "docs/phase3/d8_19_feature_gap_and_roadmap.md",
    )
    try:
        continuity = "\n".join(read(path) for path in continuity_paths)
        ok, missing = contains_all(
            continuity,
            (
                "READY_FOR_STAGING_HANDOFF",
                "WAITING_FOR_REAL_STAGING_EVIDENCE",
                "Real service Portal staging validation",
                "Portal Bridge Dry-Run",
                "Portal Customer-Safe Field Contract",
            ),
        )
        checks[8].pass_("D8.19-D8.21 source docs remain present") if ok else checks[8].fail(missing)
    except FileNotFoundError as exc:
        checks[8].fail(str(exc))

    for check in checks:
        print(check.line())

    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.22 partner feedback intake check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1

    print("\nD8.22 partner feedback intake check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
