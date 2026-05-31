from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_integration_hardening_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_integration_hardening_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_integration_hardening_requires_production_runbook_markers():
    module = _load_module()

    assert "docs/phase3/d8_production_coordination_runbook.md" in module.REQUIRED_DOCS
    assert "python scripts/d8_production_coordination_runbook_check.py" in module.REQUIRED_INTEGRATION_DOC_MARKERS
    assert "Go / No-Go handoff" in module.REQUIRED_INTEGRATION_DOC_MARKERS


def test_integration_hardening_doc_contains_required_markers():
    module = _load_module()
    text = module._integration_doc_text()

    missing = [marker for marker in module.REQUIRED_INTEGRATION_DOC_MARKERS if marker not in text]
    assert missing == []


def test_integration_hardening_safe_json_tolerates_non_json_response():
    module = _load_module()
    response = SimpleNamespace(json=lambda: (_ for _ in ()).throw(ValueError("not json")))

    assert module._safe_json(response) == {}


def test_integration_hardening_finish_reports_fail(capsys):
    module = _load_module()
    check = module.Check("integration")
    check.fail("HTTP 500")

    assert module._finish([check]) == 1
    output = capsys.readouterr().out
    assert "D8 Integration Hardening Check" in output
    assert "[FAIL] integration (HTTP 500)" in output
    assert "Result: FAIL" in output
