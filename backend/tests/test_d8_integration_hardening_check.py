from __future__ import annotations

import importlib.util
from pathlib import Path


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
