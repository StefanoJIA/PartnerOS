from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_0_staging_build_readiness_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_0_staging_build_readiness_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d8_0_check_tracks_required_environment_markers():
    module = _load_module()

    assert "PORTAL_CUSTOMER_API_ENABLED" in module.REQUIRED_DOC_MARKERS
    assert "PORTAL_CUSTOMER_API_TOKEN" in module.REQUIRED_DOC_MARKERS
    assert "PORTAL_CUSTOMER_ALLOWED_ORIGINS" in module.REQUIRED_DOC_MARKERS
    assert "PUBLIC_BASE_URL" in module.REQUIRED_DOC_MARKERS


def test_d8_0_marker_check_reports_missing_marker():
    module = _load_module()

    check = module._marker_check("sample", "alpha beta", ("alpha", "gamma"))

    assert check.ok is False
    assert check.detail == "gamma"


def test_d8_0_marker_check_passes_when_all_markers_exist():
    module = _load_module()

    check = module._marker_check("sample", "alpha beta", ("alpha", "beta"))

    assert check.ok is True
