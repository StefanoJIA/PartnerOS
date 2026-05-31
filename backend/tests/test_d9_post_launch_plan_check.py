from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d9_post_launch_plan_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d9_post_launch_plan_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d9_post_launch_plan_check_passes_for_current_plan(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D9 plan contains stage markers" in output
    assert "Result: PASS" in output


def test_d9_post_launch_plan_requires_real_evidence_wait_gate():
    module = _load_module()

    assert "WAITING_FOR_REAL_STAGING_EVIDENCE" in module.REQUIRED_MARKERS


def test_d9_post_launch_plan_check_fails_without_safety_markers(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "PLAN_DOC", tmp_path / "d9_post_launch_operating_loop.md")
    module.PLAN_DOC.write_text(
        "# D9 Post-Launch Operating Loop\n\nD9.1\nD9.2\nD9.3\nD9.4\nSTAGING_VALIDATED\nD8 Production Coordination Plan\n",
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D9 plan preserves safety boundaries" in output
    assert "Result: FAIL" in output


def test_d9_post_launch_plan_check_fails_for_generic_api_key(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "PLAN_DOC", tmp_path / "d9_post_launch_operating_loop.md")
    module.PLAN_DOC.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "SERVICE_PORTAL_API_KEY=actual-secret-value"]),
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D9 plan is redacted" in output
    assert "d9_post_launch_operating_loop.md" in output


def test_records_gate_status_rejects_final_fail(monkeypatch):
    module = _load_module()

    def fake_run(*args, **kwargs):  # noqa: ARG001
        return type(
            "Result",
            (),
            {
                "returncode": 0,
                "stdout": "[PASS] nested\nResult: PASS\nResult: FAIL\n",
                "stderr": "",
            },
        )()

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    ok, detail = module._records_gate_status()

    assert ok is False
    assert detail == "[PASS] nested\nResult: PASS\nResult: FAIL"
