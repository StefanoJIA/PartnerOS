from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d9_operating_records_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d9_operating_records_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d9_operating_records_check_passes_without_d9_records(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)

    assert module.main() == 0
    assert "Result: PASS" in capsys.readouterr().out


def test_d9_operating_records_check_rejects_noncanonical_name(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d9_notes.md").write_text("redacted\n", encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D9 operating record names are canonical" in output
    assert "d9_notes.md" in output


def test_d9_operating_records_check_rejects_token_assignment(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d9_operating_health_20260530.md").write_text(
        '$env:SERVICE_PORTAL_PARTNEROS_TOKEN="actual-secret-value"\n',
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D9 operating records are redacted" in output
    assert "d9_operating_health_20260530.md:1" in output


def test_d9_operating_records_check_rejects_generic_private_key(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d9_market_response_20260530.md").write_text(
        "SERVICE_PORTAL_PRIVATE_KEY=actual-secret-value\n",
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D9 operating records are redacted" in output
    assert "d9_market_response_20260530.md:1" in output
