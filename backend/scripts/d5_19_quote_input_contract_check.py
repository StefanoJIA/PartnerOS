"""D5.19 quote input contract UAT check."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import get_backend_base_url, log_backend_base_url

FORBIDDEN = (
    "guaranteed price",
    "in stock",
    "certified for",
    "delivery guaranteed",
    "lead time confirmed",
)

UAT_COMPANIES = (
    "SWC Office Furniture",
    "Yony's Office Furniture",
    "Jefferson Group",
    "Dancker",
    "Human Active Technology",
    "Campus Learning Furniture",
    "Metro Lab Workspace Co",
    "Transfer Enterprises",
    "Commercial Furniture Resource",
    "OCI Office Concepts",
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


def _company_map(client: httpx.Client, base: str, headers: dict[str, str]) -> dict[str, str]:
    r = client.get(f"{base}/api/companies", headers=headers, params={"limit": 300})
    if r.status_code != 200:
        return {}
    return {c["id"]: c.get("company_name", "") for c in r.json().get("items") or []}


def _safety_ok(payload: dict) -> bool:
    safety = payload.get("safety") or {}
    return (
        safety.get("quote_created") is False
        and safety.get("pricing_generated") is False
        and safety.get("inventory_promised") is False
        and safety.get("certification_promised") is False
        and safety.get("lead_time_promised") is False
        and safety.get("automatic_sending_enabled") is False
    )


def _no_forbidden(text: str) -> bool:
    lower = text.lower()
    return not any(p in lower for p in FORBIDDEN)


def main() -> int:
    base = log_backend_base_url()
    print("D5.19 Quote Input Contract Check")

    checks = [
        Check("contract API"),
        Check("route coverage"),
        Check("readiness categories"),
        Check("copyable JSON"),
        Check("no forbidden promises"),
        Check("no quote created"),
    ]

    try:
        with httpx.Client(timeout=60.0) as client:
            headers = _login(client, base)
            if not headers:
                for c in checks:
                    c.fail("login failed")
                for c in checks:
                    print(c.line())
                print("Result: FAIL")
                return 1

            board_r = client.get(f"{base}/api/a-domain/quote-input-contract-board", headers=headers)
            if board_r.status_code != 200:
                for c in checks:
                    c.fail(f"board HTTP {board_r.status_code}")
                for c in checks:
                    print(c.line())
                print("Result: FAIL")
                return 1

            board = board_r.json()
            rows = board.get("rows") or []
            if len(rows) < 5:
                checks[0].fail(f"only {len(rows)} board rows")
            else:
                checks[0].pass_(f"{len(rows)} leads on board")

            companies = _company_map(client, base, headers)
            leads_r = client.get(f"{base}/api/leads", headers=headers, params={"limit": 300})
            lead_items = leads_r.json().get("items") or [] if leads_r.status_code == 200 else []

            contracts: list[dict] = []
            for lead in lead_items:
                co_name = companies.get(lead.get("company_id"), "")
                if co_name not in UAT_COMPANIES and len(contracts) >= 8:
                    continue
                if co_name not in UAT_COMPANIES and len(contracts) >= 5 and not contracts:
                    pass
                lid = lead["id"]
                r = client.get(
                    f"{base}/api/a-domain/leads/{lid}/quote-input-contract",
                    headers=headers,
                )
                if r.status_code != 200:
                    continue
                body = r.json()
                body["_company_name"] = co_name
                contracts.append(body)
                if len(contracts) >= 10:
                    break

            if len(contracts) < 5:
                for row in rows[:8]:
                    lid = row["lead_id"]
                    r = client.get(
                        f"{base}/api/a-domain/leads/{lid}/quote-input-contract",
                        headers=headers,
                    )
                    if r.status_code == 200:
                        body = r.json()
                        body["_company_name"] = row.get("company_name", "")
                        if body not in contracts:
                            contracts.append(body)
                    if len(contracts) >= 5:
                        break

            if len(contracts) < 5:
                checks[0].fail(f"only {len(contracts)} contracts fetched")
            elif not checks[0].ok:
                checks[0].pass_(f"{len(contracts)} contracts fetched")

            routes_seen = set()
            readiness_seen = set()
            all_ok = True
            for c in contracts:
                routes_seen.update(c.get("recommended_partner_route") or [])
                readiness_seen.add(c.get("quote_module_readiness"))
                if not _safety_ok(c):
                    all_ok = False
                blob = json.dumps(c) + (c.get("copyable_handoff_summary") or "")
                if not _no_forbidden(blob):
                    all_ok = False
                try:
                    parsed = json.loads(c.get("copyable_json") or "{}")
                    if parsed.get("safety", {}).get("quote_created") is not False:
                        all_ok = False
                except json.JSONDecodeError:
                    all_ok = False
                known = (c.get("quote_input_fields") or {}).get("known_requirements") or {}
                notes_blob = " ".join(str(v) for v in known.values() if v)
                if "TBD guess" in notes_blob or "estimated" in notes_blob.lower():
                    all_ok = False

            route_ok = (
                "hosun_lifting_systems" in routes_seen
                or "project_supply" in routes_seen
                or "jooboo_education_furniture" in routes_seen
            ) and len(routes_seen) >= 1
            if route_ok:
                checks[1].pass_(f"routes: {', '.join(sorted(routes_seen)[:4])}")
            else:
                checks[1].fail(f"routes seen: {routes_seen}")

            if readiness_seen & {
                "ready_for_phase2_quote_draft",
                "needs_more_customer_info",
                "not_quote_ready",
            }:
                checks[2].pass_(f"categories: {', '.join(sorted(readiness_seen))}")
            else:
                checks[2].fail(f"readiness: {readiness_seen}")

            json_ok = all(
                json.loads(c.get("copyable_json") or "{}").get("lead_id") for c in contracts
            )
            if json_ok:
                checks[3].pass_(f"{len(contracts)} valid JSON payloads")
            else:
                checks[3].fail("invalid copyable_json")

            forbidden_ok = all(
                _no_forbidden(json.dumps(c) + (c.get("copyable_handoff_summary") or ""))
                for c in contracts
            )
            if forbidden_ok:
                checks[4].pass_()
            else:
                checks[4].fail("forbidden phrase detected")

            if all_ok and all(_safety_ok(c) for c in contracts):
                checks[5].pass_(f"{len(contracts)} contracts checked")
            else:
                checks[5].fail("safety flags or quote_created issue")

    except httpx.ConnectError:
        for c in checks:
            c.fail(f"cannot connect to {get_backend_base_url()}")
    except Exception as e:  # noqa: BLE001
        for c in checks:
            if not c.ok and not c.detail:
                c.fail(str(e)[:80])

    for c in checks:
        print(c.line())

    passed = all(c.ok for c in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
