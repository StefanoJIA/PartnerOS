from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_staging_handoff_bundle_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_staging_handoff_bundle_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d8_staging_handoff_bundle_check_passes_for_repo_doc(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D8 Staging Handoff Bundle Check" in output
    assert "Result: PASS" in output


def test_d8_staging_handoff_bundle_check_flags_token_assignment(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "bundle.md"
    records = tmp_path.parent / "records"
    records.mkdir(exist_ok=True)
    for link in module.REQUIRED_LINKS:
        if link.startswith("../records/"):
            (records / Path(link).name).write_text("redacted\n", encoding="utf-8")
    doc.write_text(
        "\n".join(
            [
                *module.REQUIRED_LINKS,
                *module.REQUIRED_COMMANDS,
                *module.REQUIRED_MARKERS,
                "SERVICE_PORTAL_PARTNEROS_TOKEN=secret",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "bundle avoids secret-like markers" in output
    assert "SERVICE_PORTAL_PARTNEROS_TOKEN=" in output


def test_d8_staging_handoff_bundle_check_flags_authorization_bearer(
    monkeypatch, tmp_path, capsys
):
    module = _load_module()
    doc = tmp_path / "bundle.md"
    records = tmp_path.parent / "records"
    records.mkdir(exist_ok=True)
    for link in module.REQUIRED_LINKS:
        if link.startswith("../records/"):
            (records / Path(link).name).write_text("redacted\n", encoding="utf-8")
    doc.write_text(
        "\n".join(
            [
                *module.REQUIRED_LINKS,
                *module.REQUIRED_COMMANDS,
                *module.REQUIRED_MARKERS,
                "Authorization: Bearer actual-secret-value",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "bundle avoids secret-like markers" in output
    assert "bundle.md" in output


def test_d8_staging_handoff_bundle_check_flags_missing_committed_record(
    monkeypatch, tmp_path, capsys
):
    module = _load_module()
    phase3 = tmp_path / "docs" / "phase3"
    phase3.mkdir(parents=True)
    doc = phase3 / "bundle.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_LINKS, *module.REQUIRED_COMMANDS, *module.REQUIRED_MARKERS]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "bundle committed record links exist" in output
    assert "../records/d8_staging_operator_handoff_20260531.md" in output
