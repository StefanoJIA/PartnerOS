"""Validate the D8 staging access request handoff."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "phase3" / "d8_staging_access_request.md"

REQUIRED_MARKERS = (
    "READY_FOR_STAGING_HANDOFF",
    "STAGING_VALIDATED",
    "WAITING_FOR_REAL_STAGING_EVIDENCE",
    "until strict staging evidence from real staging values replaces it",
    "BACKEND_BASE_URL",
    "SERVICE_PORTAL_PARTNEROS_TOKEN",
    "SERVICE_PORTAL_ORIGIN",
    "DEPLOYED_COMMIT",
    "TEST_DATA_SCOPE",
    "scripts/d8_strict_staging_evidence_check.py",
    "--evidence-json",
    "--gap-markdown",
    "python scripts/d8_staging_records_check.py",
    "python scripts/d8_readiness_audit.py",
    "provided privately",
    "<portal-server-token>",
)
REQUIRED_BOUNDARIES = (
    "Do not commit `.env`",
    "Do not deploy or modify `service.intelli-opus.com`",
    "Do not create non-TEST feedback",
    "Do not call carrier APIs",
    "Do not expose internal cost",
)
FORBIDDEN_MARKERS = (
    "Bearer ",
    "raw response body",
)
TOKEN_ASSIGNMENT = re.compile(r"SERVICE_PORTAL_PARTNEROS_TOKEN\s*=")
TOKEN_STATUS = re.compile(r"^\s*SERVICE_PORTAL_PARTNEROS_TOKEN\s*:\s*(?P<value>.+?)\s*$", re.IGNORECASE)
BACKEND_URL_STATUS = re.compile(r"^\s*BACKEND_BASE_URL\s*:\s*(?P<value>.+?)\s*$", re.IGNORECASE)


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
    return DOC.read_text(encoding="utf-8") if DOC.exists() else ""


def _missing(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def _forbidden(text: str) -> list[str]:
    forbidden = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    forbidden.extend(redaction_issues(DOC, text, include_common_markers=False))
    for line in text.splitlines():
        backend_url = BACKEND_URL_STATUS.match(line)
        if backend_url and backend_url.group("value").strip() != "provided privately":
            forbidden.append("BACKEND_BASE_URL:<non-private-status>")
        status = TOKEN_STATUS.match(line)
        if status and status.group("value").strip() != "provided privately":
            forbidden.append("SERVICE_PORTAL_PARTNEROS_TOKEN:<non-private-status>")
        if TOKEN_ASSIGNMENT.search(line) and "<portal-server-token>" not in line:
            forbidden.append("SERVICE_PORTAL_PARTNEROS_TOKEN=<non-placeholder>")
            break
    return forbidden


def main() -> int:
    checks = [
        Check("staging access request exists"),
        Check("requested inputs and command markers"),
        Check("safety boundaries"),
        Check("no secret-like or local-path markers"),
    ]

    text = _text()
    checks[0].pass_("docs/phase3/d8_staging_access_request.md") if text else checks[0].fail(str(DOC))

    missing = _missing(text, REQUIRED_MARKERS)
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    missing_boundaries = _missing(text, REQUIRED_BOUNDARIES)
    checks[2].pass_("documented") if not missing_boundaries else checks[2].fail(", ".join(missing_boundaries))

    forbidden = _forbidden(text)
    checks[3].pass_("redacted") if not forbidden else checks[3].fail(", ".join(forbidden))

    print("D8 Staging Access Request Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
