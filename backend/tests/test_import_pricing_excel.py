"""Unit tests for D6.2 Excel import helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "import_pricing_excel.py"
_spec = importlib.util.spec_from_file_location("import_pricing_excel", SCRIPT_PATH)
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)


def test_header_map_values_only_row():
    row = ("Product Name", None, "Weight", "")
    headers = _mod._header_map(row)
    assert headers["product name"] == 0
    assert headers["weight"] == 2
    assert "product name" in headers


def test_header_map_cell_objects():
    class Cell:
        def __init__(self, value):
            self.value = value

    row = (Cell("FOB Cost USD"), Cell(None), Cell("DDP Cost USD"))
    headers = _mod._header_map(row)
    assert headers["fob cost usd"] == 0
    assert headers["ddp cost usd"] == 2


def test_find_sheet_partial_match():
    class WB:
        sheetnames = ["成本表", "价目表", "Quote HOSUN"]

    assert _mod._find_sheet(WB(), _mod.SHEET_COST) == "成本表"
    assert _mod._find_sheet(WB(), _mod.SHEET_PRICE) == "价目表"


def test_import_dry_run_missing_file(capsys):
    rc = _mod.run(Path("/nonexistent/pricing.xlsx"), apply=False, overwrite=False)
    out = capsys.readouterr().out
    assert rc == 1
    assert "not found" in out.lower()


@pytest.mark.skipif(
    not Path(__file__).resolve().parents[2].joinpath("local_data", "报价模型与格式.xlsx").is_file(),
    reason="local Excel workbook not present",
)
def test_import_dry_run_reads_sheets(capsys):
    xlsx = Path(__file__).resolve().parents[2] / "local_data" / "报价模型与格式.xlsx"
    rc = _mod.run(xlsx, apply=False, overwrite=False)
    out = capsys.readouterr().out
    assert rc == 0
    assert "Available sheets:" in out
    assert "Excel Import Summary" in out


def test_dec_and_int_helpers():
    assert _mod._dec("1,234.50") == _mod.Decimal("1234.50")
    assert _mod._dec("") is None
    assert _mod._int("50") == 50
    assert _mod._int(None) is None
