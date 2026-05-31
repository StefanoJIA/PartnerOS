from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "testing_summary_d5_2_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("testing_summary_d5_2_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_testing_summary_d5_2_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D5.2 Testing Summary Check" in output
    assert "Result: PASS" in output


def test_testing_summary_d5_2_check_flags_missing_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "testing_summary_d5_2.md"
    doc.write_text("D5.2 Testing Summary\n", encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D5.2 testing summary declares historical boundary" in output


def test_testing_summary_d5_2_check_flags_stale_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "testing_summary_d5_2.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "Default `BACKEND_BASE_URL=http://127.0.0.1:8000`"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D5.2 testing summary avoids stale or mojibake markers" in output


def test_testing_summary_d5_2_check_flags_secret_like_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "testing_summary_d5_2.md"
    doc.write_text("\n".join([*module.REQUIRED_MARKERS, "Bearer secret"]), encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D5.2 testing summary is redacted" in output
