"""RFQ workspace aggregate schema contracts (no database)."""

from app.schemas.rfq_domain import RFQWorkspaceOut


def test_rfq_workspace_out_has_required_sections():
    """P4 workspace payload shape for GET /api/rfqs/{id}/workspace."""
    fields = set(RFQWorkspaceOut.model_fields.keys())
    required = {
        "rfq",
        "company",
        "contact",
        "lead",
        "owner_display",
        "rfq_items",
        "candidate_manufacturing_partners",
        "partner_candidates_with_partner_detail",
        "quotations",
        "quotation_items",
        "quotation_comparison",
        "related_samples",
        "related_orders",
        "recent_interactions",
        "open_tasks",
        "recent_ai_outputs",
        "files",
        "activity_summary",
    }
    assert required <= fields
