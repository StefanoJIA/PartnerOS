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


def test_manual_a_domain_test_plan_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Manual A-Domain Test Plan Check" in output
    assert "Result: PASS" in output


def test_manual_a_domain_test_plan_check_flags_missing_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "manual_a_domain_test_plan.md"
    doc.write_text("Manual A-Domain Test Plan\n", encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "manual A-domain test plan matches current UAT contract" in output


def test_manual_a_domain_test_plan_check_flags_stale_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "manual_a_domain_test_plan.md"
    doc.write_text("\n".join([*module.REQUIRED_MARKERS, "D6 Productization | **Not started**"]), encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "manual A-domain test plan avoids stale or mojibake markers" in output


def test_manual_a_domain_test_plan_check_flags_secret_like_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "manual_a_domain_test_plan.md"
    doc.write_text("\n".join([*module.REQUIRED_MARKERS, "Bearer secret"]), encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "manual A-domain test plan is redacted" in output
