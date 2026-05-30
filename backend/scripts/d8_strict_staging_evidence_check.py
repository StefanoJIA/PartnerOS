"""D8 strict staging/cloud validation evidence collector.

This check runs against a real deployed PartnerOS backend. It is read-only by
default and does not modify service.intelli-opus.com, nginx, orders, quotes,
partners, shipments, feedback, files, or notifications.
"""

from __future__ import annotations

import json
import os
import sys
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import httpx

FORBIDDEN = (
    "internal_cost",
    "estimated_margin",
    "margin",
    "pricing_breakdown_json",
    "cost_snapshot_json",
    "supplier_private",
    "supplier_reference",
    "storage_key",
    "backend/storage",
    "portal_customer_api_token",
    "secret_key",
    "password_hash",
    "database_url",
)
UNSAFE_TOKENS = {"", "test-portal-token", "dev-portal-token", "change-me", "d8-integration-hardening-local-token"}


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

    def evidence(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "status": "PASS" if self.ok else "FAIL",
            "detail": self.detail,
        }


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _base_url() -> str:
    return _env("BACKEND_BASE_URL").rstrip("/")


def _origin() -> str:
    return _env("SERVICE_PORTAL_ORIGIN", "https://service.intelli-opus.com")


def _portal_token() -> str:
    return (_env("SERVICE_PORTAL_PARTNEROS_TOKEN") or _env("PORTAL_CUSTOMER_API_TOKEN")).strip()


def _allow_local_http() -> bool:
    return _truthy(os.getenv("D8_STRICT_ALLOW_LOCAL_HTTP"))


def _json(response: httpx.Response | None) -> Any:
    if response is None:
        return {}
    try:
        return response.json()
    except ValueError:
        return {}


def _redacted_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.username or parsed.password:
        host = parsed.hostname or ""
        port = f":{parsed.port}" if parsed.port else ""
        return f"{parsed.scheme}://***:***@{host}{port}{parsed.path or ''}"
    return url


