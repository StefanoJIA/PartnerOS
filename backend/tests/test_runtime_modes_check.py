from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "runtime_modes_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("runtime_modes_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_modes_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Runtime Modes Check" in output
    assert "Result: PASS" in output


def test_runtime_modes_check_flags_missing_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "runtime_modes.md"
    doc.write_text("Runtime Modes\n", encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "runtime modes match current D8 state" in output


def test_runtime_modes_check_flags_stale_port_guidance(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "runtime_modes.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "default development examples may use `8010`"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "runtime modes avoid stale or mojibake markers" in output


def test_runtime_modes_check_flags_secret_like_assignment(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "runtime_modes.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, 'SERVICE_PORTAL_PARTNEROS_TOKEN="actual-secret-value"']),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "runtime modes are redacted" in output
