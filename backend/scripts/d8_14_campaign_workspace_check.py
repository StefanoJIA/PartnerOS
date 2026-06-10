"""D8.14 campaign workspace MVP check."""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8014").rstrip("/")


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


def _request_json(path: str, method: str = "GET", payload: dict[str, object] | None = None, token: str | None = None) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{BACKEND_BASE_URL}{path}", data=data, headers=headers, method=method)
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    checks = [
        Check("migration and models"),
        Check("growth campaign API routes"),
        Check("Chinese campaign workspace UI"),
        Check("docs and handoff boundary"),
        Check("runtime creates HOSUN and JOOBOO campaigns"),
        Check("runtime task create and manual status update"),
        Check("operations console remains available"),
        Check("no forbidden automation or staging claim"),
    ]

    migration = _read("backend/alembic/versions/0018_growth_campaign_workspace.py")
    models = _read("backend/app/models/growth.py")
    schemas = _read("backend/app/schemas/growth.py")
    route = _read("backend/app/api/v1/routes/growth_operations.py")
    api = _read("frontend/src/api/growthOperations.ts")
    page = _read("frontend/src/pages/growth/GrowthOperationsPage.vue")
    docs = _read("docs/phase3/d8_14_campaign_workspace_mvp.md")

    ok, missing = _contains_all(
        "\n".join([migration, models, schemas]),
        ("growth_campaigns", "growth_campaign_tasks", "partner_focus", "product_focus", "manual_sent", "quote_requested"),
    )
    checks[0].pass_("tables, model, and statuses present") if ok else checks[0].fail(missing)

    ok, missing = _contains_all(
        "\n".join([route, api]),
        (
            "/campaigns",
            "/campaigns/{campaign_id}",
            "/campaigns/{campaign_id}/tasks",
            "/tasks/{task_id}",
            "createGrowthCampaign",
            "updateGrowthCampaignTask",
        ),
    )
    checks[1].pass_("CRUD endpoints and API client present") if ok else checks[1].fail(missing)

    ok, missing = _contains_all(
        page,
        ("Campaign 工作台", "保存 Campaign", "创建人工外联任务", "HOSUN", "JOOBOO", "不自动发送"),
    )
    checks[2].pass_("workspace UI is Chinese and multi-partner") if ok else checks[2].fail(missing)

    ok, missing = _contains_all(
        docs,
        ("D8.14", "READY_FOR_STAGING_HANDOFF", "HOSUN", "JOOBOO", "不自动发送", "不进入 D9"),
    )
    checks[3].pass_("D8.14 docs and boundary present") if ok else checks[3].fail(missing)

    try:
        login = _request_json("/api/auth/login", "POST", {"email": "admin@example.com", "password": "admin123"})
        token = str(login["access_token"])
        suffix = str(int(time.time()))
        hosun = _request_json(
            "/api/v1/growth/campaigns",
            "POST",
            {
                "name": f"D8.14 HOSUN lifting systems demo {suffix}",
                "partner_focus": "HOSUN",
                "product_focus": ["lifting systems", "desk frames", "desk legs", "lifting columns", "heavy-duty supply"],
                "target_segment": "升降办公与项目制采购客户",
                "goal": "把升降系统兴趣推进到人工外联、报价请求和订单交付复盘。",
                "status": "planned",
                "owner": "D8.14 check",
                "next_action": "创建人工外联任务并记录状态。",
                "notes": "PartnerOS 多 partner campaign workspace runtime check.",
            },
            token,
        )
        jooboo = _request_json(
            "/api/v1/growth/campaigns",
            "POST",
            {
                "name": f"D8.14 JOOBOO education furniture demo {suffix}",
                "partner_focus": "JOOBOO",
                "product_focus": ["education furniture", "project furniture", "classroom furniture"],
                "target_segment": "教育空间与学校项目采购客户",
                "goal": "把教育家具项目兴趣推进到需求确认和项目报价。",
                "status": "planned",
                "owner": "D8.14 check",
                "next_action": "创建人工外联任务并记录状态。",
                "notes": "JOOBOO is equal to HOSUN in the demo loop.",
            },
            token,
        )
        hosun_data = hosun["data"]  # type: ignore[index]
        jooboo_data = jooboo["data"]  # type: ignore[index]
        hosun_id = hosun_data["campaign"]["id"]  # type: ignore[index]
        jooboo_id = jooboo_data["campaign"]["id"]  # type: ignore[index]
        list_data = _request_json("/api/v1/growth/campaigns", token=token)["data"]  # type: ignore[index]
        runtime_ok = (
            hosun_data["campaign"]["partner_focus"] == "HOSUN"  # type: ignore[index]
            and jooboo_data["campaign"]["partner_focus"] == "JOOBOO"  # type: ignore[index]
            and len(list_data["campaigns"]) >= 2  # type: ignore[index]
            and hosun_data["safety"]["email_sent"] is False  # type: ignore[index]
            and jooboo_data["safety"]["order_status_changed"] is False  # type: ignore[index]
        )
        checks[4].pass_("HOSUN and JOOBOO persisted") if runtime_ok else checks[4].fail("campaign runtime data incomplete")

        task_detail = _request_json(
            f"/api/v1/growth/campaigns/{hosun_id}/tasks",
            "POST",
            {"task_type": "manual_outreach", "language": "zh", "notes": "D8.14 manual task check"},
            token,
        )
        task = task_detail["data"]["tasks"][0]  # type: ignore[index]
        updated = _request_json(f"/api/v1/growth/tasks/{task['id']}", "PATCH", {"status": "manual_sent"}, token)
        updated_task = updated["data"]["tasks"][0]  # type: ignore[index]
        detail = _request_json(f"/api/v1/growth/campaigns/{jooboo_id}", token=token)
        task_ok = (
            task["draft_subject"]
            and updated_task["status"] == "manual_sent"
            and detail["data"]["campaign"]["partner_focus"] == "JOOBOO"  # type: ignore[index]
            and updated["data"]["safety"]["email_sent"] is False  # type: ignore[index]
        )
        checks[5].pass_("task draft saved and manual status updated") if task_ok else checks[5].fail("task workflow incomplete")

        console = _request_json("/api/v1/growth/operations-console", token=token)
        console_ok = console.get("ok") is True and console["data"]["safety"]["staging_validated"] is False  # type: ignore[index]
        checks[6].pass_("operations console OK") if console_ok else checks[6].fail("operations console unsafe or unavailable")
    except (HTTPError, URLError, TimeoutError, KeyError, TypeError, ValueError) as exc:
        checks[4].fail(f"runtime API failed: {exc.__class__.__name__}")
        checks[5].fail("skipped because runtime campaign create failed")
        checks[6].fail("skipped because runtime campaign create failed")

    boundary_text = "\n".join([migration, models, schemas, route, api, page, docs])
    unsafe_markers = (
        "Status: STAGING_VALIDATED",
        "D9 is ready",
        "email_sent\": True",
        "customer_notified\": True",
        "supplier_notified\": True",
        "quote_status_changed\": True",
        "order_status_changed\": True",
    )
    found = [marker for marker in unsafe_markers if marker in boundary_text]
    checks[7].pass_("READY_FOR_STAGING_HANDOFF only; no forbidden automation") if not found else checks[7].fail(", ".join(found))

    for check in checks:
        print(check.line())
    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.14 campaign workspace check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1
    print("\nD8.14 campaign workspace check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
