"""D5.11 — unified local runtime diagnostics (read-only, no auto-kill)."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import httpx

from app.core.backend_url import get_backend_base_url, get_health_url, log_backend_base_url


def _load_utils():
    path = BACKEND_ROOT / "scripts" / "runtime_check_utils.py"
    spec = importlib.util.spec_from_file_location("runtime_check_utils", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_utils = _load_utils()
RuntimeItem = _utils.RuntimeItem
get_json = _utils.get_json
login_headers = _utils.login_headers
probe_port_in_use = _utils.probe_port_in_use
stale_port_hints = _utils.stale_port_hints

FALLBACK_BACKEND = "http://127.0.0.1:8013"


def _check_database() -> RuntimeItem:
    item = RuntimeItem("database connection")
    from app.core.config import get_settings
    from app.core.database_lifecycle import check_database

    get_settings.cache_clear()
    settings = get_settings()
    status, errors = check_database(settings)
    if status == "ready":
        item.pass_("OK")
    else:
        item.fail(errors[0] if errors else status)
    return item


def _check_migration() -> RuntimeItem:
    item = RuntimeItem("migration at head")
    from app.core.config import get_settings
    from app.core.database_lifecycle import check_database, get_migration_revisions

    settings = get_settings()
    db_status, _ = check_database(settings)
    if db_status != "ready":
        item.warn("skipped — database not ready")
        return item
    try:
        current, head, _ = get_migration_revisions(settings)
        if current == head:
            item.pass_(head)
        else:
            item.fail(f"current={current} head={head}")
    except Exception as e:  # noqa: BLE001
        item.fail(str(e)[:120])
    return item


def _check_backend_health() -> RuntimeItem:
    item = RuntimeItem("backend health")
    host, port, in_use = probe_port_in_use()
    health_url = get_health_url()
    try:
        with httpx.Client(timeout=8.0) as client:
            r = client.get(health_url)
        if r.status_code == 200:
            status = r.json().get("status", "unknown")
            item.pass_(f"status={status}")
            return item
        item.fail(f"HTTP {r.status_code}")
        if in_use:
            item.detail += f"; {stale_port_hints(host, port).splitlines()[0]}"
    except httpx.HTTPError as e:
        if in_use:
            item.fail(f"port {port} in use but /health failed — possible stale uvicorn")
        else:
            item.fail(f"not reachable at {get_backend_base_url()}")
        if in_use:
            print(stale_port_hints(host, port))
    return item


def _check_readiness(client: httpx.Client, base: str) -> list[RuntimeItem]:
    item = RuntimeItem("readiness")
    url = f"{base}/api/v1/system/readiness"
    status, body, err = get_json(client, url)
    if err:
        item.fail(err)
        return [item]
    if status != 200:
        item.fail(f"HTTP {status}")
        return [item]
    data = (body or {}).get("data") or body or {}
    db_ok = data.get("database_ready")
    item.pass_(f"db={'ready' if db_ok else 'not ready'}")
    out = [item]
    if not data.get("redis_ready"):
        w = RuntimeItem("redis optional")
        w.warn("off")
        out.append(w)
    if not data.get("worker_ready"):
        w = RuntimeItem("worker optional")
        w.warn("off")
        out.append(w)
    return out


def _check_authed_endpoint(client: httpx.Client, base: str, path: str, label: str) -> RuntimeItem:
    item = RuntimeItem(label)
    headers = login_headers(client, base)
    if not headers:
        item.fail("login failed")
        return item
    url = f"{base}{path}"
    status, body, err = get_json(client, url, headers=headers)
    if err:
        item.fail(err)
        return item
    if status != 200:
        item.fail(f"HTTP {status}")
        return item
    item.pass_(f"HTTP {status}")
    return item


def _check_port_status() -> RuntimeItem:
    item = RuntimeItem("port status")
    host, port, in_use = probe_port_in_use()
    base = get_backend_base_url()
    if not in_use:
        item.pass_(f"{host}:{port} free")
        return item
    health_url = get_health_url()
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(health_url)
        if r.status_code == 200:
            item.pass_(f"{host}:{port} in use — backend already running")
        else:
            item.warn(f"{host}:{port} in use but /health HTTP {r.status_code} — stale?")
            print(stale_port_hints(host, port))
    except httpx.HTTPError:
        item.warn(f"{host}:{port} in use but /health unreachable — stale?")
        print(stale_port_hints(host, port))
        if port == 8010:
            print(f"[HINT] Try fallback: $env:BACKEND_BASE_URL=\"{FALLBACK_BACKEND}\"")
    return item


def _check_env_warnings() -> list[RuntimeItem]:
    items: list[RuntimeItem] = []
    pub = RuntimeItem("PUBLIC_BASE_URL")
    from app.core.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    pub_url = (getattr(settings, "PUBLIC_BASE_URL", None) or os.getenv("PUBLIC_BASE_URL") or "").strip()
    if pub_url:
        pub.pass_(pub_url)
    else:
        pub.warn("not set — required for production manifest URLs")
    items.append(pub)

    proxy = os.getenv("VITE_API_PROXY_TARGET", "").strip()
    backend = get_backend_base_url()
    align = RuntimeItem("BACKEND_BASE_URL / VITE_API_PROXY_TARGET")
    align.pass_(backend)
    if proxy and proxy.rstrip("/") != backend:
        align.warn(f"VITE_API_PROXY_TARGET={proxy} differs from BACKEND_BASE_URL")
    items.append(align)
    return items


def run(*, verbose: bool = True) -> int:
    if verbose:
        log_backend_base_url()
        print("D5.11 Dev Runtime Doctor")

    items: list[RuntimeItem] = [
        _check_database(),
        _check_migration(),
        _check_port_status(),
        _check_backend_health(),
    ]

    base = get_backend_base_url()
    try:
        with httpx.Client(timeout=15.0) as client:
            items.extend(_check_readiness(client, base))
            for path, label in (
                ("/api/a-domain/daily-ops-summary", "daily ops summary"),
                ("/api/a-domain/daily-work-summary", "daily work summary"),
                ("/api/a-domain/follow-up-queue", "follow-up queue"),
                ("/api/v1/portal/summary", "portal summary"),
            ):
                items.append(_check_authed_endpoint(client, base, path, label))
    except httpx.HTTPError as e:
        fail_item = RuntimeItem("backend API checks")
        fail_item.fail(str(e)[:120])
        items.append(fail_item)

    items.extend(_check_env_warnings())

    if verbose:
        for it in items:
            print(it.line())

    fails = [it for it in items if not it.ok]
    warns = [it for it in items if it.is_warn]

    if verbose:
        print()
        if fails:
            print("Result: FAIL")
        elif warns:
            print(f"Result: PASS ({len(warns)} warning(s))")
        else:
            print("Result: PASS")

    return 2 if fails else 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
