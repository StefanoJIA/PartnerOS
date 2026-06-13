"""D8.33 manual external execution tracker and response intake documentation check."""

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
        Check("D8.33 required files"),
        Check("manual external execution tracker"),
        Check("response intake rules"),
        Check("external response triage"),
        Check("tracker update examples"),
        Check("HOSUN/JOOBOO/future partner coverage"),
        Check("handoff boundary and no forbidden claims"),
        Check("D8.32/D8.31 continuity"),
    ]

    required_files = (
        "docs/phase3/d8_33_manual_external_execution_tracker.md",
        "docs/phase3/d8_33_response_intake_rules.md",
        "docs/phase3/d8_33_external_response_triage.md",
        "docs/phase3/d8_33_tracker_update_examples.md",
    )
    missing_files = [path for path in required_files if not (ROOT / path).exists()]
    if missing_files:
        checks[0].fail(", ".join(missing_files))
        for check in checks:
            print(check.line())
        return 1
    checks[0].pass_("tracker, intake rules, triage, and examples exist")

    tracker = read(required_files[0])
    rules = read(required_files[1])
    triage = read(required_files[2])
    examples = read(required_files[3])
    combined = "\n".join([tracker, rules, triage, examples])

    ok, missing = contains_all(
        tracker,
        (
            "partner rehearsal request",
            "business UAT / data sign-off request",
            "security review request",
            "staging credentials request",
            "Action ID",
            "Action Type",
            "Recipient Role",
            "Target Partner/System",
            "Sent By",
            "Sent Date",
            "Channel",
            "Expected Response",
            "Dependency",
            "Status",
            "Next Step",
            "Owner",
            "Due Date",
            "draft",
            "ready to send",
            "sent manually",
            "response received",
            "blocked",
            "complete",
            "No external message has been sent from this tracker",
        ),
    )
    checks[1].pass_("manual tracker covers required actions, fields, statuses, and unsent state") if ok else checks[1].fail(missing)

    ok, missing = contains_all(
        rules,
        (
            "Only when the user pastes a real reply may the tracker status become `response received`",
            "Do not write internal guesses as external replies",
            "Do not write oral, unconfirmed content as sign-off",
            "PROVIDED_VIA_SECURE_CHANNEL",
            "Business sign-off must include explicit owner, date, and scope",
            "Security approval must include explicit reviewer, date, and scope",
            "original quote",
            "internal observation",
            "system issue",
            "roadmap candidate",
            "Pending must not be written as approved or complete",
        ),
    )
    checks[2].pass_("response intake rules distinguish real replies, sign-off, token handling, and feedback classes") if ok else checks[2].fail(missing)

    ok, missing = contains_all(
        triage,
        (
            "partner wants rehearsal",
            "partner asks product question",
            "partner requests feature",
            "partner raises concern",
            "business owner approves fields",
            "business owner requests changes",
            "security approves",
            "security requests fixes",
            "credentials available via secure channel",
            "credentials incomplete",
            "staging window proposed",
            "blocker found",
            "Next Action",
            "Owner",
            "Enter Priority Review?",
            "Affects D9 Gate?",
            "Needs Security/Business Sign-Off?",
        ),
    )
    checks[3].pass_("external response triage covers required response classes and routing columns") if ok else checks[3].fail(missing)

    ok, missing = contains_all(
        examples,
        (
            "All examples in this document are fictional placeholders",
            "Partner Rehearsal Sent, No Reply Yet",
            "Business Owner Requests Customer-Safe Wording Changes",
            "Security Reviewer Requests CORS Test Detail",
            "Credentials Received Via Secure Channel, Not Verified",
            "HOSUN Requests Load/Noise/Test Cycle Detail",
            "PROVIDED_VIA_SECURE_CHANNEL",
            "not real replies",
            "not real credentials",
            "not real sign-off",
            "not real partner feedback",
        ),
    )
    checks[4].pass_("tracker examples are clearly fictional and cover required scenarios") if ok else checks[4].fail(missing)

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
            "customer-safe candidate",
            "needs validation",
            "internal-only",
            "pilot blocker",
            "JOOBOO",
            "education furniture",
            "school desks/chairs",
            "project furniture",
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
    checks[5].pass_("HOSUN/JOOBOO/future partner response coverage present") if ok else checks[5].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "No real external response",
            "No external message has been sent",
            "Do not mark response received without a real reply pasted by the user",
            "Do not fabricate external replies",
            "Do not fabricate credentials, evidence, sign-off, or partner feedback",
            "Do not mark pending as approved or complete",
            "Do not write STAGING_VALIDATED",
            "Do not enter D9",
            "Do not create proof records",
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
            "external response received: yes",
            "status=complete",
            "status=approved",
        )
        if marker in combined
    ]
    if forbidden:
        checks[6].fail(", ".join(forbidden))
    elif not ok:
        checks[6].fail(missing)
    else:
        checks[6].pass_("handoff boundary retained; no fabricated response/completion claim")

    continuity_paths = (
        "docs/phase3/d8_32_external_execution_message_pack.md",
        "docs/phase3/d8_32_external_action_tracker_dry_run.md",
        "docs/phase3/d8_31_next_external_actions_tracker.md",
        "docs/phase3/d8_30_d9_entry_gate.md",
    )
    try:
        continuity = "\n".join(read(path) for path in continuity_paths)
        ok, missing = contains_all(
            continuity,
            (
                "READY_FOR_STAGING_HANDOFF",
                "WAITING_FOR_REAL_STAGING_EVIDENCE",
                "Do not write STAGING_VALIDATED",
                "No external message has been sent",
                "pending",
                "HOSUN",
                "JOOBOO",
            ),
        )
        checks[7].pass_("D8.32/D8.31/D8.30 source docs remain aligned") if ok else checks[7].fail(missing)
    except FileNotFoundError as exc:
        checks[7].fail(str(exc))

    for check in checks:
        print(check.line())

    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.33 manual external execution tracker check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1

    print("\nD8.33 manual external execution tracker check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
