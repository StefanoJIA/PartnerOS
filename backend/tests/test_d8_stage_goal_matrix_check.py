from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_stage_goal_matrix_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_stage_goal_matrix_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d8_stage_goal_matrix_check_passes_for_repo_doc(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D8 Stage Goal Matrix Check" in output
    assert "Result: PASS" in output
