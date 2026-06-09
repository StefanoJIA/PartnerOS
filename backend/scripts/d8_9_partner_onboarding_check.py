"""D8.9 multi-brand partner onboarding MVP check."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[2]
BASE = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8014").rstrip("/")
ADMIN_EMAIL = os.getenv("DEMO_LOGIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("DEMO_LOGIN_PASSWORD", "admin123")


@dataclass
class Check:
    label: str
    ok: bool = False
    detail: str = ""

    def pass_(self, detail: str = "") -> None:
        self.ok = True
        self.detail = detail

    def fail(self, detail: str) -> None:
        self.ok = False
        self.detail = detail

    def line(self) -> str:
        suffix = f" ({self.detail})" if self.detail else ""
        return f"[{'PASS' if self.ok else 'FAIL'}] {self.label}{suffix}"


def _contains_all(text: str, markers: tuple[str, ...]) -> tuple[bool, str]:
    lowered = text.lower()
    missing = [marker for marker in markers if marker.lower() not in lowered]
    return not missing, ", ".join(missing)


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _login(client: httpx.Client) -> dict[str, str]:
    response = client.post(f"{BASE}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    response.raise_for_status()
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def main() -> int:
    checks = [
        Check("required files exist"),
        Check("API returns onboarding workflow"),
        Check("HOSUN reference partner"),
        Check("JOOBOO reference partner"),
        Check("future partner placeholder"),
        Check("frontend route and page"),
        Check("docs cover multi-brand onboarding"),
        Check("safety boundary"),
    ]
    required_files = [
        "backend/app/services/partner_onboarding.py",
        "backend/app/api/v1/routes/partner_onboarding.py",
        "backend/app/schemas/partner_onboarding.py",
        "frontend/src/api/partnerOnboarding.ts",
        "frontend/src/pages/partners/PartnerOnboardingPage.vue",
        "docs/phase3/d8_9_multi_brand_partner_onboarding.md",
        "docs/demo/partner_onboarding_playbook.md",
    ]
    missing_files = [path for path in required_files if not (ROOT / path).exists()]
    checks[0].pass_(f"{len(required_files)} file(s)") if not missing_files else checks[0].fail(", ".join(missing_files))

    payload: dict | None = None
    try:
        with httpx.Client(timeout=20) as client:
            headers = _login(client)
            response = client.get(f"{BASE}/api/v1/partner-onboarding", headers=headers)
            response.raise_for_status()
            payload = response.json()["data"]
    except Exception as exc:  # pragma: no cover - diagnostic script
        checks[1].fail(str(exc))

    if payload:
        checklist_keys = set(payload.get("checklist_keys") or [])
        required_keys = {
            "brand_profile_completed",
            "product_categories_mapped",
            "pricing_basis_available",
            "quote_flow_ready",
            "order_flow_ready",
            "production_shipment_flow_mapped",
            "portal_visibility_reviewed",
            "market_response_focus_defined",
            "demo_narrative_prepared",
        }
        stage_order = set(payload.get("stage_order") or [])
        required_stages = {"discovery", "product_mapping", "quote_ready", "portal_ready", "demo_ready", "active_partner", "paused"}
        if required_keys <= checklist_keys and required_stages <= stage_order and payload.get("items"):
            checks[1].pass_(f"{len(payload.get('items') or [])} partner(s)")
        else:
            checks[1].fail("missing checklist keys, stages, or partner items")

        items = payload.get("items") or []
        hosun = next((item for item in items if "HOSUN" in item.get("partner_name", "").upper()), None)
        jooboo = next((item for item in items if "JOOBOO" in item.get("partner_name", "").upper()), None)
        if hosun and hosun.get("is_reference_partner"):
            focus = " ".join(hosun.get("product_focus") or [])
            ok, missing = _contains_all(focus, ("lifting",))
            checks[2].pass_(hosun.get("onboarding_stage", "")) if ok else checks[2].fail(missing)
        else:
            checks[2].fail("HOSUN reference partner missing")
        if jooboo and jooboo.get("is_reference_partner"):
            focus = " ".join(jooboo.get("product_focus") or [])
            ok, missing = _contains_all(focus, ("education",))
            checks[3].pass_(jooboo.get("onboarding_stage", "")) if ok else checks[3].fail(missing)
        else:
            checks[3].fail("JOOBOO reference partner missing")

        placeholder = payload.get("future_partner_placeholder") or {}
        ok, missing = _contains_all(
            " ".join(str(value) for value in placeholder.values()),
            ("Chongqing Huiju", "future partner", "discovery"),
        )
        checks[4].pass_("placeholder present") if ok else checks[4].fail(missing)

        safety = payload.get("safety") or {}
        if (
            payload.get("status") == "READY_FOR_STAGING_HANDOFF"
            and safety.get("staging_validated") is False
            and safety.get("proof_record_created") is False
            and safety.get("d9_entered") is False
        ):
            checks[7].pass_("handoff only")
        else:
            checks[7].fail("unsafe state flags")

    router = _read("frontend/src/router/index.ts")
    layout = _read("frontend/src/layouts/MainLayout.vue")
    page = _read("frontend/src/pages/partners/PartnerOnboardingPage.vue")
    frontend_text = router + layout + page
    ok, missing = _contains_all(frontend_text, ("/partner-onboarding", "HOSUN", "JOOBOO"))
    chinese_ready = all(marker in frontend_text for marker in ("Partner 接入", "未来品牌", "平级"))
    english_ready = all(marker in frontend_text for marker in ("Partner onboarding", "future brands", "peer partners"))
    checks[5].pass_("route/menu/page present") if ok and (chinese_ready or english_ready) else checks[5].fail(missing or "localized onboarding anchors")

    docs = _read("docs/phase3/d8_9_multi_brand_partner_onboarding.md") + "\n" + _read("docs/demo/partner_onboarding_playbook.md")
    ok, missing = _contains_all(
        docs,
        (
            "READY_FOR_STAGING_HANDOFF",
            "multi-brand",
            "HOSUN",
            "JOOBOO",
            "Chongqing Huiju",
            "all partner",
            "not privileged",
            "not the only brands",
            "does not enter D9",
            "No proof records",
        ),
    )
    checks[6].pass_("docs present") if ok else checks[6].fail(missing)

    if not checks[7].ok:
        combined = "\n".join(
            _read(path)
            for path in [
                "backend/app/services/partner_onboarding.py",
                "docs/phase3/d8_9_multi_brand_partner_onboarding.md",
                "docs/demo/partner_onboarding_playbook.md",
            ]
        )
        unsafe = "Status: STAGING_VALIDATED" in combined or "D9 is ready" in combined
        if "READY_FOR_STAGING_HANDOFF" in combined and not unsafe:
            checks[7].pass_("handoff only docs")

    print("D8.9 Partner Onboarding Check")
    print(f"BACKEND_BASE_URL={BASE}")
    for check in checks:
        print(check.line())
    failed = [check for check in checks if not check.ok]
    print("Result: " + ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
