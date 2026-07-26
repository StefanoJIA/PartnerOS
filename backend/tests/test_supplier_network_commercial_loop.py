"""Supplier network commercial loop gates."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.enums import PartnerLifecycle, SupplierDiscoveryStatus
from app.services.partner_lifecycle import get_default_lifting_partner, is_partner_selectable_for_new_quote
from app.services.supplier_discovery_service import (
    QUALIFICATION_DIMENSIONS,
    build_dedup_fingerprint,
    init_qualification_json,
    parse_csv_import,
    update_qualification_dimension,
)


def test_qualification_dimensions_initialized():
    qual = init_qualification_json()
    assert set(qual["dimensions"].keys()) == set(QUALIFICATION_DIMENSIONS)
    assert all(d["status"] == "UNKNOWN" for d in qual["dimensions"].values())


def test_dedup_fingerprint_stable():
    fp1 = build_dedup_fingerprint(company_name="Acme Co", domain_key="acme.com")
    fp2 = build_dedup_fingerprint(company_name="Acme Co", domain_key="acme.com")
    assert fp1 == fp2
    fp3 = build_dedup_fingerprint(company_name="Other Co", domain_key="acme.com")
    assert fp1 != fp3


def test_csv_import_parses_rows():
    csv_content = "company_name,country,url,categories\nTest Mfg,CN,https://test.com,Lifting;Desk\n"
    rows = parse_csv_import(csv_content)
    assert len(rows) == 1
    assert rows[0]["company_name"] == "Test Mfg"
    assert rows[0]["domain_key"] == "test.com"


def test_qualification_dimension_update():
    from app.models.supplier_discovery import SupplierDiscoveryRecord

    record = SupplierDiscoveryRecord(company_name="Test", status=SupplierDiscoveryStatus.evaluating.value)
    reviewer = uuid4()
    update_qualification_dimension(
        record,
        dimension_key="product_capability_completeness",
        status="PASS",
        evidence="Catalog received",
        reviewer_id=reviewer,
    )
    dim = record.qualification_json["dimensions"]["product_capability_completeness"]
    assert dim["status"] == "PASS"
    assert dim["reviewer_id"] == str(reviewer)


def test_legacy_hosun_not_default_lifting():
    db = MagicMock()
    lift = MagicMock()
    lift.partner_code = "LIFT-DEMO"
    lift.lifecycle_status = PartnerLifecycle.active.value
    db.query.return_value.filter.return_value.first.return_value = lift
    assert get_default_lifting_partner(db).partner_code == "LIFT-DEMO"


def test_inactive_partner_not_selectable():
    partner = MagicMock()
    partner.lifecycle_status = PartnerLifecycle.paused.value
    partner.partner_code = "OFFICE-PAUSED"
    assert is_partner_selectable_for_new_quote(partner) is False


def test_discovery_status_flow_includes_sample_received():
    assert SupplierDiscoveryStatus.information_requested.value == "information_requested"
    assert SupplierDiscoveryStatus.sample_received.value == "sample_received"


def test_benchmark_not_eligible_for_formal_quote():
    from app.models.benchmark_knowledge import BenchmarkBrand
    from app.models.customer_project_requests import CustomerProjectRequest
    from app.services.customer_project_requests.multi_supplier_fit_service import build_benchmark_candidate

    brand = BenchmarkBrand(
        id=uuid4(),
        brand_code="BENCH",
        display_name="Benchmark Only",
        industry_vertical="lifting_systems",
        relationship_disclaimer="Reference only",
    )
    brand.capabilities = []
    row = CustomerProjectRequest(request_reference="CPR-X", status="submitted")
    payload = build_benchmark_candidate(MagicMock(), row, brand)
    assert payload["eligible_for_formal_quote"] is False


def test_selection_snapshot_immutable_after_create():
    from app.models.project_request_candidates import ProjectRequestSupplierCandidate
    from app.models.supplier_selection_snapshots import SupplierSelectionSnapshot
    from app.services.supplier_network_service import build_candidate_snapshot_payload, freeze_selection_snapshot

    db = MagicMock()
    cand = ProjectRequestSupplierCandidate(
        id=uuid4(),
        project_request_id=uuid4(),
        candidate_source_type="partner",
        display_name="Demo",
        eligible_for_formal_quote=True,
    )
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = [cand]
    actor = uuid4()

    def _add(obj):
        pass

    db.add = _add
    db.flush = MagicMock()
    snap = freeze_selection_snapshot(
        db,
        project_request_id=cand.project_request_id,
        selected_candidate=cand,
        actor_id=actor,
    )
    assert isinstance(snap, SupplierSelectionSnapshot)
    payload = build_candidate_snapshot_payload([cand])
    assert len(payload["candidates"]) == 1


def test_portal_site_project_request_out_has_no_supplier_candidates():
    from app.schemas.customer_project_request_domain import SiteProjectRequestOut

    fields = set(SiteProjectRequestOut.model_fields.keys())
    forbidden = {"candidates", "supplier_candidates", "fit_dimensions_json", "qualification_json", "margin"}
    assert forbidden.isdisjoint(fields)