def _is_localhost(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in {"localhost", "127.0.0.1", "::1"}


def _no_forbidden_blob(token: str, *payloads: Any) -> tuple[bool, str]:
    blob = json.dumps(payloads, ensure_ascii=False).lower()
    for marker in FORBIDDEN:
        if marker in blob:
            return False, marker
    if token and token.lower() in blob:
        return False, "portal token leaked"
    return True, "clean"


def _get(client: httpx.Client, path: str, headers: dict[str, str] | None = None) -> httpx.Response | None:
    try:
        return client.get(f"{_base_url()}{path}", headers=headers)
    except httpx.HTTPError:
        return None


def _envelope_ok(response: httpx.Response | None) -> bool:
    if not response or response.status_code != 200:
        return False
    body = _json(response)
    return isinstance(body, dict) and body.get("ok") is True and isinstance(body.get("data"), dict)


def _parse_args() -> Any:
    parser = ArgumentParser(description="Collect D8 strict staging/cloud validation evidence.")
    parser.add_argument(
        "--evidence-json",
        help="Optional path for redacted JSON evidence. The file must live outside backend/storage and local_data.",
    )
    parser.add_argument(
        "--gap-markdown",
        help="Optional path for a redacted Markdown follow-up register when checks fail.",
    )
    return parser.parse_args()


def _safe_evidence_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = BACKEND_ROOT / path
    resolved = path.resolve()
    repo_root = BACKEND_ROOT.parent.resolve()
    forbidden_roots = ((repo_root / "local_data").resolve(), (BACKEND_ROOT / "storage").resolve())
    for root in forbidden_roots:
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        raise ValueError("evidence path must not be under local_data or backend/storage")
    return resolved


def _safe_output_path(raw: str) -> Path:
    return _safe_evidence_path(raw)


def _recommended_action(check: Check) -> str:
    label = check.label.lower()
    if "backend_base_url" in label or "https staging url" in label:
        return "Set BACKEND_BASE_URL to the deployed HTTPS PartnerOS staging origin."
    if "portal origin" in label or "cors" in label:
        return "Align SERVICE_PORTAL_ORIGIN and PORTAL_CUSTOMER_ALLOWED_ORIGINS with the service portal HTTPS origin."
    if "token" in label:
        return "Rotate and configure a non-default SERVICE_PORTAL_PARTNEROS_TOKEN without printing it in logs."
    if "health" in label or "readiness" in label or "manifest" in label:
        return "Check deployed backend health, database readiness, migrations, PUBLIC_BASE_URL, and reverse proxy routing."
    if "products" in label or "orders" in label or "subresources" in label:
        return "Verify portal bridge API enablement, token configuration, database seed/data availability, and route wiring."
    if "forbidden" in label or "leakage" in label:
        return "Stop staging handoff and inspect portal field filters before exposing the bridge to the customer portal."
    return "Investigate the failing staging evidence and record the owner, fix, and rerun date."


def _write_gap_markdown(raw_path: str | None, *, checks: list[Check], base: str, origin: str) -> None:
    if not raw_path:
        return
    failing = [check for check in checks if not check.ok]
    path = _safe_output_path(raw_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# D8 Strict Staging Gap Register",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        f"Backend: `{_redacted_url(base) or '<missing>'}`",
        f"Service portal origin: `{origin}`",
        "",
        "Safety boundary: this register is derived from a read-only evidence run. It does not include tokens, response bodies, customer files, storage paths, or backend secrets.",
        "",
    ]
    if not failing:
        lines.extend(["## Result", "", "No failing checks were recorded."])
    else:
        lines.extend(
            [
                "## Follow-Up Items",
                "",
                "| Check | Detail | Recommended action | Owner | Status |",
                "|---|---|---|---|---|",
            ]
        )
        for check in failing:
            detail = check.detail.replace("|", "\\|") or "n/a"
            lines.append(
                f"| {check.label} | {detail} | {_recommended_action(check)} | TBD | open |"
            )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_evidence(raw_path: str | None, *, checks: list[Check], base: str, origin: str, allow_local: bool) -> None:
    if not raw_path:
        return
    path = _safe_evidence_path(raw_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": "d8_strict_staging_evidence_check.py",
        "backend_base_url": _redacted_url(base) or "<missing>",
        "service_portal_origin": origin,
        "allow_local_http": allow_local,
        "write_actions": False,
        "result": "PASS" if all(check.ok for check in checks) else "FAIL",
        "checks": [check.evidence() for check in checks],
        "safety": {
            "token_redacted": True,
            "response_bodies_stored": False,
            "customer_portal_deployed": False,
            "nginx_changed": False,
            "business_records_mutated": False,
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _finish(
    *,
    checks: list[Check],
    base: str,
    origin: str,
    allow_local: bool,
    evidence_json: str | None,
    gap_markdown: str | None,
) -> int:
    print("D8 Strict Staging Evidence Check")
    print(f"BACKEND_BASE_URL={_redacted_url(base) or '<missing>'}")
    print(f"SERVICE_PORTAL_ORIGIN={origin}")
    print(f"allow_local_http={allow_local}")
    print("write_actions=false")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    try:
        _write_evidence(evidence_json, checks=checks, base=base, origin=origin, allow_local=allow_local)
        _write_gap_markdown(gap_markdown, checks=checks, base=base, origin=origin)
    except OSError as exc:
        print(f"[FAIL] evidence output write ({str(exc)[:120]})")
        passed = False
    except ValueError as exc:
        print(f"[FAIL] evidence output path ({exc})")
        passed = False
    else:
        if evidence_json:
            print(f"evidence_json={_safe_evidence_path(evidence_json)}")
        if gap_markdown:
            print(f"gap_markdown={_safe_output_path(gap_markdown)}")
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


def main() -> int:
    args = _parse_args()
    base = _base_url()
    origin = _origin()
    token = _portal_token()
    headers = {"X-Portal-Customer-Token": token}
    allow_local = _allow_local_http()

    checks = [
        Check("BACKEND_BASE_URL configured"),
        Check("HTTPS staging URL"),
        Check("portal origin HTTPS"),
        Check("portal token safe"),
        Check("health reachable"),
        Check("system readiness envelope"),
        Check("portal manifest envelope"),
        Check("missing token rejected"),
        Check("wrong token rejected"),
        Check("CORS preflight allows service portal"),
        Check("portal products endpoint"),
        Check("portal orders endpoint"),
        Check("portal order subresources"),
        Check("no forbidden fields or token leakage"),
    ]

    if base:
        checks[0].pass_(_redacted_url(base))
    else:
        checks[0].fail("set BACKEND_BASE_URL")

    if base and urlparse(base).scheme == "https":
        checks[1].pass_("https")
    elif base and allow_local and _is_localhost(base):
        checks[1].pass_("local http explicitly allowed")
    else:
        checks[1].fail("staging/cloud validation requires HTTPS BACKEND_BASE_URL")

    if urlparse(origin).scheme == "https":
        checks[2].pass_(origin)
    else:
        checks[2].fail("SERVICE_PORTAL_ORIGIN must be HTTPS")

    if token and token not in UNSAFE_TOKENS and len(token) >= 24:
        checks[3].pass_("configured")
    else:
        checks[3].fail("set a non-default SERVICE_PORTAL_PARTNEROS_TOKEN")

    if not checks[0].ok:
        for item in checks[4:]:
            item.fail("not attempted; BACKEND_BASE_URL missing")
        return _finish(
            checks=checks,
            base=base,
            origin=origin,
            allow_local=allow_local,
            evidence_json=args.evidence_json,
            gap_markdown=args.gap_markdown,
        )

    responses: list[httpx.Response | dict[str, Any] | None] = []
    order_items: list[dict[str, Any]] = []
    with httpx.Client(timeout=20.0, follow_redirects=False) as client:
        try:
            health = client.get(f"{base}/health")
        except httpx.HTTPError as exc:
            health = None
            checks[4].fail(str(exc)[:120])
        else:
            if health.status_code == 200:
                checks[4].pass_("HTTP 200")
            else:
                checks[4].fail(f"HTTP {health.status_code}")
        responses.append(health)

        readiness = _get(client, "/api/v1/system/readiness")
        responses.append(readiness)
        if _envelope_ok(readiness):
            data = _json(readiness).get("data") or {}
            ok_detail = "ready" if data.get("ok") is True else "envelope ok; readiness degraded"
            checks[5].pass_(ok_detail)
        else:
            checks[5].fail(f"HTTP {readiness.status_code if readiness else 'unreachable'}")

        manifest = _get(client, "/api/v1/portal/manifest")
        responses.append(manifest)
        if _envelope_ok(manifest):
            data = _json(manifest).get("data") or {}
            manifest_base = str(data.get("base_url") or "")
            if manifest_base.startswith("https://") or (allow_local and manifest_base.startswith("http://")):
                checks[6].pass_(manifest_base)
            else:
                checks[6].fail("manifest base_url is not staging-safe")
        else:
            checks[6].fail(f"HTTP {manifest.status_code if manifest else 'unreachable'}")

        missing = _get(client, "/api/v1/portal/customer/products?limit=1")
        wrong = _get(client, "/api/v1/portal/customer/products?limit=1", headers={"X-Portal-Customer-Token": "wrong"})
        responses.extend([missing, wrong])
        checks[7].pass_("HTTP 401") if missing and missing.status_code == 401 else checks[7].fail(
            f"HTTP {missing.status_code if missing else 'unreachable'}"
        )
        checks[8].pass_("HTTP 403") if wrong and wrong.status_code == 403 else checks[8].fail(
            f"HTTP {wrong.status_code if wrong else 'unreachable'}"
        )

        try:
            preflight = client.options(
                f"{base}/api/v1/portal/customer/products",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "x-portal-customer-token",
                },
            )
        except httpx.HTTPError as exc:
            preflight = None
            checks[9].fail(str(exc)[:120])
        else:
            allow_origin = preflight.headers.get("access-control-allow-origin", "")
            if preflight.status_code in {200, 204} and allow_origin == origin:
                checks[9].pass_(origin)
            else:
                checks[9].fail(f"HTTP {preflight.status_code} allow-origin={allow_origin or 'missing'}")
        responses.append(preflight)

        products = _get(client, "/api/v1/portal/customer/products?limit=5", headers=headers)
        orders = _get(client, "/api/v1/portal/customer/orders?limit=5", headers=headers)
        responses.extend([products, orders])
        checks[10].pass_(f"HTTP {products.status_code}") if products and products.status_code == 200 else checks[
            10
        ].fail(f"HTTP {products.status_code if products else 'unreachable'}")
        checks[11].pass_(f"HTTP {orders.status_code}") if orders and orders.status_code == 200 else checks[11].fail(
            f"HTTP {orders.status_code if orders else 'unreachable'}"
        )

        if orders and orders.status_code == 200:
            order_items = ((_json(orders).get("data") or {}).get("items") or [])[:1]
        if order_items:
            order_id = order_items[0].get("id")
            detail = _get(client, f"/api/v1/portal/customer/orders/{order_id}", headers=headers)
            production = _get(client, f"/api/v1/portal/customer/orders/{order_id}/production", headers=headers)
            shipment = _get(client, f"/api/v1/portal/customer/orders/{order_id}/shipment", headers=headers)
            resources = _get(client, f"/api/v1/portal/customer/orders/{order_id}/resources", headers=headers)
            responses.extend([detail, production, shipment, resources])
            if all(response and response.status_code == 200 for response in (detail, production, shipment, resources)):
                checks[12].pass_(str(order_id))
            else:
                status_list = ", ".join(
                    str(response.status_code if response else "unreachable")
                    for response in (detail, production, shipment, resources)
                )
                checks[12].fail(status_list)
        else:
            checks[12].pass_("no order rows")

    clean, detail = _no_forbidden_blob(token, *responses)
    checks[13].pass_(detail) if clean else checks[13].fail(detail)

    return _finish(
        checks=checks,
        base=base,
        origin=origin,
        allow_local=allow_local,
        evidence_json=args.evidence_json,
        gap_markdown=args.gap_markdown,
    )


if __name__ == "__main__":
    raise SystemExit(main())
