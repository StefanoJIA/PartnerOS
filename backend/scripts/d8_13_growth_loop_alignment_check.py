"""D8.13 competitor alignment and growth operations loop check."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8014").rstrip("/")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://127.0.0.1:5173").rstrip("/")


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


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _contains_all(text: str, markers: tuple[str, ...]) -> tuple[bool, str]:
    missing = [marker for marker in markers if marker not in text]
    return not missing, ", ".join(missing)


def _post_json(path: str, payload: dict[str, object], token: str | None = None) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{BACKEND_BASE_URL}{path}", data=data, headers=headers, method="POST")
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_json(path: str, token: str | None = None) -> dict[str, object]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{BACKEND_BASE_URL}{path}", headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_text(url: str) -> str:
    request = Request(url)
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def _run_script(name: str) -> tuple[bool, str]:
    env = os.environ.copy()
    env.setdefault("BACKEND_BASE_URL", BACKEND_BASE_URL)
    result = subprocess.run(
        [sys.executable, f"scripts/{name}"],
        cwd=ROOT / "backend",
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=180,
    )
    tail = "\n".join(result.stdout.strip().splitlines()[-4:])
    return result.returncode == 0, tail


def main() -> int:
    checks = [
        Check("growth operations route and navigation entry"),
        Check("campaign planning MVP"),
        Check("customer segment MVP"),
        Check("manual outreach sequence MVP"),
        Check("campaign quote/order attribution"),
        Check("feedback shipment market response loop"),
        Check("multi-partner focus markers"),
        Check("Chinese-first UI copy"),
        Check("navigation group count <= 8"),
        Check("handoff-only and no forbidden automation"),
        Check("runtime growth API safety"),
        Check("D8.10/D8.11/D8.12 checks still pass"),
    ]

    router = _read("frontend/src/router/index.ts")
    layout = _read("frontend/src/layouts/MainLayout.vue")
    page = _read("frontend/src/pages/growth/GrowthOperationsPage.vue")
    api = _read("frontend/src/api/growthOperations.ts")
    service = _read("backend/app/services/growth_operations.py")
    route = _read("backend/app/api/v1/routes/growth_operations.py")
    docs = "\n".join(
        [
            _read("docs/strategy/competitor_capability_matrix.md"),
            _read("docs/phase3/d8_13_competitor_alignment_growth_loop.md"),
        ]
    )

    ok, missing = _contains_all(
        "\n".join([router, layout, page, api, route]),
        ("growth-operations", "增长运营", "/v1/growth/operations-console"),
    )
    if ok:
        try:
            html = _get_text(f"{FRONTEND_BASE_URL}/growth-operations")
            checks[0].pass_("route, API client, nav entry, and frontend URL exist") if "id=\"app\"" in html else checks[0].fail("frontend route did not return app shell")
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            checks[0].fail(f"frontend growth route failed: {exc.__class__.__name__}")
    else:
        checks[0].fail(missing)

    ok, missing = _contains_all(
        "\n".join([service, page]),
        (
            "partner_focus",
            "product_focus",
            "target_segment",
            "goal",
            "status",
            "next_action",
            "Campaign / 营销活动规划视图",
        ),
    )
    checks[1].pass_("campaign planning fields present") if ok else checks[1].fail(missing)

    ok, missing = _contains_all("\n".join([service, page]), ("segments", "company_count", "lead_count", "contact_count", "轻量客户分群"))
    checks[2].pass_("segment aggregation present") if ok else checks[2].fail(missing)

    ok, missing = _contains_all(
        "\n".join([service, page]),
        ("outreach_sequences", "drafts", "follow_up_task", "manual_event_options", "记录人工动作", "postLeadIntelligenceTouchpoint"),
    )
    checks[3].pass_("manual draft and touchpoint record path present") if ok else checks[3].fail(missing)

    ok, missing = _contains_all(
        "\n".join([service, page]),
        ("attribution", "quote_count", "order_count", "Campaign / 营销活动到报价和订单的归因"),
    )
    checks[4].pass_("quote/order attribution present") if ok else checks[4].fail(missing)

    ok, missing = _contains_all(
        "\n".join([service, page]),
        ("feedback_loop", "feedback_ticket_count", "shipment_risk_count", "market_signal_count", "反馈 / 物流风险 / 市场信号回流"),
    )
    checks[5].pass_("feedback/shipment/market loop present") if ok else checks[5].fail(missing)

    ok, missing = _contains_all(
        "\n".join([service, page, docs]),
        (
            "HOSUN",
            "JOOBOO",
            "Future Partner",
            "lifting systems",
            "desk frames",
            "desk legs",
            "lifting columns",
            "education furniture",
            "project furniture",
        ),
    )
    checks[6].pass_("HOSUN/JOOBOO/future partner markers present") if ok else checks[6].fail(missing)

    ok, missing = _contains_all(
        page,
        ("增长运营闭环", "销售易能力适配", "客户分群", "手动外联序列", "归因", "安全边界"),
    )
    checks[7].pass_("main visible copy is Chinese") if ok else checks[7].fail(missing)

    group_count = layout.count("key:")
    checks[8].pass_(f"{group_count} group(s)") if group_count <= 8 else checks[8].fail(f"{group_count} group(s)")

    boundary_text = "\n".join([service, route, page, docs])
    unsafe_markers = (
        "Status: STAGING_VALIDATED",
        "D9 is ready",
        "email_sent\": True",
        "linkedin_sent\": True",
        "quote_status_changed\": True",
        "order_status_changed\": True",
    )
    found = [marker for marker in unsafe_markers if marker in boundary_text]
    if "READY_FOR_STAGING_HANDOFF" in boundary_text and not found:
        checks[9].pass_("READY_FOR_STAGING_HANDOFF and no unsafe automation claims")
    else:
        checks[9].fail(", ".join(found) or "READY_FOR_STAGING_HANDOFF missing")

    try:
        login = _post_json("/api/auth/login", {"email": "admin@example.com", "password": "admin123"})
        token = str(login["access_token"])
        envelope = _get_json("/api/v1/growth/operations-console", token)
        data = envelope["data"]  # type: ignore[index]
        safety = data["safety"]  # type: ignore[index]
        runtime_ok = (
            envelope.get("ok") is True
            and len(data["campaigns"]) >= 3  # type: ignore[index]
            and len(data["outreach_sequences"]) >= 3  # type: ignore[index]
            and len(data["attribution"]) >= 3  # type: ignore[index]
            and len(data["feedback_loop"]) >= 3  # type: ignore[index]
            and safety["email_sent"] is False  # type: ignore[index]
            and safety["linkedin_sent"] is False  # type: ignore[index]
            and safety["quote_status_changed"] is False  # type: ignore[index]
            and safety["order_status_changed"] is False  # type: ignore[index]
            and safety["staging_validated"] is False  # type: ignore[index]
        )
        checks[10].pass_("runtime growth API returns safe loop data") if runtime_ok else checks[10].fail("runtime data incomplete or unsafe")
    except (KeyError, TypeError, HTTPError, URLError, TimeoutError, ValueError) as exc:
        checks[10].fail(f"growth API request failed: {exc.__class__.__name__}")

    failed_subchecks = []
    for script in (
        "d8_10_navigation_localization_check.py",
        "d8_11_chinese_operating_language_check.py",
        "d8_12_release_candidate_check.py",
    ):
        ok, detail = _run_script(script)
        if not ok:
            failed_subchecks.append(f"{script}: {detail}")
    checks[11].pass_("D8 predecessor checks pass") if not failed_subchecks else checks[11].fail("; ".join(failed_subchecks))

    print("D8.13 Growth Loop Alignment Check")
    print(f"BACKEND_BASE_URL={BACKEND_BASE_URL}")
    print(f"FRONTEND_BASE_URL={FRONTEND_BASE_URL}")
    for check in checks:
        print(check.line())
    failed = [check for check in checks if not check.ok]
    print("Result: " + ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
