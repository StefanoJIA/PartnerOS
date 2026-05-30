"""Check strict staging input values before running network evidence."""

from __future__ import annotations

import os
from urllib.parse import urlparse

UNSAFE_TOKENS = {
    "",
    "<portal-server-token>",
    "test-portal-token",
    "dev-portal-token",
    "change-me",
    "d8-integration-hardening-local-token",
}
MIN_TOKEN_LENGTH = 24


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


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _is_https_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def _redacted(value: str) -> str:
    if not value:
        return "<missing>"
    if len(value) <= 6:
        return "***"
    return f"{value[:2]}***{value[-2:]}"


def main() -> int:
    checks = [
        Check("BACKEND_BASE_URL provided"),
        Check("BACKEND_BASE_URL is HTTPS"),
        Check("SERVICE_PORTAL_PARTNEROS_TOKEN provided"),
        Check("SERVICE_PORTAL_PARTNEROS_TOKEN is non-default and long enough"),
        Check("SERVICE_PORTAL_ORIGIN provided"),
        Check("SERVICE_PORTAL_ORIGIN is HTTPS"),
    ]

    backend_base = _env("BACKEND_BASE_URL").rstrip("/")
    token = _env("SERVICE_PORTAL_PARTNEROS_TOKEN") or _env("PORTAL_CUSTOMER_API_TOKEN")
    origin = _env("SERVICE_PORTAL_ORIGIN")

    checks[0].pass_("provided") if backend_base else checks[0].fail("missing")
    if not backend_base:
        checks[1].pass_("waiting for BACKEND_BASE_URL")
    elif _is_https_url(backend_base):
        checks[1].pass_("https origin")
    else:
        checks[1].fail("must be https URL")

    checks[2].pass_("provided") if token else checks[2].fail("missing")
    if not token:
        checks[3].pass_("waiting for SERVICE_PORTAL_PARTNEROS_TOKEN")
    elif token not in UNSAFE_TOKENS and len(token) >= MIN_TOKEN_LENGTH:
        checks[3].pass_(f"redacted={_redacted(token)}")
    else:
        checks[3].fail(f"placeholder, known default, or shorter than {MIN_TOKEN_LENGTH} characters")

    checks[4].pass_("provided") if origin else checks[4].fail("missing")
    if not origin:
        checks[5].pass_("waiting for SERVICE_PORTAL_ORIGIN")
    elif _is_https_url(origin):
        checks[5].pass_("https origin")
    else:
        checks[5].fail("must be https URL")

    hard_fail = any(not check.ok and check.detail != "missing" for check in checks)
    missing_only = any(not check.ok for check in checks) and not hard_fail
    if all(check.ok for check in checks):
        state = "INPUTS_READY"
    elif missing_only:
        state = "WAITING_FOR_PRIVATE_VALUES"
    else:
        state = "INPUTS_UNSAFE"

    print("D8 Staging Input Preflight Check")
    for check in checks:
        print(check.line())
    print(f"Input State: {state}")
    print("Safety: token values are never printed; only a short redacted fingerprint is shown when present.")
    print(f"Result: {'PASS' if state != 'INPUTS_UNSAFE' else 'FAIL'}")
    return 0 if state != "INPUTS_UNSAFE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
