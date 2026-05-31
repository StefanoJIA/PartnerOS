from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d7_5_1_portal_integration_review_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d7_5_1_portal_integration_review_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d7_5_1_portal_integration_review_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D7.5.1 Portal Integration Review Check" in output
    assert "Result: PASS" in output


def test_d7_5_1_portal_integration_review_check_flags_stale_doc(monkeypatch, tmp_path, capsys):
    module = _load_module()
    stale_doc = tmp_path / "d7_5_1_existing_cloud_portal_integration_review.md"
    stale_doc.write_text(
        "\n".join(
            [
                "Product selection",
                "tracking",
                "feedback",
                "resource",
                "product_catalog",
                "customer_orders",
                "D7.6",
                "D7.7",
                "D7.8",
                "judgment retained as customer-facing",
                "0013_prod_milestones",
                "shipment_plans 仅设计",
                "roadmap 标注 Future",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", stale_doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "doc reflects current implemented bridge state" in output
    assert "stale or mojibake markers" in output
