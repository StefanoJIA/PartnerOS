"""Validate current database lifecycle guidance."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "database_lifecycle.md"

REQUIRED_MARKERS = (
    "Database Lifecycle",
    "current on 2026-05-30",
    "PostgreSQL + pgvector remains the authoritative",
    "READY_FOR_STAGING_HANDOFF",
    "STAGING_VALIDATED",
    "WAITING_FOR_REAL_STAGING_EVIDENCE",
    "until real staging evidence replaces it",
    "backend/app/core/database_lifecycle.py",
    "database_lifecycle_phase",
    "migration_pending",
    "alembic_current_revision",
    "alembic_head_revision",
    "auth_failed",
    "database_missing",
    "Do not require final users to run PostgreSQL, pgAdmin, Docker, Alembic, or raw SQL",
    '$env:BACKEND_BASE_URL="http://127.0.0.1:8014"',
    "SERVICE_PORTAL_PARTNEROS_TOKEN",
    "D8 Staging Operator Runbook",
)
FORBIDDEN_MARKERS = (
    "娑?",
    "閿?",
    "閳?",
    "鎼?",
    "锛",
    "鈥",
    "D0-D5.2",
    "Phase 1",
    "local checks prove STAGING_VALIDATED",
    "SERVICE_PORTAL_PARTNEROS_TOKEN=",
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
        Check("database lifecycle doc exists"),
        Check("database lifecycle matches current D8 state"),
        Check("database lifecycle avoids stale or mojibake markers"),
        Check("database lifecycle is redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/database_lifecycle.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    stale = [marker for marker in FORBIDDEN_MARKERS[:9] if marker in text]
    checks[2].pass_("no stale stage or mojibake markers") if not stale else checks[2].fail(", ".join(stale))

    redaction = [marker for marker in FORBIDDEN_MARKERS[9:] if marker.lower() in text.lower()]
    redaction.extend(_redaction_issues(text))
    checks[3].pass_("no secret-like markers") if not redaction else checks[3].fail(", ".join(redaction[:8]))

    print("Database Lifecycle Doc Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
