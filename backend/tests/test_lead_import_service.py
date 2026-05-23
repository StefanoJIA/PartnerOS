"""Tests for lead import service (D5.3)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.services.a_domain.lead_import_service import (
    apply_lead_csv_text,
    preview_lead_csv_text,
)


def _mock_db_no_companies() -> MagicMock:
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    return db


HEADER = (
    "company_name,website,company_type,industry,city,state,country,"
    "contact_name,contact_title,contact_email,contact_phone,linkedin_url,"
    "source,notes,initial_interest,priority,next_action\n"
)


def test_preview_returns_summary():
    csv_text = (
        HEADER
        + "Acme Lift Co,https://acme.example,Office Furniture Dealer,Commercial,Boston,MA,US,"
        "Alex Test,VP,alex@acme.example,,,Trade show,height-adjustable desk frames,,High,\n"
    )
    result = preview_lead_csv_text(_mock_db_no_companies(), csv_text)
    assert result.summary.total == 1
    assert result.summary.ok == 1
    assert result.rows[0].likely_segments
    assert "lift_system_signal" in result.rows[0].likely_segments


def test_preview_missing_company_name_is_error():
    csv_text = HEADER + ",https://x.example,Office Furniture Dealer,,,,,Someone,,someone@x.example,,,,notes,,,\n"
    result = preview_lead_csv_text(_mock_db_no_companies(), csv_text)
    assert result.summary.errors == 1
    assert result.rows[0].status == "error"
    assert "company_name" in result.rows[0].missing_fields


def test_preview_duplicate_in_csv():
    csv_text = (
        HEADER
        + "Dup Co,https://a.example,Office Furniture Dealer,,,,,A,,a@example.com,,,,,,,\n"
        + "Dup Co,https://b.example,Office Furniture Dealer,,,,,B,,b@example.com,,,,,,,\n"
    )
    result = preview_lead_csv_text(_mock_db_no_companies(), csv_text)
    assert result.summary.duplicates >= 1
    assert result.rows[1].duplicate_status == "possible_duplicate"


def test_preview_education_segment():
    csv_text = (
        HEADER
        + "Campus Co,https://campus.example,Education Furniture Company,Education,,,,Jordan,,j@c.example,,,"
        "Referral,university classroom furniture,,Medium,\n"
    )
    result = preview_lead_csv_text(_mock_db_no_companies(), csv_text)
    assert "education_vertical" in result.rows[0].likely_segments


def test_apply_requires_confirm():
    db = MagicMock()
    with pytest.raises(ValueError, match="confirm must be true"):
        apply_lead_csv_text(db, MagicMock(), HEADER, confirm=False)


def test_apply_refuses_error_rows():
    csv_text = HEADER + ",https://bad.example,Office Furniture Dealer,,,,,X,,x@bad.example,,,,,,,\n"
    db = MagicMock()
    with pytest.raises(ValueError, match="errors"):
        apply_lead_csv_text(db, MagicMock(), csv_text, confirm=True)
