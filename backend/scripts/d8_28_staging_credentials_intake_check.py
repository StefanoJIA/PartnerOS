"""D8.28 staging credentials intake documentation check."""

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
        Check("D8.28 required files"),
        Check("staging credentials intake playbook"),
        Check("secure validation plan"),
        Check("redacted credentials register"),
        Check("staging Go/No-Go checklist"),
        Check("HOSUN sign-off conditions"),
        Check("JOOBOO and future partner sign-off conditions"),
        Check("handoff boundary and no forbidden claims"),
        Check("D8.27/D8.26 continuity"),
    ]

    required_files = (
        "docs/phase3/d8_28_staging_credentials_intake_playbook.md",
        "docs/phase3/d8_28_secure_validation_plan.md",
        "docs/phase3/d8_28_redacted_credentials_register.md",
        "docs/phase3/d8_28_staging_go_no_go_checklist.md",
    )
    missing_files = [path for path in required_files if not (ROOT / path).exists()]
    if missing_files:
        checks[0].fail(", ".join(missing_files))
        for check in checks:
            print(check.line())
        return 1
    checks[0].pass_("intake playbook, validation plan, register, and Go/No-Go checklist exist")

    playbook = read(required_files[0])
    validation = read(required_files[1])
    register = read(required_files[2])
    go_no_go = read(required_files[3])
    combined = "\n".join([playbook, validation, register, go_no_go])

    ok, missing = contains_all(
        playbook,
        (
            "Who",
            "backend HTTPS origin",
            "service.intelli-opus.com real origin",
            "PORTAL_CUSTOMER_API_ENABLED",
            "PORTAL_CUSTOMER_API_TOKEN",
            "PORTAL_CUSTOMER_ALLOWED_ORIGINS",
            "PUBLIC_BASE_URL",
            "secure channel",
            "Do not write token values into",
            "token: PROVIDED_VIA_SECURE_CHANNEL",
            "PENDING_REAL_VALUE",
            "If any real value is not available, mark the item `pending`",
            "Rollback / Disable Procedure",
        ),
    )
    checks[1].pass_("playbook covers credential owners, secure channel, redacted values, and rollback") if ok else checks[1].fail(missing)

    ok, missing = contains_all(
        validation,
        (
            "backend HTTPS `/health`",
            "Portal bridge readiness",
            "`enabled=true` only in staging",
            "correct token success",
            "missing token fail",
            "wrong token fail",
            "allowed origin success",
            "disallowed origin fail",
            "`PUBLIC_BASE_URL` correct",
            "customer-safe payload has no forbidden fields",
            "feedback submit does not auto-reply",
            "Portal read does not auto-change quote/order status",
            "no external notifications",
            "rollback drill",
        ),
    )
    checks[2].pass_("validation plan has required secure validation sequence") if ok else checks[2].fail(missing)

    ok, missing = contains_all(
        register,
        (
            "No real staging credentials recorded in repository.",
            "Item",
            "Owner",
            "Status",
            "pending",
            "received via secure channel",
            "configured",
            "verified",
            "rejected",
            "Redacted Value Only",
            "Verification Owner",
            "Verification Date",
            "Notes",
            "PROVIDED_VIA_SECURE_CHANNEL",
            "Do not record token value",
        ),
    )
    checks[3].pass_("register is redacted-only and includes required columns/statuses") if ok else checks[3].fail(missing)

    ok, missing = contains_all(
        go_no_go,
        (
            "backend HTTPS origin verified",
            "token configured securely",
            "CORS allowed origin verified",
            "disallowed origin rejected",
            "forbidden fields absent",
            "security signoff approved",
            "business owner signoff approved",
            "UAT seed data approved",
            "rollback owner assigned",
            "P0 blockers absent",
            "allow real staging UAT",
            "still forbidden until real smoke test passes and is reviewed",
            "No-Go",
            "Conditional Go",
            "Go",
        ),
    )
    checks[4].pass_("Go/No-Go checklist covers required gates and decision outcomes") if ok else checks[4].fail(missing)

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
            "business owner approval",
        ),
    )
    checks[5].pass_("HOSUN staging sign-off conditions covered") if ok else checks[5].fail(missing)

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
    checks[6].pass_("JOOBOO and future partner sign-off conditions covered") if ok else checks[6].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "No real staging credentials recorded in repository",
            "Pending does not mean approved",
            "Do not enter D9",
            "Do not create proof records",
            "Do not write STAGING_VALIDATED",
            "Do not fabricate credentials",
            "Do not fabricate sign-off",
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
            "real staging validated",
            "production ready",
            "real credentials received",
            "token configured securely: approved",
            "security approval complete",
            "business owner approval complete",
        )
        if marker in combined
    ]
    if forbidden:
        checks[7].fail(", ".join(forbidden))
    elif not ok:
        checks[7].fail(missing)
    else:
        checks[7].pass_("handoff boundary retained; no fabricated credentials/sign-off/staging claim")

    continuity_paths = (
        "docs/phase3/d8_27_security_review_readiness_checklist.md",
        "docs/phase3/d8_27_secret_handling_dry_run.md",
        "docs/phase3/d8_26_business_owner_signoff_checklist.md",
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
                "No real security sign-off recorded yet",
                "No real business owner sign-off recorded yet",
                "PORTAL_CUSTOMER_API_TOKEN",
                "HOSUN",
            ),
        )
        checks[8].pass_("D8.27/D8.26/D8.20 source docs remain aligned") if ok else checks[8].fail(missing)
    except FileNotFoundError as exc:
        checks[8].fail(str(exc))

    for check in checks:
        print(check.line())

    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.28 staging credentials intake check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1

    print("\nD8.28 staging credentials intake check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
