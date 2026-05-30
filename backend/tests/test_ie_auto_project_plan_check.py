from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ie_auto_project_plan_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("ie_auto_project_plan_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ie_auto_project_plan_check_passes_for_current_plan(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "current state mapping reaches D9" in output
    assert "Result: PASS" in output


def test_ie_auto_project_plan_check_fails_without_partner_neutrality(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "PLAN_DOC", tmp_path / "ie_auto_project_plan.md")
    module.PLAN_DOC.write_text("intelliOffice / PartnerOS\nservice.intelli-opus.com\n", encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "product positioning and partner neutrality" in output
    assert "must not hard-code brand privilege" in output


def test_ie_auto_project_plan_check_fails_without_strict_staging_next_brief(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "PLAN_DOC", tmp_path / "ie_auto_project_plan.md")
    text = "\n".join(
        (
            *module.REQUIRED_POSITIONING,
            *module.REQUIRED_LIFECYCLE,
            *module.REQUIRED_STATE_ROWS,
            *module.REQUIRED_ORDER_MARKERS,
            *module.REQUIRED_SAFETY,
        )
    )
    module.PLAN_DOC.write_text(text + "\n", encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "immediate next brief remains strict staging" in output
    assert "Strict staging evidence run" in output
