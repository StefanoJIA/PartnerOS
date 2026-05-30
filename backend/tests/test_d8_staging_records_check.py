from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_staging_records_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_staging_records_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d8_staging_records_check_passes_without_d8_records(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)

    assert module.main() == 0
    assert "Result: PASS" in capsys.readouterr().out


def test_d8_staging_records_check_rejects_noncanonical_name(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_staging_notes.md").write_text("redacted notes\n", encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D8 staging record names are canonical" in output
    assert "d8_staging_notes.md" in output


def test_d8_staging_records_check_rejects_undated_operator_handoff(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_staging_operator_handoff.md").write_text("redacted handoff\n", encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D8 staging record names are canonical" in output
    assert "d8_staging_operator_handoff.md" in output


def test_d8_staging_records_check_requires_gap_register_for_failed_evidence(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_strict_staging_evidence_20260530.json").write_text(
        """
{
  "result": "FAIL",
  "checks": [],
  "safety": {
    "token_redacted": true,
    "response_bodies_stored": false
  }
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "missing d8_strict_staging_gaps_20260530.md" in output


def test_d8_staging_records_check_rejects_bearer_token(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_staging_operator_handoff_20260530.md").write_text(
        "Authorization: Bearer actual-secret-value\n",
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D8 staging records are redacted" in output
    assert "d8_staging_operator_handoff_20260530.md:1" in output
