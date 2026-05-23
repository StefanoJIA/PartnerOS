"""D5.2.10 external Portal consumer contract check (read-only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import httpx

from app.core.backend_url import get_backend_base_url, log_backend_base_url

BASE = get_backend_base_url()

SECRET_MARKERS = (
    "dev-secret-change-in-production",
    "sk-",
    "Bearer ",
    "password",
    "OPENAI_API_KEY",
    "postgresql+psycopg://partneros:partneros",
    "access_token",
)

MANIFEST_FIELDS = ("service_id", "runtime_mode", "api_version", "modules", "capabilities")
SUMMARY_FIELDS = ("service_id", "runtime_mode", "api_version", "health", "lead_intelligence", "capabilities", "warnings")
A_DOMAIN_FIELDS = (
    "domain",
    "manual_outreach_ready",
    "automatic_sending_enabled",
    "linkedin_automation_enabled",
    "outlook_integration_enabled",
)
READINESS_FIELDS = ("service", "database_ready", "database_status", "warnings")


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


def _envelope_ok(body: dict) -> tuple[bool, dict]:
    if body.get("ok") is not True:
        return False, {}
    data = body.get("data")
    if not isinstance(data, dict):
        return False, {}
    meta = body.get("meta")
    if not isinstance(meta, dict):
        return False, {}
    return True, data


def _has_fields(data: dict, fields: tuple[str, ...]) -> bool:
    return all(k in data for k in fields)


def run() -> int:
    global BASE
    BASE = log_backend_base_url()
    checks = [
        Check("manifest contract"),
        Check("summary contract"),
        Check("a-domain status contract"),
        Check("readiness contract"),
        Check("no secret leakage"),
        Check("manual outreach ready"),
        Check("automatic sending disabled"),
    ]
    collected: list[str] = []
    adata: dict = {}

    try:
        with httpx.Client(timeout=60.0) as client:
            mr = client.get(f"{BASE}/api/v1/portal/manifest")
            ok, mdata = _envelope_ok(mr.json()) if mr.status_code == 200 else (False, {})
            if ok and mdata.get("service_id") == "intellioffice" and _has_fields(mdata, MANIFEST_FIELDS):
                checks[0].pass_(f"{len(mdata.get('modules', []))} modules")
            else:
                checks[0].fail(f"HTTP {mr.status_code}")
            collected.append(json.dumps(mr.json()))

            sr = client.get(f"{BASE}/api/v1/portal/summary")
            ok, sdata = _envelope_ok(sr.json()) if sr.status_code == 200 else (False, {})
            li = sdata.get("lead_intelligence") if ok else {}
            if (
                ok
                and _has_fields(sdata, SUMMARY_FIELDS)
                and isinstance(li, dict)
                and "total_leads" in li
                and "high_priority" in li
            ):
                checks[1].pass_(f"total={li.get('total_leads')}")
            else:
                checks[1].fail(f"HTTP {sr.status_code}")
            collected.append(json.dumps(sr.json()))

            ar = client.get(f"{BASE}/api/v1/portal/a-domain/status")
            ok, adata = _envelope_ok(ar.json()) if ar.status_code == 200 else (False, {})
            if ok and _has_fields(adata, A_DOMAIN_FIELDS):
                checks[2].pass_(f"stage={adata.get('latest_stage', '?')}")
            else:
                checks[2].fail(f"HTTP {ar.status_code}")
            collected.append(json.dumps(ar.json()))

            rr = client.get(f"{BASE}/api/v1/system/readiness")
            ok, rdata = _envelope_ok(rr.json()) if rr.status_code == 200 else (False, {})
            if ok and _has_fields(rdata, READINESS_FIELDS):
                checks[3].pass_()
            else:
                checks[3].fail(f"HTTP {rr.status_code}")
            collected.append(json.dumps(rr.json()))

            blob = " ".join(collected).lower()
            leaks = [m for m in SECRET_MARKERS if m.lower() in blob]
            if not leaks:
                checks[4].pass_()
            else:
                checks[4].fail(", ".join(leaks[:3]))

            if adata.get("manual_outreach_ready") is True:
                checks[5].pass_()
            else:
                checks[5].fail("manual_outreach_ready != true")

            if adata.get("automatic_sending_enabled") is False:
                checks[6].pass_()
            else:
                checks[6].fail("automatic_sending_enabled != false")

    except httpx.ConnectError:
        print(f"Backend not reachable at {BASE}")
        return 1

    print("D5.2.10 Portal Consumer Check")
    for c in checks:
        print(c.line())
    failed = sum(1 for c in checks if not c.ok)
    print()
    print(f"Result: {'PASS' if failed == 0 else 'FAIL'}")
    return 0 if failed == 0 else 1


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
