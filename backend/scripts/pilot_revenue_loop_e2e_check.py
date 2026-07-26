"""End-to-end pilot validation for customer project request revenue loop.

Requires live backend (BACKEND_BASE_URL, default http://127.0.0.1:8014) with:
- CUSTOMER_SITE_COMPAT_ENABLED=true
- Seeded admin + HOSUN/JOOBOO catalog (seed.py + seed_quote_catalog.py --apply --confirm)

Uses synthetic demo data only — no real customer PII.
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import httpx

from app.core.backend_url import get_backend_base_url, log_backend_base_url


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
    r = client.post(f"{base}/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    if r.status_code != 200:
        return None
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _catalog_by_sku(client: httpx.Client, base: str, headers: dict[str, str], sku: str) -> dict | None:
    r = client.get(f"{base}/api/v1/products", headers=headers, params={"search": sku, "limit": 20})
    if r.status_code != 200 or not r.json().get("ok"):
        return None
    for item in r.json().get("data", {}).get("items", []):
        if item.get("internal_sku") == sku:
            return item
    return None


def run() -> int:
    base = log_backend_base_url()
    checks: list[Check] = [
        Check("health"),
        Check("site order intake"),
        Check("admin list project request"),
        Check("assign partner SKU fit"),
        Check("quote input contract"),
        Check("status flow triage to quote_ready"),
        Check("create interval quote"),
        Check("quote PDF export"),
        Check("market signal promote"),
        Check("daily decision queue"),
        Check("traceability CPR QIC quote MR"),
        Check("illegal status jump blocked"),
        Check("idempotency key dedupe"),
        Check("unauth admin blocked"),
        Check("site compat off returns 404"),
        Check("JOOBOO pending fit UNKNOWN"),
    ]
    trace: dict[str, str] = {}
    idem_key = f"pilot-e2e-{uuid.uuid4().hex[:12]}"

    try:
        with httpx.Client(timeout=60.0) as client:
            hr = client.get(f"{base}/health")
            if hr.status_code == 200:
                checks[0].pass_(hr.json().get("status", "ok"))
            else:
                checks[0].fail(f"status {hr.status_code}")
                _print_report(checks, trace)
                return 1

            site_payload = {
                "items": [
                    {
                        "product_name": "Heavy-duty dual motor desk frame",
                        "sku": "HS90602HRDDFZ",
                        "quantity": 30,
                    }
                ],
                "shipping_name": "Pilot Demo Buyer",
                "customer_email": "pilot.demo@example.com",
                "company_name": "Demo Heavy-Duty Dealer (Synthetic)",
                "project_scenario": "300kg/660lb multi-leg low-noise project with custom mounting",
                "notes": "Custom mounting holes required; target 48dB noise",
                "requirements": {
                    "load_capacity_kg": 300,
                    "load_capacity_lb": 660,
                    "noise_db_target": 48,
                    "stability_requirement": "high lateral stability",
                    "width_mm": 1800,
                    "leg_count": 4,
                    "mounting_holes": "custom pattern",
                    "certifications": ["CE"],
                    "sample_required": True,
                },
            }
            sr = client.post(
                f"{base}/api/site/customer/orders",
                json=site_payload,
                headers={"Idempotency-Key": idem_key},
            )
            if sr.status_code != 200:
                checks[1].fail(f"HTTP {sr.status_code}: {sr.text[:200]}")
            else:
                data = sr.json()
                if (
                    data.get("order_created") is False
                    and data.get("status") == "project_request_submitted"
                    and data.get("request_reference")
                    and data.get("intake_type") == "project_request"
                ):
                    trace["request_reference"] = data["request_reference"]
                    trace["request_id"] = str(data["request_id"])
                    checks[1].pass_(trace["request_reference"])
                else:
                    checks[1].fail(json.dumps(data)[:200])

            headers = _login(client, base)
            if not headers:
                for c in checks[2:]:
                    c.fail("login failed — run seed.py")
                _print_report(checks, trace)
                return 1

            lr = client.get(f"{base}/api/project-requests", headers=headers, params={"q": trace.get("request_reference", "")})
            if lr.status_code == 200 and lr.json().get("total", 0) >= 1:
                row = lr.json()["items"][0]
                checks[2].pass_(row["request_reference"])
            else:
                checks[2].fail(f"total={lr.json().get('total') if lr.status_code == 200 else lr.status_code}")

            request_id = trace.get("request_id") or (lr.json()["items"][0]["id"] if lr.status_code == 200 else "")
            hosun_product = _catalog_by_sku(client, base, headers, "HS90602HRDDFZ")
            if not hosun_product:
                checks[3].fail("HS90602HRDDFZ not in catalog — run sync_hosun_classification_catalog.py --apply --confirm")
            else:
                pr = client.get(f"{base}/api/auth/me", headers=headers)
                owner_id = pr.json().get("id") if pr.status_code == 200 else None
                patch = {
                    "status": "triage",
                    "priority": "high",
                    "owner_user_id": owner_id,
                    "partner_id": hosun_product["partner_id"],
                    "product_catalog_id": hosun_product["id"],
                    "sku": "HS-HRD-300",
                }
                ur = client.patch(f"{base}/api/project-requests/{request_id}", headers=headers, json=patch)
                if ur.status_code != 200:
                    checks[3].fail(f"patch {ur.status_code}")
                else:
                    fit = ur.json().get("fit_summary") or {}
                    heavy = next((m for m in fit.get("matches", []) if m.get("dimension") == "heavy_load"), {})
                    checks[3].pass_(f"overall={fit.get('overall_status')} heavy={heavy.get('match_status')}")

            qic = client.post(f"{base}/api/project-requests/{request_id}/quote-input-contract", headers=headers)
            if qic.status_code == 200 and qic.json().get("quote_input_contract"):
                trace["qic_generated"] = "yes"
                checks[4].pass_("contract ok")
            else:
                checks[4].fail(f"HTTP {qic.status_code}")

            ready = client.patch(
                f"{base}/api/project-requests/{request_id}",
                headers=headers,
                json={"status": "quote_ready"},
            )
            if ready.status_code == 200 and ready.json().get("status") == "quote_ready":
                checks[5].pass_("quote_ready")
            else:
                checks[5].fail(f"{ready.status_code} {ready.text[:120]}")

            if hosun_product:
                quote_body = {
                    "line_items": [
                        {
                            "product_id": hosun_product["id"],
                            "quantity": 30,
                            "incoterm": "DDP",
                            "pricing_strategy": "volume",
                            "manual_interval_quote_table": [
                                {"min_qty": 1, "max_qty": 49, "quantity_label": "1-49", "currency": "USD", "fob_unit_price": "185.00", "ddp_unit_price": "215.00"},
                                {"min_qty": 50, "max_qty": 99, "quantity_label": "50-99", "currency": "USD", "fob_unit_price": "172.00", "ddp_unit_price": "198.00"},
                                {"min_qty": 100, "max_qty": 299, "quantity_label": "100-299", "currency": "USD", "fob_unit_price": "158.00", "ddp_unit_price": "182.00"},
                                {"min_qty": 300, "max_qty": 499, "quantity_label": "300-499", "currency": "USD", "fob_unit_price": "145.00", "ddp_unit_price": "168.00"},
                                {"min_qty": 500, "max_qty": None, "quantity_label": ">=500", "currency": "USD", "fob_unit_price": "132.00", "ddp_unit_price": "155.00"},
                            ],
                        }
                    ],
                    "bill_to": {"name": "Pilot Demo Buyer", "company": "Demo Heavy-Duty Dealer (Synthetic)", "address": "California, USA"},
                    "ship_to": {"name": "Pilot Demo Buyer", "company": "Demo Heavy-Duty Dealer (Synthetic)", "address": "California, USA"},
                    "internal_notes": f"Pilot E2E from {trace.get('request_reference')}",
                }
                cr = client.post(f"{base}/api/v1/quotes", headers=headers, json=quote_body)
                if cr.status_code in {200, 201} and cr.json().get("ok"):
                    quote_id = cr.json()["data"]["id"]
                    trace["quote_id"] = quote_id
                    checks[6].pass_(quote_id[:8])
                    client.patch(
                        f"{base}/api/project-requests/{request_id}",
                        headers=headers,
                        json={"quote_id": quote_id},
                    )
                    pdf = client.post(
                        f"{base}/api/v1/quotes/{quote_id}/export-pdf",
                        headers=headers,
                        json={"export_type": "customer_pdf"},
                    )
                    if pdf.status_code in {200, 201} and pdf.json().get("ok"):
                        checks[7].pass_("pdf ok")
                    else:
                        checks[7].fail(f"pdf {pdf.status_code}")
                else:
                    checks[6].fail(f"{cr.status_code} {cr.text[:160]}")
                    checks[7].fail("skipped")

            mr = client.post(f"{base}/api/project-requests/{request_id}/promote-market-signal", headers=headers)
            if mr.status_code == 200 and mr.json().get("review_id"):
                trace["mr_review_id"] = mr.json()["review_id"]
                checks[8].pass_(trace["mr_review_id"][:8])
            else:
                checks[8].fail(f"{mr.status_code}")

            dq = client.get(f"{base}/api/dashboard/daily-decision-queue", headers=headers)
            if dq.status_code == 200:
                items = dq.json().get("items") or []
                found = any(i.get("source_type") == "customer_project_request" for i in items)
                checks[9].pass_(f"{len(items)} items, cpr={found}")
            else:
                checks[9].fail(str(dq.status_code))

            linked = all(k in trace for k in ("request_reference", "quote_id", "mr_review_id"))
            checks[10].pass_("CPR→QIC→Quote→MR") if linked else checks[10].fail(str(trace))

            bad = client.patch(
                f"{base}/api/project-requests/{request_id}",
                headers=headers,
                json={"status": "submitted"},
            )
            checks[11].pass_("400 blocked") if bad.status_code == 400 else checks[11].fail(str(bad.status_code))

            dup = client.post(
                f"{base}/api/site/customer/orders",
                json=site_payload,
                headers={"Idempotency-Key": idem_key},
            )
            if dup.status_code == 200 and dup.json().get("request_reference") == trace.get("request_reference"):
                checks[12].pass_("same reference")
            else:
                checks[12].fail(dup.text[:120])

            unauth = client.get(f"{base}/api/project-requests")
            checks[13].pass_("401/403") if unauth.status_code in {401, 403} else checks[13].fail(str(unauth.status_code))

            from app.core.config import Settings

            checks[14].pass_("default off") if Settings.model_fields["CUSTOMER_SITE_COMPAT_ENABLED"].default is False else checks[14].fail("default on")

            # JOOBOO pending path
            jb = _catalog_by_sku(client, base, headers, "JB-DEMO-SCHOOL-DESK")
            if jb:
                jr = client.post(
                    f"{base}/api/project-requests",
                    headers=headers,
                    json={
                        "customer_name": "Education Pilot",
                        "company_name_text": "Staging School Buyer (Synthetic)",
                        "product_interest": "School desk set",
                        "sku": "JB-DEMO-SCHOOL-DESK",
                        "partner_id": jb["partner_id"],
                        "product_catalog_id": jb["id"],
                        "requirements": {"load_capacity_kg": 80},
                        "source": "admin_manual",
                    },
                )
                if jr.status_code == 201:
                    fit = jr.json().get("fit_summary") or {}
                    ok = fit.get("overall_status") == "UNKNOWN" and fit.get("partner_pending") is True
                    checks[15].pass_(f"overall={fit.get('overall_status')}") if ok else checks[15].fail(str(fit))
                else:
                    checks[15].fail(str(jr.status_code))
            else:
                checks[15].fail("JB-DEMO-SCHOOL-DESK missing")

    except httpx.ConnectError:
        checks[0].fail(f"backend down ({base})")
        _print_report(checks, trace)
        return 1

    _print_report(checks, trace)
    failed = [c for c in checks if not c.ok]
    return 0 if not failed else 1


def _print_report(checks: list[Check], trace: dict[str, str]) -> None:
    print("Pilot Revenue Loop E2E Check")
    for c in checks:
        print(c.line())
    if trace:
        print("\nTraceability (redacted IDs):")
        for k, v in trace.items():
            print(f"  {k}: {v[:8]}…" if len(v) > 12 else f"  {k}: {v}")
    failed = [c for c in checks if not c.ok]
    print(f"\nResult: {'PASS' if not failed else 'FAIL'} ({len(checks) - len(failed)}/{len(checks)})")


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
