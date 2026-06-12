"""D8.27 security review readiness documentation check."""

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
        Check("D8.27 required files"),
        Check("security review readiness checklist"),
        Check("secret handling dry-run"),
        Check("forbidden field audit matrix"),
        Check("security signoff template"),
        Check("HOSUN security boundary"),
        Check("handoff boundary and no forbidden claims"),
        Check("D8.26/D8.25 continuity"),
    ]

    required_files = (
        "docs/phase3/d8_27_security_review_readiness_checklist.md",
        "docs/phase3/d8_27_secret_handling_dry_run.md",
        "docs/phase3/d8_27_forbidden_field_audit_matrix.md",
        "docs/phase3/d8_27_security_signoff_template.md",
    )
    missing_files = [path for path in required_files if not (ROOT / path).exists()]
    if missing_files:
        checks[0].fail(", ".join(missing_files))
        for check in checks:
            print(check.line())
        return 1
    checks[0].pass_("security checklist, dry-run, audit matrix, and signoff template exist")

    readiness = read(required_files[0])
    dry_run = read(required_files[1])
    matrix = read(required_files[2])
    signoff = read(required_files[3])
    combined = "\n".join([readiness, dry_run, matrix, signoff])

    ok, missing = contains_all(
        readiness,
        (
            "token storage / rotation / revocation",
            "CORS / allowed origins / no wildcard",
            "server-to-server Portal bridge",
            "Browser must not see token values",
            "Logs must not include token values",
            "Docs must not contain secret values",
            "customer-safe whitelist",
            "forbidden fields blacklist",
            "rollback / disable Portal API",
            "no automatic external sending",
            "no quote/order auto-status-change",
            "PORTAL_CUSTOMER_API_ENABLED=false",
            "PORTAL_CUSTOMER_API_TOKEN",
            "PORTAL_CUSTOMER_ALLOWED_ORIGINS",
        ),
    )
    checks[1].pass_("readiness checklist covers token, CORS, bridge, whitelist, rollback, automation boundaries") if ok else checks[1].fail(missing)

    ok, missing = contains_all(
        dry_run,
        (
            "no real token is used",
            "wrong/missing token should fail safely",
            "disabled state should fail safely",
            "token values must not be written into docs",
            "token values must not appear in log examples",
            ".env",
            "local_data/",
            "backend/storage/",
            "generated PDFs",
            "IE Auto.pdf",
            "dry-run only",
            "not real security approval",
        ),
    )
    checks[2].pass_("dry-run records no-token handling and non-approval boundary") if ok else checks[2].fail(missing)

    ok, missing = contains_all(
        matrix,
        (
            "products",
            "orders",
            "order detail",
            "production milestones",
            "shipment status",
            "resources",
            "feedback status",
            "Market Response preview",
            "Allowed Customer-Safe Fields",
            "Forbidden Fields",
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
            "internal audit events",
            "internal owner notes",
            "unreviewed risk notes",
            "internal Market Response scoring/ranking",
        ),
    )
    checks[3].pass_("audit matrix covers required areas and forbidden fields") if ok else checks[3].fail(missing)

    ok, missing = contains_all(
        signoff,
        (
            "Reviewer",
            "Date",
            "Scope",
            "token storage approved",
            "CORS approved",
            "forbidden fields reviewed",
            "logs reviewed",
            "rollback approved",
            "Required Fixes",
            "Signoff status",
            "pending / approved / changes required",
            "No real security sign-off recorded yet",
            "Pending does not mean approved",
        ),
    )
    checks[4].pass_("security signoff template has reviewer, gate checks, fixes, and pending status") if ok else checks[4].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "HOSUN lifting systems",
            "raw test notes",
            "complaint details",
            "delivery risk analysis",
            "warranty cost exposure",
            "supplier private notes",
            "internal Market Response scoring",
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
            "business confirmation",
        ),
    )
    checks[5].pass_("HOSUN internal-only and customer-safe boundaries covered") if ok else checks[5].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "No real security sign-off recorded yet",
            "Pending does not mean approved",
            "Do not enter D9",
            "Do not create proof records",
            "Do not write STAGING_VALIDATED",
            "Do not fabricate real security approval",
            "Do not process real token values",
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
            "real security approved",
            "real security sign-off completed",
            "security approval complete",
        )
        if marker in combined
    ]
    if forbidden:
        checks[6].fail(", ".join(forbidden))
    elif not ok:
        checks[6].fail(missing)
    else:
        checks[6].pass_("handoff boundary retained; no fabricated approval or staging claim")

    continuity_paths = (
        "docs/phase3/d8_26_business_owner_signoff_checklist.md",
        "docs/phase3/d8_26_customer_safe_wording_review.md",
        "docs/phase3/d8_25_customer_safe_copy_rules.md",
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
                "customer-safe",
                "forbidden",
                "HOSUN",
            ),
        )
        checks[7].pass_("D8.26/D8.25/D8.20 source docs remain aligned") if ok else checks[7].fail(missing)
    except FileNotFoundError as exc:
        checks[7].fail(str(exc))

    for check in checks:
        print(check.line())

    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.27 security review readiness check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1

    print("\nD8.27 security review readiness check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
