"""Multibrand export OS gates — partner lifecycle, benchmark isolation, multi-supplier fit."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.enums import PartnerLifecycle
from app.services.partner_lifecycle import (
    get_default_lifting_partner,
    is_partner_default_recommendable,
    is_partner_selectable_for_new_quote,
)


def _partner(*, code: str | None, lifecycle: str):
    p = MagicMock()
    p.partner_code = code
    p.lifecycle_status = lifecycle
    p.partner_name = code or "Test"
    p.partner_type = "Lifting System Manufacturer"
    return p


def test_legacy_hosun_not_selectable_for_new_quote():
    hosun = _partner(code="HOSUN", lifecycle=PartnerLifecycle.legacy.value)
    assert is_partner_selectable_for_new_quote(hosun) is False
    assert is_partner_default_recommendable(hosun) is False


def test_active_lift_demo_selectable():
    lift = _partner(code="LIFT-DEMO", lifecycle=PartnerLifecycle.active.value)
    assert is_partner_selectable_for_new_quote(lift) is True
    assert is_partner_default_recommendable(lift) is True


def test_get_default_lifting_partner_prefers_lift_demo():
    db = MagicMock()
    lift = _partner(code="LIFT-DEMO", lifecycle=PartnerLifecycle.active.value)
    db.query.return_value.filter.return_value.first.return_value = lift
    assert get_default_lifting_partner(db) is lift


def test_benchmark_candidate_not_eligible_for_formal_quote():
    from app.models.benchmark_knowledge import BenchmarkBrand
    from app.models.customer_project_requests import CustomerProjectRequest
    from app.services.customer_project_requests.multi_supplier_fit_service import build_benchmark_candidate

    brand = BenchmarkBrand(
        id=uuid4(),
        brand_code="LINAK",
        display_name="LINAK (public benchmark)",
        industry_vertical="lifting_systems",
        relationship_disclaimer="Industry reference only",
    )
    brand.capabilities = []
    row = CustomerProjectRequest(request_reference="CPR-BENCH", status="submitted")
    payload = build_benchmark_candidate(MagicMock(), row, brand)
    assert payload["eligible_for_formal_quote"] is False
    assert payload["is_auto_recommended"] is False
    assert payload["candidate_source_type"] == "benchmark"


def test_hosun_partner_candidate_never_auto_recommended():
    from app.models.customer_project_requests import CustomerProjectRequest
    from app.services.customer_project_requests.multi_supplier_fit_service import build_partner_candidate

    catalog = MagicMock()
    catalog.id = uuid4()
    catalog.internal_sku = "HS-HRD-300"
    catalog.product_name = "Legacy frame"
    catalog.attributes_json = {"load_capacity_kg": 300, "noise_db": 45}
    partner = _partner(code="HOSUN", lifecycle=PartnerLifecycle.legacy.value)
    row = CustomerProjectRequest(
        request_reference="CPR-LEG",
        status="submitted",
        requirements_json={"load_capacity_kg": 300},
    )
    payload = build_partner_candidate(MagicMock(), row, catalog, partner)
    assert payload["is_auto_recommended"] is False
    assert payload["eligible_for_formal_quote"] is False
