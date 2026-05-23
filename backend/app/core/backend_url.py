"""Configurable backend base URL for local scripts and health checks (D5.2.6)."""

from __future__ import annotations

import os
from urllib.parse import urlparse

DEFAULT_BACKEND_BASE_URL = "http://127.0.0.1:8000"


def get_backend_base_url() -> str:
    raw = os.getenv("BACKEND_BASE_URL", DEFAULT_BACKEND_BASE_URL).strip()
    if not raw:
        return DEFAULT_BACKEND_BASE_URL
    return raw.rstrip("/")


def get_health_url() -> str:
    return f"{get_backend_base_url()}/health"


def parse_backend_host_port() -> tuple[str, int]:
    parsed = urlparse(get_backend_base_url())
    host = parsed.hostname or "127.0.0.1"
    if parsed.port is not None:
        port = parsed.port
    elif parsed.scheme == "https":
        port = 443
    else:
        port = 80
    return host, port


def log_backend_base_url() -> str:
    url = get_backend_base_url()
    print(f"Using BACKEND_BASE_URL={url}")
    return url
