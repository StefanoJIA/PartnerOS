from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _load_script(name: str):
    path = BACKEND_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d7_7_forbidden_scan_tolerates_non_json_response():
    module = _load_script("d7_7_portal_bridge_check.py")
    response = SimpleNamespace(json=lambda: (_ for _ in ()).throw(ValueError("not json")))

    assert module._no_forbidden_blob(response) == (True, "clean")


def test_d7_7_json_helper_tolerates_non_json_response():
    module = _load_script("d7_7_portal_bridge_check.py")
    response = SimpleNamespace(json=lambda: (_ for _ in ()).throw(ValueError("not json")))

    assert module._json(response) == {}


def test_d7_9_forbidden_scan_tolerates_non_json_response():
    module = _load_script("d7_9_resource_center_check.py")
    response = SimpleNamespace(
        headers={"content-type": "application/json"},
        json=lambda: (_ for _ in ()).throw(ValueError("not json")),
    )

    assert module._no_forbidden(response) == (True, "clean")


def test_d7_9_json_helper_tolerates_non_json_response():
    module = _load_script("d7_9_resource_center_check.py")
    response = SimpleNamespace(json=lambda: (_ for _ in ()).throw(ValueError("not json")))

    assert module._json(response) == {}


def test_d7_9_finish_reports_fail(capsys):
    module = _load_script("d7_9_resource_center_check.py")
    check = module.Check("sample")
    check.fail("broken")

    assert module._finish([check]) == 1
    output = capsys.readouterr().out
    assert "[FAIL] sample (broken)" in output
    assert "Result: FAIL" in output


def test_d7_6_json_helper_tolerates_non_json_response():
    module = _load_script("d7_6_shipment_tracking_check.py")
    response = SimpleNamespace(json=lambda: (_ for _ in ()).throw(ValueError("not json")))

    assert module._json(response) == {}


def test_d7_6_finish_reports_fail(capsys):
    module = _load_script("d7_6_shipment_tracking_check.py")
    check = module.Check("shipment")
    check.fail("backend unavailable")

    assert module._finish([check]) == 1
    output = capsys.readouterr().out
    assert "[FAIL] shipment (backend unavailable)" in output
    assert "Result: FAIL" in output
