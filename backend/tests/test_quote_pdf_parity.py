"""PDF interval table parity with quote line pricing snapshot."""

from __future__ import annotations

from app.services.quotes.pdf_data_builder import _sanitize_interval_quote_table
from app.services.quotes.pricing_service import validate_interval_quote_table


def test_pdf_interval_table_matches_quote_snapshot():
    rows = [
        {
            "quantity_label": "1-49",
            "min_qty": 1,
            "max_qty": 49,
            "currency": "USD",
            "fob_unit_price": "120.00",
            "ddp_unit_price": "158.00",
            "incoterms_available": ["FOB", "DDP"],
        },
        {
            "quantity_label": "50+",
            "min_qty": 50,
            "max_qty": None,
            "currency": "USD",
            "fob_unit_price": "110.00",
            "ddp_unit_price": "145.00",
            "incoterms_available": ["FOB", "DDP"],
        },
    ]
    line = {
        "currency": "USD",
        "pricing_breakdown_json": {
            "quote_model": {
                "final_quote_stage": {"interval_quote_table": rows},
            }
        },
    }
    pdf_rows = _sanitize_interval_quote_table(line)
    assert len(pdf_rows) == 2
    assert pdf_rows[0]["fob_unit_price"] == "120.00"
    assert pdf_rows[0]["ddp_unit_price"] == "158.00"
    assert pdf_rows[1]["min_qty"] == 50
    assert validate_interval_quote_table(pdf_rows) == []


def test_validate_interval_quote_table_flags_gaps_and_negative_prices():
    bad_rows = [
        {"min_qty": 1, "max_qty": 49, "fob_unit_price": "-1", "ddp_unit_price": "10"},
        {"min_qty": 60, "max_qty": 99, "fob_unit_price": "20", "ddp_unit_price": "15"},
    ]
    issues = validate_interval_quote_table(bad_rows)
    assert any("negative" in issue for issue in issues)
    assert any("gap" in issue for issue in issues)
    assert any("ddp_lt_fob" in issue for issue in issues)
