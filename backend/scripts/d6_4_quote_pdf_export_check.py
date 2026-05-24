"""D6.4 Quote PDF export smoke check."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import httpx
import pdfplumber

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import log_backend_base_url

FORBIDDEN = (
    "guaranteed price",
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
    r = client.post(f"{base}/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    if r.status_code != 200:
        return None
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def main() -> int:
    base = log_backend_base_url()
    print("D6.4 Quote PDF Export Check")
    checks = [
        Check("seeded product exists"),
        Check("create or use quote"),
        Check("export PDF"),
        Check("export_id present"),
        Check("file_size > 0"),
        Check("quote status unchanged"),
        Check("mark_sent not triggered"),
        Check("safety flags false"),
        Check("export list works"),
        Check("download works"),
        Check("no forbidden promise text"),
    ]
    quote_id = None
    status_before = None
    manual_sent_before = None
    export_id = None

    try:
        with httpx.Client(timeout=90.0) as client:
            headers = _login(client, base)
            if not headers:
                for c in checks:
                    c.fail("login failed")
                print("\n".join(c.line() for c in checks))
                print("Result: FAIL")
                return 1

            pr = client.get(f"{base}/api/v1/products?limit=5", headers=headers)
            if pr.status_code == 200 and (pr.json().get("data") or {}).get("total", 0) > 0:
                checks[0].pass_(f"{pr.json()['data']['total']} product(s)")
                product_id = pr.json()["data"]["items"][0]["id"]
            else:
                checks[0].fail(f"HTTP {pr.status_code}")
                product_id = None

            if not product_id:
                lr = client.get(f"{base}/api/v1/quotes?limit=1", headers=headers)
                if lr.status_code == 200 and lr.json()["data"]["items"]:
                    quote_id = lr.json()["data"]["items"][0]["id"]
                    checks[1].pass_(f"existing {quote_id[:8]}")
                else:
                    checks[1].fail("no product or quote")
            else:
                cr = client.post(
                    f"{base}/api/v1/quotes",
                    headers=headers,
                    json={
                        "line_items": [{"product_id": product_id, "quantity": 10, "incoterm": "FOB"}],
                        "bill_to": {"company": "PDF Smoke Co"},
                    },
                )
                if cr.status_code == 201:
                    quote_id = cr.json()["data"]["id"]
                    checks[1].pass_(quote_id[:8])
                else:
                    checks[1].fail(f"HTTP {cr.status_code}")

            if quote_id:
                gr = client.get(f"{base}/api/v1/quotes/{quote_id}", headers=headers)
                if gr.status_code == 200:
                    status_before = gr.json()["data"]["status"]
                    manual_sent_before = gr.json()["data"].get("manual_sent")
                else:
                    for c in checks[2:]:
                        c.fail("quote fetch failed")

                er = client.post(
                    f"{base}/api/v1/quotes/{quote_id}/export-pdf",
                    headers=headers,
                    json={"export_type": "customer_pdf"},
                )
                if er.status_code == 201:
                    checks[2].pass_()
                    payload = er.json()["data"]
                    export_id = payload.get("export_id")
                    size = payload.get("file_size_bytes") or 0
                    if export_id:
                        checks[3].pass_(export_id[:8])
                    else:
                        checks[3].fail("missing export_id")
                    if size > 0:
                        checks[4].pass_(f"{size} bytes")
                    else:
                        checks[4].fail("zero size")
                    safety = payload.get("safety") or {}
                    if all(
                        safety.get(k) is False
                        for k in (
                            "automatic_sending_enabled",
                            "inventory_promised",
                            "certification_promised",
                            "lead_time_promised",
                        )
                    ):
                        checks[7].pass_()
                    else:
                        checks[7].fail(str(safety))
                else:
                    checks[2].fail(f"HTTP {er.status_code} {er.text[:160]}")
                    for c in checks[3:8]:
                        c.fail("export failed")

                gr2 = client.get(f"{base}/api/v1/quotes/{quote_id}", headers=headers)
                if gr2.status_code == 200:
                    d = gr2.json()["data"]
                    if d["status"] == status_before:
                        checks[5].pass_(status_before)
                    else:
                        checks[5].fail(f"{status_before} -> {d['status']}")
                    if d.get("manual_sent") == manual_sent_before:
                        checks[6].pass_()
                    else:
                        checks[6].fail("manual_sent changed")
                else:
                    checks[5].fail("re-fetch failed")
                    checks[6].fail("re-fetch failed")

                lr = client.get(f"{base}/api/v1/quotes/{quote_id}/pdf-exports", headers=headers)
                if lr.status_code == 200 and lr.json()["data"]["items"]:
                    checks[8].pass_(f"{lr.json()['data']['total']} export(s)")
                else:
                    checks[8].fail(f"HTTP {lr.status_code}")

                if export_id:
                    dr = client.get(
                        f"{base}/api/v1/quotes/{quote_id}/pdf-exports/{export_id}/download",
                        headers=headers,
                    )
                    if dr.status_code == 200 and dr.headers.get("content-type", "").startswith("application/pdf"):
                        checks[9].pass_(f"{len(dr.content)} bytes")
                        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                            tmp.write(dr.content)
                            tmp_path = Path(tmp.name)
                        try:
                            text = ""
                            with pdfplumber.open(tmp_path) as pdf:
                                for page in pdf.pages:
                                    text += (page.extract_text() or "").lower()
                            if text and not any(p in text for p in FORBIDDEN):
                                checks[10].pass_()
                            elif not text:
                                checks[10].fail("empty pdf text")
                            else:
                                checks[10].fail("forbidden phrase in pdf")
                        finally:
                            tmp_path.unlink(missing_ok=True)
                    else:
                        checks[9].fail(f"HTTP {dr.status_code}")
                        checks[10].fail("download failed")
                else:
                    checks[9].fail("no export_id")
                    checks[10].fail("no export_id")

    except httpx.ConnectError:
        for c in checks:
            c.fail("backend unreachable")
        print("\n".join(c.line() for c in checks))
        print("Result: FAIL")
        return 1

    for c in checks:
        print(c.line())
    passed = all(c.ok for c in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
