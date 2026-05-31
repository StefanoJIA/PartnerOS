"""Validate the Web-to-desktop migration guidance."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "migration_from_web_to_desktop.md"

REQUIRED_MARKERS = (
    "Migration From Web Development To Desktop Product",
    "current on 2026-05-30",
    "READY_FOR_STAGING_HANDOFF",
    "STAGING_VALIDATED",
    "WAITING_FOR_REAL_STAGING_EVIDENCE",
    "until real staging evidence replaces it",
    "Vue/Vite",
    "FastAPI",
    "PostgreSQL + pgvector",
    "Tauri shell",
    "backend sidecar",
    "database lifecycle",
    "D7 order, production milestone, shipment plan, portal bridge, and resource center boundaries",
    "D8 RBAC, runtime hardening, partner operations, and market response intelligence",
    "Do not fork a second desktop-only business codebase",
    "Final users should not run separate frontend/backend commands, PostgreSQL, pgAdmin, Docker, Alembic, raw SQL, or seed scripts",
    "no unreviewed SQLite replacement for PostgreSQL + pgvector",
    "backend port `8014`",
    "SERVICE_PORTAL_PARTNEROS_TOKEN",
    "service.intelli-opus.com",
    "python scripts/web_to_desktop_migration_doc_check.py",
    "python scripts/project_execution_chain_gate_check.py",
    "python scripts/d8_staging_execution_pack_check.py",
    "python scripts/project_execution_acceptance_audit_check.py",
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
        Check("Web-to-desktop migration doc exists"),
        Check("Web-to-desktop migration doc matches current state"),
        Check("Web-to-desktop migration doc avoids stale or mojibake markers"),
        Check("Web-to-desktop migration doc is redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/migration_from_web_to_desktop.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    stale = [marker for marker in FORBIDDEN_MARKERS[:9] if marker in text]
    checks[2].pass_("no stale stage or mojibake markers") if not stale else checks[2].fail(", ".join(stale))

    redaction = [marker for marker in FORBIDDEN_MARKERS[9:] if marker.lower() in text.lower()]
    redaction.extend(_redaction_issues(text))
    checks[3].pass_("no secret-like markers") if not redaction else checks[3].fail(", ".join(redaction[:8]))

    print("Web To Desktop Migration Doc Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
