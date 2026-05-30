"""Generate a redacted D8 strict staging operator handoff."""

from __future__ import annotations

import subprocess
import sys
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent


def _parse_args():
    parser = ArgumentParser(description="Generate the D8 strict staging operator handoff markdown.")
    parser.add_argument(
        "--output",
        help="Output markdown path. Relative paths are resolved from backend/. Defaults to a dated docs/records handoff.",
    )
    return parser.parse_args()


def _safe_output_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = BACKEND_ROOT / path
    resolved = path.resolve()
    forbidden_roots = ((REPO_ROOT / "local_data").resolve(), (BACKEND_ROOT / "storage").resolve())
    for root in forbidden_roots:
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        raise ValueError("handoff output must not be under local_data or backend/storage")
    return resolved


def _run_readiness_audit() -> tuple[str, str]:
    result = subprocess.run(
        [sys.executable, "scripts/d8_readiness_audit.py"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or "").strip()
    status = "UNKNOWN"
    for line in output.splitlines():
        if line.startswith("Overall:"):
            status = line.split(":", 1)[1].strip()
            break
    if result.returncode != 0 and status == "UNKNOWN":
        status = "AUDIT_FAILED"
    return status, output


def _git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return (result.stdout or "unknown").strip() if result.returncode == 0 else "unknown"


def _handoff_text(status: str, audit_output: str) -> str:
    generated = datetime.now(timezone.utc).isoformat()
    head = _git_head()
    return f"""# D8 Strict Staging Operator Handoff

Generated at: {generated}
Repository commit: `{head}`
Readiness status: `{status}`

## Purpose

Run the PartnerOS D8 strict staging evidence flow against the real deployed staging backend and preserve redacted proof for follow-up.

## Required Inputs

| Variable | Required value |
|---|---|
| `BACKEND_BASE_URL` | HTTPS PartnerOS staging backend origin |
| `SERVICE_PORTAL_PARTNEROS_TOKEN` | Non-default portal server token; do not paste into docs or screenshots |
| `SERVICE_PORTAL_ORIGIN` | `https://service.intelli-opus.com` unless the portal team confirms another HTTPS origin |

## Preflight

```powershell
cd backend
python scripts/d8_readiness_audit.py
python scripts/d8_stage_goal_matrix_check.py
python scripts/d8_integration_hardening_check.py
python scripts/d8_staging_records_check.py
python scripts/d8_production_coordination_check.py
python scripts/d9_post_launch_plan_check.py
python scripts/d9_operating_records_check.py
python scripts/phase3_roadmap_check.py
python scripts/ie_auto_project_plan_check.py
```

## Strict Staging Evidence Run

```powershell
cd backend
$env:BACKEND_BASE_URL="https://partneros-staging.example.com"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<portal-server-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md
```

## Expected Output

- Console result is `PASS` or `FAIL`.
- Evidence JSON is redacted and contains check labels, statuses, sanitized URLs, and safety metadata.
- Gap Markdown is generated when checks fail and can be used as the next fix list.

## Safety Boundaries

- Do not deploy or modify `service.intelli-opus.com` from PartnerOS.
- Do not edit nginx or cloud upstreams from this repository.
- Do not create non-TEST feedback during staging.
- Do not print, screenshot, commit, or paste portal tokens.
- Do not expose internal cost, margin, pricing breakdowns, supplier private notes, storage keys, backend paths, or secrets.
- Do not trigger email, webhook, carrier API, customer notification, supplier notification, or quote/order/shipment mutation.

## Current Readiness Audit

```text
{audit_output or 'No audit output captured.'}
```
"""


def main() -> int:
    args = _parse_args()
    status, audit_output = _run_readiness_audit()
    output_arg = args.output or f"../docs/records/d8_staging_operator_handoff_{datetime.now(timezone.utc):%Y%m%d}.md"
    output = _safe_output_path(output_arg)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_handoff_text(status, audit_output), encoding="utf-8")
    print("D8 Staging Operator Handoff")
    print(f"readiness_status={status}")
    print(f"output={output}")
    return 0 if status != "AUDIT_FAILED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
