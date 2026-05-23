"""Check whether the configured backend is reachable (read-only, D5.2.6)."""

from __future__ import annotations

import socket
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import httpx

from app.core.backend_url import get_backend_base_url, get_health_url, log_backend_base_url, parse_backend_host_port


def run() -> int:
    base = log_backend_base_url()
    health_url = get_health_url()
    host, port = parse_backend_host_port()

    port_in_use = False
    try:
        with socket.create_connection((host, port), timeout=2.0):
            port_in_use = True
    except OSError:
        port_in_use = False

    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(health_url)
        if r.status_code == 200:
            body = r.json()
            status = body.get("status", "unknown")
            print(f"[OK] backend already running — {health_url} (status={status})")
            return 0
        print(f"[FAIL] {health_url} returned HTTP {r.status_code}")
        if port_in_use:
            print(
                f"[HINT] Port {port} on {host} is in use but /health is not OK — "
                "possible stale process or wrong service."
            )
            print(f"  netstat -ano | findstr :{port}")
            print("  tasklist /FI \"PID eq <PID>\"")
            print("  Stop-Process -Id <PID> -Force")
            print('[HINT] Fallback: $env:BACKEND_BASE_URL="http://127.0.0.1:8013"')
        return 1
    except httpx.ConnectError:
        if port_in_use:
            print(
                f"[WARN] Port {port} on {host} is in use but {health_url} did not respond — "
                "stale process or non-PartnerOS service may be bound."
            )
            print("[HINT] Use a different port, e.g. BACKEND_BASE_URL=http://127.0.0.1:8013")
        else:
            print(f"[FAIL] backend not reachable at {base}")
            print("[HINT] Start backend, e.g.:")
            print(f"  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port {port}")
        return 1
    except httpx.TimeoutException:
        print(f"[FAIL] timeout contacting {health_url}")
        return 1


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
