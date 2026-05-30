from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_staging_operator_runbook_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_staging_operator_runbook_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d8_staging_operator_runbook_check_passes_for_repo_doc(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D8 Staging Operator Runbook Check" in output
    assert "Result: PASS" in output


def test_d8_staging_operator_runbook_check_fails_for_token_assignment(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "runbook.md"
    doc.write_text(
        "\n".join(
            [
                *module.REQUIRED_MARKERS,
                *module.REQUIRED_BOUNDARIES,
                "SERVICE_PORTAL_PARTNEROS_TOKEN=secret",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "runbook avoids secret-like markers" in output
    assert "SERVICE_PORTAL_PARTNEROS_TOKEN=<non-placeholder>" in output
