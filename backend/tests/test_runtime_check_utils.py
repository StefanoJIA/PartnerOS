"""Tests for runtime_check_utils."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

path = BACKEND_ROOT / "scripts" / "runtime_check_utils.py"
spec = importlib.util.spec_from_file_location("runtime_check_utils", path)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def test_runtime_item_levels():
    it = mod.RuntimeItem("test")
    it.pass_("ok")
    assert it.ok
    it.fail("x")
    assert not it.ok
    assert "FAIL" in it.line()


def test_stale_port_hints_contains_netstat():
    hint = mod.stale_port_hints("127.0.0.1", 8010)
    assert "netstat" in hint
    assert "8013" in hint
