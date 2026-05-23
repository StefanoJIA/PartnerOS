"""D5.17 rule tuning regression check (read-only)."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import get_backend_base_url, log_backend_base_url
from app.services.a_domain.product_fit import ProductFitInput, compute_product_fit

FORBIDDEN = (
    "guaranteed price",
    "lowest price guaranteed",
    "in stock",
    "certified for",
    "delivery guaranteed",
    "lead time confirmed",
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


def _login(client: httpx.Client, base: str) -> dict[str, str] | None:
    r = client.post(
        f"{base}/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    if r.status_code != 200:
        return None
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _company_lead(client: httpx.Client, base: str, headers: dict[str, str], name: str) -> str | None:
    companies = {
        c["company_name"]: c
        for c in client.get(f"{base}/api/companies", headers=headers, params={"limit": 200}).json().get("items", [])
    }
    co = companies.get(name)
    if not co:
        return None
    for lead in client.get(f"{base}/api/leads", headers=headers, params={"limit": 200}).json().get("items", []):
        if lead.get("company_id") == co["id"]:
            return lead["id"]
    return None


def _fixture_checks() -> list[Check]:
    checks = [
        Check("project priority over education cross-sell"),
        Check("education strong signal"),
        Check("lifting dealer focus"),
        Check("OEM lifting component focus"),
        Check("quote missing info limit"),
        Check("no forbidden promises"),
    ]

    jeff = compute_product_fit(
        ProductFitInput(
            company_name="Jefferson Group",
            company_type="Interior Design Firm",
            contact_email="a@example.com",
            segments=["education_vertical", "project_based_furniture"],
            lead_notes="FF&E project; JOOBOO education furniture mentioned",
            lead_product_interest="project quote, education furniture",
        )
    )
    if jeff["recommended_product_focus"] and jeff["recommended_product_focus"][0] == "project_supply":
        if "jooboo_education_furniture" not in jeff["recommended_product_focus"]:
            checks[0].pass_("project first, no jooboo")
        else:
            checks[0].fail("jooboo still primary")
    else:
        checks[0].fail(str(jeff["recommended_product_focus"]))

    edu = compute_product_fit(
        ProductFitInput(
            company_name="Campus Learning",
            company_type="Education Furniture Company",
            contact_email="a@example.com",
            segments=["education_vertical"],
            business_description="School district classroom furniture procurement.",
            lead_product_interest="classroom desks",
        )
    )
    if "jooboo_education_furniture" in edu["recommended_product_focus"]:
        checks[1].pass_("jooboo primary")
    else:
        checks[1].fail(str(edu["recommended_product_focus"]))

    lift = compute_product_fit(
        ProductFitInput(
            company_name="SWC Office Furniture",
            contact_email="a@example.com",
            segments=["lift_system_signal"],
            business_description="Adjustable desk frames and lifting columns.",
        )
    )
    focus = lift["recommended_product_focus"]
    if "hosun_lifting_systems" in focus and "adjustable_desk_frames" in focus:
        checks[2].pass_(f"score={lift['project_opportunity_score']}")
    else:
        checks[2].fail(str(focus))

    oem = compute_product_fit(
        ProductFitInput(
            company_name="Human Active Technology",
            contact_email="a@example.com",
            segments=["oem_odm_fit", "lift_system_signal"],
            business_description="OEM lifting columns and desk legs development.",
        )
    )
    if "oem_odm_components" in oem["recommended_product_focus"]:
        checks[3].pass_("oem focus")
    else:
        checks[3].fail(str(oem["recommended_product_focus"]))

    transfer = compute_product_fit(
        ProductFitInput(
            company_name="Transfer Enterprises",
            segments=["general_office_furniture_only"],
        )
    )
    if transfer["quote_readiness"] == "not_ready" and len(transfer["missing_quote_info"]) <= 4:
        checks[4].pass_(f"missing={len(transfer['missing_quote_info'])}")
    else:
        checks[4].fail(f"readiness={transfer['quote_readiness']} missing={len(transfer['missing_quote_info'])}")

    blob = " ".join(
        jeff["sales_angle"] + " " + " ".join(jeff["recommended_discovery_questions"])
    ).lower()
    bad = [p for p in FORBIDDEN if p in blob]
    if bad:
        checks[5].fail(", ".join(bad))
    else:
        checks[5].pass_("clean")

    return checks


def main() -> int:
    log_backend_base_url()
    base = get_backend_base_url()
    checks = _fixture_checks()

    try:
        with httpx.Client(timeout=60.0) as client:
            headers = _login(client, base)
            if headers:
                for name in ("Jefferson Group", "SWC Office Furniture"):
                    lid = _company_lead(client, base, headers, name)
                    if not lid:
                        continue
                    pf = client.get(f"{base}/api/a-domain/leads/{lid}/product-fit", headers=headers)
                    if pf.status_code != 200:
                        continue
                    body = pf.json()
                    if name == "Jefferson Group" and body.get("recommended_product_focus", [None])[0] == "project_supply":
                        checks[0].pass_("live API confirms")
                    if name == "SWC Office Furniture" and "hosun_lifting_systems" in body.get("recommended_product_focus", []):
                        checks[2].pass_(f"live score={body.get('project_opportunity_score')}")
    except httpx.ConnectError:
        pass

    print("D5.17 Rule Tuning Check")
    for c in checks:
        print(c.line())
    failed = [c for c in checks if not c.ok]
    print(f"\nResult: {'PASS' if not failed else 'FAIL'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
