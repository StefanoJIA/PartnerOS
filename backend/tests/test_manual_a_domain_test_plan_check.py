from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "manual_a_domain_test_plan_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("manual_a_domain_test_plan_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_valid_docs(module, tmp_path, monkeypatch):
    doc = tmp_path / "manual_a_domain_test_plan.md"
    template_doc = tmp_path / "manual_test_record_template.md"
    import_template_doc = tmp_path / "lead_import_template.md"

    doc.write_text("\n".join(module.REQUIRED_MARKERS), encoding="utf-8")
    template_doc.write_text("\n".join(module.REQUIRED_TEMPLATE_MARKERS), encoding="utf-8")
    import_template_doc.write_text("\n".join(module.REQUIRED_IMPORT_TEMPLATE_MARKERS), encoding="utf-8")

    monkeypatch.setattr(module, "DOC", doc)
    monkeypatch.setattr(module, "TEMPLATE_DOC", template_doc)
    monkeypatch.setattr(module, "IMPORT_TEMPLATE_DOC", import_template_doc)
    return doc, template_doc, import_template_doc


def test_manual_a_domain_test_plan_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Manual A-Domain Test Plan Check" in output
    assert "Result: PASS" in output


def test_manual_a_domain_test_plan_check_flags_missing_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc, _template_doc, _import_template_doc = _write_valid_docs(module, tmp_path, monkeypatch)
    doc.write_text("Manual A-Domain Test Plan\n", encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "manual A-domain test plan matches current UAT contract" in output


def test_manual_a_domain_test_plan_check_flags_missing_template_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    _doc, template_doc, _import_template_doc = _write_valid_docs(module, tmp_path, monkeypatch)
    template_doc.write_text("Manual Test Record Template\n", encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "manual A-domain templates match current UAT contract" in output
    assert "Allowed Issue Type values" in output


def test_manual_a_domain_test_plan_check_flags_stale_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc, _template_doc, _import_template_doc = _write_valid_docs(module, tmp_path, monkeypatch)
    doc.write_text("\n".join([*module.REQUIRED_MARKERS, "D6 Productization | **Not started**"]), encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "manual A-domain test plan avoids stale or mojibake markers" in output


def test_manual_a_domain_test_plan_check_flags_secret_like_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc, _template_doc, _import_template_doc = _write_valid_docs(module, tmp_path, monkeypatch)
    doc.write_text("\n".join([*module.REQUIRED_MARKERS, "Bearer secret"]), encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "manual A-domain test plan is redacted" in output
