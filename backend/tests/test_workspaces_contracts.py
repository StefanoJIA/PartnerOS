"""Workspace route and schema contracts (no DB)."""

from fastapi.routing import APIRoute

from app.main import create_app
from app.schemas.object_workspaces import (
    CompanyWorkspaceOut,
    ContactWorkspaceOut,
    PartnerWorkspaceOut,
    ProductWorkspaceOut,
)


def _api_paths() -> set[str]:
    app = create_app()
    return {r.path for r in app.routes if isinstance(r, APIRoute)}


def test_workspace_routes_registered():
    paths = _api_paths()
    assert "/api/companies/{company_id}/workspace" in paths
    assert "/api/contacts/{contact_id}/workspace" in paths
    assert "/api/manufacturing-partners/{partner_id}/workspace" in paths
    assert "/api/products/{product_id}/workspace" in paths


def test_product_partner_link_routes():
    paths = _api_paths()
    assert "/api/products/{product_id}/partners/{partner_id}" in paths
    assert "/api/manufacturing-partners/{partner_id}/products/{product_id}" in paths


def test_workspace_out_schemas_contain_core_lists():
    assert "contacts" in CompanyWorkspaceOut.model_fields
    assert "leads" in CompanyWorkspaceOut.model_fields
    assert "company" in ContactWorkspaceOut.model_fields
    assert "related_leads" in ContactWorkspaceOut.model_fields
    assert "linked_products" in PartnerWorkspaceOut.model_fields
    assert "partner_rows" in ProductWorkspaceOut.model_fields


def test_no_hardcoded_partner_priority_in_core_tree():
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent / "app"
    allow_names = {
        "prompts.py",
        "knowledge.py",
        "outreach_templates.py",
        "product_fit.py",
        "product_fit_board.py",
        "pre_quote_prep.py",
        "product_aware_outreach.py",
        "quote_handoff.py",
        "quote_handoff_board.py",
    }
    bad: list[str] = []
    for path in root.rglob("*.py"):
        if path.name in allow_names:
            continue
        text = path.read_text(encoding="utf-8")
        if "hosun" in text.lower():
            bad.append(str(path.relative_to(root)))
    assert not bad, "Unexpected HOSUN string in app code: " + ", ".join(bad)


def test_rfq_workspace_route_registered():
    paths = _api_paths()
    assert "/api/rfqs/{rfq_id}/workspace" in paths
    assert "/api/rfqs/{rfq_id}/quotation-comparison" in paths
    assert "/api/rfqs/{rfq_id}/convert-to-sample" in paths
    assert "/api/rfqs/{rfq_id}/convert-to-order" in paths


def test_sample_order_workspace_routes_registered():
    paths = _api_paths()
    assert "/api/samples/{sample_id}/workspace" in paths
    assert "/api/samples/{sample_id}/status" in paths
    assert "/api/samples/{sample_id}/shipping" in paths
    assert "/api/samples/{sample_id}/feedback" in paths
    assert "/api/samples/{sample_id}/convert-to-order" in paths
    assert "/api/orders/{order_id}/workspace" in paths
    assert "/api/orders/{order_id}/production-status" in paths
    assert "/api/orders/{order_id}/shipping-status" in paths
    assert "/api/orders/{order_id}/generate-milestones" in paths
    assert "/api/orders/{order_id}/milestones/{milestone_id}" in paths
    assert "/api/orders/{order_id}/milestones/{milestone_id}/complete" in paths
    assert "/api/orders/{order_id}/milestones/{milestone_id}/delayed" in paths
    assert "/api/orders/{order_id}/shipping-records" in paths
    assert "/api/orders/{order_id}/shipping-records/{record_id}" in paths


def test_sample_order_ai_routes_registered():
    paths = _api_paths()
    for p in (
        "/api/ai/sample-follow-up-email",
        "/api/ai/sample-feedback-request",
        "/api/ai/sample-internal-risk-summary",
        "/api/ai/sample-customer-update",
        "/api/ai/sample-next-step-recommendation",
        "/api/ai/order-delay-explanation-email",
        "/api/ai/order-internal-risk-summary",
        "/api/ai/order-shipping-status-update",
        "/api/ai/order-partner-followup",
        "/api/ai/order-next-step-recommendation",
    ):
        assert p in paths
