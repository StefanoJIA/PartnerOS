from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_staging_operator_response_intake_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_staging_operator_response_intake_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d8_staging_operator_response_intake_check_passes_for_repo_doc(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D8 Staging Operator Response Intake Check" in output
    assert "Result: PASS" in output


def test_d8_staging_operator_response_intake_check_flags_token(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "intake.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "SERVICE_PORTAL_PARTNEROS_TOKEN=secret"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "SERVICE_PORTAL_PARTNEROS_TOKEN" in output


def test_d8_staging_operator_response_intake_check_flags_token_status_value(
    monkeypatch, tmp_path, capsys
):
    module = _load_module()
    doc = tmp_path / "intake.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "SERVICE_PORTAL_PARTNEROS_TOKEN: actual-secret-value"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "SERVICE_PORTAL_PARTNEROS_TOKEN:<non-private-status>" in output


def test_d8_staging_operator_response_intake_check_flags_backend_url_status_value(
    monkeypatch, tmp_path, capsys
):
    module = _load_module()
    doc = tmp_path / "intake.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "BACKEND_BASE_URL: https://private-staging.example.com"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "BACKEND_BASE_URL:<non-private-status>" in output


def test_d8_staging_operator_response_intake_check_flags_generic_api_key(
    monkeypatch, tmp_path, capsys
):
    module = _load_module()
    doc = tmp_path / "intake.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "SERVICE_PORTAL_API_KEY=actual-secret-value"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "intake.md" in output
