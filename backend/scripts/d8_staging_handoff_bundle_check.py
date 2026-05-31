"""Validate the D8 staging handoff bundle manifest."""

from __future__ import annotations

from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "phase3" / "d8_staging_handoff_bundle.md"

REQUIRED_LINKS = (
    "../operator_guide.md",
    "../deployment_readiness_checklist.md",
    "../testing.md",
    "project_execution_chain_gate.md",
    "d8_staging_operator_handoff.md",
    "d8_local_staging_rehearsal.md",
    "d8_staging_operator_runbook.md",
    "d8_staging_input_preflight.md",
    "d8_staging_access_request.md",
    "d8_staging_operator_response_intake.md",
    "d8_strict_staging_cloud_validation.md",
    "d8_staging_gap_triage.md",
    "d8_staging_records_policy.md",
    "d8_staging_evidence_review.md",
    "d8_production_coordination_plan.md",
    "d8_production_coordination_runbook.md",
    "../records/d8_staging_operator_handoff_20260531.md",
    "../records/d8_staging_access_request_20260531.md",
)
REQUIRED_COMMANDS = (
    "python scripts/readme_check.py",
    "python scripts/deployment_readiness_checklist_check.py",
    "python scripts/testing_guide_check.py",
    "python scripts/project_execution_status.py",
    "python scripts/project_execution_chain_gate_check.py",
    "python scripts/project_execution_chain_check.py",
    "python scripts/project_execution_acceptance_audit_check.py",
    "python scripts/operator_guide_check.py",
    "python scripts/d8_staging_execution_pack_check.py",
    "python scripts/d8_staging_operator_runbook_check.py",
    "python scripts/d8_local_staging_rehearsal_check.py",
    "python scripts/d8_staging_input_preflight_check.py",
    "python scripts/d8_staging_access_request_check.py",
    "python scripts/d8_staging_operator_response_intake_check.py",
    "python scripts/d8_staging_gap_triage_check.py",
    "python scripts/d8_staging_records_check.py",
    "python scripts/d8_staging_evidence_review_check.py",
    "python scripts/d8_staging_operator_handoff.py --output ../docs/records/d8_staging_operator_handoff_YYYYMMDD.md",
    "python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md",
    "python scripts/d8_production_coordination_runbook_check.py",
    "python scripts/d8_readiness_audit.py",
)
REQUIRED_MARKERS = (
    "READY_FOR_STAGING_HANDOFF",
    "Operator Guide",
    "STAGING_VALIDATED",
    "BACKEND_BASE_URL",
    "SERVICE_PORTAL_PARTNEROS_TOKEN",
    "SERVICE_PORTAL_ORIGIN",
    "not staging proof",
    "Exclude",
    "no token values",
    "raw response bodies",
    "service.intelli-opus.com",
    "nginx",
    "Committed Records",
    "D8 Staging Operator Handoff Record",
    "D8 Staging Access Request Record",
)
FORBIDDEN_MARKERS = (
    "PORTAL_CUSTOMER_API_TOKEN=",
    "Bearer ",
    "raw customer",
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
    issues.extend(redaction_issues(DOC, text, include_common_markers=False))
    for line in text.splitlines():
        if "SERVICE_PORTAL_PARTNEROS_TOKEN" in line and "=" in line and "<portal-server-token>" not in line:
            issues.append("SERVICE_PORTAL_PARTNEROS_TOKEN=<non-placeholder>")
    return issues


def _record_link_issues() -> list[str]:
    issues: list[str] = []
    for link in REQUIRED_LINKS:
        if not link.startswith("../records/"):
            continue
        path = (DOC.parent / link).resolve()
        try:
            path.relative_to(REPO_ROOT)
        except ValueError:
            issues.append(link)
            continue
        if not path.is_file():
            issues.append(link)
    return issues


def main() -> int:
    checks = [
        Check("D8 staging handoff bundle doc exists"),
        Check("bundle links required handoff docs"),
        Check("bundle includes required commands"),
        Check("bundle preserves safety boundaries"),
        Check("bundle committed record links exist"),
        Check("bundle avoids secret-like markers"),
    ]

    text = _text()
    checks[0].pass_("docs/phase3/d8_staging_handoff_bundle.md") if text else checks[0].fail(str(DOC))

    missing_links = _missing(text, REQUIRED_LINKS)
    checks[1].pass_(f"{len(REQUIRED_LINKS)} links") if not missing_links else checks[1].fail(
        ", ".join(missing_links)
    )

    missing_commands = _missing(text, REQUIRED_COMMANDS)
    checks[2].pass_(f"{len(REQUIRED_COMMANDS)} commands") if not missing_commands else checks[2].fail(
        ", ".join(missing_commands)
    )

    missing_markers = _missing(text, REQUIRED_MARKERS)
    checks[3].pass_("documented") if not missing_markers else checks[3].fail(", ".join(missing_markers))

    record_issues = _record_link_issues()
    checks[4].pass_("committed records present") if not record_issues else checks[4].fail(
        ", ".join(record_issues)
    )

    forbidden = _forbidden(text)
    checks[5].pass_("redacted") if not forbidden else checks[5].fail(", ".join(forbidden))

    print("D8 Staging Handoff Bundle Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
