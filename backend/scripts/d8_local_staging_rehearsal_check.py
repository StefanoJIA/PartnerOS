"""Validate the D8 local staging rehearsal runbook."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "phase3" / "d8_local_staging_rehearsal.md"

REQUIRED_MARKERS = (
    "D8 Local Staging Rehearsal",
    "not a substitute for the real staging run",
    "BACKEND_BASE_URL",
    "http://127.0.0.1:8014",
    "SERVICE_PORTAL_PARTNEROS_TOKEN",
    "<local-non-default-token>",
    "SERVICE_PORTAL_ORIGIN",
    "D8_STRICT_ALLOW_LOCAL_HTTP",
    "python scripts/d8_staging_input_preflight_check.py",
    "python scripts/d8_strict_staging_evidence_check.py",
    "LOCAL_REHEARSAL_READY",
    "$env:TEMP",
    "d8_strict_staging_evidence_YYYYMMDD.json",
    "outside `docs/records`",
    "READY_FOR_STAGING",
    "WAITING_FOR_REAL_STAGING_EVIDENCE",
    "until strict staging evidence from real staging values replaces it",
    "STAGING_VALIDATED",
    "STAGING_GAPS_OPEN",
    "strict evidence script rejects local rehearsal output paths under `docs/records`",
    "Do not commit rehearsal evidence as staging proof",
    "No `.env`",
    "No email, webhook, carrier API",
)
FORBIDDEN_MARKERS = (
    "PORTAL_CUSTOMER_API_TOKEN=",
    "Bearer ",
    "password_hash",
    "database_url",
)


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


def _missing(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def _forbidden(text: str) -> list[str]:
    issues: list[str] = []
    for marker in FORBIDDEN_MARKERS:
        if marker in text:
            issues.append(marker)
    for line in text.splitlines():
        if "SERVICE_PORTAL_PARTNEROS_TOKEN" in line and "=" in line and "<local-non-default-token>" not in line:
            issues.append("SERVICE_PORTAL_PARTNEROS_TOKEN=<non-placeholder>")
    return issues


def main() -> int:
    checks = [
        Check("D8 local staging rehearsal doc exists"),
        Check("D8 local staging rehearsal doc is actionable"),
        Check("D8 local staging rehearsal keeps safety boundaries"),
    ]

    text = _text()
    checks[0].pass_("docs/phase3/d8_local_staging_rehearsal.md") if text else checks[0].fail(str(DOC))

    missing = _missing(text, REQUIRED_MARKERS)
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    forbidden = _forbidden(text)
    checks[2].pass_("redacted") if not forbidden else checks[2].fail(", ".join(forbidden))

    print("D8 Local Staging Rehearsal Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
