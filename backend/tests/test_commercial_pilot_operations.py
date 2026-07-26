"""Commercial pilot operations gates."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.enums import PartnerLifecycle, SupplierDevelopmentTaskType, SupplierRelationshipType
from app.services.commercial_pilot_service import DEVELOPMENT_TASK_TEMPLATES, build_doc_request_checklist, build_email_draft
from app.services.partner_lifecycle import is_partner_selectable_for_new_quote


def test_public_candidate_relationship_enum():
    assert SupplierRelationshipType.public_candidate.value == "PUBLIC_CANDIDATE"


def test_development_task_template_count():
    assert len(DEVELOPMENT_TASK_TEMPLATES) == len(SupplierDevelopmentTaskType)


def test_email_draft_requires_human_approval():
    draft = build_email_draft(company_name="Acme", task_type="sample_requested")
    assert draft["approval_required"] == "true"
    assert draft["auto_send_blocked"] == "true"
    assert "DRAFT" in draft["body"]


def test_doc_request_checklist_has_core_items():
    checklist = build_doc_request_checklist(task_type="price_list_requested")
    keys = {item["item"] for item in checklist}
    assert "product_catalog" in keys
    assert "interval_pricing" in keys


def test_candidate_partner_not_quote_eligible():
    from unittest.mock import MagicMock

    partner = MagicMock()
    partner.lifecycle_status = PartnerLifecycle.candidate.value
    partner.partner_code = "EDU-CANDIDATE"
    assert is_partner_selectable_for_new_quote(partner) is False


def test_legacy_partner_not_quote_eligible():
    from unittest.mock import MagicMock

    partner = MagicMock()
    partner.lifecycle_status = PartnerLifecycle.legacy.value
    partner.partner_code = "HOSUN"
    assert is_partner_selectable_for_new_quote(partner) is False


def test_import_public_candidate_fields():
    from app.services.commercial_pilot_service import import_public_candidate
    from unittest.mock import MagicMock

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    captured = {}

    def _add(row):
        captured["row"] = row

    db.add.side_effect = _add
    db.flush.return_value = None
    import_public_candidate(
        db,
        payload={
            "company_name": "Test Public OEM",
            "source_url": "https://example.com/",
            "categories": ["Lifting Systems"],
        },
        actor_id=uuid4(),
    )
    row = captured["row"]
    assert row.relationship_type == SupplierRelationshipType.public_candidate.value
    assert row.usage_restrictions.startswith("Public candidate")


def test_selection_snapshot_duplicate_blocked():
    from app.models.project_request_candidates import ProjectRequestSupplierCandidate
    from app.services.supplier_network_service import freeze_selection_snapshot

    db = MagicMock()
    cand = ProjectRequestSupplierCandidate(
        id=uuid4(),
        project_request_id=uuid4(),
        candidate_source_type="partner",
        display_name="Demo",
        eligible_for_formal_quote=True,
    )
    db.query.return_value.filter.return_value.first.return_value = MagicMock()
    with pytest.raises(Exception):
        freeze_selection_snapshot(
            db,
            project_request_id=cand.project_request_id,
            selected_candidate=cand,
            actor_id=uuid4(),
        )
