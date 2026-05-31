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


def _valid_record_body(module) -> str:
    return "\n".join(
        [
            "# D9 Operating Review - 2026-05-30",
            "",
            "Loop: Operating health",
            "Evidence source: redacted summary only",
            "Owner: TBD",
            "Status: open",
            "",
            *module.RECORD_REQUIRED_MARKERS,
        ]
    )


def test_d9_operating_records_check_passes_without_d9_records(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)

    assert module.main() == 0
    assert "Result: PASS" in capsys.readouterr().out


def test_d9_operating_records_check_accepts_aggregate_review_record(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_production_go_no_go_20260530.md").write_text("redacted go/no-go\n", encoding="utf-8")
    (tmp_path / "d9_operating_review_20260530.md").write_text(
        _valid_record_body(module) + "\n",
        encoding="utf-8",
    )

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D9 operating record names are canonical" in output
    assert "Result: PASS" in output


def test_d9_operating_records_check_accepts_template_safety_statement(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_production_go_no_go_20260530.md").write_text("redacted go/no-go\n", encoding="utf-8")
    (tmp_path / "d9_operating_review_20260530.md").write_text(
        _valid_record_body(module)
        + "\n",
        encoding="utf-8",
    )

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D9 operating records are redacted" in output
    assert "Result: PASS" in output


def test_d9_operating_records_check_rejects_d9_record_without_d8_go_no_go(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d9_operating_review_20260530.md").write_text(
        _valid_record_body(module) + "\n",
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D9 operating records are gated by D8 Go / No-Go" in output
    assert "d8_production_go_no_go_YYYYMMDD.md" in output


def test_d9_operating_records_check_rejects_missing_safety_markers(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_production_go_no_go_20260530.md").write_text("redacted go/no-go\n", encoding="utf-8")
    (tmp_path / "d9_operating_review_20260530.md").write_text("redacted summary\n", encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D9 operating records include safety markers" in output
    assert "d9_operating_review_20260530.md:missing" in output


def test_d9_operating_records_check_rejects_missing_owner(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_production_go_no_go_20260530.md").write_text("redacted go/no-go\n", encoding="utf-8")
    (tmp_path / "d9_operating_review_20260530.md").write_text(
        _valid_record_body(module).replace("Owner: TBD\n", ""),
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D9 operating records have owner and status" in output
    assert "missing Owner" in output


def test_d9_operating_records_check_rejects_invalid_status(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_production_go_no_go_20260530.md").write_text("redacted go/no-go\n", encoding="utf-8")
    (tmp_path / "d9_operating_review_20260530.md").write_text(
        _valid_record_body(module).replace("Status: open", "Status: investigating"),
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D9 operating records have owner and status" in output
    assert "invalid Status investigating" in output


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
