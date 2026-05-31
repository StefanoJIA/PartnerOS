"""Validate project-specific Codex skill pack guidance."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_DIR = REPO_ROOT / "docs" / "codex_skills"

REQUIRED_FILES = (
    "README.md",
    "project_execution_rules.md",
    "runtime_and_ports.md",
    "security_and_git_safety.md",
    "domain_boundaries.md",
    "testing_matrix.md",
    "portal_bridge_rules.md",
)
REQUIRED_MARKERS = (
    "D7 is closed through D7.9",
    "READY_FOR_STAGING_HANDOFF",
    "STAGING_VALIDATED",
    "WAITING_FOR_REAL_STAGING_EVIDENCE",
    "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "human Go / No-Go handoff",
    "docs/records/d8_production_go_no_go_YYYYMMDD.md",
    "python scripts/project_execution_chain_gate_check.py",
    "python scripts/project_execution_status.py",
    "python scripts/d8_staging_execution_pack_check.py",
    "python scripts/d9_operating_execution_pack_check.py",
    "python scripts/project_execution_acceptance_audit_check.py",
    "Preferred local backend smoke port is `8014`",
    "Historical D5/D6 records may mention `8000` or `8010`",
    "BACKEND_BASE_URL=http://127.0.0.1:8014",
    "VITE_API_PROXY_TARGET=http://127.0.0.1:8014",
    "No automatic shipment creation",
    "explicit allowlists",
    "service.intelli-opus.com",
    "Do not edit nginx, cloud upstreams, or the live service portal",
    "python scripts/codex_skill_pack_check.py",
    "Do not expose internal costs",
)
PROJECT_EXECUTION_RULE_MARKERS = (
    "WAITING_FOR_REAL_STAGING_EVIDENCE",
    "python scripts/project_execution_chain_gate_check.py",
    "python scripts/d8_staging_execution_pack_check.py",
    "python scripts/project_execution_acceptance_audit_check.py",
    "python scripts/project_execution_status.py",
)
FORBIDDEN_MARKERS = (
    "D7.1-D7.6 cover internal order lifecycle through shipment tracking",
    "D7.7 covers customer portal bridge APIs and feedback intake",
    "Use server-to-server token auth for MVP",
    "Backend default development examples may use `8010`",
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


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _texts() -> dict[str, str]:
    return {name: _read(DOC_DIR / name) for name in REQUIRED_FILES}


def _combined_text(texts: dict[str, str]) -> str:
    return "\n".join(texts.values())


def _redaction_issues(texts: dict[str, str]) -> list[str]:
    issues: list[str] = []
    for name, text in texts.items():
        for line in text.splitlines():
            if TOKEN_ASSIGNMENT.search(line) and "<portal-server-token>" not in line:
                issues.append(f"{name}:SERVICE_PORTAL_PARTNEROS_TOKEN=<non-placeholder>")
        issues.extend(redaction_issues(DOC_DIR / name, text, include_common_markers=False))
    return issues


def main() -> int:
    checks = [
        Check("Codex skill pack files exist"),
        Check("Codex skill pack matches current D7-D9 execution state"),
        Check("project execution rules require full current-stage gates"),
        Check("Codex skill pack avoids stale stage guidance"),
        Check("Codex skill pack is redacted"),
    ]

    texts = _texts()
    missing_files = [name for name, text in texts.items() if not text]
    checks[0].pass_(f"{len(REQUIRED_FILES)} files") if not missing_files else checks[0].fail(", ".join(missing_files))

    combined = _combined_text(texts)
    missing = [marker for marker in REQUIRED_MARKERS if marker not in combined]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    rule_text = texts.get("project_execution_rules.md", "")
    missing_rule_markers = [marker for marker in PROJECT_EXECUTION_RULE_MARKERS if marker not in rule_text]
    checks[2].pass_("documented") if not missing_rule_markers else checks[2].fail(
        ", ".join(missing_rule_markers)
    )

    stale = [marker for marker in FORBIDDEN_MARKERS[:4] if marker in combined]
    checks[3].pass_("no stale D7 or port markers") if not stale else checks[3].fail(", ".join(stale))

    redaction = [marker for marker in FORBIDDEN_MARKERS[4:] if marker in combined]
    redaction.extend(_redaction_issues(texts))
    checks[4].pass_("no secret-like markers") if not redaction else checks[4].fail(", ".join(redaction[:8]))

    print("Codex Skill Pack Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
