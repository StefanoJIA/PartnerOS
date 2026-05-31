from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_staging_execution_pack_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_staging_execution_pack_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d8_staging_execution_pack_uses_final_result_line():
    module = _load_module()

    passing = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="[PASS] child\nResult: PASS\n",
        stderr="",
    )
    nested_fail = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="nested Result: PASS\nResult: FAIL\n",
        stderr="",
    )
    nonzero = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout="Result: PASS\n",
        stderr="",
    )

    assert module._result_pass(passing) is True
    assert module._result_pass(nested_fail) is False
    assert module._result_pass(nonzero) is False


def test_d8_staging_execution_pack_flags_stale_local_rehearsal_url_wording(tmp_path, monkeypatch):
    module = _load_module()
    doc = tmp_path / "docs" / "phase3" / "d8_strict_staging_cloud_validation.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("local rehearsal URLs may remain local\n", encoding="utf-8")
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        module,
        "REQUIRED_FILES",
        ("docs/phase3/d8_strict_staging_cloud_validation.md",),
    )

    assert module._doc_marker_issues() == [
        "docs/phase3/d8_strict_staging_cloud_validation.md:local rehearsal URLs may remain local"
    ]
