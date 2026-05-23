"""SSRF-safe URL validation for company website enrichment (D5.2)."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


def strip_www(host: str) -> str:
    h = host.lower().strip(".")
    if h.startswith("www."):
        return h[4:]
    return h


def hosts_match_allowed(url_host: str, company_host: str) -> bool:
    return strip_www(url_host) == strip_www(company_host)


def is_blocked_hostname(hostname: str) -> bool:
    h = hostname.lower().strip(".")
    if not h or h == "localhost":
        return True
    if h.endswith(".localhost") or h.endswith(".local"):
        return True
    # literal IP
    try:
        ip = ipaddress.ip_address(h)
        return bool(
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
        )
    except ValueError:
        pass
    return False


def validate_public_http_url(url: str, allowed_hostname: str) -> tuple[bool, str]:
    try:
        p = urlparse(url)
    except Exception:  # noqa: BLE001
        return False, "invalid_url_parse"
    if p.scheme not in ("http", "https"):
        return False, "invalid_scheme"
    if not p.hostname:
        return False, "missing_host"
    if is_blocked_hostname(p.hostname):
        return False, "blocked_host"
    if not hosts_match_allowed(p.hostname, allowed_hostname):
        return False, "host_mismatch"
    return True, ""
