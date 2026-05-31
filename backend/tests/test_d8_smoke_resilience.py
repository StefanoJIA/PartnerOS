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


def test_d8_4_json_helper_tolerates_non_json_response():
    module = _load_script("d8_4_partner_operations_check.py")
    response = SimpleNamespace(json=lambda: (_ for _ in ()).throw(ValueError("not json")))

    assert module._json(response) == {}


def test_d8_4_finish_reports_fail(capsys):
    module = _load_script("d8_4_partner_operations_check.py")
    check = module.Check("operations")
    check.fail("HTTP 500")

    assert module._finish([check]) == 1
    output = capsys.readouterr().out
    assert "D8.4 Partner Operations Dashboard Check" in output
    assert "[FAIL] operations (HTTP 500)" in output
    assert "Result: FAIL" in output


def test_d8_5_json_helper_tolerates_non_json_response():
    module = _load_script("d8_5_market_response_check.py")
    response = SimpleNamespace(json=lambda: (_ for _ in ()).throw(ValueError("not json")))

    assert module._json(response) == {}


def test_d8_5_finish_reports_fail(capsys):
    module = _load_script("d8_5_market_response_check.py")
    check = module.Check("market")
    check.fail("HTTP 500")

    assert module._finish([check]) == 1
    output = capsys.readouterr().out
    assert "D8.5 Market Response Intelligence Check" in output
    assert "[FAIL] market (HTTP 500)" in output
    assert "Result: FAIL" in output


def test_d8_1_json_helper_tolerates_non_json_response():
    module = _load_script("d8_1_rbac_scoped_access_check.py")
    response = SimpleNamespace(json=lambda: (_ for _ in ()).throw(ValueError("not json")))

    assert module._json(response) == {}


def test_d8_1_finish_reports_fail(capsys):
    module = _load_script("d8_1_rbac_scoped_access_check.py")
    check = module.Check("rbac")
    check.fail("HTTP 500")

    assert module._finish([check]) == 1
    output = capsys.readouterr().out
    assert "D8.1 RBAC Scoped Access Check" in output
    assert "[FAIL] rbac (HTTP 500)" in output
    assert "Result: FAIL" in output
