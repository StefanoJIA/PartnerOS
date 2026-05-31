"""Validate current integrated backend standards."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "integrated_backend_standards.md"

REQUIRED_MARKERS = (
    "Integrated Backend Standards",
    "current on 2026-05-30",
    "D7 order, confirmation, partner/supplier, production milestone, portal bridge, feedback intake, and shipment plan foundations are closed through D7.9",
    "READY_FOR_STAGING_HANDOFF",
    "STAGING_VALIDATED",
    "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "human Go / No-Go handoff",
    "docs/records/d8_production_go_no_go_YYYYMMDD.md",
    "service.intelli-opus.com",
    "/api/v1/portal/customer/*",
    "Strict customer-visible DTOs only",
    "explicit allowlists",
    "shipment summaries from manual shipment plans",
    "customer feedback tickets",
    "Do not auto-send email, webhooks, carrier API calls",
    "automatic shipped/delivered status",
    "Manufacturing partners are peer rows",
    "Never require final users to run PostgreSQL, pgAdmin, Docker, Alembic, or raw SQL",
    '$env:BACKEND_BASE_URL="http://127.0.0.1:8014"',
    '$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"',
    "SERVICE_PORTAL_PARTNEROS_TOKEN",
    "integrated_backend_standards_check.py",
    "project_execution_chain_gate_check.py",
    "d8_staging_execution_pack_check.py",
)
FORBIDDEN_MARKERS = (
    "D0-D5.2",
    "D0鈥",
    "Phase 1",
    "Portal SSO",
    "Big-bang",
    "8000",
    "8010",
    "PORTAL_CUSTOMER_API_TOKEN=",
    "Bearer ",
    "raw response body:",
    "password_hash",
    "database_url",
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
        Check("integrated backend standards doc exists"),
        Check("integrated backend standards match current D7-D9 state"),
        Check("integrated backend standards avoid stale early-phase markers"),
        Check("integrated backend standards are redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/integrated_backend_standards.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    stale = [marker for marker in FORBIDDEN_MARKERS[:7] if marker in text]
    checks[2].pass_("no stale phase or port markers") if not stale else checks[2].fail(", ".join(stale))

    redaction = [marker for marker in FORBIDDEN_MARKERS[7:] if marker in text]
    redaction.extend(_redaction_issues(text))
    checks[3].pass_("no secret-like markers") if not redaction else checks[3].fail(", ".join(redaction[:8]))

    print("Integrated Backend Standards Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
