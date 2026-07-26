"""Tests for lifting project expectations market view."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.services.market_response_intelligence import build_lifting_project_expectations
from app.services.product_capability_schema import evaluate_project_requirement_fit


def test_evaluate_project_requirement_fit_is_explainable():
    result = evaluate_project_requirement_fit(
        "heavy_load",
        {"load_capacity_kg": 150},
        evidence="Customer asked for 150kg bench",
    )
    assert result["fit_score"] >= 80
    assert result["status"] == "strong_fit"
    assert result["confidence"] in ("high", "medium", "low")
    assert "recommended_next" in result


def test_build_lifting_project_expectations_structure():
    db = MagicMock()
    db.query.return_value.all.return_value = []
    data = build_lifting_project_expectations(db)
    assert "requirements" in data
    assert "products" in data
    assert data["safety"]["read_only"] is True
    assert data["safety"]["customer_notified"] is False
    assert data["summary"]["requirement_count"] >= 1
    row = data["requirements"][0]
    assert "requirement_label" in row
    assert row.get("single_feedback_is_not_conclusion") is True
