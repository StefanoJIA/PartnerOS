from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "lead_intelligence_docs_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("lead_intelligence_docs_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_lead_intelligence_docs_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Lead Intelligence Docs Check" in output
    assert "Result: PASS" in output


def test_lead_intelligence_docs_check_flags_missing_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    docs = []
    for idx in range(3):
        doc = tmp_path / f"doc_{idx}.md"
        doc.write_text("Lead Intelligence MVP\n", encoding="utf-8")
        docs.append(doc)
    monkeypatch.setattr(module, "DOCS", tuple(docs))

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "Lead Intelligence docs match current operating contract" in output


def test_lead_intelligence_docs_check_flags_stale_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    docs = []
    for idx in range(3):
        doc = tmp_path / f"doc_{idx}.md"
        content = "\n".join(module.REQUIRED_MARKERS)
        if idx == 0:
            content += "\nNo runtime change"
        doc.write_text(content, encoding="utf-8")
        docs.append(doc)
    monkeypatch.setattr(module, "DOCS", tuple(docs))

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "Lead Intelligence docs avoid stale or mojibake markers" in output


def test_lead_intelligence_docs_check_flags_secret_like_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    docs = []
    for idx in range(3):
        doc = tmp_path / f"doc_{idx}.md"
        content = "\n".join(module.REQUIRED_MARKERS)
        if idx == 0:
            content += "\nBearer secret"
        doc.write_text(content, encoding="utf-8")
        docs.append(doc)
    monkeypatch.setattr(module, "DOCS", tuple(docs))

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "Lead Intelligence docs are redacted" in output
