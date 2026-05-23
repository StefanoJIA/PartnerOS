"""Verify D5.2.1 segment tuning on UAT leads."""

from __future__ import annotations

import httpx

BASE = "http://127.0.0.1:8000"
TARGETS = [
    "Healthcare Lab Workspace",
    "Contract Project Interiors",
    "New England Office Furniture Dealer",
]


def main() -> None:
    r = httpx.post(
        f"{BASE}/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    for name in TARGETS:
        lr = httpx.get(f"{BASE}/api/leads", headers=h, params={"limit": 50})
        for lead in lr.json().get("items", []):
            if name in lead.get("lead_name", ""):
                wf = httpx.get(
                    f"{BASE}/api/a-domain/leads/{lead['id']}/workflow",
                    headers=h,
                ).json()
                print(f"{name}: {wf.get('market_fit_segments')}")
                break


if __name__ == "__main__":
    main()
