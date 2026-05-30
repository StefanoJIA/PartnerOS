from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "deployment_readiness_checklist_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("deployment_readiness_checklist_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_deployment_readiness_checklist_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Deployment Readiness Checklist Check" in output
    assert "Result: PASS" in output


def test_deployment_readiness_checklist_flags_missing_gate_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "deployment_readiness_checklist.md"
    doc.write_text("READY_FOR_STAGING_HANDOFF\n", encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "deployment readiness checklist matches D8/D9 stage gates" in output


def test_deployment_readiness_checklist_flags_stale_d5_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "deployment_readiness_checklist.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "D5.2 Internal MVP"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "deployment readiness checklist avoids stale D5/D6 deploy gates" in output


def test_deployment_readiness_checklist_flags_secret_like_assignment(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "deployment_readiness_checklist.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, 'SERVICE_PORTAL_PARTNEROS_TOKEN="actual-secret-value"']),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "deployment readiness checklist is redacted" in output
