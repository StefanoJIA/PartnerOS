from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d9_3_market_response_loop_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d9_3_market_response_loop_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d9_3_market_response_loop_check_passes_for_repo_doc(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D9.3 Market Response Loop Check" in output
    assert "Result: PASS" in output


def test_d9_3_market_response_loop_check_flags_token(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "market.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "SERVICE_PORTAL_PARTNEROS_TOKEN=secret"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "SERVICE_PORTAL_PARTNEROS_TOKEN" in output
