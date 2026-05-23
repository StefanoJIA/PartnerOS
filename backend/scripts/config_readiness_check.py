"""D5.2.10 local/server config readiness check (warnings + critical failures)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent


class Item:
    def __init__(self, label: str) -> None:
        self.label = label
        self.level = "OK"
        self.detail = ""

    def ok(self, detail: str = "") -> None:
        self.level = "OK"
        self.detail = detail

    def warn(self, detail: str) -> None:
        self.level = "WARN"
        self.detail = detail

    def fail(self, detail: str) -> None:
        self.level = "FAIL"
        self.detail = detail

    def line(self) -> str:
        suffix = f" ({self.detail})" if self.detail else ""
        return f"[{self.level}] {self.label}{suffix}"


def _git_ignored(path: str) -> bool:
    try:
        r = subprocess.run(
            ["git", "check-ignore", path],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return r.returncode == 0
    except OSError:
        return False


def run() -> int:
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))

    from app.core.backend_url import get_backend_base_url, log_backend_base_url
    from app.core.config import get_settings
    from app.core.database_lifecycle import check_database, get_migration_revisions
    from app.core.db_url_utils import mask_database_url

    log_backend_base_url()
    get_settings.cache_clear()
    settings = get_settings()

    items = [
        Item("APP_RUNTIME_MODE"),
        Item("PUBLIC_BASE_URL"),
        Item("DATABASE_URL"),
        Item("BACKEND_BASE_URL"),
        Item("migration pending"),
        Item("backend/.env gitignore"),
        Item("local_data gitignore"),
        Item("SECRET_KEY"),
    ]
    critical_fail = False

    mode = settings.APP_RUNTIME_MODE.value
    items[0].ok(mode)
    if mode == "development":
        items[0].warn("development mode — rotate secrets before production")

    pub = (getattr(settings, "PUBLIC_BASE_URL", None) or os.getenv("PUBLIC_BASE_URL") or "").strip()
    if pub:
        items[1].ok(pub)
    else:
        items[1].warn("not set — manifest URLs default to http://127.0.0.1:8000")

    url_raw = (settings.DATABASE_URL or "").strip()
    if url_raw:
        items[2].ok(mask_database_url(url_raw))
    else:
        items[2].fail("not configured")
        critical_fail = True

    db_status, db_errors = check_database(settings)
    if db_status != "ready":
        items[2].fail(f"{db_status}: {db_errors[0] if db_errors else 'unreachable'}")
        critical_fail = True

    backend_url = get_backend_base_url()
    items[3].ok(backend_url)
    vite_proxy = os.getenv("VITE_API_PROXY_TARGET", "").strip()
    if vite_proxy and vite_proxy.rstrip("/") != backend_url:
        items[3].warn(f"VITE_API_PROXY_TARGET={vite_proxy} differs from BACKEND_BASE_URL")

    migration_pending = False
    if db_status == "ready":
        try:
            current, head, _ = get_migration_revisions(settings)
            migration_pending = current != head
            if migration_pending:
                items[4].fail(f"current={current} head={head}")
                critical_fail = True
            else:
                items[4].ok(f"at head ({head})")
        except Exception as e:  # noqa: BLE001
            items[4].warn(str(e)[:120])
    else:
        items[4].warn("skipped — database not ready")

    items[5].ok() if _git_ignored("backend/.env") else items[5].warn("backend/.env not ignored by git")
    items[6].ok() if _git_ignored("local_data/") else items[6].warn("local_data/ not ignored by git")

    sk = (settings.SECRET_KEY or "").strip()
    if not sk:
        items[7].fail("SECRET_KEY not set")
        critical_fail = True
    elif sk == "dev-secret-change-in-production":
        items[7].warn("development default — rotate for production")
    else:
        items[7].ok("configured (value not shown)")

    print("D5.2.10 Config Readiness Check")
    for it in items:
        print(it.line())
    print()
    if critical_fail:
        print("Result: FAIL (critical)")
        return 1
    warns = sum(1 for it in items if it.level == "WARN")
    print(f"Result: PASS ({warns} warning(s))" if warns else "Result: PASS")
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
