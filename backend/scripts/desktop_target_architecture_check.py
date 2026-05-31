"""Validate current desktop target architecture guidance."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "architecture_desktop_target.md"

REQUIRED_MARKERS = (
    "Desktop Target Architecture",
    "current on 2026-05-30",
    "READY_FOR_STAGING_HANDOFF",
    "does not mean `STAGING_VALIDATED`",
    "Vue/Vite frontend with a FastAPI backend and PostgreSQL/pgvector",
    "No final-user path may require users to run PostgreSQL, pgAdmin, Docker, Alembic, or raw SQL",
    '$env:BACKEND_BASE_URL="http://127.0.0.1:8014"',
    "project_execution_chain_gate_check.py",
    "SERVICE_PORTAL_PARTNEROS_TOKEN",
    "service.intelli-opus.com",
    "must not edit nginx",
    "explicit allowlists",
    "shipment plans remain operator-recorded",
    "do not automatically change order status to shipped/delivered",
    "Product Vision",
    "Project Reorientation Summary",
)
FORBIDDEN_MARKERS = (
    "涓",
    "锛",
    "鈥",
    "搂",
    "D0-D5.2",
    "Phase 1",
    "D0 only",
    "STAGING_VALIDATED evidence is local",
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
        Check("desktop target architecture doc exists"),
        Check("desktop target architecture matches current state"),
        Check("desktop target architecture avoids stale or mojibake markers"),
        Check("desktop target architecture is redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/architecture_desktop_target.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    stale = [marker for marker in FORBIDDEN_MARKERS[:8] if marker in text]
    checks[2].pass_("no stale stage or mojibake markers") if not stale else checks[2].fail(", ".join(stale))

    redaction = [marker for marker in FORBIDDEN_MARKERS[8:] if marker in text]
    redaction.extend(_redaction_issues(text))
    checks[3].pass_("no secret-like markers") if not redaction else checks[3].fail(", ".join(redaction[:8]))

    print("Desktop Target Architecture Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
