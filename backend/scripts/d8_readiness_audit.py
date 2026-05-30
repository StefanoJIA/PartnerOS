"""D8 readiness audit across local artifacts and optional staging evidence."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
RECORDS_ROOT = REPO_ROOT / "docs" / "records"

REQUIRED_DOCS = (
    "docs/phase3/d8_delivery_stage_goal_matrix.md",
    "docs/phase3/d8_integration_hardening.md",
    "docs/phase3/d8_strict_staging_cloud_validation.md",
    "docs/phase3/d8_1_rbac_scoped_access.md",
    "docs/phase3/d8_2_runtime_hardening.md",
    "docs/phase3/d8_3_service_portal_staging_integration.md",
    "docs/phase3/d8_4_multi_partner_operations_dashboard.md",
    "docs/phase3/d8_5_market_response_intelligence.md",
    "docs/phase3/d8_staging_access_request.md",
    "docs/phase3/d8_staging_gap_triage.md",
    "docs/phase3/d8_staging_records_policy.md",
    "docs/phase3/d8_production_coordination_plan.md",
    "docs/phase3/d9_post_launch_operating_loop.md",
    "docs/phase3/d9_operating_records_policy.md",
    "docs/phase3/project_execution_chain_gate.md",
    "docs/phase3/phase3_roadmap.md",
    "docs/phase3/ie_auto_project_plan.md",
)
REQUIRED_SCRIPTS = (
    "backend/scripts/d8_stage_goal_matrix_check.py",
    "backend/scripts/d8_integration_hardening_check.py",
    "backend/scripts/d8_strict_staging_evidence_check.py",
    "backend/scripts/d8_1_rbac_scoped_access_check.py",
    "backend/scripts/d8_2_runtime_hardening_check.py",
    "backend/scripts/d8_3_service_portal_staging_check.py",
    "backend/scripts/d8_4_partner_operations_check.py",
    "backend/scripts/d8_5_market_response_check.py",
    "backend/scripts/d8_staging_access_request_check.py",
    "backend/scripts/d8_staging_gap_triage_check.py",
    "backend/scripts/d8_staging_records_check.py",
    "backend/scripts/d8_production_coordination_check.py",
    "backend/scripts/d9_post_launch_plan_check.py",
    "backend/scripts/d9_operating_records_check.py",
    "backend/scripts/phase3_roadmap_check.py",
    "backend/scripts/ie_auto_project_plan_check.py",
    "backend/scripts/project_execution_chain_check.py",
    "backend/scripts/project_execution_records_check.py",
)
SAFETY_MARKERS = (
    "No automatic customer or supplier notification",
    "No email, webhook, carrier API, nginx",
    "No customer-facing internal cost",
    "AI remains advisory",
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


def _missing(paths: tuple[str, ...]) -> list[str]:
    return [path for path in paths if not (REPO_ROOT / path).exists()]


def _strict_evidence_files() -> list[Path]:
    if not RECORDS_ROOT.exists():
        return []
    return sorted(RECORDS_ROOT.glob("d8_strict_staging_evidence_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _staging_status() -> tuple[str, str]:
    files = _strict_evidence_files()
    if not files:
        return "READY_FOR_STAGING", "no strict staging evidence JSON found"
    latest = files[0]
    data = _read_json(latest)
    result = str(data.get("result") or "").upper()
    if result == "PASS":
        return "STAGING_VALIDATED", latest.name
    if result == "FAIL":
        gap_name = latest.name.replace("evidence", "gaps").replace(".json", ".md")
        gap_path = RECORDS_ROOT / gap_name
        if gap_path.exists():
            return "STAGING_GAPS_OPEN", f"{latest.name}; gap register {gap_name}"
        return "STAGING_GAPS_OPEN", f"{latest.name}; gap register missing"
    return "STAGING_EVIDENCE_UNREADABLE", latest.name


def _records_gate_status() -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, "scripts/d8_staging_records_check.py"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    if result.returncode == 0 and "Result: PASS" in result.stdout:
        return True, "PASS"
    detail = next((line for line in output.splitlines() if line.startswith("[FAIL]")), "")
    return False, detail or output[:160] or "records gate failed"


def main() -> int:
    checks = [
        Check("D8 docs present"),
        Check("D8 scripts present"),
        Check("stage matrix safety invariants"),
        Check("staging records hygiene"),
        Check("strict staging evidence state"),
    ]

    missing_docs = _missing(REQUIRED_DOCS)
    checks[0].pass_(f"{len(REQUIRED_DOCS)} docs") if not missing_docs else checks[0].fail(", ".join(missing_docs))

    missing_scripts = _missing(REQUIRED_SCRIPTS)
    checks[1].pass_(f"{len(REQUIRED_SCRIPTS)} scripts") if not missing_scripts else checks[1].fail(
        ", ".join(missing_scripts)
    )

    matrix = REPO_ROOT / "docs/phase3/d8_delivery_stage_goal_matrix.md"
    text = matrix.read_text(encoding="utf-8") if matrix.exists() else ""
    missing_safety = [marker for marker in SAFETY_MARKERS if marker not in text]
    checks[2].pass_("documented") if not missing_safety else checks[2].fail(", ".join(missing_safety))

    records_ok, records_detail = _records_gate_status()
    checks[3].pass_(records_detail) if records_ok else checks[3].fail(records_detail)

    staging_status, staging_detail = _staging_status()
    if staging_status in {"READY_FOR_STAGING", "STAGING_VALIDATED", "STAGING_GAPS_OPEN"}:
        checks[4].pass_(f"{staging_status}: {staging_detail}")
    else:
        checks[4].fail(f"{staging_status}: {staging_detail}")

    local_ready = all(check.ok for check in checks[:4])
    if not local_ready:
        overall = "LOCAL_ARTIFACTS_INCOMPLETE"
    elif staging_status == "STAGING_VALIDATED":
        overall = "STAGING_VALIDATED"
    elif staging_status == "STAGING_GAPS_OPEN":
        overall = "STAGING_GAPS_OPEN"
    else:
        overall = "READY_FOR_STAGING"

    print("D8 Readiness Audit")
    for check in checks:
        print(check.line())
    print(f"Overall: {overall}")
    if overall == "READY_FOR_STAGING":
        print("Next: run scripts/d8_strict_staging_evidence_check.py with real staging values and save evidence/gap artifacts.")
    elif overall == "STAGING_GAPS_OPEN":
        print("Next: close the generated gap register and rerun strict staging evidence.")
    elif overall == "STAGING_VALIDATED":
        print("Next: proceed to production coordination planning without changing service.intelli-opus.com from this repo.")

    return 0 if local_ready and staging_status != "STAGING_EVIDENCE_UNREADABLE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
