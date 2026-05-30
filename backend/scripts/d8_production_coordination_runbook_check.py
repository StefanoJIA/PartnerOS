"""Validate the D8 production coordination runbook."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "phase3" / "d8_production_coordination_runbook.md"

REQUIRED_MARKERS = (
    "D8 Production Coordination Runbook",
    "STAGING_VALIDATED",
    "BLOCKED_BY_EVIDENCE_REVIEW",
    "READY_FOR_PRODUCTION_COORDINATION",
    "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "WAITING_FOR_STAGING_VALIDATION",
    "READY_FOR_PRODUCTION_GO_NO_GO",
    "PRODUCTION_COORDINATION_PAUSED",
    "POST_COORDINATION_D9_READY",
    "Go / No-Go",
    "Rollback Handoff",
    "python scripts/d8_staging_execution_pack_check.py",
    "python scripts/d8_staging_records_check.py",
    "python scripts/d8_staging_evidence_review_check.py",
    "python scripts/d8_readiness_audit.py",
    "python scripts/d8_production_coordination_check.py",
    "python scripts/d9_operating_execution_pack_check.py",
    "python scripts/d9_operating_loop_kickoff_check.py",
)
REQUIRED_BOUNDARIES = (
    "No `.env`",
    "No token values",
    "No raw response bodies",
    "No nginx",
    "No cloud upstream",
    "No `service.intelli-opus.com` deployment",
    "No email, webhook, carrier API",
    "No customer or supplier notification",
    "No quote/order/shipment/payment/inventory/partner-selection mutation",
    "No internal cost, margin, pricing breakdown",
)
FORBIDDEN_MARKERS = (
    "Bearer ",
    "SERVICE_PORTAL_PARTNEROS_TOKEN=",
    "PORTAL_CUSTOMER_API_TOKEN=",
    "password_hash",
    "database_url",
    "raw response body:",
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
    return DOC.read_text(encoding="utf-8") if DOC.exists() else ""


def _missing(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def _forbidden(text: str) -> list[str]:
    issues = [marker for marker in FORBIDDEN_MARKERS if marker.lower() in text.lower()]
    issues.extend(redaction_issues(DOC, text, include_common_markers=False))
    for line in text.splitlines():
        if TOKEN_ASSIGNMENT.search(line) and "<portal-server-token>" not in line:
            issues.append("SERVICE_PORTAL_PARTNEROS_TOKEN=<non-placeholder>")
            break
    return issues


def main() -> int:
    checks = [
        Check("production coordination runbook exists"),
        Check("runbook covers states and commands"),
        Check("runbook preserves safety boundaries"),
        Check("runbook avoids secret-like markers"),
    ]

    text = _text()
    checks[0].pass_("docs/phase3/d8_production_coordination_runbook.md") if text else checks[0].fail(str(DOC))

    missing = _missing(text, REQUIRED_MARKERS)
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    missing_boundaries = _missing(text, REQUIRED_BOUNDARIES)
    checks[2].pass_("documented") if not missing_boundaries else checks[2].fail(", ".join(missing_boundaries))

    forbidden = _forbidden(text)
    checks[3].pass_("redacted") if not forbidden else checks[3].fail(", ".join(forbidden))

    print("D8 Production Coordination Runbook Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
