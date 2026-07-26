"""Release candidate smoke — migration, feature flags, contract gates, e2e chain."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import log_backend_base_url
from app.core.config import Settings, get_settings
from app.core.database_lifecycle import get_migration_revisions


def _run_script(relative: str) -> tuple[int, str]:
    path = BACKEND_ROOT / "scripts" / relative
    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(BACKEND_ROOT),
        capture_output=True,
        text=True,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


def main() -> int:
    log_backend_base_url()
    print("Release Candidate Check")
    settings = get_settings()
    current, head, _ = get_migration_revisions(settings)
    checks: list[tuple[str, bool, str]] = []

    mig_ok = current == head == "0031_platform_intelligence"
    checks.append(("migration head 0031_platform_intelligence", mig_ok, f"{current}/{head}"))

    checks.append(
        (
            "portal schema default disabled",
            Settings.model_fields["PORTAL_CUSTOMER_API_ENABLED"].default is False,
            "config.py default",
        )
    )
    checks.append(
        (
            "customer site compat default off",
            not settings.CUSTOMER_SITE_COMPAT_ENABLED,
            str(settings.CUSTOMER_SITE_COMPAT_ENABLED),
        )
    )

    try:
        from app.api.routes.customer_site_compat import PUBLIC_PRODUCT_GROUPS

        education = PUBLIC_PRODUCT_GROUPS["Education Furniture"]
        checks.append(
            (
                "JOOBOO education group pending",
                education.get("is_pending") is True,
                education.get("description", "")[:80],
            )
        )
    except Exception as exc:
        checks.append(("JOOBOO education group pending", False, str(exc)))

    for label, script in (
        ("d6_4 quote pdf export", "d6_4_quote_pdf_export_check.py"),
        ("hosun catalog governance", "hosun_catalog_governance_check.py"),
        ("d7_7 portal bridge", "d7_7_portal_bridge_check.py"),
        ("d8_0 staging build readiness", "d8_0_staging_build_readiness_check.py"),
        ("e2e supplier convergence", "e2e_supplier_convergence_check.py"),
    ):
        code, output = _run_script(script)
        detail = "PASS" if code == 0 else (output.splitlines()[-1] if output else f"exit {code}")
        checks.append((label, code == 0, detail))

    passed = True
    for label, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {label} ({detail})")
        passed = passed and ok
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
