"""Validate the historical D5.2 testing summary boundary."""

from __future__ import annotations

from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "testing_summary_d5_2.md"

REQUIRED_MARKERS = (
    "D5.2 Testing Summary",
    "historical baseline from 2026-05-23",
    "superseded for current validation on 2026-05-30",
    "not the current D8/D9 validation matrix",
    "READY_FOR_STAGING_HANDOFF",
    "STAGING_VALIDATED",
    "WAITING_FOR_REAL_STAGING_EVIDENCE",
    "http://127.0.0.1:8014",
    "python scripts/project_execution_chain_gate_check.py",
    "python scripts/project_execution_chain_check.py",
    "python scripts/d8_staging_execution_pack_check.py",
    "python scripts/project_execution_acceptance_audit_check.py",
    "python scripts/testing_summary_d5_2_check.py",
    "D7 order, production, shipment, portal bridge, or resource-center workflows",
    "D8 RBAC, runtime hardening, partner operations, market response, or staging evidence",
    "service.intelli-opus.com",
)
FORBIDDEN_MARKERS = (
    "娑?",
    "閿?",
    "閳?",
    "鎼?",
    "锛",
    "鈥",
    "鈫?",
    "Production HTTPS / reverse proxy",
    "Default `BACKEND_BASE_URL=http://127.0.0.1:8000`",
    "SERVICE_PORTAL_PARTNEROS_TOKEN=",
    "PORTAL_CUSTOMER_API_TOKEN=",
    "Bearer ",
    "raw response body:",
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


def main() -> int:
    checks = [
        Check("D5.2 testing summary exists"),
        Check("D5.2 testing summary declares historical boundary"),
        Check("D5.2 testing summary avoids stale or mojibake markers"),
        Check("D5.2 testing summary is redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/testing_summary_d5_2.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    stale = [marker for marker in FORBIDDEN_MARKERS[:9] if marker in text]
    checks[2].pass_("no stale current-validation or mojibake markers") if not stale else checks[2].fail(", ".join(stale))

    redaction = [marker for marker in FORBIDDEN_MARKERS[9:] if marker.lower() in text.lower()]
    redaction.extend(redaction_issues(DOC, text, include_common_markers=False))
    checks[3].pass_("no secret-like markers") if not redaction else checks[3].fail(", ".join(redaction[:8]))

    print("D5.2 Testing Summary Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
