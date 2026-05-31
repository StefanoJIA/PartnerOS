"""Validate the developer guide's current local D8 handoff guidance."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "dev_guide.md"

REQUIRED_MARKERS = (
    "PartnerOS Developer Guide",
    "READY_FOR_STAGING_HANDOFF",
    "does not mean `STAGING_VALIDATED`",
    "human Go / No-Go handoff",
    "docs/records/d8_production_go_no_go_YYYYMMDD.md",
    "service.intelli-opus.com",
    "Manufacturing partners are peer rows",
    "No product path may require final users to run pgAdmin",
    "Do not auto-send email, webhooks, carrier API calls",
    "python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8014",
    '$env:BACKEND_BASE_URL="http://127.0.0.1:8014"',
    '$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"',
    "SERVICE_PORTAL_PARTNEROS_TOKEN",
    "d7_7_portal_bridge_check.py",
    "d7_6_shipment_tracking_check.py",
    "dev_guide_check.py",
    "project_execution_chain_check.py",
    "project_execution_status.py",
    "npm run test -- --run",
    "strict whitelists",
    "Manual records remain manual",
    "d8_staging_access_request.md",
)
FORBIDDEN_MARKERS = (
    "D0-D5.2",
    "D0鈥",
    "D5.2.2",
    "Phase 1",
    "current D0",
    "8000 琚",
    "8010 绀",
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
        Check("developer guide exists"),
        Check("developer guide contains current D8 handoff workflow"),
        Check("developer guide avoids stale D0/D5 local setup markers"),
        Check("developer guide is redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/dev_guide.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    stale = [marker for marker in FORBIDDEN_MARKERS[:7] if marker in text]
    checks[2].pass_("no stale phase or port markers") if not stale else checks[2].fail(", ".join(stale))

    redaction = [marker for marker in FORBIDDEN_MARKERS[7:] if marker in text]
    redaction.extend(_redaction_issues(text))
    checks[3].pass_("no secret-like markers") if not redaction else checks[3].fail(", ".join(redaction[:8]))

    print("Developer Guide Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
