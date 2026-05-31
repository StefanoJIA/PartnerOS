from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_staging_gap_triage_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_staging_gap_triage_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d8_staging_gap_triage_check_passes_for_repo_doc(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D8 Staging Gap Triage Check" in output
    assert "Result: PASS" in output


def test_d8_staging_gap_triage_check_flags_bad_gap_register(monkeypatch, tmp_path, capsys):
    module = _load_module()
    records = tmp_path / "records"
    records.mkdir()
    (records / "d8_strict_staging_gaps_20260530.md").write_text(
        "| Check | Detail |\n|---|---|\n| token | raw response body |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "RECORDS_ROOT", records)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "existing D8 gap registers are triage-ready" in output
    assert "Recommended action" in output


def test_d8_staging_gap_triage_check_flags_noncanonical_gap_register_name(monkeypatch, tmp_path, capsys):
    module = _load_module()
    records = tmp_path / "records"
    records.mkdir()
    (records / "d8_strict_staging_gaps_latest.md").write_text(
        "| Check | Detail | Recommended action | Owner | Status |\n"
        "|---|---|---|---|---|\n"
        "| token | redacted | rotate token | TBD | open |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "RECORDS_ROOT", records)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "existing D8 gap registers are triage-ready" in output
    assert "d8_strict_staging_gaps_latest.md:noncanonical name" in output


def test_d8_staging_gap_triage_check_rejects_invalid_gap_status(monkeypatch, tmp_path, capsys):
    module = _load_module()
    records = tmp_path / "records"
    records.mkdir()
    (records / "d8_strict_staging_gaps_20260530.md").write_text(
        "| Check | Detail | Recommended action | Owner | Status |\n"
        "|---|---|---|---|---|\n"
        "| token | redacted | rotate token | TBD | investigating |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "RECORDS_ROOT", records)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "existing D8 gap registers are triage-ready" in output
    assert "invalid status investigating" in output


def test_d8_staging_gap_triage_check_flags_generic_api_key(monkeypatch, tmp_path, capsys):
    module = _load_module()
    records = tmp_path / "records"
    records.mkdir()
    (records / "d8_strict_staging_gaps_20260530.md").write_text(
        "| Check | Recommended action | Owner | Status |\n"
        "|---|---|---|---|\n"
        "| token | rotate SERVICE_PORTAL_API_KEY=actual-secret-value | TBD | open |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "RECORDS_ROOT", records)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "existing D8 gap registers are triage-ready" in output
    assert "d8_strict_staging_gaps_20260530.md:3" in output
