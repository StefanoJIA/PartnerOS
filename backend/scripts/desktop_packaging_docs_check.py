"""Validate desktop packaging strategy and open-question docs."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGING_DOC = REPO_ROOT / "docs" / "packaging_strategy.md"
QUESTIONS_DOC = REPO_ROOT / "docs" / "open_questions_desktop.md"

REQUIRED_PACKAGING_MARKERS = (
    "Packaging Strategy",
    "current on 2026-05-30",
    "READY_FOR_STAGING_HANDOFF",
    "frontend/src-tauri",
    "Tauri 2",
    "sidecar_entry.py",
    "intellioffice-backend",
    "http://127.0.0.1:17888/health",
    "port `8014`",
    "PostgreSQL + pgvector remains the authoritative store",
    "Do not replace the PostgreSQL + pgvector architecture with SQLite",
    "Do not require final users to run PostgreSQL, pgAdmin, Docker, Alembic, or raw SQL",
    "service.intelli-opus.com",
    "python scripts/desktop_packaging_docs_check.py",
    "python scripts/project_execution_chain_gate_check.py",
    "python scripts/d8_staging_execution_pack_check.py",
    "python scripts/project_execution_acceptance_audit_check.py",
    "STAGING_VALIDATED",
)
REQUIRED_QUESTIONS_MARKERS = (
    "Open Questions: Desktop & Packaging",
    "current on 2026-05-30",
    "READY_FOR_STAGING_HANDOFF",
    "Tauri 2",
    "Electron",
    "MSI, NSIS, WiX",
    "PostgreSQL + pgvector remains authoritative",
    "Do not introduce SQLite",
    "Do not require final users to run PostgreSQL, pgAdmin, Docker, Alembic, or raw SQL",
    "service.intelli-opus.com",
    "python scripts/desktop_packaging_docs_check.py",
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
    "production desktop packaging is complete",
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


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _redaction_issues(path: Path, text: str) -> list[str]:
    issues: list[str] = []
    for line in text.splitlines():
        if TOKEN_ASSIGNMENT.search(line) and "<portal-server-token>" not in line:
            issues.append("SERVICE_PORTAL_PARTNEROS_TOKEN=<non-placeholder>")
    issues.extend(redaction_issues(path, text, include_common_markers=False))
    return issues


def main() -> int:
    checks = [
        Check("desktop packaging docs exist"),
        Check("packaging strategy matches current desktop boundary"),
        Check("open questions match current desktop boundary"),
        Check("desktop packaging docs avoid stale or mojibake markers"),
        Check("desktop packaging docs are redacted"),
    ]

    packaging = _text(PACKAGING_DOC)
    questions = _text(QUESTIONS_DOC)
    if packaging and questions:
        checks[0].pass_("packaging_strategy.md, open_questions_desktop.md")
    else:
        checks[0].fail(", ".join(str(path) for path, text in ((PACKAGING_DOC, packaging), (QUESTIONS_DOC, questions)) if not text))

    missing_packaging = [marker for marker in REQUIRED_PACKAGING_MARKERS if marker not in packaging]
    checks[1].pass_(f"{len(REQUIRED_PACKAGING_MARKERS)} markers") if not missing_packaging else checks[1].fail(", ".join(missing_packaging))

    missing_questions = [marker for marker in REQUIRED_QUESTIONS_MARKERS if marker not in questions]
    checks[2].pass_(f"{len(REQUIRED_QUESTIONS_MARKERS)} markers") if not missing_questions else checks[2].fail(", ".join(missing_questions))

    combined = f"{packaging}\n{questions}"
    stale = [marker for marker in FORBIDDEN_MARKERS[:10] if marker in combined]
    checks[3].pass_("no stale stage or mojibake markers") if not stale else checks[3].fail(", ".join(stale))

    redaction = [marker for marker in FORBIDDEN_MARKERS[10:] if marker.lower() in combined.lower()]
    redaction.extend(_redaction_issues(PACKAGING_DOC, packaging))
    redaction.extend(_redaction_issues(QUESTIONS_DOC, questions))
    checks[4].pass_("no secret-like markers") if not redaction else checks[4].fail(", ".join(redaction[:8]))

    print("Desktop Packaging Docs Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
