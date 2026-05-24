"""Unit tests for D6.2 / D6.2.1 Excel import script."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "import_pricing_excel.py"
_spec = importlib.util.spec_from_file_location("import_pricing_excel", SCRIPT_PATH)
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)


def test_import_dry_run_missing_file(capsys):
    rc = _mod.run(Path("/nonexistent/pricing.xlsx"), apply=False, overwrite=False)
    out = capsys.readouterr().out
    assert rc == 1
    assert "not found" in out.lower()


@pytest.mark.skipif(
    not Path(__file__).resolve().parents[2].joinpath("local_data", "报价模型与格式.xlsx").is_file(),
    reason="local Excel workbook not present",
)
def test_import_dry_run_reads_sheets_and_candidates(capsys):
    xlsx = Path(__file__).resolve().parents[2] / "local_data" / "报价模型与格式.xlsx"
    rc = _mod.run(xlsx, apply=False, overwrite=False)
    out = capsys.readouterr().out
    assert rc == 0
    assert "Available sheets:" in out
    assert "Excel Import Summary" in out
    assert "total candidate rows:" in out
    assert "Detected type: cost_model" in out
    assert "Detected type: price_tier" in out


@pytest.mark.skipif(
    not Path(__file__).resolve().parents[2].joinpath("local_data", "报价模型与格式.xlsx").is_file(),
    reason="local Excel workbook not present",
)
def test_import_dry_run_nonzero_summary(capsys):
    xlsx = Path(__file__).resolve().parents[2] / "local_data" / "报价模型与格式.xlsx"
    _mod.run(xlsx, apply=False, overwrite=False)
    out = capsys.readouterr().out
    assert "products: {'created':" in out or "'created':" in out
    assert "'created': 0" not in out.split("products:")[1].split("\n")[0]


def test_overwrite_updates_existing_cost_model():
    from app.services.quotes.pricing_excel_parser import ParsedCostRow

    product = MagicMock()
    product.id = "prod-1"
    existing_cost = MagicMock()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [product, existing_cost]
    summary = {
        "partners": {"created": 0, "updated": 0, "skipped": 0},
        "products": {"created": 0, "updated": 0, "skipped": 0},
        "cost_models": {"created": 0, "updated": 0, "skipped": 0},
        "price_tiers": {"created": 0, "updated": 0, "skipped": 0},
        "margin_tiers": {"created": 0, "updated": 0, "skipped": 0},
        "fx_rates": {"created": 0, "updated": 0, "skipped": 0},
        "warnings": [],
        "errors": [],
    }
    row = ParsedCostRow(
        partner_code="HOSUN",
        product_name="Desk",
        partner_product_code=None,
        internal_sku="HOSUN-DESK",
        material_cost=_mod.Decimal("100"),
        weight=None,
        domestic_transport=None,
        freight_cost_usd=None,
        fob_cost_usd=None,
        ddp_cost_usd=None,
    )
    partners = {"HOSUN": MagicMock(id="p1", partner_code="HOSUN")}
    with patch.object(_mod, "_upsert_product", return_value=product):
        _mod._import_cost_row(db, row, meta=MagicMock(), overwrite=True, summary=summary, partners=partners)
    assert summary["cost_models"]["updated"] == 1


def test_no_overwrite_skips_duplicate_cost_model():
    from app.services.quotes.pricing_excel_parser import ParsedCostRow

    product = MagicMock()
    product.id = "prod-1"
    existing_cost = MagicMock()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [product, existing_cost]
    summary = {
        "partners": {"created": 0, "updated": 0, "skipped": 0},
        "products": {"created": 0, "updated": 0, "skipped": 0},
        "cost_models": {"created": 0, "updated": 0, "skipped": 0},
        "price_tiers": {"created": 0, "updated": 0, "skipped": 0},
        "margin_tiers": {"created": 0, "updated": 0, "skipped": 0},
        "fx_rates": {"created": 0, "updated": 0, "skipped": 0},
        "warnings": [],
        "errors": [],
    }
    row = ParsedCostRow(
        partner_code="HOSUN",
        product_name="Desk",
        partner_product_code=None,
        internal_sku="HOSUN-DESK",
        material_cost=_mod.Decimal("100"),
        weight=None,
        domestic_transport=None,
        freight_cost_usd=None,
        fob_cost_usd=None,
        ddp_cost_usd=None,
    )
    partners = {"HOSUN": MagicMock(id="p1", partner_code="HOSUN")}
    with patch.object(_mod, "_upsert_product", return_value=product):
        _mod._import_cost_row(db, row, meta=MagicMock(), overwrite=False, summary=summary, partners=partners)
    assert summary["cost_models"]["skipped"] == 1


def test_workbook_not_in_repo():
    repo_root = Path(__file__).resolve().parents[2]
    tracked = (repo_root / ".git" / "index").exists()
    xlsx = repo_root / "local_data" / "报价模型与格式.xlsx"
    if xlsx.is_file():
        import subprocess

        result = subprocess.run(
            ["git", "check-ignore", str(xlsx)],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
