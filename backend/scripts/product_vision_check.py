"""Validate current product vision guidance."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "product_vision.md"

REQUIRED_MARKERS = (
    "Product Vision",
    "current on 2026-05-30",
    "service.intelli-opus.com",
    "READY_FOR_STAGING_HANDOFF",
    "WAITING_FOR_REAL_STAGING_EVIDENCE",
    "until real staging evidence replaces it",
    "STAGING_VALIDATED",
    "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "human Go / No-Go handoff",
    "docs/records/d8_production_go_no_go_YYYYMMDD.md",
    "D7 is closed through D7.9",
    "Lead Intelligence belongs inside this loop",
    "peer manufacturing partner rows",
    "Do not hard-code, default, or prioritize any partner by trade name",
    "AI is advisory",
    "Customer-visible data must be explicitly whitelisted",
    "Feedback intake creates internal review work only",
    "Manual-Only Safety",
    "Shipment plans do not call carriers",
    "automatically change an order to shipped/delivered",
    "python scripts/d8_staging_execution_pack_check.py",
    "python scripts/d9_operating_execution_pack_check.py",
    "python scripts/project_execution_acceptance_audit_check.py",
    "Project Reorientation Summary",
    "Integrated Backend Standards",
)
FORBIDDEN_MARKERS = (
    "涓",
    "锛",
    "鈥",
    "搂",
    "[](../README.md)",
    "D0-D5.2",
    "Phase 1",
    "PartnerOS replaces service.intelli-opus.com",
    "PORTAL_CUSTOMER_API_TOKEN=",
    "Bearer ",
    "raw response body:",
    "password_hash",
)
TOKEN_ASSIGNMENT = re.compile(r"SERVICE_PORTAL_PARTNEROS_TOKEN\s*=")


class Check:
    def __init__(self, label: str) -> None:
        self.label = label
        self.ok = False
        self.detail = ""

    def pass_(self, detail: str = "") -> None:
        self.ok = True
        self.detail = detail

    def fail(self, detail: str) -> None:
        self.ok = False
        self.detail = detail

    def line(self) -> str:
        status = "PASS" if self.ok else "FAIL"
        suffix = f" ({self.detail})" if self.detail else ""
        return f"[{status}] {self.label}{suffix}"


def _text() -> str:
    try:
        return DOC.read_text(encoding="utf-8")
    except OSError:
        return ""


def _redaction_issues(text: str) -> list[str]:
    issues: list[str] = []
    for line in text.splitlines():
        if TOKEN_ASSIGNMENT.search(line) and "<portal-server-token>" not in line:
            issues.append("SERVICE_PORTAL_PARTNEROS_TOKEN=<non-placeholder>")
    issues.extend(redaction_issues(DOC, text, include_common_markers=False))
    return issues


def main() -> int:
    checks = [
        Check("product vision doc exists"),
        Check("product vision matches current execution state"),
        Check("product vision avoids stale or mojibake markers"),
        Check("product vision is redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/product_vision.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    stale = [marker for marker in FORBIDDEN_MARKERS[:8] if marker in text]
    checks[2].pass_("no stale stage, bad link, or mojibake markers") if not stale else checks[2].fail(
        ", ".join(stale)
    )

    redaction = [marker for marker in FORBIDDEN_MARKERS[8:] if marker in text]
    redaction.extend(_redaction_issues(text))
    checks[3].pass_("no secret-like markers") if not redaction else checks[3].fail(", ".join(redaction[:8]))

    print("Product Vision Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
