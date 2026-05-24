"""Tests for D7.5 production templates."""

from __future__ import annotations

from app.services.orders.production_templates import get_default_milestone_template


def test_lifting_template_includes_welding():
    items = get_default_milestone_template(None, "lifting_frame")
    types = [i["milestone_type"] for i in items]
    assert "cutting" in types
    assert "welding" in types
    assert "painting" in types
    assert "assembly" in types
    assert "quality_check" in types


def test_education_template():
    items = get_default_milestone_template(None, "education_desk")
    types = [i["milestone_type"] for i in items]
    assert "production_started" in types
    assert "cutting" not in types


def test_generic_fallback():
    items = get_default_milestone_template(None, "office_furniture")
    assert len(items) >= 5
