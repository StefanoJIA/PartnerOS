"""D8.29 real-staging smoke test plan and evidence template documentation check."""

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
        Check("D8.29 required files"),
        Check("real staging smoke test plan"),
        Check("staging evidence template"),
        Check("staging failure triage"),
        Check("staging validation boundary"),
        Check("HOSUN customer-safe and forbidden boundary"),
        Check("handoff boundary and no forbidden claims"),
        Check("D8.28/D8.27 continuity"),
    ]

    required_files = (
        "docs/phase3/d8_29_real_staging_smoke_test_plan.md",
        "docs/phase3/d8_29_staging_evidence_template.md",
        "docs/phase3/d8_29_staging_failure_triage.md",
        "docs/phase3/d8_29_staging_validation_boundary.md",
    )
    missing_files = [path for path in required_files if not (ROOT / path).exists()]
    if missing_files:
        checks[0].fail(", ".join(missing_files))
        for check in checks:
            print(check.line())
        return 1
    checks[0].pass_("smoke plan, evidence template, triage, and boundary docs exist")

    plan = read(required_files[0])
    evidence = read(required_files[1])
    triage = read(required_files[2])
    boundary = read(required_files[3])
    combined = "\n".join([plan, evidence, triage, boundary])

    ok, missing = contains_all(
        plan,
        (
            "backend HTTPS `/health`",
            "migration/database ready",
            "Portal bridge readiness",
            "`enabled=true` only in staging",
            "correct token success",
            "missing token fail",
            "wrong token fail",
            "allowed origin success",
            "disallowed origin fail",
            "`PUBLIC_BASE_URL` correct",
            "customer-safe payload check",
            "products/orders/order detail/resources/feedback/market preview",
            "forbidden fields absent",
            "feedback submit does not auto-reply",
            "Portal read does not auto-change quote/order status",
            "no external notifications",
            "rollback / disable drill",
        ),
    )
    checks[1].pass_("smoke plan includes required real-staging sequence") if ok else checks[1].fail(missing)

    ok, missing = contains_all(
        evidence,
        (
            "No real staging evidence recorded yet",
            "test id",
            "test name",
            "environment",
            "timestamp",
            "operator",
            "redacted endpoint",
            "redacted token status",
            "request type",
            "expected result",
            "actual result",
            "pass/fail",
            "screenshot/log reference without secrets",
            "notes",
            "Do not record real token values",
            "Do not treat pending evidence as pass",
        ),
    )
    checks[2].pass_("evidence template has required fields and no-secret rules") if ok else checks[2].fail(missing)

    ok, missing = contains_all(
        triage,
        (
            "network / DNS / TLS",
            "backend health",
            "migration/database",
            "token auth",
            "CORS/origin",
            "forbidden field exposure",
            "unsafe customer copy",
            "automatic external action risk",
            "quote/order status mutation risk",
            "rollback failure",
            "Impact",
            "Owner",
            "Rollback Step",
            "do not claim validated",
        ),
    )
    checks[3].pass_("triage covers required failure classes and response fields") if ok else checks[3].fail(missing)

    ok, missing = contains_all(
        boundary,
        (
            "Only a complete real staging smoke test can lead to a future consideration of STAGING_VALIDATED",
            "local test",
            "dry-run",
            "script pass",
            "template pass",
            "do not count as real staging validated",
            "token",
            "origin",
            "`PUBLIC_BASE_URL`",
            "security signoff",
            "business signoff",
            "real smoke evidence",
            "D9 remains blocked",
            "Current status remains READY_FOR_STAGING_HANDOFF",
        ),
    )
    checks[4].pass_("validation boundary separates real evidence from local/template checks") if ok else checks[4].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "HOSUN",
            "raw test notes",
            "complaint details",
            "delivery risk analysis",
            "warranty cost exposure",
            "supplier private notes",
            "internal scoring",
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
            "business sign-off",
        ),
    )
    checks[5].pass_("HOSUN payload forbidden/customer-safe boundary covered") if ok else checks[5].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "No real staging evidence recorded yet",
            "No real staging credentials recorded in repository",
            "Do not write STAGING_VALIDATED",
            "Do not enter D9",
            "Do not create proof records",
            "Do not fabricate credentials",
            "Do not fabricate evidence",
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
            "real staging validated: yes",
            "production ready",
            "real credentials received",
            "real staging evidence recorded: yes",
            "smoke tests passed",
        )
        if marker in combined
    ]
    if forbidden:
        checks[6].fail(", ".join(forbidden))
    elif not ok:
        checks[6].fail(missing)
    else:
        checks[6].pass_("handoff boundary retained; no fabricated evidence/staging claim")

    continuity_paths = (
        "docs/phase3/d8_28_secure_validation_plan.md",
        "docs/phase3/d8_28_redacted_credentials_register.md",
        "docs/phase3/d8_27_security_review_readiness_checklist.md",
        "docs/phase3/d8_20_staging_handoff_contract.md",
    )
    try:
        continuity = "\n".join(read(path) for path in continuity_paths)
        ok, missing = contains_all(
            continuity,
            (
                "READY_FOR_STAGING_HANDOFF",
                "WAITING_FOR_REAL_STAGING_EVIDENCE",
                "Do not write STAGING_VALIDATED",
                "No real staging credentials recorded in repository",
                "PORTAL_CUSTOMER_API_TOKEN",
                "HOSUN",
            ),
        )
        checks[7].pass_("D8.28/D8.27/D8.20 source docs remain aligned") if ok else checks[7].fail(missing)
    except FileNotFoundError as exc:
        checks[7].fail(str(exc))

    for check in checks:
        print(check.line())

    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.29 real-staging smoke template check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1

    print("\nD8.29 real-staging smoke template check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
