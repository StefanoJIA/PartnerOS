"""Shared helpers for D5.11 runtime / smoke scripts."""

from __future__ import annotations

import socket
from typing import Any

import httpx

from app.core.backend_url import get_backend_base_url, get_health_url, parse_backend_host_port


class RuntimeItem:
    """Single runtime check result."""

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

    @property
    def ok(self) -> bool:
        return self.level != "FAIL"

    @property
    def is_warn(self) -> bool:
        return self.level == "WARN"

    def line(self) -> str:
        suffix = f" ({self.detail})" if self.detail else ""
        return f"[{self.level}] {self.label}{suffix}"


def probe_port_in_use() -> tuple[str, int, bool]:
    host, port = parse_backend_host_port()
    try:
        with socket.create_connection((host, port), timeout=2.0):
            return host, port, True
    except OSError:
        return host, port, False


def stale_port_hints(host: str, port: int) -> str:
    return (
        f"Port {port} on {host} may be stale. Manual check:\n"
        f"  netstat -ano | findstr :{port}\n"
        f"  tasklist /FI \"PID eq <PID>\"\n"
        f"  Stop-Process -Id <PID> -Force\n"
        f"Fallback: $env:BACKEND_BASE_URL=\"http://127.0.0.1:8013\"; "
        f"$env:VITE_API_PROXY_TARGET=\"http://127.0.0.1:8013\""
    )


def login_headers(client: httpx.Client, base: str | None = None) -> dict[str, str] | None:
    base = base or get_backend_base_url()
    try:
        r = client.post(
            f"{base}/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )
        if r.status_code != 200:
            return None
        token = r.json().get("access_token")
        if not token:
            return None
        return {"Authorization": f"Bearer {token}"}
    except httpx.HTTPError:
        return None


def friendly_http_error(exc: Exception, url: str) -> str:
    if isinstance(exc, httpx.ConnectError):
        return f"connection refused — is backend running at {url}?"
    if isinstance(exc, httpx.TimeoutException):
        return f"timeout contacting {url}"
    if isinstance(exc, httpx.HTTPError):
        return str(exc)[:160]
    return str(exc)[:160]


def get_json(
    client: httpx.Client,
    url: str,
    headers: dict[str, str] | None = None,
) -> tuple[int | None, Any, str | None]:
    try:
        r = client.get(url, headers=headers)
        if "application/json" not in (r.headers.get("content-type") or ""):
            if r.status_code == 200:
                return r.status_code, None, "non-JSON response (stale process or wrong service?)"
            return r.status_code, None, f"HTTP {r.status_code} non-JSON"
        return r.status_code, r.json(), None
    except httpx.HTTPError as e:
        return None, None, friendly_http_error(e, url)
