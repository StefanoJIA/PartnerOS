"""Validate current runtime modes guidance."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "runtime_modes.md"

REQUIRED_MARKERS = (
    "Runtime Modes",
    "current on 2026-05-30",
    "READY_FOR_STAGING_HANDOFF",
    "does not prove `STAGING_VALIDATED`",
    "WAITING_FOR_REAL_STAGING_EVIDENCE",
    "until real staging evidence replaces it",
    "`development`",
    "`desktop`",
    "`demo`",
    "`future_cloud`",
    "Preferred local D7.6+/D8 validation port",
    '$env:BACKEND_BASE_URL="http://127.0.0.1:8014"',
    "project_execution_chain_gate_check.py",
    "d8_staging_execution_pack_check.py",
    "project_execution_acceptance_audit_check.py",
    "SERVICE_PORTAL_PARTNEROS_TOKEN",
    "SERVICE_PORTAL_ORIGIN",
    "service.intelli-opus.com",
    "database_lifecycle_phase",
    "Do not automatically mutate orders to shipped/delivered",
    "Do not require final users to run PostgreSQL, pgAdmin, Docker, Alembic, or raw SQL",
    "D8 Staging Handoff Bundle",
)
FORBIDDEN_MARKERS = (
    "涓",
    "锛",
    "鈥",
    "搂",
    "D0-D5.2",
    "Phase 1",
    "default development examples may use `8010`",
    "local checks prove STAGING_VALIDATED",
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
        Check("runtime modes doc exists"),
        Check("runtime modes match current D8 state"),
        Check("runtime modes avoid stale or mojibake markers"),
        Check("runtime modes are redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/runtime_modes.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    stale = [marker for marker in FORBIDDEN_MARKERS[:8] if marker in text]
    checks[2].pass_("no stale stage, port, or mojibake markers") if not stale else checks[2].fail(", ".join(stale))

    redaction = [marker for marker in FORBIDDEN_MARKERS[8:] if marker in text]
    redaction.extend(_redaction_issues(text))
    checks[3].pass_("no secret-like markers") if not redaction else checks[3].fail(", ".join(redaction[:8]))

    print("Runtime Modes Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
