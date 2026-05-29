"""D8.2 runtime hardening check for local and staging-like environments."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import get_backend_base_url
from app.core.config import get_settings
from app.core.database_lifecycle import check_database, get_migration_revisions
from app.core.db_url_utils import mask_database_url


class Check:
    def __init__(self, label: str) -> None:
        self.label = label
        self.level = "PASS"
        self.detail = ""

    def pass_(self, detail: str = "") -> None:
        self.level = "PASS"
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


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _git_ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", path],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _check_runtime_mode(strict: bool, mode: str) -> Check:
    item = Check("runtime mode")
    if strict and mode == "development":
        item.fail("strict staging cannot use development mode")
    elif mode == "development":
        item.warn("development mode")
    else:
        item.pass_(mode)
    return item


def _check_secret(strict: bool, secret: str) -> Check:
    item = Check("SECRET_KEY")
    if not secret.strip():
        item.fail("not configured")
    elif secret == "dev-secret-change-in-production":
        (item.fail if strict else item.warn)("development default")
    elif len(secret) < 24:
        (item.fail if strict else item.warn)("short secret")
    else:
        item.pass_("configured")
    return item


def _check_public_base_url(strict: bool, value: str) -> Check:
    item = Check("PUBLIC_BASE_URL")
    if not value:
        (item.fail if strict else item.warn)("not configured")
    elif strict and not value.lower().startswith("https://"):
        item.fail("strict staging requires HTTPS")
    else:
        item.pass_(value)
    return item


def _check_database(settings) -> list[Check]:
    url = Check("DATABASE_URL")
    db = Check("database connection")
    migration = Check("migration at head")

    if settings.DATABASE_URL.strip():
        url.pass_(mask_database_url(settings.DATABASE_URL))
    else:
        url.fail("not configured")
        db.warn("skipped")
        migration.warn("skipped")
        return [url, db, migration]

    status, errors = check_database(settings)
    if status != "ready":
        db.fail(errors[0] if errors else status)
        migration.warn("skipped")
        return [url, db, migration]
    db.pass_("ready")

    try:
        current, head, _ = get_migration_revisions(settings)
    except Exception as exc:  # noqa: BLE001
        migration.fail(str(exc)[:120])
        return [url, db, migration]
    if current == head:
        migration.pass_(head)
    else:
        migration.fail(f"current={current} head={head}")
    return [url, db, migration]


def _check_proxy_alignment() -> Check:
    item = Check("BACKEND_BASE_URL / VITE_API_PROXY_TARGET")
    backend = get_backend_base_url().rstrip("/")
    proxy = os.getenv("VITE_API_PROXY_TARGET", "").strip().rstrip("/")
    if proxy and proxy != backend:
        item.warn(f"proxy={proxy} backend={backend}")
    else:
        item.pass_(backend)
    return item


def _check_portal_token(strict: bool, settings) -> list[Check]:
    enabled = Check("portal customer API")
    token = Check("portal customer token")
    origins = Check("portal customer CORS")

    if not settings.PORTAL_CUSTOMER_API_ENABLED:
        enabled.warn("disabled")
    else:
        enabled.pass_("enabled")

    raw_token = settings.PORTAL_CUSTOMER_API_TOKEN.strip()
    unsafe_tokens = {"", "test-portal-token", "dev-portal-token", "change-me"}
    if settings.PORTAL_CUSTOMER_API_REQUIRE_TOKEN and raw_token in unsafe_tokens:
        (token.fail if strict or settings.PORTAL_CUSTOMER_API_ENABLED else token.warn)("token missing or unsafe")
    elif settings.PORTAL_CUSTOMER_API_REQUIRE_TOKEN:
        token.pass_("configured")
    else:
        (token.fail if strict else token.warn)("token requirement disabled")

    allowed = settings.PORTAL_CUSTOMER_ALLOWED_ORIGINS.strip()
    if settings.PORTAL_CUSTOMER_API_ENABLED and not allowed:
        (origins.fail if strict else origins.warn)("no allowed origins configured")
    elif "service.intelli-opus.com" in allowed:
        origins.pass_("service portal origin configured")
    elif allowed:
        origins.warn(allowed)
    else:
        origins.warn("not configured")
    return [enabled, token, origins]


def _check_storage(settings) -> list[Check]:
    backend = Check("storage backend")
    path = Check("storage path")
    ignored = Check("storage gitignore")

    backend.pass_(settings.STORAGE_BACKEND or "local")
    raw_path = (settings.LOCAL_STORAGE_PATH or settings.UPLOAD_DIR or "./uploads").strip()
    if not raw_path:
        path.warn("not configured")
    else:
        path.pass_(raw_path)

    ignored_paths = ["backend/storage/", "local_data/", "backend/.env", "frontend/.env.local"]
    missing = [p for p in ignored_paths if not _git_ignored(p)]
    if missing:
        ignored.warn("not ignored: " + ", ".join(missing))
    else:
        ignored.pass_("sensitive local paths ignored")
    return [backend, path, ignored]


def run() -> int:
    get_settings.cache_clear()
    settings = get_settings()
    strict = _truthy(os.getenv("D8_2_STRICT_STAGING"))

    items: list[Check] = [
        _check_runtime_mode(strict, settings.APP_RUNTIME_MODE.value),
        _check_secret(strict, settings.SECRET_KEY),
        _check_public_base_url(strict, settings.PUBLIC_BASE_URL.strip()),
        _check_proxy_alignment(),
    ]
    items.extend(_check_database(settings))
    items.extend(_check_portal_token(strict, settings))
    items.extend(_check_storage(settings))

    print("D8.2 Runtime Hardening Check")
    print(f"strict_staging={strict}")
    for item in items:
        print(item.line())

    fails = [item for item in items if item.level == "FAIL"]
    warns = [item for item in items if item.level == "WARN"]
    print()
    if fails:
        print("Result: FAIL")
        return 1
    if warns:
        print(f"Result: PASS ({len(warns)} warning(s))")
    else:
        print("Result: PASS")
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
