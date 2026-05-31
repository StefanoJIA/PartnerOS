"""D8 integration hardening contract check.

This script is intentionally local and read-only. It validates the bridge-facing
contract without deploying or touching service.intelli-opus.com.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import create_app
from app.models import FeedbackTicket, ManufacturingPartner, MarketIntelligenceItem, Product, User
from app.models.customer_orders import (
    CustomerOrder,
    OrderLineItem,
    OrderPartnerSplit,
    OrderProductionMilestone,
    ShipmentPlan,
)
from app.models.customer_quotes import Quote, QuoteLineItem

SERVICE_PORTAL_ORIGIN = "https://service.intelli-opus.com"
INTEGRATION_DOC = REPO_ROOT / "docs" / "phase3" / "d8_integration_hardening.md"
FORBIDDEN = (
    "internal_cost",
    "estimated_margin",
    "pricing_breakdown_json",
    "cost_snapshot_json",
    "supplier_private",
    "supplier_reference",
    "storage_key",
    "backend/storage",
    "password_hash",
    "secret_key",
    "portal_customer_api_token",
)
REQUIRED_DOCS = (
    "docs/phase3/d7_7_customer_portal_bridge_api.md",
    "docs/phase3/d7_8_service_portal_integration_uat.md",
    "docs/phase3/d7_9_resource_center.md",
    "docs/phase3/d8_1_rbac_scoped_access.md",
    "docs/phase3/d8_2_runtime_hardening.md",
    "docs/phase3/d8_3_service_portal_staging_integration.md",
    "docs/phase3/d8_4_multi_partner_operations_dashboard.md",
    "docs/phase3/d8_5_market_response_intelligence.md",
    "docs/phase3/d8_production_coordination_runbook.md",
)
REQUIRED_INTEGRATION_DOC_MARKERS = (
    "D8 Production Coordination Runbook",
    "d8_production_coordination_runbook.md",
    "python scripts/d8_production_coordination_runbook_check.py",
    "STAGING_VALIDATED",
    "WAITING_FOR_REAL_STAGING_EVIDENCE",
    "strict staging evidence from real staging values",
    "Go / No-Go handoff",
)


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


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args, **kwargs):  # noqa: ARG002
        return self

    def all(self):
        return self.rows


class _Db:
    def __init__(self) -> None:
        self.mapping = {
            OrderPartnerSplit: [],
            ManufacturingPartner: [],
            OrderProductionMilestone: [],
            ShipmentPlan: [],
            FeedbackTicket: [],
            Quote: [],
            QuoteLineItem: [],
            CustomerOrder: [],
            OrderLineItem: [],
            MarketIntelligenceItem: [],
            Product: [],
        }

    def query(self, model):
        return _Query(self.mapping.get(model, []))


def _fake_db():
    yield _Db()


def _safe_json(response) -> dict:
    try:
        return response.json()
    except Exception:  # noqa: BLE001
        return {}


def _finish(checks: list[Check]) -> int:
    print("D8 Integration Hardening Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


def _git_tracked_sensitive_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ["git ls-files failed"]
    sensitive: list[str] = []
    for raw in result.stdout.splitlines():
        path = raw.replace("\\", "/")
        name = Path(path).name.lower()
        if name == ".env" or path.startswith("local_data/") or path.startswith("backend/storage/"):
            sensitive.append(raw)
        if path.startswith("backend/") and name.endswith(".env"):
            sensitive.append(raw)
    return sensitive


def _configure_safe_env() -> None:
    os.environ.setdefault("BACKEND_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    os.environ["PORTAL_CUSTOMER_ALLOWED_ORIGINS"] = SERVICE_PORTAL_ORIGIN
    os.environ.setdefault("PORTAL_CUSTOMER_API_REQUIRE_TOKEN", "true")
    os.environ.setdefault("PORTAL_CUSTOMER_API_ENABLED", "true")
    os.environ.setdefault("PORTAL_CUSTOMER_API_TOKEN", "d8-integration-hardening-local-token")
    get_settings.cache_clear()


def _integration_doc_text() -> str:
    return INTEGRATION_DOC.read_text(encoding="utf-8") if INTEGRATION_DOC.exists() else ""


def main() -> int:
    checks = [
        Check("required D7-D8 docs present"),
        Check("integration hardening doc references production runbook"),
        Check("no tracked local secrets or storage"),
        Check("service portal CORS preflight"),
        Check("portal readiness safe"),
        Check("partner operations safety"),
        Check("market response safety"),
        Check("forbidden fields absent"),
    ]

    missing_docs = [path for path in REQUIRED_DOCS if not (REPO_ROOT / path).exists()]
    checks[0].pass_("all present") if not missing_docs else checks[0].fail(", ".join(missing_docs))

    integration_doc = _integration_doc_text()
    missing_doc_markers = [marker for marker in REQUIRED_INTEGRATION_DOC_MARKERS if marker not in integration_doc]
    checks[1].pass_("production runbook linked") if not missing_doc_markers else checks[1].fail(
        ", ".join(missing_doc_markers)
    )

    tracked_sensitive = _git_tracked_sensitive_files()
    checks[2].pass_("clean") if not tracked_sensitive else checks[2].fail(", ".join(tracked_sensitive[:5]))

    _configure_safe_env()
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User(
        id=uuid4(),
        email="d8_integration@test.example",
        is_active=True,
    )
    app.dependency_overrides[get_db] = _fake_db

    responses = []
    with TestClient(app, raise_server_exceptions=False) as client:
        preflight = client.options(
            "/api/v1/portal/customer/orders",
            headers={
                "Origin": SERVICE_PORTAL_ORIGIN,
                "Access-Control-Request-Method": "GET",
            },
        )
        portal_readiness = client.get("/api/v1/portal/customer/readiness")
        partner_ops = client.get("/api/v1/operations/partner-dashboard")
        market_response = client.get("/api/v1/market/response-intelligence")
        responses.extend([portal_readiness, partner_ops, market_response])

    allow_origin = preflight.headers.get("access-control-allow-origin")
    if preflight.status_code in (200, 204) and allow_origin == SERVICE_PORTAL_ORIGIN:
        checks[3].pass_("service.intelli-opus.com allowed")
    else:
        checks[3].fail(f"HTTP {preflight.status_code} allow-origin={allow_origin!r}")

    portal_data = (_safe_json(portal_readiness).get("data") or {}) if portal_readiness.status_code == 200 else {}
    portal_safety = portal_data.get("safety") or {}
    if portal_readiness.status_code == 200 and portal_safety.get("token_exposed") is False:
        checks[4].pass_("token not exposed")
    else:
        checks[4].fail(f"HTTP {portal_readiness.status_code}")

    partner_data = (_safe_json(partner_ops).get("data") or {}) if partner_ops.status_code == 200 else {}
    partner_safety = partner_data.get("safety") or {}
    if (
        partner_ops.status_code == 200
        and partner_safety.get("read_only") is True
        and partner_safety.get("supplier_notified") is False
        and partner_safety.get("order_status_changed") is False
    ):
        checks[5].pass_("read-only")
    else:
        checks[5].fail(f"HTTP {partner_ops.status_code}")

    market_data = (_safe_json(market_response).get("data") or {}) if market_response.status_code == 200 else {}
    market_safety = market_data.get("safety") or {}
    if (
        market_response.status_code == 200
        and market_safety.get("read_only") is True
        and market_safety.get("ai_executed") is False
        and market_safety.get("customer_notified") is False
        and market_safety.get("quote_status_changed") is False
    ):
        checks[6].pass_("advisory only")
    else:
        checks[6].fail(f"HTTP {market_response.status_code}")

    blob = json.dumps([_safe_json(response) for response in responses], ensure_ascii=False).lower()
    leaked = next((marker for marker in FORBIDDEN if marker in blob), None)
    checks[7].pass_("clean") if leaked is None else checks[7].fail(leaked)

    return _finish(checks)


if __name__ == "__main__":
    raise SystemExit(main())
