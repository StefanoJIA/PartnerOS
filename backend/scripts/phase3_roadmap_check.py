"""Validate Phase 3 roadmap consistency across D7-D9 planning artifacts."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROADMAP = REPO_ROOT / "docs" / "phase3" / "phase3_roadmap.md"

REQUIRED_STAGES = (
    "D7.1",
    "D7.2",
    "D7.3",
    "D7.4",
    "D7.5",
    "D7.5.1",
    "D7.6",
    "D7.7",
    "D7.8",
    "D7.9",
    "D8.1",
    "D8.2",
    "D8.3",
    "D8.4",
    "D8.5",
    "D8",
    "D9",
)
REQUIRED_DOC_LINKS = (
    "d7_1_order_schema_api_design_review.md",
    "d7_2_order_crud_mvp.md",
    "d7_6_shipment_tracking_foundation.md",
    "d7_7_customer_portal_bridge_api.md",
    "d7_9_resource_center.md",
    "d8_delivery_stage_goal_matrix.md",
    "d8_readiness_audit.md",
    "d8_staging_execution_pack.md",
    "d8_staging_handoff_bundle.md",
    "d8_staging_access_request.md",
    "d8_staging_gap_triage.md",
    "d8_production_coordination_plan.md",
    "d9_post_launch_operating_loop.md",
    "d9_operating_records_policy.md",
    "project_execution_chain_gate.md",
    "project_execution_acceptance_audit.md",
    "ie_auto_project_plan.md",
)
REQUIRED_DOCS = tuple(f"docs/phase3/{link}" for link in REQUIRED_DOC_LINKS)
REQUIRED_SAFETY_MARKERS = (
    "No auto-send",
    "No auto production / shipment / payment",
    "Customer portal UI replacement",
    "Inventory reservation system",
    "PDF parsing for order creation",
)
REQUIRED_GRAPH_MARKERS = (
    "D6 --> D71",
    "D79 --> D81",
    "D85 --> D8",
    "D8 --> D9",
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


def _roadmap_text() -> str:
    return ROADMAP.read_text(encoding="utf-8") if ROADMAP.exists() else ""


def _missing_files(paths: tuple[str, ...]) -> list[str]:
    return [path for path in paths if not (REPO_ROOT / path).exists()]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    checks = [
        Check("phase3 roadmap exists"),
        Check("roadmap contains D7-D9 stages"),
        Check("roadmap related document links exist"),
        Check("linked phase3 docs exist"),
        Check("roadmap dependency graph is continuous"),
        Check("roadmap preserves safety boundaries"),
    ]

    text = _roadmap_text()
    checks[0].pass_(_display_path(ROADMAP)) if text else checks[0].fail(_display_path(ROADMAP))

    missing_stages = [stage for stage in REQUIRED_STAGES if f"**{stage}**" not in text]
    checks[1].pass_(f"{len(REQUIRED_STAGES)} stages") if not missing_stages else checks[1].fail(
        ", ".join(missing_stages)
    )

    missing_links = [link for link in REQUIRED_DOC_LINKS if link not in text]
    checks[2].pass_(f"{len(REQUIRED_DOC_LINKS)} links") if not missing_links else checks[2].fail(
        ", ".join(missing_links)
    )

    missing_docs = _missing_files(REQUIRED_DOCS)
    checks[3].pass_(f"{len(REQUIRED_DOCS)} docs") if not missing_docs else checks[3].fail(", ".join(missing_docs))

    missing_graph = [marker for marker in REQUIRED_GRAPH_MARKERS if marker not in text]
    checks[4].pass_("D6 through D9") if not missing_graph else checks[4].fail(", ".join(missing_graph))

    missing_safety = [marker for marker in REQUIRED_SAFETY_MARKERS if marker not in text]
    checks[5].pass_("manual-action boundaries") if not missing_safety else checks[5].fail(
        ", ".join(missing_safety)
    )

    print("Phase 3 Roadmap Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
